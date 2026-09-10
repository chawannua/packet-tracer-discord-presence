"""
Pytest configuration and environment mocks for test isolation.
"""
import os
import sys
from unittest.mock import MagicMock

# Keep the suite from writing the real .daemon.lock into the project directory.
os.environ["PT_PRESENCE_TESTING"] = "1"

# If psutil is not installed in the current environment, provide a mock module
if "psutil" not in sys.modules:
    try:
        import psutil  # noqa: F401
    except ImportError:
        psutil_mock = MagicMock()
        class NoSuchProcess(Exception):
            def __init__(self, pid=None, name=None, msg=None):
                self.pid = pid
                self.name = name
                super().__init__(msg or f"PID {pid}")

        class AccessDenied(Exception):
            def __init__(self, pid=None, name=None, msg=None):
                self.pid = pid
                self.name = name
                super().__init__(msg or f"Access denied for PID {pid}")

        class ZombieProcess(Exception):
            def __init__(self, pid=None, name=None, ppid=None, msg=None):
                self.pid = pid
                self.name = name
                self.ppid = ppid
                super().__init__(msg or f"Zombie PID {pid}")

        psutil_mock.NoSuchProcess = NoSuchProcess
        psutil_mock.AccessDenied = AccessDenied
        psutil_mock.ZombieProcess = ZombieProcess
        psutil_mock.STATUS_ZOMBIE = "zombie"
        sys.modules["psutil"] = psutil_mock

# If pypresence is not installed in the current environment, provide a mock module
if "pypresence" not in sys.modules:
    try:
        import pypresence  # noqa: F401
    except ImportError:
        pypresence_mock = MagicMock()
        exceptions_mock = MagicMock()

        class DiscordNotFound(Exception):
            pass

        class InvalidID(Exception):
            pass

        class PipeClosed(Exception):
            pass

        exceptions_mock.DiscordNotFound = DiscordNotFound
        exceptions_mock.InvalidID = InvalidID
        exceptions_mock.PipeClosed = PipeClosed

        pypresence_mock.exceptions = exceptions_mock
        pypresence_mock.Presence = MagicMock
        sys.modules["pypresence"] = pypresence_mock
        sys.modules["pypresence.exceptions"] = exceptions_mock

# If pygetwindow cannot connect to display (e.g. headless Linux CI), provide a mock
try:
    import pygetwindow as gw
    gw.getAllWindows()
except Exception:
    gw_mock = MagicMock()
    gw_mock.getWindowsWithTitle = MagicMock(return_value=[])
    gw_mock.getAllWindows = MagicMock(return_value=[])
    sys.modules["pygetwindow"] = gw_mock
