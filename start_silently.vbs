Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")
scriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
pythonwPath = FSO.BuildPath(scriptDir, ".venv\Scripts\pythonw.exe")
mainPath = FSO.BuildPath(scriptDir, "main.py")
WshShell.Run """" & pythonwPath & """ """ & mainPath & """", 0, False
