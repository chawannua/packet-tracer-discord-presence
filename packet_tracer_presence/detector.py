"""
Packet Tracer process detector
"""
import psutil
import os
from .config import KNOWN_PROCESS_NAMES

class ProcessDetector:
    def __init__(self):
        self._cached_pid = None
        self._cached_process = None

    def find_packet_tracer(self) -> bool:
        """
        Check if Packet Tracer is currently running.
        Uses cached PID for efficiency if previously found.
        """
        if self._cached_pid and self._cached_process:
            try:
                if psutil.pid_exists(self._cached_pid) and self._cached_process.status() != psutil.STATUS_ZOMBIE:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Process died or closed
            self._cached_pid = None
            self._cached_process = None

        # Scan for process
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] in KNOWN_PROCESS_NAMES:
                    self._cached_pid = proc.info['pid']
                    self._cached_process = proc
                    if proc.info.get('exe'):
                        self._running_exe_path = proc.info['exe']
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return False

    def get_running_project_file(self):
        """
        Extract active project/topology filename from process cmdline if available.
        """
        if self._cached_process:
            try:
                cmdline = self._cached_process.cmdline()
                for arg in cmdline:
                    arg_clean = arg.strip().strip('"').strip("'")
                    if arg_clean.lower().endswith(('.pkt', '.pka', '.pkz')):
                        return os.path.basename(arg_clean)
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                pass
        return None

    def get_installation_paths(self):
        """
        Auto-detect installation paths.
        Searches running process path, known user directories, and Program Files.
        """
        paths = set()
        
        # 1. Running process path
        if hasattr(self, '_running_exe_path') and self._running_exe_path:
            paths.add(os.path.dirname(self._running_exe_path))
            
        # 2. User directory
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            import glob
            user_paths = glob.glob(os.path.join(user_profile, 'Cisco Packet Tracer*'))
            for p in user_paths:
                if os.path.isdir(p):
                    paths.add(p)
                    
        # 3. Program Files
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
