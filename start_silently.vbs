Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
pythonwPath = scriptDir & "\.venv\Scripts\pythonw.exe"
mainPath = scriptDir & "\main.py"
exeDirPath = scriptDir & "\dist\PacketTracerPresence\PacketTracerPresence.exe"
exeFlatPath = scriptDir & "\dist\PacketTracerPresence.exe"

args = " --no-exit-on-close"

If FSO.FileExists(pythonwPath) Then
    cmd = """" & pythonwPath & """ """ & mainPath & """" & args
ElseIf FSO.FileExists(exeDirPath) Then
    cmd = """" & exeDirPath & """" & args
ElseIf FSO.FileExists(exeFlatPath) Then
    cmd = """" & exeFlatPath & """" & args
Else
    cmd = ""
End If

If cmd = "" Then
    On Error Resume Next
    Set errFile = FSO.OpenTextFile(scriptDir & "\vbs_err.log", 8, True)
    errFile.WriteLine Now & " - no launcher found. Looked for:"
    errFile.WriteLine "  " & pythonwPath
    errFile.WriteLine "  " & exeDirPath
    errFile.WriteLine "  " & exeFlatPath
    errFile.WriteLine "  Run install.bat to create the virtual environment."
    errFile.Close
    WScript.Quit
End If

fastRestarts = 0
Do
    startTick = Timer
    WshShell.Run cmd, 0, True
    elapsed = Timer - startTick
    If elapsed < 5 Then
        fastRestarts = fastRestarts + 1
    Else
        fastRestarts = 0
    End If
    If fastRestarts >= 3 Then
        On Error Resume Next
        Set errFile = FSO.OpenTextFile(scriptDir & "\vbs_err.log", 8, True)
        errFile.WriteLine Now & " - daemon exited within 5s three times in a row; giving up to avoid a crash loop."
        errFile.Close
        Exit Do
    End If
    WScript.Sleep 1000
Loop
