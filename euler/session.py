import json
import requests
from . import config


def load_session() -> requests.Session | None:
    if not config.SESSION_FILE.exists():
        return None
    try:
        cookies = json.loads(config.SESSION_FILE.read_text())
        s = requests.Session()
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
    config.SESSION_FILE.write_text(json.dumps(cookies))


def clear_session() -> None:
    config.SESSION_FILE.unlink(missing_ok=True)
