' Lance Griffonne SANS fenetre visible (demarrage automatique Windows).
' Passe par run_autostart.bat pour conserver un log de diagnostic.
Set fso = CreateObject("Scripting.FileSystemObject")
base = fso.GetParentFolderName(WScript.ScriptFullName)
Set sh = CreateObject("WScript.Shell")
sh.CurrentDirectory = base
sh.Run """" & base & "\run_autostart.bat""", 0, False
