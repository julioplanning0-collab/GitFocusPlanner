"""Tests pour timeline_calculator.py"""

import pytest
from datetime import datetime
from backend.planning_engine_v3.timeline_calculator import (
    assign_times_to_sequence,
    convert_timeline_to_absolute_times,
    calculate_statistics,
    _has_collision_with_temps_morts,
    _find_next_free_time
)


def test_assign_times_to_sequence():
    """Test assignation temps a sequence simple"""
    sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5},
        {"type": "work", "task": {"id": "T002"}, "duration": 25}
    ]

    planningStartTime = "09:00"
    date = "2025-11-05"
    temps_morts = []

    timeline = assign_times_to_sequence(sequence, planningStartTime, date, temps_morts)

    # Verifier nombre d'items
    assert len(timeline) == 3

    # Verifier start_min et end_min
    assert timeline[0]["start_min"] == 0
    assert timeline[0]["end_min"] == 25
    assert timeline[1]["start_min"] == 25
    assert timeline[1]["end_min"] == 30
    assert timeline[2]["start_min"] == 30
    assert timeline[2]["end_min"] == 55


def test_assign_times_with_temps_morts():
    """Test assignation temps avec temps morts"""
    sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "work", "task": {"id": "T002"}, "duration": 25}
    ]

    planningStartTime = "09:00"
    date = "2025-11-05"
    temps_morts = [
        {"date": "2025-11-05", "heure_debut": "09:15", "heure_fin": "10:00", "titre": "Reunion"}
    ]

    timeline = assign_times_to_sequence(sequence, planningStartTime, date, temps_morts)

    # Verifier nombre d'items
    assert len(timeline) == 2

    # T001 (09:00-09:25) chevauche 09:15-10:00, donc doit etre place a 10:00
    # Verifier que T001 commence APRES le temps_mort (10:00 = 60 min apres 09:00)
    assert timeline[0]["start_min"] == 60
    assert timeline[0]["end_min"] == 85

    # Verifier que T002 suit T001
    assert timeline[1]["start_min"] == 85
    assert timeline[1]["end_min"] == 110


def test_convert_timeline_to_absolute_times():
    """Test conversion timeline en temps absolus"""
    timeline = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25, "start_min": 0, "end_min": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5, "start_min": 25, "end_min": 30}
    ]

    planningStartTime = "09:00"
    date = "2025-11-05"

    result = convert_timeline_to_absolute_times(timeline, planningStartTime, date)

    # Verifier nombre d'items
    assert len(result) == 2

    # Verifier temps absolus
    assert result[0]["heure_debut"] == "09:00"
    assert result[0]["heure_fin"] == "09:25"
    assert result[1]["heure_debut"] == "09:25"
    assert result[1]["heure_fin"] == "09:30"

    # Verifier que start_min/end_min sont conserves
    assert result[0]["start_min"] == 0
    assert result[0]["end_min"] == 25


def test_calculate_statistics():
    """Test calcul statistiques"""
    timeline = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5},
        {"type": "work", "task": {"id": "T002"}, "duration": 25},
        {"type": "recurrent", "task": {"id": "R001"}, "duration": 15},
        {"type": "planned", "task": {"id": "PL001"}, "duration": 30}
    ]

    stats = calculate_statistics(timeline)

    # Verifier durees
    assert stats["total_duration_min"] == 100
    assert stats["work_duration_min"] == 50
    assert stats["pause_duration_min"] == 5
    assert stats["recurrent_duration_min"] == 15
    assert stats["planned_duration_min"] == 30

    # Verifier compteurs
    assert stats["work_count"] == 2
    assert stats["pause_count"] == 1
    assert stats["recurrent_count"] == 1
    assert stats["planned_count"] == 1


def test_calculate_statistics_empty():
    """Test statistiques avec timeline vide"""
    timeline = []

    stats = calculate_statistics(timeline)

    # Tout doit etre a zero
    assert stats["total_duration_min"] == 0
    assert stats["work_count"] == 0


def test_has_collision_with_temps_morts_true():
    """Test detection collision avec temps_mort"""
    start_time = datetime(2025, 11, 5, 9, 30)
    duration = 25
    temps_morts = [
        {"date": "2025-11-05", "heure_debut": "09:15", "heure_fin": "10:00", "titre": "Reunion"}
    ]
    date = "2025-11-05"

    # 09:30 - 09:55 chevauche 09:15 - 10:00
    assert _has_collision_with_temps_morts(start_time, duration, temps_morts, date) is True


def test_has_collision_with_temps_morts_false():
    """Test detection pas de collision"""
    start_time = datetime(2025, 11, 5, 10, 0)
    duration = 25
    temps_morts = [
        {"date": "2025-11-05", "heure_debut": "09:15", "heure_fin": "10:00", "titre": "Reunion"}
    ]
    date = "2025-11-05"

    # 10:00 - 10:25 ne chevauche pas 09:15 - 10:00
    assert _has_collision_with_temps_morts(start_time, duration, temps_morts, date) is False


def test_has_collision_different_date():
    """Test pas de collision si date differente"""
    start_time = datetime(2025, 11, 5, 9, 30)
    duration = 25
    temps_morts = [
        {"date": "2025-11-06", "heure_debut": "09:15", "heure_fin": "10:00", "titre": "Reunion"}
    ]
    date = "2025-11-05"

    # Temps_mort est pour le 06, pas de collision
    assert _has_collision_with_temps_morts(start_time, duration, temps_morts, date) is False


def test_find_next_free_time():
    """Test recherche prochain creneau libre"""
    current_time = datetime(2025, 11, 5, 9, 30)
    temps_morts = [
        {"date": "2025-11-05", "heure_debut": "09:15", "heure_fin": "10:00", "titre": "Reunion"}
    ]
    date = "2025-11-05"

    # 09:30 est dans 09:15 - 10:00, doit retourner 10:00
    next_free = _find_next_free_time(current_time, temps_morts, date)

    assert next_free.hour == 10
    assert next_free.minute == 0


def test_find_next_free_time_no_collision():
    """Test si pas de collision, retourne meme heure"""
    current_time = datetime(2025, 11, 5, 10, 30)
    temps_morts = [
        {"date": "2025-11-05", "heure_debut": "09:15", "heure_fin": "10:00", "titre": "Reunion"}
    ]
    date = "2025-11-05"

    # 10:30 n'est pas dans un temps_mort
    next_free = _find_next_free_time(current_time, temps_morts, date)

    assert next_free == current_time


def test_assign_times_with_segments():
    """Test assignation temps avec segments"""
    sequence = [
        {
            "type": "work",
            "task": {"id": "T001"},
            "duration": 25,
            "segment_index": 1,
            "total_segments": 2
        },
        {
            "type": "work",
            "task": {"id": "T001"},
            "duration": 25,
            "segment_index": 2,
            "total_segments": 2
        }
    ]

    planningStartTime = "09:00"
    date = "2025-11-05"
    temps_morts = []

    timeline = assign_times_to_sequence(sequence, planningStartTime, date, temps_morts)

    # Verifier que les champs segment sont conserves
    assert timeline[0]["segment_index"] == 1
    assert timeline[0]["total_segments"] == 2
    assert timeline[1]["segment_index"] == 2
    assert timeline[1]["total_segments"] == 2
