from bs4 import BeautifulSoup
from . import config, session

_CSRF_FIELD = "csrf_token"
_WRONG_IMAGE = "answer_wrong.png"
_CORRECT_IMAGE = "answer_correct.png"


def _find_answer_input(html: str, problem: int) -> tuple[str, str] | None:
    """Returns (answer_field_name, csrf_token) if the problem is unsolved, else None."""
    soup = BeautifulSoup(html, "html.parser")
    answer_input = soup.find("input", {"name": f"guess_{problem}"})
    if answer_input is None:
        return None
    csrf = soup.find("input", {"name": _CSRF_FIELD})
    token = csrf["value"] if csrf else ""
    return answer_input["name"], token


def _is_correct(html: str) -> bool:
    """Correct responses include answer_correct.png. Incorrect responses include
    answer_wrong.png. Anomalous pages (rate limit, session expired mid-request) have
    neither — treat as incorrect rather than silently lying."""
    return _CORRECT_IMAGE in html


def submit_answer(problem: int, answer: str) -> bool:
    """Submit answer to problem N. Returns True if correct.
    Raises PermissionError if not logged in.
    Raises ValueError if the problem is already solved.
    """
    s = session.load_session()
    if s is None:
        raise PermissionError("Not logged in")

    problem_url = f"{config.BASE_URL}/problem={problem}"
    resp = s.get(problem_url)
    resp.raise_for_status()

    if "sign_in" in resp.url:
        raise PermissionError("Session expired")

    form = _find_answer_input(resp.text, problem)
    if form is None:
        raise ValueError(f"Problem {problem} is already solved (no answer form on page).")

    field_name, token = form
    post_resp = s.post(problem_url, data={field_name: answer, _CSRF_FIELD: token})
    post_resp.raise_for_status()
    return _is_correct(post_resp.text)
