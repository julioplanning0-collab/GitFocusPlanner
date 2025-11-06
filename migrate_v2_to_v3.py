"""
Migration V2 → V3 CSV
Converts V2 data files to V3 format with proper structure.
"""

import csv
from pathlib import Path

# Paths
V2_DIR = Path(r"C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner\prod_data")
V3_DIR = Path(r"C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner\data\prod_data")

def migrate_liste_mere():
    """Migrate LISTE_MERE.v2.csv → LISTE_MERE.v3.csv"""
    v2_file = V2_DIR / "LISTE_MERE.v2.csv"
    v3_file = V3_DIR / "LISTE_MERE.v3.csv"

    with open(v2_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        rows = list(reader)

    # Write V3 format (simplified columns)
    fieldnames = ['CODE_TACHE', 'NOM_TACHE', 'DESCRIPTION', 'CATEGORIE', 'DUREE_MIN', 'STATUS']

    with open(v3_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()

        for row in rows:
            task_id = f"TASK{int(row['ID']):03d}"
            writer.writerow({
                'CODE_TACHE': task_id,
                'NOM_TACHE': row['NAME'],
                'DESCRIPTION': row['DESCRIPTION'],
                'CATEGORIE': row['CATEGORY'],
                'DUREE_MIN': row['DURATION_MIN'],
                'STATUS': row['STATUS']
            })

    print(f"[OK] LISTE_MERE.v3.csv: {len(rows)} tasks migrated")


def migrate_recurrentes():
    """Merge TACHES_RECURRENTES.v2 + TACHES_RESPIRATOIRES → TACHES_RECURRENTES.v3.csv"""
    rec_file = V2_DIR / "TACHES_RECURRENTES.v2.csv"
    resp_file = V2_DIR / "TACHES_RESPIRATOIRES.v2.csv.backup"
    v3_file = V3_DIR / "TACHES_RECURRENTES.v3.csv"

    all_tasks = []

    # Load recurrent tasks (IS_PAUSE=0)
    with open(rec_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            all_tasks.append({
                'CODE_RECURRENCE': row['ID'],
                'NOM_TACHE': row['NAME'],
                'DESCRIPTION': row['DESCRIPTION'],
                'CATEGORIE': row['CATEGORY'],
                'DUREE_MIN': row['DURATION_MIN'],
                'IS_ACTIVE': row['IS_ACTIVE'],
                'IS_PAUSE': '0'  # Recurrent = IS_PAUSE 0
            })

    recurrent_count = len(all_tasks)

    # Load respiration tasks (IS_PAUSE=1)
    with open(resp_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter=';')
        for i, row in enumerate(reader):
            # Convert R010 → REC050, R018 → REC051, etc.
            rec_id = f"REC{50 + i:03d}"
            all_tasks.append({
                'CODE_RECURRENCE': rec_id,
                'NOM_TACHE': row['NAME'],
                'DESCRIPTION': row['DESCRIPTION'],
                'CATEGORIE': row['CATEGORY'],
                'DUREE_MIN': row['DURATION_MIN'],
                'IS_ACTIVE': '1',  # All pauses active by default
                'IS_PAUSE': '1'  # Respiration = IS_PAUSE 1
            })

    pause_count = len(all_tasks) - recurrent_count

    # Write merged V3 file
    fieldnames = ['CODE_RECURRENCE', 'NOM_TACHE', 'DESCRIPTION', 'CATEGORIE', 'DUREE_MIN', 'IS_ACTIVE', 'IS_PAUSE']

    with open(v3_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(all_tasks)

    print(f"[OK] TACHES_RECURRENTES.v3.csv: {recurrent_count} recurrentes + {pause_count} pauses = {len(all_tasks)} total")


def copy_temps_morts():
    """Copy temps_morts.csv (unchanged)"""
    v2_file = V2_DIR / "temps_morts.csv"
    v3_file = V3_DIR / "temps_morts.csv"

    with open(v2_file, 'r', encoding='utf-8') as src:
        content = src.read()

    with open(v3_file, 'w', encoding='utf-8') as dst:
        dst.write(content)

    print(f"[OK] temps_morts.csv copied")


def copy_planifiees():
    """Copy TACHES_PLANIFIEES.v2.csv to v3"""
    v2_file = V2_DIR / "TACHES_PLANIFIEES.v2.csv"
    v3_file = V3_DIR / "TACHES_PLANIFIEES.v3.csv"

    # For now, just create empty file with header
    fieldnames = ['CODE_TACHE', 'NOM_TACHE', 'DATE', 'HEURE_DEBUT', 'DUREE_MIN', 'TYPE']

    with open(v3_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()

    print(f"[OK] TACHES_PLANIFIEES.v3.csv created (empty)")


if __name__ == "__main__":
    print("=" * 60)
    print("Migration V2 to V3")
    print("=" * 60)

    migrate_liste_mere()
    migrate_recurrentes()
    copy_temps_morts()
    copy_planifiees()

    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)
