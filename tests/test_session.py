# tests/test_session.py
import json
import pytest
import requests
import euler.config as config
import euler.session as session


@pytest.fixture(autouse=True)
def tmp_session(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / ".euler" / "session.json")


def test_load_session_missing_returns_none():
    assert session.load_session() is None


def test_save_then_load_session():
    s = requests.Session()
    s.cookies.set("PHPSESSID", "abc123", domain="projecteuler.net", path="/")
    session.save_session(s)
    loaded = session.load_session()
    assert loaded is not None
    assert loaded.cookies.get("PHPSESSID", domain="projecteuler.net") == "abc123"


def test_clear_session_removes_file():
    s = requests.Session()
    s.cookies.set("PHPSESSID", "abc123", domain="projecteuler.net", path="/")
    session.save_session(s)
    session.clear_session()
    assert session.load_session() is None


def test_clear_session_when_no_file_does_not_raise():
    session.clear_session()


def test_load_session_malformed_json(tmp_path, monkeypatch):
    f = tmp_path / ".euler" / "session.json"
    f.parent.mkdir()
    f.write_text("not valid json{{")
    monkeypatch.setattr(config, "SESSION_FILE", f)
    assert session.load_session() is None
