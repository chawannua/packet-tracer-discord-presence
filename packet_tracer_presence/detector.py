import logging
import os
import psutil
from .config import KNOWN_PROCESS_NAMES
logger = logging.getLogger(__name__)
_KNOWN_NAMES_LOWER = {n.lower() for n in KNOWN_PROCESS_NAMES}

class ProcessDetector:

    def __init__(self):
        self._cached_pid = None
        self._cached_process = None
        self._running_exe_path = None

    def _reset_cache(self):
        self._cached_pid = None
        self._cached_process = None

    def _is_known_name(self, name: str) -> bool:
        return name.lower() in _KNOWN_NAMES_LOWER

    def _cached_still_valid(self) -> bool:
        try:
            return self._cached_process.is_running() and self._cached_process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False

    def _scan_for_process(self):
        best = None
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'create_time']):
            try:
                info = proc.info
                if not self._is_known_name(info.get('name') or ''):
                    continue
                if proc.status() == psutil.STATUS_ZOMBIE:
                    continue
                if best is None or (info.get('create_time') or 0) < (best.info.get('create_time') or 0):
                    best = proc
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return best

    def find_packet_tracer(self) -> bool:
        if self._cached_process is not None:
            if self._cached_still_valid():
                return True
            self._reset_cache()
        best = self._scan_for_process()
        if best is None:
            return False
        self._cached_pid = best.info['pid']
        self._cached_process = best
        if best.info.get('exe'):
            self._running_exe_path = best.info['exe']
        return True

    def get_running_project_file(self):
        if self._cached_process:
            try:
                cmdline = self._cached_process.cmdline()
                for arg in cmdline:
                    arg_clean = arg.strip().strip('"').strip("'")
                    if arg_clean.lower().endswith(('.pkt', '.pka', '.pkz')):
                        return os.path.basename(arg_clean)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return None

    def get_installation_paths(self):
        paths = set()
        if self._running_exe_path:
            paths.add(os.path.dirname(self._running_exe_path))
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            import glob
            user_paths = glob.glob(os.path.join(user_profile, 'Cisco Packet Tracer*'))
            for p in user_paths:
                if os.path.isdir(p):
                    paths.add(p)
        prog_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
        prog_files_x86 = os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')
        for pf in [prog_files, prog_files_x86]:
            pt_dir = os.path.join(pf, 'Cisco Packet Tracer')
            if os.path.isdir(pt_dir):
                paths.add(pt_dir)
            import glob
            pf_paths = glob.glob(os.path.join(pf, 'Cisco Packet Tracer*'))
            for p in pf_paths:
                if os.path.isdir(p):
                    paths.add(p)
        return list(paths)