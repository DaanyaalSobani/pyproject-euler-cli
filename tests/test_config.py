# tests/test_config.py
import pytest
from unittest.mock import patch
import euler.config as config


def test_load_dev_env_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DEV_ENV_PATH", tmp_path / "dev.env")
    assert config.load_dev_env() == {}


def test_load_dev_env_present(tmp_path, monkeypatch):
    env = tmp_path / "dev.env"
    env.write_text("EULER_USERNAME=foo@bar.com\nEULER_PASSWORD=secret\n")
    monkeypatch.setattr(config, "DEV_ENV_PATH", env)
    assert config.load_dev_env() == {"EULER_USERNAME": "foo@bar.com", "EULER_PASSWORD": "secret"}


def test_load_dev_env_ignores_comments(tmp_path, monkeypatch):
    env = tmp_path / "dev.env"
    env.write_text("# comment\nEULER_USERNAME=u\nEULER_PASSWORD=p\n")
    monkeypatch.setattr(config, "DEV_ENV_PATH", env)
    assert config.load_dev_env() == {"EULER_USERNAME": "u", "EULER_PASSWORD": "p"}


def test_get_credentials_from_dev_env(tmp_path, monkeypatch):
    env = tmp_path / "dev.env"
    env.write_text("EULER_USERNAME=foo@bar.com\nEULER_PASSWORD=secret\n")
    monkeypatch.setattr(config, "DEV_ENV_PATH", env)
    assert config.get_credentials() == ("foo@bar.com", "secret")


def test_get_credentials_from_keyring(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DEV_ENV_PATH", tmp_path / "dev.env")

    def fake_get(service, key):
        if key == config.KEYRING_USERNAME_KEY:
            return "foo@bar.com"
        if key == "foo@bar.com":
            return "secret"
        return None

    with patch("keyring.get_password", side_effect=fake_get):
        assert config.get_credentials() == ("foo@bar.com", "secret")


def test_get_credentials_returns_none_when_not_set(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DEV_ENV_PATH", tmp_path / "dev.env")
    with patch("keyring.get_password", return_value=None):
        assert config.get_credentials() is None
