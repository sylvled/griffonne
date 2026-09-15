@echo off
REM SERVEUR de transcription distant (a lancer sur le PC avec le GPU)
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m griffonne.server
pause
