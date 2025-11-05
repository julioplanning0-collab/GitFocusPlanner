"""
V3 PURE - NO V2 LOGIC ALLOWED

Data export functions with atomic write patterns.

CRITICAL RULES:
- ALL CSV writes MUST be atomic (temp file + rename)
- Format: delimiter=';', quoting=QUOTE_ALL, encoding='utf-8'
- NEVER write directly to target file (prevents corruption)
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


# ==================== CSV EXPORT ====================

def write_planning_csv(csv_path: Path, planning: List[Dict]) -> None:
    """
    Write planning to CSV file using atomic write pattern.

    CRITICAL: Uses temp file + rename to prevent corruption during write.

    Args:
        csv_path: Target CSV file path
        planning: List of display slots with absolute times
                  Format: [{date, heure_debut, heure_fin, task_name, task_id,
                           type, duration_min, pomodoro_index, pomodoro_total, rescheduled}]

    Raises:
        IOError: If write fails

    Example:
        >>> planning = [
        ...     {'date': '2025-11-06', 'heure_debut': '13:25', 'heure_fin': '13:50',
        ...      'task_name': 'Maths', 'task_id': 'TASK001', 'type': 'pomodoro',
        ...      'duration_min': 25, 'pomodoro_index': 1, 'pomodoro_total': 3, 'rescheduled': False}
        ... ]
        >>> write_planning_csv(Path('planning.csv'), planning)
    """
    fieldnames = [
        'date',
        'heure_debut',
        'heure_fin',
        'task_name',
        'task_id',
        'type',
        'duration_min',
        'pomodoro_index',
        'pomodoro_total',
        'rescheduled'
    ]

    # Atomic write: temp file + rename
    temp_file = csv_path.with_suffix('.tmp')

    try:
        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=';',
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()

            # Write rows (fill missing fields with empty string)
            for row in planning:
                row_data = {field: row.get(field, '') for field in fieldnames}
                writer.writerow(row_data)

        # Atomic rename (OS-level guarantee)
        temp_file.replace(csv_path)
        logger.info(f"Planning exported to {csv_path} ({len(planning)} slots)")

    except Exception as e:
        # Clean up temp file on error
        if temp_file.exists():
            temp_file.unlink()
        logger.error(f"Failed to write planning CSV: {e}")
        raise IOError(f"CSV export failed: {e}") from e


def log_pause_usage(planning: List[Dict], export_timestamp: str, data_dir: Path) -> None:
    """
    Log which pauses were used for future intelligent scoring (ML).

    Appends to pause_usage_history.csv for machine learning analysis.
    This is NOT atomic (append-only log file).

    Args:
        planning: List of display slots
        export_timestamp: ISO timestamp of export
        data_dir: Data directory containing history file

    Example:
        >>> planning = [{'type': 'pause', 'task_id': 'REC001', ...}]
        >>> log_pause_usage(planning, '2025-11-06T14:30:00', Path('data/'))
    """
    history_file = data_dir / 'pause_usage_history.csv'

    # Extract pause entries
    pause_entries = []
    for i, slot in enumerate(planning):
        if slot.get('type') == 'pause':
            pause_entries.append({
                'timestamp': export_timestamp,
                'date': slot.get('date', ''),
                'task_id': slot.get('task_id', ''),
                'task_name': slot.get('task_name', ''),
                'placement_order': i,
                'time_placed': slot.get('heure_debut', '')
            })

    if not pause_entries:
        logger.debug("No pauses to log")
        return

    fieldnames = [
        'timestamp',
        'date',
        'task_id',
        'task_name',
        'placement_order',
        'time_placed'
    ]

    try:
        # Check if file exists and is empty
        file_exists = history_file.exists()
        write_header = not file_exists or history_file.stat().st_size == 0

        # Append to history (NOT atomic, append-only file)
        with open(history_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=';',
                quoting=csv.QUOTE_ALL
            )

            if write_header:
                writer.writeheader()

            writer.writerows(pause_entries)

        logger.info(f"Logged {len(pause_entries)} pause usages to {history_file}")

    except Exception as e:
        logger.error(f"Failed to log pause usage: {e}")
        # Don't raise - this is optional logging, shouldn't block export


# ==================== DISPLAY FORMAT CONVERSION ====================

def convert_timeline_to_display(
    timeline: List[Dict],
    planning_start: datetime,
    date: str
) -> List[Dict]:
    """
    Convert timeline with minuteOffsets to display format with absolute times.

    Args:
        timeline: List of TaskV3 with minuteOffset calculated
        planning_start: Planning start datetime
        date: Date string (YYYY-MM-DD)

    Returns:
        List of display slots with absolute times

    Example:
        >>> from datetime import datetime
        >>> timeline = [
        ...     {'minuteOffset': 0, 'duration': 25, 'task_name': 'Maths',
        ...      'task_id': 'TASK001', 'type': 'POMODORO', 'pomodoroIndex': 1, 'pomodoroTotal': 3}
        ... ]
        >>> start = datetime(2025, 11, 6, 13, 25)
        >>> display = convert_timeline_to_display(timeline, start, '2025-11-06')
        >>> display[0]['heure_debut']
        '13:25'
        >>> display[0]['heure_fin']
        '13:50'
    """
    from datetime import timedelta

    display_slots = []

    for task in timeline:
        # Calculate absolute times
        start_dt = planning_start + timedelta(minutes=task['minuteOffset'])
        end_dt = start_dt + timedelta(minutes=task['duration'])

        # Handle day overflow
        task_date = start_dt.strftime('%Y-%m-%d')

        display_slots.append({
            'date': task_date,
            'heure_debut': start_dt.strftime('%H:%M'),
            'heure_fin': end_dt.strftime('%H:%M'),
            'task_name': task.get('taskName', task.get('task_name', '')),
            'task_id': task.get('taskId', task.get('task_id', '')),
            'type': task['type'].lower(),
            'duration_min': task['duration'],
            'pomodoro_index': task.get('pomodoroIndex', task.get('pomodoro_index', '')),
            'pomodoro_total': task.get('pomodoroTotal', task.get('pomodoro_total', '')),
            'rescheduled': task.get('rescheduled', False)
        })

    return display_slots


def calculate_statistics(timeline: List[Dict]) -> Dict:
    """
    Calculate summary statistics from timeline.

    Args:
        timeline: List of TaskV3 with calculated times

    Returns:
        Statistics dict

    Example:
        >>> timeline = [
        ...     {'type': 'POMODORO', 'duration': 25},
        ...     {'type': 'PAUSE', 'duration': 10},
        ...     {'type': 'POMODORO', 'duration': 25}
        ... ]
        >>> stats = calculate_statistics(timeline)
        >>> stats['total_pomodoros']
        2
        >>> stats['total_work_min']
        50
    """
    stats = {
        'total_pomodoros': len([t for t in timeline if t['type'] == 'POMODORO']),
        'total_pauses': len([t for t in timeline if t['type'] == 'PAUSE']),
        'total_calins': len([t for t in timeline if t['type'] == 'CALIN']),
        'total_clopes': len([t for t in timeline if t['type'] == 'CLOPE']),
        'total_planned': len([t for t in timeline if t['type'] == 'PLANNED']),
        'total_work_min': sum(t['duration'] for t in timeline if t['type'] == 'POMODORO'),
        'total_pause_min': sum(t['duration'] for t in timeline if t['type'] in ['PAUSE', 'CALIN', 'CLOPE']),
    }

    # Add start/end times if timeline not empty
    if timeline:
        # Timeline should be sorted by minuteOffset
        stats['planning_start_offset'] = timeline[0]['minuteOffset']
        stats['planning_end_offset'] = timeline[-1]['minuteOffset'] + timeline[-1]['duration']
    else:
        stats['planning_start_offset'] = 0
        stats['planning_end_offset'] = 0

    return stats
