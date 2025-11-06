# Quick Reference - GitFocus V3

## 🚀 Start/Stop
```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
webapp\venv\Scripts\python.exe -m webapp.server  # Direct start
scripts\start.bat      # Kill all + start
scripts\restart.bat    # Restart
```

## 🧪 Test URLs
```
http://localhost:5000/api/v2/gitfocus/health
http://localhost:5000/api/v2/gitfocus/tasks/pomodoro
http://localhost:5000/gitfocus-v2
```

## 📁 Data Location
```
C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\
├── LISTE_MERE.v2.csv           # Pomodoros
├── TACHES_RESPIRATOIRES.v2.csv # Pauses
├── TACHES_RECURRENTES.v2.csv   # Recurrent
├── TACHES_PLANIFIEES.v2.csv    # Planned
├── temps_morts.csv             # Obstacles
└── planning_state.json         # State
```

## 💾 Atomic Write Pattern
```python
temp = csv_path.with_suffix('.tmp')
# write to temp
temp.replace(csv_path)  # Atomic
```

## 🏗️ V3 Core Pattern
```javascript
// STEP 1: ORDERING (NO minuteOffset)
const tasks = alternatePomodoresRespiration(pomos, resps);
insertCalins(tasks);    // Every 2 respirations
insertClopes(tasks);    // Every 240min work

// STEP 2: TIME CALCULATION
rebuildTimeline(tasks, obstacles);  // Calculates ALL minuteOffsets
```

## 🔍 Debug Commands
```bash
grep -r "function_name" backend/     # Find code
netstat -ano | findstr :5000         # Check port
git log --oneline -10                # Recent commits
git diff HEAD~1                      # Last changes
```

## 📊 Key Structures
```javascript
Task: {minuteOffset, duration, type, taskId, taskName, isFixed}
Obstacle: {startMinute, endMinute, type, originalData}
```

## ⚠️ Critical Rules
- CSV : délimiteur `;`, encoding `utf-8`, QUOTE_ALL
- ALWAYS atomic writes (temp + rename)
- ALWAYS call rebuildTimeline() after timeline modification
- NEVER calculate minuteOffset in STEP 1 (ORDERING)
- Dates API: `YYYY-MM-DD`, User: `DD.MM.YY`

## 🐛 Common Fixes
```bash
# Encoding error → re-encode latin-1 to UTF-8
# Port occupied → scripts\stop.bat
# Cache issue → Ctrl+F5 (browser hard reload)
# Context overflow → /clear (Claude CLI)
```

## 📚 Docs (DO NOT LOAD IN CONTEXT)
- CLAUDE_CONCIS.md → Project overview
- ESSENTIALS_V3.md → V3 implementation guide
- SPECIFICATIONS_COMPLETE_V3.md → Full specs (read only when needed)
- PLAN_REFONTE_V3.md → Migration plan (read only when needed)
