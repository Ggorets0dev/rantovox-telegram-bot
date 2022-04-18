from aiogram.dispatcher.storage import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ContentType
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import CallbackQuery
from vosk import Model, KaldiRecognizer, SetLogLevel
from loguru import logger
from dotenv import load_dotenv
import os
import pyttsx3
import pyfiglet
import subprocess
import wave
import json
import random
import pymorphy2
import RV_Config as config


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

def ExtraTextProcess(msg : str, lang : str):
    msg, lang = msg[1:], lang.upper()
    
    if lang == 'RUSSIAN':
        alphabet_ru = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ'
        morph = pymorphy2.MorphAnalyzer()
        
        FirstUpperList = []
        names_data = open(os.path.join(os.path.dirname(__file__), 'ETP_materials', config.ETP_Russian_names_filename), "r", encoding='UTF-8').readlines()
        for name in names_data:
            FirstUpperList.append(name[:len(name)-1].lower())
        
        surnames_data = open(os.path.join(os.path.dirname(__file__), 'ETP_materials', config.ETP_Russian_surnames_filename), "r", encoding='UTF-8').readlines()
        for surname in surnames_data:
            FirstUpperList.append(surname[:len(surname)-1].lower())

        msg_words = msg.split(' ')
        for w_i in range(len(msg_words)):
            word = msg_words[w_i]
            word_morphing = morph.parse(word)[0]
            
            if word_morphing.normal_form in FirstUpperList:
                msg_words[w_i] = alphabet_ru[alphabet_ru.lower().index(word[0])] + word[1:]

        if msg_words[0][0].lower() in alphabet_ru.lower():
            msg_words[0] = alphabet_ru[alphabet_ru.lower().index(msg_words[0][0].lower())] + msg_words[0][1:]

        return " ".join(msg_words)
    
    else:
        logger.warning('An unknown language was requested, ETP returned raw message')
        return msg


print(f"\n\n{pyfiglet.figlet_format('RantoVox', font = 'Doom')}")


# Creating logs and loading .env
SetLogLevel(-1)
logger.add('RV_LOGS.log', rotation='1024 MB')

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
logger.success(f'Successfully logged in (version: {config.RV_Version})')


# Loading language models
Lang_models = {
    'RUSSIAN': config.RU_lang_model_dirname,
    'ENGLISH': config.ENG_lang_model_dirname
}

for lang in Lang_models:
    logger.info(f'{lang} language model is loading into memory, it will take some time...')
    Lang_models[lang] = Model(os.path.join(os.path.dirname(__file__), Lang_models[lang]))
    logger.success(f'{lang} language model is loaded successfully')


# Cleaning old sound files if they exist
for home_file in os.listdir(os.path.dirname(__file__)):
    if home_file[len(home_file)-4:] == '.wav' or home_file[len(home_file)-4:] == '.ogg':
        os.remove(os.path.join(os.path.dirname(__file__), home_file))
        logger.warning(f'Old audio file was found and deleted ({home_file})')


# TTS module initialization, trying to find the voices in the system that are specified in the config file
TTS = pyttsx3.init()
MaleFound, FemaleFound = False, False
all_voices = TTS.getProperty('voices')
for voice in all_voices:
    if voice.name == config.male_voice_name:
        MaleFound = True
    elif voice.name == config.female_voice_name:
        FemaleFound = True
if (MaleFound is False) or (FemaleFound is False):
    logger.error('Failed to find by name the some voices specified in the configuration file')
    exit(1)


class Cond(StatesGroup):
    Req = State()


@dp.message_handler(commands=['start'], commands_prefix='/')
async def Start(message: types.Message, state: FSMContext):
    await message.answer("🔥 Добро пожаловать в чат с ботом <b>RantoVox</b>!\n\nДанный проект выполняет запросы конвертирования TTS и SST, для более подробной информации используйте /help", parse_mode='HTML')
    await Cond.Req.set()
    await state.update_data(VoiceGender="Male")
    await state.update_data(STTLanguage="RUSSIAN")


@dp.message_handler(commands=['help'], commands_prefix='/', state=Cond.Req)
async def Help(message: types.Message):
    await message.answer("🔄 <b>Возможности конвертирования:</b>\nТекст ---> Голос <i>(Отправьте текстовое сообщение)</i>\nГолос ---> Текст <i>(Отправьте голосовое сообщение)</i>\n\n 🔐 <b>Конфиденциальность данных: </b> <i>Конвертирование выполняется прямо на хосте RantoVox, поэтому ваши данные не передаются на какие-либо сторонние сервера для обработки и удаляются без возможности восстановления сразу же после выполнения вашего запроса.</i>", parse_mode='HTML')


@dp.message_handler(commands=['setvoice'], commands_prefix='/', state=Cond.Req)
async def ShowAvailableVoices(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    voice_gender = FullData.get("VoiceGender")
    voice_name = "Неизвестно"

    voice_choice = InlineKeyboardMarkup(row_width=1)
    if voice_gender == 'Male':
        voice_choice.insert(InlineKeyboardButton(text='👩 Женский', callback_data='FemaleVG'))
        voice_name = 'Мужской'
    elif voice_gender == 'Female':
        voice_choice.insert(InlineKeyboardButton(text='👨 Мужской', callback_data='MaleVG'))
        voice_name = 'Женский'
    voice_choice.insert(InlineKeyboardButton(text='💢 Отмена', callback_data='CancelVG'))

    await message.answer(text=f'⚙️ Выберите озвучку (Сейчас: {voice_name})', reply_markup=voice_choice)


@dp.callback_query_handler(text_contains='VG', state=Cond.Req)
async def SetVoice(call: CallbackQuery, state: FSMContext):
    voice_gender = call.data[:len(call.data)-2]
    new_voice_name = "Неизвестно"

    await call.message.delete()
    if voice_gender == 'Male':
        await call.message.answer('✅ Голос озвучки успешно изменен на <b>Мужской</b>', parse_mode='HTML')
        await state.update_data(VoiceGender="Male")
        new_voice_name = config.male_voice_name

    elif voice_gender == 'Female':
        await call.message.answer('✅ Голос озвучки успешно изменен на <b>Женский</b>', parse_mode='HTML')
        await state.update_data(VoiceGender="Female")
        new_voice_name = config.female_voice_name

    else:
        return await call.message.answer('💢 <b>Озвучка не была изменена</b>', parse_mode='HTML')


    all_voices = TTS.getProperty('voices')
    for voice in all_voices:
        if voice.name == new_voice_name:
            TTS.setProperty('voice', voice.id)
            break


@dp.message_handler(commands=['setlang'], commands_prefix='/', state=Cond.Req)
async def ShowAvailableLangs(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    stt_lang = FullData.get("STTLanguage")
    stt_lang_called_now = "Неизвестно"

    lang_choice = InlineKeyboardMarkup(row_width=1)
    if stt_lang == 'ENGLISH':
        lang_choice.insert(InlineKeyboardButton(text='🇷🇺 Русский', callback_data='RussianSTTL'))
        stt_lang_called_now = 'Английский'
    elif stt_lang == 'RUSSIAN':
        lang_choice.insert(InlineKeyboardButton(text='🇺🇸 Английский', callback_data='EnglishSTTL'))
        stt_lang_called_now = 'Русский'
    lang_choice.insert(InlineKeyboardButton(text='💢 Отмена', callback_data='CancelSTTL'))

    await message.answer(text=f'⚙️ Выберите язык для запросов Голос-Текст (Сейчас: {stt_lang_called_now})', reply_markup=lang_choice)


@dp.callback_query_handler(text_contains='STTL', state=Cond.Req)
async def SetSTTLang(call: CallbackQuery, state: FSMContext):
    stt_lang = call.data[:len(call.data)-4]

    await call.message.delete()
    if stt_lang == 'Russian':
        await call.message.answer('✅ Язык для запросов Голос-Текст успешно изменен на <b>Русский</b>', parse_mode='HTML')
        await state.update_data(STTLanguage=stt_lang.upper())

    elif stt_lang == 'English':
        await call.message.answer('✅ Язык для запросов Голос-Текст успешно изменен на <b>Английский</b>', parse_mode='HTML')
        await state.update_data(STTLanguage=stt_lang.upper())

    else:
        return await call.message.answer('💢 <b>Язык для запросов Голос-Текст не был изменен</b>', parse_mode='HTML')
    

@dp.message_handler(state=Cond.Req, content_types=[ContentType.TEXT])
async def TTS_REQ(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    voice_gender = FullData.get('VoiceGender')
    
    if '/start' in message.text:
        return await message.answer('✳️ <b>RantoVox</b> уже готов принимать ваши сообщения, повторный запуск не требуется', parse_mode='HTML')

    if voice_gender == 'Male':
        voice_to_use = config.male_voice_name
    elif voice_gender == 'Female':
        voice_to_use = config.female_voice_name


    voices = TTS.getProperty('voices')
    for voice in voices:
        if voice.name == voice_to_use:
            TTS.setProperty('voice', voice.id)
            break

    try:
        req_id = random.randrange(10000)
        TTS.save_to_file(message.text, f'VoiceFor{message.from_user.id}_{req_id}.wav')
        TTS.runAndWait()
    except:
        logger.error(f'Failed to convert text to voice for the user {message.from_user.id}')
        return message.reply('💢 Не удалось преобразовать ваше текстовое сообщение в голосовое, попробуйте повторить свой запрос позднее', parse_mode='HTML')
    
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
        return await message.reply('💢 Не удалось преобразовать ваше текстовое сообщение в голосовое, попробуйте повторить свой запрос позднее', parse_mode='HTML')
    
    await bot.send_voice(message.chat.id, open(ToPath, 'rb'), reply_to_message_id=message.message_id)
    logger.success(f"Performed TTS request for a user {message.from_user.id}")
    os.remove(ToPath)
    os.remove(FromPath)


@dp.message_handler(state=Cond.Req, content_types=[ContentType.VOICE])
async def STT_REQ(message: types.Message, state: FSMContext):
    FullData = await state.get_data()
    
    voice_msg = await message.voice.get_file()

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
        return await message.reply('💢 <b>Произошла ошибка во время конвертирования, попробуйте повторить свой запрос позднее</b>', parse_mode='HTML')
    
    text_msg = ExtraTextProcess(msg=VoskSpeechRecog(wav_filepath=ToPath, lang_model=Lang_models[FullData.get('STTLanguage')]), lang=FullData.get('STTLanguage'))

    os.remove(ToPath)
    os.remove(FromPath)

    if len(text_msg) < 3:
        logger.error(f'No speech found in a voice message from a user {message.from_user.id}')
        return await message.reply('💢 <b>Не удалось распознать речь в данном голосовом сообщении</b>', parse_mode='HTML')

    await message.reply(text_msg, parse_mode='HTML')
    logger.success(f"Performed STT request for a user {message.from_user.id}")


if __name__=='__main__':
    executor.start_polling(dp, skip_updates=True)
