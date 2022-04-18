# RantoVox Telegram Bot
Telegram bot for running **Speech-To-Text (STT)** and **Text-To-Speech (TTS)** queries on *Russian* and *English* languages.

<p align='left'>
   <a href="https://t.me/RantoVoxBot">
       <img height=30 src="https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white"/>
    </a>
</p>



## Tech
---
### **Used modules**

Module for working with Telegram API: [Aiogram](https://pypi.org/project/aiogram/).

Software for converting audio files into different formats: [FFmpeg](https://ffmpeg.org/).

STT and TTS queries are performed using the following libraries:
* [Vosk](https://pypi.org/project/vosk/) (STT)
* [Pyttsx3](https://pypi.org/project/pyttsx3/) (TTS)

RantoVox supports two voices (male and female), whose names are set in the configuration file.

### **Extra Text Processing (ETP)**

RantoVox has a special function called **ExtraTextProcess**, which introduces additional methods of processing text received from [Vosk](https://pypi.org/project/vosk/). By going through it, the text can be made more human and correct in terms of writing. The materials required for this function are stored strictly in the **ETP_materials** folder. 



## Installation
---
> Note: **Requires [Python 3](https://www.python.org/)**

### **Installation manual**

The following steps are required for RantoVox to work correctly:
1) Clone the repository (download source code)
2) Install dependencies using pip with requirments.txt
3) Create your own **.env** file in bot folder with the **TELEGRAM_TOKEN** variable
4) Set preferred voice names in the configuration file (you can see the available ones with [pyttsx3](https://pypi.org/project/pyttsx3/) in your system)
5) Download latest [Vosk](https://pypi.org/project/vosk/) russian and english language models (the small model is more preferable), drop them into bot's home folder and set their's names in configuration file
6) Download and install [FFmpeg](https://ffmpeg.org/) in your system **(don't forget to add it to PATH)**


### **Cloning repository and installing requirments**
```
git clone https://github.com/Ggorets0dev/RantoVoxBot.git
cd RantoVoxBot
pip install -r requirements.txt
```


## Usage
---

### **Commands**

The following commands are available in RantoVox:
* **/start** - Launch a bot for your account
* **/help** - Get an informational summary of the operating principles 
* **/setvoice** - Change voice gender for requests (TTS)
* **/setlang** - Change language for requests (STT)


## Data privacy
---
*RantoVox deletes all temporary files immediately after a TTS or STT request. All conversion is done on the host with the help of the libraries described above. Only user's **Telegram ID** is recorded in logs when requesting, composition of his request remains hidden to host.*