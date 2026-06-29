@echo off
REM Mode CONSOLE (dictée + logs visibles) - le plus simple/robuste
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m murmure.app
pause
