# Download the language models and place them in the src/lang folder
download:
	@echo Loading of the --English-- language model ~small~ is started
	curl -O https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
	mv vosk-model-small-en-us-0.15.zip src/lang
	cd src/lang; tar xf vosk-model-small-en-us-0.15.zip; rm vosk-model-small-en-us-0.15.zip
	@echo Loading of the --English-- language model ~small~ is completed
	@echo Loading of the --Russian-- language model ~small~ is started
	curl -O https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
	mv vosk-model-small-ru-0.22.zip src/lang
	cd src/lang; tar xf vosk-model-small-ru-0.22.zip; rm vosk-model-small-ru-0.22.zip
	@echo Loading of the --Russian-- language model ~small~ is completed
	@echo Set vosk-model-small-en-us-0.15.zip and vosk-model-small-ru-0.22.zip to ENV