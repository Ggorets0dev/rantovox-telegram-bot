'''Vocabulary with localization of interface'''

LOCALIZATION = {
    "RUSSIAN": {
        "start": "🔥 Добро пожаловать в чат с ботом <b>RantoVox</b>!\n\nДанный проект выполняет запросы конвертирования TTS и SST, для более подробной информации используйте /help",
        "start_again": "✳️ <b>RantoVox</b> уже готов принимать ваши сообщения, повторный запуск не требуется",
        "help": "🔄 <b>Возможности конвертирования:</b>\nТекст ---> Голос <i>(Отправьте текстовое сообщение)</i>\nГолос ---> Текст <i>(Отправьте голосовое сообщение)</i>\n\n 🔐 <b>Конфиденциальность данных:</b>\n<i>Конвертирование выполняется прямо на хосте RantoVox, поэтому ваши данные не передаются на какие-либо сторонние сервера для обработки и удаляются без возможности восстановления сразу же после выполнения вашего запроса</i>",
        "stt_lang_choice": "⚙️ Выберите язык для запросов Голос-Текст (Сейчас: {})",
        "stt_lang_changed": "✅ Язык для запросов Голос-Текст успешно изменен на <b>{}</b>",
        "stt_lang_left": "💢 <b>Язык для запросов Голос-Текст не был изменен</b>",
        "voice_gender_choice": "⚙️ Выберите пол озвучки (Сейчас: {})",
        "voice_gender_changed": "✅ Голос озвучки успешно изменен на <b>{}</b>",
        "voice_gender_left": "💢 <b>Озвучка не была изменена</b>",
        "bot_locale_choice": "⚙️ Выберите язык интерфейса (Сейчас: {})",
        "bot_locale_changed": "✅ Язык интерфейса изменен на <b>{}</b>",
        "bot_locale_left": "💢 <b>Язык интерфейса не был изменен</b>",
        "request_failed": "💢 <b>Не удалось выполнить преобразование, попробуйте повторить свой запрос позже или проверьте, корректно ли установлен ffmpeg в системе</b>",
        "no_speech_found": "💢 <b>Не удалось распознать речь в данном голосовом сообщении</b>",
        
        "female_button": "Женский",
        "male_button": "Мужской",
        "russian_button": "Русский",
        "english_button": "Англиский",
        "cancel_button": "Отмена"
    },
    "ENGLISH": {
        "start": "🔥 Welcome to chat with the bot <b>RantoVox</b>!\n\nThis project performs TTS and SST conversions, for more information use /help",
        "start_again": "✳️ <b>RantoVox</b> is ready to receive your messages, no need to start it again",
        "help": "🔄 <b>Conversion possibilities:</b>\nText ---> Voice<i> (Send text message)</i>\nVoice ---> Text<i> (Send voice message)</i>\n\n 🔐 <b>Data privacy:</b>\n<i>Conversion is performed directly on the RantoVox host, so your data is not sent to any third-party servers for processing and is deleted without possibility of recovery immediately after your request</i>",
        "stt_lang_choice": "⚙️ Select a language for Speech-to-Text queries (Now: {})",
        "stt_lang_changed": "✅ Language for Speech-to-Text queries has been successfully changed to <b>{}</b>",
        "stt_lang_left": "💢 <b>Language for Speech-to-Text queries has not been changed</b>",
        "voice_gender_choice": "⚙️ Select a gender of voice (Now: {})",
        "voice_gender_changed": "✅ Voiceover has been successfully changed to <b>{}</b>",
        "voice_gender_left": "💢 <b>Sounding has not been changed</b>",
        "bot_locale_choice": "⚙️ Select the interface language (Now: {})",
        "bot_locale_changed": "✅ Interface language has been changed to <b>{}</b>",
        "bot_locale_left": "💢 <b>Interface language has not been changed</b>",
        "request_failed": "💢 <b>Conversion failed, please try to repeat it again later or check if ffmpeg is correctly installed in the system</b>",
        "no_speech_found": "💢 <b>Failure to recognize speech in this voice message</b>",
        
        "female_button": "Female",
        "male_button": "Male",
        "russian_button": "Russian",
        "english_button": "English",
        "cancel_button": "Cancel"
    }
}


# NOTE - Check for identical keys in all languages
def check_locales_equivalence() -> bool:
    '''Check if the keys in the languages match (in order)'''
    
    first_locale_keys = list(LOCALIZATION[list(LOCALIZATION.keys())[0]].keys())
    for locale in LOCALIZATION:
        if list(LOCALIZATION[locale].keys()) != first_locale_keys:
            return False
    return True
