import unittest
from unittest.mock import MagicMock, patch
from packet_tracer_presence.window_parser import WindowParser

class TestWindowParser(unittest.TestCase):
    def setUp(self):
        self.parser = WindowParser()
        
    @patch("pygetwindow.getAllWindows", return_value=[])
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_window_parser_empty(self, mock_pids, mock_windows):
        state = self.parser.get_active_activity()
        self.assertEqual(state.file_name, "Workspace")
        self.assertFalse(state.is_unsaved)

    @patch("pygetwindow.getAllWindows", side_effect=Exception("Error"))
    def test_window_parser_exception(self, mock_windows):
        state = self.parser.get_active_activity()
        self.assertEqual(state.file_name, "Workspace")
        self.assertFalse(state.is_unsaved)

    @patch("pygetwindow.getActiveWindow", return_value=None)
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_window_parser_named_saved_project(self, mock_pids, mock_active):
        mock_win = MagicMock()
        mock_win.title = "Cisco Packet Tracer - Campus_Network.pkt"
        mock_win._hWnd = 1
        with patch("pygetwindow.getAllWindows", return_value=[mock_win]):
            with patch("ctypes.windll.user32.GetWindowThreadProcessId", side_effect=lambda hwnd, pid: ctypes_assign(pid, 1234)):
                state = self.parser.get_active_activity()
                self.assertEqual(state.file_name, "Campus_Network.pkt")
                self.assertFalse(state.is_unsaved)
                self.assertEqual(state.file_type, "pkt")

    @patch("pygetwindow.getActiveWindow")
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_window_parser_activity_timer_and_device(self, mock_pids, mock_active):
        mock_active.return_value._hWnd = 2
        mock_win1 = MagicMock()
        mock_win1.title = "Cisco Packet Tracer - Lab_Activity.pka - PT Activity: 01:23:45"
        mock_win1._hWnd = 1
        
        mock_win2 = MagicMock()
        mock_win2.title = "Router0"
        mock_win2._hWnd = 2

        with patch("pygetwindow.getAllWindows", return_value=[mock_win1, mock_win2]):
            with patch("ctypes.windll.user32.GetWindowThreadProcessId", side_effect=lambda hwnd, pid: ctypes_assign(pid, 1234)):
                state = self.parser.get_active_activity()
                self.assertEqual(state.file_name, "Lab_Activity.pka")
                self.assertFalse(state.is_unsaved)
                self.assertEqual(state.file_type, "pka")
                self.assertEqual(state.activity_timer, "01:23:45")
                self.assertEqual(state.active_device, "Router0")
                self.assertEqual(state.device_type, "router")

def ctypes_assign(pid_ref, val):
    pid_ref._obj.value = val
    return 1

if __name__ == "__main__":
    unittest.main()
