from packet_tracer_presence.config import DISCORD_CLIENT_ID, DEFAULT_POLLING_INTERVAL, RECONNECT_TIMEOUT, KNOWN_PROCESS_NAMES

def test_config_defaults():
    assert DISCORD_CLIENT_ID == '1351548975567736923'
    assert DEFAULT_POLLING_INTERVAL == 5.0
    assert RECONNECT_TIMEOUT == 15.0
    assert isinstance(KNOWN_PROCESS_NAMES, list)
    assert 'PacketTracer.exe' in KNOWN_PROCESS_NAMES
    assert 'PacketTracer' in KNOWN_PROCESS_NAMES
    assert 'PacketTracer7.exe' in KNOWN_PROCESS_NAMES
    assert 'PacketTracer8.exe' in KNOWN_PROCESS_NAMES
    assert 'PacketTracer9.exe' in KNOWN_PROCESS_NAMES