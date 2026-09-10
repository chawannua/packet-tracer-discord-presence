"""
Discord RPC Manager
"""
import threading
import time
import logging
from pypresence import Presence
from pypresence.exceptions import DiscordNotFound, InvalidID, PipeClosed
from .config import DISCORD_CLIENT_ID, RECONNECT_TIMEOUT

logger = logging.getLogger(__name__)

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
            logger.warning(f"Discord RPC connect timed out: {e}")
            self._connect_retry_time = now + RECONNECT_TIMEOUT
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
        if is_unsaved or "Untitled" in str(project_name) or "New" in str(project_name) or not project_name or project_name == "Workspace":
            details = "Designing New Topology"
        elif file_type == 'pka':
            prefix = f"Lab: {project_name}" if project_name else "Lab"
            if completion_percent and activity_timer:
                details = f"{prefix} ({completion_percent} • {activity_timer})"
            elif completion_percent:
                details = f"{prefix} ({completion_percent})"
            elif activity_timer:
                details = f"{prefix} ({activity_timer})"
            else:
                details = prefix
        elif file_type == 'pkt':
            prefix = f"Topology: {project_name}" if project_name else "Topology"
            if activity_timer:
                details = f"{prefix} ({activity_timer})"
            else:
                details = prefix
        else:
            details = f"Editing {project_name}" if project_name else "Idling"

        if len(details) > 128:
            details = details[:125] + "..."

        # State
        if active_device:
            if active_sub_app:
                state_str = f"{active_device} > {active_sub_app}"
            else:
                state_str = f"Configuring {active_device}"
        else:
            if workspace_tool:
                state_str = workspace_tool
            else:
                state_str = f"Designing {view_mode} Topology ({sim_mode})"
            
        if len(state_str) > 128:
            state_str = state_str[:125] + "..."

        # Images and tooltips (Discord uploaded assets: 'packet_tracer' and 'cisco')
        large_image = "packet_tracer"
        if file_type == 'pka':
            if completion_percent:
                large_text = f"Cisco Packet Tracer | Progress: {completion_percent}"
            else:
                large_text = f"Cisco Packet Tracer | {sim_mode} Mode"
        else:
            large_text = f"Cisco Packet Tracer | {sim_mode} ({view_mode})"

        if len(large_text) > 128:
            large_text = large_text[:125] + "..."

        small_image = "cisco"
        if active_device:
            dev_cap = (device_type or "device").capitalize()
            small_text = f"{active_device} ({dev_cap})"
        else:
            small_text = "Cisco Systems"
            
        if len(small_text) > 128:
            small_text = small_text[:125] + "..."

        try:
            _call_with_timeout(
                self.presence.update,
                PIPE_TIMEOUT,
                details=details,
                state=state_str,
                start=start_time,
                large_image=large_image,
                large_text=large_text,
                small_image=small_image,
                small_text=small_text
            )
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
