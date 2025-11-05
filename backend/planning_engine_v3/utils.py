"""
Utilitaires pour GitFocus Planner V3
Conversions de temps, validations, helpers
"""

from datetime import datetime, timedelta
from typing import Optional
import re


# ============================================================================
# CONVERSIONS DE TEMPS (RELATIF  ABSOLU)
# ============================================================================

def datetime_to_minutes(dt: datetime, reference: datetime) -> int:
    """
    Convertit une datetime absolue en minutes relatives.

    Args:
        dt: DateTime a convertir
        reference: DateTime de reference (minute 0)

    Returns:
        Nombre de minutes depuis reference

    Examples:
        >>> ref = datetime(2025, 11, 5, 14, 25)
        >>> dt = datetime(2025, 11, 5, 14, 50)
        >>> datetime_to_minutes(dt, ref)
        25
        >>> dt = datetime(2025, 11, 5, 13, 25)
        >>> datetime_to_minutes(dt, ref)
        -60
    """
    delta = dt - reference
    return int(delta.total_seconds() / 60)


def minutes_to_datetime(minutes: int, reference: datetime) -> datetime:
    """
    Convertit des minutes relatives en datetime absolue.

    Args:
        minutes: Minutes depuis reference
        reference: DateTime de reference (minute 0)

    Returns:
        DateTime absolue

    Examples:
        >>> ref = datetime(2025, 11, 5, 14, 25)
        >>> minutes_to_datetime(0, ref)
        datetime.datetime(2025, 11, 5, 14, 25)
        >>> minutes_to_datetime(25, ref)
        datetime.datetime(2025, 11, 5, 14, 50)
        >>> minutes_to_datetime(-60, ref)
        datetime.datetime(2025, 11, 5, 13, 25)
    """
    return reference + timedelta(minutes=minutes)


def time_to_minutes(time_str: str) -> int:
    """
    Convertit une heure HH:MM en minutes depuis minuit.

    Args:
        time_str: Heure au format "HH:MM"

    Returns:
        Nombre de minutes depuis 00:00

    Examples:
        >>> time_to_minutes("00:00")
        0
        >>> time_to_minutes("14:25")
        865
        >>> time_to_minutes("23:59")
        1439

    Raises:
        ValueError: Si format invalide
    """
    match = re.match(r'^(\d{2}):(\d{2})$', time_str)
    if not match:
        raise ValueError(f"Format d'heure invalide: {time_str} (attendu HH:MM)")

    hours, minutes = int(match.group(1)), int(match.group(2))

    if hours > 23 or minutes > 59:
        raise ValueError(f"Heure invalide: {time_str}")

    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    """
    Convertit des minutes depuis minuit en heure HH:MM.

    Args:
        minutes: Minutes depuis 00:00

    Returns:
        Heure au format "HH:MM"

    Examples:
        >>> minutes_to_time(0)
        '00:00'
        >>> minutes_to_time(865)
        '14:25'
        >>> minutes_to_time(1439)
        '23:59'
        >>> minutes_to_time(1440)  # Minuit du jour suivant
        '00:00'
    """
    # Gerer les debordements (minutes > 1440)
    minutes = minutes % 1440

    hours = minutes // 60
    mins = minutes % 60

    return f"{hours:02d}:{mins:02d}"


# ============================================================================
# PARSING ET VALIDATION DE DATES
# ============================================================================

def parse_date_iso(date_str: str) -> datetime:
    """
    Parse une date au format ISO (YYYY-MM-DD).

    Args:
        date_str: Date au format "YYYY-MM-DD"

    Returns:
        DateTime (heure mise a 00:00)

    Raises:
        ValueError: Si format invalide

    Examples:
        >>> parse_date_iso("2025-11-05")
        datetime.datetime(2025, 11, 5, 0, 0)
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Format de date invalide: {date_str} (attendu YYYY-MM-DD)")


def parse_date_user(date_str: str) -> datetime:
    """
    Parse une date au format utilisateur (DD.MM.YY).

    Args:
        date_str: Date au format "DD.MM.YY"

    Returns:
        DateTime (heure mise a 00:00)

    Raises:
        ValueError: Si format invalide

    Examples:
        >>> parse_date_user("05.11.25")
        datetime.datetime(2025, 11, 5, 0, 0)
    """
    try:
        return datetime.strptime(date_str, '%d.%m.%y')
    except ValueError:
        raise ValueError(f"Format de date invalide: {date_str} (attendu DD.MM.YY)")


def parse_datetime_user(datetime_str: str) -> datetime:
    """
    Parse une date+heure au format utilisateur (DD.MM.YY HH:MM).

    Args:
        datetime_str: DateTime au format "DD.MM.YY HH:MM"

    Returns:
        DateTime complete

    Raises:
        ValueError: Si format invalide

    Examples:
        >>> parse_datetime_user("05.11.25 14:30")
        datetime.datetime(2025, 11, 5, 14, 30)
    """
    try:
        return datetime.strptime(datetime_str, '%d.%m.%y %H:%M')
    except ValueError:
        raise ValueError(f"Format datetime invalide: {datetime_str} (attendu DD.MM.YY HH:MM)")


def format_date_iso(dt: datetime) -> str:
    """
    Formate une datetime en ISO (YYYY-MM-DD).

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 30)
        >>> format_date_iso(dt)
        '2025-11-05'
    """
    return dt.strftime('%Y-%m-%d')


def format_date_user(dt: datetime) -> str:
    """
    Formate une datetime en format utilisateur (DD.MM.YY).

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 30)
        >>> format_date_user(dt)
        '05.11.25'
    """
    return dt.strftime('%d.%m.%y')


def format_time(dt: datetime) -> str:
    """
    Formate une datetime en heure HH:MM.

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 30)
        >>> format_time(dt)
        '14:30'
    """
    return dt.strftime('%H:%M')


# ============================================================================
# ARRONDI DE TEMPS
# ============================================================================

def round_up_to_multiple(value: int, multiple: int) -> int:
    """
    Arrondit une valeur au multiple superieur.

    Args:
        value: Valeur a arrondir
        multiple: Multiple cible

    Returns:
        Valeur arrondie au multiple superieur

    Examples:
        >>> round_up_to_multiple(13, 5)
        15
        >>> round_up_to_multiple(15, 5)
        15
        >>> round_up_to_multiple(7, 15)
        15
    """
    if value % multiple == 0:
        return value
    return ((value // multiple) + 1) * multiple


def round_time_up(dt: datetime, minutes: int) -> datetime:
    """
    Arrondit une datetime au multiple de minutes superieur.

    Args:
        dt: DateTime a arrondir
        minutes: Multiple de minutes (ex: 5, 15)

    Returns:
        DateTime arrondie

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 7)
        >>> round_time_up(dt, 5)
        datetime.datetime(2025, 11, 5, 14, 10)
        >>> dt = datetime(2025, 11, 5, 14, 25)
        >>> round_time_up(dt, 5)
        datetime.datetime(2025, 11, 5, 14, 25)
    """
    minute = dt.minute
    rounded_minute = round_up_to_multiple(minute, minutes)

    if rounded_minute >= 60:
        # Passage a l'heure suivante
        return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        return dt.replace(minute=rounded_minute, second=0, microsecond=0)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_time_range(start: str, end: str) -> bool:
    """
    Valide qu'une plage horaire est coherente (fin > debut).

    Args:
        start: Heure de debut "HH:MM"
        end: Heure de fin "HH:MM"

    Returns:
        True si valide, False sinon

    Examples:
        >>> validate_time_range("14:00", "15:00")
        True
        >>> validate_time_range("15:00", "14:00")
        False
        >>> validate_time_range("14:00", "14:00")
        False
    """
    try:
        start_min = time_to_minutes(start)
        end_min = time_to_minutes(end)
        return end_min > start_min
    except ValueError:
        return False


def validate_priority(priority: int) -> bool:
    """
    Valide qu'une priorite est dans la plage autorisee (1-3).

    Examples:
        >>> validate_priority(1)
        True
        >>> validate_priority(4)
        False
    """
    return priority in [1, 2, 3]


# ============================================================================
# HELPERS
# ============================================================================

def clean_csv_field(field: str) -> str:
    """
    Nettoie un champ CSV (supprime guillemets, espaces superflus).

    Examples:
        >>> clean_csv_field('"  Tâche  "')
        'Tâche'
        >>> clean_csv_field('Normal')
        'Normal'
    """
    return field.strip().strip('"').strip()


def safe_int(value: str, default: int = 0) -> int:
    """
    Convertit en int, retourne default si echec.

    Examples:
        >>> safe_int("42")
        42
        >>> safe_int("abc", 0)
        0
        >>> safe_int("", 10)
        10
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def generate_slot_id(task_type: str, index: int) -> str:
    """
    Genere un ID unique pour un slot de planning.

    Args:
        task_type: Type de tâche (pomodoro, pause, etc.)
        index: Index du slot

    Returns:
        ID au format "TYPE_INDEX"

    Examples:
        >>> generate_slot_id("pomodoro", 1)
        'POMODORO_1'
        >>> generate_slot_id("pause", 5)
        'PAUSE_5'
    """
    return f"{task_type.upper()}_{index}"
