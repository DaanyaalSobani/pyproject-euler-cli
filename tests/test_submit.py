# tests/test_submit.py
import pytest
from unittest.mock import MagicMock, patch
import euler.config as config
import euler.submit as submit_mod

_CORRECT_RESPONSE_HTML = """
<html><body>
<div id="content">
  <div><img src="images/clipart/answer_correct.png" alt="Correct"></div>
  <p>Congratulations, you have solved the problem!</p>
</div>
</body></html>
"""

_INCORRECT_RESPONSE_HTML = """
<html><body>
<div id="content">
  <div><img src="images/clipart/answer_wrong.png" alt="Wrong" class="dark_img"></div>
  <p>Sorry, but the answer you gave appears to be incorrect.</p>
</div>
</body></html>
"""

_UNKNOWN_RESPONSE_HTML = """
<html><body>
<div id="content">
  <p>You are submitting too quickly. Please wait and try again.</p>
</div>
</body></html>
"""


def _loaded_session_mock():
    """Mock for session.load_session() — submit reads .cookies off it."""
    m = MagicMock()
    cookie = MagicMock()
    cookie.name = "__Host-PHPSESSID"
    cookie.value = "abc123"
    cookie.domain = "projecteuler.net"
    cookie.path = "/"
    m.cookies = [cookie]
    return m


def _mock_playwright(*, guess_input_present: bool, page_url_before_fill: str, result_html: str, result_url: str):
    """Build a fake sync_playwright() context manager whose .chromium.launch()
    context manager yields a Browser whose context/page simulate PE's responses."""
    guess_input = MagicMock() if guess_input_present else None

    def query_selector(sel):
        if "guess_" in sel:
            return guess_input
        return MagicMock()  # submit button

    page = MagicMock()
    page.url = page_url_before_fill
    page.query_selector.side_effect = query_selector
    page.goto = MagicMock()
    page.click = MagicMock()
    page.content.return_value = result_html

    # After form submit the page URL becomes result_url
    def after_click(*a, **kw):
        page.url = result_url
    page.click.side_effect = after_click

    # page.expect_navigation(...) is a context manager; make it a no-op
    nav_cm = MagicMock()
    nav_cm.__enter__ = MagicMock(return_value=None)
    nav_cm.__exit__ = MagicMock(return_value=False)
    page.expect_navigation.return_value = nav_cm

    context = MagicMock()
    context.new_page.return_value = page
    context.add_cookies = MagicMock()

    browser = MagicMock()
    browser.new_context.return_value = context
    browser.__enter__ = MagicMock(return_value=browser)
    browser.__exit__ = MagicMock(return_value=False)

    pw = MagicMock()
    pw.chromium.launch.return_value = browser

    pw_cm = MagicMock()
    pw_cm.__enter__ = MagicMock(return_value=pw)
    pw_cm.__exit__ = MagicMock(return_value=False)
    return pw_cm


def test_submit_correct_returns_correct(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    pw = _mock_playwright(
        guess_input_present=True,
        page_url_before_fill="https://projecteuler.net/problem=42",
        result_html=_CORRECT_RESPONSE_HTML,
        result_url="https://projecteuler.net/problem=42",
    )
    with patch("euler.session.load_session", return_value=_loaded_session_mock()), \
         patch("euler.submit.sync_playwright", return_value=pw):
        assert submit_mod.submit_answer(42, "162") == "correct"


def test_submit_incorrect_returns_incorrect(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    pw = _mock_playwright(
        guess_input_present=True,
        page_url_before_fill="https://projecteuler.net/problem=42",
        result_html=_INCORRECT_RESPONSE_HTML,
        result_url="https://projecteuler.net/problem=42",
    )
    with patch("euler.session.load_session", return_value=_loaded_session_mock()), \
         patch("euler.submit.sync_playwright", return_value=pw):
        assert submit_mod.submit_answer(42, "0") == "incorrect"


def test_submit_returns_blocked_on_unknown_response(tmp_path, monkeypatch):
    """A response missing both markers (bot deflection, rate limit, etc.) must
    surface as "blocked", not silently reported as correct or incorrect."""
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    pw = _mock_playwright(
        guess_input_present=True,
        page_url_before_fill="https://projecteuler.net/problem=42",
        result_html=_UNKNOWN_RESPONSE_HTML,
        result_url="https://projecteuler.net/about",
    )
    with patch("euler.session.load_session", return_value=_loaded_session_mock()), \
         patch("euler.submit.sync_playwright", return_value=pw):
        assert submit_mod.submit_answer(42, "162") == "blocked"


def test_submit_already_solved_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    pw = _mock_playwright(
        guess_input_present=False,  # no guess input = already solved
        page_url_before_fill="https://projecteuler.net/problem=1",
        result_html="",
        result_url="https://projecteuler.net/problem=1",
    )
    with patch("euler.session.load_session", return_value=_loaded_session_mock()), \
         patch("euler.submit.sync_playwright", return_value=pw):
        with pytest.raises(ValueError, match="already solved"):
            submit_mod.submit_answer(1, "233168")


def test_submit_raises_if_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=None):
        with pytest.raises(PermissionError):
            submit_mod.submit_answer(42, "162")


def test_submit_raises_if_session_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    pw = _mock_playwright(
        guess_input_present=True,
        page_url_before_fill="https://projecteuler.net/sign_in",  # redirected
        result_html="",
        result_url="https://projecteuler.net/sign_in",
    )
    with patch("euler.session.load_session", return_value=_loaded_session_mock()), \
         patch("euler.submit.sync_playwright", return_value=pw):
        with pytest.raises(PermissionError):
            submit_mod.submit_answer(42, "162")
