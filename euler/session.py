import json
import requests
from . import config

# Browser-like headers. Without these, projecteuler.net silently 302-redirects
# POSTs to /about (bot-deflection) and correct-answer submissions never register.
# Matches what Chromium sends on a same-origin form-submit navigation.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}


def load_session() -> requests.Session | None:
    if not config.SESSION_FILE.exists():
        return None
    try:
        cookies = json.loads(config.SESSION_FILE.read_text())
        s = requests.Session()
        s.headers.update(_BROWSER_HEADERS)
        for c in cookies:
            s.cookies.set(
                c["name"], c["value"],
                domain=c.get("domain", ""),
                path=c.get("path", "/"),
            )
        return s
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_session(s: requests.Session) -> None:
    config.SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    cookies = [
        {"name": c.name, "value": c.value, "domain": c.domain, "path": c.path}
        for c in s.cookies
    ]
    config.SESSION_FILE.write_text(json.dumps(cookies, indent=2))


def clear_session() -> None:
    config.SESSION_FILE.unlink(missing_ok=True)
