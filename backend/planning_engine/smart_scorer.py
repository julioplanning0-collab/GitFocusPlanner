"""
Smart Scorer Module - GitFocus Planner V2 🆕
Intelligent scoring system for automatic recurrent task selection.

LEARNING ALGORITHM (4 Criteria):
1. Recurrence DUE (50%) - Urgency (overdue tasks prioritized)
2. Day Frequency (20%) - Habits (Monday → water plants)
3. Global Frequency (15%) - Popularity (often-used tasks)
4. Recency (15%) - Actuality (recently planned tasks)

SCORE RANGE: 0.0 to 100.0

WHY:
- System learns which tasks user prefers at which times
- Automatically suggests most relevant tasks
- Improves over time as history grows
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# MAIN SCORING FUNCTION
# ============================================================================

def calculate_task_score(
    task: Dict,
    target_date: str,
    planning_history: List[Dict],
    done_history: List[Dict]
) -> float:
    """
    Calculate comprehensive score for a recurrent task.

    Args:
        task: Recurrent task dictionary
        target_date: Target date (YYYY-MM-DD)
        planning_history: List from planning_placements_history.csv
        done_history: List from done_v2.csv

    Returns:
        Score from 0.0 to 100.0

    Breakdown:
        - 0-50 points: Recurrence DUE (urgency)
        - 0-20 points: Day of week frequency (habits)
        - 0-15 points: Global frequency (popularity)
        - 0-15 points: Recency (actuality)
    """
    score = 0.0

    try:
        # Criterion 1: Recurrence DUE (50%)
        rec_score = calculate_recurrence_score(task, target_date, done_history)
        score += rec_score
        logger.debug(f"Task {task['id']} recurrence_score={rec_score:.1f}")

        # Criterion 2: Day Frequency (20%)
        day_score = calculate_day_frequency_score(task, target_date, planning_history)
        score += day_score
        logger.debug(f"Task {task['id']} day_frequency_score={day_score:.1f}")

        # Criterion 3: Global Frequency (15%)
        global_score = calculate_global_frequency_score(task, planning_history)
        score += global_score
        logger.debug(f"Task {task['id']} global_frequency_score={global_score:.1f}")

        # Criterion 4: Recency (15%)
        recency_score = calculate_recency_score(task, target_date, planning_history)
        score += recency_score
        logger.debug(f"Task {task['id']} recency_score={recency_score:.1f}")

        logger.info(f"Task {task['id']} ({task['name']}) FINAL SCORE: {score:.1f}/100")
        return score

    except Exception as e:
        logger.error(f"Error calculating score for task {task.get('id', 'UNKNOWN')}: {e}", exc_info=True)
        return 0.0  # Return neutral score on error


# ============================================================================
# CRITERION 1: RECURRENCE DUE (50% - Maximum Weight)
# ============================================================================

def calculate_recurrence_score(task: Dict, target_date: str, done_history: List[Dict]) -> float:
    """
    Score based on urgency (overdue tasks).

    Logic:
    - Never done → 50.0 points (max)
    - Overdue by X days → min(50.0, X * 10.0) points
    - Done today → 0.0 points
    - Not yet due → 0.0 points

    Args:
        task: Recurrent task
        target_date: Target date (YYYY-MM-DD)
        done_history: Completion history

    Returns:
        Score from 0.0 to 50.0
    """
    # Find last execution
    last_done = None

    for record in done_history:
        if record['ID'] == task['id'] and record['TYPE'] == 'recurrent':
            try:
                done_date = datetime.fromisoformat(record['DONE_AT']).date()
                if last_done is None or done_date > last_done:
                    last_done = done_date
            except (ValueError, TypeError) as e:
                logger.debug(f"Invalid DONE_AT for task {task['id']}: {e}")
                continue

    # Fallback to LAST_DONE_DATE from CSV
    if task.get('last_done_date'):
        try:
            csv_date = datetime.strptime(task['last_done_date'], "%d.%m.%y").date()
            if last_done is None or csv_date > last_done:
                last_done = csv_date
        except ValueError as e:
            logger.debug(f"Invalid last_done_date for task {task['id']}: {e}")

    if last_done is None:
        # Never done → Very urgent
        logger.debug(f"Task {task['id']} never done → 50.0 points")
        return 50.0

    # Calculate days since last done
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    days_since = (target - last_done).days

    # Get recurrence interval
    interval = task.get('recurrence_interval', 1)
    rec_type = task.get('recurrence_type', 'daily')

    # Calculate expected interval in days
    if rec_type == 'daily':
        expected_days = interval
    elif rec_type == 'weekly':
        expected_days = interval * 7
    elif rec_type == 'monthly':
        expected_days = interval * 30
    else:
        logger.warning(f"Unknown recurrence_type '{rec_type}' for task {task['id']}, assuming daily")
        expected_days = interval

    # Calculate overdue days
    days_overdue = days_since - expected_days

    if days_overdue <= 0:
        # Not yet due
        logger.debug(f"Task {task['id']} not yet due (done {days_since} days ago, interval {expected_days}) → 0.0 points")
        return 0.0

    # More overdue = more urgent (max 50 points)
    score = min(50.0, days_overdue * 10.0)
    logger.debug(f"Task {task['id']} overdue by {days_overdue} days → {score:.1f} points")
    return score


# ============================================================================
# CRITERION 2: DAY OF WEEK FREQUENCY (20%)
# ============================================================================

def calculate_day_frequency_score(task: Dict, target_date: str, planning_history: List[Dict]) -> float:
    """
    Score based on how often task is planned on this day of week.

    Logic:
    - Count: How many times task planned on this weekday
    - Total: How many times task planned overall
    - Frequency = Count / Total
    - Score = Frequency * 20

    Args:
        task: Recurrent task
        target_date: Target date (YYYY-MM-DD)
        planning_history: Planning placement history

    Returns:
        Score from 0.0 to 20.0
    """
    target_day = datetime.strptime(target_date, "%Y-%m-%d").weekday()  # 0=Monday, 6=Sunday

    # Filter history for this task
    task_history = [p for p in planning_history if p['task_id'] == task['id']]

    if len(task_history) == 0:
        # No history → Neutral score
        logger.debug(f"Task {task['id']} has no planning history → 10.0 points (neutral)")
        return 10.0

    # Count occurrences on this weekday
    count_this_day = sum(1 for p in task_history if int(p.get('day_of_week', -1)) == target_day)

    frequency = count_this_day / len(task_history)
    score = frequency * 20.0

    logger.debug(f"Task {task['id']} planned {count_this_day}/{len(task_history)} times on weekday {target_day} → {score:.1f} points")
    return score


# ============================================================================
# CRITERION 3: GLOBAL FREQUENCY (15%)
# ============================================================================

def calculate_global_frequency_score(task: Dict, planning_history: List[Dict]) -> float:
    """
    Score based on overall popularity (total planning count).

    Logic:
    - Count total plannings for this task
    - Normalize by most frequently planned task
    - Score = (Count / Max_Count) * 15

    Args:
        task: Recurrent task
        planning_history: Planning placement history

    Returns:
        Score from 0.0 to 15.0
    """
    # Count plannings for this task
    task_count = len([p for p in planning_history if p['task_id'] == task['id']])

    if len(planning_history) == 0:
        # No history → Neutral score
        logger.debug(f"No planning history at all → 7.5 points (neutral)")
        return 7.5

    # Find most frequently planned task
    all_task_ids = set(p['task_id'] for p in planning_history)
    max_count = max(
        len([p for p in planning_history if p['task_id'] == tid])
        for tid in all_task_ids
    ) if all_task_ids else 1

    if max_count == 0:
        return 7.5  # Neutral

    frequency = task_count / max_count
    score = frequency * 15.0

    logger.debug(f"Task {task['id']} planned {task_count} times (max={max_count}) → {score:.1f} points")
    return score


# ============================================================================
# CRITERION 4: RECENCY (15%)
# ============================================================================

def calculate_recency_score(task: Dict, target_date: str, planning_history: List[Dict]) -> float:
    """
    Score based on how recently task was planned.

    Logic:
    - Find last planning date
    - Days since = Target - Last_Planning
    - Score decays linearly from 15 (yesterday) to 0 (>30 days)

    Args:
        task: Recurrent task
        target_date: Target date (YYYY-MM-DD)
        planning_history: Planning placement history

    Returns:
        Score from 0.0 to 15.0
    """
    task_history = [p for p in planning_history if p['task_id'] == task['id']]

    if len(task_history) == 0:
        # No history → Neutral score
        logger.debug(f"Task {task['id']} has no planning history → 7.5 points (neutral)")
        return 7.5

    # Find last planning date
    try:
        last_planning_date = max(
            datetime.strptime(p['date'], "%Y-%m-%d")
            for p in task_history
            if p.get('date')
        )
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing dates in planning history for task {task['id']}: {e}")
        return 7.5  # Neutral

    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    days_since = (target_dt - last_planning_date).days

    # Score decays linearly
    if days_since <= 0:
        # Planned today or in future → Max score
        score = 15.0
    elif days_since >= 30:
        # More than 30 days ago → Min score
        score = 0.0
    else:
        # Linear decay
        score = 15.0 * (1 - days_since / 30.0)

    logger.debug(f"Task {task['id']} last planned {days_since} days ago → {score:.1f} points")
    return score


# ============================================================================
# BATCH SCORING (for all recurrent tasks)
# ============================================================================

def score_all_recurrent_tasks(
    recurrent_tasks: List[Dict],
    target_date: str,
    planning_history: List[Dict],
    done_history: List[Dict]
) -> List[Dict]:
    """
    Calculate scores for all recurrent tasks and sort by score DESC.

    Args:
        recurrent_tasks: List of all active recurrent tasks
        target_date: Target date (YYYY-MM-DD)
        planning_history: Planning placement history
        done_history: Completion history

    Returns:
        List of dicts: [{"task": {...}, "score": 87.5}, ...]
        Sorted by score descending (highest first)
    """
    scored_tasks = []

    for task in recurrent_tasks:
        score = calculate_task_score(task, target_date, planning_history, done_history)
        scored_tasks.append({'task': task, 'score': score})

    # Sort by score descending
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)

    logger.info(f"Scored {len(scored_tasks)} recurrent tasks, top score: {scored_tasks[0]['score']:.1f} ({scored_tasks[0]['task']['name']})")

    return scored_tasks
