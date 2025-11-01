@echo off
REM ============================================================
REM GitFocus Planner V2 - Script de Demarrage Complet
REM ============================================================

echo.
echo ============================================================
echo  GitFocus Planner V2 - Demarrage du Serveur
echo ============================================================
echo.

REM Se placer dans le repertoire racine du projet
cd /d "%~dp0.."

REM [1/5] Verifier Python
echo [1/5] Verification Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans PATH
    echo Installez Python 3.11+ depuis https://www.python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo       OK - %PYTHON_VERSION%

REM [2/5] Verifier les fichiers CSV requis
echo [2/5] Verification fichiers CSV...
if not exist "prod_data\LISTE_MERE.v2.csv" (
    echo [ERREUR] Fichier manquant: prod_data\LISTE_MERE.v2.csv
    pause
    exit /b 1
)
if not exist "prod_data\TACHES_RECURRENTES.v2.csv" (
    echo [ERREUR] Fichier manquant: prod_data\TACHES_RECURRENTES.v2.csv
    pause
    exit /b 1
)
if not exist "prod_data\TACHES_RESPIRATOIRES.v2.csv" (
    echo [ERREUR] Fichier manquant: prod_data\TACHES_RESPIRATOIRES.v2.csv
    pause
    exit /b 1
)
echo       OK - Tous les fichiers presents

REM [3/5] Arreter processus Flask existants
echo [3/5] Arret processus Flask existants...
taskkill /F /FI "WINDOWTITLE eq GitFocus Server V2*" >nul 2>&1
timeout /t 1 /nobreak >nul
echo       OK - Port 5000 libre

REM [4/5] Verification rapide avec verify.py
echo [4/5] Verification systeme...
python scripts\verify.py >nul 2>&1
if errorlevel 1 (
    echo [ATTENTION] Problemes detectes - Details:
    python scripts\verify.py
    echo.
    echo Continuer quand meme? (O/N)
    set /p continue=
    if /i not "%continue%"=="O" (
        pause
        exit /b 1
    )
)
echo       OK - Systeme pret

REM [5/5] Demarrer le serveur Flask
echo [5/5] Demarrage serveur Flask...
echo.
echo ============================================================
echo  SERVEUR EN COURS DE DEMARRAGE...
echo ============================================================
echo.
echo  URLs d'acces:
echo    Interface Web: http://localhost:5000/api/v2/gitfocus/interface
echo    Health Check:  http://localhost:5000/health
echo.
echo  Pour arreter: Fermez la fenetre "GitFocus Server V2" ou Ctrl+C
echo ============================================================
echo.

REM Demarrer dans une nouvelle fenetre avec titre personnalise
start "GitFocus Server V2" python -m webapp.server

REM Attendre 4 secondes pour laisser le serveur demarrer
timeout /t 4 /nobreak >nul

REM Verification finale
echo Verification demarrage...
python -c "import requests; r=requests.get('http://localhost:5000/health', timeout=3); print('       OK - Serveur demarre!') if r.status_code==200 else print('[ERREUR] Serveur non accessible')" 2>nul
if errorlevel 1 (
    echo [ATTENTION] Le serveur met du temps a demarrer...
    echo Verifiez la fenetre "GitFocus Server V2"
    timeout /t 2 /nobreak >nul
)

echo.
echo ============================================================
echo  SERVEUR DEMARRE
echo ============================================================
echo.
echo  Interface web:
echo    http://localhost:5000/api/v2/gitfocus/interface
echo.
echo  Fenetre serveur: "GitFocus Server V2"
echo  Appuyez sur une touche pour fermer cette fenetre...
echo ============================================================
echo.

pause
