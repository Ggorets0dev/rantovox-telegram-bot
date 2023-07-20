#pylint: disable=invalid-name, line-too-long, trailing-whitespace

'''Functions for working with text'''

import os

from loguru import logger
from pymorphy3 import MorphAnalyzer


def extra_text_processing(msg: str, used_lang: str) -> str:
    '''Process additional text with the help of rules'''

    CWD = os.path.dirname(__file__)
    IS_ETP_ENABLED = os.environ.get('ETP_ENABLED')

    if IS_ETP_ENABLED and IS_ETP_ENABLED == 'False':
        logger.warning('ETP is disabled in the environment file, a raw message is returned')
        return msg
    
    LANGUAGES_SUPPORTED = {
        'RUSSIAN': 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ',
        'ENGLISH': 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    }

    msg, used_lang = msg[1:], used_lang.upper()
    MORPH = MorphAnalyzer()

    if used_lang not in LANGUAGES_SUPPORTED:
        logger.warning('An unknown language was requested in ETP, a raw message is returned')
        return msg

    else:
        msg_words = msg.split(' ')
        upper_list = []

        if used_lang.upper() == 'RUSSIAN':
            RU_NAMES_PATH = os.path.join(CWD, '..', 'src', 'etp', 'russian_names.txt')
            RU_SURNAMES_PATH = os.path.join(CWD, '..', 'src', 'etp', 'russian_surnames.txt')

            # NOTE - Adding russian names to upper case filter
            with open(RU_NAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))
            
            # NOTE - Adding russian surnames to upper case filter
            with open(RU_SURNAMES_PATH, 'r', encoding='UTF-8') as file_r:
                for line in file_r:
                    upper_list.append(line.replace('\n', ''))

        elif used_lang.upper() == 'ENGLISH':
            ENG_NAMES_PATH = os.path.join(CWD, 'src', 'etp', 'english_surnames')

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
    