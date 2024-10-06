import os
import time
import random
import shutil
import requests
import torch
import torch.package
import torchaudio
from hashlib import md5
from logging import getLogger
import logging

from pydub import AudioSegment
from pathlib import Path
import json

from config import get_config

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()

formatter = logging.Formatter('%(levelname)s:     %(message)s')
handler.setFormatter(formatter)

logger.addHandler(handler)

offline_mode = get_config()['offline_mode']

device = torch.device('cpu')
torch.set_num_threads(get_config()["threads_limit"])
torchaudio.set_audio_backend("soundfile")


def list_models():
    """Grab all model links from https://models.silero.ai/models/tts"""
    lang_file = Path('langs.json')
    if lang_file.exists():
        with lang_file.open('r') as fh:
            logger.info('Loading cached language index')
            return json.load(fh)
    logger.info('Loading remote language index')
    lang_base_url = 'https://models.silero.ai/models/tts'
    models = {}

    # Parse initial web directory for languages
    logger.info(f"GET \"{lang_base_url}\"")
    response = requests.get(lang_base_url)
    langs = [lang.split('/')[0] for lang in response.text.split('<a href="')][1:]

    for lang in langs:
        logger.info(f"GET \"{lang_base_url}/{lang}\"")
        response = requests.get(f"{lang_base_url}/{lang}")
        if not response.ok:
            raise f"Failed to get languages: {response.status_code}"
        lang_files = [f.split('"')[0] for f in response.text.split('<a href="')][1:]

        for lang_file in lang_files:
            if any([lang_file.startswith(f'v{i}') for i in range(get_config()["min_model_version"], 5)]):
                models[lang_file] = f"{lang_base_url}/{lang}/{lang_file}"
    with open('langs.json', 'w') as fh:
        json.dump(models, fh)
    return models


if not offline_mode:
    models = list_models()
    logger.info(f"Loaded actual list of models.")
else:
    models = {model: f"models/{model}" for model in os.listdir('models')}
    logger.info(f"Working offline. Available models: {', '.join(models)}")


class Model:
    file: str
    language: str
    voices: [str, ]

    def __init__(self, model):
        logger.info(F"Loading model: {model}")
        self.sessions_path = Path(F"sessions")
        self.model = None

        self.max_char_length = get_config()["max_char_length"]

        self.model_file: Path = None
        # Load model
        self.load_model(model)

    def load_model(self, model="v3_en.pt"):

        if model not in models:
            raise FileNotFoundError(f"Model {model} not in {list(models.keys())}."
                                    f" Are you using offline mode without downloaded model?")

        model_url = models[model]
        self.model_file = Path(f"models/{model}")

        if not Path.is_file(self.model_file):
            logger.warning(f"Downloading Silero {model} model...")
            torch.hub.download_url_to_file(model_url,
                                           str(self.model_file))
            logger.info(f"Model download completed.")

        self.model = torch.package.PackageImporter(self.model_file).load_pickle("tts_models", "model")
        self.model.to(device)

    def save_session_audio(self, audio_path: Path, speaker, session: Path or str = None):
        if isinstance(session, str):
            session = Path(session)

        if session is None:
            token = md5(str(random.randint(13, 128) ** random.randint(1, 6)).encode())
            session = token.hexdigest()
        session_path = self.sessions_path.joinpath(session)
        if not session_path.exists():
            session_path.mkdir()
        dst = session_path.joinpath(f"tts_{session}_{int(time.time())}_{speaker}_.wav")
        shutil.copy(audio_path, dst)

    def generate(self, speaker, text, session="", sample_rate=None, **kwargs) -> Path:
        if sample_rate is None:
            sample_rate = get_config()["sample_rate"]
        if len(text) > self.max_char_length:
            # Handle long text input
            text_chunks = self.split_text(text)
            combined_wav = AudioSegment.empty()

            for chunk in text_chunks:
                audio_path = Path(self.model.save_wav(text=chunk, speaker=speaker, sample_rate=sample_rate))
                combined_wav += AudioSegment.silent(500)  # Insert 500ms pause
                combined_wav += AudioSegment.from_file(audio_path)

            file_path = "sessions/no_session.wav"
            combined_wav.export(file_path, format="wav")
            audio_path = Path(file_path)
        else:
            audio_path = Path(self.model.save_wav(text=text, speaker=speaker, sample_rate=sample_rate))
        if session:
            self.save_session_audio(audio_path, speaker, session)
        return audio_path

    def split_text(self, text: str) -> list[str]:
        # Split text into chunks less than self.max_char_length
        chunk_list = []
        chunk_str = ""

        for word in text.split(' '):
            word = word.replace('\n', ' ') + " "
            if len(chunk_str + word) > self.max_char_length:
                chunk_list.append(chunk_str)
                chunk_str = ""
            chunk_str += word

        # Add the last chunk
        if len(chunk_str) > 0:
            chunk_list.append(chunk_str)

        return chunk_list

    def get_speakers(self):
        """List of speakers in model"""
        return self.model.speakers


class TTS:
    models: {str: Model, }

    def __init__(self):
        self.models = dict()

    def generate(self, voice, text, **kwargs):
        model_name, speaker = voice.split(':')
        if model_name not in self.models:
            model = Model(model_name + ".pt")
            self.models[model_name] = model
        else:
            model = self.models[model_name]

        path = model.generate(speaker, text, **kwargs)
        return path


_tts = TTS()


def get_tts() -> TTS:
    return _tts
