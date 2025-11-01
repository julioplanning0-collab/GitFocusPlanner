"""
Slot Calculator Module - GitFocus Planner V2
Calculates free 30-minute time slots avoiding temps_morts.

LOGIC:
- Day: 06:00 to 23:00 (17 hours)
- If date == today: Start at current time (rounded up to 15min)
- 30-minute blocks
- Overlap detection: slot_start < tm_end AND slot_end > tm_start
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


def calculate_free_slots(date: str, temps_morts: List[Dict]) -> List[Dict]:
    """
    Calculate free 30-minute slots for a specific date.

    Args:
        date: ISO date YYYY-MM-DD
        temps_morts: List of blocked time slots
                     Format: [{"heure_debut": "HH:MM", "heure_fin": "HH:MM"}, ...]

    Returns:
        List of free slots: [{"heure_debut": "HH:MM", "heure_fin": "HH:MM"}, ...]

    Raises:
        ValueError: If date format invalid
    """
    # Parse date
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date}'. Expected YYYY-MM-DD") from e

    # NEW APPROACH: Fill all "holes" between temps_morts with 30-min slots
    # This ensures we use ALL available time, not just aligned slots

    day_start = datetime.combine(target_date, datetime.min.time()).replace(hour=6, minute=0)
    day_end = datetime.combine(target_date, datetime.min.time()).replace(hour=23, minute=59) + timedelta(minutes=1)

    now = datetime.now()
    today = now.date()

    # Sort temps_morts by start time
    sorted_temps_morts = sorted(temps_morts, key=lambda tm: tm['heure_debut'])

    # Build list of blocked periods
    blocked_periods = []
    for tm in sorted_temps_morts:
        try:
            tm_start = datetime.combine(target_date, datetime.strptime(tm['heure_debut'], "%H:%M").time())
            tm_end = datetime.combine(target_date, datetime.strptime(tm['heure_fin'], "%H:%M").time())
            blocked_periods.append((tm_start, tm_end))
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid temps_mort entry {tm}: {e}")
            continue

    # Find all "holes" (free periods) and fill them with 30-min slots
    free_slots = []

    # Start from day_start (or current time if today)
    current = day_start
    if target_date == today:
        # Round up to next 15-min mark if planning for today
        minutes = now.minute
        rounded_minutes = ((minutes // 15) + 1) * 15
        if rounded_minutes == 60:
            current = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)
        else:
            current = now.replace(minute=rounded_minutes, second=0, microsecond=0)

        # Make sure we don't start before 06:00
        if current < day_start:
            current = day_start

    # Generate slots by filling holes between blocked periods
    for tm_start, tm_end in blocked_periods:
        # Fill the hole from current to tm_start
        while current + timedelta(minutes=30) <= tm_start:
            slot_end = current + timedelta(minutes=30)
            free_slots.append({
                'heure_debut': current.strftime("%H:%M"),
                'heure_fin': slot_end.strftime("%H:%M")
            })
            current = slot_end

        # Jump past this temps_mort
        if tm_end > current:
            current = tm_end

    # Fill the final hole from current to day_end
    while current < day_end:
        slot_end = min(current + timedelta(minutes=30), day_end)
        # Only create slot if it's at least 30 minutes OR if it reaches exactly day_end
        if slot_end - current >= timedelta(minutes=30) or slot_end == day_end:
            free_slots.append({
                'heure_debut': current.strftime("%H:%M"),
                'heure_fin': slot_end.strftime("%H:%M")
            })
            current = slot_end
        else:
            break

    logger.info(f"Found {len(free_slots)} free 30-min slots")

    # Debug: Log first and last slots
    if free_slots:
        logger.info(f"First free slot: {free_slots[0]['heure_debut']}-{free_slots[0]['heure_fin']}")
        logger.info(f"Last free slot: {free_slots[-1]['heure_debut']}-{free_slots[-1]['heure_fin']}")

    return free_slots


def _overlaps_temps_mort(slot: Dict, temps_morts: List[Dict], date: datetime.date) -> bool:
    """
    Check if slot overlaps with any temps_mort.

    Overlap formula: slot_start < tm_end AND slot_end > tm_start

    Args:
        slot: {"heure_debut": "HH:MM", "heure_fin": "HH:MM"}
        temps_morts: List of temps_mort dicts
        date: Date for time parsing

    Returns:
        True if overlap detected, False otherwise
    """
    slot_start = datetime.combine(date, datetime.strptime(slot['heure_debut'], "%H:%M").time())
    slot_end = datetime.combine(date, datetime.strptime(slot['heure_fin'], "%H:%M").time())

    for tm in temps_morts:
        try:
            tm_start = datetime.combine(date, datetime.strptime(tm['heure_debut'], "%H:%M").time())
            tm_end = datetime.combine(date, datetime.strptime(tm['heure_fin'], "%H:%M").time())

            # Overlap detection
            if slot_start < tm_end and slot_end > tm_start:
                logger.debug(f"Slot {slot['heure_debut']}-{slot['heure_fin']} overlaps with temps_mort {tm['heure_debut']}-{tm['heure_fin']}")
                return True

        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid temps_mort entry {tm}: {e}")
            continue

    return False


def find_next_free_slot(start_time: datetime, duration_min: int, temps_morts: List[Dict]) -> datetime:
    """
    Find next available time slot that doesn't overlap with temps_morts.

    Args:
        start_time: Candidate start time
        duration_min: Duration in minutes
        temps_morts: List of blocked time slots

    Returns:
        Next available start time (may be same as start_time if no overlap)
    """
    max_attempts = 100  # Safety limit (avoid infinite loop)
    candidate_start = start_time

    for _ in range(max_attempts):
        candidate_end = candidate_start + timedelta(minutes=duration_min)

        # Check overlap with temps_morts
        overlaps = False
        for tm in temps_morts:
            try:
                tm_start = datetime.combine(
                    candidate_start.date(),
                    datetime.strptime(tm['heure_debut'], "%H:%M").time()
                )
                tm_end = datetime.combine(
                    candidate_start.date(),
                    datetime.strptime(tm['heure_fin'], "%H:%M").time()
                )

                if candidate_start < tm_end and candidate_end > tm_start:
                    overlaps = True
                    # Jump to end of temps_mort
                    candidate_start = tm_end
                    break

            except (ValueError, KeyError) as e:
                logger.warning(f"Invalid temps_mort entry {tm}: {e}")
                continue

        if not overlaps:
            return candidate_start  # Found free slot

        # Advance by 15 minutes and retry
        candidate_start += timedelta(minutes=15)

        # Safety: don't go past 23:00
        if candidate_start.hour >= 23:
            logger.error(f"Cannot find free slot for duration {duration_min} min starting from {start_time.time()}")
            return start_time  # Return original (caller will handle)

    logger.error(f"Exceeded max attempts ({max_attempts}) finding free slot, returning start_time")
    return start_time
