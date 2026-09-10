"""
End-to-end process lifecycle tests: run a real child process, make the
detector see it as "Packet Tracer" (via a controlled psutil.process_iter
stand-in rather than renaming a real exe, which breaks DLL loading and
looks like the renamed-system-binary pattern AV heuristics flag), run the
actual daemon loop against it, kill it, and assert the daemon detects the
closure and exits promptly with zero leftover processes. This is the
regression test for the hang-on-close bug.
"""
import subprocess
import sys
import threading
import time
from unittest.mock import patch

import psutil
import pytest

from packet_tracer_presence.window_parser import PacketTracerState

FAKE_PROCESS_NAME = "PacketTracer9.exe"  # already in KNOWN_PROCESS_NAMES


class _FakeProcView:
    """Wraps a real psutil.Process so is_running()/status() reflect genuine
    OS process state, while reporting a Packet Tracer-like name/info dict
    the detector will match — without touching any real system process."""

    def __init__(self, pid, name=FAKE_PROCESS_NAME):
        self._real = psutil.Process(pid)
        self.info = {
            "pid": pid,
            "name": name,
            "exe": None,
            "create_time": self._real.create_time(),
        }

    def is_running(self):
        return self._real.is_running()

    def status(self):
        return self._real.status()

    def cmdline(self):
        return self._real.cmdline()


def _process_iter_stub(pid):
    def side_effect(*args, **kwargs):
        if psutil.pid_exists(pid):
            try:
                return iter([_FakeProcView(pid)])
            except psutil.NoSuchProcess:
                return iter([])
        return iter([])
    return side_effect


@pytest.fixture
def fake_packet_tracer():
    """A real, unmodified child process the tests treat as 'Packet Tracer'."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    yield proc
    if proc.poll() is None:
        proc.kill()
        proc.wait(timeout=5)


def test_detector_finds_and_loses_real_process(fake_packet_tracer):
    from packet_tracer_presence.detector import ProcessDetector

    detector = ProcessDetector()

    with patch("psutil.process_iter", side_effect=_process_iter_stub(fake_packet_tracer.pid)):
        deadline = time.time() + 5
        found = False
        while time.time() < deadline:
            if detector.find_packet_tracer():
                found = True
                break
            time.sleep(0.1)

        assert found is True
        assert detector._cached_pid == fake_packet_tracer.pid

        fake_packet_tracer.kill()
        fake_packet_tracer.wait(timeout=5)

        deadline = time.time() + 5
        gone = False
        while time.time() < deadline:
            if not detector.find_packet_tracer():
                gone = True
                break
            time.sleep(0.1)

        assert gone is True

    assert psutil.pid_exists(fake_packet_tracer.pid) is False


def test_daemon_exits_promptly_when_process_closes(fake_packet_tracer):
    """Runs the real cli.main() loop against a real process and confirms it
    self-terminates within a bounded time after that process dies, with no
    leftover child processes — the actual regression this overhaul fixes."""
    from packet_tracer_presence import cli

    argv = ["packet_tracer_presence", "--interval", "0.2"]
    thread_exc = []

    def run():
        try:
            old_argv = sys.argv
            sys.argv = argv
            try:
                # The real ProcessDetector is deliberately left unpatched - it is
                # what this test exercises. RPCManager and WindowParser are not:
                # unpatched they open Discord's IPC pipe and set the developer's
                # actual Rich Presence, and drive real UIAutomation/COM scanning,
                # just from running the test suite.
                state = PacketTracerState(file_name="Project1", is_unsaved=False)
                with patch("psutil.process_iter", side_effect=_process_iter_stub(fake_packet_tracer.pid)), \
                        patch("packet_tracer_presence.cli.RPCManager"), \
                        patch("packet_tracer_presence.cli.WindowParser") as mock_parser_class:
                    mock_parser_class.return_value.get_active_activity.return_value = state
                    cli.main()
            finally:
                sys.argv = old_argv
        except BaseException as exc:  # capture for the main test thread
            thread_exc.append(exc)

    t = threading.Thread(target=run, daemon=True)
    t.start()

    # Give the loop at least one poll cycle to pick up the fake process.
    time.sleep(0.6)

    fake_packet_tracer.kill()
    fake_packet_tracer.wait(timeout=5)

    t.join(timeout=10)

    assert not t.is_alive(), "daemon loop failed to exit after Packet Tracer closed"
    assert thread_exc == []
    assert psutil.pid_exists(fake_packet_tracer.pid) is False
