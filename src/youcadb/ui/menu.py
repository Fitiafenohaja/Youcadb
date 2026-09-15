"""Interactive menus with keyboard + mouse support."""

from __future__ import annotations


def select_menu(prompt: str, options: list[str]) -> str | None:
    """Display an interactive selection menu.

    Uses *questionary* if available for rich keyboard/mouse support;
    falls back to a plain numbered-list with keyboard input.
    """
    try:
        import questionary

        result = questionary.select(prompt, choices=options).ask()
        return result if isinstance(result, str) and result else None
    except ImportError:
        pass
    except Exception:
        pass

    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    try:
        choice = input("Select an option: ").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except (ValueError, EOFError):
        pass
    return None


def confirm(prompt: str, default: bool = False) -> bool:
    """Ask for yes/no confirmation."""
    try:
        import questionary

        result = questionary.confirm(prompt, default=default).ask()
        return bool(result)
    except ImportError:
        pass
    except Exception:
        pass

    suffix = " [Y/n]: " if default else " [y/N]: "
    answer = input(f"{prompt}{suffix}").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def password_input(prompt: str) -> str:
    """Prompt for a password without echoing."""
    try:
        import questionary

        result = questionary.password(prompt).ask()
        return result if isinstance(result, str) else ""
    except ImportError:
        pass
    except Exception:
        pass

    import getpass

    return getpass.getpass(f"{prompt}: ")


def text_input(prompt: str, default: str = "") -> str:
    """Prompt for text input."""
    try:
        import questionary

        result = questionary.text(prompt, default=default).ask()
        if isinstance(result, str):
            return result if result else default
        return default
    except ImportError:
        pass
    except Exception:
        pass

    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()
