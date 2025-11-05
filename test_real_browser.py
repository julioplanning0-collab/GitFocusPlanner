# -*- coding: utf-8 -*-
"""
Test avec navigateur VISIBLE pour voir exactement ce qui se passe
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

def test_real_page():
    """Test avec navigateur visible"""

    print("\n" + "="*80)
    print("TEST AVEC NAVIGATEUR VISIBLE")
    print("="*80)

    # Configuration Chrome VISIBLE (pas headless)
    chrome_options = Options()
    # Ne pas mettre --headless pour voir le navigateur

    driver = None

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)

        print("\n📄 Chargement de la page...")
        url = "http://julioplanning0.duckdns.org:5000/api/v2/gitfocus/interface"
        driver.get(url)

        # Attendre que la page soit chargée
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "planning-start-time"))
        )
        time.sleep(2)

        # Lire les valeurs initiales
        time_input = driver.find_element(By.ID, "planning-start-time")
        initial_time = time_input.get_attribute('value')
        print(f"⏰ Heure initiale: {initial_time}")

        # Changer à 10:00
        print(f"\n🔧 Changement à 10:00...")
        driver.execute_script("""
            document.getElementById('planning-start-time').value = '10:00';
            document.getElementById('planning-start-time').dispatchEvent(new Event('change'));
        """)
        time.sleep(1)

        # Vérifier state.planningStartTime
        state_time = driver.execute_script("return state.planningStartTime")
        print(f"📊 state.planningStartTime: {state_time}")

        # Vérifier combien de tâches Pomodoro sont sélectionnées
        selected_count = driver.execute_script("return state.selectedPomodoroIds.length")
        print(f"📋 Tâches Pomodoro sélectionnées: {selected_count}")

        if selected_count == 0:
            print(f"\n⚠️ Aucune tâche sélectionnée, je vais en sélectionner 3...")
            driver.execute_script("""
                state.selectedPomodoroIds = ['1', '2', '3'];
            """)

        # Cliquer sur "Générer Planning"
        print(f"\n⚡ Click sur 'Générer Planning'...")
        generate_btn = driver.find_element(By.ID, "btn-generate")
        generate_btn.click()

        # Attendre que le planning soit généré
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "planning-slot"))
        )
        time.sleep(2)

        # Compter tous les slots
        all_slots = driver.find_elements(By.CLASS_NAME, "planning-slot")
        print(f"\n📊 Planning généré: {len(all_slots)} slots")

        # Afficher les 10 premiers slots
        print(f"\n📋 Premiers 10 slots:")
        for i in range(min(10, len(all_slots))):
            slot = all_slots[i]
            time_text = slot.find_element(By.CLASS_NAME, "slot-time").text
            name_text = slot.find_element(By.CLASS_NAME, "slot-name").text
            print(f"   {i+1}. {time_text} | {name_text}")

        # Extraire l'heure du premier slot
        first_slot_time = all_slots[0].find_element(By.CLASS_NAME, "slot-time").text
        first_hour = first_slot_time.split(':')[0].strip()
        # Enlever l'emoji s'il y en a
        if '🔴' in first_hour or '🟢' in first_hour or '🟣' in first_hour:
            first_hour = first_hour.replace('🔴', '').replace('🟢', '').replace('🟣', '').strip()

        print(f"\n🔍 Premier slot commence à: {first_slot_time}")
        print(f"🔍 Heure attendue: >= 10:00")

        # Garder le navigateur ouvert pour inspection
        print(f"\n⏸️  Navigateur reste ouvert pour inspection...")
        print(f"   Appuyez sur Entrée pour fermer...")
        input()

        return True

    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

        # Garder le navigateur ouvert en cas d'erreur
        if driver:
            print(f"\n⏸️  Navigateur reste ouvert pour debug...")
            print(f"   Appuyez sur Entrée pour fermer...")
            input()

        return False

    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    test_real_page()
