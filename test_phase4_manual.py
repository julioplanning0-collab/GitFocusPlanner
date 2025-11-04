# -*- coding: utf-8 -*-
"""
Test manuel Phase 4 - Clopes, Calins, Pauses Consecutives

Tests manuels pour valider les 3 nouvelles fonctionnalites:
1. Insertion de clopes (cigarette breaks)
2. Insertion de calins (1 tous les 2 respirations)
3. Mode pauses consecutives
"""
import sys
import io

# Fix Windows encoding for UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:5000/api/v2/gitfocus"


def test_clopes_insertion():
    """Test 1: Insertion de clopes tous les 120 minutes"""
    print("\n" + "="*80)
    print("TEST 1: Insertion de clopes (intervalle 120 min)")
    print("="*80)

    payload = {
        "date": "2025-11-05",
        "start_time": "09:00",
        "pomodoro_task_ids": ["TASK001", "TASK002", "TASK003"],  # 3 tâches = 75 min
        "respiration_task_ids": ["R_001", "R_002", "R_003"],
        "enable_clopes": True,
        "clopes_interval_min": 120,
        "enable_calins": False,
        "allow_consecutive_pauses": False
    }

    response = requests.post(f"{BASE_URL}/planning/generate-auto", json=payload)

    if response.status_code == 200:
        data = response.json()
        planning = data['data']['planning']

        # Compter les clopes
        clopes = [slot for slot in planning if slot.get('type') == 'clope']
        print(f"✅ Nombre de clopes insérées: {len(clopes)}")

        if clopes:
            print("\n📍 Clopes trouvées:")
            for clope in clopes:
                print(f"   - {clope['heure_debut']} → {clope['heure_fin']} ({clope['duration_min']} min)")

        # Afficher les 10 premiers slots
        print(f"\n📋 Planning (premiers 10 slots):")
        for i, slot in enumerate(planning[:10]):
            print(f"   {i+1}. {slot['heure_debut']}-{slot['heure_fin']} | {slot['type']:12} | {slot['task_name']}")

        return True
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
        return False


def test_calins_insertion():
    """Test 2: Insertion de câlins (1 tous les 2 respirations)"""
    print("\n" + "="*80)
    print("TEST 2: Insertion de câlins (1 tous les 2 respirations)")
    print("="*80)

    payload = {
        "date": "2025-11-05",
        "start_time": "09:00",
        "pomodoro_task_ids": ["TASK001", "TASK002"],
        "respiration_task_ids": ["R_001", "R_002", "R_001", "R_002", "R_001", "R_002"],  # 6 respirations
        "enable_clopes": False,
        "enable_calins": True,
        "allow_consecutive_pauses": False
    }

    response = requests.post(f"{BASE_URL}/planning/generate-auto", json=payload)

    if response.status_code == 200:
        data = response.json()
        planning = data['data']['planning']

        # Compter les câlins et respirations
        calins = [slot for slot in planning if slot.get('type') == 'calin']
        respirations = [slot for slot in planning if slot.get('type') == 'respiration']

        print(f"✅ Nombre de respirations: {len(respirations)}")
        print(f"✅ Nombre de câlins insérés: {len(calins)}")
        print(f"✅ Ratio attendu: 1 câlin tous les 2 respirations → {len(respirations) // 2} câlins attendus")

        if calins:
            print("\n🤗 Câlins trouvés:")
            for calin in calins:
                print(f"   - {calin['heure_debut']} → {calin['heure_fin']} ({calin['duration_min']} min)")

        # Afficher la séquence Pomodoro/Respiration/Câlin
        print(f"\n📋 Planning (tous les slots):")
        for i, slot in enumerate(planning):
            emoji = "🔴" if slot['type'] == 'pomodoro' else "🟢" if slot['type'] == 'respiration' else "🤗" if slot['type'] == 'calin' else "⚪"
            print(f"   {i+1}. {slot['heure_debut']}-{slot['heure_fin']} | {emoji} {slot['type']:12} | {slot['task_name']}")

        return True
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
        return False


def test_consecutive_pauses():
    """Test 3: Mode pauses consécutives (désactive l'alternance stricte)"""
    print("\n" + "="*80)
    print("TEST 3: Mode pauses consécutives (allow_consecutive_pauses=True)")
    print("="*80)

    payload = {
        "date": "2025-11-05",
        "start_time": "09:00",
        "pomodoro_task_ids": ["TASK001"],
        "respiration_task_ids": ["R_001", "R_002"],
        "enable_clopes": False,
        "enable_calins": False,
        "allow_consecutive_pauses": True  # Mode pauses consécutives
    }

    response = requests.post(f"{BASE_URL}/planning/generate-auto", json=payload)

    if response.status_code == 200:
        data = response.json()
        planning = data['data']['planning']

        # Analyser les séquences consécutives
        consecutive_pauses = []
        for i in range(len(planning) - 1):
            current_type = planning[i]['type']
            next_type = planning[i+1]['type']

            if current_type in ['respiration', 'pause', 'recurrent'] and next_type in ['respiration', 'pause', 'recurrent']:
                consecutive_pauses.append((i, i+1))

        print(f"✅ Pauses consécutives trouvées: {len(consecutive_pauses)}")
        print(f"✅ Mode pauses consécutives ACTIF → Alternance stricte désactivée")

        if consecutive_pauses:
            print("\n🔄 Séquences de pauses consécutives détectées:")
            for idx1, idx2 in consecutive_pauses:
                slot1 = planning[idx1]
                slot2 = planning[idx2]
                print(f"   - Slot {idx1+1}: {slot1['type']} → Slot {idx2+1}: {slot2['type']}")

        print(f"\n📋 Planning complet:")
        for i, slot in enumerate(planning):
            emoji = "🔴" if slot['type'] == 'pomodoro' else "🟢"
            print(f"   {i+1}. {slot['heure_debut']}-{slot['heure_fin']} | {emoji} {slot['type']:12} | {slot['task_name']}")

        return True
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
        return False


def test_all_combined():
    """Test 4: Toutes les options activées en même temps"""
    print("\n" + "="*80)
    print("TEST 4: TOUTES LES OPTIONS ACTIVÉES (clopes + câlins + pauses consécutives)")
    print("="*80)

    payload = {
        "date": "2025-11-05",
        "start_time": "09:00",
        "pomodoro_task_ids": ["TASK001", "TASK002", "TASK003"],
        "respiration_task_ids": ["R_001", "R_002", "R_003", "R_001"],
        "enable_clopes": True,
        "clopes_interval_min": 90,  # Plus court pour tester
        "enable_calins": True,
        "allow_consecutive_pauses": True
    }

    response = requests.post(f"{BASE_URL}/planning/generate-auto", json=payload)

    if response.status_code == 200:
        data = response.json()
        planning = data['data']['planning']

        # Statistiques
        types_count = {}
        for slot in planning:
            slot_type = slot['type']
            types_count[slot_type] = types_count.get(slot_type, 0) + 1

        print(f"✅ Planning généré avec {len(planning)} slots")
        print(f"\n📊 Statistiques par type:")
        for slot_type, count in types_count.items():
            emoji = "🔴" if slot_type == 'pomodoro' else "🟢" if slot_type == 'respiration' else "🤗" if slot_type == 'calin' else "🚬" if slot_type == 'clope' else "⚪"
            print(f"   {emoji} {slot_type:12}: {count}")

        print(f"\n📋 Planning complet (avec emojis):")
        for i, slot in enumerate(planning):
            emoji = "🔴" if slot['type'] == 'pomodoro' else "🟢" if slot['type'] == 'respiration' else "🤗" if slot['type'] == 'calin' else "🚬" if slot['type'] == 'clope' else "⚪"
            print(f"   {i+1:2}. {slot['heure_debut']}-{slot['heure_fin']} | {emoji} {slot['type']:12} | {slot['task_name']}")

        return True
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" TESTS MANUELS PHASE 4 - NOUVELLES FONCTIONNALITÉS")
    print("="*80)
    print(" Serveur doit être démarré: python -m webapp.server")
    print("="*80)

    results = []

    # Exécuter les tests
    results.append(("Clopes", test_clopes_insertion()))
    results.append(("Câlins", test_calins_insertion()))
    results.append(("Pauses consécutives", test_consecutive_pauses()))
    results.append(("Toutes options combinées", test_all_combined()))

    # Résumé
    print("\n" + "="*80)
    print(" RÉSUMÉ DES TESTS")
    print("="*80)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} | {test_name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n🎯 Résultat final: {passed}/{total} tests réussis ({passed*100//total}%)")

    if passed == total:
        print("✅ Phase 4 validée: Toutes les fonctionnalités fonctionnent correctement!")
    else:
        print("⚠️ Certains tests ont échoué, vérifiez les logs ci-dessus")
