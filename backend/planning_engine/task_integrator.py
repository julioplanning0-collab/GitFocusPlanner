"""
Task Integrator Module - GitFocus Planner V2
Integrates special tasks into base planning (planned tasks, recurrent tasks).
Repairs alternation violations (ensures Pomodoro ↔ Pause rhythm).

FUNCTIONS:
1. Integrate planned tasks (fixed time) → Replace closest Pomodoros
2. Integrate recurrent tasks (due tasks) → Insert at available slots
3. Repair consecutive work tasks → Ensure alternation
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# PLANNED TASKS INTEGRATION (Fixed Date/Time)
# ============================================================================

def integrate_planned_tasks(planning: List[Dict], planned_tasks: List[Dict], date: str) -> List[Dict]:
    """
    Replace Pomodoros with planned tasks at closest available times.

    Algorithm:
    1. For each planned task:
       - Calculate required Pomodoros (duration ÷ 25, rounded up)
       - Find Pomodoros closest to planned time
       - Replace with planned task slots
       - Mark if rescheduled (time ≠ original)

    Args:
        planning: Base planning (Pomodoro + Recurrent alternation)
        planned_tasks: Tasks with PLANNED_START field
        date: Target date (YYYY-MM-DD)

    Returns:
        Modified planning with planned tasks integrated
    """
    if not planned_tasks:
        logger.debug("No planned tasks to integrate")
        return planning

    modified_planning = planning.copy()

    for planned_task in planned_tasks:
        planned_start_str = planned_task.get('planned_start', '')
        if not planned_start_str:
            logger.warning(f"Planned task {planned_task.get('id')} missing PLANNED_START, skipping")
            continue

        # Parse planned time (format: "DD.MM.YY HH:MM")
        try:
            desired_time = datetime.strptime(planned_start_str, "%d.%m.%y %H:%M")
        except ValueError as e:
            logger.error(f"Invalid PLANNED_START format for task {planned_task.get('id')}: {planned_start_str}: {e}")
            continue

        # Calculate required Pomodoros
        duration_min = planned_task.get('duration_min', 25)
        nb_pomodoros = math.ceil(duration_min / 25)

        # Find available Pomodoros (not already replaced)
        available_pomodoros = [
            (idx, slot) for idx, slot in enumerate(modified_planning)
            if slot.get('type') == 'pomodoro'
        ]

        if len(available_pomodoros) < nb_pomodoros:
            logger.warning(f"Not enough Pomodoros available for planned task {planned_task.get('id')} ({nb_pomodoros} needed, {len(available_pomodoros)} available)")
            # Take what's available
            nb_pomodoros = len(available_pomodoros)

        if nb_pomodoros == 0:
            logger.warning(f"No Pomodoros available for planned task {planned_task.get('id')}, skipping")
            continue

        # Calculate distance from each Pomodoro to desired time
        # 🆕 Filter out past slots for today
        now = datetime.now()
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        is_today = (target_date == now.date())

        distances = []
        for idx, slot in available_pomodoros:
            try:
                slot_time = datetime.strptime(f"{date} {slot['heure_debut']}", "%Y-%m-%d %H:%M")

                # 🆕 Skip past slots for today
                if is_today and slot_time < now:
                    logger.debug(f"Skipping past slot {slot['heure_debut']} for planned task integration")
                    continue

                distance_seconds = abs((slot_time - desired_time).total_seconds())
                distances.append((distance_seconds, idx, slot))
            except (ValueError, KeyError) as e:
                logger.debug(f"Cannot parse time for slot {slot.get('id')}: {e}")
                continue

        if not distances:
            logger.warning(f"Cannot calculate distances for planned task {planned_task.get('id')}, skipping")
            continue

        # Sort by distance (ascending)
        distances.sort(key=lambda x: x[0])

        # Replace N closest Pomodoros
        for i, (dist_seconds, idx, old_slot) in enumerate(distances[:nb_pomodoros], start=1):
            is_rescheduled = dist_seconds > 900  # > 15 minutes

            replacement_slot = {
                'id': old_slot['id'],  # Keep same ID
                'heure_debut': old_slot['heure_debut'],
                'heure_fin': old_slot['heure_fin'],
                'type': 'planned',
                'task_id': planned_task['id'],
                'task_name': planned_task['name'],
                'category': planned_task.get('category', ''),
                'sub_category': planned_task.get('sub_category', ''),
                'duration_min': 25,  # Each Pomodoro is still 25 min
                'pomodoro_num': i,
                'total_pomodoros': nb_pomodoros,
                'original_time': desired_time.strftime("%H:%M"),
                'is_rescheduled': is_rescheduled,
                'date': date
            }

            modified_planning[idx] = replacement_slot
            logger.debug(f"Replaced Pomodoro at {old_slot['heure_debut']} with planned task {planned_task['id']} ({i}/{nb_pomodoros})")

    logger.info(f"Integrated {len(planned_tasks)} planned tasks into planning")
    return modified_planning


# ============================================================================
# CONSECUTIVE TASKS REPAIR (Alternation Enforcement)
# ============================================================================

def repair_consecutive_work_tasks(planning: List[Dict]) -> List[Dict]:
    """
    Ensure strict alternation: No two work tasks consecutive, no two pauses consecutive.

    Work types: pomodoro, planned, recurrent
    Pause types: respiration, pause

    Algorithm:
    1. Scan for violations (two work tasks or two pauses consecutive)
    2. Find available pause/work task to insert
    3. Insert between violating tasks
    4. Repeat until no violations

    Args:
        planning: Planning to repair

    Returns:
        Repaired planning with strict alternation
    """
    modified = True
    max_iterations = 50  # Safety limit
    iteration = 0

    while modified and iteration < max_iterations:
        modified = False
        iteration += 1

        for i in range(len(planning) - 1):
            current = planning[i]
            next_slot = planning[i + 1]

            current_type = current.get('type')
            next_type = next_slot.get('type')

            work_types = {'pomodoro', 'planned', 'recurrent'}
            pause_types = {'respiration', 'pause'}

            current_is_work = current_type in work_types
            next_is_work = next_type in work_types

            # Violation: Two work tasks consecutive
            if current_is_work and next_is_work:
                logger.debug(f"Found consecutive work tasks at {i}: {current_type} → {next_type}")

                # Find available pause to insert
                pause_slot = _find_available_pause(planning, i)

                if pause_slot:
                    planning.insert(i + 1, pause_slot)
                    logger.debug(f"Inserted pause between {current_type} and {next_type}")
                    modified = True
                    break  # Restart scan
                else:
                    # Create default pause
                    default_pause = {
                        'id': f"pause_{i}",
                        'type': 'pause',
                        'task_id': 'default_pause',
                        'task_name': 'Pause',
                        'duration_min': 5,
                        'heure_debut': '',  # Will be recalculated
                        'heure_fin': '',
                        'date': current.get('date', '')
                    }
                    planning.insert(i + 1, default_pause)
                    logger.debug(f"Created default pause between {current_type} and {next_type}")
                    modified = True
                    break

            # Violation: Two pauses consecutive (rare but possible)
            current_is_pause = current_type in pause_types
            next_is_pause = next_type in pause_types

            if current_is_pause and next_is_pause:
                logger.debug(f"Found consecutive pauses at {i}: {current_type} → {next_type}")

                # Remove second pause (simpler than finding work task)
                planning.pop(i + 1)
                logger.debug(f"Removed consecutive pause")
                modified = True
                break

    if iteration >= max_iterations:
        logger.warning(f"Repair hit max iterations ({max_iterations}), may still have violations")

    logger.info(f"Repaired alternation in {iteration} iterations")
    return planning


def _find_available_pause(planning: List[Dict], exclude_index: int) -> Dict:
    """
    Find a pause task that can be moved.

    Args:
        planning: Current planning
        exclude_index: Index to exclude from search

    Returns:
        Pause slot dict, or None if not found
    """
    pause_types = {'respiration', 'pause'}

    for i, slot in enumerate(planning):
        if i == exclude_index:
            continue

        if slot.get('type') in pause_types:
            # Found pause, remove and return it
            return planning.pop(i)

    return None


# ============================================================================
# TIME RECALCULATION (After modifications)
# ============================================================================

def recalculate_times(planning: List[Dict], date: str, temps_morts: List[Dict]) -> List[Dict]:
    """
    Recalculate all heure_debut/heure_fin after modifications.

    Ensures:
    - Continuity (no gaps)
    - No overlap with temps_morts
    - Day bounds (06:00 - 23:00)
    - 🆕 If date is today, start at current time (rounded up to 15 min)

    Args:
        planning: Planning with potentially incorrect times
        date: Target date (YYYY-MM-DD)
        temps_morts: Blocked time slots

    Returns:
        Planning with recalculated times
    """
    from backend.planning_engine.slot_calculator import find_next_free_slot

    # 🆕 Start at current time if today
    target_date = datetime.strptime(date, "%Y-%m-%d").date()
    today = datetime.now().date()

    if target_date == today:
        # Start at current time (rounded up to 15min)
        now = datetime.now()
        start_hour = now.hour
        start_minute = now.minute

        # Round up to next 15-minute mark
        rounded_minute = ((start_minute // 15) + 1) * 15
        if rounded_minute == 60:
            start_hour += 1
            rounded_minute = 0

        # Ensure within day bounds
        if start_hour < 6:
            start_hour = 6
            rounded_minute = 0
        elif start_hour >= 23:
            logger.warning(f"Current time {now.time()} is past end of day (23:00), no slots available")
            return []

        current_time = datetime.strptime(f"{date} {start_hour:02d}:{rounded_minute:02d}", "%Y-%m-%d %H:%M")
        logger.info(f"Recalculating times starting at current time: {current_time.strftime('%H:%M')}")
    else:
        # Start at 06:00 for future dates
        current_time = datetime.strptime(f"{date} 06:00", "%Y-%m-%d %H:%M")
        logger.debug(f"Recalculating times starting at 06:00 (future date)")

    # Max time is 23:59:59 (NOT midnight)
    max_time = datetime.strptime(f"{date} 23:59:59", "%Y-%m-%d %H:%M:%S")

    recalculated_planning = []
    for slot in planning:
        duration = slot.get('duration_min', 25)

        # Find next free slot
        current_time = find_next_free_slot(current_time, duration, temps_morts)

        # Check if exceeds day bounds (23:59)
        slot_end = current_time + timedelta(minutes=duration)
        if slot_end > max_time:
            logger.warning(f"Slot {slot.get('id')} would end at {slot_end.strftime('%H:%M')}, exceeds day bounds (23:59), truncating planning")
            break

        slot['heure_debut'] = current_time.strftime("%H:%M")
        slot['heure_fin'] = slot_end.strftime("%H:%M")
        slot['date'] = date

        recalculated_planning.append(slot)
        current_time = slot_end

    logger.debug(f"Recalculated times for {len(recalculated_planning)} slots (truncated from {len(planning)})")
    return recalculated_planning


# ============================================================================
# GENERATE UNIQUE SLOT IDS
# ============================================================================

_slot_id_counter = 0

def generate_slot_id() -> str:
    """
    Generate unique slot ID.

    Returns:
        Unique ID string (e.g., "slot_001")
    """
    global _slot_id_counter
    _slot_id_counter += 1
    return f"slot_{_slot_id_counter:03d}"


def reset_slot_id_counter():
    """Reset slot ID counter (useful for tests)."""
    global _slot_id_counter
    _slot_id_counter = 0
