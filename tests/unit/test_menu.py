"""Tests for interactive menu utilities."""

from __future__ import annotations

from unittest.mock import patch

from youcadb.ui.menu import confirm, select_menu


def test_select_menu_valid_choice() -> None:
    with patch("builtins.input", return_value="2"):
        result = select_menu("Choose:", ["a", "b", "c"])
    assert result == "b"


def test_select_menu_invalid_choice_returns_none() -> None:
    with patch("builtins.input", return_value="99"):
        result = select_menu("Choose:", ["a", "b"])
    assert result is None


def test_select_menu_non_numeric_input() -> None:
    with patch("builtins.input", return_value="abc"):
        result = select_menu("Choose:", ["a", "b"])
    assert result is None


def test_select_menu_eof() -> None:
    with patch("builtins.input", side_effect=EOFError):
        result = select_menu("Choose:", ["a", "b"])
    assert result is None


def test_confirm_yes() -> None:
    with patch("builtins.input", return_value="y"):
        assert confirm("Proceed?") is True


def test_confirm_yes_upper() -> None:
    with patch("builtins.input", return_value="Y"):
        assert confirm("Proceed?") is True


def test_confirm_no() -> None:
    with patch("builtins.input", return_value="n"):
        assert confirm("Proceed?") is False


def test_confirm_default_no() -> None:
    with patch("builtins.input", return_value=""):
        assert confirm("Proceed?") is False
