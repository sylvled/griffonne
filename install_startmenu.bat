@echo off
REM ===== Ajoute Griffonne au menu Demarrer de Windows =====
REM Le raccourci devient alors cherchable (touche Windows puis "griffonne").
REM Note : le dossier Demarrage n'est PAS indexe par la recherche, d'ou ce
REM raccourci distinct dans Menu Demarrer\Programmes.
powershell -NoProfile -Command "$s=New-Object -ComObject WScript.Shell; $l=$s.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Programs')) 'Griffonne.lnk')); $l.TargetPath='%~dp0Griffonne.vbs'; $l.WorkingDirectory='%~dp0'; $l.IconLocation='%~dp0assets\griffonne.ico,0'; $l.Description='Griffonne - dictee vocale locale'; $l.Save()"
if errorlevel 1 goto :err
echo.
echo OK : tape la touche Windows puis "griffonne" pour lancer l'application.
echo Pour desinstaller : supprimer Griffonne.lnk du menu Demarrer (shell:programs).
pause
exit /b 0
:err
echo ECHEC de la creation du raccourci.
pause
exit /b 1
