import sys
import unittest
from pathlib import Path
from unittest import mock


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import startup


class _FakeKey:
    def __init__(self, store):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _FakeWinreg:
    HKEY_CURRENT_USER = object()
    KEY_READ = 1
    KEY_SET_VALUE = 2
    REG_SZ = 1

    def __init__(self):
        self.store = {}

    def OpenKey(self, root, path, reserved=0, access=0):
        return _FakeKey(self.store)

    def CreateKeyEx(self, root, path, reserved=0, access=0):
        return _FakeKey(self.store)

    def QueryValueEx(self, key, name):
        if name not in self.store:
            raise FileNotFoundError(name)
        return self.store[name], self.REG_SZ

    def SetValueEx(self, key, name, reserved, reg_type, value):
        self.store[name] = value

    def DeleteValue(self, key, name):
        if name not in self.store:
            raise FileNotFoundError(name)
        del self.store[name]


class StartupTests(unittest.TestCase):
    def test_get_launch_command_for_script_mode_points_to_main(self) -> None:
        command = startup.get_launch_command()
        self.assertIn("main.py", command)
        self.assertTrue(command.startswith('"'))

    def test_get_startup_command_includes_minimized_flag(self) -> None:
        command = startup.get_startup_command()
        self.assertIn("main.py", command)
        self.assertTrue(command.endswith(" --minimized"))

    def test_is_startup_enabled_ignores_case_and_extra_spaces(self) -> None:
        fake_winreg = _FakeWinreg()
        fake_winreg.store[startup.APP_NAME] = f"  {startup.get_startup_command().upper()}  "

        with mock.patch.object(startup, "_is_windows", return_value=True):
            with mock.patch.dict(sys.modules, {"winreg": fake_winreg}):
                self.assertTrue(startup.is_startup_enabled())

    def test_enable_and_disable_startup_registry_value(self) -> None:
        fake_winreg = _FakeWinreg()

        with mock.patch.object(startup, "_is_windows", return_value=True):
            with mock.patch.dict(sys.modules, {"winreg": fake_winreg}):
                startup.set_startup_enabled(True)
                self.assertTrue(startup.is_startup_enabled())
                self.assertEqual(fake_winreg.store[startup.APP_NAME], startup.get_startup_command())

                startup.set_startup_enabled(False)
                self.assertFalse(startup.is_startup_enabled())


if __name__ == "__main__":
    unittest.main()
