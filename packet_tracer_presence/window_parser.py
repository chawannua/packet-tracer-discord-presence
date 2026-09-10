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
    workspace_tool: Optional[str] = None

TAB_MAPPINGS = {
    "Physical": "Physical (Hardware)",
    "Config": "Config Tab",
    "CLI": "CLI",
    "Services": "Services",
    "Programming": "Programming",
    "Attributes": "Attributes",
}

KNOWN_APPLETS = [
    "Terminal",
    "Command Prompt",
    "IP Configuration",
    "Web Browser",
    "PC Wireless",
    "Text Editor",
    "Email",
    "Traffic Generator",
    "MIB Browser",
    "Cisco Webex",
    "VPN",
    "Dial-up",
    "Bluetooth",
    "Firewall",
    "Netflow Collector",
    "IoT IDE",
]

WORKSPACE_TOOLS = {
    "Inspect (I)": "Inspecting Network Components",
    "Delete (Del)": "Deleting Components",
    "Place Note (N)": "Annotating Topology (Notes)",
    "Add Simple PDU (P)": "Testing Connectivity (Simple PDU Ping)",
    "Add Complex PDU (C)": "Sending Complex PDU Packets",
}

def parse_cli_mode(text: str) -> Optional[str]:
    r"""
    Parse CLI/terminal buffer or last line to identify specific Cisco/shell mode.
    Modes:
    - 'Press RETURN to get started' -> [Console Connected]
    - (config-subif)# -> [Sub-Interface Config]
    - (config-if)# -> [Interface Config]
    - (config-router)# -> [Routing Config]
    - (config-line)# -> [Line/Console Config]
    - (config-vlan)# -> [VLAN Config]
    - (dhcp-config)# -> [DHCP Config]
    - (config)# -> [Global Config]
    - ^[A-Za-z]:\\.*>\s*$ -> [Command Shell]
    - .*#\s*$ -> [Privileged Mode]
    - .*>\s*$ -> [User EXEC Mode]
    """
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        if "Press RETURN to get started" in text:
            return "[Console Connected]"
        return None
    last = lines[-1]

    if "Press RETURN to get started" in last:
        return "[Console Connected]"
    if re.search(r"\(config-subif\)#\s*$", last):
        return "[Sub-Interface Config]"
    if re.search(r"\(config-if\)#\s*$", last):
        return "[Interface Config]"
    if re.search(r"\(config-router\)#\s*$", last):
        return "[Routing Config]"
    if re.search(r"\(config-line\)#\s*$", last):
        return "[Line/Console Config]"
    if re.search(r"\(config-vlan\)#\s*$", last):
        return "[VLAN Config]"
    if re.search(r"\(dhcp-config\)#\s*$", last):
        return "[DHCP Config]"
    if re.search(r"\(config\)#\s*$", last):
        return "[Global Config]"
    if re.search(r"^[A-Za-z]:\\.*>\s*$", last):
        return "[Command Shell]"
    if re.search(r"#\s*$", last):
        return "[Privileged Mode]"
    if re.search(r">\s*$", last):
        return "[User EXEC Mode]"
    if "Press RETURN to get started" in text:
        return "[Console Connected]"
    return None

class WindowParser:
    parse_cli_mode = staticmethod(parse_cli_mode)
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
            state.workspace_tool = f"Designing {state.view_mode} Topology ({state.sim_mode})"
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
                            c_name = c.Name or ""
                            if c_name in ("Realtime Mode", "Simulation Mode", "Logical Mode", "Physical Mode"):
                                toggle = c.GetPattern(auto.PatternId.TogglePattern)
                                if toggle and toggle.ToggleState == 1:
                                    if "Realtime" in c_name:
                                        state.sim_mode = "Realtime"
                                    elif "Simulation" in c_name:
                                        state.sim_mode = "Simulation"
                                    elif "Logical" in c_name:
                                        state.view_mode = "Logical"
                                    elif "Physical" in c_name:
                                        state.view_mode = "Physical"

                            for tool_btn, tool_desc in WORKSPACE_TOOLS.items():
                                if tool_btn == c_name or tool_btn in c_name:
                                    toggle = c.GetPattern(auto.PatternId.TogglePattern)
                                    if toggle and toggle.ToggleState == 1:
                                        state.workspace_tool = tool_desc
                                        break
                                    sel = c.GetPattern(auto.PatternId.SelectionItemPattern)
                                    if sel and sel.IsSelected:
                                        state.workspace_tool = tool_desc
                                        break

                    # Device Window:
                    if state.active_device and name.startswith(state.active_device) and cname in ("CWorkstationDialog", "CRouterDialog", "CSwitchDialog", "CDeviceDialog"):
                        sub_title = ""
                        selected_tab = None
                        terminal_text = ""
                        for c, _ in auto.WalkControl(win):
                            c_name = c.Name or ""
                            c_class = c.ClassName or ""
                            c_auto_id = c.AutomationId or ""

                            # Tab selection detection
                            if c_class == "QTabBar" or getattr(c, "ControlType", None) == getattr(auto.ControlType, "TabItemControl", None) or "TabItem" in getattr(c, "ControlTypeName", ""):
                                sel_item = c.GetPattern(auto.PatternId.SelectionItemPattern)
                                if sel_item and sel_item.IsSelected and c_name:
                                    selected_tab = c_name
                                elif c_class == "QTabBar":
                                    sel_pat = c.GetPattern(auto.PatternId.SelectionPattern)
                                    if sel_pat:
                                        try:
                                            for item in sel_pat.GetSelection():
                                                if item.Name:
                                                    selected_tab = item.Name
                                                    break
                                        except Exception:
                                            pass
                                    if not selected_tab and c_name and c_name in ("Physical", "Config", "CLI", "Desktop", "Services", "Programming", "Attributes"):
                                        selected_tab = c_name

                            # Applet detection on Desktop
                            if c_class == "QLabel" and "m_titleLabel" in c_auto_id and c_name:
                                sub_title = c_name
                            elif c_name in KNOWN_APPLETS:
                                sub_title = c_name
                            elif not sub_title:
                                for app in KNOWN_APPLETS:
                                    if app in c_name and (c_class in ("QMdiSubWindow", "QDialog", "QWidget") or "Window" in getattr(c, "ControlTypeName", "")):
                                        sub_title = app
                                        break

                            # Terminal / Command line buffer
                            if c_class == "CCommandLine" or "CommandLine" in c_class or c_class in ("QTextEdit", "QPlainTextEdit"):
                                val_pattern = c.GetPattern(auto.PatternId.ValuePattern)
                                if val_pattern and val_pattern.Value:
                                    terminal_text = val_pattern.Value
                                elif not terminal_text:
                                    text_pattern = c.GetPattern(auto.PatternId.TextPattern)
                                    if text_pattern:
                                        try:
                                            terminal_text = text_pattern.DocumentRange.GetText(-1)
                                        except Exception:
                                            pass
                                if not terminal_text and c_name:
                                    terminal_text = c_name

                        cli_mode = parse_cli_mode(terminal_text) if terminal_text else None

                        if cli_mode:
                            if sub_title:
                                state.active_sub_app = f"{sub_title} {cli_mode}"
                            elif selected_tab == "CLI" or not selected_tab:
                                state.active_sub_app = f"CLI {cli_mode}"
                            else:
                                mapped_tab = TAB_MAPPINGS.get(selected_tab, selected_tab)
                                state.active_sub_app = f"{mapped_tab} {cli_mode}"
                        elif sub_title:
                            state.active_sub_app = sub_title
                        elif selected_tab:
                            state.active_sub_app = TAB_MAPPINGS.get(selected_tab, selected_tab)
            except Exception as e:
                pass

        if not state.active_device:
            if not state.workspace_tool:
                state.workspace_tool = f"Designing {state.view_mode} Topology ({state.sim_mode})"

        return state

    def get_active_project(self) -> Tuple[Optional[str], bool]:
        """
        Backward compatibility wrapper
        """
        state = self.get_active_activity()
        return (state.file_name if state.file_name != "Workspace" else None), state.is_unsaved
