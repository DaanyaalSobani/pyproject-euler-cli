import re
from bs4 import BeautifulSoup
from . import config, session

_PROGRESS_PATH = "/progress"
# Match numbers with optional comma separators (e.g., "1,234")
_SOLVED_PATTERN = re.compile(r"Solved\s+([\d,]+)\s+out of\s+([\d,]+)", re.IGNORECASE)


def get_status() -> dict:
    """Returns dict with 'username' (str), 'solved' (int), 'total' (int).

    Raises PermissionError if not logged in or session expired.
    Raises ValueError if the progress page structure cannot be parsed.
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
    if name_el is None:
        raise ValueError("Could not parse username from progress page.")
    username = name_el.get_text(strip=True)

    page = soup.find(id="progress_page")
    if page is None:
        raise ValueError("Could not find progress page container.")

    match = _SOLVED_PATTERN.search(page.get_text())
    if match is None:
        raise ValueError("Could not parse solve count from progress page.")

    solved = int(match.group(1).replace(",", ""))
    total = int(match.group(2).replace(",", ""))

    return {"username": username, "solved": solved, "total": total}
