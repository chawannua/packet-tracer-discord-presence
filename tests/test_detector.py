"""
Unit tests for packet_tracer_presence.detector
"""
from unittest.mock import MagicMock, patch
import psutil
from packet_tracer_presence.detector import ProcessDetector


def test_detector_init():
    detector = ProcessDetector()
    assert detector._cached_pid is None
    assert detector._cached_process is None


def test_find_packet_tracer_with_valid_cache():
    detector = ProcessDetector()
    mock_proc = MagicMock()
    mock_proc.status.return_value = "running"
    detector._cached_pid = 1234
    detector._cached_process = mock_proc

    with patch("psutil.pid_exists", return_value=True):
        assert detector.find_packet_tracer() is True
        assert detector._cached_pid == 1234


def test_find_packet_tracer_with_stale_cache():
    detector = ProcessDetector()
    mock_proc = MagicMock()
    mock_proc.status.side_effect = psutil.NoSuchProcess(pid=1234)
    detector._cached_pid = 1234
    detector._cached_process = mock_proc

    with patch("psutil.pid_exists", return_value=True), \
         patch("psutil.process_iter", return_value=[]):
        assert detector.find_packet_tracer() is False
        assert detector._cached_pid is None
        assert detector._cached_process is None


def test_find_packet_tracer_scan_found():
    detector = ProcessDetector()
    mock_proc = MagicMock()
    mock_proc.info = {
        "pid": 5678,
        "name": "PacketTracer.exe",
        "exe": r"C:\Program Files\Cisco Packet Tracer 8.2\bin\PacketTracer.exe"
    }

    with patch("psutil.process_iter", return_value=[mock_proc]):
        assert detector.find_packet_tracer() is True
        assert detector._cached_pid == 5678
        assert detector._cached_process == mock_proc
        assert detector._running_exe_path == r"C:\Program Files\Cisco Packet Tracer 8.2\bin\PacketTracer.exe"


def test_find_packet_tracer_scan_not_found():
    detector = ProcessDetector()
    mock_proc = MagicMock()
    mock_proc.info = {
        "pid": 9999,
        "name": "chrome.exe",
        "exe": r"C:\Program Files\Google\Chrome\chrome.exe"
    }

    with patch("psutil.process_iter", return_value=[mock_proc]):
        assert detector.find_packet_tracer() is False
        assert detector._cached_pid is None


def test_find_packet_tracer_scan_handles_exceptions():
    detector = ProcessDetector()

    def mock_iter_gen(*args, **kwargs):
        mock_dead = MagicMock()
        mock_dead.info.side_effect = psutil.NoSuchProcess(pid=1)
        yield mock_dead

        mock_alive = MagicMock()
        mock_alive.info = {
            "pid": 4321,
            "name": "PacketTracer8.exe",
            "exe": r"C:\PacketTracer8.exe"
        }
        yield mock_alive

    with patch("psutil.process_iter", side_effect=mock_iter_gen):
        assert detector.find_packet_tracer() is True
        assert detector._cached_pid == 4321


def test_find_packet_tracer_cache_rejects_reused_pid():
    """is_running() is create_time-aware: if the cached PID got reused by an
    unrelated process after Packet Tracer exited, it must report not-running
    rather than trusting a stale pid_exists()-style check."""
    detector = ProcessDetector()
    mock_proc = MagicMock()
    mock_proc.is_running.return_value = False  # psutil detected the PID was reused
    detector._cached_pid = 1234
    detector._cached_process = mock_proc

    with patch("psutil.process_iter", return_value=[]):
        assert detector.find_packet_tracer() is False
        assert detector._cached_pid is None
        assert detector._cached_process is None


def test_find_packet_tracer_prefers_oldest_of_multiple_matches():
    detector = ProcessDetector()

    newer = MagicMock()
    newer.info = {"pid": 111, "name": "PacketTracer.exe", "exe": r"C:\PT\PacketTracer.exe", "create_time": 200.0}
    newer.status.return_value = "running"

    older = MagicMock()
    older.info = {"pid": 222, "name": "PacketTracer.exe", "exe": r"C:\PT\PacketTracer.exe", "create_time": 100.0}
    older.status.return_value = "running"

    with patch("psutil.process_iter", return_value=[newer, older]):
        assert detector.find_packet_tracer() is True
        assert detector._cached_pid == 222


def test_get_installation_paths():
    detector = ProcessDetector()
    detector._running_exe_path = r"C:\Program Files\Cisco Packet Tracer\bin\PacketTracer.exe"

    with patch("os.environ.get", return_value=r"C:\fake"), \
         patch("glob.glob", return_value=[]), \
         patch("os.path.isdir", return_value=False):
        paths = detector.get_installation_paths()
        assert r"C:\Program Files\Cisco Packet Tracer\bin" in paths
