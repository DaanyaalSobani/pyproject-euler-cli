# tests/test_auth.py
import pytest
from unittest.mock import MagicMock, patch
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
    page.wait_for_url.side_effect = Exception("Timeout waiting for /archives")

    context = MagicMock()
    context.new_page.return_value = page

    browser = MagicMock()
    browser.new_context.return_value = context

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
