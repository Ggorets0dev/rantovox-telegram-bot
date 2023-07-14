'''Entry point with all code'''

import json
import os
import random
import subprocess
import wave

from pyfiglet import figlet_format
from pymorphy3 import MorphAnalyzer
import pyttsx3
import yaml
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.storage import FSMContext
from aiogram.types import (CallbackQuery, ContentType, InlineKeyboardButton,
                           InlineKeyboardMarkup)
from dotenv import load_dotenv
from loguru import logger
from vosk import KaldiRecognizer, Model, SetLogLevel
from src.lang.localization import LOCALIZATION, check_locales_equivalence


# NOTE - Declaring a class to save the user's state
class Condition(StatesGroup):
    '''Describes the stage of the conversation with the bot that the user is in'''
    Req = State()


# NOTE - Saving the path to the working directory
DIRNAME = os.path.join(os.path.dirname(__file__))


# NOTE - Reading the configuration file
with open("config.yaml", "r", encoding='UTF-8') as file_read:
    try:
        CONFIG = yaml.safe_load(file_read)
    except yaml.YAMLError as e:
        raise e
    

def recognize_speech(wav_filepath: str, lang_model: Model) -> str:
    '''Recognize speech in a wav file using the vosk model and return the text'''
    if not(os.path.isfile(wav_filepath)): 
        return ''

    wf = wave.open(wav_filepath, 'rb')
    recog = KaldiRecognizer(lang_model, wf.getframerate())

    result_text = ''
    last_char = False

    while True:
        data_frame = wf.readframes(wf.getnframes())
        if len(data_frame) == 0:
            break

        elif recog.AcceptWaveform(data_frame):
            res = json.loads(recog.Result())

            if res['text'] != '':
                result_text += f" {res['text']}"
                last_char = False
            elif not last_char:
                result_text += '\n'
                last_char = True

    res = json.loads(recog.FinalResult())
    result_text += f" {res['text']}"

    return result_text

def extra_text_processing(msg: str, used_lang: str) -> str:
    '''Process additional text with the help of rules'''
    if not(CONFIG.get('ETP_ENABLED')):
        logger.warning('ETP is disabled in the configuration file, a raw message is returned')
        return msg
    
    LANGUAGES_SUPPORTED = {
        'RUSSIAN': 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
        'ENGLISH': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    }

    msg, used_lang = msg[1:], used_lang.upper()
    MORPH = MorphAnalyzer()

    if used_lang not in list(LANGUAGES_SUPPORTED.keys()):
        logger.warning('An unknown language was requested in ETP, a raw message is returned')
        return msg

    else:
        msg_words = msg.split(' ')
        upper_list = []

        if used_lang.upper() == 'RUSSIAN':
            RU_NAMES_PATH = os.path.join(DIRNAME, 'src', 'etp', CONFIG.get('ETP_RUSSIAN_NAMES_FILENAME'))
            RU_SURNAMES_PATH = os.path.join(DIRNAME, 'src', 'etp', CONFIG.get('ETP_RUSSIAN_SURNAMES_FILENAME'))

            # NOTE - Adding russian names to upper case filter
            with open(RU_NAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))
            
            # NOTE - Adding russian surnames to upper case filter
            with open(RU_SURNAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))

        elif used_lang.upper() == 'ENGLISH':
            ENG_NAMES_PATH = os.path.join(DIRNAME, 'src', 'etp', CONFIG.get('ETP_ENGLISH_NAMES_FILENAME'))

            # NOTE - Adding russian names to upper case filter
            with open(ENG_NAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))


        for word_inx, word in enumerate(msg_words):
            word_morphing = MORPH.parse(word)[0]
            
            if word_morphing.normal_form in upper_list:
                msg_words[word_inx] = word.capitalize()

        if msg_words[0][0].lower() in LANGUAGES_SUPPORTED[used_lang].lower():
            msg_words[0] = msg_words[0].capitalize()

        return " ".join(msg_words)


print(f"\n\n{figlet_format('RantoVox', font = 'Doom')}")


# NOTE - Creating logs and loading .env
SetLogLevel(-1)
logger.add('LOGS.log', rotation='512 MB')
print(f"Developed by Ggorets0dev, original GitHub page: https://github.com/Ggorets0dev/RantoVoxBot (version: {CONFIG.get('VERSION')})", end='\n\n')

dotenv_path = os.path.join(DIRNAME, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    logger.error('Could not find environment file in home directory (.env)')
    logger.warning('It is not possible to work without .env file, because the TELEGRAM_TOKEN variable must be declared inside the file for the bot to work')
    exit(1)


# NOTE - Sign in to Telegram
bot = Bot(token=os.environ.get('TELEGRAM_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logger.success('Successfully logged in Telegram')


# NOTE - Check if the keys of the languages are the same and load language models
if not check_locales_equivalence():
    logger.error('A line mismatch is detected in the connected languages')
    exit(1)
else:
    # NOTE - Loading language models
    lang_models = {
        'RUSSIAN': os.path.join(DIRNAME, 'src', 'lang', CONFIG.get('RU_LANG_MODEL_DIRNAME')),
        'ENGLISH': os.path.join(DIRNAME, 'src', 'lang', CONFIG.get('ENG_LANG_MODEL_DIRNAME')),
    }

    for lang in lang_models:
        logger.info(f'{lang} language model is loading into memory, it will take some time...')
        lang_models[lang] = Model(os.path.join(DIRNAME, lang_models[lang]))
        logger.success(f'{lang} language model is loaded successfully')


# NOTE - Cleaning old sound files if they exist
for home_file in os.listdir(DIRNAME):
    if home_file[len(home_file)-4:] in ['.wav', '.ogg']:
        os.remove(os.path.join(DIRNAME, home_file))
        logger.warning(f'Old audio file was found and deleted ({home_file})')


# NOTE - TTS module initialization, trying to find the voices in the system that are specified in the config file
TTS_ENGINE = pyttsx3.init()

male_found, female_found = False, False
all_voices = TTS_ENGINE.getProperty('voices')
for voice in all_voices:
    if voice.name == CONFIG.get('MALE_VOICE_NAME'):
        male_found = True
        TTS_ENGINE.setProperty('voice', voice.id)
    elif voice.name == CONFIG.get('FEMALE_VOICE_NAME'):
        female_found = True
if (male_found is False) or (female_found is False):
    logger.error('Failed to find by name some voices specified in the configuration file')
    exit(1)


@dp.message_handler(commands=['start'], commands_prefix='/')
async def start(message: types.Message, state: FSMContext):
    '''Start a conversation with the bot for the user'''
    await Condition.Req.set()
    await state.update_data(bot_language='RUSSIAN', STTLanguage='RUSSIAN', voice_gender='male')
    await message.answer(LOCALIZATION['RUSSIAN']['start'] + '\n\n\n' + LOCALIZATION['ENGLISH']['start'], parse_mode='HTML')


@dp.message_handler(commands=['help'], commands_prefix='/', state=Condition.Req)
async def help(message: types.Message, state: FSMContext):
    '''Print help about bot commands'''
    full_data = await state.get_data()
    await message.answer(LOCALIZATION[full_data.get('bot_language')]['help'], parse_mode='HTML')


@dp.message_handler(commands=['setvoice'], commands_prefix='/', state=Condition.Req)
async def show_available_voices(message: types.Message, state: FSMContext):
    '''Show available gender of voice'''

    full_data = await state.get_data()
    voice_gender, bot_language = full_data.get('voice_gender'), full_data.get('bot_language')
    voice_name = None

    voice_choice = InlineKeyboardMarkup(row_width=1)
    if voice_gender == 'male':
        voice_choice.insert(InlineKeyboardButton(text=f"👩 {LOCALIZATION[bot_language]['female_button']}", callback_data='femaleVG'))
        voice_name = LOCALIZATION[bot_language]['male_button']
    elif voice_gender == 'female':
        voice_choice.insert(InlineKeyboardButton(text=f"👨 {LOCALIZATION[bot_language]['male_button']}", callback_data='maleVG'))
        voice_name = LOCALIZATION[bot_language]['female_button']
    voice_choice.insert(InlineKeyboardButton(text=f"💢 {LOCALIZATION[bot_language]['cancel_button']}", callback_data='CancelVG'))

    await message.answer(text=LOCALIZATION[bot_language]['voice_gender_choice'].format(voice_name), reply_markup=voice_choice, parse_mode='HTML')


@dp.callback_query_handler(text_contains='VG', state=Condition.Req)
async def set_voice_gender(call: CallbackQuery, state: FSMContext):
    '''Set the gender of voiceover voices'''
    full_data = await state.get_data()
    bot_language = full_data.get('bot_language')
    new_voice_name = None

    voice_gender = call.data[:len(call.data)-2]

    await call.message.delete()
    if voice_gender == 'male':
        await call.message.answer(LOCALIZATION[bot_language]['voice_gender_changed'].format(LOCALIZATION[bot_language]['male_button']), parse_mode='HTML')
        await state.update_data(voice_gender='male')
        new_voice_name = CONFIG.get('MALE_VOICE_NAME')

    elif voice_gender == 'female':
        await call.message.answer(LOCALIZATION[bot_language]['voice_gender_changed'].format(LOCALIZATION[bot_language]['female_button']), parse_mode='HTML')
        await state.update_data(voice_gender='female')
        new_voice_name = CONFIG.get('FEMALE_VOICE_NAME')

    else:
        return await call.message.answer(LOCALIZATION[bot_language]['voice_gender_left'], parse_mode='HTML')

    AVAILABLE_VOICES = TTS_ENGINE.getProperty('voices')
    for voice in AVAILABLE_VOICES:
        if voice.name == new_voice_name:
            TTS_ENGINE.setProperty('voice', voice.id)
            break


@dp.message_handler(commands=['setlang'], commands_prefix='/', state=Condition.Req)
async def show_available_stt_langs(message: types.Message, state: FSMContext):
    '''Show the user a list of languages available for recognition'''

    full_data = await state.get_data()
    stt_lang, bot_language = full_data.get('STTLanguage'), full_data.get('bot_language')
    stt_lang_using_now = None

    lang_choice = InlineKeyboardMarkup(row_width=1)
    if stt_lang == 'ENGLISH':
        lang_choice.insert(InlineKeyboardButton(text=f"🇷🇺 {LOCALIZATION[bot_language]['russian_button']}", callback_data='RussianSTTL'))
        stt_lang_using_now = LOCALIZATION[bot_language]['english_button']
    elif stt_lang == 'RUSSIAN':
        lang_choice.insert(InlineKeyboardButton(text=f"🇺🇸 {LOCALIZATION[bot_language]['english_button']}", callback_data='EnglishSTTL'))
        stt_lang_using_now = LOCALIZATION[bot_language]['russian_button']
    lang_choice.insert(InlineKeyboardButton(text=f"💢 {LOCALIZATION[bot_language]['cancel_button']}", callback_data='CancelSTTL'))

    await message.answer(text=LOCALIZATION[bot_language]['stt_lang_choice'].format(stt_lang_using_now), reply_markup=lang_choice)


@dp.callback_query_handler(text_contains='STTL', state=Condition.Req)
async def set_stt_lang(call: CallbackQuery, state: FSMContext):
    '''Set the language that will be detected when it is recognized'''
    full_data = await state.get_data()
    bot_language = full_data.get('bot_language')

    stt_lang = call.data[:len(call.data)-4]

    await call.message.delete()
    if stt_lang != 'Cancel':
        await call.message.answer(text=LOCALIZATION[bot_language]['stt_lang_changed'].format(LOCALIZATION[bot_language][f"{stt_lang.lower()}_button"]), parse_mode='HTML')
        await state.update_data(STTLanguage=stt_lang.upper())

    else:
        return await call.message.answer(text=LOCALIZATION[bot_language]['stt_lang_left'], parse_mode='HTML')
    

@dp.message_handler(commands=['setlocale'], commands_prefix='/', state=Condition.Req)
async def show_available_locales(message: types.Message, state: FSMContext):
    '''Display a list of available languages to the user'''
    full_data = await state.get_data()
    bot_language = full_data.get('bot_language')
    bot_lang_using_now = None

    locale_choice = InlineKeyboardMarkup(row_width=1)
    if bot_language == 'ENGLISH':
        locale_choice.insert(InlineKeyboardButton(text=f"🇷🇺 {LOCALIZATION[bot_language]['russian_button']}", callback_data='RussianBOTL'))
        bot_lang_using_now = LOCALIZATION[bot_language]['english_button']
    elif bot_language == 'RUSSIAN':
        locale_choice.insert(InlineKeyboardButton(text=f"🇺🇸 {LOCALIZATION[bot_language]['english_button']}", callback_data='EnglishBOTL'))
        bot_lang_using_now = LOCALIZATION[bot_language]['russian_button']
    locale_choice.insert(InlineKeyboardButton(text=f"💢 {LOCALIZATION[bot_language]['cancel_button']}", callback_data='CancelBOTL'))

    await message.answer(text=LOCALIZATION[bot_language]['bot_locale_choice'].format(bot_lang_using_now), parse_mode='HTML', reply_markup=locale_choice)


@dp.callback_query_handler(text_contains='BOTL', state=Condition.Req)
async def set_bot_locale(call: CallbackQuery, state: FSMContext):
    '''Set the interface language of the bot'''

    full_data = await state.get_data()
    bot_language = full_data.get('bot_language')

    new_bot_locale = call.data[:len(call.data)-4]

    await call.message.delete()
    if new_bot_locale != 'Cancel':
        await call.message.answer(text=LOCALIZATION[new_bot_locale.upper()]['bot_locale_changed'].format(LOCALIZATION[new_bot_locale.upper()][f"{new_bot_locale.lower()}_button"]), parse_mode='HTML')
        await state.update_data(bot_language=new_bot_locale.upper())

    else:
        return await call.message.answer(text=LOCALIZATION[bot_language]['bot_locale_left'], parse_mode='HTML')


@dp.message_handler(state=Condition.Req, content_types=[ContentType.TEXT])
async def perform_tts(message: types.Message, state: FSMContext):
    '''Perform text-to-speech conversion'''

    full_data = await state.get_data()
    bot_language = full_data.get('bot_language')
    
    if '/start' in message.text:
        return await message.answer(LOCALIZATION[bot_language]['start_again'], parse_mode='HTML')

    try:
        req_id = random.randrange(CONFIG.get('MAX_REQUEST_INDEX') + 1)
        while os.path.isfile(os.path.join(DIRNAME, f'VoiceFor{message.from_user.id}_{req_id}.wav')) or os.path.isfile(os.path.join(DIRNAME, f'VoiceFor{message.from_user.id}_{req_id}.ogg')):
            req_id = random.randrange(CONFIG.get('MAX_REQUEST_INDEX') + 1)
        
        TTS_ENGINE.save_to_file(message.text, f'VoiceFor{message.from_user.id}_{req_id}.wav')
        TTS_ENGINE.runAndWait()
    except:
        logger.error(f'Failed to convert text to voice for the user {message.from_user.id}')
        return await message.reply(LOCALIZATION[bot_language]['request_failed'], parse_mode='HTML')
    
    FROM_PATH = os.path.join(DIRNAME, f'VoiceFor{message.from_user.id}_{req_id}.wav')
    TO_PATH = os.path.join(DIRNAME, f'VoiceFor{message.from_user.id}_{req_id}.ogg')

    # NOTE - FFMPEG WAV -> OGG
    try:
        cmd = f'ffmpeg -i {FROM_PATH} -acodec libvorbis {TO_PATH}'
        DEVNULL = os.open(os.devnull, os.O_WRONLY)
        subprocess.run(cmd,stdout=DEVNULL,stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        os.remove(FROM_PATH)
        logger.error(f'An error occurred while converting a voice message from a user {message.from_user.id}, check if ffmpeg is correctly installed in the system')
        return await message.reply(LOCALIZATION[bot_language]['request_failed'], parse_mode='HTML')

    await bot.send_voice(message.chat.id, open(TO_PATH, 'rb'), reply_to_message_id=message.message_id)
    
    if (message.from_user.username):
        logger.success(f"Performed TTS request for a user {message.from_user.username}#{message.from_user.id}")
    else:
        logger.success(f"Performed TTS request for a user {message.from_user.id}")

    os.remove(TO_PATH)
    os.remove(FROM_PATH)


@dp.message_handler(state=Condition.Req, content_types=[ContentType.VOICE])
async def perform_stt(message: types.Message, state: FSMContext):
    '''Perform speech-to-text conversion'''

    full_data = await state.get_data()
    stt_language, bot_language = full_data.get('STTLanguage'), full_data.get('bot_language')

    voice_msg = await message.voice.get_file()

    req_id = random.randrange(CONFIG.get('MAX_REQUEST_INDEX')  + 1)
    while os.path.isfile(os.path.join(DIRNAME, f'VoiceFrom{message.from_user.id}_{req_id}.ogg')) or os.path.isfile(os.path.join(DIRNAME, f'VoiceFrom{message.from_user.id}_{req_id}.wav')):
        req_id = random.randrange(CONFIG.get('MAX_REQUEST_INDEX')  + 1)

    FROM_PATH = os.path.join(DIRNAME, f'VoiceFrom{message.from_user.id}_{req_id}.ogg')
    TO_PATH = os.path.join(DIRNAME, f'VoiceFrom{message.from_user.id}_{req_id}.wav')
    
    await bot.download_file(file_path=voice_msg.file_path, destination=FROM_PATH)
    
    # NOTE - FFMPEG OGG -> WAV
    try:
        cmd = f'ffmpeg -i {FROM_PATH} -acodec pcm_s16le {TO_PATH}'
        DEVNULL = os.open(os.devnull, os.O_WRONLY)
        subprocess.run(cmd,stdout=DEVNULL,stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        os.remove(FROM_PATH)
        logger.error(f"An error occurred while converting a voice message from a user {message.from_user.id}")
        return await message.reply(LOCALIZATION[bot_language]['request_failed'], parse_mode='HTML')
    
    text_msg = extra_text_processing(msg=recognize_speech(wav_filepath=TO_PATH, lang_model=lang_models[stt_language]), used_lang=stt_language)

    if len(text_msg) < 3:
        logger.error(f'No speech found in a voice message from a user {message.from_user.id}')
        return await message.reply(LOCALIZATION[bot_language]['no_speech_found'], parse_mode='HTML')

    await message.reply(text_msg, parse_mode='HTML')
    
    if (message.from_user.username):
        logger.success(f"Performed STT request for a user {message.from_user.username}#{message.from_user.id}")
    else:
        logger.success(f"Performed STT request for a user {message.from_user.id}")

    os.remove(TO_PATH)
    os.remove(FROM_PATH)


if __name__=='__main__':
    executor.start_polling(dp, skip_updates=True)
