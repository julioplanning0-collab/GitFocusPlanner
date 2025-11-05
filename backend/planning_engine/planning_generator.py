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
    start_time: Optional[str] = None,
    respiration_ids: Optional[List[str]] = None,
    max_recurrent_tasks: int = 10,
    enable_clopes: bool = False,
    clopes_interval_min: int = 120,
    enable_calins: bool = False,
    allow_consecutive_pauses: bool = False
) -> Dict:
    """
    Generate daily planning with automatic recurrent task selection (🆕).

    This is the main entry point with intelligent scoring.

    Args:
        date: Target date (YYYY-MM-DD)
        pomodoro_ids: List of selected Pomodoro task IDs
        data_dir: Path to prod_data/ directory
        start_time: Planning start time HH:MM (optional, will calculate now+15min if not provided)
        respiration_ids: List of respiration task IDs (can contain duplicates, optional)
        max_recurrent_tasks: Max number of recurrent tasks to select (default 10)
        enable_clopes: Enable cigarette breaks insertion (default False)
        clopes_interval_min: Interval for clopes in minutes (default 120)
        enable_calins: Enable câlins insertion (1 every 2 respirations, default False)
        allow_consecutive_pauses: Allow consecutive pauses without Pomodoros (default False)

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
        load_respiration_tasks,
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

    # 🆕 Load respiration tasks for pause alternance
    if respiration_ids:
        logger.info(f"🔍 DEBUG: Loading respiration tasks for IDs: {respiration_ids}")
        all_respiration = load_respiration_tasks(data_dir / 'TACHES_RESPIRATOIRES.v2.csv')
        # Build list with duplicates preserved (respiration_ids can contain duplicates)
        selected_respiration = []
        for resp_id in respiration_ids:
            matching_task = next((t for t in all_respiration if t['id'] == resp_id), None)
            if matching_task:
                selected_respiration.append(matching_task)
            else:
                logger.warning(f"Respiration task ID {resp_id} not found in CSV, skipping")
        logger.info(f"🔍 DEBUG: Selected {len(selected_respiration)} respiration tasks (with duplicates): {[t['id'] + ':' + t['name'] for t in selected_respiration]}")
    else:
        logger.info("🔍 DEBUG: No respiration_ids provided, will use recurrent tasks for alternance")
        selected_respiration = []

    # Load recurrent tasks for fallback (if no respirations provided)
    all_recurrent = load_recurrent_tasks(data_dir / 'TACHES_RECURRENTES.v2.csv', active_only=True)

    # Planned tasks (fixed time) for this date
    planned_tasks = load_planned_tasks(data_dir / 'TACHES_PLANIFIEES.v2.csv', date=date)

    # Temps morts (blocked slots) for this date
    temps_morts = load_temps_morts(data_dir / 'temps_morts.csv', date)

    # History for scoring (🆕 only needed if using recurrent tasks)
    planning_history = load_planning_history(data_dir / 'planning_placements_history.csv')
    done_history = load_done_history(data_dir / 'done_v2.csv')

    logger.info(f"Loaded: {len(selected_pomodoro)} Pomodoro, {len(selected_respiration)} respiration, {len(all_recurrent)} recurrent, {len(planned_tasks)} planned, {len(temps_morts)} temps_morts")

    # ========================================================================
    # STEP 2: Calculate Free Time Slots
    # ========================================================================
    from backend.planning_engine.slot_calculator import calculate_free_slots

    free_slots = calculate_free_slots(date, temps_morts, start_time=start_time)
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
    # STEP 3: Decide Alternance Strategy (🆕 User Manual Selection Only)
    # ========================================================================
    # If respiration_ids provided → use respirations for alternance
    # Otherwise → NO pause tasks (user wants ONLY Pomodoros)

    if selected_respiration:
        logger.info("🔍 DEBUG: Using manually selected respiration tasks for alternance")
        pause_tasks = selected_respiration
        recurrent_task_scores = []  # No scoring needed
    else:
        logger.info("🔍 DEBUG: No respiration tasks selected, planning will contain ONLY Pomodoros (no pauses)")
        pause_tasks = []  # No automatic pause insertion
        recurrent_task_scores = []

    # ========================================================================
    # STEP 3.5: Log Advanced Options (Phase 4)
    # ========================================================================
    if enable_clopes or enable_calins or allow_consecutive_pauses:
        logger.info(f"🔍 DEBUG: Advanced options enabled:")
        if enable_clopes:
            logger.info(f"  - Clopes: every {clopes_interval_min} minutes")
        if enable_calins:
            logger.info(f"  - Câlins: 1 every 2 respirations")
        if allow_consecutive_pauses:
            logger.info(f"  - Consecutive pauses: allowed")

    # ========================================================================
    # STEP 4: Generate Base Planning (Alternation)
    # ========================================================================
    # Support multi-day: continue on next day if needed
    planning = _generate_multiday_planning(
        selected_pomodoro, pause_tasks, free_slots, date,
        data_dir, temps_morts, max_days=2,
        enable_calins=enable_calins,
        allow_consecutive_pauses=allow_consecutive_pauses
    )

    logger.info(f"Generated base planning with {len(planning)} slots")

    # ========================================================================
    # STEP 4.5: Insert Clopes (Phase 4)
    # ========================================================================
    if enable_clopes and planning:
        planning = _insert_clopes(planning, clopes_interval_min, date)
        logger.info(f"Inserted clopes (interval: {clopes_interval_min} min)")

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
    # STEP 6: Repair Alternation Violations (Phase 4: Optional)
    # ========================================================================
    from backend.planning_engine.task_integrator import repair_consecutive_work_tasks

    if not allow_consecutive_pauses:
        planning = repair_consecutive_work_tasks(planning)
        logger.info("Repaired consecutive work tasks (alternation enforced)")
    else:
        logger.info("Skipped alternation repair (allow_consecutive_pauses=True)")

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
        'recurrent_task_scores': recurrent_task_scores  # Already formatted in Step 3
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
    pause_tasks: List[Dict],
    free_slots: List[Dict],
    date: str,
    data_dir: Path,
    temps_morts: List[Dict],
    max_days: int = 2,
    enable_calins: bool = False,
    allow_consecutive_pauses: bool = False
) -> List[Dict]:
    """
    Generate planning across multiple days if needed.

    Args:
        pomodoro_tasks: Pomodoro tasks to place
        pause_tasks: Pause tasks (respiration or recurrent)
        free_slots: Free slots for day 1
        date: Starting date (YYYY-MM-DD)
        data_dir: Data directory for loading temps_morts
        temps_morts: Temps morts for day 1
        max_days: Maximum number of days to generate (default 2)
        enable_calins: Enable câlins insertion (Phase 4)
        allow_consecutive_pauses: Allow consecutive pauses (Phase 4)

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
        day_planning = _generate_base_planning(
            current_pomodoro, pause_tasks, free_slots, current_date,
            enable_calins=enable_calins,
            allow_consecutive_pauses=allow_consecutive_pauses
        )

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
    pause_tasks: List[Dict],
    free_slots: List[Dict],
    date: str,
    enable_calins: bool = False,
    allow_consecutive_pauses: bool = False
) -> List[Dict]:
    """
    Generate base planning with Pomodoro ↔ Pause alternation.

    Args:
        pomodoro_tasks: Selected Pomodoro tasks
        pause_tasks: Selected pause tasks (respiration or recurrent)
        free_slots: Available time slots
        date: Target date
        enable_calins: Insert 1 câlin every 2 respirations (Phase 4)
        allow_consecutive_pauses: Allow multiple pauses without Pomodoros (Phase 4)

    Returns:
        List of planning slots

    Note:
        pause_tasks can be respiration tasks (type='respiration') or recurrent tasks (type='recurrent').
        The function detects the type by checking if the task has 'duration_min' field.
    """
    from backend.planning_engine.task_integrator import generate_slot_id, reset_slot_id_counter

    reset_slot_id_counter()

    planning = []
    slot_index = 0
    pause_index = 0  # Renamed from recurrent_index

    # 🆕 Phase 4: Track câlins (1 every 2 respirations)
    respiration_count = 0  # Count respirations for câlin insertion

    # Detect task type (respiration or recurrent) by checking for 'earliest_time' field
    # Respiration tasks have 'earliest_time', 'latest_time', 'ideal_time' fields
    # Recurrent tasks don't have these fields
    pause_task_type = 'respiration' if (pause_tasks and 'earliest_time' in pause_tasks[0]) else 'recurrent'
    logger.info(f"🔍 DEBUG: Pause task type detected: {pause_task_type}")
    logger.info(f"🔍 DEBUG: Phase 4 options - enable_calins: {enable_calins}, allow_consecutive_pauses: {allow_consecutive_pauses}")

    # Sort Pomodoro by priority (1=High → 3=Low), then by deadline
    pomodoro_tasks_sorted = sorted(
        pomodoro_tasks,
        key=lambda t: (t.get('priority', 3), t.get('deadline', '99.99.99'))
    )

    logger.info(f"🔍 DEBUG: _generate_base_planning called with {len(pomodoro_tasks)} Pomodoro tasks")
    logger.info(f"🔍 DEBUG: After sorting: {[t['id'] + ':' + t['name'] for t in pomodoro_tasks_sorted]}")
    logger.info(f"🔍 DEBUG: {len(pause_tasks)} pause tasks provided ({pause_task_type})")
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

            if not pause_tasks:
                # No pause tasks, add default 5-min pause
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
                # 🆕 Phase 4: Check if we should insert a câlin instead
                should_insert_calin = (
                    enable_calins and
                    pause_task_type == 'respiration' and
                    respiration_count > 0 and
                    respiration_count % 2 == 0  # Every 2 respirations
                )

                if should_insert_calin:
                    # Insert câlin (10 min)
                    calin_duration = 10

                    # Advance to next free slot if needed
                    current_time = advance_to_next_free_slot(current_time, calin_duration)
                    if current_time is None:
                        logger.warning(f"🔍 DEBUG: No more free slots for câlin, stopping")
                        return planning

                    calin_end = current_time + timedelta(minutes=calin_duration)

                    # Check if exceeds day bounds (23:59)
                    if calin_end > max_time:
                        logger.warning(f"Câlin exceeds day bounds at {current_time.strftime('%H:%M')}, truncating")
                        return planning

                    planning.append({
                        'id': generate_slot_id(),
                        'heure_debut': current_time.strftime('%H:%M'),
                        'heure_fin': calin_end.strftime('%H:%M'),
                        'type': 'calin',
                        'task_id': 'calin_auto',
                        'task_name': 'Câlin',
                        'duration_min': calin_duration,
                        'date': current_time.strftime('%Y-%m-%d')
                    })
                    current_time = calin_end
                    logger.info(f"🔍 DEBUG: Inserted câlin after {respiration_count} respirations")

                # Cycle through pause tasks (respiration or recurrent)
                pause_task = pause_tasks[pause_index % len(pause_tasks)]
                pause_index += 1

                pause_duration = pause_task['duration_min']

                # Advance to next free slot if needed
                current_time = advance_to_next_free_slot(current_time, pause_duration)
                if current_time is None:
                    logger.warning(f"🔍 DEBUG: No more free slots for pause task, stopping")
                    return planning

                pause_end = current_time + timedelta(minutes=pause_duration)

                # Check if exceeds day bounds (23:59)
                if pause_end > max_time:
                    logger.warning(f"Pause task exceeds day bounds at {current_time.strftime('%H:%M')}, truncating")
                    return planning

                planning.append({
                    'id': generate_slot_id(),
                    'heure_debut': current_time.strftime('%H:%M'),
                    'heure_fin': pause_end.strftime('%H:%M'),
                    'type': pause_task_type,  # 🆕 Use detected type ('respiration' or 'recurrent')
                    'task_id': pause_task['id'],
                    'task_name': pause_task['name'],
                    'category': pause_task.get('category', ''),
                    'sub_category': pause_task.get('sub_category', ''),
                    'duration_min': pause_duration,
                    'date': current_time.strftime('%Y-%m-%d')
                })
                current_time = pause_end

                # 🆕 Phase 4: Track respirations for câlin insertion
                if pause_task_type == 'respiration':
                    respiration_count += 1

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


def _insert_clopes(planning: List[Dict], interval_min: int, date: str) -> List[Dict]:
    """
    Insert clope (cigarette) breaks at regular intervals.

    Args:
        planning: Existing planning
        interval_min: Interval in minutes for clope breaks
        date: Target date

    Returns:
        Planning with clopes inserted

    Algorithm:
        1. Track cumulative duration (all tasks)
        2. When cumulative >= interval_min, insert clope (5 min)
        3. Reset counter after each clope
    """
    from datetime import datetime, timedelta
    from backend.planning_engine.task_integrator import generate_slot_id

    result = []
    cumulative_minutes = 0
    target_date_obj = datetime.strptime(date, "%Y-%m-%d").date()

    for slot in planning:
        # Add cumulative duration
        cumulative_minutes += slot.get('duration_min', 0)

        # Check if we need a clope
        if cumulative_minutes >= interval_min:
            # Insert clope before this slot
            slot_start = datetime.combine(target_date_obj, datetime.strptime(slot['heure_debut'], "%H:%M").time())
            clope_duration = 5

            result.append({
                'id': generate_slot_id(),
                'heure_debut': slot['heure_debut'],
                'heure_fin': (slot_start + timedelta(minutes=clope_duration)).strftime('%H:%M'),
                'type': 'clope',
                'task_id': 'clope_auto',
                'task_name': 'Pause Cigarette',
                'duration_min': clope_duration,
                'date': date
            })

            # Reset counter
            cumulative_minutes = 0

            # Adjust current slot start time
            new_start = slot_start + timedelta(minutes=clope_duration)
            slot['heure_debut'] = new_start.strftime('%H:%M')
            new_end = new_start + timedelta(minutes=slot.get('duration_min', 0))
            slot['heure_fin'] = new_end.strftime('%H:%M')

        result.append(slot)

    logger.info(f"🔍 DEBUG: Inserted {len([s for s in result if s.get('type') == 'clope'])} clopes")
    return result


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
