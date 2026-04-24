# tests/test_submit.py
import pytest
from unittest.mock import MagicMock, patch
import euler.config as config
import euler.submit as submit_mod

_UNSOLVED_PROBLEM_HTML = """
<html><body>
<form name="form" method="post" action="problem=42">
  <div class="data_entry">
    <div class="row">
      <div class="cell right w200">Answer:&nbsp;&nbsp;</div>
      <div class="cell"><input size="20" type="text" name="guess_42" id="guess" maxlength="30"></div>
      <input type="hidden" name="csrf_token" value="tok789">
    </div>
  </div>
</form>
</body></html>
"""

_SOLVED_PROBLEM_HTML = """
<html><body>
<form name="form" method="post" action="problem=1">
  <div class="data_entry">
    <div>Answer:&nbsp;&nbsp;<span class="strong">233168</span></div>
    <div class="small_notice">Completed on Thu, 23 Apr 2026, 16:31</div>
  </div>
</form>
</body></html>
"""

_CORRECT_RESPONSE_HTML = """
<html><body>
<div id="content">
  <div><img src="images/clipart/answer_correct.png" alt="Correct"></div>
  <p>Congratulations, you have solved the problem!</p>
</div>
</body></html>
"""

_INCORRECT_RESPONSE_HTML = """
<html><body>
<div id="content">
  <div><img src="images/clipart/answer_wrong.png" alt="Wrong" class="dark_img"></div>
  <p>Sorry, but the answer you gave appears to be incorrect.</p>
</div>
</body></html>
"""


def _make_session(get_html: str, post_html: str, get_url: str = "https://projecteuler.net/problem=42") -> MagicMock:
    get_resp = MagicMock()
    get_resp.text = get_html
    get_resp.url = get_url
    get_resp.raise_for_status = MagicMock()

    post_resp = MagicMock()
    post_resp.text = post_html
    post_resp.url = get_url
    post_resp.raise_for_status = MagicMock()

    s = MagicMock()
    s.get.return_value = get_resp
    s.post.return_value = post_resp
    return s


def test_submit_correct_returns_true(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(_UNSOLVED_PROBLEM_HTML, _CORRECT_RESPONSE_HTML)):
        assert submit_mod.submit_answer(42, "162") is True


def test_submit_incorrect_returns_false(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(_UNSOLVED_PROBLEM_HTML, _INCORRECT_RESPONSE_HTML)):
        assert submit_mod.submit_answer(42, "0") is False


def test_submit_posts_correct_dynamic_field_name(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    mock_sess = _make_session(_UNSOLVED_PROBLEM_HTML, _CORRECT_RESPONSE_HTML)
    with patch("euler.session.load_session", return_value=mock_sess):
        submit_mod.submit_answer(42, "162")
    data = mock_sess.post.call_args[1]["data"]
    assert data["guess_42"] == "162"
    assert data["csrf_token"] == "tok789"


def test_submit_already_solved_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    mock_sess = _make_session(_SOLVED_PROBLEM_HTML, "")
    with patch("euler.session.load_session", return_value=mock_sess):
        with pytest.raises(ValueError, match="already solved"):
            submit_mod.submit_answer(1, "233168")


def test_submit_raises_if_not_logged_in(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=None):
        with pytest.raises(PermissionError):
            submit_mod.submit_answer(42, "162")


def test_submit_raises_if_session_expired(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    mock_sess = _make_session(_UNSOLVED_PROBLEM_HTML, _CORRECT_RESPONSE_HTML, get_url="https://projecteuler.net/sign_in")
    with patch("euler.session.load_session", return_value=mock_sess):
        with pytest.raises(PermissionError):
            submit_mod.submit_answer(42, "162")


_UNKNOWN_RESPONSE_HTML = """
<html><body>
<div id="content">
  <p>You are submitting too quickly. Please wait and try again.</p>
</div>
</body></html>
"""


def test_submit_returns_false_on_unknown_response(tmp_path, monkeypatch):
    """A response missing both correct and wrong markers (e.g., rate-limit page)
    must not be silently classified as correct."""
    monkeypatch.setattr(config, "SESSION_FILE", tmp_path / "session.json")
    with patch("euler.session.load_session", return_value=_make_session(_UNSOLVED_PROBLEM_HTML, _UNKNOWN_RESPONSE_HTML)):
        assert submit_mod.submit_answer(42, "162") is False
