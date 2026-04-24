# tests/test_cli.py
import pytest
from unittest.mock import patch
from click.testing import CliRunner
from euler.cli import main


def test_login_success():
    runner = CliRunner()
    with patch("euler.config.get_credentials", return_value=("u@e.com", "pass")), \
         patch("euler.auth.login", return_value="daanyaalsobani"):
        result = runner.invoke(main, ["login"])
    assert result.exit_code == 0
    assert "daanyaalsobani" in result.output


def test_login_prompts_when_no_creds_stored():
    runner = CliRunner()
    with patch("euler.config.get_credentials", return_value=None), \
         patch("euler.config.save_credentials") as mock_save, \
         patch("euler.auth.login", return_value="daanyaalsobani"):
        result = runner.invoke(main, ["login"], input="u@e.com\npass\n")
    assert result.exit_code == 0
    mock_save.assert_called_once_with("u@e.com", "pass")


def test_login_does_not_save_creds_when_login_fails():
    runner = CliRunner()
    with patch("euler.config.get_credentials", return_value=None), \
         patch("euler.config.save_credentials") as mock_save, \
         patch("euler.auth.login", side_effect=ValueError("Login timed out")):
        result = runner.invoke(main, ["login"], input="u@e.com\nbadpass\n")
    assert result.exit_code == 1
    mock_save.assert_not_called()


def test_login_exits_1_on_login_failure():
    runner = CliRunner()
    with patch("euler.config.get_credentials", return_value=("u@e.com", "bad")), \
         patch("euler.auth.login", side_effect=ValueError("Login timed out")):
        result = runner.invoke(main, ["login"])
    assert result.exit_code == 1
    assert "timed out" in result.output.lower()


def test_logout_default_keeps_keyring():
    runner = CliRunner()
    with patch("euler.auth.logout") as mock_logout:
        result = runner.invoke(main, ["logout"], input="n\n")
    assert result.exit_code == 0
    mock_logout.assert_called_once_with(remove_keyring=False)
    assert "Logged out" in result.output


def test_logout_removes_keyring_when_confirmed():
    runner = CliRunner()
    with patch("euler.auth.logout") as mock_logout:
        result = runner.invoke(main, ["logout"], input="y\n")
    assert result.exit_code == 0
    mock_logout.assert_called_once_with(remove_keyring=True)
    assert "Logged out" in result.output


def test_submit_correct():
    runner = CliRunner()
    with patch("euler.submit.submit_answer", return_value=True):
        result = runner.invoke(main, ["submit", "42", "162"])
    assert result.exit_code == 0
    assert "Correct" in result.output


def test_submit_incorrect():
    runner = CliRunner()
    with patch("euler.submit.submit_answer", return_value=False):
        result = runner.invoke(main, ["submit", "42", "0"])
    assert result.exit_code == 0
    assert "Incorrect" in result.output


def test_submit_not_logged_in_exits_1():
    runner = CliRunner()
    with patch("euler.submit.submit_answer", side_effect=PermissionError("Not logged in")):
        result = runner.invoke(main, ["submit", "42", "162"])
    assert result.exit_code == 1
    assert "euler login" in result.output


def test_submit_already_solved_exits_1():
    runner = CliRunner()
    with patch("euler.submit.submit_answer", side_effect=ValueError("Problem 1 is already solved (no answer form on page).")):
        result = runner.invoke(main, ["submit", "1", "233168"])
    assert result.exit_code == 1
    assert "already solved" in result.output


def test_submit_network_error_exits_1():
    import requests
    runner = CliRunner()
    with patch("euler.submit.submit_answer", side_effect=requests.exceptions.ConnectionError("network unreachable")):
        result = runner.invoke(main, ["submit", "42", "162"])
    assert result.exit_code == 1
    assert "Network error" in result.output


def test_status_shows_username_solved_and_total():
    runner = CliRunner()
    with patch("euler.status.get_status", return_value={"username": "daanyaalsobani", "solved": 5, "total": 993}):
        result = runner.invoke(main, ["status"])
    assert result.exit_code == 0
    assert "daanyaalsobani" in result.output
    assert "5" in result.output
    assert "993" in result.output


def test_status_not_logged_in_exits_1():
    runner = CliRunner()
    with patch("euler.status.get_status", side_effect=PermissionError("Not logged in")):
        result = runner.invoke(main, ["status"])
    assert result.exit_code == 1
    assert "euler login" in result.output


def test_status_network_error_exits_1():
    import requests
    runner = CliRunner()
    with patch("euler.status.get_status", side_effect=requests.exceptions.ConnectionError("network unreachable")):
        result = runner.invoke(main, ["status"])
    assert result.exit_code == 1
    assert "Network error" in result.output


def test_get_problem_shows_problem_text():
    runner = CliRunner()
    with patch("euler.problem.get_problem_text", return_value="A Pythagorean triplet...\n\nFind abc."):
        result = runner.invoke(main, ["get-problem", "9"])
    assert result.exit_code == 0
    assert "Problem 9" in result.output
    assert "Pythagorean triplet" in result.output
    assert "Find abc." in result.output


def test_get_problem_invalid_exits_1():
    runner = CliRunner()
    with patch("euler.problem.get_problem_text", side_effect=ValueError("Problem 99999 returned empty response")):
        result = runner.invoke(main, ["get-problem", "99999"])
    assert result.exit_code == 1
    assert "empty response" in result.output


def test_get_problem_network_error_exits_1():
    import requests
    runner = CliRunner()
    with patch("euler.problem.get_problem_text", side_effect=requests.exceptions.ConnectionError("unreachable")):
        result = runner.invoke(main, ["get-problem", "9"])
    assert result.exit_code == 1
    assert "Network error" in result.output
