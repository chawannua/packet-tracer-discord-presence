"""
Discord RPC Manager
"""
import time
import logging
from pypresence import Presence
from pypresence.exceptions import DiscordNotFound, InvalidID, PipeClosed
from .config import DISCORD_CLIENT_ID, RECONNECT_TIMEOUT

logger = logging.getLogger(__name__)

class RPCManager:
    def __init__(self, client_id=DISCORD_CLIENT_ID):
        self.client_id = client_id
        self.presence = Presence(client_id)
        self.connected = False
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
            self.presence.connect()
            self.connected = True
            logger.info("Connected to Discord RPC")
            return True
        except (DiscordNotFound, ConnectionRefusedError, FileNotFoundError, PipeClosed) as e:
            logger.debug(f"Failed to connect to Discord RPC: {e}")
            self._connect_retry_time = now + RECONNECT_TIMEOUT
            return False

    def update(self, project_name: str, is_unsaved: bool, start_time: int, file_type: str = "unknown", active_device: str = None, device_type: str = "pt_logo", activity_timer: str = None):
        if not self.connect():
            return

        now = time.time()
        # Rate limit to 1 per 15s to be safe against Discord limits
        if now - self._last_update_time < 15.0:
            return

        state = {
            "project_name": project_name,
            "is_unsaved": is_unsaved,
            "file_type": file_type,
            "active_device": active_device,
            "device_type": device_type,
            "activity_timer": activity_timer
        }
        
        if state == self._last_state:
            return

        # Details
        details = f"Editing {project_name}" if project_name else "Idling"
        if file_type == 'pka':
            details = f"Lab: {project_name}"
        elif file_type == 'pkt':
            details = f"Topology: {project_name}"
            
        if is_unsaved or "Untitled" in str(project_name) or "New" in str(project_name):
            details = "Designing New Topology"

        if activity_timer:
            # Append timer if space permits
            timer_str = f" (Timer: {activity_timer})"
            if len(details) + len(timer_str) <= 128:
                details += timer_str

        # State
        if active_device:
            state_str = f"Configuring: {active_device}"
        else:
            state_str = "Designing Topology"

        # Small image
        small_image = device_type if device_type in ['router', 'switch', 'laptop', 'pc', 'server', 'phone', 'pt_logo'] else "pt_logo"
        small_text = f"Configuring {active_device}" if active_device else "Cisco Packet Tracer"

        try:
            self.presence.update(
                details=details,
                state=state_str,
                start=start_time,
                large_image="pt_logo",
                large_text="Cisco Packet Tracer",
                small_image=small_image,
                small_text=small_text
            )
            self._last_update_time = now
            self._last_state = state
            logger.debug(f"Updated RPC: {details} | {state_str}")
        except PipeClosed:
            logger.warning("Discord RPC pipe closed")
            self.connected = False
            self.presence = Presence(self.client_id)
        except Exception as e:
            logger.error(f"Error updating RPC: {e}")

    def clear(self):
        if not self.connected:
            return
        try:
            self.presence.clear()
        except Exception as e:
            logger.debug(f"Failed to clear presence: {e}")
            
    def close(self):
        if self.connected:
            try:
                self.presence.close()
            except Exception as e:
                logger.debug(f"Failed to close presence: {e}")
            self.connected = False
