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
