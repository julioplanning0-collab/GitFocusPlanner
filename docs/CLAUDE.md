# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**GitFocus Planner** - Web-based task planning system for Pomodoro-style work sessions with automatic scheduling. Generates daily schedules from task lists, handles multiple task types (work, respiration, recurrent, planned), and exports to CSV for client consumption.

**Key Components**:
- `webapp/` - Flask web server with REST API and web interface
- `backend/` - Planning engine modules (data loading, scheduling, CSV writing)
- `scripts/` - Server management scripts (start, stop, restart)
- `data/` - Example CSV data files

**External Data** (production):
- Located at: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\`
- CSV files with semicolon delimiter, UTF-8 encoding

---

## Essential Commands

### Development

```bash
# Start server (recommended method)
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
webapp\venv\Scripts\python.exe -m webapp.server

# Using scripts (Windows)
scripts\start.bat    # Kill all processes + start server
scripts\stop.bat     # Stop all processes
scripts\restart.bat  # Stop + start
```

### Testing

```bash
# Test API endpoints
curl http://localhost:5000/api/v2/gitfocus/health
curl http://localhost:5000/api/v2/gitfocus/tasks/pomodoro
curl http://localhost:5000/api/v2/gitfocus/tasks/respiration

# Access web interface
http://localhost:5000/gitfocus-v2
```

---

## Architecture Overview

### Layered Architecture (STRICT separation)

```
GitfocusPlanner/
├── backend/
│   └── planning_engine/       # Business logic ONLY
│       ├── data_loader.py     # Read CSV files (List[Dict])
│       ├── data_writer.py     # Write CSV files (ATOMIC)
│       ├── slot_calculator.py # Calculate free time slots
│       ├── task_integrator.py # Integrate special tasks
│       ├── planning_generator.py # Main orchestrator
│       └── state_manager.py   # Server-side state persistence
│
├── webapp/
│   ├── server.py              # Flask application
│   ├── api/
│   │   └── routes_gitfocus_v2.py # REST API Blueprint (28 endpoints)
│   ├── templates/
│   │   └── gitfocus_v2.html   # Web interface
│   └── static/
│       ├── css/gitfocus_v2.css
│       └── js/gitfocus_v2.js
│
└── scripts/
    ├── start.bat              # Server startup (kill + verify + start)
    ├── stop.bat               # Stop all processes
    └── restart.bat            # Restart server
```

**Critical Rules**:
- `backend/` NEVER does direct I/O (reads via Path objects, writes via atomic functions)
- `webapp/api/` handles HTTP/JSON, delegates logic to `backend/`
- All CSV writes MUST use atomic operations (temp file + rename)
- All data models use `List[Dict]` (not Pydantic, not dataclasses)

### Planning Generation Pipeline

```
TRIGGER (user clicks "Générer Planning")
    ↓
1. Load Selected Tasks
   → User selects Pomodoro tasks (checkboxes)
   → User selects Respiration tasks (with counters x2, x3...)
   → POST /api/v2/gitfocus/planning/generate
    ↓
2. Load Data Sources (data_loader.py)
   → LISTE_MERE.v2.csv (Pomodoro tasks)
   → TACHES_RESPIRATOIRES.v2.csv (Respiration tasks, sorted by EXPORT_COUNT)
   → TACHES_RECURRENTES.v2.csv (Recurrent tasks, filter IS_ACTIVE=1)
   → TACHES_PLANIFIEES.v2.csv (Planned tasks with fixed time)
   → temps_morts.csv (Blocked time slots from Google Calendar)
    ↓
3. Calculate Free Slots (slot_calculator.py)
   → Day: 06:00 to 23:00 (30-minute blocks)
   → If date=today: Start at current time (rounded up to 15min)
   → Overlap detection: slot_start < tm_end AND slot_end > tm_start
   → Filter past slots for today
    ↓
4. Generate Base Planning (planning_generator.py)
   → Alternation: Pomodoro (25 min) → Pause (variable duration)
   → Use respiration task durations (5-20 min)
   → Fill free slots sequentially
    ↓
5. Integrate Planned Tasks (task_integrator.py)
   → Load TACHES_PLANIFIEES.v2.csv for target date
   → Calculate required Pomodoros (duration ÷ 25, rounded up)
   → Find closest Pomodoros to planned time
   → Replace with planned task (keep original slots)
   → Mark if rescheduled (original_time ≠ final time)
    ↓
6. Integrate Recurrent Tasks (task_integrator.py)
   → Filter tasks where NEXT_DUE_DATE <= target date
   → Place at available slots
    ↓
7. Repair Consecutive Pomodoros (task_integrator.py)
   → Scan for consecutive work tasks (no pause between)
   → Find next available pause (search after, then before)
   → Move pause between consecutive tasks
   → Repeat until no consecutive tasks remain
    ↓
8. Calculate Statistics
   → Total work time, pause time, task counts
   → Free time remaining
    ↓
9. Save State (state_manager.py)
   → planning_state.json (server-side, cross-device sync)
   → Atomic write (temp file + rename)
    ↓
10. Return Planning JSON
    → Frontend displays in timeline
```

### NO FALLBACKS Policy

**CRITICAL**: Never use default values when external dependencies fail.

**CSV file not found** → Return empty list `[]`, log WARNING (don't crash, allow partial data)
**Invalid CSV row** → Skip row, log ERROR with row details (don't fail entire load)
**Encoding error** → Re-encode from latin-1 to UTF-8, then retry (fix root cause)
**temps_morts missing** → Use empty list (assume no blocked time)

**When to BLOCK**:
- Invalid date format → Raise ValueError (API returns 400)
- Missing required fields in CSV → Skip row + log ERROR
- File write fails → Raise IOError (API returns 500)

**Why**:
- CSV data files are user-editable and may have errors
- System should degrade gracefully (show what's available)
- BUT: Log all errors clearly so user can fix root cause

See `REFONTE_SPECS.md` for detailed error handling specifications.

---

## Critical File Operations

### Atomic Writes (MANDATORY)

```python
from pathlib import Path

def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    """
    Atomic CSV write to prevent corruption on crash.

    NEVER use:
        with open(csv_path, 'w') as f:  # ❌ Risk of corruption

    ALWAYS use temp file + rename pattern:
    """
    temp_file = csv_path.with_suffix('.tmp')

    # Write to temp file first
    with open(temp_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    # Atomic rename (OS guarantees atomicity)
    temp_file.replace(csv_path)
```

**Why**:
- If process crashes during write → temp file is corrupted, original file is intact
- `Path.replace()` is atomic on all OS (POSIX guarantees)
- CSV files are critical data (user's task list, planning state)

### CSV Format Standards

All CSV files use:
- **Delimiter**: `;` (semicolon, NOT comma)
- **Quoting**: `csv.QUOTE_ALL` (all fields quoted, even empty)
- **Encoding**: `UTF-8` (NOT latin-1, NOT cp1252)
- **Line ending**: `\n` (LF, not CRLF)
- **Escape**: `""` (double quotes escaped as two double quotes)

**Example**:
```csv
"ID";"NAME";"DURATION_MIN";"PRIORITY"
"TASK001";"Révision mathématiques";"25";"1"
"TASK002";"Pause café";"10";"3"
```

**Common Pitfalls**:
```python
# ❌ WRONG - Uses comma, no quoting
writer = csv.DictWriter(f, delimiter=',')

# ❌ WRONG - No explicit encoding (defaults to system encoding)
with open(csv_path, 'w', newline='') as f:

# ✅ CORRECT
with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
```

---

## Data Files

### Source Data (`prod_data/`)

**Location**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\`

- `LISTE_MERE.v2.csv` - Pomodoro work tasks
  - Format: `ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;REMAINING_MIN;PRIORITY;TAGS;KEYWORDS;DEPENDENCIES;NOTES;DEADLINE;FIXED_START;PLANNED_START;STATUS`
  - Deadline format: `DD.MM.YY` (e.g., "29.10.25")

- `TACHES_RESPIRATOIRES.v2.csv` - Respiration/pause tasks
  - Format: `ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;REPEAT_INTERVAL_MIN;LAST_DONE_TIMESTAMP;LAST_DONE_DATE;EARLIEST_TIME;LATEST_TIME;IDEAL_TIME;PRIORITY;TAGS;KEYWORDS;DEPENDENCIES;NOTES;STATUS;EXPORT_COUNT`
  - Sorted by `EXPORT_COUNT DESC` (most popular first)
  - ID format: `R_001`, `R_002`, etc.

- `TACHES_RECURRENTES.v2.csv` - Recurrent tasks (daily/weekly/monthly)
  - Format: `ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;RECURRENCE_TYPE;RECURRENCE_INTERVAL;LAST_DONE_DATE;NEXT_DUE_DATE;PRIORITY;STATUS;IS_ACTIVE`
  - Filter: Only `IS_ACTIVE=1` are used in planning
  - ID format: `REC001`, `REC002`, etc.

- `TACHES_PLANIFIEES.v2.csv` - Planned tasks (fixed date/time)
  - Format: `ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;REMAINING_MIN;PRIORITY;TAGS;KEYWORDS;DEPENDENCIES;NOTES;DEADLINE;FIXED_START;PLANNED_START;STATUS`
  - `PLANNED_START` format: `DD.MM.YY HH:MM` (e.g., "29.10.25 14:30")
  - Auto-integrated into planning (replaces closest Pomodoros)

- `temps_morts.csv` - Blocked time slots (from Google Calendar)
  - Format: `DATE;HEURE DEBUT;HEURE FIN;TITRE`
  - Date format: `YYYY-MM-DD` (ISO format)
  - Time format: `HH:MM` (24-hour)

- `categories.csv` - Centralized categories for all task types
  - Format: `CATEGORY;SUB_CATEGORY`
  - Shared across Pomodoro, Respiration, Recurrent, Planned tasks

### Generated Data (`prod_data/`)

- `planned.csv` - Generated planning (exported)
  - Format: `ID;NAME;DATE;HEURE_DEBUT;HEURE_FIN;DURATION_MIN;KIND;ORIGINAL_TIME`
  - `KIND`: `pomodoro`, `respiration`, `planned`, `recurrent`
  - Overwritten on each export (not append)

- `respiration_planning_history.csv` - Respiration task usage history
  - Format: `ID;NAME;DATE;PLANNED_TIME;DURATION_MIN;EXPORT_TIMESTAMP`
  - Append-only (cumulative history for analytics)

- `planning_state.json` - Server-side state (cross-device sync)
  - Format: `{"current_date": "YYYY-MM-DD", "selected_pomodoro_ids": [...], "selected_respiration_ids": [...]}`
  - Atomic writes (temp file + rename)

### Date Format Standards

**Different formats for different files** (legacy compatibility):

- **temps_morts.csv**: `YYYY-MM-DD` (ISO format) ← Google Calendar export
- **Task deadlines**: `DD.MM.YY` (e.g., "29.10.25") ← User-friendly input
- **Planned start times**: `DD.MM.YY HH:MM` (e.g., "29.10.25 14:30")
- **API communication**: `YYYY-MM-DD` (ISO format) ← REST API standard

**Conversion functions** (always explicit):
```python
from datetime import datetime

# User input (DD.MM.YY) → ISO (YYYY-MM-DD)
def parse_user_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, '%d.%m.%y')
    return dt.strftime('%Y-%m-%d')

# ISO (YYYY-MM-DD) → User display (DD.MM.YY)
def format_user_date(iso_date: str) -> str:
    dt = datetime.strptime(iso_date, '%Y-%m-%d')
    return dt.strftime('%d.%m.%y')
```

---

## API Endpoints

### REST API Blueprint

**Prefix**: `/api/v2/gitfocus`

**All endpoints return JSON**:
```json
{
  "success": true,
  "data": {...},
  "message": "Optional message"
}
```

**Error responses**:
```json
{
  "success": false,
  "error": "Error message"
}
```

### Health & Data Retrieval

- `GET /health` - Health check
  - Returns: `{"status": "healthy", "version": "2.0", "data_dir": "..."}`

- `GET /tasks/pomodoro` - List all Pomodoro tasks
- `GET /tasks/respiration` - List respiration tasks (sorted by popularity)
- `GET /tasks/recurrent` - List recurrent tasks
- `GET /tasks/planned?date=YYYY-MM-DD` - List planned tasks (optional date filter)
- `GET /categories` - List all categories and sub-categories

### Planning Generation

- `POST /planning/generate` - Generate daily planning
  - Body: `{"date": "YYYY-MM-DD", "pomodoro_ids": [...], "respiration_ids": [...]}`
  - Returns: Full planning with statistics

- `POST /planning/export` - Export planning to CSV
  - Writes to `planned.csv` on server
  - Returns: `{"csv_path": "...", "task_count": 42}`

### State Management

- `GET /state` - Get current server-side state
  - Returns: `{"current_date": "...", "selected_pomodoro_ids": [...], ...}`

- `POST /state` - Save server-side state
  - Body: `{"current_date": "...", "selected_pomodoro_ids": [...], ...}`
  - Atomic write to `planning_state.json`

### Task CRUD (Pomodoro)

- `POST /tasks/pomodoro` - Create Pomodoro task
- `PUT /tasks/pomodoro/<task_id>` - Update Pomodoro task
- `DELETE /tasks/pomodoro/<task_id>` - Delete Pomodoro task

### Task CRUD (Respiration)

- `POST /tasks/respiration` - Create respiration task
- `PUT /tasks/respiration/<task_id>` - Update respiration task
- `DELETE /tasks/respiration/<task_id>` - Delete respiration task

### Task CRUD (Recurrent)

- `POST /tasks/recurrent` - Create recurrent task
- `PUT /tasks/recurrent/<task_id>` - Update recurrent task
- `DELETE /tasks/recurrent/<task_id>` - Delete recurrent task
- `PATCH /tasks/recurrent/<task_id>/toggle` - Toggle IS_ACTIVE (0 ↔ 1)

### Task CRUD (Planned)

- `POST /tasks/planned` - Create planned task
- `PUT /tasks/planned/<task_id>` - Update planned task
- `DELETE /tasks/planned/<task_id>` - Delete planned task

### Categories

- `POST /categories` - Add new category/sub-category
  - Body: `{"category": "...", "sub_category": "..."}`
  - Updates `categories.csv` immediately

---

## Key Modules

### backend/planning_engine/data_loader.py

**Purpose**: Read all CSV files, return `List[Dict]`

**Functions**:
```python
def load_pomodoro_tasks(csv_path: Path) -> List[Dict]:
    """Load Pomodoro tasks from LISTE_MERE.v2.csv"""

def load_respiration_tasks(csv_path: Path) -> List[Dict]:
    """Load respiration tasks, sorted by EXPORT_COUNT DESC"""

def load_recurrent_tasks(csv_path: Path, active_only: bool = False) -> List[Dict]:
    """Load recurrent tasks, optionally filter IS_ACTIVE=1"""

def load_planned_tasks(csv_path: Path, date: Optional[str] = None) -> List[Dict]:
    """Load planned tasks, optionally filter by date"""

def load_temps_morts(csv_path: Path, date: str) -> List[Dict]:
    """Load blocked time slots for specific date"""

def load_categories(csv_path: Path) -> Dict[str, List[str]]:
    """Load categories, returns {"Category": ["SubCat1", "SubCat2"]}"""
```

**Error Handling**:
- File not found → Return `[]` + log WARNING
- Invalid CSV row → Skip row + log ERROR
- Encoding error → Re-encode latin-1 → UTF-8

**Helper functions**:
```python
def _clean_csv_field(field: str) -> str:
    """Remove surrounding quotes"""

def _safe_int(value: str, default: int = 0) -> int:
    """Safely convert to int, return default if invalid"""
```

### backend/planning_engine/data_writer.py

**Purpose**: Write all CSV files with atomic operations

**Functions**:
```python
def update_pomodoro_task(csv_path: Path, task_id: str, updates: Dict) -> None:
    """Update single Pomodoro task (atomic write)"""

def delete_pomodoro_task(csv_path: Path, task_id: str) -> None:
    """Delete single Pomodoro task (atomic write)"""

def increment_respiration_export_count(csv_path: Path, task_ids: List[str]) -> None:
    """Increment EXPORT_COUNT for used respiration tasks"""

def update_recurrent_task_active(csv_path: Path, task_id: str, is_active: int) -> None:
    """Toggle IS_ACTIVE (0/1) for recurrent task"""

def write_planning_csv(csv_path: Path, planning: List[Dict]) -> None:
    """Write planning to planned.csv (overwrites)"""

def append_respiration_history(csv_path: Path, entries: List[Dict]) -> None:
    """Append to respiration_planning_history.csv (cumulative)"""
```

**All writes use atomic pattern**:
```python
def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    temp_file = csv_path.with_suffix('.tmp')
    with open(temp_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    temp_file.replace(csv_path)  # Atomic
```

### backend/planning_engine/slot_calculator.py

**Purpose**: Calculate free 30-minute time slots

**Function**:
```python
def calculate_free_slots(date: str, temps_morts: List[Dict]) -> List[Dict]:
    """
    Calculate free slots for date, avoiding temps_morts.

    Args:
        date: ISO format YYYY-MM-DD
        temps_morts: List of blocked time slots

    Returns:
        List of {"heure_debut": "HH:MM", "heure_fin": "HH:MM"}

    Logic (🆕 2025-10-30 - Greedy Fill Algorithm):
        - Day: 06:00 to 24:00 (midnight)
        - If date == today: Start at current time (rounded up to 15min)
        - Sort temps_morts by start time
        - Fill ALL "holes" between temps_morts sequentially with 30-min slots
        - No gaps or alignment issues (100% time utilization)
    """
```

**Algorithm (Greedy Fill)**:
```python
# Start from day_start (06:00) or current time if today
current = day_start  # or rounded current time

# Build list of blocked periods from temps_morts
blocked_periods = [(tm_start, tm_end), ...]  # sorted

# Fill holes between blocked periods
for tm_start, tm_end in blocked_periods:
    # Fill the hole from current to tm_start
    while current + timedelta(minutes=30) <= tm_start:
        free_slots.append({
            'heure_debut': current.strftime("%H:%M"),
            'heure_fin': (current + timedelta(minutes=30)).strftime("%H:%M")
        })
        current += timedelta(minutes=30)

    # Jump past this temps_mort
    current = tm_end

# Fill final hole from current to midnight
while current < day_end:
    free_slots.append({...})
    current += timedelta(minutes=30)
```

**Key Improvement**: No longer generates fixed aligned slots - fills ALL available time continuously, maximizing utilization.

### backend/planning_engine/task_integrator.py

**Purpose**: Integrate special tasks into base planning

**Functions**:
```python
def integrate_planned_tasks(planning: List[Dict], planned_tasks: List[Dict]) -> List[Dict]:
    """
    Replace Pomodoros with planned tasks at closest time slots.

    Algorithm:
        1. For each planned task:
           - Calculate required Pomodoros (duration ÷ 25, rounded up)
           - Calculate distance from each Pomodoro to planned time
           - Sort Pomodoros by distance (ascending)
           - Replace N closest Pomodoros with planned task
           - Mark if rescheduled (original_time ≠ final_time)
    """

def integrate_recurrent_tasks(planning: List[Dict], recurrent_tasks: List[Dict]) -> List[Dict]:
    """
    Add recurrent tasks to planning at available slots.

    Algorithm:
        - Filter tasks where NEXT_DUE_DATE <= target date
        - Find available slots (no overlap)
        - Insert recurrent tasks
    """

def repair_consecutive_pomodoros(planning: List[Dict]) -> List[Dict]:
    """
    Ensure Pomodoro/Pause alternation.

    Algorithm:
        1. Scan for consecutive Pomodoros (no pause between)
        2. Find next available pause:
           - Search after consecutive block
           - If not found, search before
        3. Move pause between consecutive Pomodoros
        4. Repeat until no consecutive Pomodoros remain

    Why: Pomodoro technique requires alternation
    """
```

### backend/planning_engine/planning_generator.py

**Purpose**: Main orchestrator for planning generation

**Function**:
```python
def generate_planning(
    date: str,
    pomodoro_ids: List[str],
    respiration_ids: List[str],
    data_dir: Path
) -> Dict:
    """
    Generate daily planning (8-step algorithm).

    Returns:
        {
            "planning": [...],
            "statistics": {
                "total_work_time_min": 300,
                "total_pause_time_min": 60,
                "pomodoro_count": 12,
                "respiration_count": 12,
                "planned_count": 2,
                "recurrent_count": 1,
                "free_time_min": 120
            }
        }
    """
```

**8-Step Algorithm** (see Pipeline above)

**🆕 2025-10-30 - Key Modification in Base Planning Generation**:

The `_generate_base_planning()` function now uses a **time pointer approach** instead of slot indices:

```python
# Track current time instead of relying on slot indices
current_time = datetime.combine(target_date_obj,
    datetime.strptime(free_slots[0]['heure_debut'], "%H:%M").time())

for i in range(nb_pomodoros):
    # Add Pomodoro using current_time
    pomodoro_end = current_time + timedelta(minutes=25)
    planning.append({
        'heure_debut': current_time.strftime('%H:%M'),
        'heure_fin': pomodoro_end.strftime('%H:%M'),
        ...
    })
    current_time = pomodoro_end  # Advance time pointer

    # Add Recurrent task using current_time
    recurrent_end = current_time + timedelta(minutes=recurrent_duration)
    planning.append({
        'heure_debut': current_time.strftime('%H:%M'),
        'heure_fin': recurrent_end.strftime('%H:%M'),
        ...
    })
    current_time = recurrent_end  # Advance time pointer
```

**Why this change?**
- Previous approach used `free_slots[slot_index]['heure_debut']` which lost time continuity
- `recalculate_times()` then rewrote everything, causing 15-min loss at start
- New approach maintains strict time continuity, no recalculation needed (unless planned tasks integrated)
- Result: **100% time utilization** from first free slot to midnight

**Conditional recalculate_times()**:
```python
# Only recalculate if we integrated planned tasks (which may break continuity)
if has_planned_tasks:
    planning = recalculate_times(planning, date, temps_morts)
else:
    logger.info("Skipping recalculate_times (times already correct)")
```

### backend/planning_engine/state_manager.py

**Purpose**: Server-side state persistence (cross-device sync)

**Functions**:
```python
def load_state(state_file: Path) -> Dict:
    """Load state from planning_state.json"""

def save_state(state_file: Path, state: Dict) -> None:
    """Save state to planning_state.json (atomic write)"""
```

**State Schema**:
```json
{
  "current_date": "2025-10-29",
  "selected_pomodoro_ids": ["TASK001", "TASK002"],
  "selected_respiration_ids": ["R_001", "R_002", "R_001"]
}
```

---

## Common Pitfalls to Avoid

1. **Encoding Errors**: Always specify `encoding='utf-8'` for file operations
   - CSV files may contain accented characters (French names)
   - Default encoding is system-dependent (cp1252 on Windows)

2. **Non-Atomic Writes**: Always use temp file + rename pattern
   - Direct writes risk corruption on crash
   - CSV files are critical user data

3. **Incorrect CSV Delimiter**: Always use `;` (semicolon)
   - Comma `,` will break parsing (task names contain commas)

4. **Date Format Confusion**: Different formats for different contexts
   - API: `YYYY-MM-DD` (ISO)
   - User input: `DD.MM.YY` (French format)
   - Always convert explicitly

5. **Missing Error Logs**: Always log errors with context
   - Don't silently skip invalid data
   - User needs to know what's wrong to fix it

6. **Hardcoded Paths**: Always use `Path` objects
   - Windows uses backslash `\`, Unix uses slash `/`
   - `Path` handles this automatically

7. **Process Leaks**: Always kill previous processes before starting
   - `scripts\start.bat` kills all Python processes first
   - Prevents port conflicts (port 5000)

---

## Workflow Before Code Changes

1. **Read specs**: Check `REFONTE_SPECS.md` and `REFONTE_PLAN.md`
2. **Search for existing code**: `grep -r "function_name" backend/`
3. **Plan change**: Document what you'll change (1 objective only)
4. **Identify root cause**: Don't patch symptoms, fix the real problem
5. **Implement**: Small incremental changes
6. **Test immediately**: Manual API test or browser test
7. **Verify encoding**: Check file is UTF-8 after edit
8. **Delete old code**: Remove obsolete code (don't comment out)
9. **Verify no duplication**: `grep -r` again
10. **Update docs**: Update `CLAUDE.md` if architecture changes

---

## Development Philosophy

This project follows strict engineering discipline:

- **No shortcuts**: Always find root cause, never patch symptoms
- **No silent failures**: Log all errors clearly with context
- **Atomic operations**: All file writes atomic, prevent data corruption
- **Explicit conversions**: Never rely on implicit type coercion
- **Clear error messages**: User needs actionable information to fix issues
- **Single responsibility**: One change per commit, clear separation of concerns
- **Degrade gracefully**: Missing data → show what's available, log error

**When to fail hard** (raise exception):
- Invalid API request (400 Bad Request)
- File write failure (500 Internal Server Error)
- Invalid date format (400 Bad Request)

**When to degrade gracefully** (return partial data + log error):
- CSV file not found → Return `[]` + log WARNING
- Invalid CSV row → Skip row + log ERROR
- Encoding error → Re-encode + retry + log INFO

**Why this distinction**:
- User errors (bad API request) → Fail fast, return clear error
- Data errors (corrupt CSV) → Show what's available, allow user to fix

---

## Troubleshooting

### Server won't start

```bash
# Check if port 5000 is occupied
netstat -ano | findstr :5000

# Kill all Python processes
scripts\stop.bat

# Restart server
scripts\start.bat
```

### Encoding errors in CSV

```python
# Re-encode file from latin-1 to UTF-8
from pathlib import Path

file_path = Path("C:/path/to/file.csv")
content = file_path.read_text(encoding='latin-1')
file_path.write_text(content, encoding='utf-8')
```

### Planning generation fails

Check logs for:
- Missing CSV files → Verify `prod_data/` directory exists
- Invalid date format → Use ISO format `YYYY-MM-DD`
- Invalid task IDs → Check IDs exist in CSV files

### Browser cache issues

Force reload:
- Windows: `Ctrl + F5`
- Mac: `Cmd + Shift + R`

Or clear browser cache entirely

---

## Scripts Documentation

### scripts/start.bat

**Purpose**: Start server with full cleanup and verification

**Phases**:
1. Kill all Python processes (`taskkill /F /IM python.exe`)
2. Verify environment:
   - Check `webapp\venv\` exists
   - Check `prod_data\` directory exists
   - Free port 5000 if occupied
3. Start Flask server (`python -m webapp.server`)

**URLs after startup**:
- Local: http://localhost:5000
- Network: http://192.168.1.117:5000
- Public: http://julioplanning0.duckdns.org:5000

**Interfaces**:
- V1 (legacy): `/gitfocus`
- V2 (refonte): `/gitfocus-v2`

### scripts/stop.bat

**Purpose**: Stop all server processes cleanly

**Actions**:
- Kill all Python processes
- Free port 5000

### scripts/restart.bat

**Purpose**: Restart server (stop + start)

**Actions**:
1. Call `stop.bat`
2. Wait 3 seconds
3. Call `start.bat`

---

**Last Updated**: 2025-10-29
**Maintainer**: Julio
**Python Version**: 3.11+
**Flask Version**: 2.x
**Architecture**: V2 Refonte (backend-first, REST API, server-side state)
