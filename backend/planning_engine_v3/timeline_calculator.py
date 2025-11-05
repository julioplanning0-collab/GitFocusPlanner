"""
Module de calcul des temps de la timeline (TIME CALCULATION)
Assigne des temps absolus a chaque item de la sequence
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict

from .utils import (
    datetime_to_minutes,
    minutes_to_datetime,
    time_to_minutes,
    minutes_to_time,
    parse_date_iso
)

logger = logging.getLogger(__name__)


# ============================================================================
# CALCUL DES TEMPS (TIME CALCULATION)
# ============================================================================

def assign_times_to_sequence(
    sequence: List[Dict],
    planningStartTime: str,
    date: str,
    temps_morts: List[Dict]
) -> List[Dict]:
    """
    Assigne des temps absolus a chaque item de la sequence.

    Args:
        sequence: Sequence ordonnee d'items
        planningStartTime: Heure de debut du planning (format HH:MM)
        date: Date du planning (format YYYY-MM-DD)
        temps_morts: Liste des temps morts a eviter

    Returns:
        Timeline avec champs start_min et end_min (minutes relatives)

    Logique:
        - Minute 0 = planningStartTime
        - Assigne start_min et end_min a chaque item
        - Evite les temps_morts (saute par-dessus)
        - Retourne timeline lineaire (liste ordonnee)
    """
    date_obj = parse_date_iso(date)
    start_time_obj = datetime.combine(
        date_obj,
        datetime.strptime(planningStartTime, "%H:%M").time()
    )

    # Minute 0 = planningStartTime
    current_minutes = 0
    timeline = []

    for item in sequence:
        duration = item["duration"]

        # Calculer heure absolue de debut
        item_start_time = minutes_to_datetime(current_minutes, start_time_obj)

        # Verifier collision avec temps_morts (max 100 iterations pour eviter boucle infinie)
        max_iterations = 100
        iteration_count = 0

        while _has_collision_with_temps_morts(
            item_start_time,
            duration,
            temps_morts,
            date
        ) and iteration_count < max_iterations:
            iteration_count += 1

            # Trouver le temps_mort qui bloque
            for tm in temps_morts:
                if tm.get("date") != date:
                    continue

                try:
                    tm_end_minutes = time_to_minutes(tm["heure_fin"])
                    tm_end = datetime.combine(
                        item_start_time.date(),
                        datetime.min.time().replace(
                            hour=tm_end_minutes // 60,
                            minute=tm_end_minutes % 60
                        )
                    )

                    # Si ce temps_mort bloque, sauter a sa fin
                    if _has_collision_with_single_temps_mort(item_start_time, duration, tm, date):
                        # Sauter juste apres la fin du temps_mort
                        current_minutes = datetime_to_minutes(tm_end, start_time_obj)
                        item_start_time = tm_end
                        break  # Re-verifier les collisions avec le nouveau start_time

                except (ValueError, KeyError):
                    continue

        if iteration_count >= max_iterations:
            logger.error(f"Max iterations atteintes pour placement item, abandon")

        # Assigner temps
        timeline_item = {
            "type": item["type"],
            "task": item["task"],
            "duration": duration,
            "start_min": current_minutes,
            "end_min": current_minutes + duration
        }

        # Copier champs additionnels (segment_index, target_time, etc.)
        for key in ["segment_index", "total_segments", "target_time"]:
            if key in item:
                timeline_item[key] = item[key]

        timeline.append(timeline_item)

        # Avancer curseur
        current_minutes += duration

    logger.info(f"Timeline calculee: {len(timeline)} items, duree totale {current_minutes} min")

    return timeline


def _has_collision_with_single_temps_mort(
    start_time: datetime,
    duration: int,
    tm: Dict,
    date: str
) -> bool:
    """
    Verifie si un item entre en collision avec UN temps_mort specifique.

    Args:
        start_time: Heure de debut de l'item
        duration: Duree de l'item (minutes)
        tm: Un temps_mort specifique
        date: Date du planning

    Returns:
        True si collision, False sinon
    """
    if tm.get("date") != date:
        return False

    end_time = start_time + timedelta(minutes=duration)

    try:
        tm_start_minutes = time_to_minutes(tm["heure_debut"])
        tm_end_minutes = time_to_minutes(tm["heure_fin"])

        tm_start = datetime.combine(
            start_time.date(),
            datetime.min.time().replace(
                hour=tm_start_minutes // 60,
                minute=tm_start_minutes % 60
            )
        )

        tm_end = datetime.combine(
            start_time.date(),
            datetime.min.time().replace(
                hour=tm_end_minutes // 60,
                minute=tm_end_minutes % 60
            )
        )

        # Verifier collision
        return start_time < tm_end and end_time > tm_start

    except (ValueError, KeyError):
        return False


def _has_collision_with_temps_morts(
    start_time: datetime,
    duration: int,
    temps_morts: List[Dict],
    date: str
) -> bool:
    """
    Verifie si un item entre en collision avec un temps_mort.

    Args:
        start_time: Heure de debut de l'item
        duration: Duree de l'item (minutes)
        temps_morts: Liste des temps_morts
        date: Date du planning (format YYYY-MM-DD)

    Returns:
        True si collision, False sinon

    Logique de collision:
        item_start < tm_end AND item_end > tm_start
    """
    end_time = start_time + timedelta(minutes=duration)

    for tm in temps_morts:
        # Filtrer par date
        if tm.get("date") != date:
            continue

        # Parser heure debut/fin
        try:
            tm_start_minutes = time_to_minutes(tm["heure_debut"])
            tm_end_minutes = time_to_minutes(tm["heure_fin"])

            tm_start = datetime.combine(
                start_time.date(),
                datetime.min.time().replace(
                    hour=tm_start_minutes // 60,
                    minute=tm_start_minutes % 60
                )
            )

            tm_end = datetime.combine(
                start_time.date(),
                datetime.min.time().replace(
                    hour=tm_end_minutes // 60,
                    minute=tm_end_minutes % 60
                )
            )

            # Verifier collision
            if start_time < tm_end and end_time > tm_start:
                return True

        except (ValueError, KeyError) as e:
            logger.error(f"Erreur parsing temps_mort: {e}")
            continue

    return False


def _find_next_free_time(
    current_time: datetime,
    temps_morts: List[Dict],
    date: str
) -> datetime:
    """
    Trouve le prochain creneau libre apres current_time.

    Args:
        current_time: Heure actuelle
        temps_morts: Liste des temps_morts
        date: Date du planning

    Returns:
        Heure du prochain creneau libre (ou current_time si aucun temps_mort)

    Logique:
        - Trouve le temps_mort qui chevauche current_time
        - Retourne l'heure de fin de ce temps_mort
        - Si pas de chevauchement, retourne current_time
    """
    for tm in temps_morts:
        # Filtrer par date
        if tm.get("date") != date:
            continue

        try:
            tm_start_minutes = time_to_minutes(tm["heure_debut"])
            tm_end_minutes = time_to_minutes(tm["heure_fin"])

            tm_start = datetime.combine(
                current_time.date(),
                datetime.min.time().replace(
                    hour=tm_start_minutes // 60,
                    minute=tm_start_minutes % 60
                )
            )

            tm_end = datetime.combine(
                current_time.date(),
                datetime.min.time().replace(
                    hour=tm_end_minutes // 60,
                    minute=tm_end_minutes % 60
                )
            )

            # Si current_time est dans ce temps_mort, retourner la fin
            if tm_start <= current_time < tm_end:
                return tm_end

        except (ValueError, KeyError) as e:
            logger.error(f"Erreur parsing temps_mort: {e}")
            continue

    return current_time


def convert_timeline_to_absolute_times(
    timeline: List[Dict],
    planningStartTime: str,
    date: str
) -> List[Dict]:
    """
    Convertit la timeline (minutes relatives) en temps absolus (HH:MM).

    Args:
        timeline: Timeline avec start_min/end_min
        planningStartTime: Heure de debut du planning
        date: Date du planning (format YYYY-MM-DD)

    Returns:
        Timeline avec champs heure_debut et heure_fin (format HH:MM)

    Logique:
        - Convertit start_min -> heure_debut (HH:MM)
        - Convertit end_min -> heure_fin (HH:MM)
        - Conserve tous les autres champs
    """
    date_obj = parse_date_iso(date)
    start_time_obj = datetime.combine(
        date_obj,
        datetime.strptime(planningStartTime, "%H:%M").time()
    )

    result = []

    for item in timeline:
        # Calculer heures absolues
        start_dt = minutes_to_datetime(item["start_min"], start_time_obj)
        end_dt = minutes_to_datetime(item["end_min"], start_time_obj)

        # Creer item avec temps absolus
        result_item = {
            "type": item["type"],
            "task": item["task"],
            "duration": item["duration"],
            "heure_debut": start_dt.strftime("%H:%M"),
            "heure_fin": end_dt.strftime("%H:%M"),
            "start_min": item["start_min"],
            "end_min": item["end_min"]
        }

        # Copier champs additionnels
        for key in ["segment_index", "total_segments", "target_time"]:
            if key in item:
                result_item[key] = item[key]

        result.append(result_item)

    logger.info(f"Timeline convertie en temps absolus: {len(result)} items")

    return result


def calculate_statistics(timeline: List[Dict]) -> Dict:
    """
    Calcule les statistiques du planning.

    Args:
        timeline: Timeline complete avec temps

    Returns:
        Dict avec statistiques:
            - total_duration_min: Duree totale (minutes)
            - work_duration_min: Duree travail
            - pause_duration_min: Duree pauses
            - recurrent_duration_min: Duree recurrentes
            - planned_duration_min: Duree planifiees
            - work_count: Nombre taches travail
            - pause_count: Nombre pauses
            - recurrent_count: Nombre recurrentes
            - planned_count: Nombre planifiees
    """
    stats = {
        "total_duration_min": 0,
        "work_duration_min": 0,
        "pause_duration_min": 0,
        "recurrent_duration_min": 0,
        "planned_duration_min": 0,
        "work_count": 0,
        "pause_count": 0,
        "recurrent_count": 0,
        "planned_count": 0
    }

    for item in timeline:
        item_type = item["type"]
        duration = item["duration"]

        stats["total_duration_min"] += duration

        if item_type == "work":
            stats["work_duration_min"] += duration
            stats["work_count"] += 1
        elif item_type == "pause":
            stats["pause_duration_min"] += duration
            stats["pause_count"] += 1
        elif item_type == "recurrent":
            stats["recurrent_duration_min"] += duration
            stats["recurrent_count"] += 1
        elif item_type == "planned":
            stats["planned_duration_min"] += duration
            stats["planned_count"] += 1

    logger.info(f"Statistiques calculees: {stats['total_duration_min']} min total, "
                f"{stats['work_count']} travail, {stats['pause_count']} pauses")

    return stats
