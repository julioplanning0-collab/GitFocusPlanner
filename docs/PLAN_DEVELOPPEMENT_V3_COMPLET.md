# PLAN DE DÉVELOPPEMENT COMPLET - GITFOCUS PLANNER V3

**Date**: 2025-11-05
**Objectif**: Développer l'application complète en une seule passe, sans erreurs
**Durée estimée**: 54 heures (13 phases)
**Méthode**: Plan → Revue → Corrections plan → Implémentation parfaite du premier coup

---

## TABLE DES MATIÈRES

1. [PHASE 0: Préparation et Vérifications](#phase-0-préparation-et-vérifications)
2. [PHASE 1: Structure de Fichiers](#phase-1-structure-de-fichiers)
3. [PHASE 2: Fichiers de Données CSV](#phase-2-fichiers-de-données-csv)
4. [PHASE 3: Fichiers de Configuration JSON](#phase-3-fichiers-de-configuration-json)
5. [PHASE 4: Backend - Utilitaires de Base](#phase-4-backend---utilitaires-de-base)
6. [PHASE 5: Backend - Chargement Données](#phase-5-backend---chargement-données)
7. [PHASE 6: Backend - Timeline Core](#phase-6-backend---timeline-core)
8. [PHASE 7: Backend - Générateur de Planning](#phase-7-backend---générateur-de-planning)
9. [PHASE 8: Backend - Export CSV](#phase-8-backend---export-csv)
10. [PHASE 9: API Flask - Routes](#phase-9-api-flask---routes)
11. [PHASE 10: Frontend - HTML Structure](#phase-10-frontend---html-structure)
12. [PHASE 11: Frontend - CSS Styling](#phase-11-frontend---css-styling)
13. [PHASE 12: Frontend - JavaScript Logic](#phase-12-frontend---javascript-logic)
14. [PHASE 13: Tests et Validation](#phase-13-tests-et-validation)

---

## PRINCIPES DIRECTEURS

### 1. Architecture Backend-First (100% logique côté Python)

**RÈGLE ABSOLUE**: Le frontend ne fait AUCUN calcul de planning, AUCUNE logique métier.

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (JS)                        │
│  - Affichage uniquement                                 │
│  - Drag & drop (ordre seulement)                        │
│  - Envoi de l'ordre au backend                          │
│  - Réception du planning calculé                        │
│  - Affichage du planning                                │
└─────────────────────────────────────────────────────────┘
                          ↓ POST /planning/generate
┌─────────────────────────────────────────────────────────┐
│                    BACKEND (Python)                     │
│  - Calcul de TOUT le planning                           │
│  - Timeline en minutes relatives                        │
│  - Gestion des collisions                               │
│  - Conversion en heures absolues                        │
│  - Retour JSON complet                                  │
└─────────────────────────────────────────────────────────┘
```

### 2. Système de Temps Relatif (Timeline Linéaire)

**TOUT** le système utilise des **minutes relatives** depuis `planningStartTime`:

```python
planningStartTime = "2025-11-05 14:25"  # Heure de départ (minute 0)

# Exemples de conversion
14:25 → minute 0
14:50 → minute 25 (Pomodoro de 25 min)
14:55 → minute 30 (+ pause de 5 min)
15:20 → minute 55 (+ Pomodoro de 25 min)
```

**Conversion uniquement pour l'affichage final**.

### 3. Architecture en 2 Étapes (ORDERING → TIME CALCULATION)

```
ÉTAPE 1: ORDERING (Construction de la séquence)
├─ Utilisateur sélectionne tâches de travail
├─ Utilisateur sélectionne pauses (drag & drop pour ordonner)
├─ Frontend envoie l'ORDRE au backend
└─ Backend construit la timeline: [Pomo1, Pause1, Pomo2, Pause2, ...]

ÉTAPE 2: TIME CALCULATION (Assignation des heures)
├─ Backend charge temps_morts.csv et tâches_planifiées.csv
├─ Backend calcule la timeline avec collisions
├─ Backend insère temps_morts et tâches_planifiées
├─ Backend convertit minutes relatives → heures absolues
└─ Backend retourne planning complet (JSON)
```

### 4. Format de Données Standard

**TOUT le backend** utilise `List[Dict]` (pas de classes, pas de Pydantic):

```python
# Exemple de tâche
{
    "id": "TASK001",
    "name": "Révision mathématiques",
    "duration": 75,  # minutes
    "category": "Études",
    "priority": 1
}

# Exemple de slot de planning
{
    "type": "pomodoro",
    "task_id": "TASK001",
    "task_name": "Révision mathématiques",
    "minute_offset": 0,  # Relatif à planningStartTime
    "duration": 25,
    "heure_debut": "14:25",  # Converti pour affichage
    "heure_fin": "14:50",
    "pomodoro_index": 1,
    "pomodoro_total": 3
}
```

### 5. Gestion des Collisions (Ordre de Priorité)

```
1. TEMPS MORT (priorité absolue)
   → Bloque tout, planning contourne

2. TÂCHE PLANIFIÉE (priorité secondaire)
   → Insérée à l'heure prévue si possible
   → Sinon, décalée au créneau libre le plus proche

3. POMODORO / PAUSE (priorité tertiaire)
   → S'insèrent dans les trous restants
```

### 6. Opérations Atomiques (Écritures CSV)

**TOUTES** les écritures CSV utilisent le pattern temp file + rename:

```python
def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]):
    temp_file = csv_path.with_suffix('.tmp')

    # Écriture dans fichier temporaire
    with open(temp_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    # Renommage atomique (garanti par l'OS)
    temp_file.replace(csv_path)
```

---

## PHASE 0: PRÉPARATION ET VÉRIFICATIONS

**Durée**: 30 minutes
**Objectif**: Vérifier l'environnement et préparer les outils

### Étape 0.1: Vérifier l'environnement Python

```bash
# Vérifier version Python (minimum 3.11)
python --version

# Vérifier l'environnement virtuel existe
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
.\webapp\venv\Scripts\activate
```

**Checkpoint**: `python --version` affiche 3.11 ou supérieur

### Étape 0.2: Vérifier les dépendances Flask

```bash
# Vérifier Flask installé
python -c "import flask; print(flask.__version__)"

# Si manquant, installer
pip install flask
```

**Checkpoint**: Commande affiche version Flask (2.x ou supérieur)

### Étape 0.3: Arrêter tous les serveurs en cours

```bash
# Windows
scripts\stop.bat

# Ou manuellement
taskkill /F /IM python.exe
```

**Checkpoint**: `netstat -ano | findstr :5000` ne retourne rien

### Étape 0.4: Vérifier le répertoire prod_data existe

```bash
cd C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data
dir
```

**Checkpoint**: Le répertoire existe et contient des fichiers CSV

### Étape 0.5: Créer une sauvegarde complète

```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner

# Créer backup avec timestamp
mkdir backups\backup_2025-11-05_pre-v3
xcopy /E /I . backups\backup_2025-11-05_pre-v3
```

**Checkpoint**: `backups\backup_2025-11-05_pre-v3` contient tous les fichiers

### Étape 0.6: Créer une branche Git dédiée

```bash
# Créer branche pour V3
git checkout -b refonte-v3

# Commit l'état actuel
git add -A
git commit -m "État initial avant refonte V3"
```

**Checkpoint**: `git branch` affiche `* refonte-v3`

---

## PHASE 1: STRUCTURE DE FICHIERS

**Durée**: 1 heure
**Objectif**: Créer toute la structure de répertoires et fichiers vides

### Étape 1.1: Créer l'arborescence backend

```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner

# Créer répertoires backend
mkdir backend\planning_engine_v3
type nul > backend\__init__.py
type nul > backend\planning_engine_v3\__init__.py
```

**Fichiers à créer**:
```
backend/
├── __init__.py
└── planning_engine_v3/
    ├── __init__.py
    ├── utils.py              # Utilitaires (conversions, validations)
    ├── data_loader.py        # Chargement CSV
    ├── data_writer.py        # Écriture CSV (atomique)
    ├── timeline_builder.py   # Construction timeline (ORDERING)
    ├── timeline_calculator.py # Calcul temps (TIME CALCULATION)
    ├── collision_manager.py  # Gestion collisions
    └── planning_generator.py # Orchestrateur principal
```

**Commandes**:
```bash
cd backend\planning_engine_v3
type nul > utils.py
type nul > data_loader.py
type nul > data_writer.py
type nul > timeline_builder.py
type nul > timeline_calculator.py
type nul > collision_manager.py
type nul > planning_generator.py
```

**Checkpoint**: `dir backend\planning_engine_v3` affiche 8 fichiers

### Étape 1.2: Créer l'arborescence webapp

```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner

# Créer répertoires webapp V3
mkdir webapp\api_v3
mkdir webapp\templates_v3
mkdir webapp\static\css_v3
mkdir webapp\static\js_v3
```

**Fichiers à créer**:
```
webapp/
├── server_v3.py              # Serveur Flask V3
├── api_v3/
│   ├── __init__.py
│   └── routes_v3.py          # Routes API V3
├── templates_v3/
│   └── planner_v3.html       # Interface V3
├── static/
│   ├── css_v3/
│   │   └── planner_v3.css
│   └── js_v3/
│       └── planner_v3.js
```

**Commandes**:
```bash
type nul > webapp\server_v3.py
type nul > webapp\api_v3\__init__.py
type nul > webapp\api_v3\routes_v3.py
type nul > webapp\templates_v3\planner_v3.html
type nul > webapp\static\css_v3\planner_v3.css
type nul > webapp\static\js_v3\planner_v3.js
```

**Checkpoint**: Tous les fichiers existent

### Étape 1.3: Créer répertoire de tests

```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner

# Créer répertoires tests
mkdir tests_v3
type nul > tests_v3\__init__.py
```

**Fichiers à créer**:
```
tests_v3/
├── __init__.py
├── test_utils.py
├── test_data_loader.py
├── test_timeline_builder.py
├── test_timeline_calculator.py
├── test_collision_manager.py
├── test_planning_generator.py
└── test_api_routes.py
```

**Commandes**:
```bash
cd tests_v3
type nul > test_utils.py
type nul > test_data_loader.py
type nul > test_timeline_builder.py
type nul > test_timeline_calculator.py
type nul > test_collision_manager.py
type nul > test_planning_generator.py
type nul > test_api_routes.py
```

**Checkpoint**: `dir tests_v3` affiche 8 fichiers

### Étape 1.4: Créer répertoire de données de test

```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner

# Créer répertoire data de test
mkdir data_test_v3
```

**Fichiers à créer** (exemples avec peu de données pour tests rapides):
```
data_test_v3/
├── LISTE_MERE.v2.csv
├── TACHES_RECURRENTES.v2.csv
├── temps_morts.csv
├── TACHES_PLANIFIEES.v2.csv
├── categories.csv
├── planned.csv (vide au départ)
└── pinned_pauses.json
```

**Checkpoint**: Répertoire `data_test_v3` existe (fichiers créés en Phase 2)

---

## PHASE 2: FICHIERS DE DONNÉES CSV

**Durée**: 2 heures
**Objectif**: Créer tous les fichiers CSV avec structure exacte et données de test

### Étape 2.1: Créer LISTE_MERE.v2.csv (tâches de travail)

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\LISTE_MERE.v2.csv`

**Structure**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
```

**Colonnes détaillées**:
- `ID`: Identifiant unique (format `TASK001`, `TASK002`...)
- `NAME`: Nom de la tâche (50 caractères max)
- `DESCRIPTION`: Description longue (optionnel)
- `CATEGORY`: Catégorie principale (ex: "Études", "Travail")
- `SUB_CATEGORY`: Sous-catégorie (ex: "Mathématiques", "Programmation")
- `DURATION_MIN`: Durée totale en minutes
- `REMAINING_MIN`: Durée restante en minutes (initialement = DURATION_MIN)
- `PRIORITY`: 1 (Haute), 2 (Moyenne), 3 (Basse)
- `TAGS`: Tags séparés par virgules (optionnel)
- `KEYWORDS`: Mots-clés pour recherche (optionnel)
- `DEPENDENCIES`: IDs de tâches dépendantes (optionnel)
- `NOTES`: Notes libres (optionnel)
- `DEADLINE`: Date limite format `DD.MM.YY` (optionnel)
- `FIXED_START`: Heure de démarrage fixe `HH:MM` (optionnel)
- `PLANNED_START`: Date+heure planifiée `DD.MM.YY HH:MM` (optionnel)
- `STATUS`: `TODO`, `IN_PROGRESS`, `DONE`, `CANCELLED`

**Exemple de données de test** (5 tâches):
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
"TASK001";"Révision mathématiques";"Réviser chapitres 1-3";"Études";"Mathématiques";"75";"75";"1";"urgent,examen";"algèbre,équations";"";"Examen vendredi";"08.11.25";"";"";""TODO""
"TASK002";"Développement API";"Créer endpoints REST";"Travail";"Programmation";"100";"100";"1";"dev,backend";"python,flask";"";"Sprint actuel";"10.11.25";"";"";""TODO""
"TASK003";"Lecture chapitre 5";"Lire et résumer";"Études";"Littérature";"50";"50";"2";"lecture";"résumé";"";"";"15.11.25";"";"";""TODO""
"TASK004";"Réunion d'équipe";"Planning sprint";"Travail";"Management";"25";"25";"1";"réunion";"planning";"";"";"05.11.25";"14:30";"05.11.25 14:30";""TODO""
"TASK005";"Ranger bureau";"Trier documents";"Perso";"Organisation";"50";"50";"3";"ménage";"organisation";"";"";"";"";"";"TODO""
```

**Commande de création**:
```bash
# Créer le fichier avec encodage UTF-8
python -c "
import csv
from pathlib import Path

data_dir = Path('C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data')
csv_path = data_dir / 'LISTE_MERE.v2.csv'

fieldnames = ['ID', 'NAME', 'DESCRIPTION', 'CATEGORY', 'SUB_CATEGORY', 'DURATION_MIN',
              'REMAINING_MIN', 'PRIORITY', 'TAGS', 'KEYWORDS', 'DEPENDENCIES', 'NOTES',
              'DEADLINE', 'FIXED_START', 'PLANNED_START', 'STATUS']

rows = [
    {'ID': 'TASK001', 'NAME': 'Révision mathématiques', 'DESCRIPTION': 'Réviser chapitres 1-3',
     'CATEGORY': 'Études', 'SUB_CATEGORY': 'Mathématiques', 'DURATION_MIN': '75', 'REMAINING_MIN': '75',
     'PRIORITY': '1', 'TAGS': 'urgent,examen', 'KEYWORDS': 'algèbre,équations', 'DEPENDENCIES': '',
     'NOTES': 'Examen vendredi', 'DEADLINE': '08.11.25', 'FIXED_START': '', 'PLANNED_START': '', 'STATUS': 'TODO'},
    # ... (autres lignes)
]

with open(csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows(rows)

print(f'Créé: {csv_path}')
"
```

**Checkpoint**:
- Fichier existe
- Ouvrir dans Excel/LibreOffice: toutes les colonnes sont visibles
- 5 lignes de données + 1 ligne d'en-tête

### Étape 2.2: Créer TACHES_RECURRENTES.v2.csv (pauses et tâches récurrentes)

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\TACHES_RECURRENTES.v2.csv`

**Structure**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE";"IS_PAUSE"
```

**Colonnes détaillées**:
- `ID`: Identifiant unique (format `REC001`, `REC002`... ou `R_001`, `R_002`... pour pauses)
- `NAME`: Nom de la pause/tâche
- `DESCRIPTION`: Description (optionnel)
- `CATEGORY`: Catégorie
- `SUB_CATEGORY`: Sous-catégorie
- `DURATION_MIN`: Durée en minutes
- `RECURRENCE_TYPE`: `DAILY`, `WEEKLY`, `MONTHLY`, `MANUAL` (pour pauses)
- `RECURRENCE_INTERVAL`: Intervalle (ex: 1 pour quotidien, 7 pour hebdomadaire)
- `LAST_DONE_DATE`: Date dernière exécution `YYYY-MM-DD` (optionnel)
- `NEXT_DUE_DATE`: Prochaine date prévue `YYYY-MM-DD` (optionnel)
- `PRIORITY`: 1, 2, ou 3
- `STATUS`: `TODO`, `DONE`
- `IS_ACTIVE`: `1` (actif) ou `0` (inactif)
- `IS_PAUSE`: `1` (pause) ou `0` (tâche récurrente)

**Exemple de données de test** (10 pauses + 5 tâches récurrentes):
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE";"IS_PAUSE"
"R_001";"Pause café";"Boire un café";"Pause";"Boisson";"5";"MANUAL";"0";"";"";""2";"TODO";"1";"1"
"R_002";"Méditation";"5 min de méditation";"Pause";"Bien-être";"5";"MANUAL";"0";"";"";""1";"TODO";"1";"1"
"R_003";"Étirements";"Exercices d'étirement";"Pause";"Sport";"10";"MANUAL";"0";"";"";""2";"TODO";"1";"1"
"R_004";"Pause déjeuner";"Repas de midi";"Pause";"Repas";"60";"MANUAL";"0";"";"";""1";"TODO";"1";"1"
"R_005";"Marche extérieur";"10 min de marche";"Pause";"Sport";"10";"MANUAL";"0";"";"";""2";"TODO";"1";"1"
"R_006";"Pause thé";"Boire un thé";"Pause";"Boisson";"5";"MANUAL";"0";"";"";""3";"TODO";"1";"1"
"R_007";"Exercices respiration";"Respiration profonde";"Pause";"Bien-être";"5";"MANUAL";"0";"";"";""1";"TODO";"1";"1"
"R_008";"Pause goûter";"Collation";"Pause";"Repas";"15";"MANUAL";"0";"";"";""2";"TODO";"1";"1"
"R_009";"Rangement bureau";"Ranger 5 min";"Pause";"Organisation";"5";"MANUAL";"0";"";"";""3";"TODO";"1";"1"
"R_010";"Pause water";"Boire de l'eau";"Pause";"Boisson";"3";"MANUAL";"0";"";"";""3";"TODO";"1";"1"
"REC001";"Arrosage plantes";"Arroser toutes les plantes";"Maison";"Jardinage";"10";"DAILY";"2";"2025-11-04";"2025-11-06";"2";"TODO";"1";"0"
"REC002";"Nettoyage cuisine";"Nettoyer surfaces";"Maison";"Ménage";"20";"DAILY";"1";"2025-11-04";"2025-11-05";"2";"TODO";"1";"0"
"REC003";"Sortir poubelles";"Descendre poubelles";"Maison";"Ménage";"5";"WEEKLY";"7";"2025-11-01";"2025-11-08";"2";"TODO";"1";"0"
"REC004";"Aspirateur salon";"Passer l'aspirateur";"Maison";"Ménage";"25";"WEEKLY";"7";"2025-11-03";"2025-11-10";"2";"TODO";"0";"0"
"REC005";"Lessive";"Lancer une machine";"Maison";"Linge";"15";"WEEKLY";"3";"2025-11-03";"2025-11-06";"2";"TODO";"1";"0"
```

**Checkpoint**:
- Fichier existe avec 16 lignes (1 en-tête + 10 pauses + 5 récurrentes)
- Colonne `IS_PAUSE` permet de distinguer pauses (1) des tâches récurrentes (0)

### Étape 2.3: Créer temps_morts.csv (plages horaires bloquées)

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\temps_morts.csv`

**Structure**:
```csv
"DATE";"HEURE_DEBUT";"HEURE_FIN";"TITRE"
```

**Colonnes détaillées**:
- `DATE`: Date au format ISO `YYYY-MM-DD`
- `HEURE_DEBUT`: Heure de début `HH:MM` (24h)
- `HEURE_FIN`: Heure de fin `HH:MM` (24h)
- `TITRE`: Nom du temps mort

**Exemple de données de test** (3 temps morts pour aujourd'hui):
```csv
"DATE";"HEURE_DEBUT";"HEURE_FIN";"TITRE"
"2025-11-05";"12:00";"13:30";"Déjeuner"
"2025-11-05";"17:00";"18:00";"Rendez-vous médecin"
"2025-11-05";"20:00";"21:00";"Cours de sport"
```

**Checkpoint**: Fichier existe avec 4 lignes (1 en-tête + 3 temps morts)

### Étape 2.4: Créer TACHES_PLANIFIEES.v2.csv (tâches avec date/heure fixe)

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\TACHES_PLANIFIEES.v2.csv`

**Structure**: Identique à LISTE_MERE.v2.csv, mais filtrée sur les tâches ayant `PLANNED_START` rempli.

**Note**: Dans V3, on utilise directement LISTE_MERE.v2.csv et on filtre par `PLANNED_START != ""`. Ce fichier séparé n'est plus nécessaire, mais on le garde pour compatibilité.

**Exemple**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
"TASK004";"Réunion d'équipe";"Planning sprint";"Travail";"Management";"25";"25";"1";"réunion";"planning";"";"";"05.11.25";"14:30";"05.11.25 14:30";"TODO"
```

**Checkpoint**: Fichier existe avec 2 lignes (1 en-tête + 1 tâche planifiée)

### Étape 2.5: Créer categories.csv (catégories centralisées)

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\categories.csv`

**Structure**:
```csv
"CATEGORY";"SUB_CATEGORY"
```

**Exemple de données de test** (15 combinaisons):
```csv
"CATEGORY";"SUB_CATEGORY"
"Études";"Mathématiques"
"Études";"Littérature"
"Études";"Sciences"
"Travail";"Programmation"
"Travail";"Management"
"Travail";"Documentation"
"Perso";"Organisation"
"Perso";"Sport"
"Perso";"Lecture"
"Pause";"Boisson"
"Pause";"Repas"
"Pause";"Sport"
"Pause";"Bien-être"
"Maison";"Ménage"
"Maison";"Jardinage"
```

**Checkpoint**: Fichier existe avec 16 lignes (1 en-tête + 15 catégories)

### Étape 2.6: Créer planned.csv vide (planning exporté)

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\planned.csv`

**Structure**:
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"TYPE";"TASK_ID";"POMODORO_INDEX";"POMODORO_TOTAL"
```

**Colonnes détaillées**:
- `ID`: ID unique du slot (généré automatiquement)
- `NAME`: Nom de la tâche
- `DATE`: Date `YYYY-MM-DD`
- `HEURE_DEBUT`: Heure de début `HH:MM`
- `HEURE_FIN`: Heure de fin `HH:MM`
- `DURATION_MIN`: Durée en minutes
- `TYPE`: `pomodoro`, `pause`, `temps_mort`, `planned`, `recurrent`
- `TASK_ID`: ID de la tâche source
- `POMODORO_INDEX`: Index du Pomodoro (ex: 1, 2, 3...)
- `POMODORO_TOTAL`: Total de Pomodoros pour cette tâche

**Fichier vide au départ** (seulement en-tête):
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"TYPE";"TASK_ID";"POMODORO_INDEX";"POMODORO_TOTAL"
```

**Checkpoint**: Fichier existe avec 1 ligne (en-tête seulement)

---

## PHASE 3: FICHIERS DE CONFIGURATION JSON

**Durée**: 30 minutes
**Objectif**: Créer fichiers JSON pour persistance de l'état

### Étape 3.1: Créer pinned_pauses.json

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\pinned_pauses.json`

**Structure**:
```json
{
  "pinned_pause_ids": []
}
```

**Explication**:
- `pinned_pause_ids`: Liste d'IDs de pauses épinglées (restent sélectionnées après rafraîchissement)
- Exemple: `["R_001", "R_002", "R_003"]`

**Commande de création**:
```bash
python -c "
import json
from pathlib import Path

data_dir = Path('C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data')
json_path = data_dir / 'pinned_pauses.json'

data = {'pinned_pause_ids': []}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Créé: {json_path}')
"
```

**Checkpoint**: Fichier existe avec structure JSON valide

### Étape 3.2: Créer planning_state.json

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\planning_state.json`

**Structure**:
```json
{
  "current_date": "",
  "planning_start_time": "",
  "selected_work_task_ids": [],
  "selected_pause_ids_ordered": []
}
```

**Explication**:
- `current_date`: Date actuelle du planning `YYYY-MM-DD`
- `planning_start_time`: Heure de départ `YYYY-MM-DD HH:MM`
- `selected_work_task_ids`: IDs des tâches de travail sélectionnées
- `selected_pause_ids_ordered`: IDs des pauses dans l'ordre drag & drop

**Exemple après utilisation**:
```json
{
  "current_date": "2025-11-05",
  "planning_start_time": "2025-11-05 14:25",
  "selected_work_task_ids": ["TASK001", "TASK002"],
  "selected_pause_ids_ordered": ["R_001", "R_002", "R_003", "R_004"]
}
```

**Commande de création**:
```bash
python -c "
import json
from pathlib import Path

data_dir = Path('C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data')
json_path = data_dir / 'planning_state.json'

data = {
    'current_date': '',
    'planning_start_time': '',
    'selected_work_task_ids': [],
    'selected_pause_ids_ordered': []
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Créé: {json_path}')
"
```

**Checkpoint**: Fichier existe avec structure JSON valide

### Étape 3.3: Créer clope_settings.json

**Emplacement**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\clope_settings.json`

**Structure**:
```json
{
  "enabled": false,
  "interval_minutes": 120
}
```

**Explication**:
- `enabled`: `true` si clopes activées, `false` sinon
- `interval_minutes`: Intervalle en minutes entre chaque clope

**Commande de création**:
```bash
python -c "
import json
from pathlib import Path

data_dir = Path('C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data')
json_path = data_dir / 'clope_settings.json'

data = {
    'enabled': False,
    'interval_minutes': 120
}

with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Créé: {json_path}')
"
```

**Checkpoint**: Fichier existe avec structure JSON valide

---

## PHASE 4: BACKEND - UTILITAIRES DE BASE

**Durée**: 2 heures
**Objectif**: Créer tous les utilitaires de conversion et validation

### Étape 4.1: Créer backend/planning_engine_v3/utils.py

**Fichier**: `backend/planning_engine_v3/utils.py`

**Contenu complet**:

```python
"""
Utilitaires pour GitFocus Planner V3
Conversions de temps, validations, helpers
"""

from datetime import datetime, timedelta
from typing import Optional
import re


# ============================================================================
# CONVERSIONS DE TEMPS (RELATIF ↔ ABSOLU)
# ============================================================================

def datetime_to_minutes(dt: datetime, reference: datetime) -> int:
    """
    Convertit une datetime absolue en minutes relatives.

    Args:
        dt: DateTime à convertir
        reference: DateTime de référence (minute 0)

    Returns:
        Nombre de minutes depuis reference

    Examples:
        >>> ref = datetime(2025, 11, 5, 14, 25)
        >>> dt = datetime(2025, 11, 5, 14, 50)
        >>> datetime_to_minutes(dt, ref)
        25
        >>> dt = datetime(2025, 11, 5, 13, 25)
        >>> datetime_to_minutes(dt, ref)
        -60
    """
    delta = dt - reference
    return int(delta.total_seconds() / 60)


def minutes_to_datetime(minutes: int, reference: datetime) -> datetime:
    """
    Convertit des minutes relatives en datetime absolue.

    Args:
        minutes: Minutes depuis reference
        reference: DateTime de référence (minute 0)

    Returns:
        DateTime absolue

    Examples:
        >>> ref = datetime(2025, 11, 5, 14, 25)
        >>> minutes_to_datetime(0, ref)
        datetime.datetime(2025, 11, 5, 14, 25)
        >>> minutes_to_datetime(25, ref)
        datetime.datetime(2025, 11, 5, 14, 50)
        >>> minutes_to_datetime(-60, ref)
        datetime.datetime(2025, 11, 5, 13, 25)
    """
    return reference + timedelta(minutes=minutes)


def time_to_minutes(time_str: str) -> int:
    """
    Convertit une heure HH:MM en minutes depuis minuit.

    Args:
        time_str: Heure au format "HH:MM"

    Returns:
        Nombre de minutes depuis 00:00

    Examples:
        >>> time_to_minutes("00:00")
        0
        >>> time_to_minutes("14:25")
        865
        >>> time_to_minutes("23:59")
        1439

    Raises:
        ValueError: Si format invalide
    """
    match = re.match(r'^(\d{2}):(\d{2})$', time_str)
    if not match:
        raise ValueError(f"Format d'heure invalide: {time_str} (attendu HH:MM)")

    hours, minutes = int(match.group(1)), int(match.group(2))

    if hours > 23 or minutes > 59:
        raise ValueError(f"Heure invalide: {time_str}")

    return hours * 60 + minutes


def minutes_to_time(minutes: int) -> str:
    """
    Convertit des minutes depuis minuit en heure HH:MM.

    Args:
        minutes: Minutes depuis 00:00

    Returns:
        Heure au format "HH:MM"

    Examples:
        >>> minutes_to_time(0)
        '00:00'
        >>> minutes_to_time(865)
        '14:25'
        >>> minutes_to_time(1439)
        '23:59'
        >>> minutes_to_time(1440)  # Minuit du jour suivant
        '00:00'
    """
    # Gérer les débordements (minutes > 1440)
    minutes = minutes % 1440

    hours = minutes // 60
    mins = minutes % 60

    return f"{hours:02d}:{mins:02d}"


# ============================================================================
# PARSING ET VALIDATION DE DATES
# ============================================================================

def parse_date_iso(date_str: str) -> datetime:
    """
    Parse une date au format ISO (YYYY-MM-DD).

    Args:
        date_str: Date au format "YYYY-MM-DD"

    Returns:
        DateTime (heure mise à 00:00)

    Raises:
        ValueError: Si format invalide

    Examples:
        >>> parse_date_iso("2025-11-05")
        datetime.datetime(2025, 11, 5, 0, 0)
    """
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError(f"Format de date invalide: {date_str} (attendu YYYY-MM-DD)")


def parse_date_user(date_str: str) -> datetime:
    """
    Parse une date au format utilisateur (DD.MM.YY).

    Args:
        date_str: Date au format "DD.MM.YY"

    Returns:
        DateTime (heure mise à 00:00)

    Raises:
        ValueError: Si format invalide

    Examples:
        >>> parse_date_user("05.11.25")
        datetime.datetime(2025, 11, 5, 0, 0)
    """
    try:
        return datetime.strptime(date_str, '%d.%m.%y')
    except ValueError:
        raise ValueError(f"Format de date invalide: {date_str} (attendu DD.MM.YY)")


def parse_datetime_user(datetime_str: str) -> datetime:
    """
    Parse une date+heure au format utilisateur (DD.MM.YY HH:MM).

    Args:
        datetime_str: DateTime au format "DD.MM.YY HH:MM"

    Returns:
        DateTime complète

    Raises:
        ValueError: Si format invalide

    Examples:
        >>> parse_datetime_user("05.11.25 14:30")
        datetime.datetime(2025, 11, 5, 14, 30)
    """
    try:
        return datetime.strptime(datetime_str, '%d.%m.%y %H:%M')
    except ValueError:
        raise ValueError(f"Format datetime invalide: {datetime_str} (attendu DD.MM.YY HH:MM)")


def format_date_iso(dt: datetime) -> str:
    """
    Formate une datetime en ISO (YYYY-MM-DD).

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 30)
        >>> format_date_iso(dt)
        '2025-11-05'
    """
    return dt.strftime('%Y-%m-%d')


def format_date_user(dt: datetime) -> str:
    """
    Formate une datetime en format utilisateur (DD.MM.YY).

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 30)
        >>> format_date_user(dt)
        '05.11.25'
    """
    return dt.strftime('%d.%m.%y')


def format_time(dt: datetime) -> str:
    """
    Formate une datetime en heure HH:MM.

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 30)
        >>> format_time(dt)
        '14:30'
    """
    return dt.strftime('%H:%M')


# ============================================================================
# ARRONDI DE TEMPS
# ============================================================================

def round_up_to_multiple(value: int, multiple: int) -> int:
    """
    Arrondit une valeur au multiple supérieur.

    Args:
        value: Valeur à arrondir
        multiple: Multiple cible

    Returns:
        Valeur arrondie au multiple supérieur

    Examples:
        >>> round_up_to_multiple(13, 5)
        15
        >>> round_up_to_multiple(15, 5)
        15
        >>> round_up_to_multiple(7, 15)
        15
    """
    if value % multiple == 0:
        return value
    return ((value // multiple) + 1) * multiple


def round_time_up(dt: datetime, minutes: int) -> datetime:
    """
    Arrondit une datetime au multiple de minutes supérieur.

    Args:
        dt: DateTime à arrondir
        minutes: Multiple de minutes (ex: 5, 15)

    Returns:
        DateTime arrondie

    Examples:
        >>> dt = datetime(2025, 11, 5, 14, 7)
        >>> round_time_up(dt, 5)
        datetime.datetime(2025, 11, 5, 14, 10)
        >>> dt = datetime(2025, 11, 5, 14, 25)
        >>> round_time_up(dt, 5)
        datetime.datetime(2025, 11, 5, 14, 25)
    """
    minute = dt.minute
    rounded_minute = round_up_to_multiple(minute, minutes)

    if rounded_minute >= 60:
        # Passage à l'heure suivante
        return dt.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        return dt.replace(minute=rounded_minute, second=0, microsecond=0)


# ============================================================================
# VALIDATION
# ============================================================================

def validate_time_range(start: str, end: str) -> bool:
    """
    Valide qu'une plage horaire est cohérente (fin > début).

    Args:
        start: Heure de début "HH:MM"
        end: Heure de fin "HH:MM"

    Returns:
        True si valide, False sinon

    Examples:
        >>> validate_time_range("14:00", "15:00")
        True
        >>> validate_time_range("15:00", "14:00")
        False
        >>> validate_time_range("14:00", "14:00")
        False
    """
    try:
        start_min = time_to_minutes(start)
        end_min = time_to_minutes(end)
        return end_min > start_min
    except ValueError:
        return False


def validate_priority(priority: int) -> bool:
    """
    Valide qu'une priorité est dans la plage autorisée (1-3).

    Examples:
        >>> validate_priority(1)
        True
        >>> validate_priority(4)
        False
    """
    return priority in [1, 2, 3]


# ============================================================================
# HELPERS
# ============================================================================

def clean_csv_field(field: str) -> str:
    """
    Nettoie un champ CSV (supprime guillemets, espaces superflus).

    Examples:
        >>> clean_csv_field('"  Tâche  "')
        'Tâche'
        >>> clean_csv_field('Normal')
        'Normal'
    """
    return field.strip().strip('"').strip()


def safe_int(value: str, default: int = 0) -> int:
    """
    Convertit en int, retourne default si échec.

    Examples:
        >>> safe_int("42")
        42
        >>> safe_int("abc", 0)
        0
        >>> safe_int("", 10)
        10
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def generate_slot_id(task_type: str, index: int) -> str:
    """
    Génère un ID unique pour un slot de planning.

    Args:
        task_type: Type de tâche (pomodoro, pause, etc.)
        index: Index du slot

    Returns:
        ID au format "TYPE_INDEX"

    Examples:
        >>> generate_slot_id("pomodoro", 1)
        'POMODORO_1'
        >>> generate_slot_id("pause", 5)
        'PAUSE_5'
    """
    return f"{task_type.upper()}_{index}"
```

**Checkpoint**:
- Fichier créé avec 500+ lignes
- Toutes les fonctions documentées avec docstrings et exemples
- Imports corrects (datetime, typing, re)

### Étape 4.2: Tester utils.py

Créer `tests_v3/test_utils.py`:

```python
"""Tests pour utils.py"""

import pytest
from datetime import datetime
from backend.planning_engine_v3.utils import (
    datetime_to_minutes,
    minutes_to_datetime,
    time_to_minutes,
    minutes_to_time,
    round_up_to_multiple,
    round_time_up,
    validate_time_range,
    clean_csv_field,
    safe_int
)


def test_datetime_to_minutes():
    """Test conversion datetime → minutes relatives"""
    ref = datetime(2025, 11, 5, 14, 25)

    # Minute 0
    assert datetime_to_minutes(ref, ref) == 0

    # +25 minutes
    dt = datetime(2025, 11, 5, 14, 50)
    assert datetime_to_minutes(dt, ref) == 25

    # -60 minutes
    dt = datetime(2025, 11, 5, 13, 25)
    assert datetime_to_minutes(dt, ref) == -60


def test_minutes_to_datetime():
    """Test conversion minutes relatives → datetime"""
    ref = datetime(2025, 11, 5, 14, 25)

    # Minute 0
    assert minutes_to_datetime(0, ref) == ref

    # +25 minutes
    assert minutes_to_datetime(25, ref) == datetime(2025, 11, 5, 14, 50)

    # -60 minutes
    assert minutes_to_datetime(-60, ref) == datetime(2025, 11, 5, 13, 25)


def test_time_to_minutes():
    """Test conversion HH:MM → minutes depuis minuit"""
    assert time_to_minutes("00:00") == 0
    assert time_to_minutes("14:25") == 865
    assert time_to_minutes("23:59") == 1439

    # Format invalide
    with pytest.raises(ValueError):
        time_to_minutes("25:00")

    with pytest.raises(ValueError):
        time_to_minutes("14:60")


def test_minutes_to_time():
    """Test conversion minutes depuis minuit → HH:MM"""
    assert minutes_to_time(0) == "00:00"
    assert minutes_to_time(865) == "14:25"
    assert minutes_to_time(1439) == "23:59"

    # Débordement (minuit du jour suivant)
    assert minutes_to_time(1440) == "00:00"


def test_round_up_to_multiple():
    """Test arrondi au multiple supérieur"""
    assert round_up_to_multiple(13, 5) == 15
    assert round_up_to_multiple(15, 5) == 15
    assert round_up_to_multiple(7, 15) == 15
    assert round_up_to_multiple(0, 5) == 0


def test_round_time_up():
    """Test arrondi datetime"""
    dt = datetime(2025, 11, 5, 14, 7)
    assert round_time_up(dt, 5) == datetime(2025, 11, 5, 14, 10)

    dt = datetime(2025, 11, 5, 14, 25)
    assert round_time_up(dt, 5) == datetime(2025, 11, 5, 14, 25)

    dt = datetime(2025, 11, 5, 14, 58)
    assert round_time_up(dt, 5) == datetime(2025, 11, 5, 15, 0)


def test_validate_time_range():
    """Test validation plage horaire"""
    assert validate_time_range("14:00", "15:00") is True
    assert validate_time_range("15:00", "14:00") is False
    assert validate_time_range("14:00", "14:00") is False


def test_clean_csv_field():
    """Test nettoyage champ CSV"""
    assert clean_csv_field('"  Tâche  "') == "Tâche"
    assert clean_csv_field('Normal') == "Normal"
    assert clean_csv_field('""') == ""


def test_safe_int():
    """Test conversion int sécurisée"""
    assert safe_int("42") == 42
    assert safe_int("abc", 0) == 0
    assert safe_int("", 10) == 10
    assert safe_int(None, 5) == 5
```

**Commande de test**:
```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
python -m pytest tests_v3/test_utils.py -v
```

**Checkpoint**: Tous les tests passent (14/14)

---

## PHASE 5: BACKEND - CHARGEMENT DONNÉES

**Durée**: 3 heures
**Objectif**: Créer data_loader.py pour charger tous les fichiers CSV

### Étape 5.1: Créer backend/planning_engine_v3/data_loader.py

**Fichier**: `backend/planning_engine_v3/data_loader.py`

**Contenu complet** (tronqué pour lisibilité, voir fichier complet dans le projet):

```python
"""
Module de chargement des données CSV
Toutes les fonctions retournent List[Dict]
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional

from .utils import clean_csv_field, safe_int

logger = logging.getLogger(__name__)


# ============================================================================
# HELPER: LECTURE CSV GÉNÉRIQUE
# ============================================================================

def _read_csv(csv_path: Path, required_fields: Optional[List[str]] = None) -> List[Dict]:
    """
    Lit un fichier CSV et retourne une liste de dictionnaires.

    Args:
        csv_path: Chemin du fichier CSV
        required_fields: Liste des champs requis (optionnel)

    Returns:
        Liste de dictionnaires (une ligne = un dict)

    Gestion d'erreurs:
        - Fichier absent → retourne [] + log WARNING
        - Ligne invalide → skip ligne + log ERROR
        - Encodage erreur → réencode latin-1 → UTF-8
    """
    if not csv_path.exists():
        logger.warning(f"Fichier CSV absent: {csv_path}")
        return []

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = []

            for i, row in enumerate(reader, start=2):  # Ligne 2 = première data
                # Nettoyer tous les champs
                cleaned_row = {k: clean_csv_field(v) for k, v in row.items()}

                # Vérifier champs requis
                if required_fields:
                    missing = [f for f in required_fields if not cleaned_row.get(f)]
                    if missing:
                        logger.error(f"{csv_path.name} ligne {i}: Champs manquants {missing}")
                        continue

                rows.append(cleaned_row)

            logger.info(f"Chargé {len(rows)} lignes depuis {csv_path.name}")
            return rows

    except UnicodeDecodeError:
        # Réencodage latin-1 → UTF-8
        logger.warning(f"Erreur encodage {csv_path.name}, réencodage en cours...")

        content = csv_path.read_text(encoding='latin-1')
        csv_path.write_text(content, encoding='utf-8')

        # Retry
        return _read_csv(csv_path, required_fields)

    except Exception as e:
        logger.error(f"Erreur lecture {csv_path.name}: {e}")
        return []


# ============================================================================
# CHARGEMENT TÂCHES DE TRAVAIL
# ============================================================================

def load_work_tasks(data_dir: Path) -> List[Dict]:
    """
    Charge les tâches de travail depuis LISTE_MERE.v2.csv.

    Returns:
        Liste de dicts avec clés:
            - id, name, description, category, sub_category
            - duration_min, remaining_min, priority
            - tags, keywords, dependencies, notes
            - deadline, fixed_start, planned_start, status

    Filtres appliqués:
        - Status != 'DONE' et != 'CANCELLED'
    """
    csv_path = data_dir / 'LISTE_MERE.v2.csv'
    required_fields = ['ID', 'NAME', 'DURATION_MIN']

    rows = _read_csv(csv_path, required_fields)

    tasks = []
    for row in rows:
        # Filtrer tâches terminées/annulées
        if row.get('STATUS') in ['DONE', 'CANCELLED']:
            continue

        task = {
            'id': row['ID'],
            'name': row['NAME'],
            'description': row.get('DESCRIPTION', ''),
            'category': row.get('CATEGORY', ''),
            'sub_category': row.get('SUB_CATEGORY', ''),
            'duration_min': safe_int(row.get('DURATION_MIN'), 0),
            'remaining_min': safe_int(row.get('REMAINING_MIN'), safe_int(row.get('DURATION_MIN'), 0)),
            'priority': safe_int(row.get('PRIORITY'), 3),
            'tags': row.get('TAGS', ''),
            'keywords': row.get('KEYWORDS', ''),
            'dependencies': row.get('DEPENDENCIES', ''),
            'notes': row.get('NOTES', ''),
            'deadline': row.get('DEADLINE', ''),
            'fixed_start': row.get('FIXED_START', ''),
            'planned_start': row.get('PLANNED_START', ''),
            'status': row.get('STATUS', 'TODO')
        }

        tasks.append(task)

    logger.info(f"Chargé {len(tasks)} tâches de travail")
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
        Liste de dicts avec clés:
            - id, name, description, category, sub_category
            - duration_min, is_active, is_pause

    Filtres appliqués:
        - IS_PAUSE = '1'
        - Si active_only=True: IS_ACTIVE = '1'
    """
    csv_path = data_dir / 'TACHES_RECURRENTES.v2.csv'
    required_fields = ['ID', 'NAME', 'DURATION_MIN', 'IS_PAUSE']

    rows = _read_csv(csv_path, required_fields)

    pauses = []
    for row in rows:
        # Filtrer: seulement les pauses
        if row.get('IS_PAUSE') != '1':
            continue

        # Filtrer: seulement actives si demandé
        if active_only and row.get('IS_ACTIVE') != '1':
            continue

        pause = {
            'id': row['ID'],
            'name': row['NAME'],
            'description': row.get('DESCRIPTION', ''),
            'category': row.get('CATEGORY', ''),
            'sub_category': row.get('SUB_CATEGORY', ''),
            'duration_min': safe_int(row.get('DURATION_MIN'), 5),
            'is_active': row.get('IS_ACTIVE') == '1',
            'is_pause': True
        }

        pauses.append(pause)

    logger.info(f"Chargé {len(pauses)} pauses" + (" (actives uniquement)" if active_only else ""))
    return pauses


# ============================================================================
# CHARGEMENT TÂCHES RÉCURRENTES
# ============================================================================

def load_recurrent_tasks(data_dir: Path, active_only: bool = False) -> List[Dict]:
    """
    Charge les tâches récurrentes depuis TACHES_RECURRENTES.v2.csv.

    Args:
        active_only: Si True, filtre sur IS_ACTIVE=1

    Returns:
        Liste de dicts avec clés:
            - id, name, description, category, sub_category
            - duration_min, recurrence_type, recurrence_interval
            - last_done_date, next_due_date, is_active

    Filtres appliqués:
        - IS_PAUSE = '0' (tâches récurrentes, pas pauses)
        - Si active_only=True: IS_ACTIVE = '1'
    """
    csv_path = data_dir / 'TACHES_RECURRENTES.v2.csv'
    required_fields = ['ID', 'NAME', 'DURATION_MIN', 'IS_PAUSE']

    rows = _read_csv(csv_path, required_fields)

    tasks = []
    for row in rows:
        # Filtrer: seulement les tâches récurrentes (pas pauses)
        if row.get('IS_PAUSE') == '1':
            continue

        # Filtrer: seulement actives si demandé
        if active_only and row.get('IS_ACTIVE') != '1':
            continue

        task = {
            'id': row['ID'],
            'name': row['NAME'],
            'description': row.get('DESCRIPTION', ''),
            'category': row.get('CATEGORY', ''),
            'sub_category': row.get('SUB_CATEGORY', ''),
            'duration_min': safe_int(row.get('DURATION_MIN'), 15),
            'recurrence_type': row.get('RECURRENCE_TYPE', 'DAILY'),
            'recurrence_interval': safe_int(row.get('RECURRENCE_INTERVAL'), 1),
            'last_done_date': row.get('LAST_DONE_DATE', ''),
            'next_due_date': row.get('NEXT_DUE_DATE', ''),
            'priority': safe_int(row.get('PRIORITY'), 2),
            'is_active': row.get('IS_ACTIVE') == '1',
            'is_pause': False
        }

        tasks.append(task)

    logger.info(f"Chargé {len(tasks)} tâches récurrentes" + (" (actives uniquement)" if active_only else ""))
    return tasks


# ============================================================================
# CHARGEMENT TEMPS MORTS
# ============================================================================

def load_temps_morts(data_dir: Path, date: str) -> List[Dict]:
    """
    Charge les temps morts pour une date donnée.

    Args:
        date: Date au format YYYY-MM-DD

    Returns:
        Liste de dicts avec clés:
            - date, heure_debut, heure_fin, titre

    Filtres appliqués:
        - DATE = date (filtre sur la date demandée)
    """
    csv_path = data_dir / 'temps_morts.csv'
    required_fields = ['DATE', 'HEURE_DEBUT', 'HEURE_FIN']

    rows = _read_csv(csv_path, required_fields)

    temps_morts = []
    for row in rows:
        # Filtrer sur la date
        if row.get('DATE') != date:
            continue

        tm = {
            'date': row['DATE'],
            'heure_debut': row['HEURE_DEBUT'],
            'heure_fin': row['HEURE_FIN'],
            'titre': row.get('TITRE', 'Temps mort')
        }

        temps_morts.append(tm)

    logger.info(f"Chargé {len(temps_morts)} temps morts pour {date}")
    return temps_morts


# ============================================================================
# CHARGEMENT TÂCHES PLANIFIÉES
# ============================================================================

def load_planned_tasks(data_dir: Path, date: Optional[str] = None) -> List[Dict]:
    """
    Charge les tâches planifiées (PLANNED_START rempli).

    Args:
        date: Date au format YYYY-MM-DD (optionnel, filtre par date)

    Returns:
        Liste de dicts avec clés:
            - Toutes les colonnes de LISTE_MERE.v2.csv

    Filtres appliqués:
        - PLANNED_START != ''
        - Si date fournie: filtre sur la date de PLANNED_START
    """
    # Charger toutes les tâches de travail
    all_tasks = load_work_tasks(data_dir)

    planned_tasks = []
    for task in all_tasks:
        # Filtrer: seulement si PLANNED_START rempli
        if not task.get('planned_start'):
            continue

        # Filtrer par date si demandé
        if date:
            # Extraire la date de PLANNED_START (format DD.MM.YY HH:MM)
            try:
                from .utils import parse_datetime_user, format_date_iso
                dt = parse_datetime_user(task['planned_start'])
                task_date = format_date_iso(dt)

                if task_date != date:
                    continue
            except ValueError:
                logger.error(f"Format PLANNED_START invalide pour {task['id']}: {task['planned_start']}")
                continue

        planned_tasks.append(task)

    logger.info(f"Chargé {len(planned_tasks)} tâches planifiées" + (f" pour {date}" if date else ""))
    return planned_tasks


# ============================================================================
# CHARGEMENT CATÉGORIES
# ============================================================================

def load_categories(data_dir: Path) -> Dict[str, List[str]]:
    """
    Charge les catégories depuis categories.csv.

    Returns:
        Dict avec structure:
            {
                "Études": ["Mathématiques", "Littérature"],
                "Travail": ["Programmation", "Management"],
                ...
            }
    """
    csv_path = data_dir / 'categories.csv'
    required_fields = ['CATEGORY', 'SUB_CATEGORY']

    rows = _read_csv(csv_path, required_fields)

    categories = {}
    for row in rows:
        cat = row['CATEGORY']
        subcat = row['SUB_CATEGORY']

        if cat not in categories:
            categories[cat] = []

        if subcat not in categories[cat]:
            categories[cat].append(subcat)

    logger.info(f"Chargé {len(categories)} catégories")
    return categories
```

**Checkpoint**:
- Fichier créé avec 400+ lignes
- Toutes les fonctions de chargement implémentées
- Gestion d'erreurs (fichier absent, ligne invalide, encodage)
- Logging détaillé

### Étape 5.2: Tester data_loader.py

Créer `tests_v3/test_data_loader.py`:

```python
"""Tests pour data_loader.py"""

import pytest
from pathlib import Path
from backend.planning_engine_v3.data_loader import (
    load_work_tasks,
    load_pauses,
    load_recurrent_tasks,
    load_temps_morts,
    load_planned_tasks,
    load_categories
)


@pytest.fixture
def data_dir():
    """Répertoire de données de test"""
    return Path('C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data')


def test_load_work_tasks(data_dir):
    """Test chargement tâches de travail"""
    tasks = load_work_tasks(data_dir)

    assert len(tasks) >= 3  # Au moins 3 tâches de test

    # Vérifier structure
    task = tasks[0]
    assert 'id' in task
    assert 'name' in task
    assert 'duration_min' in task
    assert isinstance(task['duration_min'], int)


def test_load_pauses(data_dir):
    """Test chargement pauses"""
    pauses = load_pauses(data_dir)

    assert len(pauses) >= 5  # Au moins 5 pauses de test

    # Vérifier structure
    pause = pauses[0]
    assert 'id' in pause
    assert 'name' in pause
    assert 'duration_min' in pause
    assert pause['is_pause'] is True


def test_load_pauses_active_only(data_dir):
    """Test chargement pauses actives uniquement"""
    pauses_all = load_pauses(data_dir, active_only=False)
    pauses_active = load_pauses(data_dir, active_only=True)

    assert len(pauses_active) <= len(pauses_all)


def test_load_recurrent_tasks(data_dir):
    """Test chargement tâches récurrentes"""
    tasks = load_recurrent_tasks(data_dir)

    assert len(tasks) >= 3  # Au moins 3 tâches récurrentes de test

    # Vérifier structure
    task = tasks[0]
    assert 'id' in task
    assert 'recurrence_type' in task
    assert task['is_pause'] is False


def test_load_temps_morts(data_dir):
    """Test chargement temps morts"""
    temps_morts = load_temps_morts(data_dir, "2025-11-05")

    assert len(temps_morts) >= 0  # Peut être vide si aucun temps mort

    if len(temps_morts) > 0:
        tm = temps_morts[0]
        assert 'date' in tm
        assert 'heure_debut' in tm
        assert 'heure_fin' in tm


def test_load_planned_tasks(data_dir):
    """Test chargement tâches planifiées"""
    tasks = load_planned_tasks(data_dir)

    # Peut être vide si aucune tâche planifiée
    assert len(tasks) >= 0

    # Toutes doivent avoir PLANNED_START rempli
    for task in tasks:
        assert task['planned_start'] != ''


def test_load_categories(data_dir):
    """Test chargement catégories"""
    categories = load_categories(data_dir)

    assert len(categories) >= 3  # Au moins 3 catégories

    # Vérifier structure
    assert isinstance(categories, dict)

    for cat, subcats in categories.items():
        assert isinstance(subcats, list)
        assert len(subcats) > 0
```

**Commande de test**:
```bash
python -m pytest tests_v3/test_data_loader.py -v
```

**Checkpoint**: Tous les tests passent

---

**FIN DE LA PHASE 5**

Les phases suivantes (6-13) suivront le même niveau de détail. Voulez-vous que je continue avec les phases suivantes, ou préférez-vous que j'ajuste quelque chose dans ce plan avant de continuer ?

**Résumé des phases restantes** (à détailler):

- **PHASE 6**: Backend - Timeline Core (timeline_builder.py, timeline_calculator.py)
- **PHASE 7**: Backend - Gestion Collisions (collision_manager.py)
- **PHASE 8**: Backend - Générateur Principal (planning_generator.py)
- **PHASE 9**: Backend - Export CSV (data_writer.py)
- **PHASE 10**: API Flask - Routes (routes_v3.py, server_v3.py)
- **PHASE 11**: Frontend - HTML (planner_v3.html)
- **PHASE 12**: Frontend - CSS (planner_v3.css)
- **PHASE 13**: Frontend - JavaScript (planner_v3.js)
- **PHASE 14**: Tests et Validation

**Durée totale estimée**: 54 heures (toutes phases confondues)
