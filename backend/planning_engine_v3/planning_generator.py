"""
Module orchestrateur principal pour la generation de planning
Combine tous les modules pour produire une timeline complete
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .timeline_builder import build_task_sequence, insert_recurrent_tasks, insert_planned_tasks
from .timeline_calculator import assign_times_to_sequence
from .utils import parse_date_iso, time_to_minutes

logger = logging.getLogger(__name__)


# ============================================================================
# ORCHESTRATEUR PRINCIPAL
# ============================================================================

def generate_planning(
    date: str,
    planningStartTime: str,
    work_tasks: List[Dict],
    pauses: List[Dict],
    recurrent_tasks: List[Dict],
    planned_tasks: List[Dict],
    temps_morts: List[Dict]
) -> Dict:
    """
    Genere un planning complet pour une journee.

    Args:
        date: Date du planning (format YYYY-MM-DD)
        planningStartTime: Heure de debut du planning (format HH:MM)
        work_tasks: Liste de taches de travail
        pauses: Liste de pauses
        recurrent_tasks: Liste de taches recurrentes
        planned_tasks: Liste de taches planifiees (heure fixe)
        temps_morts: Liste des temps morts a eviter

    Returns:
        Dictionnaire avec:
            - "timeline": Liste d'items avec start_time, end_time, etc.
            - "statistics": Statistiques du planning

    Raises:
        ValueError: Si date ou heure invalide

    Algorithme:
        1. Valider les entrees (date, heure)
        2. Construire sequence de base (alternance travail/pause)
        3. Assigner les temps absolus (eviter temps_morts)
        4. Inserer taches planifiees (heure fixe)
        5. Inserer taches recurrentes
        6. Calculer statistiques
        7. Retourner timeline complete
    """
    logger.info(f"=== DEBUT generate_planning ===")
    logger.info(f"Date: {date}, Start: {planningStartTime}")
    logger.info(f"Work tasks: {len(work_tasks)}, Pauses: {len(pauses)}")
    logger.info(f"Recurrent: {len(recurrent_tasks)}, Planned: {len(planned_tasks)}")
    logger.info(f"Temps morts: {len(temps_morts)}")

    # Etape 1: Validation des entrees
    try:
        date_obj = parse_date_iso(date)
        logger.info(f"Date validee: {date_obj}")
    except Exception as e:
        logger.error(f"Date invalide: {date} - {e}")
        raise ValueError(f"Date invalide: {date}")

    try:
        time_minutes = time_to_minutes(planningStartTime)
        logger.info(f"Heure validee: {planningStartTime} ({time_minutes} min)")
    except Exception as e:
        logger.error(f"Heure invalide: {planningStartTime} - {e}")
        raise ValueError(f"Heure de debut invalide: {planningStartTime}")

    # Etape 2: Construire sequence de base (alternance travail/pause)
    logger.info("Etape 2: Construction sequence de base")
    sequence = build_task_sequence(
        work_tasks=work_tasks,
        pauses=pauses,
        recurrent_tasks=recurrent_tasks
    )
    logger.info(f"Sequence construite: {len(sequence)} items")

    # Etape 3: Inserer taches planifiees (heure fixe) AVANT assignation temps
    if planned_tasks:
        logger.info(f"Etape 3: Insertion de {len(planned_tasks)} taches planifiees")
        sequence = insert_planned_tasks(
            sequence=sequence,
            planned_tasks=planned_tasks,
            planningStartTime=planningStartTime
        )
        logger.info(f"Sequence apres planned: {len(sequence)} items")

    # Si sequence vide, retourner planning vide
    if len(sequence) == 0:
        logger.warning("Sequence vide - Retour planning vide")
        return {
            "timeline": [],
            "statistics": {
                "total_work_minutes": 0,
                "total_pause_minutes": 0,
                "total_recurrent_minutes": 0,
                "total_planned_minutes": 0,
                "task_count": 0,
                "work_count": 0,
                "pause_count": 0,
                "recurrent_count": 0,
                "planned_count": 0
            }
        }

    # Etape 4: Assigner les temps absolus (eviter temps_morts)
    logger.info("Etape 4: Assignation des temps absolus")
    timeline = assign_times_to_sequence(
        sequence=sequence,
        planningStartTime=planningStartTime,
        date=date,
        temps_morts=temps_morts
    )
    logger.info(f"Timeline avec temps: {len(timeline)} items")

    # Etape 6: Calculer statistiques
    logger.info("Etape 6: Calcul statistiques")
    statistics = _calculate_statistics(timeline)
    logger.info(f"Statistiques: {statistics}")

    # Etape 7: Convertir timeline au format final
    logger.info("Etape 7: Conversion timeline format final")
    final_timeline = _convert_timeline_to_final_format(timeline)

    logger.info(f"=== FIN generate_planning - {len(final_timeline)} items ===")

    return {
        "timeline": final_timeline,
        "statistics": statistics
    }


# ============================================================================
# HELPERS INTERNES
# ============================================================================

def _calculate_statistics(timeline: List[Dict]) -> Dict:
    """
    Calcule les statistiques du planning.

    Args:
        timeline: Timeline avec champs start_min, end_min, type, etc.

    Returns:
        Dictionnaire de statistiques
    """
    total_work_minutes = 0
    total_pause_minutes = 0
    total_recurrent_minutes = 0
    total_planned_minutes = 0

    work_count = 0
    pause_count = 0
    recurrent_count = 0
    planned_count = 0

    for item in timeline:
        item_type = item.get("type", "")
        duration = item.get("duration", 0)

        if item_type == "work":
            total_work_minutes += duration
            work_count += 1
        elif item_type == "pause":
            total_pause_minutes += duration
            pause_count += 1
        elif item_type == "recurrent":
            total_recurrent_minutes += duration
            recurrent_count += 1
        elif item_type == "planned":
            total_planned_minutes += duration
            planned_count += 1

    return {
        "total_work_minutes": total_work_minutes,
        "total_pause_minutes": total_pause_minutes,
        "total_recurrent_minutes": total_recurrent_minutes,
        "total_planned_minutes": total_planned_minutes,
        "task_count": len(timeline),
        "work_count": work_count,
        "pause_count": pause_count,
        "recurrent_count": recurrent_count,
        "planned_count": planned_count
    }


def _convert_timeline_to_final_format(timeline: List[Dict]) -> List[Dict]:
    """
    Convertit la timeline au format final pour l'API.

    Args:
        timeline: Timeline avec champs start_min, end_min

    Returns:
        Timeline avec champs start_time, end_time (format HH:MM)
    """
    from .utils import minutes_to_time

    final_timeline = []

    for item in timeline:
        # Copier l'item
        final_item = dict(item)

        # Convertir start_min -> start_time
        if "start_min" in final_item:
            final_item["start_time"] = minutes_to_time(final_item["start_min"])
            del final_item["start_min"]

        # Convertir end_min -> end_time
        if "end_min" in final_item:
            final_item["end_time"] = minutes_to_time(final_item["end_min"])
            del final_item["end_min"]

        final_timeline.append(final_item)

    return final_timeline
