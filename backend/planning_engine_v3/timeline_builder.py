"""
Module de construction de la timeline (ORDERING)
Construit la sequence des taches SANS assigner de temps
"""

import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTRUCTION DE SEQUENCE (ORDERING)
# ============================================================================

def build_task_sequence(
    work_tasks: List[Dict],
    pauses: List[Dict],
    recurrent_tasks: List[Dict]
) -> List[Dict]:
    """
    Construit la sequence de taches en alternant travail/pause.

    Args:
        work_tasks: Liste de taches de travail (depuis LISTE_MERE.v2.csv)
        pauses: Liste de pauses (depuis TACHES_RECURRENTES.v2.csv, IS_PAUSE=1)
        recurrent_tasks: Liste de taches recurrentes (IS_PAUSE=0)

    Returns:
        Liste ordonnee d'items avec structure:
            {
                "type": "work" | "pause" | "recurrent",
                "task": {dictionnaire de la tache},
                "duration": int (minutes)
            }

    Logique d'alternance:
        - Tri des taches de travail par priorite (1 > 2 > 3)
        - Alternance: Tache travail -> Pause -> Tache travail -> Pause
        - Utilise pauses dans l'ordre (rotation circulaire)
        - Taches recurrentes inserees entre travail/pause
    """
    sequence = []

    # Trier work_tasks par priorite (1 = haute, 3 = basse)
    sorted_work_tasks = sorted(work_tasks, key=lambda t: t.get("priority", 3))

    # Index pour rotation circulaire des pauses
    pause_index = 0

    # Alterner travail/pause
    for work_task in sorted_work_tasks:
        # Ajouter tache de travail
        sequence.append({
            "type": "work",
            "task": work_task,
            "duration": work_task.get("duration_min", 25)
        })

        # Ajouter pause (rotation circulaire)
        if pauses:
            pause = pauses[pause_index % len(pauses)]
            sequence.append({
                "type": "pause",
                "task": pause,
                "duration": pause.get("duration_min", 5)
            })
            pause_index += 1

    logger.info(f"Sequence construite: {len(sequence)} items "
                f"({len(sorted_work_tasks)} travail, {len(sequence) - len(sorted_work_tasks)} pauses)")

    return sequence


def insert_recurrent_tasks(
    sequence: List[Dict],
    recurrent_tasks: List[Dict]
) -> List[Dict]:
    """
    Insere les taches recurrentes dans la sequence.

    Args:
        sequence: Sequence de base (travail/pause)
        recurrent_tasks: Taches recurrentes a inserer

    Returns:
        Sequence avec taches recurrentes inserees

    Logique d'insertion:
        - Une tache recurrente toutes les 2 heures (environ)
        - Inseree APRES une pause (pour eviter 2 taches travail consecutives)
        - Si pas de recurrent tasks, retourne sequence inchangee
    """
    if not recurrent_tasks:
        return sequence

    # Calculer intervalle d'insertion (environ toutes les 2h = 4 items)
    interval = max(4, len(sequence) // max(1, len(recurrent_tasks)))

    result = []
    recurrent_index = 0

    for i, item in enumerate(sequence):
        result.append(item)

        # Inserer recurrent apres pause, tous les N items
        if (item["type"] == "pause" and
            (i + 1) % interval == 0 and
            recurrent_index < len(recurrent_tasks)):

            recurrent = recurrent_tasks[recurrent_index]
            result.append({
                "type": "recurrent",
                "task": recurrent,
                "duration": recurrent.get("duration_min", 15)
            })
            recurrent_index += 1

    logger.info(f"Sequence avec recurrentes: {len(result)} items "
                f"({recurrent_index} recurrentes inserees)")

    return result


def insert_planned_tasks(
    sequence: List[Dict],
    planned_tasks: List[Dict],
    planningStartTime: str
) -> List[Dict]:
    """
    Insere les taches planifiees a leur heure cible.

    Args:
        sequence: Sequence de base
        planned_tasks: Taches avec PLANNED_START fixe
        planningStartTime: Heure de debut du planning (format HH:MM)

    Returns:
        Sequence avec taches planifiees inserees

    Logique d'insertion:
        - Calculer position cible dans la timeline (en minutes)
        - Inserer la tache AVANT l'item le plus proche
        - Si heure deja passee, inserer en debut
        - Si heure trop loin, inserer en fin
    """
    from .utils import time_to_minutes, parse_datetime_user

    if not planned_tasks:
        return sequence

    result = list(sequence)
    start_minutes = time_to_minutes(planningStartTime)

    for planned in planned_tasks:
        # Parser PLANNED_START (format "DD.MM.YY HH:MM")
        planned_start = planned.get("planned_start", "")
        if not planned_start:
            continue

        try:
            dt = parse_datetime_user(planned_start)
            target_minutes = dt.hour * 60 + dt.minute

            # Calculer position cible (offset depuis start)
            offset = target_minutes - start_minutes
            if offset < 0:
                offset = 0  # Inserer en debut si deja passe

            # Trouver meilleure position d'insertion
            cumulative_duration = 0
            insert_position = 0

            for i, item in enumerate(result):
                if cumulative_duration >= offset:
                    insert_position = i
                    break
                cumulative_duration += item["duration"]
            else:
                insert_position = len(result)

            # Inserer tache planifiee
            result.insert(insert_position, {
                "type": "planned",
                "task": planned,
                "duration": planned.get("duration_min", 25),
                "target_time": planned_start
            })

            logger.info(f"Tache planifiee inseree: {planned['name']} a position {insert_position}")

        except ValueError as e:
            logger.error(f"Erreur parsing PLANNED_START pour {planned.get('id')}: {e}")
            continue

    return result


def split_long_tasks(
    sequence: List[Dict],
    max_duration: int = 25
) -> List[Dict]:
    """
    Decoupe les taches longues en segments de max_duration minutes.

    Args:
        sequence: Sequence de taches
        max_duration: Duree max par segment (defaut: 25 min = 1 Pomodoro)

    Returns:
        Sequence avec taches longues decoupees

    Logique:
        - Tache > max_duration -> decoupe en segments
        - Conserve infos originales (task_id, name, etc.)
        - Ajoute segment_index et total_segments
    """
    result = []

    for item in sequence:
        duration = item["duration"]

        if duration <= max_duration:
            result.append(item)
        else:
            # Calculer nombre de segments
            total_segments = (duration + max_duration - 1) // max_duration

            for segment_index in range(total_segments):
                segment_duration = min(max_duration, duration - segment_index * max_duration)

                result.append({
                    "type": item["type"],
                    "task": item["task"],
                    "duration": segment_duration,
                    "segment_index": segment_index + 1,
                    "total_segments": total_segments
                })

            logger.info(f"Tache {item['task'].get('name')} decoupee en {total_segments} segments")

    return result


def validate_sequence(sequence: List[Dict]) -> bool:
    """
    Valide qu'une sequence est correcte.

    Args:
        sequence: Sequence a valider

    Returns:
        True si valide, False sinon

    Regles de validation:
        - Au moins 1 item
        - Tous les items ont "type", "task", "duration"
        - Durees > 0
        - Pas de doublons (meme task_id consecutifs)
    """
    if not sequence:
        logger.error("Sequence vide")
        return False

    for i, item in enumerate(sequence):
        # Verifier champs requis
        if "type" not in item or "task" not in item or "duration" not in item:
            logger.error(f"Item {i}: Champs manquants (type/task/duration)")
            return False

        # Verifier duree
        if item["duration"] <= 0:
            logger.error(f"Item {i}: Duree invalide ({item['duration']})")
            return False

        # Verifier doublons consecutifs (sauf segments)
        if i > 0:
            prev_item = sequence[i - 1]
            if (item["task"].get("id") == prev_item["task"].get("id") and
                "segment_index" not in item):
                logger.error(f"Item {i}: Doublon consecutif ({item['task'].get('id')})")
                return False

    logger.info(f"Sequence validee: {len(sequence)} items")
    return True
