"""
V3 PURE - NO V2 LOGIC ALLOWED

Data loading functions for V3 with unified recurrent tasks.

KEY CHANGES FROM V2:
- Single TACHES_RECURRENTES.v3.csv with IS_PAUSE field:
  - IS_PAUSE = 1 → Pause tasks (short breaks 5-20min)
  - IS_PAUSE = 0 → True recurrent tasks
- Returns List[Dict] (NO Pydantic, pure backend logic)
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from .types_v3 import TaskV3, Obstacle  # V3 types for type hints
from datetime import datetime

logger = logging.getLogger(__name__)

# CSV Format Configuration
CSV_DELIMITER = ';'
CSV_ENCODING = 'utf-8'


# ==================== PATH CONFIGURATION ====================

def get_prod_data_path() -> Path:
    """
    Get production data directory path.

    Returns:
        Path to production data directory
    """
    # V3 Pure: data in GitfocusPlanner/data/prod_data
    project_root = Path(__file__).parent.parent.parent
    return project_root / 'data' / 'prod_data'


def get_csv_path(filename: str) -> Path:
    """
    Get full path to CSV file.

    Args:
        filename: CSV filename (e.g., "LISTE_MERE.v2.csv")

    Returns:
        Full path to CSV file
    """
    return get_prod_data_path() / filename


# ==================== CSV READING (CORE) ====================

def read_csv_file(csv_path: Path, encoding: str = CSV_ENCODING) -> List[Dict]:
    """
    Read CSV file and return list of dicts.

    Args:
        csv_path: Path to CSV file
        encoding: File encoding (default: utf-8)

    Returns:
        List of dicts (one per row, keys = column names)
        Empty list if file not found or error

    CSV Format:
        - Delimiter: ; (semicolon)
        - Quoting: QUOTE_ALL
        - Encoding: UTF-8
    """
    if not csv_path.exists():
        logger.warning(f"CSV not found: {csv_path}")
        return []

    try:
        with open(csv_path, 'r', newline='', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
            rows = list(reader)
            logger.info(f"Loaded {len(rows)} rows from {csv_path.name}")
            return rows

    except UnicodeDecodeError:
        # Retry with latin-1 encoding
        logger.warning(f"UTF-8 decode failed for {csv_path}, retrying with latin-1")
        try:
            with open(csv_path, 'r', newline='', encoding='latin-1') as f:
                reader = csv.DictReader(f, delimiter=CSV_DELIMITER)
                rows = list(reader)
                logger.info(f"Loaded {len(rows)} rows from {csv_path.name} (latin-1)")
                return rows
        except Exception as e:
            logger.error(f"Failed to read {csv_path} with latin-1: {e}")
            return []

    except Exception as e:
        logger.error(f"Error reading {csv_path}: {e}")
        return []


# ==================== POMODORO TASKS ====================

def load_pomodoro_tasks() -> List[Dict]:
    """
    Load Pomodoro tasks from LISTE_MERE.v3.csv.

    Returns:
        List of task dicts with fields:
        - CODE_TACHE: Unique ID (e.g., "TASK001")
        - NOM_TACHE: Task name
        - DUREE_MIN: Duration in minutes
        - STATUS: Task status
        - ... other fields
    """
    csv_path = get_csv_path("LISTE_MERE.v3.csv")
    return read_csv_file(csv_path)


def load_pomodoro_task_by_id(task_id: str) -> Optional[Dict]:
    """
    Load single Pomodoro task by ID.

    Args:
        task_id: Task ID (CODE_TACHE)

    Returns:
        Task dict or None if not found
    """
    tasks = load_pomodoro_tasks()
    for task in tasks:
        if task.get('CODE_TACHE') == task_id:
            return task
    return None


def load_pomodoro_tasks_by_ids(task_ids: List[str]) -> List[Dict]:
    """
    Load multiple Pomodoro tasks by IDs (preserves order).

    Args:
        task_ids: List of task IDs to load

    Returns:
        List of task dicts in same order as task_ids
        Skip missing IDs with warning
    """
    all_tasks = load_pomodoro_tasks()
    task_dict = {task['CODE_TACHE']: task for task in all_tasks}

    result = []
    for task_id in task_ids:
        if task_id in task_dict:
            result.append(task_dict[task_id])
        else:
            logger.warning(f"Pomodoro task not found: {task_id}")

    return result


# ==================== RECURRENT TASKS (WITH IS_PAUSE) ====================

def load_recurrent_tasks_v3(
    include_pauses: bool = True,
    include_recurrent: bool = True,
    active_only: bool = True
) -> List[Dict]:
    """
    ✅ V3 UNIFIED LOADER - Load tasks from TACHES_RECURRENTES.v3.csv.

    V3 CHANGE: Single CSV with IS_PAUSE field (NO separate respiration file).

    Args:
        include_pauses: Include tasks with IS_PAUSE=1 (former respirations)
        include_recurrent: Include tasks with IS_PAUSE=0 (true recurrents)
        active_only: Filter by IS_ACTIVE=1

    Returns:
        List of task dicts with fields:
        - CODE_RECURRENCE: Unique ID (e.g., "REC001")
        - NOM_TACHE: Task name
        - DUREE_MIN: Duration in minutes
        - IS_PAUSE: 1 = pause, 0 = recurrent (✅ NEW IN V3)
        - IS_ACTIVE: 1 = active, 0 = inactive
        - ... other fields

    Examples:
        load_recurrent_tasks_v3(include_pauses=True, include_recurrent=False)
        → Only pauses (IS_PAUSE=1)

        load_recurrent_tasks_v3(include_pauses=False, include_recurrent=True)
        → Only recurrents (IS_PAUSE=0)

        load_recurrent_tasks_v3()
        → All active tasks (pauses + recurrents)
    """
    csv_path = get_csv_path("TACHES_RECURRENTES.v3.csv")
    tasks = read_csv_file(csv_path)

    filtered = []
    for task in tasks:
        # Filter by IS_ACTIVE
        if active_only and task.get('IS_ACTIVE') != '1':
            continue

        # Filter by IS_PAUSE
        is_pause = task.get('IS_PAUSE') == '1'
        if is_pause and not include_pauses:
            continue
        if not is_pause and not include_recurrent:
            continue

        filtered.append(task)

    logger.info(
        f"Loaded {len(filtered)} recurrent tasks "
        f"(pauses={include_pauses}, recurrent={include_recurrent}, active={active_only})"
    )
    return filtered


def load_pause_tasks_v3() -> List[Dict]:
    """
    Load ONLY pause tasks (IS_PAUSE=1).

    Shortcut for load_recurrent_tasks_v3(include_pauses=True, include_recurrent=False)
    """
    return load_recurrent_tasks_v3(include_pauses=True, include_recurrent=False)


def load_true_recurrent_tasks_v3() -> List[Dict]:
    """
    Load ONLY true recurrent tasks (IS_PAUSE=0).

    Shortcut for load_recurrent_tasks_v3(include_pauses=False, include_recurrent=True)
    """
    return load_recurrent_tasks_v3(include_pauses=False, include_recurrent=True)


def load_recurrent_tasks_by_ids_v3(task_ids: List[str]) -> List[Dict]:
    """
    Load multiple recurrent tasks by IDs (preserves order & duplicates).

    ✅ V3 FEATURE: Preserves duplicates (important for drag & drop pauses).

    Args:
        task_ids: List of task IDs (can contain duplicates)
                  Example: ["REC001", "REC003", "REC001"]

    Returns:
        List of task dicts in same order (with duplicates)
        Skip missing IDs with warning

    Example:
        load_recurrent_tasks_by_ids_v3(["REC001", "REC003", "REC001"])
        → Returns [task_001, task_003, task_001] (duplicate preserved)
    """
    all_tasks = load_recurrent_tasks_v3(include_pauses=True, include_recurrent=True)

    # Support both old format (CODE_RECURRENCE) and new format (ID)
    task_dict = {}
    for task in all_tasks:
        task_id = task.get('ID', task.get('CODE_RECURRENCE', ''))
        if task_id:
            task_dict[task_id] = task

    result = []
    for task_id in task_ids:
        if task_id in task_dict:
            # Important: Create copy to allow duplicates
            result.append(task_dict[task_id].copy())
        else:
            logger.warning(f"Recurrent task not found: {task_id}")

    return result


# ==================== PLANNED TASKS ====================

def load_planned_tasks(date: str) -> List[Dict]:
    """
    Load planned tasks for specific date.

    Args:
        date: Date string (YYYY-MM-DD)

    Returns:
        List of planned task dicts with fields:
        - CODE_TACHE: Task ID
        - NOM_TACHE: Task name
        - DATE: Date (YYYY-MM-DD)
        - HEURE_DEBUT: Start time (HH:MM)
        - DUREE_MIN: Duration in minutes
        - ... other fields
    """
    csv_path = get_csv_path("TACHES_PLANIFIEES.v2.csv")
    all_tasks = read_csv_file(csv_path)

    # Filter by date
    filtered = [task for task in all_tasks if task.get('DATE') == date]

    logger.info(f"Loaded {len(filtered)} planned tasks for {date}")
    return filtered


# ==================== TEMPS MORTS ====================

def load_temps_morts(date: str) -> List[Dict]:
    """
    Load temps morts (obstacles) for specific date.

    Args:
        date: Date string (YYYY-MM-DD)

    Returns:
        List of temps mort dicts with fields:
        - date: Date (YYYY-MM-DD)
        - heure_debut: Start time (HH:MM)
        - heure_fin: End time (HH:MM)
        - titre: Event title
        - ... other fields
    """
    csv_path = get_csv_path("temps_morts.csv")
    all_temps_morts = read_csv_file(csv_path)

    # Filter by date (CSV uses 'DATE' in uppercase)
    filtered = [tm for tm in all_temps_morts if tm.get('DATE', tm.get('date')) == date]

    logger.info(f"Loaded {len(filtered)} temps morts for {date}")
    return filtered


# ==================== VALIDATION HELPERS ====================

def validate_task_fields(task: Dict, required_fields: List[str]) -> bool:
    """
    Check if task has all required fields.

    Args:
        task: Task dict
        required_fields: List of required field names

    Returns:
        True if all fields present, False otherwise
    """
    for field in required_fields:
        if field not in task or not task[field]:
            logger.error(f"Missing required field '{field}' in task: {task}")
            return False
    return True


# ==================== PUBLIC API FUNCTIONS (for routes_v3.py) ====================

def load_all_pomodoro_tasks(csv_path: Path) -> List[Dict]:
    """
    Load ALL pomodoro tasks from LISTE_MERE.v3.csv.

    Used by API endpoint GET /api/v3/tasks/pomodoro

    Returns:
        List of all pomodoro task dicts (active and inactive)
    """
    return read_csv_file(csv_path)


def load_all_recurrent_tasks(csv_path: Path) -> List[Dict]:
    """
    Load ALL recurrent tasks from TACHES_RECURRENTES.v3.csv.

    Used by API endpoint GET /api/v3/tasks/recurrent

    Returns:
        List of all recurrent task dicts (includes IS_PAUSE field)
    """
    return read_csv_file(csv_path)


# ==================== HELPER FUNCTIONS ====================

def get_task_duration_minutes(task: Dict) -> int:
    """
    Extract duration from task dict.

    Args:
        task: Task dict with DURATION_MIN or DUREE_MIN field

    Returns:
        Duration in minutes (default: 0 if invalid)
    """
    try:
        # Support both new format (DURATION_MIN) and old format (DUREE_MIN)
        duration = task.get('DURATION_MIN', task.get('DUREE_MIN', 0))
        return int(duration)
    except (ValueError, TypeError):
        logger.warning(f"Invalid DURATION_MIN/DUREE_MIN in task: {task}")
        return 0


def get_task_name(task: Dict) -> str:
    """
    Extract task name from dict.

    Args:
        task: Task dict with NAME or NOM_TACHE field

    Returns:
        Task name (default: "Unnamed" if missing)
    """
    # Support both new format (NAME) and old format (NOM_TACHE)
    return task.get('NAME', task.get('NOM_TACHE', 'Unnamed'))


def get_task_id(task: Dict) -> str:
    """
    Extract task ID from dict (works for all task types).

    Args:
        task: Task dict

    Returns:
        Task ID from ID, CODE_TACHE, CODE_RECURRENCE, or "UNKNOWN"
    """
    # Support new format (ID) and old formats (CODE_TACHE, CODE_RECURRENCE)
    return task.get('ID') or task.get('CODE_TACHE') or task.get('CODE_RECURRENCE') or 'UNKNOWN'
