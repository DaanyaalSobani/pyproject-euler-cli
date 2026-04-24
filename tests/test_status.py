# tests/test_status.py
import pytest
from unittest.mock import MagicMock, patch
import euler.config as config
import euler.status as status_mod

_PROGRESS_HTML = """
<html><body>
<div id="progress_page">
  <div id="header_section">
    <div id="profile_name_box"><h2 id="profile_name_text">daanyaalsobani</h2></div>
  </div>
  <h3>Solved 5 out of 993 problems (0.5%)</h3>
</div>
</body></html>
"""


def _make_session(html: str, url: str = "https://projecteuler.net/progress") -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.url = url
    resp.raise_for_status = MagicMock()
    s = MagicMock()
    s.get.return_value = resp
    return s


def test_get_status_returns_username_solved_and_total(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(_PROGRESS_HTML)):
        info = status_mod.get_status()
    assert info["username"] == "daanyaalsobani"
    assert info["solved"] == 5
    assert info["total"] == 993


def test_get_status_raises_if_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=None):
        with pytest.raises(PermissionError):
            status_mod.get_status()


def test_get_status_raises_if_session_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    expired = _make_session(_PROGRESS_HTML, url="https://projecteuler.net/sign_in")
    with patch("euler.session.load_session", return_value=expired):
        with pytest.raises(PermissionError):
            status_mod.get_status()


_NO_PROFILE_HTML = """
<html><body>
<div id="progress_page">
  <h3>Solved 5 out of 993 problems (0.5%)</h3>
</div>
</body></html>
"""

_NO_PROGRESS_HTML = """
<html><body>
<div id="progress_page">
  <div id="header_section">
    <div id="profile_name_box"><h2 id="profile_name_text">daanyaalsobani</h2></div>
  </div>
</div>
</body></html>
"""


def test_get_status_raises_when_username_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(_NO_PROFILE_HTML)):
        with pytest.raises(ValueError, match="username"):
            status_mod.get_status()


def test_get_status_raises_when_solve_count_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(_NO_PROGRESS_HTML)):
        with pytest.raises(ValueError, match="solve count|progress"):
            status_mod.get_status()


def test_get_status_handles_comma_formatted_numbers(tmp_path, monkeypatch):
    """Future-proof: if PE ever displays counts like '1,000', still parse correctly."""
    html = """
    <html><body>
    <div id="progress_page">
      <div id="header_section">
        <div id="profile_name_box"><h2 id="profile_name_text">test_user</h2></div>
      </div>
      <h3>Solved 1,234 out of 5,000 problems</h3>
    </div>
    </body></html>
    """
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(html)):
        info = status_mod.get_status()
    assert info["solved"] == 1234
    assert info["total"] == 5000
