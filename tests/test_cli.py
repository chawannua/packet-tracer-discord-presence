import pytest
from unittest.mock import patch, MagicMock
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
