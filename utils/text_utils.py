'''Functions for working with text'''

from os import path

from loguru import logger
from pymorphy3 import MorphAnalyzer

from utils.config_utils import read_config


def extra_text_processing(msg: str, used_lang: str) -> str:
    '''Process additional text with the help of rules'''

    DIRNAME = path.dirname(__file__)
    CONFIG = read_config('config.yaml')

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
            RU_NAMES_PATH = path.join(DIRNAME, '..', 'src', 'etp', CONFIG.get('ETP_RUSSIAN_NAMES_FILENAME'))
            RU_SURNAMES_PATH = path.join(DIRNAME, '..', 'src', 'etp', CONFIG.get('ETP_RUSSIAN_SURNAMES_FILENAME'))

            # NOTE - Adding russian names to upper case filter
            with open(RU_NAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))
            
            # NOTE - Adding russian surnames to upper case filter
            with open(RU_SURNAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))

        elif used_lang.upper() == 'ENGLISH':
            ENG_NAMES_PATH = path.join(DIRNAME, 'src', 'etp', CONFIG.get('ETP_ENGLISH_NAMES_FILENAME'))

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