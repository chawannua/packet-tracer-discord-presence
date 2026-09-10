import os
import subprocess

def install():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    pythonw = os.path.join(project_dir, '.venv', 'Scripts', 'pythonw.exe')
    vbs_path = os.path.join(project_dir, 'start_silently.vbs')
    ps_code = f"""\n    $ws = New-Object -ComObject WScript.Shell\n    $startup = Join-Path $env:APPDATA 'Microsoft\\Windows\\Start Menu\\Programs\\Startup'\n    $lnk = Join-Path $startup 'PacketTracerPresence.lnk'\n    $s = $ws.CreateShortcut($lnk)\n    $s.TargetPath = '{vbs_path}'\n    $s.WorkingDirectory = '{project_dir}'\n    $s.WindowStyle = 7\n    $s.Description = 'Cisco Packet Tracer Discord Rich Presence (Silent)'\n    $s.Save()\n    Write-Output "SUCCESS: Created startup shortcut at $lnk"\n    """
    res = subprocess.run(['powershell', '-NoProfile', '-Command', ps_code], capture_output=True, text=True)
    print(res.stdout.strip())
    if res.stderr:
        print('Error:', res.stderr.strip())
if __name__ == '__main__':
    install()