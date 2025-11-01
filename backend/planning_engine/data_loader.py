"""
Data Loader Module - GitFocus Planner V2
Reads all CSV files and returns List[Dict] structures.

CRITICAL RULES:
- ALWAYS specify encoding='utf-8'
- File not found → Return [] + log WARNING (don't crash)
- Invalid CSV row → Skip row + log ERROR
- NO fallbacks, NO rustines: Log errors clearly
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _clean_csv_field(field: str) -> str:
    """
    Remove surrounding quotes from CSV field.

    Args:
        field: Raw CSV field value

    Returns:
        Cleaned string
    """
    if not field:
        return ""

    # Remove quotes at start/end
    field = field.strip()
    if field.startswith('"') and field.endswith('"'):
        field = field[1:-1]

    # Handle escaped double quotes
    field = field.replace('""', '"')

    return field


def _safe_int(value: str, default: int = 0) -> int:
    """
    Safely convert string to int, return default if invalid.

    Args:
        value: String to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        cleaned = _clean_csv_field(value)
        return int(cleaned) if cleaned else default
    except (ValueError, TypeError):
        logger.debug(f"Cannot convert '{value}' to int, using default {default}")
        return default


def _safe_read_csv(csv_path: Path, required: bool = True) -> List[Dict]:
    """
    Safely read CSV file with error handling.

    Args:
        csv_path: Path to CSV file
        required: If True, log WARNING when file missing, else log DEBUG

    Returns:
        List of dictionaries (empty list if file missing/unreadable)
    """
    if not csv_path.exists():
        log_level = logging.WARNING if required else logging.DEBUG
        logger.log(log_level, f"CSV file not found: {csv_path}")
        return []

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            logger.debug(f"Loaded {len(rows)} rows from {csv_path.name}")
            return rows

    except UnicodeDecodeError:
        logger.warning(f"{csv_path.name} not UTF-8, attempting latin-1 conversion")

        try:
            # Read with latin-1
            with open(csv_path, 'r', encoding='latin-1') as f:
                content = f.read()

            # Re-encode to UTF-8
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"{csv_path.name} re-encoded to UTF-8")

            # Retry
            with open(csv_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                rows = list(reader)
                logger.debug(f"Loaded {len(rows)} rows from {csv_path.name} after re-encoding")
                return rows

        except Exception as e:
            logger.error(f"Failed to read {csv_path.name} even after re-encoding: {e}")
            return []

    except Exception as e:
        logger.error(f"Error reading {csv_path.name}: {e}", exc_info=True)
        return []


# ============================================================================
# MAIN LOADERS
# ============================================================================

def load_pomodoro_tasks(csv_path: Path) -> List[Dict]:
    """
    Load Pomodoro work tasks from LISTE_MERE.v2.csv

    Args:
        csv_path: Path to LISTE_MERE.v2.csv

    Returns:
        List of task dictionaries with cleaned fields
    """
    raw_rows = _safe_read_csv(csv_path, required=True)

    tasks = []
    for idx, row in enumerate(raw_rows, start=2):  # Start at 2 (header is 1)
        try:
            # Clean and validate required fields
            task_id = _clean_csv_field(row.get('ID', ''))
            if not task_id:
                logger.error(f"Row {idx} in {csv_path.name}: Missing ID, skipping")
                continue

            task = {
                'id': task_id,
                'name': _clean_csv_field(row.get('NAME', '')),
                'description': _clean_csv_field(row.get('DESCRIPTION', '')),
                'category': _clean_csv_field(row.get('CATEGORY', '')),
                'sub_category': _clean_csv_field(row.get('SUB_CATEGORY', '')),
                'duration_min': _safe_int(row.get('DURATION_MIN', '25'), default=25),
                'remaining_min': _safe_int(row.get('REMAINING_MIN', row.get('DURATION_MIN', '25')), default=25),
                'priority': _safe_int(row.get('PRIORITY', '3'), default=3),
                'tags': _clean_csv_field(row.get('TAGS', '')),
                'keywords': _clean_csv_field(row.get('KEYWORDS', '')),
                'dependencies': _clean_csv_field(row.get('DEPENDENCIES', '')),
                'notes': _clean_csv_field(row.get('NOTES', '')),
                'deadline': _clean_csv_field(row.get('DEADLINE', '')),
                'fixed_start': _clean_csv_field(row.get('FIXED_START', '')),
                'planned_start': _clean_csv_field(row.get('PLANNED_START', '')),
                'status': _clean_csv_field(row.get('STATUS', 'available'))
            }

            tasks.append(task)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(tasks)} Pomodoro tasks from {csv_path.name}")
    return tasks


def load_respiration_tasks(csv_path: Path) -> List[Dict]:
    """
    Load respiration/pause tasks from TACHES_RESPIRATOIRES.v2.csv
    Sorted by EXPORT_COUNT DESC (most popular first)

    Args:
        csv_path: Path to TACHES_RESPIRATOIRES.v2.csv

    Returns:
        List of respiration task dictionaries, sorted by popularity
    """
    raw_rows = _safe_read_csv(csv_path, required=True)

    tasks = []
    for idx, row in enumerate(raw_rows, start=2):
        try:
            task_id = _clean_csv_field(row.get('ID', ''))
            if not task_id:
                logger.error(f"Row {idx} in {csv_path.name}: Missing ID, skipping")
                continue

            task = {
                'id': task_id,
                'name': _clean_csv_field(row.get('NAME', '')),
                'description': _clean_csv_field(row.get('DESCRIPTION', '')),
                'category': _clean_csv_field(row.get('CATEGORY', '')),
                'sub_category': _clean_csv_field(row.get('SUB_CATEGORY', '')),
                'duration_min': _safe_int(row.get('DURATION_MIN', '5'), default=5),
                'repeat_interval_min': _safe_int(row.get('REPEAT_INTERVAL_MIN', '0'), default=0),
                'last_done_timestamp': _clean_csv_field(row.get('LAST_DONE_TIMESTAMP', '')),
                'last_done_date': _clean_csv_field(row.get('LAST_DONE_DATE', '')),
                'earliest_time': _clean_csv_field(row.get('EARLIEST_TIME', '')),
                'latest_time': _clean_csv_field(row.get('LATEST_TIME', '')),
                'ideal_time': _clean_csv_field(row.get('IDEAL_TIME', '')),
                'priority': _safe_int(row.get('PRIORITY', '3'), default=3),
                'tags': _clean_csv_field(row.get('TAGS', '')),
                'keywords': _clean_csv_field(row.get('KEYWORDS', '')),
                'dependencies': _clean_csv_field(row.get('DEPENDENCIES', '')),
                'notes': _clean_csv_field(row.get('NOTES', '')),
                'status': _clean_csv_field(row.get('STATUS', 'available')),
                'export_count': _safe_int(row.get('EXPORT_COUNT', '0'), default=0)
            }

            tasks.append(task)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    # Sort by export_count DESC (most popular first)
    tasks.sort(key=lambda t: t['export_count'], reverse=True)

    logger.info(f"Loaded {len(tasks)} respiration tasks from {csv_path.name} (sorted by popularity)")
    return tasks


def load_recurrent_tasks(csv_path: Path, active_only: bool = False) -> List[Dict]:
    """
    Load recurrent tasks from TACHES_RECURRENTES.v2.csv

    Args:
        csv_path: Path to TACHES_RECURRENTES.v2.csv
        active_only: If True, return only tasks with IS_ACTIVE=1

    Returns:
        List of recurrent task dictionaries
    """
    raw_rows = _safe_read_csv(csv_path, required=True)

    tasks = []
    for idx, row in enumerate(raw_rows, start=2):
        try:
            task_id = _clean_csv_field(row.get('ID', ''))
            if not task_id:
                logger.error(f"Row {idx} in {csv_path.name}: Missing ID, skipping")
                continue

            is_active = _safe_int(row.get('IS_ACTIVE', '1'), default=1)

            # Filter if active_only requested
            if active_only and is_active != 1:
                continue

            task = {
                'id': task_id,
                'name': _clean_csv_field(row.get('NAME', '')),
                'description': _clean_csv_field(row.get('DESCRIPTION', '')),
                'category': _clean_csv_field(row.get('CATEGORY', '')),
                'sub_category': _clean_csv_field(row.get('SUB_CATEGORY', '')),
                'duration_min': _safe_int(row.get('DURATION_MIN', '10'), default=10),
                'recurrence_type': _clean_csv_field(row.get('RECURRENCE_TYPE', 'daily')),
                'recurrence_interval': _safe_int(row.get('RECURRENCE_INTERVAL', '1'), default=1),
                'last_done_date': _clean_csv_field(row.get('LAST_DONE_DATE', '')),
                'next_due_date': _clean_csv_field(row.get('NEXT_DUE_DATE', '')),
                'priority': _safe_int(row.get('PRIORITY', '2'), default=2),
                'status': _clean_csv_field(row.get('STATUS', 'available')),
                'is_active': is_active
            }

            tasks.append(task)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(tasks)} recurrent tasks from {csv_path.name} (active_only={active_only})")
    return tasks


def load_planned_tasks(csv_path: Path, date: Optional[str] = None) -> List[Dict]:
    """
    Load planned tasks (with fixed date/time) from TACHES_PLANIFIEES.v2.csv

    Args:
        csv_path: Path to TACHES_PLANIFIEES.v2.csv
        date: Optional ISO date (YYYY-MM-DD) to filter tasks

    Returns:
        List of planned task dictionaries
    """
    raw_rows = _safe_read_csv(csv_path, required=False)

    tasks = []
    for idx, row in enumerate(raw_rows, start=2):
        try:
            task_id = _clean_csv_field(row.get('ID', ''))
            if not task_id:
                logger.error(f"Row {idx} in {csv_path.name}: Missing ID, skipping")
                continue

            planned_start = _clean_csv_field(row.get('PLANNED_START', ''))

            # Filter by date if requested
            if date and planned_start:
                try:
                    # PLANNED_START format: "DD.MM.YY HH:MM"
                    task_date_part = planned_start.split()[0]  # "DD.MM.YY"
                    task_date = datetime.strptime(task_date_part, "%d.%m.%y").date()
                    target_date = datetime.strptime(date, "%Y-%m-%d").date()

                    if task_date != target_date:
                        continue  # Skip task (wrong date)

                    # 🆕 Filter past tasks for today
                    if task_date == datetime.now().date():
                        # Parse full datetime
                        task_datetime = datetime.strptime(planned_start, "%d.%m.%y %H:%M")
                        now = datetime.now()

                        if task_datetime < now:
                            logger.debug(f"Skipping past planned task: {_clean_csv_field(row.get('NAME', ''))} at {planned_start}")
                            continue  # Skip task (in the past)

                except Exception as e:
                    logger.warning(f"Row {idx} in {csv_path.name}: Invalid PLANNED_START format '{planned_start}': {e}")
                    continue

            task = {
                'id': task_id,
                'name': _clean_csv_field(row.get('NAME', '')),
                'description': _clean_csv_field(row.get('DESCRIPTION', '')),
                'category': _clean_csv_field(row.get('CATEGORY', '')),
                'sub_category': _clean_csv_field(row.get('SUB_CATEGORY', '')),
                'duration_min': _safe_int(row.get('DURATION_MIN', '25'), default=25),
                'remaining_min': _safe_int(row.get('REMAINING_MIN', row.get('DURATION_MIN', '25')), default=25),
                'priority': _safe_int(row.get('PRIORITY', '1'), default=1),
                'tags': _clean_csv_field(row.get('TAGS', '')),
                'keywords': _clean_csv_field(row.get('KEYWORDS', '')),
                'dependencies': _clean_csv_field(row.get('DEPENDENCIES', '')),
                'notes': _clean_csv_field(row.get('NOTES', '')),
                'deadline': _clean_csv_field(row.get('DEADLINE', '')),
                'fixed_start': _clean_csv_field(row.get('FIXED_START', '')),
                'planned_start': planned_start,
                'status': _clean_csv_field(row.get('STATUS', 'available'))
            }

            tasks.append(task)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(tasks)} planned tasks from {csv_path.name} (date={date or 'all'})")
    return tasks


def load_temps_morts(csv_path: Path, date: str) -> List[Dict]:
    """
    Load blocked time slots from temps_morts.csv for specific date

    Args:
        csv_path: Path to temps_morts.csv
        date: ISO date (YYYY-MM-DD) to filter

    Returns:
        List of temps_mort dictionaries for the date
    """
    raw_rows = _safe_read_csv(csv_path, required=False)

    temps_morts = []
    for idx, row in enumerate(raw_rows, start=2):
        try:
            tm_date = _clean_csv_field(row.get('DATE', ''))

            # Filter by date
            if tm_date != date:
                continue

            temps_mort = {
                'date': tm_date,
                'heure_debut': _clean_csv_field(row.get('HEURE DEBUT', row.get('HEURE_DEBUT', ''))),
                'heure_fin': _clean_csv_field(row.get('HEURE FIN', row.get('HEURE_FIN', ''))),
                'titre': _clean_csv_field(row.get('TITRE', ''))
            }

            # Validate time format
            if not temps_mort['heure_debut'] or not temps_mort['heure_fin']:
                logger.warning(f"Row {idx} in {csv_path.name}: Missing time, skipping")
                continue

            temps_morts.append(temps_mort)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(temps_morts)} temps_morts for date {date}")
    return temps_morts


def load_categories(csv_path: Path) -> Dict[str, List[str]]:
    """
    Load categories from categories.csv

    Args:
        csv_path: Path to categories.csv

    Returns:
        Dictionary mapping category -> list of sub-categories
        Example: {"Maison": ["Jardinage", "Rangement"], ...}
    """
    raw_rows = _safe_read_csv(csv_path, required=True)

    categories_dict = {}
    for idx, row in enumerate(raw_rows, start=2):
        try:
            category = _clean_csv_field(row.get('CATEGORY', ''))
            sub_category = _clean_csv_field(row.get('SUB_CATEGORY', ''))

            if not category:
                logger.warning(f"Row {idx} in {csv_path.name}: Missing CATEGORY, skipping")
                continue

            if category not in categories_dict:
                categories_dict[category] = []

            if sub_category and sub_category not in categories_dict[category]:
                categories_dict[category].append(sub_category)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(categories_dict)} categories with sub-categories")
    return categories_dict


def load_planning_history(csv_path: Path) -> List[Dict]:
    """
    🆕 Load planning placements history from planning_placements_history.csv
    Used for intelligent scoring (learning system)

    Args:
        csv_path: Path to planning_placements_history.csv

    Returns:
        List of placement records
    """
    raw_rows = _safe_read_csv(csv_path, required=False)  # Not required (file may be empty initially)

    placements = []
    for idx, row in enumerate(raw_rows, start=2):
        try:
            placement = {
                'task_id': _clean_csv_field(row.get('TASK_ID', '')),
                'task_name': _clean_csv_field(row.get('TASK_NAME', '')),
                'date': _clean_csv_field(row.get('DATE', '')),
                'planned_time': _clean_csv_field(row.get('PLANNED_TIME', '')),
                'day_of_week': _safe_int(row.get('DAY_OF_WEEK', '0'), default=0),
                'week_type': _clean_csv_field(row.get('WEEK_TYPE', '')),
                'mood': _clean_csv_field(row.get('MOOD', '')),
                'energy': _clean_csv_field(row.get('ENERGY', '')),
                'weather': _clean_csv_field(row.get('WEATHER', '')),
                'season': _clean_csv_field(row.get('SEASON', '')),
                'export_timestamp': _clean_csv_field(row.get('EXPORT_TIMESTAMP', ''))
            }

            placements.append(placement)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(placements)} placement records from planning history")
    return placements


def load_done_history(csv_path: Path) -> List[Dict]:
    """
    🆕 Load task completion history from done_v2.csv
    Used for calculating recurrence scores (when task was last done)

    Args:
        csv_path: Path to done_v2.csv

    Returns:
        List of done task records
    """
    raw_rows = _safe_read_csv(csv_path, required=False)

    done_tasks = []
    for idx, row in enumerate(raw_rows, start=2):
        try:
            done_task = {
                'ID': _clean_csv_field(row.get('ID', '')),
                'NAME': _clean_csv_field(row.get('NAME', '')),
                'DONE_AT': _clean_csv_field(row.get('DONE_AT', '')),
                'DURATION_MIN': _safe_int(row.get('DURATION_MIN', '0'), default=0),
                'TYPE': _clean_csv_field(row.get('TYPE', ''))
            }

            done_tasks.append(done_task)

        except Exception as e:
            logger.error(f"Row {idx} in {csv_path.name}: Error parsing row: {e}", exc_info=True)
            continue

    logger.info(f"Loaded {len(done_tasks)} done task records from history")
    return done_tasks
