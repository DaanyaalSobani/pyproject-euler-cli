import re
from bs4 import BeautifulSoup
from . import config, session

_PROGRESS_PATH = "/progress"
_SOLVED_PATTERN = re.compile(r"Solved\s+(\d+)\s+out of\s+(\d+)", re.IGNORECASE)


def get_status() -> dict:
    """Returns dict with 'username' (str), 'solved' (int), 'total' (int).
    Raises PermissionError if not logged in.
    """
    s = session.load_session()
    if s is None:
        raise PermissionError("Not logged in")

    resp = s.get(f"{config.BASE_URL}{_PROGRESS_PATH}")
    resp.raise_for_status()

    if "sign_in" in resp.url:
        raise PermissionError("Session expired")

    soup = BeautifulSoup(resp.text, "html.parser")

    name_el = soup.find(id="profile_name_text")
    username = name_el.get_text(strip=True) if name_el else "Unknown"

    solved = 0
    total = 0
    page = soup.find(id="progress_page")
    if page:
        match = _SOLVED_PATTERN.search(page.get_text())
        if match:
            solved = int(match.group(1))
            total = int(match.group(2))

    return {"username": username, "solved": solved, "total": total}
