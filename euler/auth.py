import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from . import config, session

_LOGIN_URL = f"{config.BASE_URL}/sign_in"
_POST_LOGIN_URL_PATTERN = f"{config.BASE_URL}/archives"
_LOGIN_TIMEOUT_MS = 180_000  # 3 minutes for the user to solve the CAPTCHA


def _extract_display_name(html: str) -> str | None:
    """Extract the logged-in username from the post-login page.

    PE shows it as: <div id="info_panel">Logged in as <strong>USERNAME</strong>...</div>
    """
    soup = BeautifulSoup(html, "html.parser")
    info = soup.find(id="info_panel")
    if info is None:
        return None
    strong = info.find("strong")
    return strong.get_text(strip=True) if strong else None


def _playwright_cookies_to_requests_session(cookies: list[dict]) -> requests.Session:
    """Convert Playwright's cookie list into a requests.Session with the same jar."""
    s = requests.Session()
    for c in cookies:
        s.cookies.set(
            c["name"], c["value"],
            domain=c.get("domain", ""),
            path=c.get("path", "/"),
        )
    return s


def login(username: str, password: str) -> str:
    """Launch a browser, auto-fill credentials, wait for the user to solve the CAPTCHA
    and click Sign In, then persist the resulting cookies.

    Returns the display username on success. Raises ValueError on failure.
    """
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(_LOGIN_URL)

        # Auto-fill username and password. User still has to solve the CAPTCHA.
        page.fill("#username", username)
        page.fill("#password", password)

        try:
            page.wait_for_url(_POST_LOGIN_URL_PATTERN, timeout=_LOGIN_TIMEOUT_MS)
        except Exception as e:
            browser.close()
            raise ValueError(
                f"Login timed out or was not completed ({_LOGIN_TIMEOUT_MS // 1000}s)."
            ) from e

        html = page.content()
        cookies = context.cookies()
        browser.close()

    display_name = _extract_display_name(html)
    if display_name is None:
        raise ValueError("Login succeeded but could not detect username in page.")

    s = _playwright_cookies_to_requests_session(cookies)
    session.save_session(s)
    return display_name


def logout(remove_keyring: bool = False) -> None:
    """Clear the saved session. Optionally remove credentials from keyring."""
    session.clear_session()
    if remove_keyring:
        config.delete_credentials()
