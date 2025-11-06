# GitFocus Planner - Script d'arret PowerShell
# Arrete TOUS les processus Python et libere les ports 5000 (V2) et 5001 (V3)

Write-Host ""
Write-Host "========================================"
Write-Host " GitFocus Planner - Arret TOTAL"
Write-Host "========================================"
Write-Host ""

# Fonction pour afficher les processus Python
function Show-PythonProcesses {
    $pythonProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue
    if ($pythonProcs) {
        Write-Host "[INFO] Processus Python trouves:"
        $pythonProcs | ForEach-Object {
            Write-Host "  PID: $($_.Id) | Mem: $([math]::Round($_.WorkingSet64/1MB, 2)) MB"
        }
        return $pythonProcs.Count
    } else {
        Write-Host "[INFO] Aucun processus Python trouve"
        return 0
    }
}

# Fonction pour tuer les processus Python
function Stop-AllPythonProcesses {
    param ([int]$AttemptNumber)

    Write-Host ""
    Write-Host "[TENTATIVE $AttemptNumber/5] Arret des processus Python..."

    $pythonProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue

    if (-not $pythonProcs) {
        Write-Host "[RESULTAT] Aucun processus Python a arreter"
        return $false
    }

    $killCount = 0
    foreach ($proc in $pythonProcs) {
        try {
            Write-Host "  Arret PID $($proc.Id)..."
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            $killCount++
            Write-Host "  [OK] PID $($proc.Id) arrete"
        } catch {
            Write-Host "  [ERREUR] Impossible d'arreter PID $($proc.Id): $_" -ForegroundColor Red
        }
    }

    Write-Host "[RESULTAT] $killCount processus arretes"
    Start-Sleep -Seconds 2
    return $killCount -gt 0
}

# ETAPE 1: Afficher les processus AVANT
Write-Host "[AVANT] Etat des processus Python:"
$countBefore = Show-PythonProcesses

# ETAPE 2: Arreter tous les processus Python (5 tentatives)
Write-Host ""
Write-Host "========================================"
Write-Host " ARRET DES PROCESSUS PYTHON"
Write-Host "========================================"

$stopped = $false
for ($i = 1; $i -le 5; $i++) {
    $hadProcesses = Stop-AllPythonProcesses -AttemptNumber $i
    if (-not $hadProcesses) {
        Write-Host ""
        Write-Host "[SUCCESS] Tous les processus Python ont ete arretes!"
        $stopped = $true
        break
    }
}

# ETAPE 3: Verification finale
Write-Host ""
Write-Host "========================================"
Write-Host " VERIFICATION FINALE"
Write-Host "========================================"
Write-Host ""
Write-Host "[APRES] Etat des processus Python:"
$countAfter = Show-PythonProcesses

if ($countAfter -gt 0) {
    Write-Host ""
    Write-Host "[ERREUR] $countAfter processus Python sont encore actifs!" -ForegroundColor Red
    Write-Host "[DIAGNOSTIC] Raisons possibles:" -ForegroundColor Yellow
    Write-Host "  - Processus proteges par l'OS"
    Write-Host "  - Privileges administrateur requis"
    Write-Host "  - Processus en cours de fermeture"
} else {
    Write-Host ""
    Write-Host "[OK] Tous les processus Python ont ete arretes!" -ForegroundColor Green
}

# ETAPE 4: Verification des ports 5000 (V2) et 5001 (V3)
Write-Host ""
Write-Host "========================================"
Write-Host " VERIFICATION PORTS"
Write-Host "========================================"

# Port 5000 (V2)
Write-Host ""
Write-Host "[INFO] Verification du port 5000 (V2)..."
$port5000 = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

if ($port5000) {
    Write-Host "[ATTENTION] Le port 5000 est encore occupe:" -ForegroundColor Yellow
    $port5000 | ForEach-Object {
        Write-Host "  Etat: $($_.State) | PID: $($_.OwningProcess)"
    }

    Write-Host ""
    Write-Host "[ACTION] Tentative de liberation forcee du port 5000..."

    foreach ($conn in $port5000) {
        $pid = $conn.OwningProcess
        try {
            Write-Host "  Arret PID $pid sur port 5000..."
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "  [OK] PID $pid arrete"
        } catch {
            Write-Host "  [ERREUR] Impossible d'arreter PID $pid : $_" -ForegroundColor Red
        }
    }

    Start-Sleep -Seconds 2

    # Verification finale
    $port5000Final = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue

    if ($port5000Final) {
        Write-Host ""
        Write-Host "[ERREUR] Le port 5000 est ENCORE occupe!" -ForegroundColor Red
        Write-Host "[DIAGNOSTIC] Raisons possibles:" -ForegroundColor Yellow
        Write-Host "  - Etat TIME_WAIT (attendre 30-120 secondes)"
        Write-Host "  - Processus non tue correctement"
        Write-Host "  - Privileges administrateur requis"
    } else {
        Write-Host ""
        Write-Host "[OK] Port 5000 libere!" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] Port 5000 libre!" -ForegroundColor Green
}

# Port 5001 (V3)
Write-Host ""
Write-Host "[INFO] Verification du port 5001 (V3)..."
$port5001 = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue

if ($port5001) {
    Write-Host "[ATTENTION] Le port 5001 est encore occupe:" -ForegroundColor Yellow
    $port5001 | ForEach-Object {
        Write-Host "  Etat: $($_.State) | PID: $($_.OwningProcess)"
    }

    Write-Host ""
    Write-Host "[ACTION] Tentative de liberation forcee du port 5001..."

    foreach ($conn in $port5001) {
        $pid = $conn.OwningProcess
        try {
            Write-Host "  Arret PID $pid sur port 5001..."
            Stop-Process -Id $pid -Force -ErrorAction Stop
            Write-Host "  [OK] PID $pid arrete"
        } catch {
            Write-Host "  [ERREUR] Impossible d'arreter PID $pid : $_" -ForegroundColor Red
        }
    }

    Start-Sleep -Seconds 2

    # Verification finale
    $port5001Final = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue

    if ($port5001Final) {
        Write-Host ""
        Write-Host "[ERREUR] Le port 5001 est ENCORE occupe!" -ForegroundColor Red
        Write-Host "[DIAGNOSTIC] Raisons possibles:" -ForegroundColor Yellow
        Write-Host "  - Etat TIME_WAIT (attendre 30-120 secondes)"
        Write-Host "  - Processus non tue correctement"
        Write-Host "  - Privileges administrateur requis"
    } else {
        Write-Host ""
        Write-Host "[OK] Port 5001 libere!" -ForegroundColor Green
    }
} else {
    Write-Host "[OK] Port 5001 libre!" -ForegroundColor Green
}

# RESUME FINAL
Write-Host ""
Write-Host "========================================"
Write-Host " RESUME"
Write-Host "========================================"
Write-Host ""
Write-Host "Processus Python avant: $countBefore"
Write-Host "Processus Python apres: $countAfter"
Write-Host ""

if ($countAfter -eq 0) {
    Write-Host "[SUCCESS] Arret complet reussi!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "[ERREUR] Arret incomplet - $countAfter processus restants" -ForegroundColor Red
    Write-Host ""
    Write-Host "[INSTRUCTIONS] Pour arreter manuellement:"
    Write-Host "1. Ouvrez le Gestionnaire des taches (Ctrl+Shift+Esc)"
    Write-Host "2. Onglet Details"
    Write-Host "3. Cherchez python.exe"
    Write-Host "4. Clic droit > Terminer le processus"
    exit 1
}
