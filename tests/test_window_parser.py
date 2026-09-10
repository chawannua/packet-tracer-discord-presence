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

    def test_parse_cli_modes(self):
        # 1. Console Connected
        self.assertEqual(self.parser.parse_cli_mode("Press RETURN to get started"), "[Console Connected]")
        self.assertEqual(self.parser.parse_cli_mode("Press RETURN to get started!"), "[Console Connected]")
        self.assertEqual(self.parser.parse_cli_mode("Booting IOS...\nPress RETURN to get started!\n"), "[Console Connected]")

        # 2. Interface Config
        self.assertEqual(self.parser.parse_cli_mode("Router(config-if)#"), "[Interface Config]")
        self.assertEqual(self.parser.parse_cli_mode("Switch(config-if)# "), "[Interface Config]")

        # 3. Sub-Interface Config
        self.assertEqual(self.parser.parse_cli_mode("Router(config-subif)#"), "[Sub-Interface Config]")

        # 4. Routing Config
        self.assertEqual(self.parser.parse_cli_mode("Router(config-router)#"), "[Routing Config]")

        # 5. Line/Console Config
        self.assertEqual(self.parser.parse_cli_mode("Router(config-line)#"), "[Line/Console Config]")

        # 6. VLAN Config
        self.assertEqual(self.parser.parse_cli_mode("Switch(config-vlan)#"), "[VLAN Config]")

        # 7. DHCP Config
        self.assertEqual(self.parser.parse_cli_mode("Router(dhcp-config)#"), "[DHCP Config]")

        # 8. Global Config
        self.assertEqual(self.parser.parse_cli_mode("Router(config)#"), "[Global Config]")
        self.assertEqual(self.parser.parse_cli_mode("Switch(config)# "), "[Global Config]")

        # 9. Command Shell
        self.assertEqual(self.parser.parse_cli_mode("C:\\>"), "[Command Shell]")
        self.assertEqual(self.parser.parse_cli_mode("C:\\Users\\PC> "), "[Command Shell]")
        self.assertEqual(self.parser.parse_cli_mode("D:\\test\\dir>"), "[Command Shell]")

        # 10. Privileged Mode
        self.assertEqual(self.parser.parse_cli_mode("Router#"), "[Privileged Mode]")
        self.assertEqual(self.parser.parse_cli_mode("Switch# "), "[Privileged Mode]")

        # 11. User EXEC Mode
        self.assertEqual(self.parser.parse_cli_mode("Router>"), "[User EXEC Mode]")
        self.assertEqual(self.parser.parse_cli_mode("Switch> "), "[User EXEC Mode]")

        # Edge cases
        self.assertIsNone(self.parser.parse_cli_mode(""))
        self.assertIsNone(self.parser.parse_cli_mode("   \n\t  "))
        self.assertIsNone(self.parser.parse_cli_mode("Just some random output"))

    @patch("pygetwindow.getAllWindows", return_value=[])
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value=set())
    def test_default_workspace_tool_when_no_device(self, mock_pids, mock_windows):
        state = self.parser.get_active_activity()
        self.assertIsNone(state.active_device)
        self.assertEqual(state.workspace_tool, "Designing Logical Topology (Realtime)")

    @patch("packet_tracer_presence.window_parser.auto")
    @patch("pygetwindow.getActiveWindow", return_value=None)
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_workspace_canvas_tools_uia(self, mock_pids, mock_active, mock_auto):
        # Mock main window with "Add Simple PDU (P)" toggled
        mock_win_ctrl = MagicMock()
        mock_win_ctrl.Name = "Cisco Packet Tracer"
        mock_win_ctrl.ClassName = "CAppWindow"

        mock_tool_ctrl = MagicMock()
        mock_tool_ctrl.Name = "Add Simple PDU (P)"
        mock_toggle = MagicMock()
        mock_toggle.ToggleState = 1
        mock_tool_ctrl.GetPattern.return_value = mock_toggle

        mock_auto.GetRootControl().GetChildren.return_value = [mock_win_ctrl]
        mock_auto.WalkControl.return_value = [(mock_tool_ctrl, 0)]

        mock_pt_win = MagicMock()
        mock_pt_win.title = "Cisco Packet Tracer - Topology.pkt"
        mock_pt_win._hWnd = 1

        with patch("pygetwindow.getAllWindows", return_value=[mock_pt_win]):
            with patch("ctypes.windll.user32.GetWindowThreadProcessId", side_effect=lambda hwnd, pid: ctypes_assign(pid, 1234)):
                state = self.parser.get_active_activity()
                self.assertEqual(state.workspace_tool, "Testing Connectivity (Simple PDU Ping)")

    @patch("packet_tracer_presence.window_parser.auto")
    @patch("pygetwindow.getActiveWindow")
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_device_terminal_cli_mode_uia(self, mock_pids, mock_active, mock_auto):
        mock_active.return_value._hWnd = 2

        mock_win1 = MagicMock()
        mock_win1.title = "Cisco Packet Tracer - Lab.pka"
        mock_win1._hWnd = 1
        
        mock_win2 = MagicMock()
        mock_win2.title = "Router0"
        mock_win2._hWnd = 2

        # Mock device window with CLI tab and (config-if)# prompt
        mock_dev_ctrl = MagicMock()
        mock_dev_ctrl.Name = "Router0"
        mock_dev_ctrl.ClassName = "CRouterDialog"

        mock_tab = MagicMock()
        mock_tab.ClassName = "QTabBar"
        mock_tab.Name = "CLI"
        mock_tab.GetPattern.return_value = None

        mock_cmd = MagicMock()
        mock_cmd.ClassName = "CCommandLine"
        mock_cmd_val = MagicMock()
        mock_cmd_val.Value = "Router(config)# interface g0/0\nRouter(config-if)# "
        mock_cmd.GetPattern.return_value = mock_cmd_val

        mock_auto.GetRootControl().GetChildren.return_value = [mock_dev_ctrl]
        mock_auto.WalkControl.return_value = [(mock_tab, 0), (mock_cmd, 1)]

        with patch("pygetwindow.getAllWindows", return_value=[mock_win1, mock_win2]):
            with patch("ctypes.windll.user32.GetWindowThreadProcessId", side_effect=lambda hwnd, pid: ctypes_assign(pid, 1234)):
                state = self.parser.get_active_activity()
                self.assertEqual(state.active_device, "Router0")
                self.assertEqual(state.active_sub_app, "CLI [Interface Config]")

    @patch("packet_tracer_presence.window_parser.auto")
    @patch("pygetwindow.getActiveWindow")
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_device_tab_detection_uia(self, mock_pids, mock_active, mock_auto):
        mock_active.return_value._hWnd = 2

        mock_win1 = MagicMock()
        mock_win1.title = "Cisco Packet Tracer - Test.pkt"
        mock_win1._hWnd = 1
        
        mock_win2 = MagicMock()
        mock_win2.title = "Switch0"
        mock_win2._hWnd = 2

        mock_dev_ctrl = MagicMock()
        mock_dev_ctrl.Name = "Switch0"
        mock_dev_ctrl.ClassName = "CSwitchDialog"

        mock_tab = MagicMock()
        mock_tab.ClassName = "QTabBar"
        mock_tab.Name = "Config"
        mock_tab.GetPattern.return_value = None

        mock_auto.GetRootControl().GetChildren.return_value = [mock_dev_ctrl]
        mock_auto.WalkControl.return_value = [(mock_tab, 0)]

        with patch("pygetwindow.getAllWindows", return_value=[mock_win1, mock_win2]):
            with patch("ctypes.windll.user32.GetWindowThreadProcessId", side_effect=lambda hwnd, pid: ctypes_assign(pid, 1234)):
                state = self.parser.get_active_activity()
                self.assertEqual(state.active_device, "Switch0")
                self.assertEqual(state.active_sub_app, "Config Tab")

    @patch("packet_tracer_presence.window_parser.auto")
    @patch("pygetwindow.getActiveWindow")
    @patch("packet_tracer_presence.window_parser.WindowParser._get_pt_pids", return_value={1234})
    def test_desktop_applet_detection_uia(self, mock_pids, mock_active, mock_auto):
        mock_active.return_value._hWnd = 2

        mock_win1 = MagicMock()
        mock_win1.title = "Cisco Packet Tracer - Test.pkt"
        mock_win1._hWnd = 1
        
        mock_win2 = MagicMock()
        mock_win2.title = "PC0"
        mock_win2._hWnd = 2

        mock_dev_ctrl = MagicMock()
        mock_dev_ctrl.Name = "PC0"
        mock_dev_ctrl.ClassName = "CWorkstationDialog"

        mock_label = MagicMock()
        mock_label.ClassName = "QLabel"
        mock_label.AutomationId = "m_titleLabel"
        mock_label.Name = "Command Prompt"
        mock_label.GetPattern.return_value = None

        mock_cmd = MagicMock()
        mock_cmd.ClassName = "CCommandLine"
        mock_cmd_val = MagicMock()
        mock_cmd_val.Value = "C:\\Users\\PC> "
        mock_cmd.GetPattern.return_value = mock_cmd_val

        mock_auto.GetRootControl().GetChildren.return_value = [mock_dev_ctrl]
        mock_auto.WalkControl.return_value = [(mock_label, 0), (mock_cmd, 1)]

        with patch("pygetwindow.getAllWindows", return_value=[mock_win1, mock_win2]):
            with patch("ctypes.windll.user32.GetWindowThreadProcessId", side_effect=lambda hwnd, pid: ctypes_assign(pid, 1234)):
                state = self.parser.get_active_activity()
                self.assertEqual(state.active_device, "PC0")
                self.assertEqual(state.active_sub_app, "Command Prompt [Command Shell]")

def ctypes_assign(pid_ref, val):
    pid_ref._obj.value = val
    return 1

if __name__ == "__main__":
    unittest.main()
