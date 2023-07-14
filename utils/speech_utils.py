'''Functions for working with speech'''

import json
import wave
from os import path

from vosk import KaldiRecognizer, Model


def recognize_speech(wav_filepath: str, lang_model: Model) -> str:
    '''Recognize speech in a wav file using the vosk model and return the text'''
    if not path.isfile(wav_filepath):
        return ''

    wav_file = wave.open(wav_filepath, 'rb')
    recog = KaldiRecognizer(lang_model, wav_file.getframerate())

    result_text = ''
    last_char = False

    while True:
        data_frame = wav_file.readframes(wav_file.getnframes())
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
