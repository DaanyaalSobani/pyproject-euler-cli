# tests/test_auth.py
import pytest
from unittest.mock import MagicMock, patch
from playwright.sync_api import Error as PlaywrightError
import euler.config as config
import euler.auth as auth


def test_login_saves_cookies_and_returns_username(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")

    logged_in_html = (
        '<html><body><div id="info_panel">Logged in as '
        '<strong>daanyaalsobani</strong></div></body></html>'
    )

    page = MagicMock()
    page.url = "https://projecteuler.net/archives"
    page.content.return_value = logged_in_html

    context = MagicMock()
    context.new_page.return_value = page
    context.cookies.return_value = [
        {"name": "PHPSESSID", "value": "abc123", "domain": "projecteuler.net", "path": "/",
         "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"},
    ]

    browser = MagicMock()
    browser.new_context.return_value = context
    # browser is now used as a context manager: `with pw.chromium.launch(...) as browser:`
    browser.__enter__ = MagicMock(return_value=browser)
    browser.__exit__ = MagicMock(return_value=False)

    pw = MagicMock()
    pw.chromium.launch.return_value = browser

    class FakePlaywrightCM:
        def __enter__(self): return pw
        def __exit__(self, *a): return False

    with patch("euler.auth.sync_playwright", return_value=FakePlaywrightCM()):
        name = auth.login("daanyaalsobani", "hunter2")

    assert name == "daanyaalsobani"
    assert (tmp_path / "session.json").exists()


def test_login_raises_when_not_logged_in_after_timeout(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")

    page = MagicMock()
    page.url = "https://projecteuler.net/sign_in"
    page.content.return_value = "<html><body>still on sign-in</body></html>"
    # Must raise PlaywrightError specifically — that's what the narrowed except clause catches
    page.wait_for_url.side_effect = PlaywrightError("Timeout waiting for /archives")

    context = MagicMock()
    context.new_page.return_value = page

    browser = MagicMock()
    browser.new_context.return_value = context
    # browser is now used as a context manager: `with pw.chromium.launch(...) as browser:`
    browser.__enter__ = MagicMock(return_value=browser)
    browser.__exit__ = MagicMock(return_value=False)

    pw = MagicMock()
    pw.chromium.launch.return_value = browser

    class FakePlaywrightCM:
        def __enter__(self): return pw
        def __exit__(self, *a): return False

    with patch("euler.auth.sync_playwright", return_value=FakePlaywrightCM()):
        with pytest.raises(ValueError, match="timed out|not.*logged"):
            auth.login("daanyaalsobani", "wrong")


def test_login_raises_when_username_not_found_in_page(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")

    page = MagicMock()
    page.url = "https://projecteuler.net/archives"
    page.content.return_value = "<html><body>no info panel here</body></html>"

    context = MagicMock()
    context.new_page.return_value = page
    context.cookies.return_value = []

    browser = MagicMock()
    browser.new_context.return_value = context
    # browser is now used as a context manager: `with pw.chromium.launch(...) as browser:`
    browser.__enter__ = MagicMock(return_value=browser)
    browser.__exit__ = MagicMock(return_value=False)

    pw = MagicMock()
    pw.chromium.launch.return_value = browser

    class FakePlaywrightCM:
        def __enter__(self): return pw
        def __exit__(self, *a): return False

    with patch("euler.auth.sync_playwright", return_value=FakePlaywrightCM()):
        with pytest.raises(ValueError, match="could not detect"):
            auth.login("daanyaalsobani", "hunter2")


def test_logout_clears_session(tmp_path, monkeypatch):
    session_file = tmp_path / "session.json"
    session_file.write_text("[]")
    monkeypatch.setattr(config, "SESSION_FILE", session_file)

    auth.logout(remove_keyring=False)

    assert not session_file.exists()


def test_logout_with_remove_keyring_calls_delete_credentials(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.config.delete_credentials") as mock_delete:
        auth.logout(remove_keyring=True)
    mock_delete.assert_called_once()


def test_playwright_cookies_round_trip_through_session_file(tmp_path, monkeypatch):
    """End-to-end: Playwright cookie dict -> requests.Session -> save -> load -> PHPSESSID retrievable."""
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    from euler import session as session_mod

    playwright_cookies = [
        {"name": "PHPSESSID", "value": "round_trip_value", "domain": "projecteuler.net",
         "path": "/", "expires": -1, "httpOnly": True, "secure": True, "sameSite": "Lax"},
    ]

    s = auth._playwright_cookies_to_requests_session(playwright_cookies)
    session_mod.save_session(s)
    loaded = session_mod.load_session()

    assert loaded is not None
    assert loaded.cookies.get("PHPSESSID", domain="projecteuler.net") == "round_trip_value"
