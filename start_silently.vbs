Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
pythonwPath = scriptDir & "\.venv\Scripts\pythonw.exe"
mainPath = scriptDir & "\main.py"
exePath = scriptDir & "\dist\PacketTracerPresence.exe"

If FSO.FileExists(pythonwPath) Then
    WshShell.Run """" & pythonwPath & """ """ & mainPath & """", 0, False
ElseIf FSO.FileExists(exePath) Then
    WshShell.Run """" & exePath & """", 0, False
End If
