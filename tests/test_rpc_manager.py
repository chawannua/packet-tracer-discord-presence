"""
Unit tests for packet_tracer_presence.rpc_manager
"""
import logging
import time
import pytest
from unittest.mock import MagicMock, patch
from pypresence.exceptions import (
    DiscordNotFound,
    InvalidArgument,
    InvalidPipe,
    PipeClosed,
    ResponseTimeout,
    ServerError,
)
from packet_tracer_presence.rpc_manager import RPCManager, _progress_bar
from packet_tracer_presence.config import PRESENCE_BUTTONS

MIDDOT = chr(0x00B7)

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
            buttons=PRESENCE_BUTTONS,
            details=f"Building network {MIDDOT} NetworkLab.pkt",
            state="Provisioning Router0",
            start=1000,
            large_image="packet_tracer",
            large_text=f"Cisco Packet Tracer {MIDDOT} Realtime mode {MIDDOT} Logical view",
            small_image="cisco",
            small_text=f"Router0 {MIDDOT} Cisco router"
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
            buttons=PRESENCE_BUTTONS,
            details="Architecting a new network",
            state="Designing the network topology",
            start=1000,
            large_image="packet_tracer",
            large_text=f"Cisco Packet Tracer {MIDDOT} Realtime mode {MIDDOT} Logical view",
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
            buttons=PRESENCE_BUTTONS,
            details=f"Certification lab {MIDDOT} 75% solved",
            state=f"Laptop0 {MIDDOT} Terminal (Switch#)",
            start=1000,
            large_image="packet_tracer",
            large_text=f"Cisco Packet Tracer {MIDDOT} {_progress_bar('75%')} 75%",
            small_image="cisco",
            small_text=f"Laptop0 {MIDDOT} Cisco laptop"
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
            buttons=PRESENCE_BUTTONS,
            details=f"Certification lab {MIDDOT} 75% solved",
            state=f"PC0 {MIDDOT} Command Prompt",
            start=1000,
            large_image="packet_tracer",
            large_text=f"Cisco Packet Tracer {MIDDOT} {_progress_bar('75%')} 75%",
            small_image="cisco",
            small_text=f"PC0 {MIDDOT} Cisco pc"
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
            buttons=PRESENCE_BUTTONS,
            details=f"Building network {MIDDOT} Campus.pkt",
            state="Using Testing Connectivity (Simple PDU Ping)",
            start=1000,
            large_image="packet_tracer",
            large_text=f"Cisco Packet Tracer {MIDDOT} Realtime mode {MIDDOT} Logical view",
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
            buttons=PRESENCE_BUTTONS,
            details=f"Certification lab {MIDDOT} Activity.pka",
            state="Tracing packets hop-by-hop",
            start=1000,
            large_image="packet_tracer",
            large_text=f"Cisco Packet Tracer {MIDDOT} Simulation mode {MIDDOT} Physical view",
            small_image="cisco",
            small_text="Cisco Systems"
        )


def test_rpc_update_unknown_file_type_with_project_name():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(project_name="Scratchpad", is_unsaved=False, start_time=1000, file_type="unknown")

        assert rpc.presence.update.call_args.kwargs["details"] == f"Working on {MIDDOT} Scratchpad"


def test_rpc_update_unknown_file_type_without_project_name_is_unreachable_via_new_topology():
    """An empty project_name is caught by the 'new/blank project' branch before the
    generic file-type fallback, so this exercises that priority explicitly."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(project_name="", is_unsaved=False, start_time=1000, file_type="unknown")

        assert rpc.presence.update.call_args.kwargs["details"] == "Architecting a new network"


@pytest.mark.parametrize("sub_app,expected_state", [
    ("CLI", "Live IOS console on Router0"),
    ("cli", "Live IOS console on Router0"),
    ("Config", "Configuring interfaces on Router0"),
    ("CONFIG", "Configuring interfaces on Router0"),
    ("Desktop", "Running diagnostics from Router0"),
    ("desktop", "Running diagnostics from Router0"),
])
def test_rpc_update_state_sub_app_variants(sub_app, expected_state):
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="NetworkLab.pkt",
            is_unsaved=False,
            start_time=1000,
            file_type="pkt",
            active_device="Router0",
            active_sub_app=sub_app,
        )

        assert rpc.presence.update.call_args.kwargs["state"] == expected_state


def test_rpc_update_state_device_no_sub_app_is_provisioning():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="NetworkLab.pkt",
            is_unsaved=False,
            start_time=1000,
            file_type="pkt",
            active_device="Switch1",
            active_sub_app=None,
        )

        assert rpc.presence.update.call_args.kwargs["state"] == "Provisioning Switch1"


def test_rpc_update_small_text_missing_device_type():
    """active_device with a missing/pt_logo device_type still reports a device tooltip."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(
            project_name="NetworkLab.pkt",
            is_unsaved=False,
            start_time=1000,
            file_type="pkt",
            active_device="Blade0",
            device_type="pt_logo",
        )

        assert rpc.presence.update.call_args.kwargs["small_text"] == f"Blade0 {MIDDOT} Cisco device"


def test_rpc_update_details_truncates_to_128_chars():
    """The new copy is longer than the old phrasing in places; truncation must still apply."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        long_name = "A" * 200
        rpc.update(project_name=long_name, is_unsaved=False, start_time=1000, file_type="pkt")

        details = rpc.presence.update.call_args.kwargs["details"]
        assert len(details) == 128
        assert details.endswith("...")
        assert details.startswith(f"Building network {MIDDOT} AAA")


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

def test_rpc_connect_times_out_without_hanging():
    """Guards the hang-on-close fix: a stalled Discord pipe must never block
    the daemon beyond PIPE_TIMEOUT, not hang forever."""
    from packet_tracer_presence.rpc_manager import PIPE_TIMEOUT

    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.presence.connect.side_effect = lambda: time.sleep(PIPE_TIMEOUT + 5)

        started = time.time()
        result = rpc.connect()
        elapsed = time.time() - started

        assert result is False
        assert rpc.connected is False
        assert elapsed < PIPE_TIMEOUT + 2, "connect() blocked far longer than the pipe timeout"


def test_rpc_close_times_out_without_hanging():
    from packet_tracer_presence.rpc_manager import PIPE_TIMEOUT

    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.presence.close.side_effect = lambda: time.sleep(PIPE_TIMEOUT + 5)
        rpc.connected = True

        started = time.time()
        rpc.close()
        elapsed = time.time() - started

        assert rpc.connected is False
        assert elapsed < PIPE_TIMEOUT + 2, "close() blocked far longer than the pipe timeout"


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


def test_progress_bar_renders_expected_blocks():
    full, empty = chr(0x2588), chr(0x2591)
    assert _progress_bar("0%") == empty * 10
    assert _progress_bar("100%") == full * 10
    assert _progress_bar("50%") == full * 5 + empty * 5
    assert _progress_bar("75%") == full * 8 + empty * 2


@pytest.mark.parametrize("bad", [None, "", "n/a", "--", "abc%"])
def test_progress_bar_returns_none_for_unusable_values(bad):
    assert _progress_bar(bad) is None


@pytest.mark.parametrize("value,expected_filled", [("-10%", 0), ("150%", 10)])
def test_progress_bar_clamps_out_of_range(value, expected_filled):
    bar = _progress_bar(value)
    assert bar.count(chr(0x2588)) == expected_filled


def test_rpc_update_falls_back_when_discord_rejects_buttons():
    """A buttons rejection must cost the buttons, never the whole presence."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0
        rpc.presence.update.side_effect = [TypeError("buttons unsupported"), None]

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000, file_type="pkt")

        assert rpc.presence.update.call_count == 2
        assert "buttons" not in rpc.presence.update.call_args_list[1].kwargs
        assert rpc._buttons is None
        assert rpc._last_state is not None


@pytest.mark.parametrize("transport_error", [
    ServerError("discord hiccup"),
    ResponseTimeout(),
    InvalidPipe(),
    AssertionError(),  # pypresence send_data raises this when sock_writer is None
])
def test_rpc_update_transport_error_does_not_disable_buttons(transport_error):
    """Only argument errors mean "buttons unsupported".

    A transport failure must not be misread as a buttons rejection: retrying
    would write a second SET_ACTIVITY frame whose response read consumes the
    first frame's response, desyncing the pipe, and would permanently drop
    buttons that Discord never actually rejected.
    """
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0
        rpc.presence.update.side_effect = transport_error

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000, file_type="pkt")

        assert rpc.presence.update.call_count == 1, "must not write a second frame"
        assert rpc._buttons is not None, "buttons must survive a transport failure"


def test_rpc_update_invalid_argument_does_disable_buttons():
    """The genuine 'buttons unsupported' signal still triggers the fallback."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0
        rpc.presence.update.side_effect = [InvalidArgument("buttons", "none"), None]

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000, file_type="pkt")

        assert rpc.presence.update.call_count == 2
        assert rpc._buttons is None


def test_rpc_connect_timeout_rebuilds_presence():
    """A timed-out connect leaves a worker thread mid-handshake on the old
    Presence; reusing it races that thread's loop/socket assignment and can
    wedge the client silently for the rest of the session."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        stale = MagicMock()
        rpc.presence = stale

        with patch("packet_tracer_presence.rpc_manager._call_with_timeout",
                   side_effect=TimeoutError("timed out")):
            assert rpc.connect() is False

        assert rpc.presence is not stale
        assert rpc.connected is False


def test_rpc_connect_unexpected_error_is_logged_not_swallowed(caplog):
    """A RuntimeError from a racing event loop previously escaped every handler
    and died in a DEBUG log line, invisible at the default level."""
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        stale = MagicMock()
        rpc.presence = stale

        with patch("packet_tracer_presence.rpc_manager._call_with_timeout",
                   side_effect=RuntimeError("This event loop is already running")):
            with caplog.at_level(logging.WARNING):
                assert rpc.connect() is False

        assert any("This event loop is already running" in r.message for r in caplog.records)
        assert rpc.presence is not stale


def test_rpc_update_pka_completion_renders_bar():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(project_name="Activity.pka", is_unsaved=False, start_time=1000,
                   file_type="pka", completion_percent="50%")

        large_text = rpc.presence.update.call_args.kwargs["large_text"]
        assert chr(0x2588) * 5 + chr(0x2591) * 5 in large_text
        assert "50%" in large_text


def test_rpc_update_unknown_device_type_falls_back_to_default_asset():
    with patch("packet_tracer_presence.rpc_manager.Presence"):
        rpc = RPCManager()
        rpc.presence = MagicMock()
        rpc.connected = True
        rpc._last_update_time = 0.0

        rpc.update(project_name="NetworkLab.pkt", is_unsaved=False, start_time=1000,
                   file_type="pkt", active_device="Blade0", device_type="not_a_real_device")

        assert rpc.presence.update.call_args.kwargs["small_image"] == "cisco"
