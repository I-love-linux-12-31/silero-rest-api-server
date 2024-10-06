import logging

from fastapi import FastAPI, UploadFile, Header, Request
from fastapi.responses import FileResponse, Response

from swagger_ui import api_doc

from hashlib import md5
import random
import time

import os
import json
from config import get_config

silero_license = os.environ.get("SILERO_LICENCE", False)
if not silero_license:
    print(
        "This software runs Silero TTS Models,"
        " that distributed by CC BY-NC-SA license."
        " (github.com/snakers4/silero-models).\n"
        " You need to accept license to use this models!"
    )
    print("If you accept license add SILERO_LICENCE=1 to app environment. Now server works in offline mode.")
    get_config()["offline_mode"] = True

from tts import Model, models, get_tts
import admin

app = FastAPI()

admin.generate_passwd()


def get_languages() -> set:
    """Returns list of available languages"""
    _languages = set()
    for model in models.keys():
        if model.endswith(".pt"):
            lang = model[:-3]
        else:
            lang = model
        lang = lang.split('_')[1]
        if lang.isalpha():
            _languages.add(lang)
    return _languages


@app.get("/api/languages")
def languages(tts_name="silero") -> list:
    """"Get languages list endpoint"""
    if tts_name not in "silero":
        return []
    return list(sorted(get_languages()))


@app.get("/api/voices")
def languages(language="", locale="", gender="", tts_name="silero") -> dict:
    """Get voices list endpoint"""
    result = dict()
    if tts_name not in "silero":
        return result
    voices = get_voices()

    for voice_title in voices:
        voice = voices[voice_title]
        add = True
        if (language not in voice["language"] or
                locale not in voice["locale"] or
                gender not in voice["gender"]):
            add = False
        if add:
            result[voice_title] = voice

    return result


def get_local_voices() -> dict:
    """This function collecting info about available voices from every local model."""
    result = dict()
    _tts = get_tts()
    for file_name in os.listdir("models"):
        try:
            if file_name in _tts.models:
                model = _tts.models[file_name]
            else:
                model = Model(file_name)
                if file_name.endswith(".pt"):
                    _tts.models[file_name[:-3]] = model
                else:
                    _tts.models[file_name[:-3]] = model

        except Exception as e:
            logging.warning(f"Error while loading model: {file_name}. File not found or model not supported!")
            continue
        try:
            speakers = model.get_speakers()
        except AttributeError:
            # Not supported model
            continue
        for name in speakers:
            block = dict()
            block["gender"] = '?'
            block["id"] = name

            if file_name.endswith(".pt"):
                lang = file_name[:-3]
            else:
                lang = file_name

            split_filename = lang.split('_')
            if split_filename[-2].isalpha():
                lang = split_filename[-2]
                block["language"] = lang
                block["locale"] = f"{lang}-{split_filename[-1]}"
            else:
                lang = split_filename[-1]
                block["language"] = split_filename[-1]
                block["locale"] = f"{lang}-{lang}"

            if len(block["language"]) > 3:
                block["multispeaker"] = True
            else:
                block["multispeaker"] = False

            block['name'] = name
            block["speakers"] = None
            block["tag"] = None

            model_name = file_name
            if file_name.endswith(".pt"):
                model_name = file_name[:-3]

            block["tts_name"] = model_name

            result[f"{model_name}:{name}"] = block
    return result


def get_voices() -> dict:
    """
    Function for loading list of speakers.

    Output example:
    {
        "v4_ru:aidar": {
            "gender": "?",
            "id": "aidar",
            "language": "ru",
            "locale": "ru-ru",
            "multispeaker": false,
            "name": "aidar",
            "speakers": null,
            "tag": null,
            "tts_name": "v4_ru"
        },
    }

    """
    if get_config()["update_voices"]:
        speakers = get_local_voices()
        get_config()["update_voices"] = False
        with open("speakers.json", "wt") as f:
            json.dump(speakers, f)
    else:
        if os.path.exists('speakers.json'):
            with open('speakers.json', 'r') as f:
                speakers = json.load(f)
        else:
            speakers = get_local_voices()

    return speakers


@app.get("/api/tts")
def tts(
        voice: str = None,
        text: str = None,
        token=None,
        vocoder="",
        denoiserStrength=0.03,
        cache=False
) -> Response:
    """Generate audio endpoint"""
    if voice is None or text is None or not text.strip():
        return Response(status_code=412)
    if token is None:
        token = md5(str(random.randint(13, 128) ** random.randint(1, 6)).encode()).hexdigest()
    try:
        tts_api = get_tts()
        path = tts_api.generate(voice, text, seswsion=token)
        return FileResponse(
            path=path,
            filename=f"{token}.wav",
        )
    except Exception as e:
        logging.warning(f"Unknown error at /api/tts. {e} : {e.__class__.__name__}")
        return Response(status_code=500)


@app.post("/upload_model/")
async def upload_file(request: Request, file: UploadFile) -> Response:
    """Upload custom model file endpoint"""
    api_key = request.headers.get('api_key')
    if not admin.is_valid(api_key):
        return Response(status_code=403)

    file_path = os.path.join("models", file.filename)

    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    return Response(status_code=202)


@app.delete("/remove_file_cache/")
async def remove_file_cache(request: Request) -> Response or dict:
    """Remove old cache files endpoint"""
    api_key = request.headers.get('api_key')
    if not admin.is_valid(api_key):
        return Response(status_code=403)

    current_time = time.time()
    files_deleted = 0
    folders_deleted = 0
    for root, dirs, files in os.walk("sessions", topdown=False):
        for file in files:
            file_path = os.path.join(root, file)

            last_access_time = os.path.getatime(file_path)

            if current_time - last_access_time > 15 * 60:
                os.remove(file_path)
                files_deleted += 1

        if not os.listdir(root):
            if root == "sessions":
                continue
            os.rmdir(root)
            folders_deleted += 1

    return {
        "folders_deleted": folders_deleted, "files_deleted": files_deleted
    }


# Swagger UI
api_doc(app, config_path="swagger.yaml", url_prefix="/openapi", title="silero-tts-rest-api")
