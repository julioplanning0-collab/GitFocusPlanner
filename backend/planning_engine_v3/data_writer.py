"""
Module d'ecriture CSV pour export du planning
Toutes les ecritures sont ATOMIQUES (temp file + rename)
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# ECRITURE PLANNING (EXPORT CSV)
# ============================================================================

def write_planning_csv(csv_path: Path, timeline: List[Dict], date: str) -> None:
    """
    Ecrit le planning dans un fichier CSV.

    Args:
        csv_path: Chemin du fichier CSV de sortie
        timeline: Timeline complete (liste d'items)
        date: Date du planning (format YYYY-MM-DD)

    Raises:
        IOError: Si ecriture echoue

    Format CSV:
        - Delimiteur: ;
        - Encoding: UTF-8
        - Quoting: QUOTE_ALL
        - Headers: DATE;TYPE;NAME;START_TIME;END_TIME;DURATION

    Ecriture ATOMIQUE:
        - Ecrit dans fichier temporaire
        - Puis rename atomique vers fichier final
        - Garantit pas de corruption si crash
    """
    logger.info(f"=== Ecriture planning CSV: {csv_path} ===")
    logger.info(f"Date: {date}, Items: {len(timeline)}")

    # Preparer les lignes pour le CSV
    rows = []
    for item in timeline:
        row = {
            "DATE": date,
            "TYPE": item.get("type", ""),
            "NAME": item.get("name", ""),
            "START_TIME": item.get("start_time", ""),
            "END_TIME": item.get("end_time", ""),
            "DURATION": item.get("duration", 0)
        }
        rows.append(row)

    # Ecriture atomique
    _atomic_write_csv(
        csv_path=csv_path,
        rows=rows,
        fieldnames=["DATE", "TYPE", "NAME", "START_TIME", "END_TIME", "DURATION"]
    )

    logger.info(f"Planning ecrit: {len(rows)} lignes")


# ============================================================================
# HELPERS INTERNES
# ============================================================================

def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    """
    Ecriture atomique d'un fichier CSV.

    Args:
        csv_path: Chemin du fichier final
        rows: Lignes a ecrire
        fieldnames: Noms des colonnes

    Raises:
        IOError: Si ecriture echoue

    Principe:
        1. Ecrire dans fichier temporaire (.tmp)
        2. Rename atomique vers fichier final
        3. Si crash pendant ecriture, fichier original intact
    """
    # Fichier temporaire dans meme repertoire
    temp_path = csv_path.with_suffix('.tmp')

    try:
        # Ecrire dans fichier temporaire
        with open(temp_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames,
                delimiter=';',
                quoting=csv.QUOTE_ALL
            )
            writer.writeheader()
            writer.writerows(rows)

        # Rename atomique (OS garantit atomicite)
        temp_path.replace(csv_path)
        logger.debug(f"Fichier ecrit avec succes: {csv_path}")

    except Exception as e:
        # Cleanup fichier temporaire si erreur
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Erreur ecriture CSV: {e}")
        raise IOError(f"Impossible d'ecrire {csv_path}: {e}")
