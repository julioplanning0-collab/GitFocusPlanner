"""Tests pour timeline_builder.py"""

import pytest
from backend.planning_engine_v3.timeline_builder import (
    build_task_sequence,
    insert_recurrent_tasks,
    insert_planned_tasks,
    split_long_tasks,
    validate_sequence
)


def test_build_task_sequence():
    """Test construction sequence de base avec alternance travail/pause"""
    work_tasks = [
        {"id": "T001", "name": "Task 1", "duration_min": 25, "priority": 1},
        {"id": "T002", "name": "Task 2", "duration_min": 25, "priority": 2},
        {"id": "T003", "name": "Task 3", "duration_min": 25, "priority": 3}
    ]

    pauses = [
        {"id": "P001", "name": "Pause courte", "duration_min": 5},
        {"id": "P002", "name": "Pause longue", "duration_min": 10}
    ]

    recurrent_tasks = []

    sequence = build_task_sequence(work_tasks, pauses, recurrent_tasks)

    # Verifier structure
    assert len(sequence) == 6  # 3 travaux + 3 pauses
    assert sequence[0]["type"] == "work"
    assert sequence[1]["type"] == "pause"
    assert sequence[2]["type"] == "work"
    assert sequence[3]["type"] == "pause"

    # Verifier tri par priorite
    assert sequence[0]["task"]["id"] == "T001"  # Priorite 1
    assert sequence[2]["task"]["id"] == "T002"  # Priorite 2
    assert sequence[4]["task"]["id"] == "T003"  # Priorite 3

    # Verifier rotation des pauses
    assert sequence[1]["task"]["id"] == "P001"
    assert sequence[3]["task"]["id"] == "P002"
    assert sequence[5]["task"]["id"] == "P001"  # Rotation circulaire


def test_build_task_sequence_no_pauses():
    """Test construction sans pauses disponibles"""
    work_tasks = [
        {"id": "T001", "name": "Task 1", "duration_min": 25, "priority": 1}
    ]

    pauses = []
    recurrent_tasks = []

    sequence = build_task_sequence(work_tasks, pauses, recurrent_tasks)

    # Seulement taches de travail
    assert len(sequence) == 1
    assert sequence[0]["type"] == "work"


def test_insert_recurrent_tasks():
    """Test insertion taches recurrentes dans sequence"""
    base_sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5},
        {"type": "work", "task": {"id": "T002"}, "duration": 25},
        {"type": "pause", "task": {"id": "P002"}, "duration": 5},
        {"type": "work", "task": {"id": "T003"}, "duration": 25},
        {"type": "pause", "task": {"id": "P003"}, "duration": 5}
    ]

    recurrent_tasks = [
        {"id": "R001", "name": "Recurrent 1", "duration_min": 15}
    ]

    result = insert_recurrent_tasks(base_sequence, recurrent_tasks)

    # Verifier qu'au moins une recurrente est inseree
    assert len(result) > len(base_sequence)

    # Trouver la recurrente
    recurrent_found = any(item["type"] == "recurrent" for item in result)
    assert recurrent_found is True


def test_insert_recurrent_tasks_empty():
    """Test insertion avec liste vide de recurrentes"""
    base_sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5}
    ]

    recurrent_tasks = []

    result = insert_recurrent_tasks(base_sequence, recurrent_tasks)

    # Sequence inchangee
    assert result == base_sequence


def test_insert_planned_tasks():
    """Test insertion taches planifiees a heure cible"""
    base_sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5},
        {"type": "work", "task": {"id": "T002"}, "duration": 25}
    ]

    planned_tasks = [
        {
            "id": "PL001",
            "name": "Planned 1",
            "duration_min": 25,
            "planned_start": "05.11.25 10:00"
        }
    ]

    planningStartTime = "09:00"

    result = insert_planned_tasks(base_sequence, planned_tasks, planningStartTime)

    # Verifier qu'une planifiee est inseree
    assert len(result) > len(base_sequence)

    # Trouver la planifiee
    planned_found = any(item["type"] == "planned" for item in result)
    assert planned_found is True


def test_split_long_tasks():
    """Test decoupage taches longues en segments"""
    sequence = [
        {"type": "work", "task": {"id": "T001", "name": "Task 1"}, "duration": 50},
        {"type": "work", "task": {"id": "T002", "name": "Task 2"}, "duration": 25}
    ]

    result = split_long_tasks(sequence, max_duration=25)

    # Verifier qu'il y a plus d'items (T001 decoupe)
    assert len(result) > len(sequence)

    # Verifier que T001 est decoupe en 2 segments
    t001_segments = [item for item in result if item["task"]["id"] == "T001"]
    assert len(t001_segments) == 2
    assert t001_segments[0]["segment_index"] == 1
    assert t001_segments[0]["total_segments"] == 2
    assert t001_segments[1]["segment_index"] == 2
    assert t001_segments[1]["total_segments"] == 2

    # Verifier que T002 reste intact
    t002_items = [item for item in result if item["task"]["id"] == "T002"]
    assert len(t002_items) == 1
    assert "segment_index" not in t002_items[0]


def test_split_long_tasks_exact_multiple():
    """Test decoupage tache exactement divisible"""
    sequence = [
        {"type": "work", "task": {"id": "T001", "name": "Task 1"}, "duration": 75}
    ]

    result = split_long_tasks(sequence, max_duration=25)

    # 75 / 25 = 3 segments exacts
    assert len(result) == 3
    assert all(item["duration"] == 25 for item in result)


def test_validate_sequence_valid():
    """Test validation sequence correcte"""
    sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "pause", "task": {"id": "P001"}, "duration": 5},
        {"type": "work", "task": {"id": "T002"}, "duration": 25}
    ]

    assert validate_sequence(sequence) is True


def test_validate_sequence_empty():
    """Test validation sequence vide"""
    sequence = []

    assert validate_sequence(sequence) is False


def test_validate_sequence_missing_fields():
    """Test validation avec champs manquants"""
    sequence = [
        {"type": "work", "duration": 25}  # Missing "task"
    ]

    assert validate_sequence(sequence) is False


def test_validate_sequence_invalid_duration():
    """Test validation avec duree invalide"""
    sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 0}
    ]

    assert validate_sequence(sequence) is False


def test_validate_sequence_consecutive_duplicates():
    """Test validation avec doublons consecutifs"""
    sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25},
        {"type": "work", "task": {"id": "T001"}, "duration": 25}
    ]

    assert validate_sequence(sequence) is False


def test_validate_sequence_segments_allowed():
    """Test validation permet segments (meme ID consecutif si segment_index present)"""
    sequence = [
        {"type": "work", "task": {"id": "T001"}, "duration": 25, "segment_index": 1, "total_segments": 2},
        {"type": "work", "task": {"id": "T001"}, "duration": 25, "segment_index": 2, "total_segments": 2}
    ]

    assert validate_sequence(sequence) is True
