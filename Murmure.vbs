' Lance Murmure SANS fenetre console (ideal pour le demarrage automatique).
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = base
sh.Environment("PROCESS")("PYTHONUTF8") = "1"
sh.Run """" & base & "\.venv\Scripts\pythonw.exe"" -m murmure", 0, False
