#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitFocus Planner V2 - Verification Script
Quick health check and system verification
"""

import requests
import sys
import io
from pathlib import Path

# Force UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

BASE_URL = "http://localhost:5000"

def check_endpoint(name: str, url: str) -> bool:
    """Check if endpoint is accessible and returns success"""
    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        if response.status_code == 200:
            print(f"✅ {name}: OK")
            return True
        else:
            print(f"❌ {name}: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ {name}: {str(e)}")
        return False

def verify_files() -> bool:
    """Verify required CSV files exist"""
    data_dir = Path(__file__).parent.parent / "prod_data"

    required_files = [
        "LISTE_MERE.v2.csv",
        "TACHES_RECURRENTES.v2.csv",
        "TACHES_RESPIRATOIRES.v2.csv",
        "TACHES_PLANIFIEES.v2.csv",
        "temps_morts.csv",
        "categories.csv",
        "done_v2.csv"
    ]

    all_exist = True
    print("\n📁 Fichiers CSV requis:")
    for filename in required_files:
        filepath = data_dir / filename
        if filepath.exists():
            print(f"  ✅ {filename}")
        else:
            print(f"  ❌ {filename} - MANQUANT")
            all_exist = False

    return all_exist

def main():
    print("=" * 60)
    print(" GitFocus Planner V2 - Vérification Système")
    print("=" * 60)
    print()

    # Check files (pre-startup verification)
    files_ok = verify_files()

    # Check API endpoints only if --full flag is passed
    check_api = "--full" in sys.argv

    if check_api:
        print("\n🌐 Endpoints API:")

        # Check health
        health_ok = check_endpoint("Health Check", f"{BASE_URL}/health")

        # Check data endpoints
        pomodoro_ok = check_endpoint("Tâches Pomodoro", f"{BASE_URL}/api/v2/gitfocus/tasks/pomodoro")
        recurrent_ok = check_endpoint("Tâches Récurrentes", f"{BASE_URL}/api/v2/gitfocus/tasks/recurrent")
        respiration_ok = check_endpoint("Tâches Respiratoires", f"{BASE_URL}/api/v2/gitfocus/tasks/respiration")
    else:
        # Skip API checks if server not started yet
        health_ok = True
        pomodoro_ok = True
        recurrent_ok = True
        respiration_ok = True

    # Summary
    print()
    print("=" * 60)

    all_ok = files_ok and health_ok and pomodoro_ok and recurrent_ok and respiration_ok

    if all_ok:
        print("✅ SYSTÈME PRÊT" if not check_api else "✅ SYSTÈME OPÉRATIONNEL")
        print()
        if check_api:
            print("🌐 Interface Web:")
            print(f"   {BASE_URL}/api/v2/gitfocus/interface")
            print()
        return 0
    else:
        print("❌ PROBLÈMES DÉTECTÉS")
        print()
        print("Vérifiez que:")
        if not check_api:
            print("1. Les fichiers CSV existent dans prod_data/")
        else:
            print("1. Le serveur est démarré: python -m webapp.server")
            print("2. Les fichiers CSV existent dans prod_data/")
            print("3. Le port 5000 n'est pas occupé")
        return 1

if __name__ == "__main__":
    sys.exit(main())
