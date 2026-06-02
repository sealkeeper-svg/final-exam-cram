import json
import os
from unittest.mock import patch

import pytest

import crammer.config


@pytest.fixture
def temp_config_path(tmp_path):
    config_file = tmp_path / "config.json"
    with patch.object(crammer.config, "CONFIG_PATH", str(config_file)):
        yield str(config_file)


def test_save_and_load(temp_config_path):
    crammer.config.save_config("api_key", "sk-test-123")
    cfg = crammer.config.load_config()
    assert cfg["api_key"] == "sk-test-123"

    crammer.config.save_config("model", "gpt-4")
    cfg = crammer.config.load_config()
    assert cfg["api_key"] == "sk-test-123"
    assert cfg["model"] == "gpt-4"


def test_default_when_no_file(tmp_path):
    config_file = tmp_path / "config.json"
    with patch.object(crammer.config, "CONFIG_PATH", str(config_file)):
        assert not os.path.exists(config_file)
        cfg = crammer.config.load_config()
        assert cfg == crammer.config.DEFAULT_CONFIG
        assert os.path.exists(config_file)

        with open(config_file, "r") as f:
            saved = json.load(f)
        assert saved == crammer.config.DEFAULT_CONFIG
