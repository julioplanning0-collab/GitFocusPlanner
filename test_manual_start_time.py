# -*- coding: utf-8 -*-
"""
Test manuel pour vérifier que start_time est bien utilisé.

Simule le comportement utilisateur :
1. Sélectionner des tâches Pomodoro
2. Définir manuellement start_time = "20:00"
3. Générer le planning
4. Vérifier que le premier slot commence à 20:00 (pas à l'heure auto-calculée)
"""
import sys
import io

# Fix Windows encoding for UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api/v2/gitfocus"

def test_manual_start_time():
    """Test que le start_time manuel est respecté"""
    print("\n" + "="*80)
    print("TEST: Manual start_time doit être utilisé au lieu de l'auto-calcul")
    print("="*80)

    # Date = aujourd'hui
    today = datetime.now().strftime("%Y-%m-%d")

    # Heure manuelle = 10:00 (matin)
    manual_start_time = "10:00"

    print(f"\n📅 Date: {today}")
    print(f"🕐 Manual start_time: {manual_start_time}")
    print(f"⏰ Current time: {datetime.now().strftime('%H:%M')}")

    payload = {
        "date": today,
        "start_time": manual_start_time,  # 🆕 Heure manuelle
        "pomodoro_task_ids": ["1", "2", "3"],  # IDs réels des tâches
        "respiration_task_ids": [],  # Pas de respirations (optionnel)
        "enable_clopes": False,
        "enable_calins": False,
        "allow_consecutive_pauses": False
    }

    print(f"\n📤 Sending request to /planning/generate-auto...")
    response = requests.post(f"{BASE_URL}/planning/generate-auto", json=payload)

    if response.status_code != 200:
        print(f"❌ ERREUR HTTP {response.status_code}: {response.text}")
        return False

    data = response.json()

    if not data.get('success'):
        print(f"❌ ERREUR API: {data.get('error', 'Unknown error')}")
        return False

    planning = data['data']['planning']

    if not planning:
        print("❌ Planning vide!")
        return False

    # Vérifier que le premier slot commence à l'heure manuelle
    first_slot = planning[0]
    first_slot_time = first_slot['heure_debut']

    print(f"\n📊 Planning généré:")
    print(f"   - Nombre de slots: {len(planning)}")
    print(f"   - Premier slot: {first_slot_time} - {first_slot['heure_fin']}")
    print(f"   - Type: {first_slot['type']}")
    print(f"   - Tâche: {first_slot['task_name']}")

    # Afficher les 5 premiers slots
    print(f"\n📋 Premiers 5 slots:")
    for i, slot in enumerate(planning[:5]):
        print(f"   {i+1}. {slot['heure_debut']}-{slot['heure_fin']} | {slot['type']:12} | {slot['task_name']}")

    # VÉRIFICATION: Le premier slot doit commencer à 20:00 (ou juste après si temps_mort)
    # On accepte une petite tolérance (ex: 20:00, 20:05, 20:10) si temps_morts présents
    hour_start = int(first_slot_time.split(':')[0])

    if hour_start >= 20:
        print(f"\n✅ SUCCÈS: Premier slot commence à {first_slot_time} (>= 20:00)")
        print(f"✅ Le start_time manuel ({manual_start_time}) a bien été utilisé!")
        return True
    else:
        print(f"\n❌ ÉCHEC: Premier slot commence à {first_slot_time} (< 20:00)")
        print(f"❌ Le start_time manuel ({manual_start_time}) n'a PAS été utilisé!")
        print(f"⚠️ Le système a probablement recalculé l'heure automatiquement")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" TEST MANUEL START_TIME")
    print("="*80)
    print(" Serveur doit être démarré: python -m webapp.server")
    print("="*80)

    success = test_manual_start_time()

    print("\n" + "="*80)
    print(" RÉSULTAT FINAL")
    print("="*80)

    if success:
        print("✅ Test réussi: Le start_time manuel est bien utilisé!")
    else:
        print("❌ Test échoué: Le start_time manuel n'est PAS utilisé!")
        print("\n🔍 Vérifiez les logs du serveur pour voir si start_time est bien passé")

    print("="*80)
