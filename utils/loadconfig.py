import json


def load_config(config_path='../'):
    with open(config_path) as f:
        cfg = json.load(f)
    return cfg
