import json
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from . import config, session

_CSRF_FIELD = "csrf_token"
_WRONG_IMAGE = "answer_wrong.png"
_CORRECT_IMAGE = "answer_correct.png"


def _save_debug_dump(final_url: str, html: str) -> None:
    """Write submit outcome details to ~/.euler/last_submit_debug.json.
    Best-effort: swallows all errors so this never breaks a submission."""
    try:
        debug_file = config.SESSION_FILE.parent / "last_submit_debug.json"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        debug_file.write_text(json.dumps({
            "final_url": final_url,
            "has_wrong_marker": _WRONG_IMAGE in html,
            "has_correct_marker": _CORRECT_IMAGE in html,
            "final_response_text_head": html[:2000],
        }, indent=2))
    except Exception:
        pass


def _cookies_for_playwright(requests_cookiejar) -> list[dict]:
    """Convert a requests.Session cookie jar into Playwright's add_cookies format."""
    out = []
    for c in requests_cookiejar:
        cookie = {
            "name": c.name,
            "value": c.value,
            "domain": (c.domain or "projecteuler.net").lstrip("."),
            "path": c.path or "/",
        }
        # __Host- and __Secure- prefixes require Secure attribute
        if c.name.startswith("__Host-") or c.name.startswith("__Secure-"):
            cookie["secure"] = True
        out.append(cookie)
    return out


def _classify_response(html: str) -> str:
    """Returns "correct", "incorrect", or "blocked"."""
    if _CORRECT_IMAGE in html:
        return "correct"
    if _WRONG_IMAGE in html:
        return "incorrect"
    return "blocked"


def submit_answer(problem: int, answer: str) -> str:
    """Submit answer to problem N. Returns "correct", "incorrect", or "blocked".
    Raises PermissionError if not logged in.
    Raises ValueError if the problem is already solved.

    Uses a headless Playwright browser for the submission itself — PE's
    bot deflection 302-redirects any `requests`/`curl_cffi` POST to /about,
    even with matching TLS fingerprint and all browser headers. Reusing the
    same client stack that logged in is the only thing that works.
    """
    loaded = session.load_session()
    if loaded is None:
        raise PermissionError("Not logged in")

    cookies = _cookies_for_playwright(loaded.cookies)
    problem_url = f"{config.BASE_URL}/problem={problem}"

    with sync_playwright() as pw:
        with pw.chromium.launch(headless=True) as browser:
            context = browser.new_context()
            context.add_cookies(cookies)
            page = context.new_page()
            page.goto(problem_url)

            if "sign_in" in page.url:
                raise PermissionError("Session expired")

            guess_input = page.query_selector(f"input[name='guess_{problem}']")
            if guess_input is None:
                raise ValueError(
                    f"Problem {problem} is already solved (no answer form on page)."
                )

            guess_input.fill(answer)
            with page.expect_navigation(wait_until="domcontentloaded"):
                page.click("input[type='submit']")

            final_url = page.url
            result_html = page.content()

    _save_debug_dump(final_url, result_html)
    return _classify_response(result_html)
