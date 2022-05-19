from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType, CallbackQuery
from aiogram import Bot, Dispatcher, executor, types
from vosk import Model, KaldiRecognizer, SetLogLevel
from loguru import logger
from dotenv import load_dotenv
import os
import sys
import pyttsx3
import pyfiglet
import subprocess
import wave
import json
import random
import pymorphy2
import config

sys.path.append(os.path.join(os.path.dirname(__file__), 'lang_materials'))
import localization as Locale



def VoskSpeechRecog(wav_filepath, lang_model):
    if not(os.path.isfile(wav_filepath)): 
        return ''

    wf = wave.open(wav_filepath, 'rb')
    recog = KaldiRecognizer(lang_model, wf.getframerate())

    result_text = ''
    last_chr = False

    while True:
        data_frame = wf.readframes(wf.getnframes())
        if len(data_frame) == 0:
            break

        elif recog.AcceptWaveform(data_frame):
            res = json.loads(recog.Result())

            if res['text'] != '':
                result_text += f" {res['text']}"
                last_chr = False
            elif not last_chr:
                result_text += '\n'
                last_chr = True

    res = json.loads(recog.FinalResult())
    result_text += f" {res['text']}"

    return result_text

def ExtraTextProcessing(msg : str, lang : str):
    if not(config.ETP_Enabled):
        logger.warning('ETP is disabled in the configuration file, a raw message is returned')
        return msg
    
    Languages_Supported = {
        'RUSSIAN': 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
        'ENGLISH': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    }

    msg, lang = msg[1:], lang.upper()
    morph = pymorphy2.MorphAnalyzer()

    if lang not in list(Languages_Supported.keys()):
        logger.warning('An unknown language was requested in ETP, a raw message is returned')
        return msg

    else:
        msg_words = msg.split(' ')
        FirstUpperList = []

        if lang == 'RUSSIAN':
            names_data = open(os.path.join(os.path.dirname(__file__), 'ETP_materials', config.ETP_Russian_names_filename), "r", encoding='UTF-8').readlines()
            for name in names_data:
                FirstUpperList.append(name[:len(name)-1].lower())
            
            surnames_data = open(os.path.join(os.path.dirname(__file__), 'ETP_materials', config.ETP_Russian_surnames_filename), "r", encoding='UTF-8').readlines()
            for surname in surnames_data:
                FirstUpperList.append(surname[:len(surname)-1].lower())


        elif lang == 'ENGLISH':
            names_data = open(os.path.join(os.path.dirname(__file__), 'ETP_materials', config.ETP_English_names_filename), "r", encoding='UTF-8').readlines()
            for name in names_data:
                FirstUpperList.append(name[:len(name)-1].lower())


        for w_i in range(len(msg_words)):
            word = msg_words[w_i]
            word_morphing = morph.parse(word)[0]
            
            if word_morphing.normal_form in FirstUpperList:
                msg_words[w_i] = word[0].upper() + word[1:]

        if msg_words[0][0].lower() in Languages_Supported[lang].lower():
            msg_words[0] = msg_words[0][0].upper() + msg_words[0][1:]

        return " ".join(msg_words)


print(f"\n\n{pyfiglet.figlet_format('RantoVox', font = 'Doom')}")


# Creating logs and loading .env
SetLogLevel(-1)
logger.add('RV_LOGS.log', rotation='1024 MB')
print(f'Developed by Ggorets0dev, original GitHub page: https://github.com/Ggorets0dev/RantoVoxBot (version: {config.RV_Version})', end='\n\n')

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    logger.error('Could not find environment file in home directory (.env)')
    logger.warning('It is not possible to work without .env file, because the TELEGRAM_TOKEN variable must be declared inside the file for the bot to work')
    exit(1)


# Sign in to Telegram
bot = Bot(token=os.environ.get('TELEGRAM_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logger.success('Successfully logged in Telegram')


# Loading language models
Lang_models = {
    'RUSSIAN': os.path.join(os.path.dirname(__file__), 'lang_materials', config.RU_lang_model_dirname),
    'ENGLISH': os.path.join(os.path.dirname(__file__), 'lang_materials', config.ENG_lang_model_dirname),
}

for lang in Lang_models:
    logger.info(f'{lang} language model is loading into memory, it will take some time...')
    Lang_models[lang] = Model(os.path.join(os.path.dirname(__file__), Lang_models[lang]))
    logger.success(f'{lang} language model is loaded successfully')


# Cleaning old sound files if they exist
for home_file in os.listdir(os.path.dirname(__file__)):
    if home_file[len(home_file)-4:] in ['.wav', '.ogg']:
        os.remove(os.path.join(os.path.dirname(__file__), home_file))
        logger.warning(f'Old audio file was found and deleted ({home_file})')


# TTS module initialization, trying to find the voices in the system that are specified in the config file
TTS = pyttsx3.init()
MaleFound, FemaleFound = False, False
all_voices = TTS.getProperty('voices')
for voice in all_voices:
    if voice.name == config.male_voice_name:
        MaleFound = True
        TTS.setProperty('voice', voice.id)
    elif voice.name == config.female_voice_name:
        FemaleFound = True
if (MaleFound is False) or (FemaleFound is False):
    logger.error('Failed to find by name the some voices specified in the configuration file')
    exit(1)


class Cond(StatesGroup):
    Req = State()


@dp.message_handler(commands=['start'], commands_prefix='/')
async def Start(message: types.Message, state: FSMContext):
    await Cond.Req.set()
    await state.update_data(BOTLanguage='RUSSIAN', STTLanguage='RUSSIAN', VoiceGender='Male')
    
    await message.answer(Locale.localization['RUSSIAN']['start'] + '\n\n\n' + Locale.localization['ENGLISH']['start'], parse_mode='HTML')


@dp.message_handler(commands=['help'], commands_prefix='/', state=Cond.Req)
async def Help(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    await message.answer(Locale.localization[FullData.get('BOTLanguage')]['help'], parse_mode='HTML')


@dp.message_handler(commands=['setvoice'], commands_prefix='/', state=Cond.Req)
async def ShowAvailableVoices(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    voice_gender, bot_language = FullData.get('VoiceGender'), FullData.get('BOTLanguage')
    voice_name = 'Unknown'

    voice_choice = InlineKeyboardMarkup(row_width=1)
    if voice_gender == 'Male':
        voice_choice.insert(InlineKeyboardButton(text=f"👩 {Locale.localization[bot_language]['female_button']}", callback_data='FemaleVG'))
        voice_name = Locale.localization[bot_language]['male_button']
    elif voice_gender == 'Female':
        voice_choice.insert(InlineKeyboardButton(text=f"👨 {Locale.localization[bot_language]['male_button']}", callback_data='MaleVG'))
        voice_name = Locale.localization[bot_language]['female_button']
    voice_choice.insert(InlineKeyboardButton(text=f"💢 {Locale.localization[bot_language]['cancel_button']}", callback_data='CancelVG'))

    await message.answer(text=Locale.localization[bot_language]['voice_gender_choice'].format(voice_name), reply_markup=voice_choice, parse_mode='HTML')


@dp.callback_query_handler(text_contains='VG', state=Cond.Req)
async def SetVoice(call: CallbackQuery, state: FSMContext):
    FullData = await state.get_data()
    bot_language = FullData.get('BOTLanguage')
    new_voice_name = 'Unknown'

    voice_gender = call.data[:len(call.data)-2]

    await call.message.delete()
    if voice_gender == 'Male':
        await call.message.answer(Locale.localization[bot_language]['voice_gender_changed'].format(Locale.localization[bot_language]['male_button']), parse_mode='HTML')
        await state.update_data(VoiceGender='Male')
        new_voice_name = config.male_voice_name

    elif voice_gender == 'Female':
        await call.message.answer(Locale.localization[bot_language]['voice_gender_changed'].format(Locale.localization[bot_language]['female_button']), parse_mode='HTML')
        await state.update_data(VoiceGender='Female')
        new_voice_name = config.female_voice_name

    else:
        return await call.message.answer(Locale.localization[bot_language]['voice_gender_left'], parse_mode='HTML')


    all_voices = TTS.getProperty('voices')
    for voice in all_voices:
        if voice.name == new_voice_name:
            TTS.setProperty('voice', voice.id)
            break


@dp.message_handler(commands=['setlang'], commands_prefix='/', state=Cond.Req)
async def ShowAvailableSTTLangs(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    stt_lang, bot_language = FullData.get('STTLanguage'), FullData.get('BOTLanguage')
    stt_lang_using_now = "Unknown"

    lang_choice = InlineKeyboardMarkup(row_width=1)
    if stt_lang == 'ENGLISH':
        lang_choice.insert(InlineKeyboardButton(text=f"🇷🇺 {Locale.localization[bot_language]['russian_button']}", callback_data='RussianSTTL'))
        stt_lang_using_now = Locale.localization[bot_language]['english_button']
    elif stt_lang == 'RUSSIAN':
        lang_choice.insert(InlineKeyboardButton(text=f"🇺🇸 {Locale.localization[bot_language]['english_button']}", callback_data='EnglishSTTL'))
        stt_lang_using_now = Locale.localization[bot_language]['russian_button']
    lang_choice.insert(InlineKeyboardButton(text=f"💢 {Locale.localization[bot_language]['cancel_button']}", callback_data='CancelSTTL'))

    await message.answer(text=Locale.localization[bot_language]['stt_lang_choice'].format(stt_lang_using_now), reply_markup=lang_choice)


@dp.callback_query_handler(text_contains='STTL', state=Cond.Req)
async def SetSTTLang(call: CallbackQuery, state: FSMContext):
    FullData = await state.get_data()
    bot_language = FullData.get('BOTLanguage')

    stt_lang = call.data[:len(call.data)-4]

    await call.message.delete()
    if stt_lang != 'Cancel':
        await call.message.answer(text=Locale.localization[bot_language]['stt_lang_changed'].format(Locale.localization[bot_language][f"{stt_lang.lower()}_button"]), parse_mode='HTML')
        await state.update_data(STTLanguage=stt_lang.upper())

    else:
        return await call.message.answer(text=Locale.localization[bot_language]['stt_lang_left'], parse_mode='HTML')
    

@dp.message_handler(commands=['setlocale'], commands_prefix='/', state=Cond.Req)
async def ShowAvailableLocales(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    bot_language = FullData.get('BOTLanguage')
    bot_lang_using_now = 'Unknown'

    locale_choice = InlineKeyboardMarkup(row_width=1)
    if bot_language == 'ENGLISH':
        locale_choice.insert(InlineKeyboardButton(text=f"🇷🇺 {Locale.localization[bot_language]['russian_button']}", callback_data='RussianBOTL'))
        bot_lang_using_now = Locale.localization[bot_language]['english_button']
    elif bot_language == 'RUSSIAN':
        locale_choice.insert(InlineKeyboardButton(text=f"🇺🇸 {Locale.localization[bot_language]['english_button']}", callback_data='EnglishBOTL'))
        bot_lang_using_now = Locale.localization[bot_language]['russian_button']
    locale_choice.insert(InlineKeyboardButton(text=f"💢 {Locale.localization[bot_language]['cancel_button']}", callback_data='CancelBOTL'))

    await message.answer(text=Locale.localization[bot_language]['bot_locale_choice'].format(bot_lang_using_now), parse_mode='HTML', reply_markup=locale_choice)


@dp.callback_query_handler(text_contains='BOTL', state=Cond.Req)
async def SetBotLocale(call: CallbackQuery, state: FSMContext):
    FullData = await state.get_data()
    bot_language = FullData.get('BOTLanguage')

    new_bot_locale = call.data[:len(call.data)-4]

    await call.message.delete()
    if new_bot_locale != 'Cancel':
        await call.message.answer(text=Locale.localization[new_bot_locale.upper()]['bot_locale_changed'].format(Locale.localization[new_bot_locale.upper()][f"{new_bot_locale.lower()}_button"]), parse_mode='HTML')
        await state.update_data(BOTLanguage=new_bot_locale.upper())

    else:
        return await call.message.answer(text=Locale.localization[bot_language]['bot_locale_left'], parse_mode='HTML')


@dp.message_handler(state=Cond.Req, content_types=[ContentType.TEXT])
async def TTS_REQ(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    bot_language = FullData.get('BOTLanguage')
    
    if '/start' in message.text:
        return await message.answer(Locale.localization[bot_language]['start_again'], parse_mode='HTML')

    try:
        req_id = random.randrange(10000+1)
        while os.path.isfile(os.path.join(os.path.dirname(__file__), f'VoiceFor{message.from_user.id}_{req_id}.wav')) or os.path.isfile(os.path.join(os.path.dirname(__file__), f'VoiceFor{message.from_user.id}_{req_id}.ogg')):
            req_id = random.randrange(10000+1)
        
        TTS.save_to_file(message.text, f'VoiceFor{message.from_user.id}_{req_id}.wav')
        TTS.runAndWait()
    except:
        logger.error(f'Failed to convert text to voice for the user {message.from_user.id}')
        return await message.reply(Locale.localization[bot_language]['request_failed'], parse_mode='HTML')
    
    FromPath = os.path.join(os.path.dirname(__file__), f'VoiceFor{message.from_user.id}_{req_id}.wav')
    ToPath = os.path.join(os.path.dirname(__file__), f'VoiceFor{message.from_user.id}_{req_id}.ogg')

    # FFMPEG WAV -> OGG
    try:
        cmd = f'ffmpeg -i {FromPath} -acodec libvorbis {ToPath}'
        DEVNULL = os.open(os.devnull, os.O_WRONLY)
        subprocess.run(cmd,stdout=DEVNULL,stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        os.remove(FromPath)
        logger.error(f'An error occurred while converting a voice message from a user {message.from_user.id}')
        return await message.reply(Locale.localization[bot_language]['request_failed'], parse_mode='HTML')
    
    await bot.send_voice(message.chat.id, open(ToPath, 'rb'), reply_to_message_id=message.message_id)
    logger.success(f"Performed TTS request for a user {message.from_user.id}")
    os.remove(ToPath)
    os.remove(FromPath)


@dp.message_handler(state=Cond.Req, content_types=[ContentType.VOICE])
async def STT_REQ(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    stt_language, bot_language = FullData.get('STTLanguage'), FullData.get('BOTLanguage')

    voice_msg = await message.voice.get_file()

    req_id = random.randrange(10000+1)

    while os.path.isfile(os.path.join(os.path.dirname(__file__), f'VoiceFrom{message.from_user.id}_{req_id}.ogg')) or os.path.isfile(os.path.join(os.path.dirname(__file__), f'VoiceFrom{message.from_user.id}_{req_id}.wav')):
        req_id = random.randrange(10000+1)

    FromPath = os.path.join(os.path.dirname(__file__), f'VoiceFrom{message.from_user.id}_{req_id}.ogg')
    ToPath = os.path.join(os.path.dirname(__file__), f'VoiceFrom{message.from_user.id}_{req_id}.wav')
    
    await bot.download_file(file_path=voice_msg.file_path, destination=FromPath)
    
    # FFMPEG OGG -> WAV
    try:
        cmd = f'ffmpeg -i {FromPath} -acodec pcm_s16le {ToPath}'
        DEVNULL = os.open(os.devnull, os.O_WRONLY)
        subprocess.run(cmd,stdout=DEVNULL,stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
    except:
        os.remove(FromPath)
        logger.error(f"An error occurred while converting a voice message from a user {message.from_user.id}")
        return await message.reply(Locale.localization[bot_language]['request_failed'], parse_mode='HTML')
    
    text_msg = ExtraTextProcessing(msg=VoskSpeechRecog(wav_filepath=ToPath, lang_model=Lang_models[stt_language]), lang=stt_language)

    os.remove(ToPath)
    os.remove(FromPath)

    if len(text_msg) < 3:
        logger.error(f'No speech found in a voice message from a user {message.from_user.id}')
        return await message.reply(Locale.localization[bot_language]['no_speech_found'], parse_mode='HTML')

    await message.reply(text_msg, parse_mode='HTML')
    logger.success(f"Performed STT request for a user {message.from_user.id}")


if __name__=='__main__':
    executor.start_polling(dp, skip_updates=True)
