import argparse
import faulthandler
import time
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from .config import DEFAULT_POLLING_INTERVAL, IDLE_POLLING_INTERVAL, DISCORD_CLIENT_ID
from .detector import ProcessDetector
from .window_parser import WindowParser
from .rpc_manager import RPCManager
from . import __version__
logger = logging.getLogger(__name__)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK_FILE = os.path.join(PROJECT_ROOT, '.daemon.lock')
NATIVE_CRASH_FILE = os.path.join(PROJECT_ROOT, 'native_crash.log')
_native_crash_fh = None

def _enable_native_crash_dumps():
    global _native_crash_fh
    try:
        _native_crash_fh = open(NATIVE_CRASH_FILE, 'a', encoding='utf-8')
        faulthandler.enable(file=_native_crash_fh, all_threads=True)
    except Exception:
        pass
LOG_MAX_BYTES = 1000000
LOG_BACKUP_COUNT = 3

def _running_under_tests() -> bool:
    return os.environ.get('PT_PRESENCE_TESTING') == '1' or 'pytest' in sys.modules

def _is_own_process_name(name: str) -> bool:
    lowered = (name or '').lower()
    return 'python' in lowered or 'packettracerpresence' in lowered

def ensure_single_instance():
    if _running_under_tests():
        return True
    try:
        import psutil
        if os.path.exists(LOCK_FILE):
            try:
                with open(LOCK_FILE, 'r') as f:
                    old_pid = int(f.read().strip())
            except (ValueError, OSError):
                old_pid = None
            if old_pid is not None and old_pid != os.getpid() and psutil.pid_exists(old_pid):
                try:
                    if _is_own_process_name(psutil.Process(old_pid).name()):
                        return None
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            os.remove(LOCK_FILE)
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except Exception as e:
        logger.warning('Single-instance lock unavailable (%s); continuing without it', e)
        return True

def resolve_project_start(project_name, last_project, start_time, now):
    if not project_name or project_name == 'Workspace':
        return (start_time, last_project)
    if last_project is None:
        return (start_time, project_name)
    if project_name != last_project:
        return (now, project_name)
    return (start_time, last_project)

def remove_lock_file():
    if _running_under_tests():
        return
    try:
        with open(LOCK_FILE, 'r') as f:
            owner_pid = int(f.read().strip())
    except (ValueError, OSError):
        return
    if owner_pid != os.getpid():
        return
    try:
        os.remove(LOCK_FILE)
    except OSError:
        pass

def main():
    _enable_native_crash_dumps()
    parser = argparse.ArgumentParser(description='Discord Rich Presence for Cisco Packet Tracer')
    parser.add_argument('--interval', type=float, default=DEFAULT_POLLING_INTERVAL, help='Polling interval in seconds')
    parser.add_argument('--client-id', type=str, default=DISCORD_CLIENT_ID, help='Discord Client ID')
    parser.add_argument('--launch', action='store_true', help='Launch Discord Presence in background')
    parser.add_argument('--exit-on-close', dest='exit_on_close', action='store_true', default=True, help='Exit when Packet Tracer closes (default: on)')
    parser.add_argument('--no-exit-on-close', dest='exit_on_close', action='store_false', help='Keep running (waiting for Packet Tracer to reopen) after it closes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    args = parser.parse_args()
    handlers = []
    log_file = os.path.join(PROJECT_ROOT, 'presence.log')
    try:
        handlers.append(RotatingFileHandler(log_file, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding='utf-8'))
    except Exception:
        pass
    try:
        if sys.stderr and hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
            handlers.append(logging.StreamHandler(sys.stderr))
    except Exception:
        pass
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s', handlers=handlers)
    logging.getLogger('comtypes').setLevel(logging.WARNING)
    mutex = ensure_single_instance()
    if not mutex:
        logger.info('Another instance is already running. Exiting.')
        return
    detector = ProcessDetector()
    window_parser = WindowParser()
    rpc = RPCManager(client_id=args.client_id)
    start_time = None
    was_running = False
    last_project = None
    idle_interval = max(args.interval, IDLE_POLLING_INTERVAL)
    logger.info('Starting Packet Tracer Presence...')
    try:
        while True:
            try:
                is_running = detector.find_packet_tracer()
                if is_running:
                    if not was_running:
                        logger.info('Packet Tracer started')
                        start_time = int(time.time())
                        last_project = None
                        was_running = True
                    state = window_parser.get_active_activity()
                    project_name = state.file_name
                    is_unsaved = state.is_unsaved
                    if not project_name or project_name == 'Workspace':
                        cmd_file = detector.get_running_project_file()
                        if cmd_file:
                            project_name = cmd_file
                            is_unsaved = False
                            ext = project_name.split('.')[-1].lower() if '.' in project_name else ''
                            if ext in ['pka', 'pkt', 'pkz']:
                                state.file_type = ext
                    previous_project = last_project
                    start_time, last_project = resolve_project_start(project_name, last_project, start_time, int(time.time()))
                    if previous_project is not None and last_project != previous_project:
                        logger.info('Switched project: %s -> %s', previous_project, last_project)
                    rpc.update(project_name=project_name, is_unsaved=is_unsaved, start_time=start_time, file_type=state.file_type, active_device=state.active_device, active_sub_app=state.active_sub_app, device_type=state.device_type, activity_timer=state.activity_timer, completion_percent=state.completion_percent, sim_mode=state.sim_mode, view_mode=state.view_mode, workspace_tool=state.workspace_tool)
                elif was_running:
                    logger.info('Packet Tracer closed')
                    rpc.clear()
                    start_time = None
                    last_project = None
                    was_running = False
                    if args.exit_on_close:
                        logger.info('Exiting because Packet Tracer closed (--exit-on-close)')
                        break
            except Exception as loop_err:
                logger.debug(f'Loop iteration error: {loop_err}')
            time.sleep(args.interval if was_running else idle_interval)
    except KeyboardInterrupt:
        logger.info('Exiting...')
    finally:
        rpc.close()
        remove_lock_file()
if __name__ == '__main__':
    main()