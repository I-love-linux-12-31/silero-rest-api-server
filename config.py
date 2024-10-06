import json

app_config: dict = None


def load_config():
    global app_config
    with open('config.json') as config_file:
        app_config = json.load(config_file)
    return app_config


def get_config():
    if app_config is None:
        load_config()
    return app_config
