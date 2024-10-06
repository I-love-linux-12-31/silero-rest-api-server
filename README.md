# Rest API server for Silero TTS
Server for running Silero TTS models (or other compatible models) with OpenTTS-like API. 
This server allows users to generate speech using different models and provides an easy-to-use REST API.

## Features
- Generate speech from text using multiple TTS models.
- Support for custom model uploads.
- OpenAPI documentation available.
- Full OpenTTS API compatibility

## Supported languages:
* 🇩🇪 German (de)
* 🇬🇧 English (en)
* 🇪🇸 Spanish (es)
* 🇫🇷 French (fr)
* 🇮🇳 Indic scripts (indic)
* 🇷🇺 Russian (ru)
* 🇷🇺 Tatar (tt)
* 🇺🇦 Ukrainian (ua)
* 🇺🇿 Uzbek (uz)
* 🇷🇺 Kalmyk (xal)
* 🌐 Other cyrillic languages

## Dependencies
* FastAPI
* swagger-ui
* pydub
* PyTorch

## API endpoints
****/api/tts****<br>
Generate speach.<br>
If you use not local model, it will be downloaded automatically.<br>
****/api/languages****<br>
Get available languages list (From only local models!)<br>
****/api/voices****<br>
Get available speakers list (From only local models!)<br>
****/upload_model/****<br>
Upload custom model. Admin auth required!<br>
****/remove_file_cache/****<br>
Remove cached files. Admin auth required!<br>
****/openapi****<br>
OpenAPI docs

For authorization used key in HTTP headers:
api_key: <64-byte token>

More information you can find at /openapi or swagger.yaml

## Licenses

****AGPLv3****

To use Silero models you need to accept Silero's [license](https://github.com/snakers4/silero-models).

## Running in container

### Building image:
```bash
podman build -t silero-rest-api-server:latest .
```

### Container setup
From local image:
```bash
podman run -d --name silero-rest-api-server-container -p 5500:5500 -e SILERO_LICENCE=ACCEPTED silero-rest-api-server
```
From repository:
```bash
podman run -d --name silero-rest-api-server-container -p 5500:5500 -e SILERO_LICENCE=ACCEPTED yaroslavk1231/silero-rest-api-server
```
API KEY
```bash
podman logs silero-rest-api-server-container | grep "API KEY"
```

## How to run

### To setup
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip3 install --no-cache-dir -r requirements.txt
```

### To run
```bash
source venv/bin/activate
SILERO_LICENCE="ACCEPTED" uvicorn main:app --host 0.0.0.0 --port 5500
```

### Usage examples
####  Getting speakers list example
```bash
curl -X 'GET' \
  'http://127.0.0.1:5500/api/voices?language=en&locale=en-indic' \
  -H 'accept: */*'
```

#### Getting languages list example
```bash
curl -X 'GET' \
  'http://127.0.0.1:5500/api/languages' \
  -H 'accept: */*'
```

#### Example of speach generation.
```bash
curl -X 'GET' 'http://127.0.0.1:5500/api/tts?voice=v3_en%3Aen_64&text=Hello%20World%21' -H 'accept: */*' --output test.wav
```
Out: Audio file "test.wav"

#### Model uploading example.
```bash
curl -X POST "http://localhost:5500/upload_model/" -H "Content-Type: multipart/form-data" -H "api_key:<YOUR API KEY>" -F "file=@v3_en.pt"
```


### Config files:
#### config.json
```json
{
  "max_char_length": 600,  # Maximum size of text block. If text is larger than this value, it will be divided to blocks.
  "sample_rate": 48000,  # Sampling rate: 48000 or 24000 or 8000
  "threads_limit": 6,  # Maximum threads usage for models
  "min_model_version": 3,  # Minimum model version (Using models below version 3 may cause problems)

  "offline_mode": false,  # Prohibit server to download new models from models.silero.ai/models/tts
  "update_voices": true  # Save list of local speakers to speakers.json
}
```
#### langs.json
List of official SileroTTS models. Can be updated automatically.  
```json
{
    "model_name.pt": "download_url",
    ...
}
```

### Project structure
* main.py - api server and main functions
* admin.py - functions for admin auth
* config.py - functions for work with config.json 
* tts.py - function for work with models and pytorch

## Used Projects

This project incorporates some code from the [silero-api-server](https://github.com/ouoertheo/silero-api-server)(MIT).

This app downloads add runs [Silero TTS models](https://github.com/snakers4/silero-models) provided by CC-BY-NC(or other) license.