"""
Unit tests for packet_tracer_presence.window_parser
"""
from unittest.mock import MagicMock, patch
from packet_tracer_presence.window_parser import WindowParser


def test_window_parser_empty():
    parser = WindowParser()
    with patch("pygetwindow.getWindowsWithTitle", return_value=[]):
        name, is_unsaved = parser.get_active_project()
        assert name is None
        assert is_unsaved is False


def test_window_parser_exception():
    parser = WindowParser()
    with patch("pygetwindow.getWindowsWithTitle", side_effect=RuntimeError("X11 display not available")):
        name, is_unsaved = parser.get_active_project()
        assert name is None
        assert is_unsaved is False


def test_window_parser_untitled_default():
    parser = WindowParser()
    mock_win = MagicMock()
    mock_win.title = "Cisco Packet Tracer"
    with patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        name, is_unsaved = parser.get_active_project()
        assert name == "Untitled"
        assert is_unsaved is False


def test_window_parser_named_saved_project():
    parser = WindowParser()
    mock_win = MagicMock()
    mock_win.title = "Cisco Packet Tracer - [Campus_Network.pkt]"
    with patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        name, is_unsaved = parser.get_active_project()
        assert name == "Campus_Network.pkt"
        assert is_unsaved is False


def test_window_parser_named_unsaved_project():
    parser = WindowParser()
    mock_win = MagicMock()
    mock_win.title = "Cisco Packet Tracer - [Datacenter_Core.pkt*]"
    with patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        name, is_unsaved = parser.get_active_project()
        assert name == "Datacenter_Core.pkt"
        assert is_unsaved is True


def test_window_parser_empty_brackets():
    parser = WindowParser()
    mock_win = MagicMock()
    mock_win.title = "Cisco Packet Tracer - []"
    with patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        name, is_unsaved = parser.get_active_project()
        assert name == "Untitled"
        assert is_unsaved is False


def test_window_parser_asterisk_only():
    parser = WindowParser()
    mock_win = MagicMock()
    mock_win.title = "Cisco Packet Tracer - [*]"
    with patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        name, is_unsaved = parser.get_active_project()
        assert name == "Untitled"
        assert is_unsaved is True


def test_window_parser_non_matching_window():
    parser = WindowParser()
    mock_win = MagicMock()
    mock_win.title = "Not Packet Tracer Window"
    with patch("pygetwindow.getWindowsWithTitle", return_value=[mock_win]):
        name, is_unsaved = parser.get_active_project()
        assert name is None
        assert is_unsaved is False
