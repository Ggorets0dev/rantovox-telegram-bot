# RantoVox (Telegram bot)

Telegram bot based on Python 3.11 for running **Speech-To-Text (STT)** and **Text-To-Speech (TTS)** queries. Languages supported: **Russian**, **English** (queries and interface).

<p align='center'>
       <img height=300 src="src/img/rantovox_github_logo.png"/>
</p>

<p align='center'>
   <a href="https://t.me/RantoVoxBot">
       <img height=35 src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"/>
    </a>
</p>

## Stack

### **Used modules**

Module for working with Telegram API: [Aiogram](https://pypi.org/project/aiogram/).

Software for converting audio files into different formats: [FFmpeg](https://ffmpeg.org/).

STT and TTS queries are performed using the following libraries:

* [Vosk](https://pypi.org/project/vosk/) (STT)
  
* [Pyttsx3](https://pypi.org/project/pyttsx3/) (TTS)

RantoVox supports two voices (male and female), whose names are set in the configuration file.

### **Extra Text Processing (ETP)**

RantoVox has a special function called **extra_text_processing**, which introduces additional methods of processing text received from [Vosk](https://pypi.org/project/vosk/). By going through it, the text can be made more human and correct in terms of writing. The materials required for this function are stored strictly in the **src/etp**.

## Installation

> **Note:** Requires [Python 3.11](https://www.python.org/)

### **Installation manual**

The following steps are required for RantoVox to work correctly:

1) Clone the repository (download source code)

2) Install dependencies using pip with requirements.txt

3) Download latest [vosk](https://pypi.org/project/vosk/) russian and english language models (the small model is more preferable), drop them into **src/lang**

4) Create your own **.env** file in root folder with variables described in **Environment file** section.

5) Download and install [FFmpeg](https://ffmpeg.org/) in your system (don't forget to add it to PATH)

### **Cloning repository and installing requirements**

```bash
git clone https://github.com/Ggorets0dev/RantoVoxBot.git
cd RantoVoxBot
pip install -r requirements.txt
```

## Usage

### **Commands**

The following commands are available in RantoVox:

* **start** - Launch a bot for your account

* **help** - Get an informational summary of the operating principles

* **setlocale** - Set language of bot's interface

* **setvoice** - Set voice gender for requests (TTS)

* **setlang** - Set language for requests (STT)

## Environment file

A **.env** file with the following variables must be created before running the bot:

| Name | Example | Default | Description |
|:-|:-|:-:|:-|
| TELEGRAM_TOKEN | 1234567890:ABCDEFGHIJKLMNOPQRSTUVXYZabcdefghi | - | Access token to the created Telegram bot |
| MALE_VOICE_NAME | Aleskandr | - | Name of the voice to be used in the male voiceover |
| FEMALE_VOICE_NAME | Elena | - | Name of the voice to be used in the female voiceover |
| RU_LANG_MODEL_DIRNAME | vosk-model-small-ru-0.22 | - | Name of folder with Russian language model (should be in src/lang) |
| ENG_LANG_MODEL_DIRNAME | vosk-model-small-en-us-0.15 | - | Name of folder with Russian language model (should be in src/lang) |
| MAX_REQUEST_INDEX | 100 | 1000 | A value from the range 0 - n will be assigned to the temporarily created files (affects the number of simultaneously served clients) |
| ETP_ENABLED | False | True | Whether post processing of the raw text from the conversion will be used |

> **Note:** Default - value that the bot will take on its own if the value is in the wrong format in the environment file

> **Note:** Call the bot for a list of available votes, filling in all remaining variables. It will display a list of available values (be careful: not all voices support Russian and English at the same time)

## Privacy

Bot deletes all temporary files immediately after a TTS or STT request. All conversion is done on the host with the help of the libraries described above. Only user's **Login** and **ID** are recorded in logs when requesting, composition of request remains hidden to host.
