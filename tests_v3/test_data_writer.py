"""
Tests pour data_writer.py
Module d'ecriture CSV (export planning)
"""

import pytest
import csv
from pathlib import Path
from backend.planning_engine_v3.data_writer import write_planning_csv


def test_write_planning_csv_basic(tmp_path):
    """
    Test ecriture CSV basique.
    
    Verifie:
        - Fichier cree
        - Headers corrects
        - Donnees ecrites
    """
    csv_path = tmp_path / "planning.csv"
    
    timeline = [
        {
            "type": "work",
            "name": "Tache 1",
            "start_time": "08:00",
            "end_time": "08:25",
            "duration": 25
        },
        {
            "type": "pause",
            "name": "Pause",
            "start_time": "08:25",
            "end_time": "08:30",
            "duration": 5
        }
    ]
    
    write_planning_csv(csv_path, timeline, date="2025-11-05")
    
    # Verifier fichier existe
    assert csv_path.exists()
    
    # Lire et verifier contenu
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]["TYPE"] == "work"
    assert rows[0]["NAME"] == "Tache 1"
    assert rows[1]["TYPE"] == "pause"


def test_write_planning_csv_empty(tmp_path):
    """
    Test ecriture avec timeline vide.
    
    Verifie:
        - Fichier cree
        - Headers presents
        - Aucune donnee
    """
    csv_path = tmp_path / "planning_empty.csv"
    
    write_planning_csv(csv_path, [], date="2025-11-05")
    
    assert csv_path.exists()
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    
    assert len(rows) == 0


def test_write_planning_csv_overwrites(tmp_path):
    """
    Test que ecriture ecrase fichier existant.
    
    Verifie:
        - Ancien contenu supprime
        - Nouveau contenu ecrit
    """
    csv_path = tmp_path / "planning_overwrite.csv"
    
    # Premier write
    timeline1 = [{"type": "work", "name": "Old", "start_time": "08:00", "end_time": "08:25", "duration": 25}]
    write_planning_csv(csv_path, timeline1, date="2025-11-05")
    
    # Deuxieme write (ecrase)
    timeline2 = [{"type": "pause", "name": "New", "start_time": "09:00", "end_time": "09:05", "duration": 5}]
    write_planning_csv(csv_path, timeline2, date="2025-11-05")
    
    # Verifier nouveau contenu
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]["NAME"] == "New"
    assert rows[0]["TYPE"] == "pause"


def test_write_planning_csv_special_characters(tmp_path):
    """
    Test avec caracteres speciaux.
    
    Verifie:
        - Accents preserves
        - Guillemets echappes
        - Point-virgules dans donnees OK
    """
    csv_path = tmp_path / "planning_special.csv"
    
    timeline = [
        {
            "type": "work",
            "name": "Revision; mathematiques",  # Point-virgule
            "start_time": "08:00",
            "end_time": "08:25",
            "duration": 25
        }
    ]
    
    write_planning_csv(csv_path, timeline, date="2025-11-05")
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        rows = list(reader)
    
    assert rows[0]["NAME"] == "Revision; mathematiques"
