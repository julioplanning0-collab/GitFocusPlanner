# 🔄 FLUX COMPLET TIMELINE V3 - VERSION CORRIGÉE

**Date**: 2025-11-06
**Différence clé avec V2**: Les tâches respiratoires n'existent plus comme entité séparée. Elles sont intégrées dans les tâches récurrentes.

---

## 🎯 CHANGEMENT ARCHITECTURAL MAJEUR V2 → V3

### V2 (Version Actuelle)
```
3 Onglets séparés:
├── Pomodoro (tâches de travail)
├── Pauses/Respiration (TACHES_RESPIRATOIRES.v2.csv) ❌ SUPPRIMÉ EN V3
└── Récurrentes (TACHES_RECURRENTES.v2.csv)
```

### V3 (Version Cible)
```
3 Onglets:
├── Pomodoro (tâches de travail) - INCHANGÉ
├── Pauses (drag & drop, inclut anciennes respirations) ✅ NOUVEAU
└── Récurrentes (inclut respirations + autres tâches) ✅ FUSIONNÉ
```

**Pourquoi ce changement?**
- Les tâches respiratoires étaient un type spécial artificiel
- En réalité, ce sont juste des tâches récurrentes courtes (5-20min)
- Simplification: 1 seul fichier CSV pour toutes les pauses/récurrentes

---

## 📊 STRUCTURE DONNÉES V3

### Fichiers CSV

**Avant (V2)** ❌:
```
LISTE_MERE.v2.csv            → Pomodoro
TACHES_RESPIRATOIRES.v2.csv  → Respirations (SUPPRIMÉ!)
TACHES_RECURRENTES.v2.csv    → Récurrentes
TACHES_PLANIFIEES.v2.csv     → Planifiées
temps_morts.csv              → Obstacles
```

**Après (V3)** ✅:
```
LISTE_MERE.v3.csv         → Pomodoro (inchangé)
TACHES_RECURRENTES.v3.csv → Récurrentes + Respirations (FUSIONNÉ!)
TACHES_PLANIFIEES.v3.csv  → Planifiées (inchangé)
temps_morts.csv           → Obstacles (inchangé)
```

### Structure TACHES_RECURRENTES.v3.csv

```csv
ID;NAME;DESCRIPTION;CATEGORY;DURATION_MIN;RECURRENCE_TYPE;IS_ACTIVE;IS_PAUSE
"REC001";"Méditation";"Respiration profonde";"Respiration";10;"daily";1;1
"REC002";"Arroser plantes";"Entretien quotidien";"Entretien";15;"2_days";1;0
"REC003";"Pause café";"Courte pause";"Respiration";5;"daily";1;1
```

**Nouveau champ** `IS_PAUSE`:
- `IS_PAUSE = 1` → Ancienne tâche respiratoire (affichée onglet Pauses)
- `IS_PAUSE = 0` → Vraie tâche récurrente (affichée onglet Récurrentes)

---

## 🗂️ INTERFACE UTILISATEUR V3

### Onglet 1: Pomodoro (INCHANGÉ)
```
┌────────────────────────────┐
│ Tâches Pomodoro            │
│ ☑ Révision maths (75min)  │
│ ☑ Exercices physique (50) │
│ ☐ Lecture livre (100min)  │
└────────────────────────────┘
```
**Source**: `LISTE_MERE.v3.csv`
**Action**: Checkboxes

### Onglet 2: Pauses ✅ NOUVEAU - Drag & Drop
```
┌──────────────────────┬─────────────────────────────┐
│ DISPONIBLES          │ SÉLECTIONNÉES (ordre)       │
├──────────────────────┼─────────────────────────────┤
│ 🫁 Méditation 10min  │ 1. 🫁 Méditation 10min      │
│ 🌬️ Respiration 5min  │ 2. 🌬️ Respiration 5min      │
│ ☕ Pause café 5min   │ 3. 🌬️ Respiration 5min (dup)│
│                      │                             │
│ [Drag items ici →]   │ [📌 Épingler] [🗑️ Vider]   │
│                      │ [Envoyer vers planning]     │
└──────────────────────┴─────────────────────────────┘
```
**Source**: `TACHES_RECURRENTES.v3.csv WHERE IS_PAUSE=1`
**Action**: Drag & drop pour ordonner, duplicatas autorisés

### Onglet 3: Récurrentes (Filtre IS_PAUSE=0)
```
┌──────────────────────────────────────────┐
│ Tâches Récurrentes                       │
│ [ON]  🪴 Arroser plantes (15min, 2j)    │
│ [ON]  🧹 Ménage salon (30min, weekly)   │
│ [OFF] 📧 Trier emails (20min, daily)    │
└──────────────────────────────────────────┘
```
**Source**: `TACHES_RECURRENTES.v3.csv WHERE IS_PAUSE=0`
**Action**: Toggle ON/OFF

---

## 🔄 FLUX COMPLET - GÉNÉRATION PLANNING V3

### PHASE 1: Chargement Page (Frontend)

**1. Init Planning Start Time**
```javascript
// Calculate: now + 15min, rounded up to next 5min
const now = new Date();
const future = new Date(now.getTime() + 15 * 60000);
const roundedMin = Math.ceil(future.getMinutes() / 5) * 5;
state.planningStartTime = future; // Ex: 13:07 → 13:25
```

**2. Load Tasks from API**
```javascript
// 3 API calls in parallel
GET /api/v3/gitfocus/tasks/pomodoro
→ state.pomodoroTasks = [...] (LISTE_MERE.v3.csv)

GET /api/v3/gitfocus/tasks/recurrent?pause_only=true
→ state.pauseTasks = [...] (IS_PAUSE=1)

GET /api/v3/gitfocus/tasks/recurrent?exclude_pauses=true
→ state.recurrentTasks = [...] (IS_PAUSE=0)
```

**3. Load Obstacles**
```javascript
GET /api/v3/gitfocus/temps-morts?date=2025-11-06
→ state.tempsMorts = [...] (temps_morts.csv filtered by date)
```

---

### PHASE 2: Sélection Utilisateur (Frontend)

**4. User Selects Pomodoros**
```javascript
// Onglet Pomodoro - checkboxes
state.selectedPomodoroIds = ["TASK001", "TASK002"]; // 2 tâches sélectionnées
```

**5. User Drags Pauses** ✅ NOUVEAU
```javascript
// Onglet Pauses - drag & drop
// User dragged: Méditation → Respiration → Méditation (dup)
state.selectedPauseIds = ["REC001", "REC003", "REC001"]; // Ordre important!
state.pauseOrder = [0, 1, 2]; // Index dans la liste drag & drop
```

**6. User Toggles Récurrentes**
```javascript
// Onglet Récurrentes - toggle switches
// User enabled: Arroser plantes, Ménage salon
state.enabledRecurrentIds = ["REC002", "REC005"];
```

**7. User Config Options**
```javascript
state.options = {
    calin_enabled: true,     // Insérer câlins (every 2 pauses)
    clope_enabled: false,    // Insérer clopes (every 240min work)
    clope_interval_min: 120
};
```

---

### PHASE 3: Génération Backend (POST /planning/generate)

**8. Frontend → Backend Request**
```javascript
POST /api/v3/gitfocus/planning/generate
Body: {
    date: "2025-11-06",
    planning_start_time: "13:25",
    pomodoro_ids: ["TASK001", "TASK002"],
    pause_ids: ["REC001", "REC003", "REC001"], // ✅ Ordre préservé, duplicatas OK
    recurrent_ids: ["REC002", "REC005"],       // ✅ Récurrentes actives
    calin_enabled: true,
    clope_enabled: false
}
```

**9. Backend Load Data**
```python
# backend/planning_engine_v3/data_loader.py

# Load selected Pomodoro tasks
pomodoros = load_pomodoro_tasks(data_dir / 'LISTE_MERE.v3.csv', pomodoro_ids)

# Load selected Pause tasks (by ID, preserve order and duplicates)
pauses = []
for pause_id in pause_ids:  # ✅ Loop preserves order and duplicates
    task = load_recurrent_task_by_id(data_dir / 'TACHES_RECURRENTES.v3.csv', pause_id)
    if task:
        pauses.append(task)

# Load active Recurrent tasks (exclude pauses)
recurrents = load_recurrent_tasks(data_dir / 'TACHES_RECURRENTES.v3.csv',
                                   recurrent_ids,
                                   exclude_pauses=True)

# Load Planned tasks for date
planned = load_planned_tasks(data_dir / 'TACHES_PLANIFIEES.v3.csv', date)

# Load Temps morts for date
temps_morts = load_temps_morts(data_dir / 'temps_morts.csv', date)
```

---

### PHASE 4: Backend - ÉTAPE 1 : ORDERING (Construction Séquence)

**10. Expand Pomodoros**
```python
# backend/planning_engine_v3/timeline_builder.py

def expand_pomodoros(pomodoros: List[Dict]) -> List[Dict]:
    """
    Convert tasks to 25-minute pomodoro units.

    Input: [{id: TASK001, name: "Maths", duration: 75}]
    Output: [
        {type: POMODORO, task_id: TASK001, name: "Maths", duration: 25, pomo_idx: 1, pomo_total: 3},
        {type: POMODORO, task_id: TASK001, name: "Maths", duration: 25, pomo_idx: 2, pomo_total: 3},
        {type: POMODORO, task_id: TASK001, name: "Maths", duration: 25, pomo_idx: 3, pomo_total: 3}
    ]
    """
    expanded = []
    for task in pomodoros:
        nb_pomos = math.ceil(task['duration'] / 25)
        for i in range(nb_pomos):
            expanded.append({
                'type': 'POMODORO',
                'task_id': task['id'],
                'task_name': task['name'],
                'duration': 25,
                'pomodoro_index': i + 1,
                'pomodoro_total': nb_pomos,
                'minuteOffset': 0  # Placeholder (calculated in STEP 2)
            })
    return expanded
```

**11. Alternate Pomodoros & Pauses** ✅ LOGIQUE CLÉ
```python
def alternate_pomodoros_pauses(pomodoros: List[Dict], pauses: List[Dict]) -> List[Dict]:
    """
    Alternate work and pauses.
    Cycle through pauses list (with duplicates preserved).

    Input:
        pomodoros: [P1, P2, P3, P4, P5]
        pauses: [Pause1, Pause2, Pause1]  # Note: Pause1 appears twice

    Output: [P1, Pause1, P2, Pause2, P3, Pause1, P4, Pause2, P5, Pause1, ...]
    """
    alternated = []
    pause_index = 0

    for i, pomo in enumerate(pomodoros):
        # Add pomodoro
        alternated.append(pomo)

        # Add pause after (except last pomodoro)
        if i < len(pomodoros) - 1:
            pause = pauses[pause_index % len(pauses)]  # Cycle through pauses
            alternated.append({
                'type': 'PAUSE',
                'task_id': pause['id'],
                'task_name': pause['name'],
                'duration': pause['duration'],
                'minuteOffset': 0  # Placeholder
            })
            pause_index += 1

    return alternated
```

**12. Insert Calins** (Optional, if enabled)
```python
def insert_calins(alternated: List[Dict]) -> List[Dict]:
    """
    Insert 5-minute câlin after every 2 pauses.

    Input: [P1, Pause1, P2, Pause2, P3, Pause3, P4, ...]
    Output: [P1, Pause1, P2, Pause2, CÂLIN, P3, Pause3, P4, Pause4, CÂLIN, ...]
    """
    result = []
    pause_count = 0

    for task in alternated:
        result.append(task)

        if task['type'] == 'PAUSE':
            pause_count += 1

            # Every 2 pauses, insert câlin
            if pause_count % 2 == 0:
                result.append({
                    'type': 'CALIN',
                    'task_name': 'Câlin',
                    'duration': 5,
                    'minuteOffset': 0,
                    'autoGenerated': True
                })

    return result
```

**13. Insert Clopes** (Optional, if enabled)
```python
def insert_clopes(alternated: List[Dict], interval_min: int) -> List[Dict]:
    """
    Insert 25-minute clope break when cumulative work time >= interval_min.

    Input: alternated list, interval_min=120
    Behavior: After 120min of POMODORO work, insert CLOPE (25min), reset counter
    """
    result = []
    cumulative_work_min = 0

    for task in alternated:
        result.append(task)

        if task['type'] == 'POMODORO':
            cumulative_work_min += task['duration']

            # Check if threshold reached
            if cumulative_work_min >= interval_min:
                result.append({
                    'type': 'CLOPE',
                    'task_name': 'Clope',
                    'duration': 25,
                    'minuteOffset': 0,
                    'autoGenerated': True
                })
                cumulative_work_min = 0  # Reset counter

    return result
```

**Résultat ÉTAPE 1** : Liste ordonnée sans heures
```python
ordered_tasks = [
    {type: POMODORO, task_name: "Maths", duration: 25, minuteOffset: 0, pomo_idx: 1},
    {type: PAUSE, task_name: "Méditation", duration: 10, minuteOffset: 0},
    {type: POMODORO, task_name: "Maths", duration: 25, minuteOffset: 0, pomo_idx: 2},
    {type: PAUSE, task_name: "Respiration", duration: 5, minuteOffset: 0},
    {type: CALIN, task_name: "Câlin", duration: 5, minuteOffset: 0},  # ← Inserted
    {type: POMODORO, task_name: "Maths", duration: 25, minuteOffset: 0, pomo_idx: 3},
    {type: PAUSE, task_name: "Méditation", duration: 10, minuteOffset: 0},  # ← Duplicate preserved
    ...
]
```

---

### PHASE 5: Backend - ÉTAPE 2 : TIME CALCULATION (Calcul Heures)

**14. Convert Temps Morts to Linear Obstacles**
```python
# backend/planning_engine_v3/timeline_calculator.py

def convert_temps_morts_to_obstacles(temps_morts: List[Dict], planning_start: datetime) -> List[Dict]:
    """
    Convert CSV temps_morts to linear obstacles (minutes from planning_start).

    Input:
        temps_morts: [{date: "2025-11-06", heure_debut: "15:00", heure_fin: "16:00", titre: "RDV"}]
        planning_start: datetime(2025-11-06 13:25)

    Output:
        obstacles: [{startMinute: 95, endMinute: 155, type: "temps_mort", originalData: {...}}]
    """
    obstacles = []

    for tm in temps_morts:
        # Parse dates
        tm_start = datetime.strptime(f"{tm['date']} {tm['heure_debut']}", "%Y-%m-%d %H:%M")
        tm_end = datetime.strptime(f"{tm['date']} {tm['heure_fin']}", "%Y-%m-%d %H:%M")

        # Convert to minutes from planning_start
        start_minute = int((tm_start - planning_start).total_seconds() / 60)
        end_minute = int((tm_end - planning_start).total_seconds() / 60)

        # Skip past obstacles
        if end_minute < 0:
            continue

        obstacles.append({
            'startMinute': start_minute,
            'endMinute': end_minute,
            'type': 'temps_mort',
            'originalData': tm
        })

    return sorted(obstacles, key=lambda x: x['startMinute'])
```

**15. Rebuild Timeline (Calculate All minuteOffsets)**
```python
def rebuild_timeline(ordered_tasks: List[Dict], obstacles: List[Dict]) -> List[Dict]:
    """
    Calculate minuteOffset for each task, respecting obstacles.

    Algorithm:
        1. Start at minute 0
        2. For each task:
            a. Find next free slot (skip obstacles)
            b. Assign minuteOffset
            c. Advance current time by task duration
    """
    current_minute = 0

    for task in ordered_tasks:
        # Find next free slot
        next_free = find_next_free_slot(current_minute, task['duration'], obstacles)

        # Assign minuteOffset
        task['minuteOffset'] = next_free

        # Advance time
        current_minute = next_free + task['duration']

    return ordered_tasks
```

**16. Find Next Free Slot (Collision Detection)**
```python
def find_next_free_slot(start_minute: int, duration: int, obstacles: List[Dict]) -> int:
    """
    Find next available slot that doesn't overlap obstacles.

    Algorithm:
        1. Check if [start_minute, start_minute+duration] overlaps any obstacle
        2. If overlap: jump to obstacle.endMinute, retry
        3. If no overlap: return start_minute
    """
    candidate_start = start_minute
    MAX_SEARCH = 43200  # 30 days in minutes

    while candidate_start < MAX_SEARCH:
        candidate_end = candidate_start + duration
        has_collision = False

        # Check all obstacles
        for obstacle in obstacles:
            # Overlap condition: start < obstacle.end AND end > obstacle.start
            if candidate_start < obstacle['endMinute'] and candidate_end > obstacle['startMinute']:
                # Collision detected, jump past obstacle
                candidate_start = obstacle['endMinute']
                has_collision = True
                break

        if not has_collision:
            return candidate_start  # Found free slot

    raise Exception("No free slot found in 30 days")
```

**17. Insert Planned Tasks** (After timeline built)
```python
def insert_planned_tasks(timeline: List[Dict], planned_tasks: List[Dict], obstacles: List[Dict]) -> List[Dict]:
    """
    Insert tasks with fixed time requests.

    Algorithm:
        1. For each planned task:
            a. Calculate requested minuteOffset
            b. Try to place at requested time
            c. If collision with obstacle/other planned: find closest free slot
            d. Mark as rescheduled if moved
    """
    for planned in planned_tasks:
        # Calculate requested time
        planned_time = datetime.strptime(f"{planned['date']} {planned['planned_start']}", "%Y-%m-%d %H:%M")
        requested_minute = int((planned_time - planning_start).total_seconds() / 60)

        # Try to place at requested time
        actual_minute = find_next_free_slot(requested_minute, planned['duration'], obstacles)

        # Insert in timeline (sorted by minuteOffset)
        timeline.append({
            'type': 'PLANNED',
            'task_name': planned['name'],
            'duration': planned['duration'],
            'minuteOffset': actual_minute,
            'originalPlannedTime': requested_minute,
            'rescheduled': (actual_minute != requested_minute)
        })

    # Re-sort timeline by minuteOffset
    timeline.sort(key=lambda x: x['minuteOffset'])

    return timeline
```

**Résultat ÉTAPE 2** : Timeline avec heures calculées
```python
timeline = [
    {type: POMODORO, task_name: "Maths", duration: 25, minuteOffset: 0, pomo_idx: 1},
    {type: PAUSE, task_name: "Méditation", duration: 10, minuteOffset: 25},
    {type: POMODORO, task_name: "Maths", duration: 25, minuteOffset: 35, pomo_idx: 2},
    {type: PAUSE, task_name: "Respiration", duration: 5, minuteOffset: 60},
    {type: CALIN, task_name: "Câlin", duration: 5, minuteOffset: 65},
    {type: TEMPS_MORT, task_name: "RDV médical", duration: 60, minuteOffset: 95},  # ← Obstacle
    {type: POMODORO, task_name: "Maths", duration: 25, minuteOffset: 155, pomo_idx: 3},  # ← Jumped past obstacle
    ...
]
```

---

### PHASE 6: Backend - Conversion Display Format

**18. Convert to Absolute Times**
```python
def convert_timeline_to_display(timeline: List[Dict], planning_start: datetime, date: str) -> List[Dict]:
    """
    Convert minuteOffsets to absolute times for display.

    Input:
        timeline: [{minuteOffset: 0, duration: 25, ...}]
        planning_start: datetime(2025-11-06 13:25)

    Output:
        display: [{date: "2025-11-06", heure_debut: "13:25", heure_fin: "13:50", ...}]
    """
    display_slots = []

    for task in timeline:
        # Calculate absolute times
        start_dt = planning_start + timedelta(minutes=task['minuteOffset'])
        end_dt = start_dt + timedelta(minutes=task['duration'])

        display_slots.append({
            'date': start_dt.strftime('%Y-%m-%d'),
            'heure_debut': start_dt.strftime('%H:%M'),
            'heure_fin': end_dt.strftime('%H:%M'),
            'task_name': task['task_name'],
            'task_id': task.get('task_id', ''),
            'type': task['type'].lower(),
            'duration_min': task['duration'],
            'pomodoro_index': task.get('pomodoro_index'),
            'pomodoro_total': task.get('pomodoro_total'),
            'rescheduled': task.get('rescheduled', False)
        })

    return display_slots
```

**19. Calculate Statistics**
```python
def calculate_statistics(timeline: List[Dict]) -> Dict:
    """Calculate summary stats."""
    stats = {
        'total_pomodoros': len([t for t in timeline if t['type'] == 'POMODORO']),
        'total_pauses': len([t for t in timeline if t['type'] == 'PAUSE']),
        'total_calins': len([t for t in timeline if t['type'] == 'CALIN']),
        'total_clopes': len([t for t in timeline if t['type'] == 'CLOPE']),
        'total_work_min': sum(t['duration'] for t in timeline if t['type'] == 'POMODORO'),
        'total_pause_min': sum(t['duration'] for t in timeline if t['type'] in ['PAUSE', 'CALIN', 'CLOPE']),
        'planning_start': timeline[0]['heure_debut'],
        'planning_end': timeline[-1]['heure_fin']
    }
    return stats
```

**20. Return JSON Response**
```python
# backend/planning_engine_v3/planning_generator.py

def generate_planning(date, planning_start_time, pomodoro_ids, pause_ids, recurrent_ids, options):
    # ... all steps above ...

    return {
        'success': True,
        'date': date,
        'planning': display_slots,  # List of display slot objects
        'statistics': stats,
        'timeline_debug': {  # Optional debug info
            'planning_start_minute': 0,
            'total_obstacles': len(obstacles),
            'total_tasks': len(timeline)
        }
    }
```

---

### PHASE 7: Frontend Display

**21. Receive Planning**
```javascript
// Frontend - gitfocus_v3.js

const response = await fetch('/api/v3/gitfocus/planning/generate', {
    method: 'POST',
    body: JSON.stringify({...})
});

const data = await response.json();
state.currentPlanning = data.planning;  // Save for export later
renderPlanning(data.planning);
renderStatistics(data.statistics);
```

**22. Render Planning Timeline**
```javascript
function renderPlanning(planning) {
    const container = document.getElementById('planning-display');
    container.innerHTML = '';

    for (const slot of planning) {
        const item = document.createElement('div');
        item.className = `planning-item type-${slot.type}`;

        let content = `
            <span class="time">${slot.heure_debut} - ${slot.heure_fin}</span>
            <span class="name">${slot.task_name}</span>
        `;

        // Add pomodoro index if applicable
        if (slot.type === 'pomodoro') {
            content += `<span class="pomo-badge">${slot.pomodoro_index}/${slot.pomodoro_total}</span>`;
        }

        // Mark rescheduled tasks
        if (slot.rescheduled) {
            content += `<span class="rescheduled-badge">⚠️ Décalé</span>`;
        }

        item.innerHTML = content;
        container.appendChild(item);
    }
}
```

---

### PHASE 8: Export CSV

**23. User Clicks Export**
```javascript
// Frontend
document.getElementById('export-csv-btn').addEventListener('click', async () => {
    const response = await fetch('/api/v3/gitfocus/planning/export', {
        method: 'POST',
        body: JSON.stringify({
            date: state.currentDate,
            planning: state.currentPlanning
        })
    });

    const data = await response.json();
    showNotification(`Planning exporté: ${data.file_path}`, 'success');
});
```

**24. Backend Export to CSV**
```python
# backend/planning_engine_v3/data_writer.py

def write_planning_csv(csv_path: Path, planning: List[Dict]) -> None:
    """
    Write planning to planned.csv (atomic operation).

    CRITICAL: Use atomic write (temp + rename) to prevent corruption.
    """
    fieldnames = ['date', 'heure_debut', 'heure_fin', 'task_name', 'task_id',
                  'type', 'duration_min', 'pomodoro_index', 'pomodoro_total', 'rescheduled']

    # Atomic write pattern
    temp_file = csv_path.with_suffix('.tmp')

    with open(temp_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(planning)

    # Atomic rename (OS-level guarantee)
    temp_file.replace(csv_path)
```

**25. Log Pause Usage** (Machine Learning)
```python
def log_pause_usage(planning: List[Dict], export_timestamp: str, data_dir: Path) -> None:
    """
    Log which pauses were used for future scoring.
    Append to pause_usage_history.csv.
    """
    history_file = data_dir / 'pause_usage_history.csv'

    pause_entries = []
    for i, slot in enumerate(planning):
        if slot['type'] == 'pause':
            pause_entries.append({
                'timestamp': export_timestamp,
                'date': slot['date'],
                'task_id': slot['task_id'],
                'task_name': slot['task_name'],
                'placement_order': i,
                'time_placed': slot['heure_debut']
            })

    # Append to history (NOT atomic, append-only file)
    with open(history_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'date', 'task_id', 'task_name',
                                                'placement_order', 'time_placed'],
                                delimiter=';', quoting=csv.QUOTE_ALL)
        if history_file.stat().st_size == 0:  # Empty file, write header
            writer.writeheader()
        writer.writerows(pause_entries)
```

---

## 📊 RÉCAPITULATIF FLUX COMPLET

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND                                                        │
├─────────────────────────────────────────────────────────────────┤
│ 1. Init planning start time (now + 15min, rounded to 5)        │
│ 2. Load tasks (Pomodoro, Pauses, Récurrentes)                  │
│ 3. Load obstacles (temps_morts)                                │
│ 4-7. User selections (Pomodoro IDs, Pause IDs ordered, Toggle) │
└────────────────────────┬────────────────────────────────────────┘
                         │ POST /planning/generate
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND - ÉTAPE 1: ORDERING (Build sequence)                   │
├─────────────────────────────────────────────────────────────────┤
│ 9. Load data from CSV (filter by IDs)                          │
│ 10. Expand Pomodoros (75min → 3x 25min)                        │
│ 11. Alternate Pomodoros & Pauses (cycle through pauses)        │
│ 12. Insert Calins (every 2 pauses, if enabled)                 │
│ 13. Insert Clopes (every 240min work, if enabled)              │
│    → ordered_tasks = [P1, Pause1, P2, Pause2, CÂLIN, P3, ...]  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND - ÉTAPE 2: TIME CALCULATION (Calculate times)          │
├─────────────────────────────────────────────────────────────────┤
│ 14. Convert temps_morts to obstacles (startMinute, endMinute)  │
│ 15. Rebuild timeline (calculate minuteOffset for all tasks)    │
│ 16. Find next free slot (collision detection with obstacles)   │
│ 17. Insert planned tasks (at requested time if possible)       │
│    → timeline with minuteOffsets = [0, 25, 35, 95, 155, ...]   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND - CONVERSION & RETURN                                   │
├─────────────────────────────────────────────────────────────────┤
│ 18. Convert to display format (minuteOffset → absolute times)  │
│ 19. Calculate statistics (total work, pauses, etc.)            │
│ 20. Return JSON (planning, stats)                              │
└────────────────────────┬────────────────────────────────────────┘
                         │ JSON Response
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND - DISPLAY                                              │
├─────────────────────────────────────────────────────────────────┤
│ 21. Receive planning JSON                                       │
│ 22. Render timeline (colored items by type)                    │
│    [Enable Export button]                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │ User clicks Export
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND - EXPORT                                                │
├─────────────────────────────────────────────────────────────────┤
│ 23. POST /planning/export                                       │
│ 24. Write planned.csv (ATOMIC: temp + rename)                  │
│ 25. Log pause usage (pause_usage_history.csv for ML)           │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ POINTS CRITIQUES V3

### 1. **Ordre Pauses Préservé** ✅ CRITIQUE
```javascript
// Frontend envoie l'ordre exact dragué par l'utilisateur
pause_ids: ["REC001", "REC003", "REC001"]  // Duplicates + ordre intentionnel

// Backend DOIT préserver cet ordre et duplicatas
for pause_id in pause_ids:  # Loop itère dans l'ordre exact
    task = load_by_id(pause_id)
    pauses.append(task)
```

### 2. **Timeline Linéaire (Minutes Relatives)** ✅ ARCHITECTURE
```
TOUT calcul en minutes depuis planningStartTime:
- minuteOffset = 0 → planning start
- minuteOffset = 25 → +25 minutes
- minuteOffset = 1440 → +1 jour (jour suivant)

Conversion UNIQUEMENT pour affichage final:
- minutesToDateTime(minuteOffset, planningStart) → {date, time}
```

### 3. **Architecture 2-Step OBLIGATOIRE** ✅ RÈGLE D'OR
```
ÉTAPE 1: ORDERING
└─ Construire séquence SANS minuteOffset (ou =0)
   [P1, Pause1, CÂLIN, P2, Pause2, ...]

ÉTAPE 2: TIME CALCULATION
└─ Appeler rebuildTimeline()
   Calculer minuteOffsets séquentiellement
   [P1@0, Pause1@25, CÂLIN@35, P2@40, Pause2@65, ...]
```

### 4. **Collisions (Ordre Priorité)** ✅ ALGORITHM
```
1. TEMPS_MORT (priorité absolue)
   → Bloque complètement, planning saute par-dessus

2. TÂCHE PLANIFIÉE (priorité secondaire)
   → Place à l'heure demandée si possible
   → Sinon: trouve créneau libre le plus proche
   → Mark rescheduled=true si déplacée

3. POMODORO/PAUSE/CÂLIN/CLOPE (priorité tertiaire)
   → Remplissent créneaux libres restants
```

### 5. **Atomic Writes OBLIGATOIRE** ✅ DATA INTEGRITY
```python
# JAMAIS écrire directement dans le fichier final
# TOUJOURS: temp file + atomic rename
temp = csv_path.with_suffix('.tmp')
# ... write to temp ...
temp.replace(csv_path)  # OS-level atomic operation
```

### 6. **Drag & Drop Natif (Pas de Lib)** ✅ FRONTEND
```javascript
// Utiliser Drag & Drop API native HTML5
item.draggable = true;
item.addEventListener('dragstart', ...);
selectedPanel.addEventListener('drop', ...);

// PAS de sortable.js, PAS de dnd-kit, PAS de react-beautiful-dnd
// JavaScript vanilla uniquement
```

---

## 🎯 DIFFÉRENCES CLÉS V2 → V3

| Aspect | V2 | V3 |
|--------|----|----|
| **Tâches Respiration** | CSV séparé (TACHES_RESPIRATOIRES.v2.csv) | Fusionné dans TACHES_RECURRENTES.v3.csv (IS_PAUSE=1) |
| **Onglet Pauses** | Compteurs (x1, x2...) | Drag & drop, ordre libre, duplicatas |
| **Sélection Pauses** | Click multiple sur même tâche | Drag multiple fois même tâche |
| **Ordre Pauses** | Implicite (tri CSV) | Explicite (ordre drag & drop) |
| **Calcul Timeline** | Slots 30min pré-calculés | Minutes relatives + rebuildTimeline() |
| **Collisions** | String parsing dates | Arithmétique entière (minuteOffset) |
| **Multi-jours** | Complexe (gestion dates) | Natif (minuteOffset > 1440) |
| **Backend Logic** | Partiel (frontend calcule aussi) | 100% backend (frontend affiche seulement) |
| **Drag & Drop** | Non disponible | Natif HTML5 |
| **Épinglage** | Non | Oui (pauses persistent après refresh) |

---

## 🚀 PROCHAINES ÉTAPES

**Pour implémenter V3** :

1. **Backend d'abord** (déjà commencé dans `backend/planning_engine_v3/`)
   - Finir `timeline_calculator.py`
   - Finir `planning_generator.py`
   - Tests unitaires

2. **API Flask** (`webapp_v3/api/routes.py`)
   - Route `/planning/generate`
   - Route `/planning/export`
   - Route `/pinned-pauses`

3. **Frontend HTML** (`webapp_v3/templates/gitfocus_v3.html`)
   - Onglet Pauses avec 2 colonnes
   - Drag & drop zones

4. **Frontend JS** (`webapp_v3/static/js/`)
   - Drag & Drop API
   - État local (selectedPauseIds avec ordre)
   - Render timeline

5. **Tests E2E**
   - Scénario complet: sélection → génération → affichage → export

---

**DATE**: 2025-11-06
**VERSION**: V3 (Timeline Linéaire - Backend-First)
**STATUT**: Documentation de référence
**AUTEUR**: Claude + Julio
