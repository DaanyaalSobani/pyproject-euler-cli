import json
from bs4 import BeautifulSoup
from . import config, session

_CSRF_FIELD = "csrf_token"
_WRONG_IMAGE = "answer_wrong.png"
_CORRECT_IMAGE = "answer_correct.png"


def _save_debug_dump(post_resp) -> None:
    """Write POST request+response details to ~/.euler/last_submit_debug.json.
    Best-effort: swallows all errors so this never breaks a submission."""
    try:
        debug_file = config.SESSION_FILE.parent / "last_submit_debug.json"
        debug_file.parent.mkdir(parents=True, exist_ok=True)
        history = [
            {
                "url": h.url,
                "status": h.status_code,
                "method": h.request.method,
                "location_header": h.headers.get("Location"),
                "set_cookie": h.headers.get("Set-Cookie"),
            }
            for h in post_resp.history
        ]
        # The *original* POST request (before any redirects)
        original_req = post_resp.history[0].request if post_resp.history else post_resp.request
        debug_file.write_text(json.dumps({
            "original_request_method": original_req.method,
            "original_request_url": original_req.url,
            "original_request_headers": dict(original_req.headers),
            "original_request_body": original_req.body,
            "redirect_chain": history,
            "final_response_status": post_resp.status_code,
            "final_response_url": post_resp.url,
            "final_response_text_head": post_resp.text[:2000],
            "has_wrong_marker": _WRONG_IMAGE in post_resp.text,
            "has_correct_marker": _CORRECT_IMAGE in post_resp.text,
        }, indent=2))
    except Exception:
        pass


def _find_answer_input(html: str, problem: int) -> tuple[str, str] | None:
    """Returns (answer_field_name, csrf_token) if the problem is unsolved, else None."""
    soup = BeautifulSoup(html, "html.parser")
    answer_input = soup.find("input", {"name": f"guess_{problem}"})
    if answer_input is None:
        return None
    csrf = soup.find("input", {"name": _CSRF_FIELD})
    token = csrf["value"] if csrf else ""
    return answer_input["name"], token


def _classify_response(html: str) -> str:
    """Returns "correct", "incorrect", or "blocked".

    "blocked" means PE returned a response with neither marker — typically the
    /about page it 302-redirects to when bot-deflection kicks in. The answer
    was not actually processed; treat this as a submission failure rather than
    silently reporting "incorrect"."""
    if _CORRECT_IMAGE in html:
        return "correct"
    if _WRONG_IMAGE in html:
        return "incorrect"
    return "blocked"


def submit_answer(problem: int, answer: str) -> str:
    """Submit answer to problem N. Returns "correct", "incorrect", or "blocked".
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
    # Referer and Origin are required by PE's bot deflection; without them the
    # server 302-redirects the POST to /about and the answer is never processed.
    post_headers = {
        "Referer": problem_url,
        "Origin": config.BASE_URL,
    }
    post_resp = s.post(
        problem_url,
        data={field_name: answer, _CSRF_FIELD: token},
        headers=post_headers,
    )
    _save_debug_dump(post_resp)
    post_resp.raise_for_status()
    return _classify_response(post_resp.text)
