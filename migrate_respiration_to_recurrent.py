# -*- coding: utf-8 -*-
"""
Migrate respiration tasks to recurrent tasks.

Converts TACHES_RESPIRATOIRES.v2.csv to recurrent task format
and appends to TACHES_RECURRENTES.v2.csv.

Mapping:
- ID: Keep as-is (R010 → R010)
- RECURRENCE_TYPE: "daily" (most respirations are repeatable daily)
- RECURRENCE_INTERVAL: Use REPEAT_INTERVAL_MIN / 1440 (convert minutes to days)
- Other fields: Map directly or use empty defaults
"""

import sys
import io

# Fix Windows encoding for UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import csv
from pathlib import Path

# Paths
data_dir = Path("prod_data")
respiration_file = data_dir / "TACHES_RESPIRATOIRES.v2.csv"
recurrent_file = data_dir / "TACHES_RECURRENTES.v2.csv"
backup_file = data_dir / "TACHES_RESPIRATOIRES.v2.csv.backup"

# Backup respiration file before deletion
print(f"📦 Creating backup: {backup_file}")
import shutil
shutil.copy(respiration_file, backup_file)

# Read respiration tasks
print(f"📖 Reading {respiration_file}")
with open(respiration_file, 'r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f, delimiter=';')
    respiration_tasks = list(reader)

print(f"   Found {len(respiration_tasks)} respiration tasks")

# Read existing recurrent tasks
print(f"📖 Reading {recurrent_file}")
with open(recurrent_file, 'r', encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f, delimiter=';')
    recurrent_tasks = list(reader)

print(f"   Found {len(recurrent_tasks)} existing recurrent tasks")

# Find highest REC ID to avoid conflicts
rec_ids = [t['ID'].strip('"') for t in recurrent_tasks if t['ID'].strip('"').startswith('REC')]
max_rec_num = max([int(id[3:]) for id in rec_ids]) if rec_ids else 0
next_rec_num = max_rec_num + 1

print(f"   Highest REC ID: REC{max_rec_num:03d}, next available: REC{next_rec_num:03d}")

# Convert respiration tasks to recurrent format
converted_tasks = []

for resp_task in respiration_tasks:
    # Determine recurrence type and interval
    repeat_interval_min = int(resp_task['REPEAT_INTERVAL_MIN']) if resp_task['REPEAT_INTERVAL_MIN'] else 1440

    if repeat_interval_min >= 10080:  # 7 days
        recurrence_type = "weekly"
        recurrence_interval = 7
    elif repeat_interval_min >= 1440:  # 1 day
        recurrence_type = "daily"
        recurrence_interval = 1
    else:
        # Less than daily - treat as daily
        recurrence_type = "daily"
        recurrence_interval = 1

    # Map to recurrent task format
    rec_task = {
        'ID': resp_task['ID'],  # Keep original ID (R010, R018, etc.)
        'NAME': resp_task['NAME'],
        'DESCRIPTION': resp_task['DESCRIPTION'],
        'CATEGORY': resp_task['CATEGORY'],
        'SUB_CATEGORY': resp_task['SUB_CATEGORY'],
        'DURATION_MIN': resp_task['DURATION_MIN'],
        'RECURRENCE_TYPE': recurrence_type,
        'RECURRENCE_INTERVAL': str(recurrence_interval),
        'LAST_DONE_DATE': resp_task.get('LAST_DONE_DATE', ''),
        'NEXT_DUE_DATE': '',  # Will be calculated by system
        'PRIORITY': resp_task.get('PRIORITY', '2'),
        'STATUS': resp_task.get('STATUS', 'available'),
        'IS_ACTIVE': '1'  # Active by default
    }

    converted_tasks.append(rec_task)
    print(f"   ✅ Converted {resp_task['ID']}: {resp_task['NAME']} → {recurrence_type} (every {recurrence_interval} day(s))")

# Append converted tasks to recurrent file
print(f"\n💾 Appending {len(converted_tasks)} tasks to {recurrent_file}")

fieldnames = [
    'ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY', 'DURATION_MIN',
    'RECURRENCE_TYPE', 'RECURRENCE_INTERVAL', 'LAST_DONE_DATE', 'NEXT_DUE_DATE',
    'PRIORITY', 'STATUS', 'IS_ACTIVE'
]

# Write all tasks (existing + converted) atomically
temp_file = recurrent_file.with_suffix('.tmp')

with open(temp_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(recurrent_tasks + converted_tasks)

# Atomic rename
temp_file.replace(recurrent_file)

print(f"   ✅ Written {len(recurrent_tasks) + len(converted_tasks)} total tasks")

# Delete original respiration file
print(f"\n🗑️  Deleting {respiration_file}")
respiration_file.unlink()

print(f"\n✅ Migration complete!")
print(f"   - Backup saved: {backup_file}")
print(f"   - Respiration file deleted: {respiration_file}")
print(f"   - Recurrent file updated: {recurrent_file}")
print(f"   - Total tasks in recurrent file: {len(recurrent_tasks) + len(converted_tasks)}")
