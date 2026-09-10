import pytest
from unittest.mock import patch, MagicMock
from packet_tracer_presence.cli import main

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
         mock_parser.get_active_project.return_value = ("Project1", False)
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         mock_detector.find_packet_tracer.assert_called_once()
         mock_parser.get_active_project.assert_called_once()
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
         mock_parser.get_active_project.return_value = (None, False)
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         mock_rpc.update.assert_called_once()
         assert mock_rpc.update.call_args[0][0] == "Workspace"

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
         mock_parser.get_active_project.return_value = (None, False)
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         mock_rpc.update.assert_called_once()
         assert mock_rpc.update.call_args[0][0] == "Topology.pka"

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
         mock_parser.get_active_project.return_value = (None, False)
         
         mock_rpc = mock_rpc_class.return_value
         
         main()
         
         assert mock_detector.find_packet_tracer.call_count == 2
         mock_rpc.clear.assert_called_once()
