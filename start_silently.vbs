Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
pythonwPath = scriptDir & "\.venv\Scripts\pythonw.exe"
mainPath = scriptDir & "\main.py"
' --onedir builds nest the exe in its own folder alongside _internal\. The flat
' path is kept as a fallback so an already-downloaded --onefile build still runs.
exeDirPath = scriptDir & "\dist\PacketTracerPresence\PacketTracerPresence.exe"
exeFlatPath = scriptDir & "\dist\PacketTracerPresence.exe"

' Background/autostart mode stays resident: this script is what the Startup
' shortcut launches, and it only runs once per login. With the default
' exit-on-close the daemon would quit the first time Packet Tracer closed and
' nothing would restart it until the next login, so it polls for Packet Tracer
' to reappear instead (slowly, while idle).
args = " --no-exit-on-close"

If FSO.FileExists(pythonwPath) Then
    WshShell.Run """" & pythonwPath & """ """ & mainPath & """" & args, 0, False
ElseIf FSO.FileExists(exeDirPath) Then
    WshShell.Run """" & exeDirPath & """" & args, 0, False
ElseIf FSO.FileExists(exeFlatPath) Then
    WshShell.Run """" & exeFlatPath & """" & args, 0, False
Else
    ' Launched with neither a venv nor a built exe present. Without this the
    ' Startup shortcut would fail completely silently, with nothing to diagnose.
    On Error Resume Next
    Set errFile = FSO.OpenTextFile(scriptDir & "\vbs_err.log", 8, True)
    errFile.WriteLine Now & " - no launcher found. Looked for:"
    errFile.WriteLine "  " & pythonwPath
    errFile.WriteLine "  " & exeDirPath
    errFile.WriteLine "  " & exeFlatPath
    errFile.WriteLine "  Run install.bat to create the virtual environment."
    errFile.Close
End If
