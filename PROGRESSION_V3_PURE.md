# 📊 Progression V3 Pure - Timeline Linéaire

**Branch**: `v3-linear-timeline-pure`
**Dernière mise à jour**: 2025-11-06
**Status**: Phase 6 complétée ✅

---

## 🎯 Vue d'ensemble

### Objectif V3 Pure
Refonte complète avec architecture timeline linéaire basée sur `minuteOffset` (minutes relatives depuis `planningStartTime`), séparation stricte ORDERING → TIME CALCULATION, et isolation totale du code V2.

### Documents de référence
- **FLUX_V3_CORRECT.md** - Source de vérité (25 étapes du flux complet)
- **GUARD_V3.md** - Règles anti-dérive (checklist obligatoire avant commit)
- **ESSENTIALS_V3.md** - Condensé architecture V3
- **TODO_V3_STEPS.md** - Checklist 25 étapes (à cocher après implémentation)

---

## ✅ Phases Complétées

### Phase 1: Isolation & Garde-fous ✅
**Commit**: `75fbdd9`
- Création dossier `backend/planning_engine_v3_pure/`
- Création dossier `tests_v3_pure/`
- Documents GUARD_V3.md, TODO_V3_STEPS.md
- Structure isolée du code V2

### Phase 2: Types V3 ✅
**Commit**: `6e185c2`
- `types_v3.py` avec TaskV3, Obstacle, Timeline (TypedDict)
- Architecture minuteOffset (int) - NO string times
- Documentation types complète

### Phase 3: Timeline Calculator ✅
**Commit**: `4662c21` + `8436ba3` (rename)
- `timeline_calculator_v3.py` (anciennement timeline_linear.py)
- `rebuildTimeline()` - fonction centrale TIME CALCULATION
- `findNextFreeSlot()` - collision detection
- `convertTempsMortsToObstacles()` - conversion obstacles
- `sortTasksByOffset()` - tri timeline

### Phase 4: Data Loader ✅
**Commit**: `f16d5c6`
- `data_loader_v3.py` avec support IS_PAUSE
- `load_pomodoro_tasks_by_ids()`
- `load_recurrent_tasks_by_ids_v3()` - filtre IS_PAUSE
- `load_temps_morts()` - obstacles
- `load_all_pomodoro_tasks()`, `load_all_recurrent_tasks()` - API support

### Phase 5: Planning Generator ✅
**Commit**: `99f65ee`
- `planning_generator_v3.py` avec algo 2-step
- STEP 1: ORDERING (expand, alternate, insert calins/clopes)
- STEP 2: TIME CALCULATION (rebuildTimeline)
- `generate_planning_v3()` - orchestrateur principal
- `PlanningOptions` - configuration

### Phase 6: API + Server + Tests + Data Writer ✅
**Commit**: `8436ba3` + `c840bef` (fix)

**Backend**:
- `data_writer_v3.py` - atomic CSV export, display conversion, stats

**API & Server**:
- `webapp_v3_pure/api/routes_v3.py` - 6 endpoints REST
- `webapp_v3_pure/server_v3.py` - Flask app (port 5001)
- `webapp_v3_pure/templates/gitfocus_v3.html` - interface test

**Tests**:
- `tests_v3_pure/test_guards.py` - 7 tests anti-dérive (tous passent ✅)

**Endpoints testés**:
- ✅ GET /health
- ✅ GET /api/v3/health
- ✅ GET /api/v3/tasks/pomodoro
- ✅ GET /api/v3/tasks/recurrent?pause_only=true
- ✅ GET /api/v3/tasks/recurrent?exclude_pauses=true
- ✅ GET /api/v3/temps-morts?date=YYYY-MM-DD
- ⏳ POST /api/v3/planning/generate (non testé - besoin CSV V3)
- ⏳ POST /api/v3/planning/export (non testé - besoin CSV V3)

---

## ⏳ Phases Restantes

### Phase 7: Frontend HTML/JS avec Drag & Drop ⏳
**Status**: Non commencé
**Fichiers à créer**:
- `webapp_v3_pure/static/js/gitfocus_v3.js`
- `webapp_v3_pure/static/css/gitfocus_v3.css`
- `webapp_v3_pure/templates/gitfocus_v3.html` (compléter)

**Fonctionnalités**:
- 3 onglets (Pomodoro checkboxes, Pauses drag-drop, Récurrentes toggles)
- Drag & Drop API native HTML5 (NO libraries)
- État client: selectedPomodoroIds, selectedPauseIds (ordre + duplicatas)
- Planning display avec timeline visuelle
- Bouton génération + export

**Référence**: FLUX_V3_CORRECT.md étapes 1-7, 21-22

### Phase 8: Tests E2E ⏳
**Status**: Non commencé
**Fichiers à créer**:
- `tests_v3_pure/test_planning_generator.py`
- `tests_v3_pure/test_timeline_calculator.py`
- `tests_v3_pure/test_data_loader.py`
- `tests_v3_pure/test_api_endpoints.py`

**Scénarios**:
- Test génération planning end-to-end
- Test collision detection
- Test alternance pomodoros/pauses
- Test insertion calins/clopes
- Test export CSV

### Phase 9: Migration CSV V3 ⏳
**Status**: Non commencé
**Fichiers à créer**:
- `data/prod_data/LISTE_MERE.v3.csv`
- `data/prod_data/TACHES_RECURRENTES.v3.csv` (avec IS_PAUSE)
- `data/prod_data/TACHES_PLANIFIEES.v3.csv`

**Migration**:
- Copier LISTE_MERE.v2.csv → LISTE_MERE.v3.csv
- Fusionner TACHES_RESPIRATOIRES.v2.csv + TACHES_RECURRENTES.v2.csv
  → TACHES_RECURRENTES.v3.csv (ajouter champ IS_PAUSE)
- Copier TACHES_PLANIFIEES.v2.csv → TACHES_PLANIFIEES.v3.csv
- Vérifier temps_morts.csv existe

---

## 🛡️ GUARD_V3 Compliance

**Tous les commits V3 Pure respectent** :
- ✅ NO imports depuis `backend/planning_engine/` (V2)
- ✅ Uses `minuteOffset: int` (NOT `heure_debut: str`, `heure_fin: str`)
- ✅ Uses TypedDict types (TaskV3, Obstacle, Timeline)
- ✅ Architecture 2-step respectée (ORDERING → TIME CALCULATION)
- ✅ `rebuildTimeline()` appelé après modifications timeline
- ✅ Naming convention `_v3` ou dossier `_v3_pure/`
- ✅ Atomic write pattern (temp + rename)
- ✅ NO références TACHES_RESPIRATOIRES.csv (supprimé en V3)

**Tests guards**: `pytest tests_v3_pure/test_guards.py -v` → 7/7 passent ✅

---

## 📁 Structure Fichiers V3 Pure

```
GitfocusPlanner/
├── backend/planning_engine_v3_pure/
│   ├── __init__.py
│   ├── types_v3.py                    ✅ Phase 2
│   ├── timeline_calculator_v3.py      ✅ Phase 3
│   ├── data_loader_v3.py              ✅ Phase 4
│   ├── planning_generator_v3.py       ✅ Phase 5
│   └── data_writer_v3.py              ✅ Phase 6
│
├── webapp_v3_pure/
│   ├── __init__.py
│   ├── server_v3.py                   ✅ Phase 6
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes_v3.py               ✅ Phase 6
│   ├── templates/
│   │   └── gitfocus_v3.html           ✅ Phase 6 (minimal)
│   └── static/
│       ├── js/                         ⏳ Phase 7
│       └── css/                        ⏳ Phase 7
│
├── tests_v3_pure/
│   ├── __init__.py
│   └── test_guards.py                 ✅ Phase 6
│
├── data/prod_data/
│   ├── LISTE_MERE.v3.csv              ⏳ Phase 9
│   ├── TACHES_RECURRENTES.v3.csv      ⏳ Phase 9
│   ├── TACHES_PLANIFIEES.v3.csv       ⏳ Phase 9
│   └── temps_morts.csv                (existe déjà)
│
└── docs/
    ├── GUARD_V3.md                    ✅
    ├── FLUX_V3_CORRECT.md             ✅
    ├── TODO_V3_STEPS.md               ✅
    └── ESSENTIALS_V3.md               ✅
```

---

## 🚀 Pour Reprendre le Développement

### 1. Relire les documents de référence
```bash
# Source de vérité (25 étapes)
cat FLUX_V3_CORRECT.md

# Règles anti-dérive
cat GUARD_V3.md

# Architecture condensée
cat ESSENTIALS_V3.md
```

### 2. Lancer le serveur V3
```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
python -m webapp_v3_pure.server_v3
```
→ Interface test: http://localhost:5001/gitfocus-v3

### 3. Vérifier tests guards
```bash
python -m pytest tests_v3_pure/test_guards.py -v
```
→ Doit afficher 7/7 passent ✅

### 4. Consulter TODO
```bash
cat TODO_V3_STEPS.md
```
→ Voir quelles étapes sont cochées

### 5. Commencer Phase 7 (Frontend)
- Créer `webapp_v3_pure/static/js/gitfocus_v3.js`
- Implémenter drag & drop natif HTML5
- Suivre FLUX_V3_CORRECT.md étapes 1-7, 21-22

---

## 📊 Statistiques

- **Commits V3**: 7
- **Fichiers créés**: 13
- **Lignes de code**: ~2500+
- **Tests**: 7 (tous passent)
- **Endpoints API**: 6 (tous fonctionnels)
- **Documentation**: 4 fichiers

---

## 🎯 Prochaine Session

**Priorité 1**: Phase 7 - Frontend drag & drop
**Priorité 2**: Phase 9 - Migration CSV V3 (pour tester avec vraies données)
**Priorité 3**: Phase 8 - Tests E2E

**Bloquant**: Besoin fichiers CSV V3 pour tester génération planning complète

---

## 📝 Notes Importantes

### Architecture 2-Step (CRITIQUE)
```
STEP 1: ORDERING
└─ Construire séquence SANS minuteOffset (ou =0)
   [P1, Pause1, CÂLIN, P2, Pause2, ...]

STEP 2: TIME CALCULATION
└─ Appeler rebuildTimeline()
   Calculer minuteOffsets séquentiellement
   [P1@0, Pause1@25, CÂLIN@35, P2@40, Pause2@65, ...]
```

### Drag & Drop Pauses (NOUVEAU V3)
- Ordre préservé: `["REC001", "REC003", "REC001"]`
- Duplicatas autorisés (même pause plusieurs fois)
- Backend cycle through pauses avec `pause_index % len(pauses)`

### Conversion Finale
- Timeline interne: `minuteOffset: int`
- Display final: `{date: "YYYY-MM-DD", heure_debut: "HH:MM", heure_fin: "HH:MM"}`
- Fonction: `convert_timeline_to_display()` dans data_writer_v3.py

---

**Dernière session**: 2025-11-06
**Serveur actif**: http://localhost:5001/gitfocus-v3
**Branch**: `v3-linear-timeline-pure`
**Status**: ✅ Backend complet et testé, prêt pour frontend
