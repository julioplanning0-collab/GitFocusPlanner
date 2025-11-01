"""
Planning Generator Module - GitFocus Planner V2
Main orchestrator for intelligent Pomodoro planning generation.

ALGORITHM (9 Steps):
1. Validate inputs
2. Load all data sources (CSV files)
3. Calculate free time slots
4. Score recurrent tasks (🆕 intelligent scoring)
5. Generate base planning (Pomodoro ↔ Recurrent alternation)
6. Integrate planned tasks (fixed time)
7. Repair alternation violations
8. Recalculate times (skip temps_morts)
9. Calculate statistics

Returns complete planning ready for export.
"""

import logging
import math
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_planning_auto(
    date: str,
    pomodoro_ids: List[str],
    data_dir: Path,
    max_recurrent_tasks: int = 10
) -> Dict:
    """
    Generate daily planning with automatic recurrent task selection (🆕).

    This is the main entry point with intelligent scoring.

    Args:
        date: Target date (YYYY-MM-DD)
        pomodoro_ids: List of selected Pomodoro task IDs
        data_dir: Path to prod_data/ directory
        max_recurrent_tasks: Max number of recurrent tasks to select (default 10)

    Returns:
        {
            "date": "2025-10-30",
            "planning": [...],  # List of slots
            "stats": {...},
            "recurrent_task_scores": [...]  # 🆕 Transparency (show scores)
        }

    Raises:
        ValueError: If inputs invalid
        FileNotFoundError: If required CSV missing
    """
    # ========================================================================
    # STEP 0: Validate Inputs
    # ========================================================================
    _validate_inputs(date, pomodoro_ids)

    # ========================================================================
    # STEP 1: Load All Data Sources
    # ========================================================================
    logger.info(f"=== Starting planning generation for {date} ===")

    from backend.planning_engine.data_loader import (
        load_pomodoro_tasks,
        load_recurrent_tasks,
        load_planned_tasks,
        load_temps_morts,
        load_planning_history,
        load_done_history
    )

    # Pomodoro tasks (user-selected)
    all_pomodoro = load_pomodoro_tasks(data_dir / 'LISTE_MERE.v2.csv')
    logger.info(f"🔍 DEBUG: Loaded {len(all_pomodoro)} total Pomodoro tasks from CSV")
    logger.info(f"🔍 DEBUG: Filtering tasks with IDs in {pomodoro_ids}")

    selected_pomodoro = [t for t in all_pomodoro if t['id'] in pomodoro_ids]
    logger.info(f"🔍 DEBUG: Selected {len(selected_pomodoro)} Pomodoro tasks: {[t['id'] + ':' + t['name'] for t in selected_pomodoro]}")

    if len(selected_pomodoro) == 0:
        logger.warning("No Pomodoro tasks selected, planning will be empty")

    # All active recurrent tasks
    all_recurrent = load_recurrent_tasks(data_dir / 'TACHES_RECURRENTES.v2.csv', active_only=True)

    # Planned tasks (fixed time) for this date
    planned_tasks = load_planned_tasks(data_dir / 'TACHES_PLANIFIEES.v2.csv', date=date)

    # Temps morts (blocked slots) for this date
    temps_morts = load_temps_morts(data_dir / 'temps_morts.csv', date)

    # History for scoring (🆕)
    planning_history = load_planning_history(data_dir / 'planning_placements_history.csv')
    done_history = load_done_history(data_dir / 'done_v2.csv')

    logger.info(f"Loaded: {len(selected_pomodoro)} Pomodoro, {len(all_recurrent)} recurrent, {len(planned_tasks)} planned, {len(temps_morts)} temps_morts")

    # ========================================================================
    # STEP 2: Calculate Free Time Slots
    # ========================================================================
    from backend.planning_engine.slot_calculator import calculate_free_slots

    free_slots = calculate_free_slots(date, temps_morts)
    logger.info(f"🔍 DEBUG: Found {len(free_slots)} free 30-min slots")
    if free_slots:
        logger.info(f"🔍 DEBUG: First free slot: {free_slots[0]['heure_debut']}")
        logger.info(f"🔍 DEBUG: Last free slot: {free_slots[-1]['heure_debut']}-{free_slots[-1]['heure_fin']}")
    logger.info(f"Found {len(free_slots)} free 30-min slots")

    if len(free_slots) == 0:
        logger.warning("No free slots available, returning empty planning")
        return {
            'date': date,
            'planning': [],
            'stats': _calculate_stats([]),
            'recurrent_task_scores': []
        }

    # ========================================================================
    # STEP 3: Score Recurrent Tasks (🆕 Intelligent Selection)
    # ========================================================================
    from backend.planning_engine.smart_scorer import score_all_recurrent_tasks

    scored_tasks = score_all_recurrent_tasks(all_recurrent, date, planning_history, done_history)

    # Select top N
    top_scored = scored_tasks[:max_recurrent_tasks]
    selected_recurrent = [st['task'] for st in top_scored]

    logger.info(f"Selected top {len(selected_recurrent)} recurrent tasks (scores: {[st['score'] for st in top_scored]})")

    # ========================================================================
    # STEP 4: Generate Base Planning (Alternation)
    # ========================================================================
    # Support multi-day: continue on next day if needed
    planning = _generate_multiday_planning(
        selected_pomodoro, selected_recurrent, free_slots, date,
        data_dir, temps_morts, max_days=2
    )

    logger.info(f"Generated base planning with {len(planning)} slots")

    # ========================================================================
    # STEP 5: Integrate Planned Tasks (Fixed Time)
    # ========================================================================
    has_planned_tasks = False
    if planned_tasks:
        from backend.planning_engine.task_integrator import integrate_planned_tasks

        planning = integrate_planned_tasks(planning, planned_tasks, date)
        logger.info(f"Integrated {len(planned_tasks)} planned tasks")
        has_planned_tasks = True

    # ========================================================================
    # STEP 6: Repair Alternation Violations
    # ========================================================================
    from backend.planning_engine.task_integrator import repair_consecutive_work_tasks

    planning = repair_consecutive_work_tasks(planning)

    # ========================================================================
    # STEP 7: Recalculate Times (Skip temps_morts)
    # ========================================================================
    # Only recalculate if we integrated planned tasks (which may have broken continuity)
    # Otherwise, times from _generate_base_planning are already correct
    # NOTE: Skip recalculate for multi-day planning (it only handles single day)
    has_multiday = len(set(slot.get('date') for slot in planning)) > 1
    if has_planned_tasks and not has_multiday:
        from backend.planning_engine.task_integrator import recalculate_times
        planning = recalculate_times(planning, date, temps_morts)
        logger.info("Recalculated times after integrating planned tasks")
    elif has_multiday:
        logger.info("Skipping recalculate_times (multi-day planning, times already correct)")
    else:
        logger.info("Skipping recalculate_times (no planned tasks integrated, times already correct)")

    # ========================================================================
    # STEP 8: Calculate Statistics
    # ========================================================================
    stats = _calculate_stats(planning)

    # ========================================================================
    # STEP 9: Format Response
    # ========================================================================
    logger.info(f"=== Planning generation complete: {len(planning)} slots, {stats['work_minutes']} min work ===")

    return {
        'date': date,
        'planning': planning,
        'stats': stats,
        'recurrent_task_scores': [
            {'task_id': st['task']['id'], 'task_name': st['task']['name'], 'score': st['score']}
            for st in top_scored
        ]
    }


# ============================================================================
# INTERNAL FUNCTIONS
# ============================================================================

def _validate_inputs(date: str, pomodoro_ids: List[str]) -> None:
    """
    Validate inputs.

    Args:
        date: ISO date (YYYY-MM-DD)
        pomodoro_ids: List of task IDs

    Raises:
        ValueError: If inputs invalid
    """
    # Validate date format
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
        raise ValueError(f"Invalid date format: '{date}'. Expected YYYY-MM-DD")

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date: '{date}': {e}") from e

    # Validate pomodoro_ids type
    if not isinstance(pomodoro_ids, list):
        raise TypeError(f"pomodoro_ids must be list, got {type(pomodoro_ids)}")

    logger.debug(f"Inputs validated: date={date}, pomodoro_ids={pomodoro_ids}")


def _generate_multiday_planning(
    pomodoro_tasks: List[Dict],
    recurrent_tasks: List[Dict],
    free_slots: List[Dict],
    date: str,
    data_dir: Path,
    temps_morts: List[Dict],
    max_days: int = 2
) -> List[Dict]:
    """
    Generate planning across multiple days if needed.

    Args:
        pomodoro_tasks: Pomodoro tasks to place
        recurrent_tasks: Recurrent tasks
        free_slots: Free slots for day 1
        date: Starting date (YYYY-MM-DD)
        data_dir: Data directory for loading temps_morts
        temps_morts: Temps morts for day 1
        max_days: Maximum number of days to generate (default 2)

    Returns:
        Planning across multiple days
    """
    from datetime import datetime, timedelta
    from backend.planning_engine.slot_calculator import calculate_free_slots
    from backend.planning_engine.data_loader import load_temps_morts

    all_planning = []
    current_date = date
    current_pomodoro = pomodoro_tasks[:]  # Copy

    for day_offset in range(max_days):
        if day_offset > 0:
            # Calculate next date
            current_date_obj = datetime.strptime(date, "%Y-%m-%d")
            next_date_obj = current_date_obj + timedelta(days=day_offset)
            current_date = next_date_obj.strftime("%Y-%m-%d")

            # Load temps_morts for next day
            temps_morts_next = load_temps_morts(data_dir / 'temps_morts.csv', current_date)
            logger.info(f"Multi-day: Day {day_offset+1} ({current_date}) - Loaded {len(temps_morts_next)} temps_morts")
            if temps_morts_next:
                for tm in temps_morts_next[:3]:  # Log first 3
                    logger.info(f"  - Temps mort: {tm.get('heure_debut')}-{tm.get('heure_fin')} ({tm.get('title', 'N/A')})")

            free_slots = calculate_free_slots(current_date, temps_morts_next)
            logger.info(f"Multi-day: Day {day_offset+1} ({current_date}) - {len(free_slots)} free slots")
            if free_slots:
                logger.info(f"  - First free slot: {free_slots[0]['heure_debut']}-{free_slots[0]['heure_fin']}")
                logger.info(f"  - Last free slot: {free_slots[-1]['heure_debut']}-{free_slots[-1]['heure_fin']}")

        # Generate planning for this day
        day_planning = _generate_base_planning(current_pomodoro, recurrent_tasks, free_slots, current_date)

        all_planning.extend(day_planning)
        logger.info(f"Multi-day: Day {day_offset+1} generated {len(day_planning)} slots")

        # Count how many Pomodoros of each task were placed
        placed_counts = {}
        for slot in day_planning:
            if slot.get('type') == 'pomodoro':
                task_id = slot.get('task_id')
                placed_counts[task_id] = placed_counts.get(task_id, 0) + 1

        # Calculate remaining Pomodoros
        remaining_pomodoro = []
        for pomo in current_pomodoro:
            placed = placed_counts.get(pomo['id'], 0)
            remaining_min = pomo.get('remaining_min', pomo.get('duration_min', 25))
            total_pomodoros = (remaining_min + 24) // 25
            remaining_pomodoros = total_pomodoros - placed

            if remaining_pomodoros > 0:
                # Create new dict with updated remaining_min
                remaining_task = pomo.copy()
                remaining_task['remaining_min'] = remaining_pomodoros * 25
                remaining_pomodoro.append(remaining_task)

        if not remaining_pomodoro:
            logger.info(f"Multi-day: All Pomodoros placed after {day_offset+1} day(s)")
            break

        logger.info(f"Multi-day: {len(remaining_pomodoro)} Pomodoro tasks remaining for next day")
        current_pomodoro = remaining_pomodoro

    return all_planning


def _generate_base_planning(
    pomodoro_tasks: List[Dict],
    recurrent_tasks: List[Dict],
    free_slots: List[Dict],
    date: str
) -> List[Dict]:
    """
    Generate base planning with Pomodoro ↔ Recurrent alternation.

    Args:
        pomodoro_tasks: Selected Pomodoro tasks
        recurrent_tasks: Selected recurrent tasks (scored)
        free_slots: Available time slots
        date: Target date

    Returns:
        List of planning slots
    """
    from backend.planning_engine.task_integrator import generate_slot_id, reset_slot_id_counter

    reset_slot_id_counter()

    planning = []
    slot_index = 0
    recurrent_index = 0

    # Sort Pomodoro by priority (1=High → 3=Low), then by deadline
    pomodoro_tasks_sorted = sorted(
        pomodoro_tasks,
        key=lambda t: (t.get('priority', 3), t.get('deadline', '99.99.99'))
    )

    logger.info(f"🔍 DEBUG: _generate_base_planning called with {len(pomodoro_tasks)} Pomodoro tasks")
    logger.info(f"🔍 DEBUG: After sorting: {[t['id'] + ':' + t['name'] for t in pomodoro_tasks_sorted]}")
    logger.info(f"🔍 DEBUG: Available free slots: {len(free_slots)}")

    # Track current time instead of relying on slot indices
    from datetime import datetime, timedelta
    target_date_obj = datetime.strptime(date, "%Y-%m-%d").date()

    if free_slots:
        current_time = datetime.combine(target_date_obj, datetime.strptime(free_slots[0]['heure_debut'], "%H:%M").time())
    else:
        return planning  # No free slots, return empty planning

    # Define day bounds (truncate at 23:59)
    max_time = datetime.combine(target_date_obj, datetime.max.time().replace(hour=23, minute=59, second=59))

    # Track current free slot index
    free_slot_index = 0
    current_free_slot_end = datetime.combine(target_date_obj, datetime.strptime(free_slots[0]['heure_fin'], "%H:%M").time())

    def advance_to_next_free_slot(current_t, duration_needed_min):
        """Advance to next free slot if current time + duration would exceed current slot."""
        nonlocal free_slot_index, current_free_slot_end

        # Check if we have enough space in current slot
        required_end = current_t + timedelta(minutes=duration_needed_min)

        # If we fit in current slot, no need to advance
        if required_end <= current_free_slot_end:
            return current_t

        # Otherwise, move to next free slot
        free_slot_index += 1
        if free_slot_index >= len(free_slots):
            # No more free slots - return None to signal stop
            logger.info(f"🔍 DEBUG: No more free slots available, stopping planning")
            return None

        next_slot = free_slots[free_slot_index]
        next_slot_start = datetime.combine(target_date_obj, datetime.strptime(next_slot['heure_debut'], "%H:%M").time())
        current_free_slot_end = datetime.combine(target_date_obj, datetime.strptime(next_slot['heure_fin'], "%H:%M").time())
        return next_slot_start

    # Generate slots
    for pomo_task in pomodoro_tasks_sorted:
        # Calculate required Pomodoros
        remaining_min = pomo_task.get('remaining_min', pomo_task.get('duration_min', 25))
        nb_pomodoros = math.ceil(remaining_min / 25)

        logger.info(f"🔍 DEBUG: Processing task {pomo_task['id']}:{pomo_task['name']} - {remaining_min}min → {nb_pomodoros} Pomodoros")

        for i in range(nb_pomodoros):
            # Advance to next free slot if needed
            current_time = advance_to_next_free_slot(current_time, 25)
            if current_time is None:
                logger.warning(f"🔍 DEBUG: No more free slots available, stopping planning generation")
                return planning

            # Add Pomodoro slot
            pomodoro_end = current_time + timedelta(minutes=25)

            # Check if exceeds day bounds (23:59)
            if pomodoro_end > max_time:
                logger.warning(f"Planning exceeds day bounds at {current_time.strftime('%H:%M')}, truncating")
                return planning

            planning.append({
                'id': generate_slot_id(),
                'heure_debut': current_time.strftime('%H:%M'),
                'heure_fin': pomodoro_end.strftime('%H:%M'),
                'type': 'pomodoro',
                'task_id': pomo_task['id'],
                'task_name': pomo_task['name'],
                'category': pomo_task.get('category', ''),
                'sub_category': pomo_task.get('sub_category', ''),
                'pomodoro_num': i + 1,
                'total_pomodoros': nb_pomodoros,
                'duration_min': 25,
                'date': current_time.strftime('%Y-%m-%d')
            })
            current_time = pomodoro_end

            if not recurrent_tasks:
                # No recurrent tasks, add default pause
                # Advance to next free slot if needed
                current_time = advance_to_next_free_slot(current_time, 5)
                if current_time is None:
                    logger.warning(f"🔍 DEBUG: No more free slots for pause, stopping")
                    return planning

                pause_end = current_time + timedelta(minutes=5)

                # Check if exceeds day bounds (23:59)
                if pause_end > max_time:
                    logger.warning(f"Pause exceeds day bounds at {current_time.strftime('%H:%M')}, truncating")
                    return planning

                planning.append({
                    'id': generate_slot_id(),
                    'heure_debut': current_time.strftime('%H:%M'),
                    'heure_fin': pause_end.strftime('%H:%M'),
                    'type': 'pause',
                    'task_id': 'default_pause',
                    'task_name': 'Pause',
                    'duration_min': 5,
                    'date': current_time.strftime('%Y-%m-%d')
                })
                current_time = pause_end
            else:
                # Cycle through recurrent tasks
                recurrent_task = recurrent_tasks[recurrent_index % len(recurrent_tasks)]
                recurrent_index += 1

                recurrent_duration = recurrent_task['duration_min']

                # Advance to next free slot if needed
                current_time = advance_to_next_free_slot(current_time, recurrent_duration)
                if current_time is None:
                    logger.warning(f"🔍 DEBUG: No more free slots for recurrent task, stopping")
                    return planning

                recurrent_end = current_time + timedelta(minutes=recurrent_duration)

                # Check if exceeds day bounds (23:59)
                if recurrent_end > max_time:
                    logger.warning(f"Recurrent task exceeds day bounds at {current_time.strftime('%H:%M')}, truncating")
                    return planning

                planning.append({
                    'id': generate_slot_id(),
                    'heure_debut': current_time.strftime('%H:%M'),
                    'heure_fin': recurrent_end.strftime('%H:%M'),
                    'type': 'recurrent',
                    'task_id': recurrent_task['id'],
                    'task_name': recurrent_task['name'],
                    'category': recurrent_task.get('category', ''),
                    'sub_category': recurrent_task.get('sub_category', ''),
                    'duration_min': recurrent_duration,
                    'date': current_time.strftime('%Y-%m-%d')
                })
                current_time = recurrent_end

    return planning


def _calculate_end_time(start_time: str, duration_min: int) -> str:
    """
    Calculate end time given start time and duration.

    Args:
        start_time: Start time (HH:MM)
        duration_min: Duration in minutes

    Returns:
        End time (HH:MM)
    """
    from datetime import datetime, timedelta

    try:
        start_dt = datetime.strptime(start_time, "%H:%M")
        end_dt = start_dt + timedelta(minutes=duration_min)
        return end_dt.strftime("%H:%M")
    except ValueError as e:
        logger.error(f"Invalid start_time format: {start_time}: {e}")
        raise


def _calculate_stats(planning: List[Dict]) -> Dict:
    """
    Calculate planning statistics.

    Args:
        planning: Complete planning

    Returns:
        Statistics dictionary
    """
    work_types = {'pomodoro', 'planned'}
    pause_types = {'recurrent', 'respiration', 'pause'}

    stats = {
        'total_slots': len(planning),
        'pomodoro_slots': len([s for s in planning if s.get('type') == 'pomodoro']),
        'recurrent_slots': len([s for s in planning if s.get('type') == 'recurrent']),
        'planned_slots': len([s for s in planning if s.get('type') == 'planned']),
        'respiration_slots': len([s for s in planning if s.get('type') == 'respiration']),
        'pause_slots': len([s for s in planning if s.get('type') == 'pause']),
        'work_minutes': sum(s.get('duration_min', 0) for s in planning if s.get('type') in work_types),
        'pause_minutes': sum(s.get('duration_min', 0) for s in planning if s.get('type') in pause_types),
    }

    stats['total_minutes'] = stats['work_minutes'] + stats['pause_minutes']

    return stats
