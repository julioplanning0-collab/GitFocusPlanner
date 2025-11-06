# GitFocus Planner - Guide Condensé

**Système de planification Pomodoro avec génération automatique de planning quotidien**

---

## 🎯 Architecture Essentielle

```
GitfocusPlanner/
├── backend/planning_engine/    # Logique métier pure (NO I/O)
│   ├── data_loader.py          # Lecture CSV → List[Dict]
│   ├── data_writer.py          # Écriture CSV atomique
│   ├── planning_generator.py  # Orchestrateur principal
│   ├── task_integrator.py     # Intégration tâches spéciales
│   └── state_manager.py        # Persistance état serveur
└── webapp/
    ├── server.py               # Flask app
    ├── api/routes_gitfocus_v2.py  # 28 endpoints REST
    └── templates/gitfocus_v2.html # Interface web
```

**Règles strictes** :
- `backend/` = logique pure, List[Dict] uniquement, NO Pydantic
- `webapp/api/` = HTTP/JSON, délègue à `backend/`
- Écritures CSV = TOUJOURS atomiques (temp + rename)

---

## ⚡ Commandes Essentielles

```bash
# Démarrer serveur
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
webapp\venv\Scripts\python.exe -m webapp.server

# OU via scripts
scripts\start.bat    # Kill all + start
scripts\restart.bat  # Stop + start

# Test API
curl http://localhost:5000/api/v2/gitfocus/health
curl http://localhost:5000/api/v2/gitfocus/tasks/pomodoro

# Interface web
http://localhost:5000/gitfocus-v2
```

---

## 📁 Données Critiques

**Location** : `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\`

**CSV Files** (délimiteur `;`, UTF-8, QUOTE_ALL) :
- `LISTE_MERE.v2.csv` - Tâches Pomodoro
- `TACHES_RESPIRATOIRES.v2.csv` - Tâches respiration (tri EXPORT_COUNT DESC)
- `TACHES_RECURRENTES.v2.csv` - Tâches récurrentes (filtre IS_ACTIVE=1)
- `TACHES_PLANIFIEES.v2.csv` - Tâches à heure fixe
- `temps_morts.csv` - Blocages agenda Google

**JSON State** :
- `planning_state.json` - État serveur (sync multi-device)

---

## 🔄 Pipeline de Génération (8 Étapes)

```
1. Load Selected Tasks     → Checkboxes Pomodoro + compteurs Respiration
2. Load Data Sources       → 5 CSV files
3. Calculate Free Slots    → 06:00-23:00, évite temps_morts
4. Generate Base Planning  → Alternance Pomodoro(25min)/Pause(5-20min)
5. Integrate Planned Tasks → Replace closest Pomodoros
6. Integrate Recurrent     → Fill available slots
7. Repair Consecutive Pomo → Insert pauses between work blocks
8. Save State + Return     → planning_state.json + JSON response
```

---

## 💾 Opérations Fichiers (CRITIQUE)

### Écriture Atomique (OBLIGATOIRE)
```python
def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]):
    temp = csv_path.with_suffix('.tmp')
    with open(temp, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(csv_path)  # Atomic rename
```

### Format CSV Standard
- Délimiteur : `;` (semicolon)
- Quoting : `csv.QUOTE_ALL`
- Encoding : `UTF-8`
- Line ending : `\n` (LF)

---

## ⚠️ Gestion Erreurs (NO FALLBACKS)

**Dégrader gracieusement** :
- CSV not found → `[]` + log WARNING
- Invalid CSV row → skip + log ERROR
- Encoding error → re-encode latin-1→UTF-8 + retry

**Échouer fort** :
- Invalid date format → ValueError (400)
- File write fails → IOError (500)
- Missing required fields → skip row + log ERROR

---

## 🐛 Pièges Communs

1. **Encoding** : TOUJOURS `encoding='utf-8'`
2. **CSV Delimiter** : TOUJOURS `;` (pas `,`)
3. **Atomic Writes** : TOUJOURS temp + rename
4. **Dates** : API=`YYYY-MM-DD`, User=`DD.MM.YY`
5. **Paths** : TOUJOURS `Path` objects (cross-platform)

---

## 🔧 Troubleshooting Rapide

```bash
# Port occupé
netstat -ano | findstr :5000
scripts\stop.bat

# Encoding CSV corrompu
# Re-encode : latin-1 → UTF-8

# Planning fails
# Check logs : CSV manquant? Date invalide? IDs inexistants?

# Cache browser
# Ctrl+F5 (Win) / Cmd+Shift+R (Mac)
```

---

## 📚 Workflow Avant Code

1. Lire specs relevantes (REFONTE_SPECS.md, REFONTE_PLAN.md)
2. Grep code existant : `grep -r "function_name" backend/`
3. Identifier ROOT CAUSE (pas patcher symptômes)
4. Implémenter (petit incrément)
5. Tester immédiatement
6. Vérifier encoding UTF-8
7. Supprimer old code (pas commenter)
8. Update docs si archi change

---

## 🎨 Philosophie Développement

- NO shortcuts : fix root cause
- NO silent failures : log tout clairement
- Atomic operations : prevent corruption
- Explicit conversions : no implicit coercion
- Clear error messages : actionable info
- Single responsibility : 1 change/commit
- Degrade gracefully : show partial data + log

---

**Dernière MAJ** : 2025-11-05
**Python** : 3.11+
**Architecture** : V2 Refonte (backend-first, REST API, server-side state)
**Documentation complète** : Voir REFONTE_SPECS.md, REFONTE_PLAN.md (ne pas charger en contexte)
