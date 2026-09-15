@echo off
REM ===== Installation de Griffonne sur un PC SANS carte graphique =====
cd /d "%~dp0"
echo.
echo [1/3] Creation de l'environnement Python...
python -m venv .venv
if errorlevel 1 goto :err

echo [2/3] Installation des dependances (mode CPU, sans CUDA)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements-cpu.txt
if errorlevel 1 goto :err

echo [3/3] Configuration CPU par defaut...
if not exist config.json copy config.cpu.json config.json >nul

echo.
echo ===== Installation terminee =====
echo Lance run.bat pour demarrer (le modele 'small' se telechargera au 1er lancement).
pause
exit /b 0

:err
echo.
echo ECHEC. Verifie que Python est installe et accessible ("python --version").
pause
exit /b 1
