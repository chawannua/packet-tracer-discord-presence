"""
Installs Packet Tracer Presence into the Windows Startup folder so it runs silently in the background automatically.
"""
import os
import subprocess

def install():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    pythonw = os.path.join(project_dir, ".venv", "Scripts", "pythonw.exe")
    vbs_path = os.path.join(project_dir, "start_silently.vbs")

    ps_code = f"""
    $ws = New-Object -ComObject WScript.Shell
    $startup = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
    $lnk = Join-Path $startup 'PacketTracerPresence.lnk'
    $s = $ws.CreateShortcut($lnk)
    $s.TargetPath = '{vbs_path}'
    $s.WorkingDirectory = '{project_dir}'
    $s.WindowStyle = 7
    $s.Description = 'Cisco Packet Tracer Discord Rich Presence (Silent)'
    $s.Save()
    Write-Output "SUCCESS: Created startup shortcut at $lnk"
    """
    
    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_code], capture_output=True, text=True)
    print(res.stdout.strip())
    if res.stderr:
        print("Error:", res.stderr.strip())

if __name__ == "__main__":
    install()
