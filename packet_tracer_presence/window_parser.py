"""
Window title parser for Cisco Packet Tracer
"""
try:
    import pygetwindow as gw
except Exception:
    gw = None
import re
from typing import Optional, Tuple

class WindowParser:
    def __init__(self):
        self.base_title_re = re.compile(r"^Cisco Packet Tracer(?:\s*-\s*\[(.*?)\])?$")

    def get_active_project(self) -> Tuple[Optional[str], bool]:
        """
        Returns (project_name, is_unsaved)
        """
        try:
            if gw is None or not hasattr(gw, "getWindowsWithTitle"):
                return None, False
            windows = gw.getWindowsWithTitle("Cisco Packet Tracer")
        except Exception:
            return None, False

        for window in windows:
            title = window.title.strip()
            
            if title == "Cisco Packet Tracer":
                return "Untitled", False
            
            match = self.base_title_re.match(title)
            if match:
                inner = match.group(1)
                if inner is not None:
                    inner_clean = inner.strip()
                    is_unsaved = inner_clean.endswith("*")
                    name = inner_clean[:-1].strip() if is_unsaved else inner_clean
                    return (name if name else "Untitled"), is_unsaved
                return "Untitled", False
                    
        return None, False
