"""
Data Writer Module - GitFocus Planner V2
Writes all CSV files using ATOMIC operations (temp file + rename).

CRITICAL RULES:
- ALL writes MUST use _atomic_write_csv (temp file + rename)
- NEVER write directly to CSV (risk corruption on crash)
- Delimiter ';', Quoting QUOTE_ALL, Encoding UTF-8
- Log all operations clearly
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# ATOMIC WRITE PATTERN (MANDATORY FOR ALL CSV WRITES)
# ============================================================================

def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    """
    Write CSV file atomically using temp file + rename pattern.

    WHY ATOMIC:
    - If process crashes during write, temp file is corrupted but original intact
    - Path.replace() is atomic on all OS (POSIX guarantees)
    - Critical for user data preservation

    Args:
        csv_path: Target CSV file path
        rows: List of dictionaries to write
        fieldnames: Column names (in order)

    Raises:
        IOError: If write fails
    """
    temp_file = csv_path.with_suffix('.tmp')

    try:
        # Write to temp file first
        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)

        # Atomic rename (OS-level guarantee)
        temp_file.replace(csv_path)

        logger.debug(f"Atomically wrote {len(rows)} rows to {csv_path.name}")

    except Exception as e:
        # Cleanup temp file on error
        if temp_file.exists():
            temp_file.unlink()
        logger.error(f"Failed to write {csv_path.name}: {e}", exc_info=True)
        raise IOError(f"Failed to write {csv_path.name}: {e}") from e


def _append_csv_rows(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    """
    Append rows to CSV file (for append-only files like history).

    NOTE: Mode 'a' (append) doesn't need atomic pattern because we're adding,
    not overwriting. Even if crash, old data is intact.

    Args:
        csv_path: Target CSV file path
        rows: List of dictionaries to append
        fieldnames: Column names (in order)

    Raises:
        IOError: If append fails
    """
    try:
        # If file doesn't exist, create with header
        if not csv_path.exists():
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
                writer.writeheader()
            logger.debug(f"Created new CSV file {csv_path.name} with header")

        # Append rows
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerows(rows)

        logger.debug(f"Appended {len(rows)} rows to {csv_path.name}")

    except Exception as e:
        logger.error(f"Failed to append to {csv_path.name}: {e}", exc_info=True)
        raise IOError(f"Failed to append to {csv_path.name}: {e}") from e


# ============================================================================
# POMODORO TASKS (LISTE_MERE.v2.csv)
# ============================================================================

def create_pomodoro_task(csv_path: Path, new_task: Dict) -> None:
    """
    Create new Pomodoro task.

    Args:
        csv_path: Path to LISTE_MERE.v2.csv
        new_task: Task dictionary with all fields

    Raises:
        IOError: If write fails
    """
    from backend.planning_engine.data_loader import load_pomodoro_tasks

    # Load existing tasks
    tasks = load_pomodoro_tasks(csv_path)

    # Add new task
    tasks.append(new_task)

    # Fieldnames
    fieldnames = [
        'ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY',
        'DURATION_MIN', 'REMAINING_MIN', 'PRIORITY', 'TAGS', 'KEYWORDS',
        'DEPENDENCIES', 'NOTES', 'DEADLINE', 'FIXED_START', 'PLANNED_START', 'STATUS'
    ]

    # Atomic write
    _atomic_write_csv(csv_path, tasks, fieldnames)
    logger.info(f"Created Pomodoro task {new_task['id']}")


def update_pomodoro_task(csv_path: Path, task_id: str, updates: Dict) -> None:
    """
    Update single Pomodoro task.

    Args:
        csv_path: Path to LISTE_MERE.v2.csv
        task_id: ID of task to update
        updates: Dictionary with fields to update

    Raises:
        ValueError: If task_id not found
        IOError: If write fails
    """
    from backend.planning_engine.data_loader import load_pomodoro_tasks

    # Load existing tasks
    tasks = load_pomodoro_tasks(csv_path)

    # Find and update task
    task_found = False
    for task in tasks:
        if task['id'] == task_id:
            task.update(updates)
            task_found = True
            break

    if not task_found:
        raise ValueError(f"Pomodoro task {task_id} not found in {csv_path.name}")

    # Fieldnames
    fieldnames = [
        'ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY',
        'DURATION_MIN', 'REMAINING_MIN', 'PRIORITY', 'TAGS', 'KEYWORDS',
        'DEPENDENCIES', 'NOTES', 'DEADLINE', 'FIXED_START', 'PLANNED_START', 'STATUS'
    ]

    # Atomic write
    _atomic_write_csv(csv_path, tasks, fieldnames)
    logger.info(f"Updated Pomodoro task {task_id}")


def delete_pomodoro_task(csv_path: Path, task_id: str) -> None:
    """
    Delete single Pomodoro task.

    Args:
        csv_path: Path to LISTE_MERE.v2.csv
        task_id: ID of task to delete

    Raises:
        ValueError: If task_id not found
        IOError: If write fails
    """
    from backend.planning_engine.data_loader import load_pomodoro_tasks

    # Load existing tasks
    tasks = load_pomodoro_tasks(csv_path)

    # Filter out task to delete
    original_count = len(tasks)
    tasks = [t for t in tasks if t['id'] != task_id]

    if len(tasks) == original_count:
        raise ValueError(f"Pomodoro task {task_id} not found in {csv_path.name}")

    # Fieldnames
    fieldnames = [
        'ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY',
        'DURATION_MIN', 'REMAINING_MIN', 'PRIORITY', 'TAGS', 'KEYWORDS',
        'DEPENDENCIES', 'NOTES', 'DEADLINE', 'FIXED_START', 'PLANNED_START', 'STATUS'
    ]

    # Atomic write
    _atomic_write_csv(csv_path, tasks, fieldnames)
    logger.info(f"Deleted Pomodoro task {task_id}")


# ============================================================================
# RESPIRATION TASKS (TACHES_RESPIRATOIRES.v2.csv)
# ============================================================================

def increment_respiration_export_count(csv_path: Path, task_ids: List[str]) -> None:
    """
    Increment EXPORT_COUNT for used respiration tasks.

    Args:
        csv_path: Path to TACHES_RESPIRATOIRES.v2.csv
        task_ids: List of task IDs to increment

    Raises:
        IOError: If write fails
    """
    from backend.planning_engine.data_loader import load_respiration_tasks

    # Load all respiration tasks (unsorted)
    tasks = load_respiration_tasks(csv_path)

    # Increment export_count for matching IDs
    for task in tasks:
        if task['id'] in task_ids:
            task['export_count'] += 1
            logger.debug(f"Incremented export_count for {task['id']} to {task['export_count']}")

    # Fieldnames
    fieldnames = [
        'ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY', 'DURATION_MIN',
        'REPEAT_INTERVAL_MIN', 'LAST_DONE_TIMESTAMP', 'LAST_DONE_DATE',
        'EARLIEST_TIME', 'LATEST_TIME', 'IDEAL_TIME', 'PRIORITY',
        'TAGS', 'KEYWORDS', 'DEPENDENCIES', 'NOTES', 'STATUS', 'EXPORT_COUNT'
    ]

    # Atomic write
    _atomic_write_csv(csv_path, tasks, fieldnames)
    logger.info(f"Incremented export_count for {len(task_ids)} respiration tasks")


# ============================================================================
# RECURRENT TASKS (TACHES_RECURRENTES.v2.csv)
# ============================================================================

def update_recurrent_task_active(csv_path: Path, task_id: str, is_active: int) -> None:
    """
    Toggle IS_ACTIVE (0 or 1) for recurrent task.

    Args:
        csv_path: Path to TACHES_RECURRENTES.v2.csv
        task_id: ID of task to update
        is_active: 0 (inactive) or 1 (active)

    Raises:
        ValueError: If task_id not found or is_active invalid
        IOError: If write fails
    """
    from backend.planning_engine.data_loader import load_recurrent_tasks

    if is_active not in [0, 1]:
        raise ValueError(f"is_active must be 0 or 1, got {is_active}")

    # Load all recurrent tasks
    tasks = load_recurrent_tasks(csv_path, active_only=False)

    # Find and update task
    task_found = False
    for task in tasks:
        if task['id'] == task_id:
            task['is_active'] = is_active
            task_found = True
            break

    if not task_found:
        raise ValueError(f"Recurrent task {task_id} not found in {csv_path.name}")

    # Fieldnames
    fieldnames = [
        'ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY', 'DURATION_MIN',
        'RECURRENCE_TYPE', 'RECURRENCE_INTERVAL', 'LAST_DONE_DATE', 'NEXT_DUE_DATE',
        'PRIORITY', 'STATUS', 'IS_ACTIVE'
    ]

    # Atomic write
    _atomic_write_csv(csv_path, tasks, fieldnames)
    logger.info(f"Updated recurrent task {task_id} IS_ACTIVE to {is_active}")


# ============================================================================
# PLANNING EXPORT (planned.csv)
# ============================================================================

def write_planning_csv(csv_path: Path, planning: List[Dict]) -> None:
    """
    Write planning to planned.csv (overwrites existing file).

    Args:
        csv_path: Path to planned.csv
        planning: List of planning slots

    Raises:
        IOError: If write fails
    """
    # Fieldnames
    fieldnames = [
        'ID', 'NAME', 'DATE', 'HEURE_DEBUT', 'HEURE_FIN',
        'DURATION_MIN', 'KIND', 'ORIGINAL_TIME'
    ]

    # Convert planning slots to CSV format
    rows = []
    for slot in planning:
        row = {
            'ID': slot.get('task_id', ''),
            'NAME': slot.get('task_name', ''),
            'DATE': slot.get('date', ''),
            'HEURE_DEBUT': slot.get('heure_debut', ''),
            'HEURE_FIN': slot.get('heure_fin', ''),
            'DURATION_MIN': str(slot.get('duration_min', 0)),
            'KIND': slot.get('type', ''),  # pomodoro, respiration, recurrent, planned
            'ORIGINAL_TIME': slot.get('original_time', '')
        }
        rows.append(row)

    # Atomic write
    _atomic_write_csv(csv_path, rows, fieldnames)
    logger.info(f"Exported planning with {len(rows)} slots to {csv_path.name}")


# ============================================================================
# CATEGORIES (categories.csv)
# ============================================================================

def add_category(csv_path: Path, category: str, sub_category: str) -> None:
    """
    Add new category/sub-category pair to categories.csv.

    Args:
        csv_path: Path to categories.csv
        category: Category name
        sub_category: Sub-category name

    Raises:
        IOError: If write fails
    """
    from backend.planning_engine.data_loader import load_categories

    # Load existing categories
    categories_dict = load_categories(csv_path)

    # Add new pair (avoid duplicates)
    if category not in categories_dict:
        categories_dict[category] = []

    if sub_category and sub_category not in categories_dict[category]:
        categories_dict[category].append(sub_category)
        logger.info(f"Added category pair: {category} -> {sub_category}")
    else:
        logger.debug(f"Category pair already exists: {category} -> {sub_category}")

    # Convert back to rows
    rows = []
    for cat, subcats in categories_dict.items():
        for subcat in subcats:
            rows.append({'CATEGORY': cat, 'SUB_CATEGORY': subcat})

    # Fieldnames
    fieldnames = ['CATEGORY', 'SUB_CATEGORY']

    # Atomic write
    _atomic_write_csv(csv_path, rows, fieldnames)
