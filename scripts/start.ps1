# ============================================================
# GitFocus Planner - Script de Demarrage PowerShell
# Versions: V2 (existante) + V3 (en developpement)
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GitFocus Planner - Demarrage du Serveur" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Se placer dans le repertoire racine du projet
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# [1/5] Verifier Python
Write-Host "[1/5] Verification Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python non trouve"
    }
    Write-Host "       OK - $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Python n'est pas installe ou pas dans PATH" -ForegroundColor Red
    Write-Host "Installez Python 3.11+ depuis https://www.python.org" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

# [2/5] Verifier repertoire des donnees
Write-Host "[2/5] Verification repertoire donnees..." -ForegroundColor Yellow
$dataDir = "$ProjectRoot\data\prod_data"

if (-not (Test-Path $dataDir)) {
    Write-Host "[ERREUR] Repertoire data\prod_data absent: $dataDir" -ForegroundColor Red
    Write-Host "Verifiez que le repertoire existe" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}

# Verifier fichiers CSV critiques V3
$requiredFiles = @(
    "$dataDir\LISTE_MERE.v3.csv",
    "$dataDir\TACHES_RECURRENTES.v3.csv",
    "$dataDir\temps_morts.csv"
)

$missingFiles = @()
foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "[ERREUR] Fichiers critiques manquants:" -ForegroundColor Red
    foreach ($file in $missingFiles) {
        Write-Host "  - $file" -ForegroundColor Red
    }
    Read-Host "Appuyez sur Entree pour quitter"
    exit 1
}
Write-Host "       OK - Fichiers critiques presents" -ForegroundColor Green

# [3/5] Arreter TOUS les processus Python existants
Write-Host "[3/5] Arret processus Python existants..." -ForegroundColor Yellow
# Méthode 1: Tuer tous les processus python.exe
Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Méthode 2: Vérifier qu'aucun processus n'écoute sur le port 5001 (V3)
$portInUse = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "       [WARNING] Port 5001 encore occupé, tentative de libération..." -ForegroundColor Yellow
    $processId = $portInUse.OwningProcess
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# Vérification finale
$stillInUse = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
if ($stillInUse) {
    Write-Host "       [ERREUR] Impossible de libérer le port 5001" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

Write-Host "       OK - Port 5001 libre" -ForegroundColor Green

# [4/5] Verification systeme avec verify.py
Write-Host "[4/5] Verification systeme..." -ForegroundColor Yellow
$verifyResult = python scripts\verify.py 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ATTENTION] Problemes detectes - Details:" -ForegroundColor Yellow
    Write-Host $verifyResult
    Write-Host ""
    $continue = Read-Host "Continuer quand meme? (O/N)"
    if ($continue -ne "O" -and $continue -ne "o") {
        exit 1
    }
} else {
    Write-Host "       OK - Systeme pret" -ForegroundColor Green
}

# [5/5] Demarrer le serveur Flask
Write-Host "[5/5] Demarrage serveur Flask..." -ForegroundColor Yellow
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SERVEUR V3 EN COURS DE DEMARRAGE..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " URLs d'acces:" -ForegroundColor White
Write-Host "   Interface Web V3: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5001/gitfocus-v3" -ForegroundColor Green
Write-Host "   Health Check:     " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5001/api/v3/health" -ForegroundColor Green
Write-Host ""
Write-Host " Pour arreter: Ctrl+C dans cette fenetre" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Demarrer le serveur V3 dans une nouvelle fenetre
$serverProcess = Start-Process -FilePath "python" -ArgumentList "-m", "webapp_v3_pure.server_v3" -WindowStyle Normal -PassThru

# Attendre 4 secondes pour laisser le serveur demarrer
Start-Sleep -Seconds 4

# Verification finale
Write-Host "Verification demarrage..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5001/api/v3/health" -TimeoutSec 3 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "       OK - Serveur V3 demarre!" -ForegroundColor Green
    } else {
        throw "Status code: $($response.StatusCode)"
    }
} catch {
    Write-Host "[ATTENTION] Le serveur met du temps a demarrer..." -ForegroundColor Yellow
    Write-Host "Verifiez que le serveur est bien demarre" -ForegroundColor Yellow
    Start-Sleep -Seconds 2
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " SERVEUR V3 DEMARRE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Interface web:" -ForegroundColor White
Write-Host "   V3: http://localhost:5001/gitfocus-v3" -ForegroundColor Green
Write-Host ""
Write-Host " PID Serveur: $($serverProcess.Id)" -ForegroundColor Gray
Write-Host " Pour arreter: Ctrl+C ou fermez la fenetre du serveur" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Ouvrir le navigateur automatiquement sur V3
Write-Host "Ouverture du navigateur dans 3 secondes..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Start-Process "http://localhost:5001/gitfocus-v3"

Write-Host ""
Write-Host "Appuyez sur une touche pour fermer cette fenetre..." -ForegroundColor Gray
Read-Host
