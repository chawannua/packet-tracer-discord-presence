"""
Unit tests for packet_tracer_presence.rpc_manager
"""
import time
from unittest.mock import MagicMock, patch
from pypresence.exceptions import DiscordNotFound, PipeClosed
from packet_tracer_presence.rpc_manager import RPCManager

def test_rpc_manager_init():
    with patch("packet_tracer_presence.rpc_manager.Presence") as mock_presence:
        rpc = RPCManager(client_id="12345")
        mock_presence.assert_called_once_with("12345")
        assert rpc.client_id == "12345"
        assert rpc.connected is False

def test_rpc_connect_success():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        assert rpc.connect() is True
        assert rpc.connected is True
        rpc.presence.connect.assert_called_once()
        assert rpc.connect() is True
        assert rpc.presence.connect.call_count == 1

def test_rpc_connect_failure_and_backoff():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.presence.connect.side_effect = DiscordNotFound()
        assert rpc.connect() is False
        assert rpc.connected is False
        assert rpc._connect_retry_time > time.time()
        assert rpc.connect() is False
        assert rpc.presence.connect.call_count == 1

def test_rpc_update_success():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000,
                   file_type="pkt", active_device="Router0", device_type="router", activity_timer="01:20:00")

        rpc.presence.update.assert_called_once_with(
            details="Topology: NetworkLab.pkt (Timer: 01:20:00)",
            state="Configuring: Router0",
            start=1000,
            large_image="pt_logo",
            large_text="Cisco Packet Tracer",
            small_image="router",
            small_text="Configuring Router0"
        )
        assert rpc._last_state["project_name"] == "NetworkLab.pkt"
        assert rpc._last_state["activity_timer"] == "01:20:00"

def test_rpc_update_unsaved_state():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(project_name="Topology.pkt", is_unsaved=True, start_time=1000,
                   file_type="pkt", active_device=None, device_type="pt_logo", activity_timer=None)

        rpc.presence.update.assert_called_once_with(
            details="Designing New Topology",
            state="Designing Topology",
            start=1000,
            large_image="pt_logo",
            large_text="Cisco Packet Tracer",
            small_image="pt_logo",
            small_text="Cisco Packet Tracer"
        )

def test_rpc_update_rate_limiting():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = time.time()

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000)
        rpc.presence.update.assert_not_called()

def test_rpc_update_state_deduplication():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0
        
        state = {
            "project_name": "NetworkLab.pkt",
            "is_unsaved": False,
            "file_type": "unknown",
            "active_device": None,
            "device_type": "pt_logo",
            "activity_timer": None
        }
        rpc._last_state = state

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000)
        rpc.presence.update.assert_not_called()

def test_rpc_update_pipe_closed_recovery():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0
        rpc.presence.update.side_effect = PipeClosed()

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000)
        assert rpc.connected is False

def test_rpc_clear_and_close():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc.clear()
        rpc.presence.clear.assert_called_once()
        rpc.close()
        rpc.presence.close.assert_called_once()
        assert rpc.connected is False
