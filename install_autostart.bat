@echo off
REM ===== Ajoute Murmure au demarrage automatique de Windows (sans console) =====
REM IMPORTANT : on cree un RACCOURCI vers le .vbs reste dans le projet.
REM Copier le .vbs dans le dossier Demarrage casserait ses chemins relatifs.
powershell -NoProfile -Command "$s=New-Object -ComObject WScript.Shell; $l=$s.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Startup')) 'Murmure.lnk')); $l.TargetPath='%~dp0Murmure.vbs'; $l.WorkingDirectory='%~dp0'; $l.Description='Murmure - dictee vocale locale'; $l.Save()"
if errorlevel 1 goto :err
echo.
echo OK : Murmure demarrera automatiquement a l'ouverture de session.
echo Pour desinstaller : supprimer Murmure.lnk du dossier Demarrage (shell:startup).
pause
exit /b 0
:err
echo ECHEC de la creation du raccourci.
pause
exit /b 1
