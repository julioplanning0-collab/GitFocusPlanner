@echo off
REM ============================================================================
REM GitFocus Planner - Script de redémarrage Windows
REM Ce script arrête puis redémarre le serveur proprement
REM ============================================================================

echo.
echo ========================================
echo  GitFocus Planner - Redemarrage
echo ========================================
echo.

REM Détection du répertoire du projet
cd /d "%~dp0.."
set PROJECT_DIR=%CD%

REM Arrêt du serveur
echo [INFO] Arret du serveur en cours...
call "%PROJECT_DIR%\scripts\stop.bat"

REM Attente pour être sûr que tout est bien arrêté
echo [INFO] Attente de 3 secondes...
timeout /t 3 /nobreak >nul

REM Redémarrage du serveur
echo [INFO] Redemarrage du serveur...
call "%PROJECT_DIR%\scripts\start.bat"
