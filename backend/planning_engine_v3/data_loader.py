"""
Module de chargement des donnees CSV
Toutes les fonctions retournent List[Dict]
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .utils import clean_csv_field, safe_int

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER: LECTURE CSV GENERIQUE
# ============================================================================

def _read_csv(csv_path: Path, required_fields: Optional[List[str]] = None) -> List[Dict]:
    """
    Lit un fichier CSV et retourne une liste de dictionnaires.

    Args:
        csv_path: Chemin du fichier CSV
        required_fields: Liste des champs requis (optionnel)

    Returns:
        Liste de dictionnaires (une ligne = un dict)

    Gestion erreurs:
        - Fichier absent -> retourne [] + log WARNING
        - Ligne invalide -> skip ligne + log ERROR
        - Encodage erreur -> reencode latin-1 -> UTF-8
    """
    if not csv_path.exists():
        logger.warning(f"Fichier CSV absent: {csv_path}")
        return []

    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=";")
            rows = []

            for i, row in enumerate(reader, start=2):  # Ligne 2 = premiere data
                # Nettoyer tous les champs
                cleaned_row = {k: clean_csv_field(v) for k, v in row.items()}

                # Verifier champs requis
                if required_fields:
                    missing = [f for f in required_fields if not cleaned_row.get(f)]
                    if missing:
                        logger.error(f"{csv_path.name} ligne {i}: Champs manquants {missing}")
                        continue

                rows.append(cleaned_row)

            logger.info(f"Charge {len(rows)} lignes depuis {csv_path.name}")
            return rows

    except UnicodeDecodeError:
        # Reencodage latin-1 -> UTF-8
        logger.warning(f"Erreur encodage {csv_path.name}, reencodage en cours...")

        content = csv_path.read_text(encoding="latin-1")
        csv_path.write_text(content, encoding="utf-8")

        # Retry
        return _read_csv(csv_path, required_fields)

    except Exception as e:
        logger.error(f"Erreur lecture {csv_path.name}: {e}")
        return []


# ============================================================================
# CHARGEMENT TACHES DE TRAVAIL
# ============================================================================

def load_work_tasks(data_dir: Path) -> List[Dict]:
    """
    Charge les taches de travail depuis LISTE_MERE.v2.csv.

    Returns:
        Liste de dicts avec cles:
            - id, name, description, category, sub_category
            - duration_min, remaining_min, priority
            - tags, keywords, dependencies, notes
            - deadline, fixed_start, planned_start, status

    Filtres appliques:
        - Status != DONE et != CANCELLED
    """
    csv_path = data_dir / "LISTE_MERE.v2.csv"
    required_fields = ["ID", "NAME", "DURATION_MIN"]

    rows = _read_csv(csv_path, required_fields)

    tasks = []
    for row in rows:
        # Filtrer taches terminees/annulees
        if row.get("STATUS") in ["DONE", "CANCELLED"]:
            continue

        task = {
            "id": row["ID"],
            "name": row["NAME"],
            "description": row.get("DESCRIPTION", ""),
            "category": row.get("CATEGORY", ""),
            "sub_category": row.get("SUB_CATEGORY", ""),
            "duration_min": safe_int(row.get("DURATION_MIN"), 0),
            "remaining_min": safe_int(row.get("REMAINING_MIN"), safe_int(row.get("DURATION_MIN"), 0)),
            "priority": safe_int(row.get("PRIORITY"), 3),
            "tags": row.get("TAGS", ""),
            "keywords": row.get("KEYWORDS", ""),
            "dependencies": row.get("DEPENDENCIES", ""),
            "notes": row.get("NOTES", ""),
            "deadline": row.get("DEADLINE", ""),
            "fixed_start": row.get("FIXED_START", ""),
            "planned_start": row.get("PLANNED_START", ""),
            "status": row.get("STATUS", "TODO")
        }

        tasks.append(task)

    logger.info(f"Charge {len(tasks)} taches de travail")
    return tasks


# ============================================================================
# CHARGEMENT PAUSES
# ============================================================================

def load_pauses(data_dir: Path, active_only: bool = False) -> List[Dict]:
    """
    Charge les pauses depuis TACHES_RECURRENTES.v2.csv.

    Args:
        active_only: Si True, filtre sur IS_ACTIVE=1

    Returns:
        Liste de dicts avec cles:
            - id, name, description, category, sub_category
            - duration_min, is_active, is_pause

    Filtres appliques:
        - IS_PAUSE = 1
        - Si active_only=True: IS_ACTIVE = 1
    """
    csv_path = data_dir / "TACHES_RECURRENTES.v2.csv"
    required_fields = ["ID", "NAME", "DURATION_MIN", "IS_PAUSE"]

    rows = _read_csv(csv_path, required_fields)

    pauses = []
    for row in rows:
        # Filtrer: seulement les pauses
        if row.get("IS_PAUSE") != "1":
            continue

        # Filtrer: seulement actives si demande
        if active_only and row.get("IS_ACTIVE") != "1":
            continue

        pause = {
            "id": row["ID"],
            "name": row["NAME"],
            "description": row.get("DESCRIPTION", ""),
            "category": row.get("CATEGORY", ""),
            "sub_category": row.get("SUB_CATEGORY", ""),
            "duration_min": safe_int(row.get("DURATION_MIN"), 5),
            "is_active": row.get("IS_ACTIVE") == "1",
            "is_pause": True
        }

        pauses.append(pause)

    logger.info(f"Charge {len(pauses)} pauses" + (" (actives uniquement)" if active_only else ""))
    return pauses


# ============================================================================
# CHARGEMENT TACHES RECURRENTES
# ============================================================================

def load_recurrent_tasks(data_dir: Path, active_only: bool = False) -> List[Dict]:
    """
    Charge les taches recurrentes depuis TACHES_RECURRENTES.v2.csv.

    Args:
        active_only: Si True, filtre sur IS_ACTIVE=1

    Returns:
        Liste de dicts avec cles:
            - id, name, description, category, sub_category
            - duration_min, recurrence_type, recurrence_interval
            - last_done_date, next_due_date, is_active

    Filtres appliques:
        - IS_PAUSE = 0 (taches recurrentes, pas pauses)
        - Si active_only=True: IS_ACTIVE = 1
    """
    csv_path = data_dir / "TACHES_RECURRENTES.v2.csv"
    required_fields = ["ID", "NAME", "DURATION_MIN", "IS_PAUSE"]

    rows = _read_csv(csv_path, required_fields)

    tasks = []
    for row in rows:
        # Filtrer: seulement les taches recurrentes (pas pauses)
        if row.get("IS_PAUSE") == "1":
            continue

        # Filtrer: seulement actives si demande
        if active_only and row.get("IS_ACTIVE") != "1":
            continue

        task = {
            "id": row["ID"],
            "name": row["NAME"],
            "description": row.get("DESCRIPTION", ""),
            "category": row.get("CATEGORY", ""),
            "sub_category": row.get("SUB_CATEGORY", ""),
            "duration_min": safe_int(row.get("DURATION_MIN"), 15),
            "recurrence_type": row.get("RECURRENCE_TYPE", "DAILY"),
            "recurrence_interval": safe_int(row.get("RECURRENCE_INTERVAL"), 1),
            "last_done_date": row.get("LAST_DONE_DATE", ""),
            "next_due_date": row.get("NEXT_DUE_DATE", ""),
            "priority": safe_int(row.get("PRIORITY"), 2),
            "is_active": row.get("IS_ACTIVE") == "1",
            "is_pause": False
        }

        tasks.append(task)

    logger.info(f"Charge {len(tasks)} taches recurrentes" + (" (actives uniquement)" if active_only else ""))
    return tasks


# ============================================================================
# CHARGEMENT TEMPS MORTS
# ============================================================================

def load_temps_morts(data_dir: Path, date: str) -> List[Dict]:
    """
    Charge les temps morts pour une date donnee.

    Args:
        date: Date au format YYYY-MM-DD

    Returns:
        Liste de dicts avec cles:
            - date, heure_debut, heure_fin, titre

    Filtres appliques:
        - DATE = date (filtre sur la date demandee)
    """
    csv_path = data_dir / "temps_morts.csv"
    required_fields = ["DATE", "HEURE_DEBUT", "HEURE_FIN"]

    rows = _read_csv(csv_path, required_fields)

    temps_morts = []
    for row in rows:
        # Filtrer sur la date
        if row.get("DATE") != date:
            continue

        tm = {
            "date": row["DATE"],
            "heure_debut": row["HEURE_DEBUT"],
            "heure_fin": row["HEURE_FIN"],
            "titre": row.get("TITRE", "Temps mort")
        }

        temps_morts.append(tm)

    logger.info(f"Charge {len(temps_morts)} temps morts pour {date}")
    return temps_morts


# ============================================================================
# CHARGEMENT TACHES PLANIFIEES
# ============================================================================

def load_planned_tasks(data_dir: Path, date: Optional[str] = None) -> List[Dict]:
    """
    Charge les taches planifiees (PLANNED_START rempli).

    Args:
        date: Date au format YYYY-MM-DD (optionnel, filtre par date)

    Returns:
        Liste de dicts avec cles:
            - Toutes les colonnes de LISTE_MERE.v2.csv

    Filtres appliques:
        - PLANNED_START != ""
        - Si date fournie: filtre sur la date de PLANNED_START
    """
    # Charger toutes les taches de travail
    all_tasks = load_work_tasks(data_dir)

    planned_tasks = []
    for task in all_tasks:
        # Filtrer: seulement si PLANNED_START rempli
        if not task.get("planned_start"):
            continue

        # Filtrer par date si demande
        if date:
            # Extraire la date de PLANNED_START (format DD.MM.YY HH:MM)
            try:
                from .utils import parse_datetime_user, format_date_iso
                dt = parse_datetime_user(task["planned_start"])
                task_date = format_date_iso(dt)

                if task_date != date:
                    continue
            except ValueError:
                logger.error(f"Format PLANNED_START invalide pour {task['id']}: {task['planned_start']}")
                continue

        planned_tasks.append(task)

    logger.info(f"Charge {len(planned_tasks)} taches planifiees" + (f" pour {date}" if date else ""))
    return planned_tasks


# ============================================================================
# CHARGEMENT CATEGORIES
# ============================================================================

def load_categories(data_dir: Path) -> Dict[str, List[str]]:
    """
    Charge les categories depuis categories.csv.

    Returns:
        Dict avec structure:
            {
                "Etudes": ["Mathematiques", "Litterature"],
                "Travail": ["Programmation", "Management"],
                ...
            }
    """
    csv_path = data_dir / "categories.csv"
    required_fields = ["CATEGORY", "SUB_CATEGORY"]

    rows = _read_csv(csv_path, required_fields)

    categories = {}
    for row in rows:
        cat = row["CATEGORY"]
        subcat = row["SUB_CATEGORY"]

        if cat not in categories:
            categories[cat] = []

        if subcat not in categories[cat]:
            categories[cat].append(subcat)

    logger.info(f"Charge {len(categories)} categories")
    return categories
