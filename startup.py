from __future__ import annotations

import sys
from pathlib import Path


APP_NAME = "LanShutdownControl"
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def get_launch_command(start_minimized: bool = False) -> str:
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        command = _quote(str(executable))
    else:
        main_script = Path(__file__).resolve().parent / "main.py"
        command = f'{_quote(sys.executable)} {_quote(str(main_script))}'

    if start_minimized:
        command = f"{command} --minimized"
    return command


def get_startup_command() -> str:
    return get_launch_command(start_minimized=True)


def is_startup_enabled(app_name: str = APP_NAME) -> bool:
    if not _is_windows():
        return False

    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, app_name)
    except FileNotFoundError:
        return False

    return _normalize_command(value) == _normalize_command(get_startup_command())


def set_startup_enabled(enabled: bool, app_name: str = APP_NAME) -> None:
    if not _is_windows():
        raise RuntimeError("Windows startup registration is only supported on Windows.")

    import winreg

    access = getattr(winreg, "KEY_SET_VALUE", 0)
    create_key = getattr(winreg, "CreateKeyEx", None)
    open_key = getattr(winreg, "OpenKey")
    key_context = (
        create_key(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, access)
        if create_key is not None
        else open_key(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, access)
    )

    with key_context as key:
        if enabled:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, get_startup_command())
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass


def sync_startup_setting(enabled: bool, app_name: str = APP_NAME) -> None:
    if enabled != is_startup_enabled(app_name):
        set_startup_enabled(enabled, app_name)


def _quote(text: str) -> str:
    return f'"{text}"'


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().split()).casefold()
