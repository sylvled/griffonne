@echo off
REM Mode APPLICATION : icone dans la barre des taches + reglages (avec logs)
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m murmure
pause
