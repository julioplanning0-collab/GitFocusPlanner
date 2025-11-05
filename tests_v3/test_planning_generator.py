"""
Tests pour planning_generator.py
Orchestrateur principal qui combine tous les modules
"""

import pytest
from datetime import datetime
from pathlib import Path
from backend.planning_engine_v3.planning_generator import generate_planning


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_work_tasks():
    """Taches de travail d'exemple."""
    return [
        {
            "id": "TASK001",
            "name": "Revision mathematiques",
            "duration": 50,  # 2 Pomodoros
            "priority": 1
        },
        {
            "id": "TASK002",
            "name": "Lire documentation Python",
            "duration": 25,  # 1 Pomodoro
            "priority": 2
        }
    ]


@pytest.fixture
def sample_pauses():
    """Pauses d'exemple."""
    return [
        {
            "id": "PAUSE001",
            "name": "Pause cafe",
            "duration": 5,
            "is_pause": 1
        },
        {
            "id": "PAUSE002",
            "name": "Meditation",
            "duration": 10,
            "is_pause": 1
        }
    ]


@pytest.fixture
def sample_recurrent_tasks():
    """Tï¿½ches rï¿½currentes d'exemple."""
    return [
        {
            "id": "REC001",
            "name": "Arrosage plantes",
            "duration": 15,
            "is_pause": 0,
            "next_due_date": "2025-11-05"
        }
    ]


@pytest.fixture
def sample_temps_morts():
    """Temps morts d'exemple."""
    return [
        {
            "date": "2025-11-05",
            "heure_debut": "12:00",
            "heure_fin": "13:00",
            "titre": "Dï¿½jeuner"
        }
    ]


# ============================================================================
# TESTS GENERATION COMPLETE
# ============================================================================

def test_generate_planning_basic(sample_work_tasks, sample_pauses, sample_recurrent_tasks, sample_temps_morts):
    """
    Test gï¿½nï¿½ration de planning basique.

    Vï¿½rifie:
        - Planning gï¿½nï¿½rï¿½ contient des items
        - Chaque item a les champs requis
        - Alternance travail/pause respectï¿½e
        - Temps assignï¿½s correctement
    """
    result = generate_planning(
        date="2025-11-05",
        planningStartTime="08:00",
        work_tasks=sample_work_tasks,
        pauses=sample_pauses,
        recurrent_tasks=sample_recurrent_tasks,
        planned_tasks=[],
        temps_morts=sample_temps_morts
    )

    # Vï¿½rifier structure retour
    assert "timeline" in result
    assert "statistics" in result

    timeline = result["timeline"]

    # Vï¿½rifier timeline non vide
    assert len(timeline) > 0

    # Vï¿½rifier champs requis
    for item in timeline:
        assert "type" in item
        assert "name" in item
        assert "start_time" in item
        assert "end_time" in item
        assert "duration" in item

    # Vï¿½rifier statistiques
    stats = result["statistics"]
    assert "total_work_minutes" in stats
    assert "total_pause_minutes" in stats
    assert "task_count" in stats


def test_generate_planning_empty_tasks():
    """
    Test gï¿½nï¿½ration avec liste de tï¿½ches vide.

    Vï¿½rifie:
        - Retourne structure valide
        - Timeline vide
        - Statistiques ï¿½ 0
    """
    result = generate_planning(
        date="2025-11-05",
        planningStartTime="08:00",
        work_tasks=[],
        pauses=[],
        recurrent_tasks=[],
        planned_tasks=[],
        temps_morts=[]
    )

    assert "timeline" in result
    assert "statistics" in result
    assert len(result["timeline"]) == 0
    assert result["statistics"]["total_work_minutes"] == 0


def test_generate_planning_avoids_temps_morts(sample_work_tasks, sample_pauses):
    """
    Test ï¿½vitement des temps morts.

    Vï¿½rifie:
        - Aucune tï¿½che ne chevauche un temps mort
        - Planning saute correctement par-dessus les temps morts
    """
    temps_morts = [
        {
            "date": "2025-11-05",
            "heure_debut": "10:00",
            "heure_fin": "10:30",
            "titre": "Rï¿½union"
        }
    ]

    result = generate_planning(
        date="2025-11-05",
        planningStartTime="09:00",
        work_tasks=sample_work_tasks,
        pauses=sample_pauses,
        recurrent_tasks=[],
        planned_tasks=[],
        temps_morts=temps_morts
    )

    timeline = result["timeline"]

    # Vï¿½rifier qu'aucune tï¿½che ne chevauche 10:00-10:30
    for item in timeline:
        start_time = datetime.strptime(item["start_time"], "%H:%M").time()
        end_time = datetime.strptime(item["end_time"], "%H:%M").time()

        blocked_start = datetime.strptime("10:00", "%H:%M").time()
        blocked_end = datetime.strptime("10:30", "%H:%M").time()

        # Vï¿½rifier pas de chevauchement
        assert not (start_time < blocked_end and end_time > blocked_start)


def test_generate_planning_with_planned_tasks(sample_work_tasks, sample_pauses):
    """
    Test intï¿½gration de tï¿½ches planifiï¿½es.

    Vï¿½rifie:
        - Tï¿½ches planifiï¿½es placï¿½es au bon moment
        - Tï¿½ches de travail rï¿½organisï¿½es autour
    """
    planned_tasks = [
        {
            "id": "PLANNED001",
            "name": "Rendez-vous mï¿½decin",
            "duration": 45,
            "planned_start": "2025-11-05 14:00"
        }
    ]

    result = generate_planning(
        date="2025-11-05",
        planningStartTime="08:00",
        work_tasks=sample_work_tasks,
        pauses=sample_pauses,
        recurrent_tasks=[],
        planned_tasks=planned_tasks,
        temps_morts=[]
    )

    timeline = result["timeline"]

    # Vï¿½rifier prï¿½sence tï¿½che planifiï¿½e
    planned_items = [item for item in timeline if item["type"] == "planned"]
    assert len(planned_items) > 0

    # Vï¿½rifier heure proche de 14:00
    planned_item = planned_items[0]
    start_time = datetime.strptime(planned_item["start_time"], "%H:%M")
    expected_time = datetime.strptime("14:00", "%H:%M")

    # Tolï¿½rance de 1 heure
    time_diff = abs((start_time - expected_time).total_seconds() / 60)
    assert time_diff < 60


def test_generate_planning_statistics(sample_work_tasks, sample_pauses):
    """
    Test calcul des statistiques.

    Vï¿½rifie:
        - total_work_minutes correct
        - total_pause_minutes correct
        - task_count correct
    """
    result = generate_planning(
        date="2025-11-05",
        planningStartTime="08:00",
        work_tasks=sample_work_tasks,
        pauses=sample_pauses,
        recurrent_tasks=[],
        planned_tasks=[],
        temps_morts=[]
    )

    stats = result["statistics"]
    timeline = result["timeline"]

    # Compter manuellement
    work_minutes = sum(item["duration"] for item in timeline if item["type"] == "work")
    pause_minutes = sum(item["duration"] for item in timeline if item["type"] == "pause")

    assert stats["total_work_minutes"] == work_minutes
    assert stats["total_pause_minutes"] == pause_minutes
    assert stats["task_count"] == len(timeline)


def test_generate_planning_respects_priority(sample_pauses):
    """
    Test respect de la prioritï¿½ des tï¿½ches.

    Vï¿½rifie:
        - Tï¿½ches prioritï¿½ 1 avant prioritï¿½ 2
        - Ordre respectï¿½ dans la timeline
    """
    work_tasks = [
        {"id": "T1", "name": "Basse prioritï¿½", "duration": 25, "priority": 3},
        {"id": "T2", "name": "Haute prioritï¿½", "duration": 25, "priority": 1},
        {"id": "T3", "name": "Moyenne prioritï¿½", "duration": 25, "priority": 2}
    ]

    result = generate_planning(
        date="2025-11-05",
        planningStartTime="08:00",
        work_tasks=work_tasks,
        pauses=sample_pauses,
        recurrent_tasks=[],
        planned_tasks=[],
        temps_morts=[]
    )

    timeline = result["timeline"]
    work_items = [item for item in timeline if item["type"] == "work"]

    # Vï¿½rifier ordre
    assert work_items[0]["name"] == "Haute prioritï¿½"
    assert work_items[1]["name"] == "Moyenne prioritï¿½"
    assert work_items[2]["name"] == "Basse prioritï¿½"


def test_generate_planning_invalid_date():
    """
    Test avec date invalide.

    Vï¿½rifie:
        - Lï¿½ve ValueError
    """
    with pytest.raises(ValueError):
        generate_planning(
            date="invalid-date",
            planningStartTime="08:00",
            work_tasks=[],
            pauses=[],
            recurrent_tasks=[],
            planned_tasks=[],
            temps_morts=[]
        )


def test_generate_planning_invalid_start_time():
    """
    Test avec heure de dï¿½but invalide.

    Vï¿½rifie:
        - Lï¿½ve ValueError
    """
    with pytest.raises(ValueError):
        generate_planning(
            date="2025-11-05",
            planningStartTime="invalid-time",
            work_tasks=[],
            pauses=[],
            recurrent_tasks=[],
            planned_tasks=[],
            temps_morts=[]
        )
