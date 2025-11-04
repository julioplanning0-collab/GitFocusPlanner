"""
Tests API simples pour la refonte du planning (sans Selenium).

Tests rapides pour validation API avant et après refonte.

Exécution:
    pytest test_api_refonte.py -v
"""

import pytest
import requests
from pathlib import Path


BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api/v2/gitfocus"
HEALTH_URL = f"{BASE_URL}/health"


@pytest.fixture(scope="module")
def check_server():
    """Vérifie que le serveur est démarré."""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"\n✓ Server healthy (version: {data.get('version', 'unknown')})")
        return True
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Server not running. Start with: python -m webapp.server")


class TestAPIHealth:
    """Tests de santé de l'API."""

    def test_health_endpoint(self, check_server):
        """Test 1: Health endpoint répond correctement."""
        response = requests.get(HEALTH_URL)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        print(f"✓ Health OK (version: {data['version']})")


class TestAPIPomodoroTasks:
    """Tests des tâches Pomodoro."""

    def test_get_pomodoro_tasks(self, check_server):
        """Test 2: GET /tasks/pomodoro retourne des tâches."""
        response = requests.get(f"{API_BASE}/tasks/pomodoro")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

        print(f"✓ Pomodoro tasks OK ({len(data['tasks'])} tâches)")

    def test_pomodoro_task_structure(self, check_server):
        """Test 3: Les tâches Pomodoro ont la structure attendue."""
        response = requests.get(f"{API_BASE}/tasks/pomodoro")
        data = response.json()

        if len(data["tasks"]) > 0:
            task = data["tasks"][0]
            required_fields = ["id", "name", "duration_min"]

            for field in required_fields:
                assert field in task, f"Field '{field}' missing in task"

            print(f"✓ Task structure OK (fields: {list(task.keys())})")
        else:
            pytest.skip("No Pomodoro tasks to test structure")


class TestAPIRespirationTasks:
    """Tests des tâches de respiration."""

    def test_get_respiration_tasks(self, check_server):
        """Test 4: GET /tasks/respiration retourne des tâches."""
        response = requests.get(f"{API_BASE}/tasks/respiration")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

        print(f"✓ Respiration tasks OK ({len(data['tasks'])} tâches)")

    def test_respiration_sorted_by_popularity(self, check_server):
        """Test 5: Les tâches de respiration sont triées par popularité."""
        response = requests.get(f"{API_BASE}/tasks/respiration")
        data = response.json()

        if len(data["tasks"]) >= 2:
            # Vérifier que EXPORT_COUNT décroît
            counts = [t.get("export_count", 0) for t in data["tasks"]]

            # Au moins les premiers doivent être triés
            for i in range(len(counts) - 1):
                assert counts[i] >= counts[i+1], \
                    f"Tri incorrect: counts[{i}]={counts[i]} < counts[{i+1}]={counts[i+1]}"

            print(f"✓ Respiration sorted by popularity (counts: {counts[:5]}...)")
        else:
            pytest.skip("Not enough respiration tasks to test sorting")


class TestAPIRecurrentTasks:
    """Tests des tâches récurrentes."""

    def test_get_recurrent_tasks(self, check_server):
        """Test 6: GET /tasks/recurrent retourne des tâches."""
        response = requests.get(f"{API_BASE}/tasks/recurrent")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

        print(f"✓ Recurrent tasks OK ({len(data['tasks'])} tâches)")

    def test_get_recurrent_tasks_active_only(self, check_server):
        """Test 7: GET /tasks/recurrent?active_only=true filtre correctement."""
        response = requests.get(f"{API_BASE}/tasks/recurrent?active_only=true")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Toutes les tâches doivent être actives
        for task in data["tasks"]:
            assert task.get("is_active") == 1, \
                f"Task {task.get('id')} not active but returned in active_only=true"

        print(f"✓ Active recurrent tasks filter OK ({len(data['tasks'])} actives)")


class TestAPIDataFiles:
    """Tests de présence des fichiers de données."""

    def test_liste_mere_exists(self):
        """Test 8: Le fichier LISTE_MERE.v2.csv existe."""
        path1 = Path("C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data/LISTE_MERE.v2.csv")
        path2 = Path("prod_data/LISTE_MERE.v2.csv")

        assert path1.exists() or path2.exists(), "LISTE_MERE.v2.csv not found"
        print(f"✓ LISTE_MERE.v2.csv exists")

    def test_temps_morts_exists(self):
        """Test 9: Le fichier temps_morts.csv existe."""
        path1 = Path("C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data/temps_morts.csv")
        path2 = Path("prod_data/temps_morts.csv")

        assert path1.exists() or path2.exists(), "temps_morts.csv not found"
        print(f"✓ temps_morts.csv exists")

    def test_respiration_tasks_exists(self):
        """Test 10: Le fichier TACHES_RESPIRATOIRES.v2.csv existe."""
        path1 = Path("C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data/TACHES_RESPIRATOIRES.v2.csv")
        path2 = Path("prod_data/TACHES_RESPIRATOIRES.v2.csv")

        assert path1.exists() or path2.exists(), "TACHES_RESPIRATOIRES.v2.csv not found"
        print(f"✓ TACHES_RESPIRATOIRES.v2.csv exists")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
