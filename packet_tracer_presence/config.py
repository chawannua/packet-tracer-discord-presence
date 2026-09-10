"""
Configuration constants for Packet Tracer Presence
"""

DISCORD_CLIENT_ID = "1351548975567736923"
DEFAULT_POLLING_INTERVAL = 5.0
# Slower poll while Packet Tracer is closed, so the resident background mode
# (--no-exit-on-close, used by the autostart path) stays cheap when idle.
IDLE_POLLING_INTERVAL = 15.0
RECONNECT_TIMEOUT = 15.0

KNOWN_PROCESS_NAMES = [
    "PacketTracer.exe",
    "PacketTracer",
    "PacketTracer7.exe",
    "PacketTracer8.exe",
    "PacketTracer9.exe",
]
