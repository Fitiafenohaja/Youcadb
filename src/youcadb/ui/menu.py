"""Interactive menus with keyboard + mouse support (stub)."""

from __future__ import annotations


def select_menu(prompt: str, options: list[str]) -> str | None:
    """Display an interactive selection menu.

    Uses *questionary* if available for mouse support; falls back to a
    plain numbered-list with keyboard input.

    TODO: integrate questionary / InquirerPy once the UI layer is fleshed out.
    """
    # Fallback: simple numbered list
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


def confirm(prompt: str) -> bool:
    """Ask for yes/no confirmation."""
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in ("y", "yes")
