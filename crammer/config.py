import json
import os
import getpass

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
    print()
    key = input("Enter your DeepSeek API Key: ").strip()
    if not key:
        return ""

    print("Verifying...", end="", flush=True)
    ok, error_msg = deepseek_verify(key)
    if ok:
        print(" Connected!")
        save_config("api_key", key)
        return key

    print(" Failed")
    print("Error:", error_msg)
    print()
    print("Tip: If you are in China, you may need a proxy.")
    print("Edit start.bat and uncomment the HTTP_PROXY/HTTPS_PROXY lines.")
    print()

    input("Press Enter to continue (you can edit data/config.json manually later)...")
    return ""
