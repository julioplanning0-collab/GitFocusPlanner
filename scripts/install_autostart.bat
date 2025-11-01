@echo off
echo ================================================
echo   Installation Démarrage Automatique
echo ================================================
echo.

set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set TARGET=%~dp0start.bat
set SHORTCUT=%STARTUP%\Planning System.lnk

echo Installation du raccourci dans le dossier Démarrage...
echo Cible: %TARGET%
echo.

REM Crée le raccourci avec PowerShell
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT%'); $Shortcut.TargetPath = '%TARGET%'; $Shortcut.WorkingDirectory = '%~dp0..'; $Shortcut.WindowStyle = 7; $Shortcut.Description = 'Système de Planning'; $Shortcut.Save()"

if exist "%SHORTCUT%" (
    echo [OK] Raccourci créé avec succès
    echo.
    echo Le système se lancera automatiquement au démarrage de Windows
    echo.
    echo Pour désinstaller: supprime le fichier
    echo %SHORTCUT%
) else (
    echo [ERREUR] Échec de création du raccourci
)

echo.
pause
