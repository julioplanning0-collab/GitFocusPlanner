"""Tests pour data_loader.py"""

import pytest
from pathlib import Path
from backend.planning_engine_v3.data_loader import (
    load_work_tasks,
    load_pauses,
    load_recurrent_tasks,
    load_temps_morts,
    load_planned_tasks,
    load_categories
)


# Utiliser le repertoire prod_data comme source de donnees
PROD_DATA_DIR = Path("C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data")


def test_load_work_tasks():
    """Test chargement taches de travail depuis LISTE_MERE.v2.csv"""
    tasks = load_work_tasks(PROD_DATA_DIR)

    # Verifier que le chargement retourne une liste
    assert isinstance(tasks, list)

    # Si fichier existe, verifier structure
    if len(tasks) > 0:
        task = tasks[0]

        # Verifier champs obligatoires
        assert "id" in task
        assert "name" in task
        assert "duration_min" in task

        # Verifier types
        assert isinstance(task["id"], str)
        assert isinstance(task["name"], str)
        assert isinstance(task["duration_min"], int)
        assert isinstance(task["priority"], int)

        # Verifier filtrage STATUS
        for t in tasks:
            assert t.get("status") not in ["DONE", "CANCELLED"]


def test_load_pauses():
    """Test chargement pauses depuis TACHES_RECURRENTES.v2.csv"""
    # Sans filtre actif
    all_pauses = load_pauses(PROD_DATA_DIR, active_only=False)
    assert isinstance(all_pauses, list)

    # Avec filtre actif
    active_pauses = load_pauses(PROD_DATA_DIR, active_only=True)
    assert isinstance(active_pauses, list)

    # Verifier que toutes les actives sont incluses dans all
    assert len(active_pauses) <= len(all_pauses)

    # Si pauses existent, verifier structure
    if len(all_pauses) > 0:
        pause = all_pauses[0]

        assert "id" in pause
        assert "name" in pause
        assert "duration_min" in pause
        assert "is_pause" in pause
        assert pause["is_pause"] is True

        # Verifier types
        assert isinstance(pause["duration_min"], int)
        assert isinstance(pause["is_active"], bool)


def test_load_recurrent_tasks():
    """Test chargement taches recurrentes depuis TACHES_RECURRENTES.v2.csv"""
    # Sans filtre actif
    all_tasks = load_recurrent_tasks(PROD_DATA_DIR, active_only=False)
    assert isinstance(all_tasks, list)

    # Avec filtre actif
    active_tasks = load_recurrent_tasks(PROD_DATA_DIR, active_only=True)
    assert isinstance(active_tasks, list)

    # Verifier que toutes les actives sont incluses dans all
    assert len(active_tasks) <= len(all_tasks)

    # Si taches existent, verifier structure
    if len(all_tasks) > 0:
        task = all_tasks[0]

        assert "id" in task
        assert "name" in task
        assert "duration_min" in task
        assert "recurrence_type" in task
        assert "is_pause" in task
        assert task["is_pause"] is False

        # Verifier types
        assert isinstance(task["duration_min"], int)
        assert isinstance(task["recurrence_interval"], int)
        assert isinstance(task["is_active"], bool)


def test_load_temps_morts():
    """Test chargement temps morts pour une date"""
    # Test avec date ISO
    date = "2025-11-05"
    temps_morts = load_temps_morts(PROD_DATA_DIR, date)

    assert isinstance(temps_morts, list)

    # Si temps morts existent, verifier structure
    if len(temps_morts) > 0:
        tm = temps_morts[0]

        assert "date" in tm
        assert "heure_debut" in tm
        assert "heure_fin" in tm
        assert "titre" in tm

        # Verifier que tous sont pour la bonne date
        for t in temps_morts:
            assert t["date"] == date


def test_load_planned_tasks():
    """Test chargement taches planifiees"""
    # Sans filtre de date
    all_tasks = load_planned_tasks(PROD_DATA_DIR)
    assert isinstance(all_tasks, list)

    # Avec filtre de date
    date = "2025-11-05"
    filtered_tasks = load_planned_tasks(PROD_DATA_DIR, date=date)
    assert isinstance(filtered_tasks, list)

    # Les filtrees doivent etre un sous-ensemble
    assert len(filtered_tasks) <= len(all_tasks)

    # Si taches existent, verifier structure
    if len(all_tasks) > 0:
        task = all_tasks[0]

        assert "id" in task
        assert "name" in task
        assert "duration_min" in task
        assert "planned_start" in task

        # Verifier que PLANNED_START est rempli
        assert task["planned_start"] != ""


def test_load_categories():
    """Test chargement categories depuis categories.csv"""
    categories = load_categories(PROD_DATA_DIR)

    # Verifier que c'est un dictionnaire
    assert isinstance(categories, dict)

    # Si categories existent, verifier structure
    if len(categories) > 0:
        # Verifier qu'au moins une categorie existe
        assert len(categories) > 0

        # Prendre une categorie au hasard
        cat_name = list(categories.keys())[0]
        subcats = categories[cat_name]

        # Verifier que les sous-categories sont une liste
        assert isinstance(subcats, list)

        # Verifier que les sous-categories ne sont pas vides
        if len(subcats) > 0:
            assert isinstance(subcats[0], str)


def test_load_work_tasks_missing_file():
    """Test comportement quand fichier absent"""
    fake_dir = Path("/chemin/inexistant")
    tasks = load_work_tasks(fake_dir)

    # Doit retourner liste vide, pas d'exception
    assert tasks == []


def test_load_pauses_missing_file():
    """Test comportement quand fichier absent"""
    fake_dir = Path("/chemin/inexistant")
    pauses = load_pauses(fake_dir)

    # Doit retourner liste vide, pas d'exception
    assert pauses == []
