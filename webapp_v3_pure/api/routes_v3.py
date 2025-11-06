"""
V3 PURE - NO V2 LOGIC ALLOWED

Flask REST API routes for V3 timeline-linear architecture.

CRITICAL RULES:
- NO imports from backend/planning_engine/ (old V2 code)
- ONLY delegate to backend/planning_engine_v3_pure/
- Return JSON responses (NO server-side HTML rendering for planning)
- Client-side controls ALL UI logic

ENDPOINTS (from FLUX_V3_CORRECT.md):
    GET  /api/v3/tasks/pomodoro
    GET  /api/v3/tasks/recurrent?pause_only=true
    GET  /api/v3/tasks/recurrent?exclude_pauses=true
    GET  /api/v3/temps-morts?date=YYYY-MM-DD
    POST /api/v3/planning/generate
    POST /api/v3/planning/export
"""

from flask import Blueprint, request, jsonify
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# V3 PURE imports ONLY
from backend.planning_engine_v3_pure.data_loader_v3 import (
    load_pomodoro_tasks_by_ids,
    load_recurrent_tasks_by_ids_v3,
    load_temps_morts,
)
from backend.planning_engine_v3_pure.planning_generator_v3 import (
    generate_planning_v3,
    PlanningOptions
)
from backend.planning_engine_v3_pure.data_writer_v3 import (
    write_planning_csv,
    log_pause_usage
)

logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('api_v3', __name__, url_prefix='/api/v3')

# Data directory (TODO: make configurable)
DATA_DIR = Path(__file__).parent.parent.parent / 'data' / 'prod_data'


# ==================== HELPER FUNCTIONS ====================

def _get_data_dir() -> Path:
    """Get data directory path (configurable)"""
    return DATA_DIR


def _error_response(message: str, status_code: int = 400) -> tuple:
    """Standard error response"""
    return jsonify({'success': False, 'error': message}), status_code


# ==================== ENDPOINT 1: GET POMODORO TASKS ====================

@bp.route('/tasks/pomodoro', methods=['GET'])
def get_pomodoro_tasks():
    """
    Get all pomodoro tasks (LISTE_MERE.v3.csv)

    Returns:
        JSON: {success: true, tasks: [...]}

    Example:
        GET /api/v3/tasks/pomodoro
    """
    try:
        data_dir = _get_data_dir()
        csv_path = data_dir / 'LISTE_MERE.v3.csv'

        # Load all pomodoro tasks (no ID filter)
        from backend.planning_engine_v3_pure.data_loader_v3 import load_all_pomodoro_tasks
        tasks = load_all_pomodoro_tasks(csv_path)

        return jsonify({
            'success': True,
            'tasks': tasks
        })

    except Exception as e:
        logger.error(f"Failed to load pomodoro tasks: {e}")
        return _error_response(f"Failed to load tasks: {str(e)}", 500)


# ==================== ENDPOINT 2 & 3: GET RECURRENT TASKS ====================

@bp.route('/tasks/recurrent', methods=['GET'])
def get_recurrent_tasks():
    """
    Get recurrent tasks with optional filtering.

    Query params:
        pause_only (bool): If true, return only IS_PAUSE=1 (pauses)
        exclude_pauses (bool): If true, return only IS_PAUSE=0 (recurrents)

    Returns:
        JSON: {success: true, tasks: [...]}

    Examples:
        GET /api/v3/tasks/recurrent?pause_only=true  → Pauses only
        GET /api/v3/tasks/recurrent?exclude_pauses=true → Recurrents only
        GET /api/v3/tasks/recurrent → All recurrent tasks
    """
    try:
        data_dir = _get_data_dir()
        csv_path = data_dir / 'TACHES_RECURRENTES.v3.csv'

        pause_only = request.args.get('pause_only', 'false').lower() == 'true'
        exclude_pauses = request.args.get('exclude_pauses', 'false').lower() == 'true'

        # Load all recurrent tasks
        from backend.planning_engine_v3_pure.data_loader_v3 import load_all_recurrent_tasks
        all_tasks = load_all_recurrent_tasks(csv_path)

        # Filter by IS_PAUSE
        if pause_only:
            tasks = [t for t in all_tasks if t.get('IS_PAUSE') == '1']
        elif exclude_pauses:
            tasks = [t for t in all_tasks if t.get('IS_PAUSE') == '0']
        else:
            tasks = all_tasks

        return jsonify({
            'success': True,
            'tasks': tasks
        })

    except Exception as e:
        logger.error(f"Failed to load recurrent tasks: {e}")
        return _error_response(f"Failed to load tasks: {str(e)}", 500)


# ==================== ENDPOINT 4: GET TEMPS MORTS (OBSTACLES) ====================

@bp.route('/temps-morts', methods=['GET'])
def get_temps_morts():
    """
    Get obstacles (temps morts) for a specific date.

    Query params:
        date (str): Date in YYYY-MM-DD format

    Returns:
        JSON: {success: true, temps_morts: [...]}

    Example:
        GET /api/v3/temps-morts?date=2025-11-06
    """
    try:
        date_str = request.args.get('date')
        if not date_str:
            return _error_response("Missing 'date' query parameter")

        # Validate date format
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return _error_response("Invalid date format. Use YYYY-MM-DD")

        data_dir = _get_data_dir()

        temps_morts = load_temps_morts(date_str)

        return jsonify({
            'success': True,
            'temps_morts': temps_morts
        })

    except Exception as e:
        logger.error(f"Failed to load temps morts: {e}")
        return _error_response(f"Failed to load obstacles: {str(e)}", 500)


# ==================== ENDPOINT 5: POST GENERATE PLANNING ====================

@bp.route('/planning/generate', methods=['POST'])
def generate_planning():
    """
    Generate planning using V3 2-step architecture.

    Request body:
        {
            "date": "YYYY-MM-DD",
            "planning_start_time": "HH:MM",
            "pomodoro_ids": ["TASK001", "TASK002"],
            "pause_ids": ["REC001", "REC003", "REC001"],  # Ordered, duplicates OK
            "recurrent_ids": ["REC002", "REC005"],
            "calin_enabled": true,
            "clope_enabled": false,
            "clope_interval_min": 120
        }

    Returns:
        JSON: {success: true, date, planning: [...], statistics: {...}}

    Example:
        POST /api/v3/planning/generate
        Body: {...}
    """
    try:
        data = request.get_json()

        # Validate required fields
        required = ['date', 'planning_start_time', 'pomodoro_ids', 'pause_ids']
        for field in required:
            if field not in data:
                return _error_response(f"Missing required field: {field}")

        # Extract parameters
        date = data['date']
        planning_start_time = data['planning_start_time']
        pomodoro_ids = data['pomodoro_ids']
        pause_ids = data['pause_ids']
        recurrent_ids = data.get('recurrent_ids', [])

        # Options
        options = PlanningOptions(
            calin_enabled=data.get('calin_enabled', False),
            clope_enabled=data.get('clope_enabled', False),
            clope_interval_min=data.get('clope_interval_min', 120)
        )

        # Generate planning (delegates to V3 Pure backend)
        data_dir = _get_data_dir()
        result = generate_planning_v3(
            date=date,
            planning_start_time=planning_start_time,
            pomodoro_ids=pomodoro_ids,
            pause_ids=pause_ids,
            recurrent_ids=recurrent_ids,
            options=options,
            data_dir=data_dir
        )

        return jsonify(result)

    except ValueError as e:
        logger.warning(f"Invalid planning request: {e}")
        return _error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Failed to generate planning: {e}")
        return _error_response(f"Planning generation failed: {str(e)}", 500)


# ==================== ENDPOINT 6: POST EXPORT PLANNING ====================

@bp.route('/planning/export', methods=['POST'])
def export_planning():
    """
    Export planning to CSV (atomic write).

    Request body:
        {
            "date": "YYYY-MM-DD",
            "planning": [{date, heure_debut, heure_fin, ...}, ...]
        }

    Returns:
        JSON: {success: true, file_path: "..."}

    Example:
        POST /api/v3/planning/export
        Body: {date: "2025-11-06", planning: [...]}
    """
    try:
        data = request.get_json()

        # Validate required fields
        if 'date' not in data or 'planning' not in data:
            return _error_response("Missing 'date' or 'planning' fields")

        date = data['date']
        planning = data['planning']

        if not isinstance(planning, list):
            return _error_response("'planning' must be a list")

        # Determine export filename
        data_dir = _get_data_dir()
        export_path = data_dir / f'planning_{date}.csv'

        # Write CSV (atomic)
        write_planning_csv(export_path, planning)

        # Log pause usage for ML (optional, doesn't block on failure)
        try:
            export_timestamp = datetime.now().isoformat()
            log_pause_usage(planning, export_timestamp, data_dir)
        except Exception as e:
            logger.warning(f"Failed to log pause usage: {e}")

        return jsonify({
            'success': True,
            'file_path': str(export_path),
            'slots_count': len(planning)
        })

    except Exception as e:
        logger.error(f"Failed to export planning: {e}")
        return _error_response(f"Export failed: {str(e)}", 500)


# ==================== HEALTH CHECK ====================

@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'success': True,
        'service': 'GitFocus V3 Pure API',
        'version': '3.0.0',
        'architecture': 'timeline-linear'
    })
