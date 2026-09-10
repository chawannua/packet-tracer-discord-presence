Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
pythonwPath = scriptDir & "\.venv\Scripts\pythonw.exe"
mainPath = scriptDir & "\main.py"
exePath = scriptDir & "\dist\PacketTracerPresence.exe"

' Background/autostart mode stays resident: this script is what the Startup
' shortcut launches, and it only runs once per login. With the default
' exit-on-close the daemon would quit the first time Packet Tracer closed and
' nothing would restart it until the next login, so it polls for Packet Tracer
' to reappear instead (slowly, while idle).
args = " --no-exit-on-close"

If FSO.FileExists(pythonwPath) Then
    WshShell.Run """" & pythonwPath & """ """ & mainPath & """" & args, 0, False
ElseIf FSO.FileExists(exePath) Then
    WshShell.Run """" & exePath & """" & args, 0, False
End If
