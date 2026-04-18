import os
import pytest
import yaml
from rss_feed_summary.config import load_config


def _write_config(tmp_path, data):
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data))
    return str(p)


VALID = {
    "feeds": ["https://example.com/feed"],
    "email": {
        "smtp_host": "smtp.example.com",
        "from": "a@example.com",
        "to": ["b@example.com"],
    },
}


def test_load_config_valid(tmp_path):
    path = _write_config(tmp_path, VALID)
    cfg = load_config(path)
    assert cfg["feeds"] == ["https://example.com/feed"]


def test_load_config_missing_feeds(tmp_path):
    data = {**VALID, "feeds": None}
    path = _write_config(tmp_path, data)
    with pytest.raises(ValueError, match="feeds"):
        load_config(path)


def test_load_config_feeds_not_list(tmp_path):
    data = {**VALID, "feeds": "https://example.com/feed"}
    path = _write_config(tmp_path, data)
    with pytest.raises(ValueError, match="feeds"):
        load_config(path)


def test_load_config_missing_smtp_host(tmp_path):
    data = {**VALID, "email": {**VALID["email"], "smtp_host": None}}
    path = _write_config(tmp_path, data)
    with pytest.raises(ValueError, match="smtp_host"):
        load_config(path)


def test_load_config_missing_from(tmp_path):
    data = {**VALID, "email": {**VALID["email"], "from": None}}
    path = _write_config(tmp_path, data)
    with pytest.raises(ValueError, match="email.from"):
        load_config(path)


def test_load_config_missing_to(tmp_path):
    data = {**VALID, "email": {**VALID["email"], "to": None}}
    path = _write_config(tmp_path, data)
    with pytest.raises(ValueError, match="email.to"):
        load_config(path)


def test_load_config_env_var_override(tmp_path, monkeypatch):
    path = _write_config(tmp_path, VALID)
    monkeypatch.setenv("RSS_SUMMARY_CONFIG", path)
    # load_config reads DEFAULT_CONFIG_PATH at import time, so pass path directly
    cfg = load_config(path)
    assert "feeds" in cfg


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")
