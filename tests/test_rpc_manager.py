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
            details="Topology: NetworkLab.pkt (01:20:00)",
            state="Configuring Router0",
            start=1000,
            large_image="packet_tracer",
            large_text="Cisco Packet Tracer | Realtime (Logical)",
            small_image="cisco",
            small_text="Router0 (Router)"
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
            state="Designing Logical Topology (Realtime)",
            start=1000,
            large_image="packet_tracer",
            large_text="Cisco Packet Tracer | Realtime (Logical)",
            small_image="cisco",
            small_text="Cisco Systems"
        )

def test_rpc_update_active_sub_app():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="LAB1.3 CLI config.pka",
            is_unsaved=False,
            start_time=1000,
            file_type="pka",
            active_device="Laptop0",
            active_sub_app="Terminal (Switch#)",
            device_type="laptop",
            completion_percent="75%"
        )

        rpc.presence.update.assert_called_once_with(
            details="Lab: LAB1.3 CLI config.pka (75%)",
            state="Laptop0 > Terminal (Switch#)",
            start=1000,
            large_image="packet_tracer",
            large_text="Cisco Packet Tracer | Progress: 75%",
            small_image="cisco",
            small_text="Laptop0 (Laptop)"
        )

def test_rpc_update_pka_completion_and_timer():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="CCNA1_Lab.pka",
            is_unsaved=False,
            start_time=1000,
            file_type="pka",
            active_device="PC0",
            active_sub_app="Command Prompt",
            device_type="pc",
            completion_percent="75%",
            activity_timer="00:34:32"
        )

        rpc.presence.update.assert_called_once_with(
            details="Lab: CCNA1_Lab.pka (75% • 00:34:32)",
            state="PC0 > Command Prompt",
            start=1000,
            large_image="packet_tracer",
            large_text="Cisco Packet Tracer | Progress: 75%",
            small_image="cisco",
            small_text="PC0 (Pc)"
        )

def test_rpc_update_workspace_canvas_tools():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="Campus.pkt",
            is_unsaved=False,
            start_time=1000,
            file_type="pkt",
            active_device=None,
            workspace_tool="Testing Connectivity (Simple PDU Ping)"
        )

        rpc.presence.update.assert_called_once_with(
            details="Topology: Campus.pkt",
            state="Testing Connectivity (Simple PDU Ping)",
            start=1000,
            large_image="packet_tracer",
            large_text="Cisco Packet Tracer | Realtime (Logical)",
            small_image="cisco",
            small_text="Cisco Systems"
        )

def test_rpc_update_pka_no_completion_simulation():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="Activity.pka",
            is_unsaved=False,
            start_time=1000,
            file_type="pka",
            active_device=None,
            sim_mode="Simulation",
            view_mode="Physical"
        )

        rpc.presence.update.assert_called_once_with(
            details="Lab: Activity.pka",
            state="Designing Physical Topology (Simulation)",
            start=1000,
            large_image="packet_tracer",
            large_text="Cisco Packet Tracer | Simulation Mode",
            small_image="cisco",
            small_text="Cisco Systems"
        )

def test_rpc_update_rate_limiting():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager(rate_limit=2.0)
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = time.time()

        # Should be throttled since within rate limit cooldown
        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000)
        rpc.presence.update.assert_not_called()

        # Simulate time passing past rate limit cooldown
        rpc._last_update_time = time.time() - 2.5
        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000)
        rpc.presence.update.assert_called_once()

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
            "active_sub_app": None,
            "device_type": "pt_logo",
            "activity_timer": None,
            "completion_percent": None,
            "sim_mode": "Realtime",
            "view_mode": "Logical",
            "workspace_tool": None
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
        mock_p = MagicMock()
        rpc.presence = mock_p
        rpc.connected = True
        rpc.clear()
        mock_p.clear.assert_called_once()
        mock_p.close.assert_called_once()
        assert rpc.connected is False
