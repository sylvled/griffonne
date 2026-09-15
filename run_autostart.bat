@echo off
REM Lancement au demarrage : fenetre cachee (via Griffonne.vbs) + log de diagnostic
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" -u -m griffonne > "%~dp0griffonne_autostart.log" 2>&1
