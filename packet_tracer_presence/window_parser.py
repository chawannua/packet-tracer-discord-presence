"""
Window title parser for Cisco Packet Tracer
"""
try:
    import pygetwindow as gw
except Exception:
    gw = None
try:
    import uiautomation as auto
except Exception:
    auto = None
import re
import os
import ctypes
import psutil
from typing import Optional, Tuple, List
from dataclasses import dataclass
from .config import KNOWN_PROCESS_NAMES

@dataclass
class PacketTracerState:
    file_name: str = "Workspace"
    file_type: str = "unknown"
    is_unsaved: bool = False
    active_device: Optional[str] = None
    active_sub_app: Optional[str] = None
    device_type: str = "pt_logo"
    activity_timer: Optional[str] = None
    completion_percent: Optional[str] = None
    sim_mode: Optional[str] = "Realtime"
    view_mode: Optional[str] = "Logical"

class WindowParser:
    def __init__(self):
        # Base title regex for PT 8/9 and 7
        # Format: Cisco Packet Tracer - <FilePathOrName> [- <Profile>] [- <Timestamp>]
        self.base_title_re = re.compile(r"^Cisco Packet Tracer\s*-\s*(.*?)$")
        self.timer_re = re.compile(r"PT Activity:\s*(\d{1,2}:\d{2}:\d{2})")
        
    def _apply_desktop_context(self):
        if os.name == 'nt':
            try:
                user32 = ctypes.windll.user32
                h_desktop = user32.OpenDesktopW("default", 0, False, 0x1FF)
                if h_desktop:
                    user32.SetThreadDesktop(h_desktop)
            except Exception:
                pass

    def _determine_device_type(self, title: str) -> str:
        title_lower = title.lower()
        if any(x in title_lower for x in ["router", "2911", "1941", "4321", "4331", "isr"]):
            return "router"
        if any(x in title_lower for x in ["switch", "2960", "3560", "3650", "bridge"]):
            return "switch"
        if any(x in title_lower for x in ["pc", "computer", "desktop"]):
            return "pc"
        if "laptop" in title_lower:
            return "laptop"
        if "server" in title_lower:
            return "server"
        if any(x in title_lower for x in ["phone", "smart", "tablet"]):
            return "phone"
        if any(x in title_lower for x in ["iot", "thing", "sensor", "mcu", "sbc"]):
            return "iot"
        return "device"

    def _get_pt_pids(self) -> set:
        pids = set()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] in KNOWN_PROCESS_NAMES:
                    pids.add(proc.info['pid'])
            except:
                pass
        return pids

    def get_active_activity(self) -> PacketTracerState:
        """
        Returns full enriched state.
        """
        state = PacketTracerState()
        
        self._apply_desktop_context()

        try:
            if gw is None or not hasattr(gw, "getAllWindows"):
                return state
            windows = gw.getAllWindows()
        except Exception:
            return state

        pt_pids = self._get_pt_pids()
        if not pt_pids:
            return state

        main_title = None
        devices = []
        user32 = ctypes.windll.user32
        
        # Get active window globally to check if we are actively configuring
        active_window = gw.getActiveWindow()
        active_hwnd = active_window._hWnd if active_window else None
        
        for window in windows:
            title = window.title.strip()
            if not title:
                continue

            try:
                hwnd = window._hWnd
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value not in pt_pids:
                    continue
            except Exception:
                continue

            # It's a PT window
            timer_match = self.timer_re.search(title)
            if timer_match:
                state.activity_timer = timer_match.group(1)

            if title.startswith("Cisco Packet Tracer"):
                if title != "Cisco Packet Tracer":
                    main_title = title
                continue

            # Device window filtering
            excluded = False
            for ex in ["PT Activity", "Default IME", "MSCTFIME UI", "Please wait", "Chrome_WidgetWin", "QTreeViewThemeHelper"]:
                if title.startswith(ex.replace("*", "")) or title == ex:
                    excluded = True
                    break
            
            if not excluded:
                is_active = (hwnd == active_hwnd)
                devices.append((title, is_active))

        if main_title:
            match = self.base_title_re.match(main_title)
            if match:
                inner = match.group(1).strip()
                
                is_unsaved = False
                if inner.endswith("*") or "Untitled" in inner or "New" in inner:
                    is_unsaved = True
                
                parts = inner.split(" - ")
                file_part = parts[0]
                if file_part.endswith("*"):
                    file_part = file_part[:-1]
                
                file_name = os.path.basename(file_part)
                state.file_name = file_name
                state.is_unsaved = is_unsaved
                
                ext = file_name.split(".")[-1].lower() if "." in file_name else ""
                if ext in ["pka", "pkt", "pkz"]:
                    state.file_type = ext

        active_device = None
        for title, is_active in devices:
            if is_active:
                active_device = title
                break
        if not active_device and devices:
            active_device = devices[0][0]

        if active_device:
            if active_device.endswith(" - CLI"):
                active_device = active_device[:-6]
            state.active_device = active_device
            state.device_type = self._determine_device_type(active_device)

        # Deep Telemetry via uiautomation
        if auto is not None:
            try:
                auto.SetGlobalSearchTimeout(0.2)
                for win in auto.GetRootControl().GetChildren():
                    name = win.Name
                    cname = win.ClassName

                    # Instruction / Activity Dialog:
                    if "Instruction" in cname or "Activity" in name:
                        for c, _ in auto.WalkControl(win):
                            if c.Name and c.Name.startswith("Completion:"):
                                state.completion_percent = c.Name.split("Completion:")[1].strip()
                                break

                    # Main Window:
                    if "Packet Tracer" in name and cname == "CAppWindow":
                        for c, _ in auto.WalkControl(win):
                            if c.Name in ("Realtime Mode", "Simulation Mode", "Logical Mode", "Physical Mode"):
                                toggle = c.GetPattern(auto.PatternId.TogglePattern)
                                if toggle and toggle.ToggleState == 1:
                                    if "Realtime" in c.Name:
                                        state.sim_mode = "Realtime"
                                    elif "Simulation" in c.Name:
                                        state.sim_mode = "Simulation"
                                    elif "Logical" in c.Name:
                                        state.view_mode = "Logical"
                                    elif "Physical" in c.Name:
                                        state.view_mode = "Physical"

                    # Device Window:
                    if state.active_device and name.startswith(state.active_device) and cname in ("CWorkstationDialog", "CRouterDialog", "CSwitchDialog", "CDeviceDialog"):
                        sub_title = ""
                        prompt = ""
                        for c, _ in auto.WalkControl(win):
                            if c.ClassName == "QLabel" and "m_titleLabel" in (c.AutomationId or ""):
                                sub_title = c.Name
                            if c.ClassName == "QTabBar":
                                tab_pattern = c.GetPattern(auto.PatternId.SelectionPattern)
                                if not sub_title and c.Name:
                                    sub_title = c.Name
                            if c.ClassName == "CCommandLine":
                                val_pattern = c.GetPattern(auto.PatternId.ValuePattern)
                                if val_pattern and val_pattern.Value:
                                    lines = [ln.strip() for ln in val_pattern.Value.splitlines() if ln.strip()]
                                    if lines:
                                        last = lines[-1]
                                        m = re.search(r"([\w\-]+(?:\([^\)]+\))?[>#])\s*$", last)
                                        if m:
                                            prompt = m.group(1)
                        
                        if sub_title and prompt:
                            state.active_sub_app = f"{sub_title} ({prompt})"
                        elif sub_title:
                            state.active_sub_app = sub_title
                        elif prompt:
                            state.active_sub_app = f"CLI ({prompt})"
            except Exception as e:
                pass

        return state

    def get_active_project(self) -> Tuple[Optional[str], bool]:
        """
        Backward compatibility wrapper
        """
        state = self.get_active_activity()
        return (state.file_name if state.file_name != "Workspace" else None), state.is_unsaved
