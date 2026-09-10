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

# Discord shows at most 2 buttons and truncates labels past roughly 31 chars.
# URLs must be https.
PRESENCE_BUTTONS = [
    {"label": "Get Packet Tracer", "url": "https://www.netacad.com/courses/packet-tracer"},
    {"label": "View on GitHub", "url": "https://github.com/chawannua/packet-tracer-discord-presence"},
]

DEFAULT_SMALL_ASSET = "cisco"

# Discord asset keys per detected device type. Every entry deliberately points at
# DEFAULT_SMALL_ASSET until per-device art is uploaded to the Discord developer
# application: an asset key Discord does not know renders as no image at all,
# which is worse than the generic logo. Change a value only after uploading it.
DEVICE_ASSET_KEYS = {
    "router": DEFAULT_SMALL_ASSET,
    "switch": DEFAULT_SMALL_ASSET,
    "pc": DEFAULT_SMALL_ASSET,
    "server": DEFAULT_SMALL_ASSET,
    "laptop": DEFAULT_SMALL_ASSET,
    "firewall": DEFAULT_SMALL_ASSET,
    "wireless": DEFAULT_SMALL_ASSET,
}
