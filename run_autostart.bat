@echo off
REM Lancement au demarrage : fenetre cachee (via Murmure.vbs) + log de diagnostic
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" -u -m murmure > "%~dp0murmure_autostart.log" 2>&1
