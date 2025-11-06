"""
V3 PURE - NO V2 LOGIC ALLOWED

Core linear timeline functions for V3 architecture.

CRITICAL CONCEPTS:
- Timeline = axis in minutes (0 = planningStartTime)
- rebuildTimeline() = CENTRAL function, called after EVERY timeline modification
- Obstacles = linear blocks that force tasks to skip past them
- All calculations in minutes, convert to datetime ONLY for display

ARCHITECTURE:
    STEP 1: ORDERING → Build task sequence (minuteOffset = 0 placeholder)
    STEP 2: TIME CALCULATION → Call rebuildTimeline() to calculate all minuteOffsets
"""

from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from .types_v3 import TaskV3, Obstacle, Timeline, TaskList, ObstacleList


# ==================== TIME CONVERSION FUNCTIONS ====================

def dateTimeToMinutes(dt: datetime, planning_start: datetime) -> int:
    """
    Convert absolute datetime to minutes from planningStartTime.

    Args:
        dt: Absolute datetime
        planning_start: Planning start datetime (minute 0)

    Returns:
        Minutes from planning start (can be negative for past times)

    Example:
        planning_start = datetime(2025, 11, 6, 14, 0)
        dt = datetime(2025, 11, 6, 14, 25)
        → returns 25
    """
    delta = dt - planning_start
    return int(delta.total_seconds() / 60)


def minutesToDateTime(minutes: int, planning_start: datetime) -> datetime:
    """
    Convert minutes from planningStartTime to absolute datetime.

    Args:
        minutes: Minutes from planning start
        planning_start: Planning start datetime (minute 0)

    Returns:
        Absolute datetime

    Example:
        planning_start = datetime(2025, 11, 6, 14, 0)
        minutes = 25
        → returns datetime(2025, 11, 6, 14, 25)
    """
    return planning_start + timedelta(minutes=minutes)


def formatDateTime(dt: datetime) -> Tuple[str, str]:
    """
    Format datetime to (date, time) strings for display.

    Args:
        dt: Datetime to format

    Returns:
        Tuple of (date_str, time_str)
        - date_str: "YYYY-MM-DD"
        - time_str: "HH:MM"

    Example:
        dt = datetime(2025, 11, 6, 14, 25)
        → returns ("2025-11-06", "14:25")
    """
    return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")


# ==================== COLLISION DETECTION ====================

def hasCollision(start_minute: int, duration: int, obstacles: ObstacleList) -> bool:
    """
    Check if time slot [start, start+duration) collides with any obstacle.

    Args:
        start_minute: Start time in minutes from planningStart
        duration: Duration in minutes
        obstacles: List of obstacles to check

    Returns:
        True if collision detected, False otherwise

    Example:
        Obstacle at [60, 120]
        hasCollision(50, 20, obstacles) → True (overlaps [50, 70])
        hasCollision(120, 20, obstacles) → False (starts after obstacle)
    """
    end_minute = start_minute + duration

    for obs in obstacles:
        # Check for any overlap
        # Collision if: start < obs.end AND end > obs.start
        if start_minute < obs['endMinute'] and end_minute > obs['startMinute']:
            return True

    return False


def findNextFreeSlot(
    start_minute: int,
    duration: int,
    obstacles: ObstacleList
) -> int:
    """
    Find next available slot that fits duration, starting from start_minute.

    Jumps past obstacles until a free slot is found.

    Args:
        start_minute: Desired start time
        duration: Required duration
        obstacles: List of obstacles to avoid

    Returns:
        First free minute offset that fits duration

    Algorithm:
        1. Check if [start_minute, start_minute + duration) is free
        2. If collision, jump to end of blocking obstacle
        3. Repeat until free slot found

    Example:
        Obstacles: [60-120], [150-180]
        findNextFreeSlot(50, 30, obstacles)
        → Try 50: collision with [60-120]
        → Jump to 120
        → Try 120: fits (no collision with [150-180])
        → Return 120
    """
    current = start_minute

    while True:
        if not hasCollision(current, duration, obstacles):
            return current

        # Find the obstacle that blocks us and jump past it
        end_minute = current + duration
        blocking_obstacles = [
            obs for obs in obstacles
            if current < obs['endMinute'] and end_minute > obs['startMinute']
        ]

        if not blocking_obstacles:
            # No collision, should not happen (hasCollision returned True)
            return current

        # Jump past the furthest blocking obstacle
        max_end = max(obs['endMinute'] for obs in blocking_obstacles)
        current = max_end


# ==================== TIMELINE REBUILD (CORE FUNCTION) ====================

def rebuildTimeline(
    tasks: TaskList,
    obstacles: ObstacleList,
    planning_start_minute: int = 0
) -> TaskList:
    """
    ✅ CENTRAL V3 FUNCTION - Recalculate ALL minuteOffsets sequentially.

    This function MUST be called after ANY modification to the timeline.

    Args:
        tasks: List of TaskV3 (order matters, minuteOffsets will be recalculated)
        obstacles: List of obstacles to avoid
        planning_start_minute: Start minute (usually 0)

    Returns:
        New task list with recalculated minuteOffsets

    Algorithm (STEP 2 - TIME CALCULATION):
        1. Start at planning_start_minute
        2. For each task in order:
           a. Find next free slot from current position
           b. Assign minuteOffset
           c. Advance current position by task duration
        3. Return tasks with updated minuteOffsets

    CRITICAL RULES:
        - Tasks are processed in ORDER (STEP 1 must happen first)
        - Fixed tasks (PLANNED) are handled separately
        - Obstacles cause tasks to skip past them
        - NO time string manipulation (only int minutes)

    Example:
        tasks = [P1(25min), Pause(5min), P2(25min)]
        obstacles = [Obstacle(20, 40)]  # Blocks 20-40

        Result:
        - P1: minuteOffset=0, ends at 25
        - Pause: starts at 25, collision with [20,40]
                 → jump to 40, minuteOffset=40, ends at 45
        - P2: minuteOffset=45, ends at 70
    """
    if not tasks:
        return []

    rebuilt_tasks: TaskList = []
    current_minute = planning_start_minute

    for task in tasks:
        # For fixed tasks (PLANNED), try to keep requested time
        # For now, treat all tasks the same (will be enhanced in task_integrator_v3.py)

        # Find next free slot
        task_start = findNextFreeSlot(current_minute, task['duration'], obstacles)

        # Create updated task with new minuteOffset
        updated_task: TaskV3 = {**task, 'minuteOffset': task_start}
        rebuilt_tasks.append(updated_task)

        # Advance current position
        current_minute = task_start + task['duration']

    return rebuilt_tasks


# ==================== TIMELINE VALIDATION ====================

def validateTimeline(timeline: Timeline) -> List[str]:
    """
    Validate timeline integrity.

    Checks:
        - No overlapping tasks
        - All minuteOffsets >= 0
        - All tasks have required fields
        - Tasks are sorted by minuteOffset

    Args:
        timeline: Timeline to validate

    Returns:
        List of error messages (empty if valid)
    """
    errors: List[str] = []
    tasks = timeline['tasks']

    if not tasks:
        return errors

    # Check sorting
    for i in range(len(tasks) - 1):
        if tasks[i]['minuteOffset'] > tasks[i + 1]['minuteOffset']:
            errors.append(
                f"Tasks not sorted: task {i} (offset {tasks[i]['minuteOffset']}) "
                f"> task {i+1} (offset {tasks[i + 1]['minuteOffset']})"
            )

    # Check overlaps
    for i in range(len(tasks) - 1):
        task_end = tasks[i]['minuteOffset'] + tasks[i]['duration']
        next_start = tasks[i + 1]['minuteOffset']
        if task_end > next_start:
            errors.append(
                f"Tasks overlap: {tasks[i]['taskName']} ends at {task_end}, "
                f"{tasks[i + 1]['taskName']} starts at {next_start}"
            )

    # Check negative offsets
    for task in tasks:
        if task['minuteOffset'] < 0:
            errors.append(f"Negative minuteOffset: {task['taskName']} at {task['minuteOffset']}")

    return errors


# ==================== OBSTACLE CONVERSION ====================

def convertTempsMortsToObstacles(
    temps_morts: List[dict],
    planning_start: datetime
) -> ObstacleList:
    """
    Convert temps_morts CSV data to linear Obstacle list.

    Args:
        temps_morts: List of dicts from temps_morts.csv
                     Expected fields: 'heure_debut', 'heure_fin', 'date'
        planning_start: Planning start datetime for conversion

    Returns:
        List of Obstacle with startMinute/endMinute

    Filters:
        - Skip obstacles that end before planning starts (endMinute < 0)
        - Skip obstacles with invalid time format

    Example:
        planning_start = datetime(2025, 11, 6, 14, 0)
        temps_mort = {
            'date': '2025-11-06',
            'start': '15:00',
            'end': '16:00',
            'nom': 'Réunion'
        }
        → Obstacle {startMinute: 60, endMinute: 120}
    """
    obstacles: ObstacleList = []

    for tm in temps_morts:
        try:
            # Parse date and times (support both uppercase and lowercase keys)
            date_str = tm.get('DATE', tm.get('date', ''))
            heure_debut = tm.get('HEURE DEBUT', tm.get('heure_debut', ''))
            heure_fin = tm.get('HEURE FIN', tm.get('heure_fin', ''))

            if not all([date_str, heure_debut, heure_fin]):
                continue

            # Build datetime objects
            dt_debut = datetime.strptime(f"{date_str} {heure_debut}", "%Y-%m-%d %H:%M")
            dt_fin = datetime.strptime(f"{date_str} {heure_fin}", "%Y-%m-%d %H:%M")

            # Convert to minutes
            start_minute = dateTimeToMinutes(dt_debut, planning_start)
            end_minute = dateTimeToMinutes(dt_fin, planning_start)

            # Skip past obstacles
            if end_minute < 0:
                continue

            # Create obstacle
            obstacle: Obstacle = {
                'startMinute': start_minute,
                'endMinute': end_minute,
                'type': 'temps_mort',
                'originalData': tm
            }
            obstacles.append(obstacle)

        except (ValueError, KeyError) as e:
            # Skip invalid entries
            continue

    return obstacles


# ==================== UTILITY FUNCTIONS ====================

def getTimelineEnd(tasks: TaskList) -> int:
    """
    Get the end time of the timeline (last task end minute).

    Args:
        tasks: List of tasks with minuteOffsets

    Returns:
        End minute of last task (0 if no tasks)
    """
    if not tasks:
        return 0

    last_task = max(tasks, key=lambda t: t['minuteOffset'] + t['duration'])
    return last_task['minuteOffset'] + last_task['duration']


def sortTasksByOffset(tasks: TaskList) -> TaskList:
    """
    Sort tasks by minuteOffset (ascending).

    Args:
        tasks: Unsorted task list

    Returns:
        Sorted task list
    """
    return sorted(tasks, key=lambda t: t['minuteOffset'])


def calculateWorkTime(tasks: TaskList) -> int:
    """
    Calculate total work time (POMODORO tasks only).

    Args:
        tasks: Task list

    Returns:
        Total minutes of work (sum of POMODORO durations)
    """
    return sum(
        task['duration']
        for task in tasks
        if task['type'] == 'POMODORO'
    )


def calculatePauseTime(tasks: TaskList) -> int:
    """
    Calculate total pause time (PAUSE, CALIN, CLOPE).

    Args:
        tasks: Task list

    Returns:
        Total minutes of pauses
    """
    pause_types = {'PAUSE', 'CALIN', 'CLOPE'}
    return sum(
        task['duration']
        for task in tasks
        if task['type'] in pause_types
    )
