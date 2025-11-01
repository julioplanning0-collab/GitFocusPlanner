@echo off
REM ============================================================
REM GitFocus Planner V2 - Script de Lancement Rapide
REM ============================================================

echo.
echo ============================================================
echo  GitFocus Planner V2 - Demarrage
echo ============================================================
echo.

REM Verifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans PATH
    pause
    exit /b 1
)

REM Se placer dans le bon repertoire
cd /d "%~dp0"

echo [1/3] Verification des fichiers...
python scripts\verify.py >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Fichiers manquants - Voir details:
    python scripts\verify.py
    pause
    exit /b 1
)
echo       OK - Tous les fichiers presents

echo [2/3] Demarrage du serveur Flask...
start "GitFocus Server" python -m webapp.server
timeout /t 3 /nobreak >nul

echo [3/3] Verification du serveur...
timeout /t 2 /nobreak >nul
python scripts\verify.py

echo.
echo ============================================================
echo  SYSTEME DEMARRE
echo ============================================================
echo.
echo  Interface Web:
echo    http://localhost:5000/api/v2/gitfocus/interface
echo.
echo  Pour arreter: Fermez la fenetre "GitFocus Server"
echo ============================================================
echo.

pause
