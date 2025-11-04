"""
REST API Routes - GitFocus Planner V2

Blueprint: gitfocus_bp
Prefix: /api/v2/gitfocus

Total Endpoints: 28
- Health & Data (6)
- Planning Generation & Export (2) 🆕
- Pomodoro Tasks CRUD (3)
- Respiration Tasks CRUD (3)
- Recurrent Tasks CRUD (4)
- Planned Tasks CRUD (3)
- Categories (2)
- Interface (1)
- Stats (1)
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from pathlib import Path

from webapp.config import Config

logger = logging.getLogger(__name__)

# Server startup timestamp (for version tracking)
SERVER_START_TIME = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Create blueprint
gitfocus_bp = Blueprint('gitfocus_v2', __name__, url_prefix='/api/v2/gitfocus')


# ============================================================================
# HEALTH & DATA RETRIEVAL
# ============================================================================

@gitfocus_bp.route('/tasks/pomodoro', methods=['GET'])
def get_pomodoro_tasks():
    """Get all Pomodoro tasks."""
    try:
        from backend.planning_engine.data_loader import load_pomodoro_tasks

        tasks = load_pomodoro_tasks(Config.DATA_DIR / 'LISTE_MERE.v2.csv')

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })

    except Exception as e:
        logger.error(f"Error loading Pomodoro tasks: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/tasks/respiration', methods=['GET'])
def get_respiration_tasks():
    """Get all respiration tasks (sorted by popularity)."""
    try:
        from backend.planning_engine.data_loader import load_respiration_tasks

        tasks = load_respiration_tasks(Config.DATA_DIR / 'TACHES_RESPIRATOIRES.v2.csv')

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks)
        })

    except Exception as e:
        logger.error(f"Error loading respiration tasks: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/tasks/recurrent', methods=['GET'])
def get_recurrent_tasks():
    """Get all recurrent tasks."""
    try:
        from backend.planning_engine.data_loader import load_recurrent_tasks

        active_only = request.args.get('active_only', 'false').lower() == 'true'
        tasks = load_recurrent_tasks(Config.DATA_DIR / 'TACHES_RECURRENTES.v2.csv', active_only=active_only)

        active_count = len([t for t in tasks if t.get('is_active') == 1])

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks),
            'active_count': active_count
        })

    except Exception as e:
        logger.error(f"Error loading recurrent tasks: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/tasks/planned', methods=['GET'])
def get_planned_tasks():
    """Get planned tasks (optional date filter)."""
    try:
        from backend.planning_engine.data_loader import load_planned_tasks

        date = request.args.get('date')  # Optional YYYY-MM-DD
        tasks = load_planned_tasks(Config.DATA_DIR / 'TACHES_PLANIFIEES.v2.csv', date=date)

        return jsonify({
            'success': True,
            'tasks': tasks,
            'count': len(tasks),
            'date': date
        })

    except Exception as e:
        logger.error(f"Error loading planned tasks: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories and sub-categories."""
    try:
        from backend.planning_engine.data_loader import load_categories

        categories = load_categories(Config.DATA_DIR / 'categories.csv')

        return jsonify({
            'success': True,
            'categories': categories
        })

    except Exception as e:
        logger.error(f"Error loading categories: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/temps-morts', methods=['GET'])
def get_temps_morts():
    """Get temps_morts for specific date."""
    try:
        date = request.args.get('date')
        if not date:
            return jsonify({'success': False, 'error': 'Missing date parameter'}), 400

        from backend.planning_engine.data_loader import load_temps_morts

        temps_morts = load_temps_morts(Config.DATA_DIR / 'temps_morts.csv', date)

        return jsonify({
            'success': True,
            'temps_morts': temps_morts,
            'count': len(temps_morts),
            'date': date
        })

    except Exception as e:
        logger.error(f"Error loading temps_morts: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PLANNING GENERATION & EXPORT (🆕 Main Features)
# ============================================================================

@gitfocus_bp.route('/planning/generate-auto', methods=['POST'])
def generate_planning_auto():
    """
    🆕 Generate planning with automatic recurrent task selection (intelligent scoring).

    Request Body:
        {
            "date": "2025-10-30",
            "start_time": "18:30",  # 🆕 Optional (HH:MM format, will calculate if not provided)
            "pomodoro_task_ids": ["1", "2", "3"],
            "respiration_task_ids": ["R_001", "R_002", "R_001"],  # 🆕 Can contain duplicates
            "max_recurrent_tasks": 10,
            # 🆕 Phase 4: Advanced options
            "enable_clopes": false,  # Optional
            "clopes_interval_min": 120,  # Optional (default 120)
            "enable_calins": false,  # Optional
            "allow_consecutive_pauses": false  # Optional
        }

    Response:
        {
            "success": true,
            "data": {
                "date": "2025-10-30",
                "planning": [...],
                "stats": {...},
                "recurrent_task_scores": [...]  # 🆕 Transparency
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Missing request body'}), 400

        date = data.get('date')
        start_time = data.get('start_time')  # 🆕 HH:MM format (optional, will calculate if not provided)
        pomodoro_ids = data.get('pomodoro_task_ids', [])
        respiration_ids = data.get('respiration_task_ids', [])  # 🆕 Can contain duplicates
        max_recurrent = data.get('max_recurrent_tasks', 10)

        # 🆕 Phase 4: Advanced options
        enable_clopes = data.get('enable_clopes', False)
        clopes_interval = data.get('clopes_interval_min', 120)
        enable_calins = data.get('enable_calins', False)
        allow_consecutive_pauses = data.get('allow_consecutive_pauses', False)

        if not date:
            return jsonify({'success': False, 'error': 'Missing date'}), 400

        logger.info(f"🔍 DEBUG: Generating auto planning for {date}")
        logger.info(f"🔍 DEBUG: start_time: {start_time}")
        logger.info(f"🔍 DEBUG: Received {len(pomodoro_ids)} Pomodoro IDs: {pomodoro_ids}")
        logger.info(f"🔍 DEBUG: Received {len(respiration_ids)} Respiration IDs: {respiration_ids}")
        logger.info(f"🔍 DEBUG: max_recurrent_tasks: {max_recurrent}")
        logger.info(f"🔍 DEBUG: Advanced options - clopes: {enable_clopes}, calins: {enable_calins}, consecutive: {allow_consecutive_pauses}")

        from backend.planning_engine.planning_generator import generate_planning_auto

        result = generate_planning_auto(
            date=date,
            start_time=start_time,
            pomodoro_ids=pomodoro_ids,
            respiration_ids=respiration_ids,
            data_dir=Config.DATA_DIR,
            max_recurrent_tasks=max_recurrent,
            enable_clopes=enable_clopes,
            clopes_interval_min=clopes_interval,
            enable_calins=enable_calins,
            allow_consecutive_pauses=allow_consecutive_pauses
        )

        return jsonify({
            'success': True,
            'data': result
        })

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

    except Exception as e:
        logger.error(f"Error generating planning: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/planning/export', methods=['POST'])
def export_planning():
    """
    🆕 Export planning to CSV + log placements for learning.

    Request Body:
        {
            "date": "2025-10-30",
            "planning": [...]  # Complete planning (may be edited)
        }

    Response:
        {
            "success": true,
            "message": "Planning exported successfully",
            "file_path": "...",
            "task_count": 45,
            "placements_logged": 12
        }

    Side Effects:
        - Writes to planned.csv (overwrites)
        - Appends to planning_placements_history.csv (🆕 learning)
        - Increments EXPORT_COUNT for respiration tasks
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Missing request body'}), 400

        date = data.get('date')
        planning = data.get('planning', [])

        if not date or not planning:
            return jsonify({'success': False, 'error': 'Missing date or planning'}), 400

        logger.info(f"Exporting planning for {date} with {len(planning)} slots")

        # Write planned.csv
        from backend.planning_engine.data_writer import write_planning_csv

        planned_csv = Config.DATA_DIR / 'planned.csv'
        write_planning_csv(planned_csv, planning)

        # Log placements for learning (🆕)
        from backend.planning_engine.placement_logger import log_planning_placements

        export_timestamp = datetime.now().isoformat()
        placements_logged = log_planning_placements(planning, export_timestamp, Config.DATA_DIR)

        # Increment export count for respiration tasks
        respiration_ids = [s['task_id'] for s in planning if s.get('type') == 'respiration']
        if respiration_ids:
            from backend.planning_engine.data_writer import increment_respiration_export_count

            increment_respiration_export_count(
                Config.DATA_DIR / 'TACHES_RESPIRATOIRES.v2.csv',
                respiration_ids
            )

        return jsonify({
            'success': True,
            'message': 'Planning exported successfully',
            'file_path': str(planned_csv),
            'task_count': len(planning),
            'placements_logged': placements_logged
        })

    except Exception as e:
        logger.error(f"Error exporting planning: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# POMODORO TASKS CRUD
# ============================================================================

@gitfocus_bp.route('/tasks/pomodoro', methods=['POST'])
def create_pomodoro_task():
    """Create new Pomodoro task."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Missing request body'}), 400

        from backend.planning_engine.data_writer import create_pomodoro_task

        create_pomodoro_task(Config.DATA_DIR / 'LISTE_MERE.v2.csv', data)

        return jsonify({
            'success': True,
            'message': f"Created Pomodoro task {data.get('id')}"
        }), 201

    except Exception as e:
        logger.error(f"Error creating Pomodoro task: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/tasks/pomodoro/<task_id>', methods=['PUT'])
def update_pomodoro_task(task_id):
    """Update Pomodoro task."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Missing request body'}), 400

        from backend.planning_engine.data_writer import update_pomodoro_task

        update_pomodoro_task(Config.DATA_DIR / 'LISTE_MERE.v2.csv', task_id, data)

        return jsonify({
            'success': True,
            'message': f"Updated Pomodoro task {task_id}"
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404

    except Exception as e:
        logger.error(f"Error updating Pomodoro task: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/tasks/pomodoro/<task_id>', methods=['DELETE'])
def delete_pomodoro_task(task_id):
    """Delete Pomodoro task."""
    try:
        from backend.planning_engine.data_writer import delete_pomodoro_task

        delete_pomodoro_task(Config.DATA_DIR / 'LISTE_MERE.v2.csv', task_id)

        return jsonify({
            'success': True,
            'message': f"Deleted Pomodoro task {task_id}"
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404

    except Exception as e:
        logger.error(f"Error deleting Pomodoro task: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# RECURRENT TASKS CRUD
# ============================================================================

@gitfocus_bp.route('/tasks/recurrent/<task_id>/toggle', methods=['PATCH'])
def toggle_recurrent_task(task_id):
    """Toggle IS_ACTIVE for recurrent task."""
    try:
        data = request.get_json()
        is_active = data.get('is_active')

        if is_active not in [0, 1]:
            return jsonify({'success': False, 'error': 'is_active must be 0 or 1'}), 400

        from backend.planning_engine.data_writer import update_recurrent_task_active

        update_recurrent_task_active(Config.DATA_DIR / 'TACHES_RECURRENTES.v2.csv', task_id, is_active)

        return jsonify({
            'success': True,
            'message': f"Toggled recurrent task {task_id} to {'active' if is_active else 'inactive'}"
        })

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404

    except Exception as e:
        logger.error(f"Error toggling recurrent task: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CATEGORIES
# ============================================================================

@gitfocus_bp.route('/categories', methods=['POST'])
def add_category():
    """Add new category/sub-category."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Missing request body'}), 400

        category = data.get('category')
        sub_category = data.get('sub_category')

        if not category:
            return jsonify({'success': False, 'error': 'Missing category'}), 400

        from backend.planning_engine.data_writer import add_category

        add_category(Config.DATA_DIR / 'categories.csv', category, sub_category or '')

        return jsonify({
            'success': True,
            'message': f"Added category: {category} -> {sub_category}"
        })

    except Exception as e:
        logger.error(f"Error adding category: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# STATS & INTERFACE
# ============================================================================

@gitfocus_bp.route('/stats/history', methods=['GET'])
def get_history_stats():
    """Get planning history statistics."""
    try:
        from backend.planning_engine.placement_logger import get_history_stats

        stats = get_history_stats(Config.DATA_DIR)

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error getting history stats: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@gitfocus_bp.route('/interface', methods=['GET'])
def show_interface():
    """Render web interface."""
    return render_template('gitfocus_v2.html', server_version=SERVER_START_TIME)
