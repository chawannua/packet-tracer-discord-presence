import logging
import os
import pytest
from unittest.mock import patch, MagicMock
from packet_tracer_presence import cli
from packet_tracer_presence.cli import main
from packet_tracer_presence.window_parser import PacketTracerState

def test_cli_main_loop():
    test_args = ["packet_tracer_presence", "--interval", "10", "--client-id", "123", "--verbose"]
    
    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep', side_effect=KeyboardInterrupt) as mock_sleep:
         
         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.return_value = True
         
         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Project1", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         mock_detector.find_packet_tracer.assert_called_once()
         mock_parser.get_active_activity.assert_called_once()
         mock_rpc.update.assert_called_once()
         mock_rpc.close.assert_called_once()

def test_cli_main_loop_no_project():
    test_args = ["packet_tracer_presence"]
    
    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep', side_effect=KeyboardInterrupt) as mock_sleep:
         
         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.return_value = True
         mock_detector.get_running_project_file.return_value = None
         
         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Workspace", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         mock_rpc.update.assert_called_once()
         kwargs = mock_rpc.update.call_args[1]
         assert kwargs["project_name"] == "Workspace"

def test_cli_main_loop_cmdline_fallback():
    test_args = ["packet_tracer_presence"]
    
    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep', side_effect=KeyboardInterrupt) as mock_sleep:
         
         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.return_value = True
         mock_detector.get_running_project_file.return_value = "Topology.pka"
         
         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Workspace", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         mock_rpc.update.assert_called_once()
         kwargs = mock_rpc.update.call_args[1]
         assert kwargs["project_name"] == "Topology.pka"

def test_cli_main_loop_closed():
    test_args = ["packet_tracer_presence"]
    
    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep', side_effect=[None, KeyboardInterrupt]) as mock_sleep:
         
         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.side_effect = [True, False]
         
         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Workspace", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         assert mock_detector.find_packet_tracer.call_count == 2
         mock_rpc.clear.assert_called_once()

def test_cli_main_loop_default_exits_on_close():
    """exit-on-close is now the default (no flag needed) — this is the fix
    for the daemon hanging forever when launched headlessly via pythonw.exe,
    which never passed --exit-on-close."""
    test_args = ["packet_tracer_presence"]

    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep') as mock_sleep:

         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.side_effect = [True, False]

         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Workspace", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state

         mock_rpc = mock_rpc_class.return_value

         main()

         assert mock_detector.find_packet_tracer.call_count == 2
         mock_rpc.clear.assert_called_once()
         mock_rpc.close.assert_called_once()
         # Only one sleep call: the loop must break as soon as closure is
         # detected, not sleep once more before checking again.
         assert mock_sleep.call_count == 1

def test_cli_main_loop_no_exit_on_close_keeps_running():
    test_args = ["packet_tracer_presence", "--no-exit-on-close"]

    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep', side_effect=[None, KeyboardInterrupt]) as mock_sleep:

         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.side_effect = [True, False]

         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Workspace", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state

         mock_rpc = mock_rpc_class.return_value

         main()

         # Loop kept going past closure (didn't break) until KeyboardInterrupt.
         assert mock_detector.find_packet_tracer.call_count == 2
         mock_rpc.clear.assert_called_once()
         assert mock_sleep.call_count == 2

def test_ensure_single_instance_writes_lock_file(tmp_path):
    """Regression: the lock file was never written in production, because the
    guard probed for `unittest` in sys.modules and comtypes imports it."""
    lock = tmp_path / ".daemon.lock"

    with patch('packet_tracer_presence.cli._running_under_tests', return_value=False), \
         patch('packet_tracer_presence.cli.LOCK_FILE', str(lock)):
        assert cli.ensure_single_instance() is True

    assert lock.read_text().strip() == str(os.getpid())


def test_ensure_single_instance_refuses_when_live_instance_running(tmp_path):
    lock = tmp_path / ".daemon.lock"
    lock.write_text("4242")
    live = MagicMock()
    live.name.return_value = "pythonw.exe"

    with patch('packet_tracer_presence.cli._running_under_tests', return_value=False), \
         patch('packet_tracer_presence.cli.LOCK_FILE', str(lock)), \
         patch('psutil.pid_exists', return_value=True), \
         patch('psutil.Process', return_value=live):
        assert cli.ensure_single_instance() is None

    assert lock.read_text().strip() == "4242"


def test_ensure_single_instance_reclaims_stale_lock(tmp_path):
    lock = tmp_path / ".daemon.lock"
    lock.write_text("4242")

    with patch('packet_tracer_presence.cli._running_under_tests', return_value=False), \
         patch('packet_tracer_presence.cli.LOCK_FILE', str(lock)), \
         patch('psutil.pid_exists', return_value=False):
        assert cli.ensure_single_instance() is True

    assert lock.read_text().strip() == str(os.getpid())


def test_is_own_process_name_covers_launch_paths_but_not_packet_tracer():
    assert cli._is_own_process_name("pythonw.exe")
    assert cli._is_own_process_name("PacketTracerPresence.exe")
    # Packet Tracer itself must never be mistaken for another copy of the daemon.
    assert not cli._is_own_process_name("PacketTracer.exe")


def test_main_mutes_comtypes_logger():
    logging.getLogger("comtypes").setLevel(logging.NOTSET)
    test_args = ["packet_tracer_presence"]

    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser'), \
         patch('packet_tracer_presence.cli.RPCManager'), \
         patch('time.sleep', side_effect=KeyboardInterrupt):

         mock_detector_class.return_value.find_packet_tracer.return_value = False
         main()

    assert logging.getLogger("comtypes").getEffectiveLevel() >= logging.WARNING


def test_main_uses_rotating_log_handler():
    test_args = ["packet_tracer_presence"]

    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.RotatingFileHandler') as mock_handler, \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser'), \
         patch('packet_tracer_presence.cli.RPCManager'), \
         patch('time.sleep', side_effect=KeyboardInterrupt):

         mock_detector_class.return_value.find_packet_tracer.return_value = False
         main()

    mock_handler.assert_called_once()
    kwargs = mock_handler.call_args[1]
    assert kwargs["maxBytes"] == cli.LOG_MAX_BYTES
    assert kwargs["backupCount"] == cli.LOG_BACKUP_COUNT


def test_idle_poll_uses_slower_interval_while_packet_tracer_closed():
    """Resident mode must not scan the process table at the active-session rate."""
    test_args = ["packet_tracer_presence", "--no-exit-on-close"]

    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser'), \
         patch('packet_tracer_presence.cli.RPCManager'), \
         patch('time.sleep', side_effect=KeyboardInterrupt) as mock_sleep:

         mock_detector_class.return_value.find_packet_tracer.return_value = False
         main()

         mock_sleep.assert_called_once_with(15.0)


def test_cli_main_loop_exit_on_close():
    test_args = ["packet_tracer_presence", "--exit-on-close"]
    
    with patch('sys.argv', test_args), \
         patch('packet_tracer_presence.cli.ProcessDetector') as mock_detector_class, \
         patch('packet_tracer_presence.cli.WindowParser') as mock_parser_class, \
         patch('packet_tracer_presence.cli.RPCManager') as mock_rpc_class, \
         patch('time.sleep') as mock_sleep:
         
         mock_detector = mock_detector_class.return_value
         mock_detector.find_packet_tracer.side_effect = [True, False]
         
         mock_parser = mock_parser_class.return_value
         state = PacketTracerState(file_name="Workspace", is_unsaved=False)
         mock_parser.get_active_activity.return_value = state
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         assert mock_detector.find_packet_tracer.call_count == 2
         mock_rpc.clear.assert_called_once()
         mock_rpc.close.assert_called_once()


def test_resolve_project_start_resets_on_real_file_switch():
    """Opening a different topology restarts the elapsed timer."""
    start, project = cli.resolve_project_start("LabB.pkt", "LabA.pkt", 1000, 5000)
    assert start == 5000
    assert project == "LabB.pkt"


def test_resolve_project_start_keeps_timer_on_same_file():
    start, project = cli.resolve_project_start("LabA.pkt", "LabA.pkt", 1000, 5000)
    assert start == 1000
    assert project == "LabA.pkt"


@pytest.mark.parametrize("transient", ["", None, "Workspace"])
def test_resolve_project_start_ignores_transient_blank_readings(transient):
    """A failed title read must not restart the clock or forget the project."""
    start, project = cli.resolve_project_start(transient, "LabA.pkt", 1000, 5000)
    assert start == 1000
    assert project == "LabA.pkt"


def test_resolve_project_start_first_sighting_keeps_launch_time():
    """The first real reading adopts the project without discarding launch time."""
    start, project = cli.resolve_project_start("LabA.pkt", None, 1000, 5000)
    assert start == 1000
    assert project == "LabA.pkt"


def test_resolve_project_start_survives_blank_between_two_reads_of_same_file():
    """LabA -> blank -> LabA is not a file switch."""
    start, project = cli.resolve_project_start("LabA.pkt", None, 1000, 4000)
    start, project = cli.resolve_project_start("Workspace", project, start, 5000)
    start, project = cli.resolve_project_start("LabA.pkt", project, start, 6000)
    assert start == 1000
    assert project == "LabA.pkt"
