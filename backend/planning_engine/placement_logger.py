"""
Placement Logger Module - GitFocus Planner V2 🆕
Records planning placements to planning_placements_history.csv (append-only).

PURPOSE:
- Track which recurrent tasks are placed at which times
- Build historical data for smart scoring
- Enable learning system to improve over time

CRITICAL:
- Mode APPEND-ONLY (never delete history)
- One row per recurrent task in exported planning
- Extensible columns (MOOD, ENERGY, WEATHER) for future evolution
"""

import logging
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


def log_planning_placements(
    planning: List[Dict],
    export_timestamp: str,
    data_dir: Path
) -> int:
    """
    Log recurrent task placements to history file.

    Args:
        planning: Complete planning (result of planning_generator)
        export_timestamp: ISO 8601 timestamp (e.g., "2025-10-30T12:00:00")
        data_dir: Path to prod_data/ directory

    Returns:
        Number of placements logged

    Side Effects:
        Appends rows to planning_placements_history.csv
    """
    history_file = data_dir / 'planning_placements_history.csv'

    # Filter only recurrent tasks
    recurrent_slots = [slot for slot in planning if slot.get('type') == 'recurrent']

    if len(recurrent_slots) == 0:
        logger.debug("No recurrent tasks in planning, nothing to log")
        return 0

    # Build rows to append
    rows_to_add = []
    for slot in recurrent_slots:
        # Parse date for day_of_week
        date_str = slot.get('date', '')
        if not date_str:
            logger.warning(f"Slot {slot.get('id')} missing date, skipping logging")
            continue

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = date_obj.weekday()  # 0=Monday, 6=Sunday
        except ValueError as e:
            logger.error(f"Invalid date format in slot {slot.get('id')}: {date_str}: {e}")
            continue

        row = {
            'TASK_ID': slot.get('task_id', ''),
            'TASK_NAME': slot.get('task_name', ''),
            'DATE': date_str,
            'PLANNED_TIME': slot.get('heure_debut', ''),
            'DAY_OF_WEEK': str(day_of_week),
            'WEEK_TYPE': '',  # Extensible (future: work week, vacation week, etc.)
            'MOOD': '',       # Extensible (future: user mood indicator)
            'ENERGY': '',     # Extensible (future: low, medium, high)
            'WEATHER': '',    # Extensible (future: sunny, rainy, etc.)
            'SEASON': '',     # Extensible (future: spring, summer, etc.)
            'EXPORT_TIMESTAMP': export_timestamp
        }

        rows_to_add.append(row)

    # Append to history file
    fieldnames = [
        'TASK_ID', 'TASK_NAME', 'DATE', 'PLANNED_TIME', 'DAY_OF_WEEK',
        'WEEK_TYPE', 'MOOD', 'ENERGY', 'WEATHER', 'SEASON', 'EXPORT_TIMESTAMP'
    ]

    try:
        _append_to_history(history_file, rows_to_add, fieldnames)
        logger.info(f"Logged {len(rows_to_add)} recurrent task placements to history")
        return len(rows_to_add)

    except Exception as e:
        logger.error(f"Failed to log placements: {e}", exc_info=True)
        raise IOError(f"Failed to log placements: {e}") from e


def _append_to_history(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    """
    Append rows to planning_placements_history.csv.

    IMPORTANT: Mode append (not atomic) because we're adding, not overwriting.
    Even if crash, old data is intact.

    Args:
        csv_path: Path to planning_placements_history.csv
        rows: Rows to append
        fieldnames: Column names

    Raises:
        IOError: If append fails
    """
    # Create file with header if doesn't exist
    if not csv_path.exists():
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
                writer.writeheader()
            logger.info(f"Created new history file: {csv_path.name}")
        except Exception as e:
            raise IOError(f"Failed to create history file {csv_path.name}: {e}") from e

    # Append rows
    try:
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerows(rows)

        logger.debug(f"Appended {len(rows)} rows to {csv_path.name}")

    except Exception as e:
        raise IOError(f"Failed to append to {csv_path.name}: {e}") from e


def get_history_stats(data_dir: Path) -> Dict:
    """
    Get statistics about planning history.

    Args:
        data_dir: Path to prod_data/ directory

    Returns:
        Dict with stats: {"total_entries": 123, "unique_tasks": 45, ...}
    """
    history_file = data_dir / 'planning_placements_history.csv'

    if not history_file.exists():
        return {
            'total_entries': 0,
            'unique_tasks': 0,
            'date_range': None
        }

    try:
        from backend.planning_engine.data_loader import load_planning_history
        history = load_planning_history(history_file)

        unique_task_ids = set(p['task_id'] for p in history)

        # Date range
        if history:
            dates = [datetime.strptime(p['date'], "%Y-%m-%d") for p in history if p.get('date')]
            if dates:
                date_range = {
                    'start': min(dates).strftime("%Y-%m-%d"),
                    'end': max(dates).strftime("%Y-%m-%d")
                }
            else:
                date_range = None
        else:
            date_range = None

        return {
            'total_entries': len(history),
            'unique_tasks': len(unique_task_ids),
            'date_range': date_range
        }

    except Exception as e:
        logger.error(f"Error getting history stats: {e}", exc_info=True)
        return {
            'total_entries': 0,
            'unique_tasks': 0,
            'date_range': None,
            'error': str(e)
        }
