import pytest
from unittest.mock import MagicMock, patch
import requests
import euler.problem as problem_mod


def _mock_get(text: str, status: int = 200):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(f"HTTP {status}")
    return resp


def test_get_problem_text_parses_paragraphs():
    html = (
        "<p>A Pythagorean triplet is a set of three natural numbers, "
        "$a \\lt b \\lt c$, for which, $$a^2 + b^2 = c^2.$$</p>"
        "<p>For example, $3^2 + 4^2 = 9 + 16 = 25 = 5^2$.</p>"
    )
    with patch("requests.get", return_value=_mock_get(html)):
        text = problem_mod.get_problem_text(9)
    assert "Pythagorean triplet" in text
    assert "For example" in text
    # Paragraphs separated by blank line
    assert "\n\n" in text
    # LaTeX preserved
    assert "$a^2 + b^2 = c^2$" in text or "a^2 + b^2 = c^2" in text


def test_get_problem_text_replaces_br_with_newline():
    html = "<p>Line one.<br>Line two.</p>"
    with patch("requests.get", return_value=_mock_get(html)):
        text = problem_mod.get_problem_text(1)
    assert "Line one." in text
    assert "Line two." in text
    # <br> became a newline between the lines
    assert "Line one.\nLine two." in text


def test_get_problem_text_raises_on_empty_response():
    with patch("requests.get", return_value=_mock_get("")):
        with pytest.raises(ValueError, match="empty response"):
            problem_mod.get_problem_text(999999)


def test_get_problem_text_propagates_network_error():
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("boom")):
        with pytest.raises(requests.exceptions.ConnectionError):
            problem_mod.get_problem_text(1)


def test_get_problem_text_hits_minimal_endpoint():
    with patch("requests.get", return_value=_mock_get("<p>ok</p>")) as mock_get:
        problem_mod.get_problem_text(42)
    called_url = mock_get.call_args[0][0]
    assert called_url == "https://projecteuler.net/minimal=42"


def test_render_for_terminal_strips_inline_dollars():
    out = problem_mod.render_for_terminal("Given $a < b$, compute $c$.")
    assert "$" not in out
    assert "a < b" in out
    assert " c." in out or "c." in out


def test_render_for_terminal_puts_display_math_on_own_line():
    out = problem_mod.render_for_terminal("Recall $$a^2 + b^2 = c^2$$ forever.")
    assert "$$" not in out
    # Display math on its own indented line
    assert "\n    " in out


def test_render_for_terminal_replaces_latex_commands():
    out = problem_mod.render_for_terminal(r"$a \lt b \ge c$ and $\pi r^2$")
    assert "<" in out
    assert "≥" in out
    assert "π" in out


def test_render_for_terminal_superscript_single_digit():
    out = problem_mod.render_for_terminal("$3^2 + 4^2 = 5^2$")
    assert "3² + 4² = 5²" in out


def test_render_for_terminal_superscript_multi_digit():
    out = problem_mod.render_for_terminal("$10^{10001}$")
    assert "10¹⁰⁰⁰¹" in out


def test_render_for_terminal_keeps_non_math_text_intact():
    original = "Plain sentence with no math at all."
    assert problem_mod.render_for_terminal(original) == original


def test_render_for_terminal_frac_becomes_division():
    out = problem_mod.render_for_terminal(r"$\frac{a}{b}$")
    assert "(a)/(b)" in out
