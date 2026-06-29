@echo off
REM Ajoute Murmure au demarrage automatique de Windows (sans console).
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
copy /Y "%~dp0Murmure.vbs" "%STARTUP%\Murmure.vbs" >nul
if %errorlevel%==0 (
  echo OK : Murmure demarrera automatiquement a l'ouverture de session.
) else (
  echo Echec de la copie vers %STARTUP%
)
echo Pour desinstaller : supprimez "%STARTUP%\Murmure.vbs"
pause
