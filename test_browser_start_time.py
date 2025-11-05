# -*- coding: utf-8 -*-
"""
Test avec Selenium pour simuler le comportement utilisateur exact.

Scénario:
1. Charger la page
2. Changer l'heure à 10:00
3. Cliquer sur "Rafraîchir"
4. Vérifier que le planning commence à 10:00 (ou après si temps_mort)
"""
import sys
import io

# Fix Windows encoding for UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def test_manual_start_time_browser():
    """Test le start_time manuel via Selenium"""

    print("\n" + "="*80)
    print("TEST SELENIUM: Manual start_time avec interface web")
    print("="*80)

    # Configuration Chrome headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    driver = None

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)

        # Étape 1: Charger la page
        print("\n📄 Chargement de la page...")
        url = "http://julioplanning0.duckdns.org:5000/api/v2/gitfocus/interface"
        print(f"   URL: {url}")
        driver.get(url)

        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "planning-start-time"))
        )
        time.sleep(2)  # Attendre que le JavaScript s'initialise

        # Vérifier la valeur initiale du start_time
        time_input = driver.find_element(By.ID, "planning-start-time")
        initial_time = time_input.get_attribute('value')
        print(f"⏰ Heure initiale (auto-calculée): {initial_time}")

        # Lire state.planningStartTime via JavaScript
        initial_state_time = driver.execute_script("return state.planningStartTime")
        print(f"📊 state.planningStartTime initial: {initial_state_time}")

        # Étape 2: Changer l'heure à 10:00
        print(f"\n🔧 Changement de l'heure à 10:00...")
        driver.execute_script("""
            document.getElementById('planning-start-time').value = '10:00';
            document.getElementById('planning-start-time').dispatchEvent(new Event('change'));
        """)
        time.sleep(0.5)

        # Vérifier que l'input a bien été changé
        new_time = time_input.get_attribute('value')
        print(f"✅ Heure dans l'input après changement: {new_time}")

        # Vérifier state.planningStartTime
        state_time_after_change = driver.execute_script("return state.planningStartTime")
        print(f"📊 state.planningStartTime après changement: {state_time_after_change}")

        # Étape 3: Sélectionner quelques tâches Pomodoro
        print(f"\n📋 Sélection de tâches Pomodoro...")
        driver.execute_script("""
            // Sélectionner les 3 premières tâches
            state.selectedPomodoroIds = ['1', '2', '3'];
        """)

        # Étape 4: Cliquer sur "Générer Planning"
        print(f"\n⚡ Click sur 'Générer Planning'...")
        generate_btn = driver.find_element(By.ID, "btn-generate")
        generate_btn.click()

        # Attendre que le planning soit généré
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "planning-slot"))
        )
        time.sleep(1)

        # Vérifier le premier slot
        first_slot = driver.find_element(By.CLASS_NAME, "planning-slot")
        slot_time_elem = first_slot.find_element(By.CLASS_NAME, "slot-time")
        slot_time_text = slot_time_elem.text  # Format: "HH:MM - HH:MM"

        print(f"\n📊 Premier slot du planning: {slot_time_text}")

        # Extraire l'heure de début
        first_slot_start = slot_time_text.split(' - ')[0].strip()
        first_slot_hour = int(first_slot_start.split(':')[0])

        print(f"🕐 Heure de début du premier slot: {first_slot_start}")

        # Étape 5: Vérifier state.planningStartTime avant de cliquer sur Rafraîchir
        state_time_before_refresh = driver.execute_script("return state.planningStartTime")
        print(f"\n📊 state.planningStartTime avant rafraîchir: {state_time_before_refresh}")

        # Étape 6: Cliquer sur "Rafraîchir"
        print(f"\n🔄 Click sur 'Rafraîchir'...")
        refresh_btn = driver.find_element(By.ID, "btn-refresh")
        refresh_btn.click()

        # Attendre que le planning soit régénéré
        time.sleep(3)

        # Vérifier state.planningStartTime après rafraîchir
        state_time_after_refresh = driver.execute_script("return state.planningStartTime")
        print(f"📊 state.planningStartTime après rafraîchir: {state_time_after_refresh}")

        # Vérifier l'input time après rafraîchir
        time_after_refresh = time_input.get_attribute('value')
        print(f"⏰ Heure dans l'input après rafraîchir: {time_after_refresh}")

        # Vérifier le nouveau premier slot
        first_slot_after_refresh = driver.find_element(By.CLASS_NAME, "planning-slot")
        slot_time_after_refresh = first_slot_after_refresh.find_element(By.CLASS_NAME, "slot-time").text
        first_slot_start_after_refresh = slot_time_after_refresh.split(' - ')[0].strip()

        print(f"📊 Premier slot après rafraîchir: {slot_time_after_refresh}")
        print(f"🕐 Heure de début après rafraîchir: {first_slot_start_after_refresh}")

        # VÉRIFICATION
        print(f"\n" + "="*80)
        print("ANALYSE DU PROBLÈME")
        print("="*80)

        if state_time_after_refresh != "10:00":
            print(f"❌ PROBLÈME IDENTIFIÉ: state.planningStartTime a changé!")
            print(f"   Attendu: 10:00")
            print(f"   Obtenu: {state_time_after_refresh}")
            print(f"\n💡 Le problème est dans le JavaScript qui recalcule automatiquement l'heure")
            return False
        else:
            print(f"✅ state.planningStartTime est correct: {state_time_after_refresh}")

            if first_slot_start_after_refresh.startswith("10:") or int(first_slot_start_after_refresh.split(':')[0]) >= 10:
                print(f"✅ Le planning commence bien à ou après 10:00")
                return True
            else:
                print(f"❌ Le planning ne commence PAS à 10:00")
                print(f"   Premier slot: {first_slot_start_after_refresh}")
                return False

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    print("\n" + "="*80)
    print(" TEST SELENIUM - MANUAL START TIME")
    print("="*80)
    print(" Serveur doit être démarré: python -m webapp.server")
    print("="*80)

    success = test_manual_start_time_browser()

    print("\n" + "="*80)
    print(" RÉSULTAT FINAL")
    print("="*80)

    if success:
        print("✅ Test réussi: Le start_time manuel fonctionne correctement!")
    else:
        print("❌ Test échoué: Le start_time manuel ne fonctionne PAS!")

    print("="*80)
