"""Tests pour utils.py"""

import pytest
from datetime import datetime
from backend.planning_engine_v3.utils import (
    datetime_to_minutes,
    minutes_to_datetime,
    time_to_minutes,
    minutes_to_time,
    round_up_to_multiple,
    round_time_up,
    validate_time_range,
    clean_csv_field,
    safe_int
)


def test_datetime_to_minutes():
    """Test conversion datetime vers minutes relatives"""
    ref = datetime(2025, 11, 5, 14, 25)

    # Minute 0
    assert datetime_to_minutes(ref, ref) == 0

    # +25 minutes
    dt = datetime(2025, 11, 5, 14, 50)
    assert datetime_to_minutes(dt, ref) == 25

    # -60 minutes
    dt = datetime(2025, 11, 5, 13, 25)
    assert datetime_to_minutes(dt, ref) == -60


def test_minutes_to_datetime():
    """Test conversion minutes relatives vers datetime"""
    ref = datetime(2025, 11, 5, 14, 25)

    # Minute 0
    assert minutes_to_datetime(0, ref) == ref

    # +25 minutes
    assert minutes_to_datetime(25, ref) == datetime(2025, 11, 5, 14, 50)

    # -60 minutes
    assert minutes_to_datetime(-60, ref) == datetime(2025, 11, 5, 13, 25)


def test_time_to_minutes():
    """Test conversion HH:MM vers minutes depuis minuit"""
    assert time_to_minutes("00:00") == 0
    assert time_to_minutes("14:25") == 865
    assert time_to_minutes("23:59") == 1439

    # Format invalide
    with pytest.raises(ValueError):
        time_to_minutes("25:00")

    with pytest.raises(ValueError):
        time_to_minutes("14:60")


def test_minutes_to_time():
    """Test conversion minutes depuis minuit vers HH:MM"""
    assert minutes_to_time(0) == "00:00"
    assert minutes_to_time(865) == "14:25"
    assert minutes_to_time(1439) == "23:59"

    # Debordement (minuit du jour suivant)
    assert minutes_to_time(1440) == "00:00"


def test_round_up_to_multiple():
    """Test arrondi au multiple superieur"""
    assert round_up_to_multiple(13, 5) == 15
    assert round_up_to_multiple(15, 5) == 15
    assert round_up_to_multiple(7, 15) == 15
    assert round_up_to_multiple(0, 5) == 0


def test_round_time_up():
    """Test arrondi datetime"""
    dt = datetime(2025, 11, 5, 14, 7)
    assert round_time_up(dt, 5) == datetime(2025, 11, 5, 14, 10)

    dt = datetime(2025, 11, 5, 14, 25)
    assert round_time_up(dt, 5) == datetime(2025, 11, 5, 14, 25)

    dt = datetime(2025, 11, 5, 14, 58)
    assert round_time_up(dt, 5) == datetime(2025, 11, 5, 15, 0)


def test_validate_time_range():
    """Test validation plage horaire"""
    assert validate_time_range("14:00", "15:00") is True
    assert validate_time_range("15:00", "14:00") is False
    assert validate_time_range("14:00", "14:00") is False


def test_clean_csv_field():
    """Test nettoyage champ CSV"""
    assert clean_csv_field('"  Tache  "') == "Tache"
    assert clean_csv_field('Normal') == "Normal"
    assert clean_csv_field('""') == ""


def test_safe_int():
    """Test conversion int securisee"""
    assert safe_int("42") == 42
    assert safe_int("abc", 0) == 0
    assert safe_int("", 10) == 10
    assert safe_int(None, 5) == 5
