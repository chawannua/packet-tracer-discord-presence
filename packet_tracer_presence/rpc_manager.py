"""
Discord RPC Manager
"""
import threading
import time
import logging
from pypresence import Presence
from pypresence.exceptions import (
    ArgumentError,
    DiscordNotFound,
    InvalidArgument,
    InvalidID,
    PipeClosed,
)
from .config import (
    DISCORD_CLIENT_ID,
    RECONNECT_TIMEOUT,
    PRESENCE_BUTTONS,
    DEVICE_ASSET_KEYS,
    DEFAULT_SMALL_ASSET,
)

logger = logging.getLogger(__name__)

# Built from codepoints rather than literals: this module is imported by a
# pythonw process on Windows, where a source file read without a UTF-8 BOM
# mangles pasted block characters.
_BAR_FULL = chr(0x2588)
_BAR_EMPTY = chr(0x2591)
BAR_WIDTH = 10

# Same reasoning as the block characters above: built from its codepoint so a
# BOM-less read under pythonw can't mangle it.
_MIDDOT = chr(0x00B7)


def _progress_bar(completion_percent, width=BAR_WIDTH):
    """Render "75%" as a block bar. Returns None if the value is unusable."""
    if not completion_percent:
        return None
    try:
        pct = float(str(completion_percent).strip().rstrip("%"))
    except (ValueError, TypeError):
        return None
    pct = max(0.0, min(100.0, pct))
    filled = int(round(pct / 100.0 * width))
    return _BAR_FULL * filled + _BAR_EMPTY * (width - filled)

# Windows named-pipe I/O to Discord has no built-in timeout in pypresence, so
# a stalled/half-dead Discord client can otherwise block connect/update/close
# forever. Every pypresence call goes through this to guarantee we never wait
# longer than PIPE_TIMEOUT, so shutdown is always instant.
PIPE_TIMEOUT = 2.5


def _call_with_timeout(func, timeout=PIPE_TIMEOUT, *args, **kwargs):
    result = {}

    def target():
        try:
            result["value"] = func(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 - re-raised on the caller's thread below
            result["error"] = exc

    worker = threading.Thread(target=target, daemon=True)
    worker.start()
    worker.join(timeout)
    if worker.is_alive():
        raise TimeoutError(f"Discord RPC call timed out after {timeout}s")
    if "error" in result:
        raise result["error"]
    return result.get("value")


class RPCManager:
    def __init__(self, client_id=DISCORD_CLIENT_ID, rate_limit: float = 2.0):
        self.client_id = client_id
        self.presence = Presence(client_id)
        self.connected = False
        self.rate_limit = rate_limit
        self._last_update_time = 0.0
        self._last_state = None
        self._connect_retry_time = 0.0
        # Cleared permanently if Discord ever rejects the buttons payload.
        self._buttons = list(PRESENCE_BUTTONS) or None

    def connect(self) -> bool:
        if self.connected:
            return True
            
        now = time.time()
        if now < self._connect_retry_time:
            return False
            
        try:
            _call_with_timeout(self.presence.connect)
            self.connected = True
            logger.info("Connected to Discord RPC")
            return True
        except (DiscordNotFound, ConnectionRefusedError, FileNotFoundError, PipeClosed) as e:
            logger.debug(f"Failed to connect to Discord RPC: {e}")
            self._connect_retry_time = now + RECONNECT_TIMEOUT
            return False
        except TimeoutError as e:
            # The worker thread is still inside Presence.connect(), mid-handshake,
            # and will go on to assign this object's event loop and sockets.
            # Retrying on the same Presence races it and can wedge the client for
            # the rest of the session, so abandon it and start the next attempt clean.
            logger.warning(f"Discord RPC connect timed out: {e}")
            self._connect_retry_time = now + RECONNECT_TIMEOUT
            self.presence = Presence(self.client_id)
            return False
        except Exception as e:
            logger.warning(f"Discord RPC connect failed unexpectedly: {e}")
            self._connect_retry_time = now + RECONNECT_TIMEOUT
            self.presence = Presence(self.client_id)
            return False

    def update(self, project_name: str, is_unsaved: bool, start_time: int, file_type: str = "unknown", active_device: str = None, active_sub_app: str = None, device_type: str = "pt_logo", activity_timer: str = None, completion_percent: str = None, sim_mode: str = "Realtime", view_mode: str = "Logical", workspace_tool: str = None):
        if not self.connect():
            return

        state_dict = {
            "project_name": project_name,
            "is_unsaved": is_unsaved,
            "file_type": file_type,
            "active_device": active_device,
            "active_sub_app": active_sub_app,
            "device_type": device_type,
            "activity_timer": activity_timer,
            "completion_percent": completion_percent,
            "sim_mode": sim_mode,
            "view_mode": view_mode,
            "workspace_tool": workspace_tool
        }
        
        if state_dict == self._last_state:
            return

        now = time.time()
        # Rate limit updates (2-3s cooldown to respect Discord rate limits while allowing responsive updates on state change)
        if now - self._last_update_time < self.rate_limit:
            return

        # Details
        if (
            is_unsaved
            or not project_name
            or project_name == "Workspace"
            or "Untitled" in str(project_name)
            or "New" in str(project_name)
        ):
            details = "Architecting a new network"
        elif file_type == 'pka':
            if completion_percent:
                details = f"Certification lab {_MIDDOT} {completion_percent} solved"
            elif project_name:
                details = f"Certification lab {_MIDDOT} {project_name}"
            else:
                details = "Working a certification lab"
        elif file_type == 'pkt':
            if project_name:
                details = f"Building network {_MIDDOT} {project_name}"
            else:
                details = "Building a network"
        elif project_name:
            details = f"Working on {_MIDDOT} {project_name}"
        else:
            details = "Working in Packet Tracer"

        if len(details) > 128:
            details = details[:125] + "..."

        # State
        if active_device:
            sub_app_lower = (active_sub_app or "").lower()
            if sub_app_lower == "cli":
                state_str = f"Live IOS console on {active_device}"
            elif sub_app_lower == "config":
                state_str = f"Configuring interfaces on {active_device}"
            elif sub_app_lower == "desktop":
                state_str = f"Running diagnostics from {active_device}"
            elif active_sub_app:
                state_str = f"{active_device} {_MIDDOT} {active_sub_app}"
            else:
                state_str = f"Provisioning {active_device}"
        elif sim_mode == "Simulation":
            state_str = "Tracing packets hop-by-hop"
        elif workspace_tool:
            state_str = f"Using {workspace_tool}"
        else:
            state_str = "Designing the network topology"

        if len(state_str) > 128:
            state_str = state_str[:125] + "..."

        # Images and tooltips (Discord uploaded assets: 'packet_tracer' and 'cisco')
        large_image = "packet_tracer"
        bar = _progress_bar(completion_percent) if file_type == 'pka' else None
        if file_type == 'pka' and bar:
            large_text = f"Cisco Packet Tracer {_MIDDOT} {bar} {completion_percent}"
        elif file_type == 'pka' and completion_percent:
            large_text = f"Cisco Packet Tracer {_MIDDOT} {completion_percent} complete"
        else:
            large_text = f"Cisco Packet Tracer {_MIDDOT} {sim_mode} mode {_MIDDOT} {view_mode} view"

        if len(large_text) > 128:
            large_text = large_text[:125] + "..."

        small_image = DEVICE_ASSET_KEYS.get(
            (device_type or "").lower(), DEFAULT_SMALL_ASSET
        )
        if active_device:
            if device_type and device_type != "pt_logo":
                small_text = f"{active_device} {_MIDDOT} Cisco {device_type.lower()}"
            else:
                small_text = f"{active_device} {_MIDDOT} Cisco device"
        else:
            small_text = "Cisco Systems"

        if len(small_text) > 128:
            small_text = small_text[:125] + "..."

        payload = dict(
            details=details,
            state=state_str,
            start=start_time,
            large_image=large_image,
            large_text=large_text,
            small_image=small_image,
            small_text=small_text,
        )

        try:
            try:
                _call_with_timeout(
                    self.presence.update, PIPE_TIMEOUT, buttons=self._buttons, **payload
                )
            except (TypeError, InvalidArgument, ArgumentError) as button_err:
                # Only argument/serialization errors mean the buttons field itself
                # is unsupported. Transport failures (ResponseTimeout, ServerError,
                # InvalidPipe, DiscordError, the AssertionError send_data raises on a
                # dead writer) must NOT land here: retrying would write a second
                # SET_ACTIVITY frame whose read consumes the first frame's response,
                # desyncing the pipe, and would disable buttons Discord never rejected.
                if self._buttons is not None:
                    logger.warning(
                        "Discord rejected presence buttons (%s); retrying without them",
                        button_err,
                    )
                    self._buttons = None
                    _call_with_timeout(self.presence.update, PIPE_TIMEOUT, **payload)
                else:
                    raise
            self._last_update_time = now
            self._last_state = state_dict
            logger.debug(f"Updated RPC: {details} | {state_str}")
        except PipeClosed:
            logger.warning("Discord RPC pipe closed")
            self.connected = False
            self.presence = Presence(self.client_id)
        except TimeoutError as e:
            logger.warning(f"Discord RPC update timed out: {e}")
            self.connected = False
            self.presence = Presence(self.client_id)
        except Exception as e:
            logger.error(f"Error updating RPC: {e}")

    def clear(self):
        if not self.connected:
            return
        try:
            _call_with_timeout(self.presence.clear)
        except Exception as e:
            logger.debug(f"Failed to clear presence: {e}")
        try:
            _call_with_timeout(self.presence.close)
        except Exception as e:
            logger.debug(f"Failed to close presence on clear: {e}")
        self.connected = False
        self._last_state = None
        self._last_update_time = 0.0
        self.presence = Presence(self.client_id)
        logger.info("Presence cleared and disconnected from Discord")

    def close(self):
        if self.connected:
            try:
                _call_with_timeout(self.presence.close)
            except Exception as e:
                logger.debug(f"Failed to close presence: {e}")
            self.connected = False
            self._last_state = None
            self._last_update_time = 0.0
