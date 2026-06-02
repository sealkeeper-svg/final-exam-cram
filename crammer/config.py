import json
import os

import questionary

from crammer.utils import deepseek_verify

CONFIG_PATH = "data/config.json"
DEFAULT_CONFIG = {
    "api_key": "",
    "model": "deepseek-chat",
    "api_base": "https://api.deepseek.com",
}


def _resolve_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, CONFIG_PATH)


def _read_config():
    path = _resolve_path()
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def load_config():
    cfg = _read_config()
    if cfg is None:
        save_all(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    return cfg


def save_config(key, value):
    cfg = _read_config()
    if cfg is None:
        cfg = dict(DEFAULT_CONFIG)
    cfg[key] = value
    _write_config(cfg)


def save_all(cfg):
    _write_config(cfg)


def _write_config(cfg):
    path = _resolve_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


def get_api_key():
    cfg = load_config()
    return cfg.get("api_key", "")


def setup_api_key():
    key = questionary.password("Enter your DeepSeek API Key:").ask()
    if not key:
        return ""

    import sys
    sys.stdout.write("Verifying...")
    sys.stdout.flush()

    if deepseek_verify(key):
        sys.stdout.write(" Connected!\n")
        sys.stdout.flush()
        save_config("api_key", key)
        return key
    sys.stdout.write(" Failed\n")
    sys.stdout.flush()
    print("API Key verification failed. Check your key or network.")
    print("If you are in China, you may need a proxy. Set HTTP_PROXY/HTTPS_PROXY env vars.")
    return ""
