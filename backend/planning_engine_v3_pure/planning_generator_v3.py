"""
V3 PURE - NO V2 LOGIC ALLOWED

Main planning generator with 2-step architecture.

ARCHITECTURE (CRITICAL):
    STEP 1: ORDERING → Build task sequence (minuteOffset = 0 placeholder)
    STEP 2: TIME CALCULATION → Call rebuildTimeline() to calculate minuteOffsets

WORKFLOW:
    1. Load data (pomodoros, pauses, recurrents, planned, obstacles)
    2. Expand pomodoros (75min → 3x 25min)
    3. Alternate pomodoros & pauses (cycle through pauses with duplicates)
    4. Insert calins (optional, every 2 pauses)
    5. Insert clopes (optional, after X min of work)
    → STEP 1 COMPLETE: ordered_tasks (with minuteOffset=0)
    6. Convert temps_morts to obstacles
    7. Call rebuildTimeline() → calculate all minuteOffsets
    → STEP 2 COMPLETE: timeline with real times
"""

import math
import logging
from datetime import datetime
from typing import List, Dict, Optional
from .types_v3 import TaskV3, Obstacle, Timeline, TaskType, TaskList, ObstacleList, create_task_v3
from .data_loader_v3 import (
    load_pomodoro_tasks_by_ids,
    load_recurrent_tasks_by_ids_v3,
    load_temps_morts,
    get_task_duration_minutes,
    get_task_name,
    get_task_id
)
from .timeline_calculator_v3 import (
    rebuildTimeline,
    convertTempsMortsToObstacles,
    sortTasksByOffset
)

logger = logging.getLogger(__name__)


# ==================== CONFIGURATION ====================

class PlanningOptions:
    """Configuration options for planning generation"""
    def __init__(
        self,
        calin_enabled: bool = False,
        clope_enabled: bool = False,
        clope_interval_min: int = 120
    ):
        self.calin_enabled = calin_enabled
        self.clope_enabled = clope_enabled
        self.clope_interval_min = clope_interval_min


# ==================== STEP 1: ORDERING ====================

def expand_pomodoros(pomodoro_tasks: List[Dict]) -> TaskList:
    """
    Expand tasks into 25-minute pomodoro units.

    Étape 10 du flux V3.

    Args:
        pomodoro_tasks: List of task dicts from CSV (with DUREE_MIN field)

    Returns:
        List of TaskV3 with type=POMODORO, duration=25, minuteOffset=0

    Example:
        Input: [{CODE_TACHE: "TASK001", NOM_TACHE: "Maths", DUREE_MIN: 75}]
        Output: [
            TaskV3(type=POMODORO, taskName="Maths", duration=25, pomodoroIndex=1, pomodoroTotal=3),
            TaskV3(type=POMODORO, taskName="Maths", duration=25, pomodoroIndex=2, pomodoroTotal=3),
            TaskV3(type=POMODORO, taskName="Maths", duration=25, pomodoroIndex=3, pomodoroTotal=3)
        ]
    """
    expanded: TaskList = []

    for task in pomodoro_tasks:
        duration = get_task_duration_minutes(task)
        task_id = get_task_id(task)
        task_name = get_task_name(task)

        if duration <= 0:
            logger.warning(f"Skipping task with invalid duration: {task}")
            continue

        # Calculate number of 25-minute pomodoros
        nb_pomos = math.ceil(duration / 25)

        # Create one TaskV3 per pomodoro
        for i in range(nb_pomos):
            pomo_task = create_task_v3(
                minute_offset=0,  # Placeholder (STEP 1)
                duration=25,
                task_type=TaskType.POMODORO,
                task_id=task_id,
                task_name=task_name,
                is_fixed=False,
                pomodoroIndex=i + 1,
                pomodoroTotal=nb_pomos
            )
            expanded.append(pomo_task)

    logger.info(f"Expanded {len(pomodoro_tasks)} tasks into {len(expanded)} pomodoros")
    return expanded


def alternate_pomodoros_pauses(pomodoros: TaskList, pauses: List[Dict]) -> TaskList:
    """
    ✅ LOGIQUE CLÉ - Alternate pomodoros with pauses (cycle through pauses).

    Étape 11 du flux V3.

    IMPORTANT: Preserves pause order and duplicates (drag & drop behavior).

    Args:
        pomodoros: List of POMODORO TaskV3
        pauses: List of pause task dicts from CSV (with duplicates possible)

    Returns:
        Alternated list: [P1, Pause1, P2, Pause2, P3, Pause1, ...]

    Example:
        pomodoros: [P1, P2, P3, P4, P5]
        pauses: [Pause1, Pause2, Pause1]  # Note: Pause1 appears twice (user dragged twice)

        Result: [P1, Pause1, P2, Pause2, P3, Pause1, P4, Pause1, P5, ...]
                      ↑ 1st       ↑ 2nd       ↑ 3rd (cycle)  ↑ 4th (cycle)
    """
    if not pauses:
        logger.warning("No pauses provided, returning only pomodoros")
        return pomodoros

    alternated: TaskList = []
    pause_index = 0

    for i, pomo in enumerate(pomodoros):
        # Add pomodoro
        alternated.append(pomo)

        # Add pause after (except last pomodoro)
        if i < len(pomodoros) - 1:
            # Cycle through pauses (modulo to loop)
            pause_csv = pauses[pause_index % len(pauses)]

            pause_task = create_task_v3(
                minute_offset=0,  # Placeholder (STEP 1)
                duration=get_task_duration_minutes(pause_csv),
                task_type=TaskType.PAUSE,
                task_id=get_task_id(pause_csv),
                task_name=get_task_name(pause_csv),
                is_fixed=False
            )
            alternated.append(pause_task)

            pause_index += 1

    logger.info(
        f"Alternated {len(pomodoros)} pomodoros with {len(pauses)} pause types "
        f"→ {len(alternated)} total tasks"
    )
    return alternated


def insert_calins(tasks: TaskList) -> TaskList:
    """
    Insert 5-minute CALIN after every 2 pauses (optional).

    Étape 12 du flux V3.

    Args:
        tasks: Alternated task list

    Returns:
        Task list with CALINs inserted

    Example:
        Input: [P1, Pause1, P2, Pause2, P3, Pause3, P4, Pause4]
        Output: [P1, Pause1, P2, Pause2, CALIN, P3, Pause3, P4, Pause4, CALIN]
                                         ↑ after 2 pauses        ↑ after 4 pauses
    """
    result: TaskList = []
    pause_count = 0

    for task in tasks:
        result.append(task)

        if task['type'] == TaskType.PAUSE:
            pause_count += 1

            # Every 2 pauses, insert CALIN
            if pause_count % 2 == 0:
                calin_task = create_task_v3(
                    minute_offset=0,  # Placeholder (STEP 1)
                    duration=5,
                    task_type=TaskType.CALIN,
                    task_id='AUTO_CALIN',
                    task_name='Câlin',
                    is_fixed=False,
                    autoGenerated=True
                )
                result.append(calin_task)

    logger.info(f"Inserted {pause_count // 2} câlins (1 per 2 pauses)")
    return result


def insert_clopes(tasks: TaskList, interval_min: int) -> TaskList:
    """
    Insert 25-minute CLOPE after cumulative work time >= interval_min (optional).

    Étape 13 du flux V3.

    Args:
        tasks: Task list
        interval_min: Work interval before clope (e.g., 120 = insert after 2h work)

    Returns:
        Task list with CLOPEs inserted

    Example:
        interval_min = 120
        Input: [P1(25), Pause, P2(25), Pause, P3(25), Pause, P4(25), Pause, P5(25), ...]
               cumulative work: 25 → 50 → 75 → 100 → 125 (>= 120, insert CLOPE)

        Output: [P1, Pause, P2, Pause, P3, Pause, P4, Pause, P5, CLOPE, P6, ...]
    """
    result: TaskList = []
    cumulative_work_min = 0

    for task in tasks:
        result.append(task)

        if task['type'] == TaskType.POMODORO:
            cumulative_work_min += task['duration']

            # Check if threshold reached
            if cumulative_work_min >= interval_min:
                clope_task = create_task_v3(
                    minute_offset=0,  # Placeholder (STEP 1)
                    duration=25,
                    task_type=TaskType.CLOPE,
                    task_id='AUTO_CLOPE',
                    task_name='Clope',
                    is_fixed=False,
                    autoGenerated=True
                )
                result.append(clope_task)

                # Reset counter
                cumulative_work_min = 0
                logger.debug(f"Inserted clope after {interval_min}min work, counter reset")

    if cumulative_work_min > 0:
        logger.info(f"Inserted clopes, {cumulative_work_min}min work remaining (< {interval_min}min)")

    return result


def build_ordered_sequence(
    pomodoro_tasks: List[Dict],
    pause_tasks: List[Dict],
    options: PlanningOptions
) -> TaskList:
    """
    ✅ STEP 1 COMPLETE - Build ordered task sequence (minuteOffset = 0).

    Orchestrates steps 10-13 of V3 flux.

    Args:
        pomodoro_tasks: Selected pomodoro tasks from CSV
        pause_tasks: Selected pause tasks from CSV (order + duplicates preserved)
        options: Planning configuration (calins, clopes)

    Returns:
        Ordered task list with minuteOffset=0 (ready for STEP 2)

    Algorithm:
        1. Expand pomodoros (75min → 3x 25min)
        2. Alternate pomodoros & pauses
        3. Insert calins (if enabled)
        4. Insert clopes (if enabled)
    """
    # Step 10: Expand pomodoros
    pomodoros = expand_pomodoros(pomodoro_tasks)

    if not pomodoros:
        logger.warning("No pomodoros after expansion")
        return []

    # Step 11: Alternate with pauses
    alternated = alternate_pomodoros_pauses(pomodoros, pause_tasks)

    # Step 12: Insert calins (optional)
    if options.calin_enabled:
        alternated = insert_calins(alternated)

    # Step 13: Insert clopes (optional)
    if options.clope_enabled:
        alternated = insert_clopes(alternated, options.clope_interval_min)

    logger.info(f"STEP 1 complete: {len(alternated)} ordered tasks (minuteOffset=0)")
    return alternated


# ==================== STEP 2: TIME CALCULATION ====================

def calculate_timeline(
    ordered_tasks: TaskList,
    obstacles: ObstacleList,
    planning_start_minute: int = 0
) -> TaskList:
    """
    ✅ STEP 2 COMPLETE - Calculate all minuteOffsets using rebuildTimeline().

    Étapes 14-16 du flux V3.

    Args:
        ordered_tasks: Task list from STEP 1 (minuteOffset=0)
        obstacles: Linear obstacles (temps_morts converted)
        planning_start_minute: Start minute (usually 0)

    Returns:
        Task list with calculated minuteOffsets (ready for display conversion)

    CRITICAL: This function MUST be called after ANY timeline modification.
    """
    logger.info(f"STEP 2: Calculating minuteOffsets for {len(ordered_tasks)} tasks with {len(obstacles)} obstacles")

    # Call rebuildTimeline (CORE V3 FUNCTION)
    timeline_with_offsets = rebuildTimeline(ordered_tasks, obstacles, planning_start_minute)

    logger.info(f"STEP 2 complete: {len(timeline_with_offsets)} tasks with calculated minuteOffsets")
    return timeline_with_offsets


# ==================== MAIN GENERATOR ====================

def generate_planning_v3(
    date: str,
    planning_start_time: datetime,
    pomodoro_ids: List[str],
    pause_ids: List[str],
    options: PlanningOptions
) -> Timeline:
    """
    ✅ V3 MAIN GENERATOR - Generate complete planning with 2-step architecture.

    This is the main entry point for V3 planning generation.

    Args:
        date: Date string (YYYY-MM-DD)
        planning_start_time: Planning start datetime (minute 0)
        pomodoro_ids: Selected pomodoro task IDs
        pause_ids: Selected pause IDs (with order & duplicates preserved)
        options: Planning options (calins, clopes)

    Returns:
        Timeline with tasks (minuteOffsets calculated) and obstacles

    2-STEP ARCHITECTURE:
        STEP 1 (ORDERING):
            - Load data
            - Expand pomodoros
            - Alternate with pauses
            - Insert calins/clopes
            → ordered_tasks with minuteOffset=0

        STEP 2 (TIME CALCULATION):
            - Convert temps_morts to obstacles
            - Call rebuildTimeline()
            → tasks with real minuteOffsets

    Example usage:
        options = PlanningOptions(calin_enabled=True, clope_enabled=True, clope_interval_min=120)
        timeline = generate_planning_v3(
            date="2025-11-06",
            planning_start_time=datetime(2025, 11, 6, 14, 0),
            pomodoro_ids=["TASK001", "TASK002"],
            pause_ids=["REC001", "REC003", "REC001"],  # REC001 twice (drag & drop)
            options=options
        )
    """
    logger.info(f"=== V3 PLANNING GENERATION START ===")
    logger.info(f"Date: {date}, Start: {planning_start_time}")
    logger.info(f"Pomodoros: {len(pomodoro_ids)}, Pauses: {len(pause_ids)}")
    logger.info(f"Options: calins={options.calin_enabled}, clopes={options.clope_enabled}")

    # === STEP 1: ORDERING ===

    # Load selected pomodoro tasks
    pomodoro_tasks = load_pomodoro_tasks_by_ids(pomodoro_ids)
    logger.info(f"Loaded {len(pomodoro_tasks)} pomodoro tasks")

    # Load selected pause tasks (preserves order & duplicates)
    pause_tasks = load_recurrent_tasks_by_ids_v3(pause_ids)
    logger.info(f"Loaded {len(pause_tasks)} pause tasks (with duplicates preserved)")

    # Build ordered sequence (STEP 1)
    ordered_tasks = build_ordered_sequence(pomodoro_tasks, pause_tasks, options)

    if not ordered_tasks:
        logger.warning("No tasks in sequence, returning empty timeline")
        return {
            'planningStartTime': planning_start_time.isoformat(),
            'tasks': [],
            'obstacles': []
        }

    # === STEP 2: TIME CALCULATION ===

    # Load temps morts for current day AND next day (planning can span midnight)
    temps_morts_csv = load_temps_morts(date)

    # Also load next day's temps_morts
    from datetime import timedelta as td
    next_date = (datetime.strptime(date, '%Y-%m-%d') + td(days=1)).strftime('%Y-%m-%d')
    temps_morts_next_day = load_temps_morts(next_date)
    temps_morts_csv.extend(temps_morts_next_day)

    obstacles = convertTempsMortsToObstacles(temps_morts_csv, planning_start_time)
    logger.info(f"Converted {len(temps_morts_csv)} temps morts (including next day) to {len(obstacles)} obstacles")

    # Calculate minuteOffsets (STEP 2)
    final_tasks = calculate_timeline(ordered_tasks, obstacles, planning_start_minute=0)

    # Sort by minuteOffset
    final_tasks = sortTasksByOffset(final_tasks)

    # Create timeline
    timeline: Timeline = {
        'planningStartTime': planning_start_time.isoformat(),
        'tasks': final_tasks,
        'obstacles': obstacles
    }

    logger.info(f"=== V3 PLANNING GENERATION COMPLETE ===")
    logger.info(f"Final: {len(final_tasks)} tasks, {len(obstacles)} obstacles")

    return timeline


# ==================== STATISTICS ====================

def calculate_planning_statistics(timeline: Timeline) -> Dict:
    """
    Calculate statistics for generated planning.

    Args:
        timeline: Generated timeline

    Returns:
        Dict with statistics:
        - total_pomodoros: Number of POMODORO tasks
        - total_pauses: Number of PAUSE tasks
        - total_calins: Number of CALIN tasks
        - total_clopes: Number of CLOPE tasks
        - total_work_min: Total work time (minutes)
        - total_pause_min: Total pause time (minutes)
        - planning_duration_min: Total planning duration
    """
    tasks = timeline['tasks']

    pomodoro_count = sum(1 for t in tasks if t['type'] == TaskType.POMODORO)
    pause_count = sum(1 for t in tasks if t['type'] == TaskType.PAUSE)
    calin_count = sum(1 for t in tasks if t['type'] == TaskType.CALIN)
    clope_count = sum(1 for t in tasks if t['type'] == TaskType.CLOPE)

    work_time = sum(t['duration'] for t in tasks if t['type'] == TaskType.POMODORO)
    pause_time = sum(
        t['duration'] for t in tasks
        if t['type'] in [TaskType.PAUSE, TaskType.CALIN, TaskType.CLOPE]
    )

    # Calculate total duration
    if tasks:
        last_task = max(tasks, key=lambda t: t['minuteOffset'] + t['duration'])
        total_duration = last_task['minuteOffset'] + last_task['duration']
    else:
        total_duration = 0

    return {
        'total_pomodoros': pomodoro_count,
        'total_pauses': pause_count,
        'total_calins': calin_count,
        'total_clopes': clope_count,
        'total_work_min': work_time,
        'total_pause_min': pause_time,
        'planning_duration_min': total_duration
    }
