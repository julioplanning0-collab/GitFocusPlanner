"""
API REST pour GitFocus Planner V3
Routes SANS numero de version (clean URLs)
"""

import logging
from flask import Blueprint, request, jsonify
from pathlib import Path
from datetime import datetime

from backend.planning_engine_v3.data_loader import (
    load_work_tasks,
    load_pauses,
    load_recurrent_tasks,
    load_temps_morts
)
from backend.planning_engine_v3.planning_generator import generate_planning
from backend.planning_engine_v3.data_writer import write_planning_csv

logger = logging.getLogger(__name__)

# Blueprint SANS numero de version
planning_bp = Blueprint('planning', __name__, url_prefix='/api/planning')


@planning_bp.route('/tasks/pomodoro', methods=['GET'])
def get_pomodoro_tasks():
    try:
        data_dir = Path('prod_data')
        tasks = load_work_tasks(data_dir)
        return jsonify({'success': True, 'data': tasks, 'count': len(tasks)})
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@planning_bp.route('/generate', methods=['POST'])
def generate_planning_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Body JSON requis'}), 400

        date = data.get('date')
        planning_start = data.get('planningStartTime')

        if not date or not planning_start:
            return jsonify({'success': False, 'error': 'Champs requis manquants'}), 400

        data_dir = Path('prod_data')
        work_tasks = load_work_tasks(data_dir)
        pauses = load_pauses(data_dir, active_only=True)
        recurrent_tasks = load_recurrent_tasks(data_dir, active_only=True)
        temps_morts = load_temps_morts(data_dir, date)

        result = generate_planning(
            date=date,
            planningStartTime=planning_start,
            work_tasks=work_tasks,
            pauses=pauses,
            recurrent_tasks=recurrent_tasks,
            planned_tasks=[],
            temps_morts=temps_morts
        )

        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@planning_bp.route('/export', methods=['POST'])
def export_planning():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Body JSON requis'}), 400
        
        date = data.get('date')
        timeline = data.get('timeline', [])
        
        csv_path = Path('prod_data') / 'planned.csv'
        write_planning_csv(csv_path, timeline, date)
        
        return jsonify({'success': True, 'data': {'csv_path': str(csv_path), 'task_count': len(timeline)}})
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@planning_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'version': '3.0'})
