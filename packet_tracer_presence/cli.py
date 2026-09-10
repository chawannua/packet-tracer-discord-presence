"""
CLI interface for Packet Tracer Presence
"""
import argparse
import time
import logging
import sys
import os
from .config import DEFAULT_POLLING_INTERVAL, DISCORD_CLIENT_ID
from .detector import ProcessDetector
from .window_parser import WindowParser
from .rpc_manager import RPCManager
from . import __version__

def main():
    parser = argparse.ArgumentParser(description="Discord Rich Presence for Cisco Packet Tracer")
    parser.add_argument("--interval", type=float, default=DEFAULT_POLLING_INTERVAL, help="Polling interval in seconds")
    parser.add_argument("--client-id", type=str, default=DISCORD_CLIENT_ID, help="Discord Client ID")
    parser.add_argument("--launch", action="store_true", help="Launch Discord Presence in background")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    
    args = parser.parse_args()
    
    handlers = []
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler(sys.stderr))
    else:
        import os
        log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(log_dir, "presence.log")
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    
    detector = ProcessDetector()
    window_parser = WindowParser()
    rpc = RPCManager(client_id=args.client_id)
    
    start_time = None
    was_running = False
    
    logger.info("Starting Packet Tracer Presence...")
    
    try:
        while True:
            is_running = detector.find_packet_tracer()
            
            if is_running:
                if not was_running:
                    logger.info("Packet Tracer started")
                    start_time = int(time.time())
                    was_running = True
                
                state = window_parser.get_active_activity()
                project_name = state.file_name
                is_unsaved = state.is_unsaved
                
                if not project_name or project_name == "Workspace":
                    cmd_file = detector.get_running_project_file()
                    if cmd_file:
                        project_name = cmd_file
                        is_unsaved = False
                        ext = project_name.split(".")[-1].lower() if "." in project_name else ""
                        if ext in ["pka", "pkt", "pkz"]:
                            state.file_type = ext

                rpc.update(
                    project_name=project_name, 
                    is_unsaved=is_unsaved, 
                    start_time=start_time,
                    file_type=state.file_type,
                    active_device=state.active_device,
                    device_type=state.device_type,
                    activity_timer=state.activity_timer
                )
            else:
                if was_running:
                    logger.info("Packet Tracer closed")
                    rpc.clear()
                    start_time = None
                    was_running = False
                    
            time.sleep(args.interval)
            
    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        rpc.close()

if __name__ == "__main__":
    main()
