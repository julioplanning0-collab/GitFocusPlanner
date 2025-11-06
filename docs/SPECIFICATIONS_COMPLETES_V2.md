# GITFOCUS PLANNER V2 - SPÉCIFICATIONS COMPLÈTES
**Application Web de Planning Pomodoro avec Apprentissage Intelligent**

**Version**: 2.0 Final
**Date**: 2025-10-30
**Auteur**: Spécifications basées sur conversation détaillée

---

## TABLE DES MATIÈRES

1. [Vue d'ensemble](#1-vue-densemble)
2. [Objectifs et Philosophie](#2-objectifs-et-philosophie)
3. [Architecture Système](#3-architecture-système)
4. [Modèle de Données Complet](#4-modèle-de-données-complet)
5. [Algorithme de Génération de Planning](#5-algorithme-de-génération-de-planning)
6. [Système d'Apprentissage Intelligent](#6-système-dapprentissage-intelligent)
7. [Interface Drag & Drop Interactif](#7-interface-drag--drop-interactif)
8. [API REST Complète](#8-api-rest-complète)
9. [Interface Utilisateur](#9-interface-utilisateur)
10. [Bonnes Pratiques & Anti-Patterns](#10-bonnes-pratiques--anti-patterns)
11. [Tests & Validation](#11-tests--validation)
12. [Déploiement](#12-déploiement)

---

## 1. VUE D'ENSEMBLE

### 1.1 But de l'Application

**GitFocus Planner V2** est une application web de planification Pomodoro qui :
- Génère automatiquement des plannings quotidiens alternant travail (Pomodoros) et pauses
- **Apprend** quelles tâches récurrentes l'utilisateur préfère à quelles heures
- Permet l'édition interactive du planning par drag & drop
- Exporte le planning en CSV pour consommation par une application Android

**Workflow principal** :
```
1. Utilisateur sélectionne tâches Pomodoro (travail)
2. Système propose automatiquement tâches récurrentes (pauses/hygiène) via scoring intelligent
3. Planning généré respecte alternance stricte + temps morts (calendrier Google)
4. Utilisateur édite visuellement par drag & drop si nécessaire
5. Export CSV → Application Android lit et exécute
6. Historique enregistré → Système apprend pour futurs plannings
```

### 1.2 Portée de l'Apprentissage

**IMPORTANT** : Le système d'apprentissage s'applique UNIQUEMENT aux tâches récurrentes.

| Type de tâche | Sélection | Apprentissage |
|--------------|-----------|---------------|
| **Tâches Pomodoro** | Manuelle (user choisit) | ❌ NON (décision utilisateur) |
| **Tâches Respiratoires** | Manuelle (user choisit) | ❌ NON (mais tri par popularité) |
| **Tâches Récurrentes** | **Automatique (scoring)** | ✅ OUI (historique placements) |
| **Tâches Planifiées** | Automatique (heure fixe) | ❌ NON (contrainte horaire) |

### 1.3 Glossaire

- **Pomodoro** : Créneau de travail de 25 minutes
- **Tâche Pomodoro** : Projet de travail (ex: "Installer machine virtuelle", "Révision maths")
- **Tâche Respiratoire** : Pause/respiration sélectionnée manuellement (ex: "Méditation 10 min")
- **Tâche Récurrente** : Tâche d'hygiène/entretien/soins qui revient régulièrement (ex: "Arroser plantes", "Nettoyer caisse chat")
- **Tâche Planifiée** : Tâche avec date/heure fixe (ex: "RDV médecin 14h30")
- **Temps mort** : Créneau occupé (importé de Google Calendar)
- **Scoring** : Calcul d'un score 0-100 pour chaque tâche récurrente basé sur historique
- **Placement** : Action de mettre une tâche dans le planning à une heure précise
- **Historique de placements** : Enregistrement cumulatif de quand/où chaque tâche a été planifiée

---

## 2. OBJECTIFS ET PHILOSOPHIE

### 2.1 Principes de Conception

#### Backend fait TOUT
**Règle absolue** : Le frontend est une interface de présentation UNIQUEMENT.

- ✅ Backend : Calcul planning complet, gestion état, logique métier, scoring
- ✅ Frontend : Affichage, événements utilisateur, drag & drop visuel
- ❌ Frontend : AUCUN calcul de logique métier

#### Pas de Rustines (No Patches)
**Philosophie** : Toujours traiter la cause racine, jamais le symptôme.

```python
# ❌ RUSTINE (interdit)
try:
    task_id = task['id']
except KeyError:
    task_id = "unknown"  # Masque le problème

# ✅ CORRECT
if 'id' not in task:
    raise ValueError(f"Task missing required field 'id': {task}")
```

#### Fail Fast avec Messages Clairs
Quand quelque chose ne va pas, ARRÊTER IMMÉDIATEMENT avec un message explicite.

```python
# ❌ MAUVAIS
if not csv_path.exists():
    return []  # Silencieux, utilisateur ne sait pas pourquoi

# ✅ CORRECT
if not csv_path.exists():
    raise FileNotFoundError(
        f"Required file not found: {csv_path}\n"
        f"Cannot generate planning without this file."
    )
```

#### Écriture Atomique OBLIGATOIRE
Toute écriture CSV DOIT utiliser temp file + rename pour éviter corruption.

```python
temp_file = csv_path.with_suffix('.tmp')
# Écrire dans temp_file...
temp_file.replace(csv_path)  # Atomique sur tous OS
```

### 2.2 Objectifs de Performance

- Génération planning : < 2 secondes (pour 50 créneaux)
- Chargement page : < 1 seconde
- Calcul scoring (80 tâches) : < 500 ms
- Drag & drop recalcul : < 300 ms (feedback instantané)

### 2.3 Contraintes Architecturales

1. **Pas de base de données** : Tout en CSV (simplicité, portabilité)
2. **Pas de framework frontend** : HTML/CSS/JS vanilla (légèreté)
3. **Pas de build step** : Pas de Webpack, pas de transpilation (simplicité)
4. **Python 3.11+** : Backend moderne
5. **Flask minimal** : Pas de Flask-SQLAlchemy, pas d'ORM

---

## 3. ARCHITECTURE SYSTÈME

### 3.1 Structure des Répertoires

```
GitfocusPlanner/
├── backend/
│   └── planning_engine/
│       ├── __init__.py
│       ├── data_loader.py         # Lecture CSV
│       ├── data_writer.py         # Écriture CSV (atomique)
│       ├── slot_calculator.py     # Calcul créneaux libres
│       ├── task_integrator.py     # Intégration tâches spéciales
│       ├── planning_generator.py  # Orchestrateur principal
│       ├── smart_scorer.py        # 🆕 Scoring intelligent
│       └── placement_logger.py    # 🆕 Enregistrement historique
│
├── webapp/
│   ├── server.py                  # Application Flask
│   ├── config.py                  # Configuration
│   ├── api/
│   │   └── routes_gitfocus_v2.py  # Blueprint API REST
│   ├── templates/
│   │   └── gitfocus_v2.html       # Interface web
│   └── static/
│       ├── css/
│       │   └── gitfocus_v2.css
│       └── js/
│           └── gitfocus_v2.js     # 🆕 Drag & drop + recalcul
│
├── prod_data/                     # Données production
│   ├── LISTE_MERE.v2.csv         # Tâches Pomodoro (travail)
│   ├── TACHES_RESPIRATOIRES.v2.csv  # Tâches respiratoires (pauses manuelles)
│   ├── TACHES_RECURRENTES.v2.csv    # 🎯 ~80 tâches hygiène/entretien
│   ├── TACHES_PLANIFIEES.v2.csv     # Tâches heure fixe
│   ├── temps_morts.csv              # Temps occupés (Google Cal)
│   ├── categories.csv               # Catégories centralisées
│   ├── done_v2.csv                  # Historique exécution (Android écrit)
│   ├── planned.csv                  # Planning exporté (généré)
│   └── planning_placements_history.csv  # 🆕 Historique apprentissage
│
├── scripts/
│   ├── start.bat                  # Démarrage Windows
│   ├── stop.bat                   # Arrêt Windows
│   └── restart.bat                # Redémarrage
│
├── tests/
│   ├── test_smart_scorer.py       # 🆕 Tests scoring
│   ├── test_data_loader.py
│   ├── test_planning_generator.py
│   └── ...
│
├── CLAUDE.md                      # Instructions développement
├── SPECIFICATIONS_COMPLETES_V2.md # 🆕 Ce document
└── README.md
```

### 3.2 Flux de Données

```
╔════════════════════════════════════════════════════════════╗
║                    GÉNÉRATION PLANNING                      ║
╚════════════════════════════════════════════════════════════╝

[USER] Sélectionne 3 tâches Pomodoro
   ↓
[FRONTEND] POST /api/v2/gitfocus/planning/generate-auto
   {
     "date": "2025-10-30",
     "pomodoro_task_ids": ["1", "2", "3"],
     "max_recurrent_tasks": 10
   }
   ↓
[BACKEND] data_loader.py
   ├─ load_pomodoro_tasks("1", "2", "3")
   ├─ load_recurrent_tasks(active_only=True)  → 80 tâches
   ├─ load_planning_history()  → Historique apprentissage
   ├─ load_done_history()  → Dernières exécutions
   └─ load_temps_morts(date)  → Créneaux occupés
   ↓
[BACKEND] smart_scorer.py  🆕
   Pour chaque tâche récurrente (80 tâches):
      score = calculate_task_score(task, date, planning_history, done_history)
   Trier par score décroissant
   Sélectionner top 10
   ↓
[BACKEND] planning_generator.py
   1. Calculer créneaux libres (slot_calculator.py)
   2. Alterner Pomodoro ↔ Tâche récurrente
   3. Intégrer tâches planifiées (task_integrator.py)
   4. Réparer alternance si nécessaire
   5. Calculer statistiques
   ↓
[BACKEND] Retourne JSON
   {
     "planning": [
       {"heure_debut": "08:00", "heure_fin": "08:25", "type": "pomodoro", ...},
       {"heure_debut": "08:25", "heure_fin": "08:35", "type": "recurrent", ...},
       ...
     ],
     "stats": {...},
     "recurrent_task_scores": [
       {"task_id": "REC001", "task_name": "Arroser plantes", "score": 87.5},
       ...
     ]
   }
   ↓
[FRONTEND] Affiche planning dans timeline
   Planning interactif avec drag & drop activé
   ↓
[USER] Édite visuellement (drag & drop)
   ↓
[FRONTEND] Recalcul local (applyConstraints)
   ├─ Enforce alternation
   ├─ Recalculer heures (skip temps_morts)
   └─ Ré-afficher
   ↓
[USER] Click "Exporter CSV"
   ↓
[FRONTEND] POST /api/v2/gitfocus/planning/export
   {
     "planning": [...]  // Planning édité
   }
   ↓
[BACKEND] data_writer.py
   ├─ export_planning() → planned.csv (écrase)
   └─ increment_export_count() → tâches respiratoires
   ↓
[BACKEND] placement_logger.py  🆕
   log_planning_placements()
   → planning_placements_history.csv (APPEND)
   ↓
[BACKEND] Retourne confirmation
   ↓
[ANDROID APP] Lit planned.csv et exécute
   Écrit done_v2.csv lors de complétion
```

---

## 4. MODÈLE DE DONNÉES COMPLET

### 4.1 TACHES_RECURRENTES.v2.csv (Source Principale Apprentissage)

**Localisation** : `prod_data/TACHES_RECURRENTES.v2.csv`

**Format** : Délimiteur `;`, encodage UTF-8, guillemets `"` pour tous les champs

**Colonnes** :
- `ID` : Format REC001, REC002... (obligatoire)
- `NAME` : Nom de la tâche (obligatoire)
- `DESCRIPTION` : Description (optionnel)
- `CATEGORY` : Catégorie (obligatoire)
- `SUB_CATEGORY` : Sous-catégorie (obligatoire)
- `DURATION_MIN` : Durée en minutes (obligatoire)
- `RECURRENCE_TYPE` : Type récurrence (daily, weekly, monthly)
- `RECURRENCE_INTERVAL` : Intervalle (1=quotidien, 7=hebdo, 30=mensuel)
- `LAST_DONE_DATE` : Date dernière exécution DD.MM.YY (optionnel, mis à jour par Android)
- `NEXT_DUE_DATE` : Prochaine échéance calculée (optionnel)
- `PRIORITY` : Priorité 1-3 (1=Haute, 2=Moyenne, 3=Basse)
- `STATUS` : État (available, completed, cancelled)
- `IS_ACTIVE` : Actif (1) ou inactif (0)

**Exemple** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE"
"REC001";"Arroser les plantes";"Arroser toutes les plantes d'intérieur";"Maison";"Jardinage";"15";"weekly";"7";"22.10.25";"29.10.25";"2";"available";"1"
"REC015";"Nettoyer caisse chat";"Nettoyer la litière du chat";"Animaux";"Hygiène";"10";"daily";"1";"29.10.25";"30.10.25";"1";"available";"1"
"REC023";"Ranger le bureau";"Ranger et nettoyer le bureau";"Maison";"Rangement";"20";"weekly";"7";"25.10.25";"01.11.25";"2";"available";"1"
```

**Règles** :
- Seules les tâches avec `IS_ACTIVE=1` sont considérées pour le planning
- Environ **80 tâches** au total (hygiène personnelle, entretien maison, soins animaux, courses, etc.)
- `LAST_DONE_DATE` est mis à jour par l'application Android après exécution

### 4.2 planning_placements_history.csv (🆕 Historique Apprentissage)

**Localisation** : `prod_data/planning_placements_history.csv`

**Format** : Délimiteur `;`, encodage UTF-8, mode **append-only** (JAMAIS supprimer)

**Colonnes** :
- `TASK_ID` : ID tâche récurrente (REC001, REC002...)
- `TASK_NAME` : Nom tâche (copie pour lisibilité)
- `DATE` : Date du planning (YYYY-MM-DD)
- `PLANNED_TIME` : Heure début planifiée (HH:MM)
- `DAY_OF_WEEK` : Jour semaine (0=Lundi, 6=Dimanche)
- `WEEK_TYPE` : Type semaine (extensible futur, vide pour l'instant)
- `MOOD` : Humeur (extensible futur, vide)
- `ENERGY` : Niveau énergie (extensible futur, vide)
- `WEATHER` : Météo (extensible futur, vide)
- `SEASON` : Saison (extensible futur, vide)
- `EXPORT_TIMESTAMP` : Timestamp ISO 8601 export

**Exemple** :
```csv
"TASK_ID";"TASK_NAME";"DATE";"PLANNED_TIME";"DAY_OF_WEEK";"WEEK_TYPE";"MOOD";"ENERGY";"WEATHER";"SEASON";"EXPORT_TIMESTAMP"
"REC001";"Arroser les plantes";"2025-10-29";"08:30";"1";"";"";"";"";"";"2025-10-29T09:15:23"
"REC015";"Nettoyer caisse chat";"2025-10-29";"11:00";"1";"";"";"";"";"";"2025-10-29T09:15:23"
"REC023";"Ranger le bureau";"2025-10-29";"17:30";"1";"";"";"";"";"";"2025-10-29T09:15:23"
"REC001";"Arroser les plantes";"2025-10-30";"08:45";"2";"";"";"";"";"";"2025-10-30T10:22:11"
"REC001";"Arroser les plantes";"2025-11-05";"08:20";"1";"";"";"";"";"";"2025-11-05T08:10:05"
```

**Règles CRITIQUES** :
- Mode **append-only** : Chaque export AJOUTE des lignes (JAMAIS supprimer)
- Une ligne par tâche récurrente présente dans le planning exporté
- Permet analyse : "REC001 planifiée 80% du temps entre 08:00-09:00 le lundi"
- Colonnes extensibles vides pour évolution future (MOOD, ENERGY, WEATHER)

### 4.3 Autres Fichiers CSV

#### done_v2.csv (Historique Exécution)
**Écrit par** : Application Android UNIQUEMENT (web app lit seulement)

**Colonnes** :
- `ID` : ID tâche complétée
- `NAME` : Nom tâche
- `DONE_AT` : Timestamp ISO 8601 complétion
- `DURATION_MIN` : Durée réelle
- `TYPE` : Type (pomodoro, respiration, recurrent, planned)

**Usage** : Le scoring lit ce fichier pour savoir quand une tâche récurrente a été faite pour la dernière fois.

#### LISTE_MERE.v2.csv (Tâches Pomodoro)
Tâches de travail (projets). Sélection manuelle par l'utilisateur. PAS dans système d'apprentissage.

#### TACHES_RESPIRATOIRES.v2.csv (Tâches Respiratoires)
Pauses/respirations. Sélection manuelle. PAS dans système d'apprentissage mais tri par popularité (EXPORT_COUNT).

#### temps_morts.csv (Créneaux Occupés)
**Format** :
- `DATE` : YYYY-MM-DD (ISO)
- `HEURE DEBUT` : HH:MM
- `HEURE FIN` : HH:MM
- `TITRE` : Description

Bloque complètement les créneaux (Google Calendar sync).

---

## 5. ALGORITHME DE GÉNÉRATION DE PLANNING

### 5.1 Vue d'Ensemble (9 Étapes)

```
ENTRÉES :
  - date : YYYY-MM-DD
  - pomodoro_ids : ["1", "2", "3"]  (sélection manuelle)
  - max_recurrent_tasks : 10

SORTIE :
  {
    "planning": [...],  // Liste créneaux
    "stats": {...},
    "recurrent_task_scores": [...]  // Transparence scoring
  }
```

### 5.2 Étapes Détaillées

#### ÉTAPE 0 : Validation Inputs
```python
def validate_inputs(date, pomodoro_ids):
    if not re.match(r'\d{4}-\d{2}-\d{2}', date):
        raise ValueError(f"Invalid date format: {date}. Expected YYYY-MM-DD")

    if not isinstance(pomodoro_ids, list):
        raise TypeError(f"pomodoro_ids must be list, got {type(pomodoro_ids)}")

    # Vérifier que les IDs existent dans LISTE_MERE.v2.csv
    all_tasks = load_pomodoro_tasks()
    existing_ids = {t['id'] for t in all_tasks}

    for pid in pomodoro_ids:
        if pid not in existing_ids:
            raise ValueError(f"Pomodoro task ID {pid} not found in LISTE_MERE.v2.csv")
```

#### ÉTAPE 1 : Chargement Données
```python
# Tâches Pomodoro sélectionnées
pomodoro_tasks = [t for t in load_pomodoro_tasks() if t['id'] in pomodoro_ids]

# TOUTES les tâches récurrentes actives (80 tâches)
all_recurrent = load_recurrent_tasks(active_only=True)

# Historiques pour scoring
planning_history = load_planning_history()  # planning_placements_history.csv
done_history = load_done_history()  # done_v2.csv

# Temps morts pour la date
temps_morts = load_temps_morts(date)

# Tâches planifiées (heure fixe) pour la date
planned_tasks = load_planned_tasks(date)
```

#### ÉTAPE 2 : Calcul Créneaux Libres
```python
free_slots = calculate_free_slots(date, temps_morts)

# Algorithme :
# 1. Jour = 06:00 → 23:00 (17 heures)
# 2. Si date = aujourd'hui ET heure actuelle > 06:00:
#      Commencer à heure actuelle arrondie au quart d'heure supérieur
# 3. Créer blocs de 30 minutes
# 4. Filtrer blocs qui chevauchent temps_morts
#      Chevauchement si: slot_start < tm_end AND slot_end > tm_start
# 5. Retourner liste créneaux libres
```

#### ÉTAPE 3 : Scoring Tâches Récurrentes (🆕)
```python
scored_tasks = []

for task in all_recurrent:  # 80 tâches
    score = calculate_task_score(
        task,
        target_date=date,
        planning_history=planning_history,
        done_history=done_history
    )
    scored_tasks.append({'task': task, 'score': score})

# Trier par score décroissant
scored_tasks.sort(key=lambda x: x['score'], reverse=True)

# Sélectionner top N (défaut 10)
selected_recurrent = [st['task'] for st in scored_tasks[:max_recurrent_tasks]]
```

**Voir Section 6 pour détails du scoring**

#### ÉTAPE 4 : Génération Planning de Base
```python
planning = []
current_slot_index = 0
recurrent_index = 0

# Trier Pomodoro par priorité
pomodoro_tasks.sort(key=lambda t: (t['priority'], t.get('deadline', '99.99.99')))

for pomo_task in pomodoro_tasks:
    nb_pomodoros = math.ceil(pomo_task['remaining_min'] / 25)

    for i in range(nb_pomodoros):
        if current_slot_index >= len(free_slots):
            break  # Plus de créneaux disponibles

        # Ajouter Pomodoro
        slot = free_slots[current_slot_index]
        planning.append({
            'id': generate_slot_id(),
            'heure_debut': slot['heure_debut'],
            'heure_fin': calculate_end_time(slot['heure_debut'], 25),
            'type': 'pomodoro',
            'task_id': pomo_task['id'],
            'task_name': pomo_task['name'],
            'category': pomo_task['category'],
            'sub_category': pomo_task['sub_category'],
            'pomodoro_num': i + 1,
            'total_pomodoros': nb_pomodoros,
            'duration_min': 25
        })
        current_slot_index += 1

        # Ajouter Tâche Récurrente (pause)
        if current_slot_index >= len(free_slots):
            break

        recurrent_task = selected_recurrent[recurrent_index % len(selected_recurrent)]
        recurrent_index += 1

        slot = free_slots[current_slot_index]
        planning.append({
            'id': generate_slot_id(),
            'heure_debut': slot['heure_debut'],
            'heure_fin': calculate_end_time(slot['heure_debut'], recurrent_task['duration_min']),
            'type': 'recurrent',
            'task_id': recurrent_task['id'],
            'task_name': recurrent_task['name'],
            'category': recurrent_task['category'],
            'sub_category': recurrent_task['sub_category'],
            'duration_min': recurrent_task['duration_min']
        })
        current_slot_index += 1
```

**🔑 Comportement de Planification Partielle (Multi-jours)**

Le `break` à la ligne 489 implémente intentionnellement la **planification partielle** :

1. **Remplissage jusqu'à épuisement** : Le système planifie autant de Pomodoros que possible dans les créneaux disponibles de la journée (de l'heure actuelle/06h00 jusqu'à minuit).

2. **Arrêt automatique** : Lorsque tous les créneaux libres sont remplis (`current_slot_index >= len(free_slots)`), l'algorithme s'arrête immédiatement, même si certaines tâches n'ont pas tous leurs Pomodoros planifiés.

3. **Report automatique** : Le champ `remaining_min` dans `LISTE_MERE.v2.csv` **n'est PAS modifié** lors de la génération du planning. Cela signifie que :
   - Si une tâche nécessite 3 Pomodoros (75 minutes) mais qu'un seul créneau est disponible aujourd'hui
   - 1 Pomodoro sera planifié aujourd'hui
   - Les 2 Pomodoros restants seront automatiquement disponibles pour le planning de demain
   - Le champ `remaining_min` restera à 75 minutes jusqu'à ce que la tâche soit marquée comme terminée dans `done_v2.csv`

4. **Exemple concret** :
   ```
   Situation :
   - Tâche A : 75 min (3 Pomodoros) - Priorité 1
   - Tâche B : 50 min (2 Pomodoros) - Priorité 2
   - Tâche C : 25 min (1 Pomodoro) - Priorité 3
   - Créneaux disponibles : 13 créneaux (6h30-10h40 + 18h15-minuit)
   - Alternance Pomodoro/Récurrent : 2 créneaux par Pomodoro

   Résultat :
   - Jour 1 : 6 créneaux utilisés = 3 Pomodoros planifiés
     → Tâche A (1/3), Tâche A (2/3), Tâche A (3/3)
   - Jour 2 : Tâche B et C seront disponibles pour planification
   ```

5. **Justification** : Ce comportement permet une gestion naturelle du travail sur plusieurs jours sans nécessiter de mise à jour manuelle des durées restantes. L'utilisateur génère un nouveau planning chaque jour, et le système réutilise automatiquement les tâches non terminées.

#### ÉTAPE 5 : Intégration Tâches Planifiées (Heure Fixe)
```python
# Pour chaque tâche avec PLANNED_START défini
for planned_task in planned_tasks:
    desired_time = parse_time(planned_task['planned_start'])  # "DD.MM.YY HH:MM"
    nb_pomodoros = math.ceil(planned_task['duration_min'] / 25)

    # Trouver les Pomodoros les plus proches de l'heure souhaitée
    available_pomodoros = [(i, s) for i, s in enumerate(planning) if s['type'] == 'pomodoro']

    # Calculer distance temporelle
    distances = []
    for idx, slot in available_pomodoros:
        slot_time = parse_time(f"{date} {slot['heure_debut']}")
        distance = abs((slot_time - desired_time).total_seconds())
        distances.append((distance, idx, slot))

    # Trier par distance croissante
    distances.sort(key=lambda x: x[0])

    # Remplacer les N plus proches
    for i, (dist, idx, old_slot) in enumerate(distances[:nb_pomodoros], start=1):
        planning[idx] = {
            'id': old_slot['id'],
            'heure_debut': old_slot['heure_debut'],
            'heure_fin': old_slot['heure_fin'],
            'type': 'planned',
            'task_id': planned_task['id'],
            'task_name': planned_task['name'],
            'category': planned_task['category'],
            'sub_category': planned_task['sub_category'],
            'pomodoro_num': i,
            'total_pomodoros': nb_pomodoros,
            'original_time': desired_time.strftime("%H:%M"),
            'is_rescheduled': (dist > 900)  # > 15 minutes
        }
```

#### ÉTAPE 6 : Vérification Cohérence (Alternance)
```python
def repair_consecutive_work_tasks(planning):
    """
    Garantit alternance stricte: Jamais 2 Pomodoros/planned/recurrent consécutifs.
    """
    modified = True

    while modified:
        modified = False

        for i in range(len(planning) - 1):
            current = planning[i]
            next_slot = planning[i + 1]

            # Vérifier si deux tâches de travail consécutives
            work_types = {'pomodoro', 'planned', 'recurrent'}
            if current['type'] in work_types and next_slot['type'] in work_types:
                # Chercher une pause disponible dans le planning
                pause_found = False

                # Chercher après
                for j in range(i + 2, len(planning)):
                    if planning[j]['type'] in {'respiration', 'pause'}:
                        pause = planning.pop(j)
                        planning.insert(i + 1, pause)
                        modified = True
                        pause_found = True
                        break

                if not pause_found:
                    # Créer pause par défaut
                    default_pause = {
                        'id': generate_slot_id(),
                        'type': 'pause',
                        'task_name': 'Pause',
                        'duration_min': 5,
                        'heure_debut': '',  # Sera recalculé
                        'heure_fin': ''
                    }
                    planning.insert(i + 1, default_pause)
                    modified = True

                if modified:
                    break  # Recommencer la boucle

    return planning
```

#### ÉTAPE 7 : Assignation Horaires Finales

**🆕 Nouvelle logique (2025-10-30)** : Le planning démarre à l'heure actuelle pour aujourd'hui

**Règles d'initialisation** :
- Si `date == aujourd'hui` : Démarre à l'heure actuelle arrondie au prochain quart d'heure (00, 15, 30, 45)
- Si `date == future` : Démarre à 06:00
- Borne maximale : 23:00

**Algorithme** :
1. Déterminer heure de démarrage selon la date
2. Pour chaque slot du planning :
   - Trouver le prochain créneau libre (évite temps_morts)
   - Assigner heure_debut et heure_fin
   - Avancer current_time
3. Arrêter si dépasse 23:00

**Arrondi au quart d'heure** :
```
Heure actuelle : 08:03 → Premier créneau : 08:15
Heure actuelle : 08:14 → Premier créneau : 08:15
Heure actuelle : 08:15 → Premier créneau : 08:30
Heure actuelle : 14:47 → Premier créneau : 15:00
```

**Cas limites** :
- Avant 06:00 → Force à 06:00
- Après 23:00 → Planning vide, message d'avertissement

**Fonction d'assistance : Trouver créneau libre**

Algorithme pour trouver le prochain créneau qui ne chevauche aucun temps_mort :
1. Partir de `start_time`
2. Calculer `end_time = start_time + duration`
3. Vérifier chevauchement avec chaque temps_mort :
   - Chevauchement si : `start_time < temps_mort.heure_fin` ET `end_time > temps_mort.heure_debut`
4. Si aucun chevauchement → Retourner `start_time`
5. Sinon → Avancer de 15 minutes et réessayer (étape 2)

#### ÉTAPE 8 : Calcul Statistiques

Calculer les métriques du planning généré :

**Compteurs de slots** :
- Total de slots
- Nombre de Pomodoros
- Nombre de tâches récurrentes
- Nombre de tâches planifiées
- Nombre de tâches respiratoires

**Durées** :
- Minutes de travail (Pomodoro + Planifiées)
- Minutes de pause (Récurrentes + Respiratoires)
- Total minutes

#### ÉTAPE 9 : Formatage Réponse

Retourner un dictionnaire JSON avec :

**Champs principaux** :
- `date` : Date cible (YYYY-MM-DD)
- `planning` : Liste complète des slots générés
- `stats` : Statistiques calculées (étape 8)
- `recurrent_task_scores` : Scores des tâches récurrentes sélectionnées (transparence)

**Format de `recurrent_task_scores`** :
- Liste de dictionnaires avec : `task_id`, `task_name`, `score`
- Limité aux N tâches sélectionnées (défaut: 10)
- Permet à l'utilisateur de comprendre pourquoi certaines tâches ont été choisies

---

## 6. SYSTÈME D'APPRENTISSAGE INTELLIGENT

### 6.1 Vue d'Ensemble

**Objectif** : Le système apprend quelles tâches récurrentes l'utilisateur préfère placer à quelles heures, et propose automatiquement les tâches les plus pertinentes.

**Mécanique** :
1. À chaque export CSV, le système enregistre dans `planning_placements_history.csv` :
   - Quelle tâche récurrente
   - À quelle date
   - À quelle heure
   - Quel jour de la semaine
2. Au fil du temps, historique s'accumule (append-only, JAMAIS supprimer)
3. Lors de génération planning, système calcule score 0-100 pour chaque tâche récurrente
4. Sélectionne automatiquement les N tâches avec les meilleurs scores

### 6.2 Algorithme de Scoring (4 Critères)

**Module** : `backend/planning_engine/smart_scorer.py`

**Signature** :
```python
def calculate_task_score(
    task: Dict,
    target_date: str,
    planning_history: List[Dict],
    done_history: List[Dict]
) -> float:
    """
    Retourne score 0.0 à 100.0
    """
```

#### Critère 1 : Récurrence DUE (50% du score - Poids maximal)

**Logique** : Les tâches en retard doivent être prioritaires.

```python
def calculate_recurrence_score(task, target_date, done_history):
    """
    Score basé sur urgence (retard).

    Calcul :
    - Jamais faite → 50.0 points (max)
    - En retard de X jours → min(50.0, X * 10.0) points
    - Faite aujourd'hui → 0.0 points
    - Pas encore due → 0.0 points
    """
    # Trouver dernière exécution
    last_done = None
    for record in done_history:
        if record['ID'] == task['id'] and record['TYPE'] == 'recurrent':
            done_date = datetime.fromisoformat(record['DONE_AT']).date()
            if last_done is None or done_date > last_done:
                last_done = done_date

    # Fallback sur LAST_DONE_DATE du CSV
    if task.get('last_done_date'):
        csv_date = datetime.strptime(task['last_done_date'], "%d.%m.%y").date()
        if last_done is None or csv_date > last_done:
            last_done = csv_date

    if last_done is None:
        return 50.0  # Jamais faite = très urgent

    # Calculer jours de retard
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    days_since = (target - last_done).days

    # Récurrence
    interval = task['recurrence_interval']
    rec_type = task['recurrence_type']

    if rec_type == 'daily':
        days_overdue = days_since - interval
    elif rec_type == 'weekly':
        days_overdue = days_since - (interval * 7)
    elif rec_type == 'monthly':
        days_overdue = days_since - (interval * 30)
    else:
        days_overdue = 0

    if days_overdue <= 0:
        return 0.0  # Pas encore due

    # Plus c'est en retard, plus c'est urgent (max 50 points)
    return min(50.0, days_overdue * 10.0)
```

**Exemples** :
- Tâche quotidienne faite il y a 3 jours → 2 jours de retard → 20 points
- Tâche hebdomadaire faite il y a 10 jours → 3 jours de retard → 30 points
- Tâche jamais faite → 50 points

#### Critère 2 : Fréquence par Jour de la Semaine (20% du score)

**Logique** : Si "Arroser plantes" est souvent planifiée le lundi, lui donner un score élevé le lundi.

```python
def calculate_day_frequency_score(task, target_date, planning_history):
    """
    Score basé sur fréquence de planification ce jour de la semaine.

    Calcul :
    - Compter occurrences ce jour de semaine / total occurrences tâche
    - Fréquence * 20 = score
    """
    target_day = datetime.strptime(target_date, "%Y-%m-%d").weekday()  # 0=Lundi, 6=Dimanche

    # Filtrer historique pour cette tâche
    task_history = [p for p in planning_history if p['TASK_ID'] == task['id']]

    if len(task_history) == 0:
        return 10.0  # Score neutre si pas d'historique

    # Compter occurrences ce jour de semaine
    count_this_day = sum(1 for p in task_history if int(p['DAY_OF_WEEK']) == target_day)

    frequency = count_this_day / len(task_history)

    return frequency * 20.0
```

**Exemples** :
- Tâche planifiée 8 fois sur 10 le lundi → 80% → 16 points
- Tâche planifiée 2 fois sur 10 le lundi → 20% → 4 points
- Tâche jamais planifiée le lundi → 0% → 0 points

#### Critère 3 : Fréquence Globale (15% du score)

**Logique** : Les tâches souvent utilisées sont probablement importantes.

```python
def calculate_global_frequency_score(task, planning_history):
    """
    Score basé sur nombre total de planifications.

    Calcul :
    - Normaliser par rapport à la tâche la plus fréquente
    - (count / max_count) * 15 = score
    """
    # Compter planifications de cette tâche
    task_count = len([p for p in planning_history if p['TASK_ID'] == task['id']])

    # Trouver tâche la plus fréquente
    all_task_ids = set(p['TASK_ID'] for p in planning_history)
    max_count = max(
        len([p for p in planning_history if p['TASK_ID'] == tid])
        for tid in all_task_ids
    ) if all_task_ids else 1

    if max_count == 0:
        return 7.5  # Score neutre

    frequency = task_count / max_count

    return frequency * 15.0
```

**Exemples** :
- Tâche planifiée 100 fois (max) → 100% → 15 points
- Tâche planifiée 50 fois (max=100) → 50% → 7.5 points
- Tâche jamais planifiée → 0% → 0 points

#### Critère 4 : Récence (15% du score)

**Logique** : Les tâches planifiées récemment sont probablement encore pertinentes.

```python
def calculate_recency_score(task, target_date, planning_history):
    """
    Score basé sur date de dernière planification.

    Calcul :
    - Moins de jours depuis dernière planification = score élevé
    - Décroissance linéaire de 15 points (hier) à 0 points (>30 jours)
    """
    task_history = [p for p in planning_history if p['TASK_ID'] == task['id']]

    if len(task_history) == 0:
        return 7.5  # Score neutre

    # Trouver dernière planification
    last_planning_date = max(
        datetime.strptime(p['DATE'], "%Y-%m-%d")
        for p in task_history
    )

    target_dt = datetime.strptime(target_date, "%Y-%m-%d")
    days_since = (target_dt - last_planning_date).days

    # Score décroissant
    if days_since <= 0:
        return 15.0  # Planifiée aujourd'hui ou dans le futur
    elif days_since >= 30:
        return 0.0  # Plus de 30 jours
    else:
        return 15.0 * (1 - days_since / 30.0)
```

**Exemples** :
- Tâche planifiée hier → 1 jour → 14.5 points
- Tâche planifiée il y a 15 jours → 50% → 7.5 points
- Tâche planifiée il y a 30 jours → 0% → 0 points

#### Score Final

```python
def calculate_task_score(task, target_date, planning_history, done_history):
    score = 0.0

    score += calculate_recurrence_score(task, target_date, done_history)  # 0-50
    score += calculate_day_frequency_score(task, target_date, planning_history)  # 0-20
    score += calculate_global_frequency_score(task, planning_history)  # 0-15
    score += calculate_recency_score(task, target_date, planning_history)  # 0-15

    return score  # 0.0 à 100.0
```

**Pondération Résumée** :
| Critère | Poids | Logique |
|---------|-------|---------|
| Récurrence DUE | 50% | Urgence (tâches en retard prioritaires) |
| Fréquence jour semaine | 20% | Habitude (lundi = arrosage plantes) |
| Fréquence globale | 15% | Popularité (tâches souvent utilisées) |
| Récence | 15% | Actualité (tâches récentes pertinentes) |

### 6.3 Évolution au Fil du Temps

#### Mois 1 (Historique Vide)
- `planning_placements_history.csv` vide ou presque
- Scoring basé principalement sur récurrence DUE (50 points max)
- Critères fréquence/récence retournent scores neutres
- **Résultat** : Tâches triées par urgence uniquement

#### Mois 2 (~60 exports)
- Historique commence à contenir des données
- Système détecte patterns simples : "Nettoyer caisse chat" souvent le matin
- Critère fréquence jour commence à influencer
- **Résultat** : Suggestions plus pertinentes

#### Mois 6 (~360 exports)
- Historique riche
- Patterns clairs : "Arroser plantes" → 80% le lundi matin 08:00-09:00
- Tous les critères contributent
- **Résultat** : Système propose automatiquement bonnes tâches aux bons moments

#### Année 1+ (>700 exports)
- Historique très riche
- Possibilité d'ajouter colonnes extensibles (MOOD, ENERGY, WEATHER)
- Machine Learning optionnel
- **Résultat** : Système très précis, adapté aux habitudes utilisateur

### 6.4 Colonnes Extensibles (Évolution Future)

Les colonnes `MOOD`, `ENERGY`, `WEATHER`, `SEASON` sont **vides pour l'instant** mais permettent évolution future.

**Scenario 1 : Humeur & Énergie**
```python
# Utilisateur peut indiquer humeur/énergie lors export
# Système apprend : Énergie faible → proposer tâches courtes/faciles

def calculate_context_score(task, context):
    score = 0.0

    if context.get('energy') == 'low':
        # Favoriser tâches courtes
        if task['duration_min'] <= 10:
            score += 5.0
        elif task['duration_min'] >= 30:
            score -= 5.0

    return score  # Score additionnel -10 à +10
```

**Scenario 2 : Météo**
```python
# Intégration API météo
# Système apprend : Pluie → proposer tâches intérieures

def calculate_weather_score(task, weather):
    if weather == 'rain':
        # Éviter tâches extérieures
        if 'exterieur' in task.get('tags', '').lower():
            return -10.0
    return 0.0
```

### 6.5 Enregistrement des Placements

**Module** : `backend/planning_engine/placement_logger.py`

**Appelé lors** : Export CSV (endpoint `/planning/export`)

```python
def log_planning_placements(planning: List[Dict], export_timestamp: str, data_dir: Path) -> None:
    """
    Enregistre placements tâches récurrentes dans historique.

    Args:
        planning: Planning complet (résultat generate_planning)
        export_timestamp: Timestamp ISO 8601
        data_dir: Chemin prod_data/
    """
    history_file = data_dir / 'planning_placements_history.csv'

    # Filtrer uniquement tâches récurrentes
    recurrent_slots = [slot for slot in planning if slot['type'] == 'recurrent']

    if len(recurrent_slots) == 0:
        return  # Rien à enregistrer

    # Créer lignes à ajouter
    rows_to_add = []
    for slot in recurrent_slots:
        date_obj = datetime.strptime(slot.get('date', ''), "%Y-%m-%d")

        row = {
            'TASK_ID': slot['task_id'],
            'TASK_NAME': slot['task_name'],
            'DATE': slot.get('date'),
            'PLANNED_TIME': slot['heure_debut'],
            'DAY_OF_WEEK': str(date_obj.weekday()),
            'WEEK_TYPE': '',  # Extensible futur
            'MOOD': '',
            'ENERGY': '',
            'WEATHER': '',
            'SEASON': '',
            'EXPORT_TIMESTAMP': export_timestamp
        }
        rows_to_add.append(row)

    # Ajouter en mode append (atomique)
    append_csv_rows(history_file, rows_to_add)

def append_csv_rows(csv_path: Path, rows: List[Dict]) -> None:
    """
    Ajoute lignes CSV en mode append.

    IMPORTANT : Mode append (pas de temp file ici car on n'écrase pas).
    """
    # Si fichier n'existe pas, créer avec header
    if not csv_path.exists():
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if rows:
                fieldnames = list(rows[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
                writer.writeheader()

    # Ajouter lignes
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        if rows:
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writerows(rows)
```

---

## 7. INTERFACE DRAG & DROP INTERACTIF

### 7.1 Vue d'Ensemble

**Objectif** : Permettre édition visuelle du planning par drag & drop avec recalcul automatique des contraintes.

**Bibliothèque** : [SortableJS](https://sortablejs.github.io/Sortable/) (CDN)

**Workflow** :
```
1. Planning généré → Affiché dans timeline
2. Utilisateur drag & drop un créneau
3. JavaScript recalcule localement :
   - Alternance stricte (insérer pauses si nécessaire)
   - Heures début/fin (continuité + skip temps_morts)
   - Validation bornes journée (06:00-23:00)
4. Ré-affichage immédiat
5. Export conserve l'ordre édité
```

### 7.2 Contraintes à Appliquer

#### Contrainte 1 : Alternance Stricte Pomodoro ↔ Pause

**Règle** : Jamais 2 tâches de travail consécutives, jamais 2 pauses consécutives.

**Types de travail** : `pomodoro`, `planned`, `recurrent`
**Types de pause** : `respiration`, `pause`

**Implémentation JavaScript** :
```javascript
function enforceAlternation(slots) {
    const result = [];

    for (let i = 0; i < slots.length; i++) {
        const current = slots[i];
        const previous = result[result.length - 1];

        if (previous) {
            const prevIsWork = ['pomodoro', 'planned', 'recurrent'].includes(previous.type);
            const currIsWork = ['pomodoro', 'planned', 'recurrent'].includes(current.type);

            // Deux tâches de travail consécutives → insérer pause
            if (prevIsWork && currIsWork) {
                const pauseSlot = getNextAvailablePause();
                result.push(pauseSlot);
            }

            // Deux pauses consécutives → insérer Pomodoro (rare mais possible)
            if (!prevIsWork && !currIsWork) {
                const pomodoroSlot = getNextAvailablePomodoro();
                result.push(pomodoroSlot);
            }
        }

        result.push(current);
    }

    return result;
}

// Pool de pauses disponibles (non utilisées dans le planning)
const state = {
    availablePauses: [],
    availablePomodoros: []
};

function getNextAvailablePause() {
    if (state.availablePauses.length > 0) {
        return state.availablePauses.shift();
    } else {
        // Créer pause par défaut
        return {
            id: generateId(),
            type: 'pause',
            task_id: 'default_pause',
            task_name: 'Pause',
            duration_min: 5,
            heure_debut': '',
            heure_fin': ''
        };
    }
}
```

#### Contrainte 2 : Skip Temps Morts

**Règle** : Les créneaux ne doivent jamais chevaucher des temps_morts.

**Implémentation** :
```javascript
function calculateTimesWithTempsMorts(slots, tempsMorts) {
    let currentTime = parseTime('06:00');

    for (let slot of slots) {
        const duration = slot.duration_min;

        // Trouver prochain créneau libre après currentTime
        currentTime = findNextFreeSlot(currentTime, duration, tempsMorts);

        slot.heure_debut = formatTime(currentTime);
        slot.heure_fin = formatTime(addMinutes(currentTime, duration));

        currentTime = addMinutes(currentTime, duration);
    }

    return slots;
}

function findNextFreeSlot(startTime, duration, tempsMorts) {
    let candidateStart = startTime;

    while (true) {
        const candidateEnd = addMinutes(candidateStart, duration);

        // Vérifier chevauchement avec temps_morts
        const overlaps = tempsMorts.some(tm => {
            const tmStart = parseTime(tm.heure_debut);
            const tmEnd = parseTime(tm.heure_fin);

            return candidateStart < tmEnd && candidateEnd > tmStart;
        });

        if (!overlaps) {
            return candidateStart;  // Créneau libre trouvé
        }

        // Avancer de 15 minutes et réessayer
        candidateStart = addMinutes(candidateStart, 15);

        // Sécurité : ne pas boucler indéfiniment
        if (candidateStart > parseTime('23:00')) {
            throw new Error('Impossible de placer créneau : journée complète');
        }
    }
}

// Utilitaires temps
function parseTime(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;  // Minutes depuis minuit
}

function formatTime(totalMinutes) {
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`;
}

function addMinutes(totalMinutes, minutesToAdd) {
    return totalMinutes + minutesToAdd;
}
```

#### Contrainte 3 : Continuité Temporelle

**Règle** : `heure_fin[i] = heure_debut[i+1]` (pas de trous)

**Implémentation** : Automatiquement garantie par recalcul séquentiel dans `calculateTimesWithTempsMorts`.

### 7.3 Initialisation SortableJS

**HTML** :
```html
<div id="planning-display" class="planning-display sortable-list">
    <!-- Créneaux générés dynamiquement -->
</div>
```

**JavaScript** :
```javascript
import Sortable from 'https://cdn.jsdelivr.net/npm/sortablejs@latest/Sortable.min.js';

const planningContainer = document.getElementById('planning-display');

const sortable = Sortable.create(planningContainer, {
    animation: 150,
    ghostClass: 'sortable-ghost',
    chosenClass: 'sortable-chosen',
    dragClass: 'sortable-drag',

    onEnd: function(evt) {
        console.log('Drag ended, recalculating constraints...');

        // Récupérer nouvel ordre
        const newOrder = Array.from(planningContainer.children).map(el => {
            const slotId = el.dataset.slotId;
            return state.currentPlanning.find(s => s.id === slotId);
        });

        // Appliquer contraintes
        const recalculated = applyConstraints(newOrder);

        // Mettre à jour état et ré-afficher
        state.currentPlanning = recalculated;
        renderPlanning(recalculated);
    }
});
```

**Fonction de recalcul** :
```javascript
function applyConstraints(slots) {
    console.log('Applying constraints...');

    // Étape 1 : Enforce alternation
    const alternated = enforceAlternation(slots);

    // Étape 2 : Recalculate times (skip temps_morts)
    const timed = calculateTimesWithTempsMorts(alternated, state.tempsMorts);

    // Étape 3 : Validate day bounds (06:00-23:00)
    const validated = validateDayBounds(timed);

    console.log(`Constraints applied: ${validated.length} slots`);

    return validated;
}

function validateDayBounds(slots) {
    const maxEndTime = parseTime('23:00');

    // Filtrer créneaux qui dépassent
    const valid = [];
    for (let slot of slots) {
        const endTime = parseTime(slot.heure_fin);
        if (endTime <= maxEndTime) {
            valid.push(slot);
        } else {
            console.warn(`Slot ${slot.id} exceeds day bounds, removed`);
        }
    }

    return valid;
}
```

### 7.4 CSS pour Drag & Drop

```css
.planning-slot {
    cursor: grab;
    transition: all 0.2s ease;
}

.planning-slot:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.sortable-ghost {
    opacity: 0.4;
    background: #f0f0f0;
}

.sortable-chosen {
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    transform: scale(1.05);
    cursor: grabbing;
}

.sortable-drag {
    cursor: grabbing;
}
```

### 7.5 Boutons d'Action

**Ajouter créneau** :
```html
<button onclick="addSlot('pause')">➕ Ajouter pause</button>
<button onclick="addSlot('pomodoro')">➕ Ajouter Pomodoro</button>
```

**Supprimer créneau** :
```html
<!-- Sur chaque slot -->
<button class="delete-slot-btn" onclick="deleteSlot('${slot.id}')">🗑️</button>
```

**Implémentation** :
```javascript
function addSlot(type) {
    const newSlot = type === 'pause'
        ? getNextAvailablePause()
        : getNextAvailablePomodoro();

    state.currentPlanning.push(newSlot);

    // Recalculer avec contraintes
    const recalculated = applyConstraints(state.currentPlanning);
    state.currentPlanning = recalculated;

    renderPlanning(recalculated);
}

function deleteSlot(slotId) {
    state.currentPlanning = state.currentPlanning.filter(s => s.id !== slotId);

    // Recalculer avec contraintes
    const recalculated = applyConstraints(state.currentPlanning);
    state.currentPlanning = recalculated;

    renderPlanning(recalculated);
}
```

---

## 8. API REST COMPLÈTE

### 8.1 Principes

- **RESTful** : Méthodes HTTP sémantiques
- **JSON** : Tous payloads JSON
- **Codes HTTP** : 200 OK, 201 Created, 400 Bad Request, 404 Not Found, 500 Internal Server Error
- **Prefix** : `/api/v2/gitfocus`

### 8.2 Endpoints Principaux

#### POST /api/v2/gitfocus/planning/generate-auto 🆕

**Description** : Génération automatique avec scoring intelligent tâches récurrentes

**Payload** :
```json
{
  "date": "2025-10-30",
  "pomodoro_task_ids": ["1", "2", "3"],
  "max_recurrent_tasks": 10
}
```

**Réponse 200** :
```json
{
  "date": "2025-10-30",
  "planning": [
    {
      "id": "slot_001",
      "heure_debut": "08:00",
      "heure_fin": "08:25",
      "type": "pomodoro",
      "task_id": "1",
      "task_name": "Installer machine virtuelle",
      "category": "Développement",
      "sub_category": "Planification",
      "pomodoro_num": 1,
      "total_pomodoros": 8,
      "duration_min": 25
    },
    {
      "id": "slot_002",
      "heure_debut": "08:25",
      "heure_fin": "08:40",
      "type": "recurrent",
      "task_id": "REC001",
      "task_name": "Arroser les plantes",
      "category": "Maison",
      "sub_category": "Jardinage",
      "duration_min": 15
    },
    ...
  ],
  "stats": {
    "total_slots": 45,
    "pomodoro_slots": 22,
    "recurrent_slots": 23,
    "planned_slots": 0,
    "work_minutes": 550,
    "pause_minutes": 345
  },
  "recurrent_task_scores": [
    {"task_id": "REC001", "task_name": "Arroser les plantes", "score": 87.5},
    {"task_id": "REC015", "task_name": "Nettoyer caisse chat", "score": 95.2},
    {"task_id": "REC023", "task_name": "Ranger le bureau", "score": 62.1},
    ...
  ]
}
```

**Erreur 400** :
```json
{
  "error": "Invalid date format: 30/10/2025. Expected YYYY-MM-DD"
}
```

#### POST /api/v2/gitfocus/planning/export

**Description** : Exporte planning vers CSV + enregistre historique apprentissage

**Payload** :
```json
{
  "date": "2025-10-30",
  "planning": [...]  // Planning complet (peut être édité)
}
```

**Réponse 200** :
```json
{
  "message": "Planning exported successfully",
  "file_path": "C:\\...\\prod_data\\planned.csv",
  "task_count": 45,
  "placements_logged": 23
}
```

**Side Effects** :
1. Écrase `planned.csv`
2. **Append** dans `planning_placements_history.csv` (🆕)
3. Incrémente `EXPORT_COUNT` tâches respiratoires

#### GET /api/v2/gitfocus/tasks/recurrent

**Description** : Liste tâches récurrentes (80 tâches)

**Réponse 200** :
```json
{
  "tasks": [
    {
      "id": "REC001",
      "name": "Arroser les plantes",
      "description": "Arroser toutes les plantes d'intérieur",
      "category": "Maison",
      "sub_category": "Jardinage",
      "duration_min": 15,
      "recurrence_type": "weekly",
      "recurrence_interval": 7,
      "last_done_date": "22.10.25",
      "next_due_date": "29.10.25",
      "priority": 2,
      "status": "available",
      "is_active": 1
    },
    ...
  ],
  "count": 80,
  "active_count": 65
}
```

### 8.3 Endpoints CRUD

**Tous les endpoints CRUD suivent le même pattern** :
- `POST /api/v2/gitfocus/tasks/{type}` - Créer
- `PUT /api/v2/gitfocus/tasks/{type}/{id}` - Mettre à jour
- `DELETE /api/v2/gitfocus/tasks/{type}/{id}` - Supprimer

**Types** : `pomodoro`, `respiration`, `recurrent`, `planned`

**Endpoint spécial récurrentes** :
- `PATCH /api/v2/gitfocus/tasks/recurrent/{id}/toggle` - Bascule IS_ACTIVE (0 ↔ 1)

---

## 9. INTERFACE UTILISATEUR

### 9.1 Layout Général

```
┌───────────────────────────────────────────────────────────┐
│  HEADER                                                    │
│  🎯 GitFocus Planner V2                                    │
│  📅 [Date Selector] [Refresh]                              │
└───────────────────────────────────────────────────────────┘
┌──────────────────────────┬────────────────────────────────┐
│  PANEL GAUCHE (40%)      │  PANEL DROIT (60%)             │
│                          │                                │
│  📋 Tâches Pomodoro ▼    │  📊 Planning Généré            │
│  ☐ Installer VM (200m)   │                                │
│  ☐ Révision maths (100m) │  08:00-08:25 🔴 Pomodoro 1/8   │
│  [+ Nouvelle]            │  "Installer VM"                │
│                          │  [Drag handle]                 │
│  🧘 Tâches Respir. ▼     │                                │
│  ☐ Méditation (10m)      │  08:25-08:40 🟢 Arroser...     │
│  ☐ Pause café (5m)       │  [Drag handle]                 │
│  [+ Nouvelle]            │                                │
│                          │  08:40-09:05 🔴 Pomodoro 2/8   │
│  🔁 Tâches Récurr. ▼     │  "Installer VM"                │
│  [Sélection auto via scoring] │  [Drag handle]             │
│  Suggestions:            │                                │
│  • Arroser (score 87.5)  │  ...                           │
│  • Nettoyer chat (95.2)  │                                │
│  [+ Nouvelle]            │  [➕ Pause] [➕ Pomodoro]       │
│                          │                                │
│  📅 Tâches Planif. ▼     │  Stats:                        │
│  📌 RDV médecin 14:30    │  Total: 45 créneaux            │
│  [+ Nouvelle]            │  Travail: 550 min              │
│                          │  Pauses: 345 min               │
│                          │                                │
│                          │  [📥 Exporter CSV]             │
└──────────────────────────┴────────────────────────────────┘
```

### 9.2 Responsive Mobile

Sur mobile/tablette :
- Panel gauche passe au-dessus (100% width)
- Panel droit en-dessous (100% width)
- Sections collapsibles fermées par défaut
- Drag & drop fonctionne avec touch events

### 9.3 Code Couleur Planning

```css
:root {
    --bg-pomodoro: #fef3c7;     /* Jaune pâle */
    --border-pomodoro: #f59e0b; /* Orange */

    --bg-recurrent: #e9d5ff;    /* Violet pâle */
    --border-recurrent: #a855f7; /* Violet */

    --bg-planned: #dbeafe;      /* Bleu pâle */
    --border-planned: #3b82f6;  /* Bleu */

    --bg-respiration: #d1fae5;  /* Vert pâle */
    --border-respiration: #10b981; /* Vert */
}

.planning-slot {
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 6px;
    border-left: 4px solid;
}

.planning-slot.pomodoro {
    background: var(--bg-pomodoro);
    border-color: var(--border-pomodoro);
}

.planning-slot.recurrent {
    background: var(--bg-recurrent);
    border-color: var(--border-recurrent);
}
```

### 9.4 Ajout Manuel de Tâches Récurrentes (🆕 2025-10-30)

**Nouvelle fonctionnalité** : Ajout interactif de tâches récurrentes au planning

**Principe** :
- L'utilisateur peut cliquer sur n'importe quelle tâche récurrente de la liste
- La tâche est ajoutée à la **première place libre** du planning existant
- Permet d'ajouter la même tâche plusieurs fois (doublons autorisés)
- Fonctionne après la génération initiale du planning

**Flux utilisateur** :
1. Générer un planning de base (tâches Pomodoro)
2. Section "Tâches Récurrentes" affiche toutes les tâches actives
3. Cliquer sur une tâche récurrente → Elle s'ajoute immédiatement au planning
4. La tâche apparaît après le dernier créneau existant
5. Possibilité de cliquer plusieurs fois sur la même tâche
6. Vérification automatique : Refuse si dépasse 23:00

**Comportement interface** :
- Liste des tâches récurrentes cliquable (fond bleu clair)
- Hover sur tâche : Surbrillance bleue + animation de levée
- Message de confirmation : "Ajouté: [Nom tâche] ([Heure début] - [Heure fin])"
- Message d'erreur si planning vide : "Générez d'abord un planning avant d'ajouter..."
- Message d'erreur si dépasse 23h : "Impossible d'ajouter : dépasse 23h00"

**Calcul de la place libre** :
- Prendre le dernier créneau du planning (last_slot)
- Nouvelle tâche commence à : `last_slot.heure_fin`
- Nouvelle tâche finit à : `last_slot.heure_fin + durée_tâche`
- Vérifier que heure_fin <= 23:00

**Statistiques recalculées** :
- Après chaque ajout, recalculer automatiquement :
  - Total de créneaux
  - Nombre de créneaux récurrents
  - Minutes de pauses totales
- Mettre à jour l'affichage des stats en temps réel

**Persistance** :
- L'ajout manuel modifie le `state.currentPlanning` (frontend)
- Lors de l'export CSV, les tâches ajoutées manuellement sont incluses
- Type de créneau : `recurrent`

**Avantages** :
- Flexibilité totale pour l'utilisateur
- Pas besoin de recalculer tout le planning
- Conserve le planning de base intact
- Permet l'ajustement fin du planning selon les besoins du jour

### 9.5 Optimisations d'Interface (🆕 2025-10-30)

**Nouvelle configuration** : Interface optimisée pour densité et navigation

#### Extension du planning jusqu'à minuit

**Principe** :
- Le planning journalier s'étend maintenant de 06:00 à 00:00 (minuit)
- Augmente la fenêtre disponible de 17h (06:00-23:00) à 18h (06:00-00:00)
- Permet de planifier davantage de tâches par jour
- Respecte les habitudes de travail tardif

**Calcul des créneaux** :
- Début : 06:00 pour les jours futurs, heure actuelle arrondie aux 15 minutes supérieures pour aujourd'hui
- Fin : 00:00 (minuit) du jour suivant
- Blocs de 30 minutes jusqu'à 23:30-00:00
- Validation : Refuse l'ajout de tâches si la fin dépasse minuit

**Impact sur les modules** :
- Calcul des créneaux libres mis à jour (30-minute blocks jusqu'à minuit)
- Recalcul des horaires après modifications (max_time = minuit)
- Validation frontend alignée sur nouveau seuil

#### Panel droit sticky (planning toujours visible)

**Principe** :
- Le panel de droite (affichage du planning) reste fixe lors du défilement vertical
- Permet de consulter le planning pendant qu'on parcourt la liste des tâches
- Améliore l'expérience utilisateur sur les longs plannings

**Comportement** :
- Position : sticky avec top: 20px (garde 20px d'espace en haut)
- Hauteur maximale : calc(100vh - 40px) pour s'adapter à la fenêtre
- Défilement interne : Si le planning dépasse la hauteur visible, scrollbar apparaît dans le panel
- Responsive : Sur mobile/tablette, le sticky est désactivé (stacking vertical naturel)

#### Réduction de la hauteur des éléments

**Principe** :
- Réduction de l'espace vertical occupé par chaque élément
- Permet d'afficher davantage de tâches sans défilement
- Améliore la vue d'ensemble du planning

**Éléments de tâches (listes gauche)** :
- Padding réduit : 6px 10px (au lieu de 10px)
- Margin-bottom réduite : 4px (au lieu de 8px)
- Hauteur effective réduite de ~30%
- Conserve la lisibilité avec espacement suffisant

**Slots de planning (panel droit)** :
- Padding réduit : 8px 10px (au lieu de 12px)
- Margin-bottom réduite : 6px (au lieu de 10px)
- Affichage plus compact sans perte d'information

#### Affichage optimisé du planning

**Principe** :
- Simplification visuelle pour réduire l'encombrement
- Informations essentielles sur la ligne principale
- Détails en petit en dessous

**Structure de chaque slot** :
- **Ligne principale** (flex horizontal) :
  - Icône emoji + Heure de début (ex: "🔴 08:00")
  - Nom de la tâche (ex: "Installer machine virtuelle")
  - Durée (ex: "25 min")
- **Ligne secondaire** (petite police) :
  - Catégorie et sous-catégorie
  - Métadonnées (Pomodoro x/y, replanifiée, etc.)

**Affichage des heures** :
- Affichage de l'heure de début UNIQUEMENT
- L'heure de fin est implicite (= heure de début de la tâche suivante)
- Réduit la redondance visuelle
- Simplifie la lecture chronologique du planning

**Styles appliqués** :
- `.slot-header` : Flexbox horizontal avec gap de 8px, alignement centré
- `.slot-time` : Police 0.9rem, poids 700, flex-shrink: 0 (ne rétrécit jamais)
- `.slot-name` : Police 0.95rem, poids 600, flex: 1 (prend l'espace disponible)
- `.slot-duration` : Police 0.85rem, poids 600, flex-shrink: 0
- `.slot-details` : Police 0.7rem (très petite), couleur grise (#9ca3af), hauteur de ligne 1.3

**Avantages** :
- Vision panoramique améliorée : Plus de slots visibles simultanément
- Navigation facilitée : Moins de défilement nécessaire
- Lecture optimisée : Informations principales en évidence, détails discrets
- Planning toujours accessible : Panel sticky élimine les allers-retours
- Journée complète planifiable : 18h disponibles au lieu de 17h

#### Affichage optimisé des listes de tâches (🆕 2025-10-30)

**Principe** :
- Application de la même logique de resserrage aux listes de tâches (Pomodoro et Récurrentes)
- Affichage compact sur une ligne principale avec détails en petite police dessous
- Cohérence visuelle avec l'affichage du planning

**Structure des tâches Pomodoro** :
- **Checkbox** (à gauche, conservée pour la sélection)
- **Ligne principale** (flex horizontal) :
  - Nom de la tâche (ex: "Installer machine virtuelle")
  - Durée restante (ex: "200 min")
  - Priorité (ex: "P1" en orange)
- **Ligne secondaire** (petite police) :
  - Catégorie › Sous-catégorie
  - Deadline si présente
  - Description si présente

**Structure des tâches récurrentes** :
- **Ligne principale** (flex horizontal) :
  - Icône 🟣
  - Nom de la tâche (ex: "Arroser les plantes")
  - Durée (ex: "5 min")
- **Ligne secondaire** (petite police) :
  - Catégorie › Sous-catégorie
  - Date d'échéance si présente
  - Description si présente

**Styles appliqués** :
- `.task-item-header` : Flexbox horizontal avec gap de 8px, alignement centré
- `.task-item-icon` : Police 0.9rem, flex-shrink: 0
- `.task-item-name` : Police 0.95rem, poids 600, flex: 1 (prend l'espace disponible)
- `.task-item-duration` : Police 0.85rem, poids 600, couleur grise, flex-shrink: 0
- `.task-item-priority` : Police 0.8rem, poids 600, couleur orange (#f59e0b), flex-shrink: 0
- `.task-item-details` : Police 0.7rem (très petite), couleur grise claire (#9ca3af), hauteur de ligne 1.3

**Comportement** :
- Ligne principale : Informations essentielles toujours visibles
- Ligne secondaire : Contexte additionnel en retrait visuel (petite police, couleur grise)
- Utilisation de flexbox pour alignement horizontal automatique
- flex-shrink: 0 sur durée et priorité pour éviter la compression
- flex: 1 sur le nom pour qu'il prenne tout l'espace disponible

**Avantages** :
- Cohérence visuelle entre listes et planning
- Lecture rapide des informations essentielles
- Détails accessibles mais non intrusifs
- Gain d'espace vertical supplémentaire (~10% par rapport à l'affichage déjà réduit)
- Meilleure hiérarchie visuelle (nom en évidence, métadonnées discrètes)

---

## 10. BONNES PRATIQUES & ANTI-PATTERNS

### 10.1 NO RUSTINES (Règle Absolue)

**Principe** : Toujours traiter la cause racine, jamais le symptôme.

**Exemples interdits** :
```python
# ❌ RUSTINE
try:
    task_id = task['id']
except KeyError:
    task_id = "unknown"  # Masque le problème

# ❌ RUSTINE
if planning_history is None:
    planning_history = []  # Pourquoi est-ce None?

# ❌ RUSTINE
setTimeout(() => {
    renderPlanning();
}, 1000);  // Attendre au hasard
```

**Solutions correctes** :
```python
# ✅ CORRECT
if 'id' not in task:
    raise ValueError(f"Task missing required field 'id': {task}")

# ✅ CORRECT
if not csv_path.exists():
    raise FileNotFoundError(f"Required file not found: {csv_path}")

# ✅ CORRECT (JavaScript)
async function loadAndRender() {
    const planning = await fetchAPI('/api/v2/gitfocus/planning/generate-auto');
    renderPlanning(planning);
}
```

### 10.2 Écriture Atomique OBLIGATOIRE

```python
def _atomic_write_csv(csv_path, rows, fieldnames):
    """Pattern atomique pour TOUTES les écritures CSV."""
    temp_file = csv_path.with_suffix('.tmp')

    try:
        # Écrire dans temp file
        with open(temp_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(rows)

        # Renommer atomiquement (garanti par l'OS)
        temp_file.replace(csv_path)

    except Exception as e:
        # Cleanup en cas d'erreur
        if temp_file.exists():
            temp_file.unlink()
        raise
```

**Pourquoi** : Si crash pendant écriture, temp file corrompu mais original intact.

### 10.3 Logging Complet

```python
import logging

logger = logging.getLogger(__name__)

def calculate_task_score(task, target_date, planning_history, done_history):
    logger.debug(f"Calculating score for task {task['id']} on {target_date}")

    score = 0.0

    try:
        rec_score = calculate_recurrence_score(task, target_date, done_history)
        logger.debug(f"Task {task['id']}: recurrence_score={rec_score}")
        score += rec_score

        day_score = calculate_day_frequency_score(task, target_date, planning_history)
        logger.debug(f"Task {task['id']}: day_frequency_score={day_score}")
        score += day_score

        # ...

        logger.info(f"Task {task['id']} final score: {score}")
        return score

    except Exception as e:
        logger.error(f"Error calculating score for task {task['id']}: {e}", exc_info=True)
        raise
```

**Niveaux** :
- DEBUG : Détails calculs
- INFO : Événements normaux
- WARNING : Anormal mais pas bloquant
- ERROR : Erreur bloquante

### 10.4 Tests OBLIGATOIRES

```python
# tests/test_smart_scorer.py

def test_recurrence_score_never_done():
    """Tâche jamais faite → 50 points"""
    task = {'id': 'REC001', 'recurrence_type': 'daily', 'recurrence_interval': 1}
    score = calculate_recurrence_score(task, '2025-10-30', done_history=[])

    assert score == 50.0

def test_recurrence_score_overdue_3_days():
    """Tâche en retard de 3 jours → 30 points"""
    task = {'id': 'REC001', 'recurrence_type': 'daily', 'recurrence_interval': 1}
    done_history = [{'ID': 'REC001', 'DONE_AT': '2025-10-26T10:00:00', 'TYPE': 'recurrent'}]

    score = calculate_recurrence_score(task, '2025-10-30', done_history)

    assert score == 30.0

def test_day_frequency_score_80_percent():
    """Tâche planifiée 4 fois sur 5 le lundi → 16 points"""
    task = {'id': 'REC001'}
    planning_history = [
        {'TASK_ID': 'REC001', 'DAY_OF_WEEK': '0'},  # Lundi
        {'TASK_ID': 'REC001', 'DAY_OF_WEEK': '0'},
        {'TASK_ID': 'REC001', 'DAY_OF_WEEK': '0'},
        {'TASK_ID': 'REC001', 'DAY_OF_WEEK': '0'},
        {'TASK_ID': 'REC001', 'DAY_OF_WEEK': '3'},  # Jeudi
    ]

    # Target = Lundi (2025-10-27)
    score = calculate_day_frequency_score(task, '2025-10-27', planning_history)

    assert abs(score - 16.0) < 0.1
```

**Lancer** :
```bash
pytest tests/ -v
```

### 10.5 Encodage STRICT UTF-8

```python
# ✅ TOUJOURS spécifier encoding
with open(csv_path, 'r', encoding='utf-8') as f:
    ...

with open(csv_path, 'w', encoding='utf-8') as f:
    ...
```

**Gestion erreur encodage** :
```python
def load_csv_safe(csv_path):
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f, delimiter=';'))
    except UnicodeDecodeError:
        logger.warning(f"{csv_path} not UTF-8, trying latin-1")

        # Lire en latin-1
        with open(csv_path, 'r', encoding='latin-1') as f:
            content = f.read()

        # Ré-encoder en UTF-8
        with open(csv_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"{csv_path} re-encoded to UTF-8")

        # Recharger
        with open(csv_path, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f, delimiter=';'))
```

---

## 11. TESTS & VALIDATION

### 11.1 Tests Unitaires

**Modules à tester** :
- `smart_scorer.py` (scoring 4 critères)
- `placement_logger.py` (enregistrement historique)
- `data_loader.py` (lecture CSV)
- `data_writer.py` (écriture atomique)
- `slot_calculator.py` (créneaux libres)
- `planning_generator.py` (orchestration)

**Structure** :
```
tests/
├── test_smart_scorer.py         # 🆕 Tests scoring
├── test_placement_logger.py     # 🆕 Tests historique
├── test_data_loader.py
├── test_data_writer.py
├── test_slot_calculator.py
├── test_planning_generator.py
└── conftest.py                  # Fixtures pytest
```

**Fixtures** :
```python
# tests/conftest.py

import pytest
from pathlib import Path
import csv

@pytest.fixture
def temp_csv_file(tmp_path):
    """Crée fichier CSV temporaire pour tests."""
    csv_path = tmp_path / 'test.csv'

    rows = [
        {'ID': 'REC001', 'NAME': 'Test task', 'DURATION_MIN': '15'},
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['ID', 'NAME', 'DURATION_MIN']
        writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    return csv_path
```

### 11.2 Tests d'Intégration

**Scénario 1 : Planning Complet Avec Scoring**
```python
def test_full_planning_generation_with_scoring(tmp_path):
    """Test génération complète avec scoring automatique."""

    # Créer fichiers CSV temporaires
    # ...

    result = generate_planning_auto(
        date="2025-10-30",
        pomodoro_ids=["1", "2"],
        max_recurrent_tasks=10,
        data_dir=tmp_path
    )

    # Vérifications
    assert 'planning' in result
    assert 'stats' in result
    assert 'recurrent_task_scores' in result

    assert len(result['planning']) > 0
    assert len(result['recurrent_task_scores']) == 10

    # Vérifier alternance
    for i in range(len(result['planning']) - 1):
        current_type = result['planning'][i]['type']
        next_type = result['planning'][i + 1]['type']

        work_types = {'pomodoro', 'planned', 'recurrent'}
        current_is_work = current_type in work_types
        next_is_work = next_type in work_types

        # Pas deux tâches de travail consécutives
        assert not (current_is_work and next_is_work)
```

**Scénario 2 : Export + Enregistrement Historique**
```python
def test_export_logs_placements(tmp_path):
    """Test que l'export enregistre bien dans historique."""

    planning = [
        {'type': 'recurrent', 'task_id': 'REC001', 'task_name': 'Test', 'heure_debut': '08:00', 'date': '2025-10-30'},
        {'type': 'recurrent', 'task_id': 'REC015', 'task_name': 'Test2', 'heure_debut': '10:00', 'date': '2025-10-30'},
    ]

    export_timestamp = '2025-10-30T12:00:00'

    log_planning_placements(planning, export_timestamp, tmp_path)

    # Vérifier fichier créé
    history_file = tmp_path / 'planning_placements_history.csv'
    assert history_file.exists()

    # Vérifier contenu
    with open(history_file, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f, delimiter=';'))

    assert len(rows) == 2
    assert rows[0]['TASK_ID'] == 'REC001'
    assert rows[1]['TASK_ID'] == 'REC015'
```

### 11.3 Tests Manuels (Checklist)

- [ ] Ouvrir `/gitfocus-v2` sur desktop
- [ ] Ouvrir sur mobile (ou mode responsive)
- [ ] Sélectionner 3 tâches Pomodoro → Planning généré automatiquement
- [ ] Vérifier que tâches récurrentes affichent scores (transparence)
- [ ] Drag & drop un créneau → Recalcul immédiat
- [ ] Drag & drop créant 2 Pomodoros consécutifs → Pause insérée auto
- [ ] Ajouter pause manuellement → Fonctionne
- [ ] Supprimer créneau → Recalcul correct
- [ ] Changer date → Données rechargées
- [ ] Exporter CSV → Fichiers générés (`planned.csv` + `planning_placements_history.csv`)
- [ ] Vérifier historique append (ne pas écraser)
- [ ] Vider cache navigateur → Page se recharge correctement

---

## 12. DÉPLOIEMENT

### 12.1 Configuration Serveur

**Variables d'environnement** :
```bash
# .env (optionnel)
DATA_DIR=C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data
HOST=0.0.0.0
PORT=5000
DEBUG=True
LOG_LEVEL=INFO
```

**Configuration** :
```python
# webapp/config.py

from pathlib import Path
import os

class Config:
    DATA_DIR = Path(os.getenv('DATA_DIR', 'C:/Users/juli0/AndroidStudioProjects/GitFocus_2/prod_data'))
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
```

### 12.2 Scripts Démarrage

**Windows** : `scripts/start.bat`
```batch
@echo off
echo ========================================
echo  GitFocus Planner V2 - Démarrage
echo ========================================

REM Tuer processus Python existants
taskkill /F /IM python.exe /T 2>nul

REM Attendre 2 secondes
timeout /t 2 /nobreak >nul

REM Démarrer serveur
cd /d C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
webapp\venv\Scripts\python.exe -m webapp.server

pause
```

**Linux/Mac** : `scripts/start.sh`
```bash
#!/bin/bash

echo "========================================"
echo " GitFocus Planner V2 - Démarrage"
echo "========================================"

# Tuer processus Python existants
pkill -9 python

# Attendre 2 secondes
sleep 2

# Démarrer serveur
cd /path/to/GitfocusPlanner
source webapp/venv/bin/activate
python -m webapp.server
```

### 12.3 Health Check

**Endpoint** : `GET /health`

```python
@app.route('/health')
def health_check():
    """Vérifie fichiers CSV requis + historique."""
    required_files = [
        'LISTE_MERE.v2.csv',
        'TACHES_RESPIRATOIRES.v2.csv',
        'TACHES_RECURRENTES.v2.csv',
        'temps_morts.csv',
        'categories.csv',
        'done_v2.csv',
        'planning_placements_history.csv'  # 🆕
    ]

    missing = []
    for filename in required_files:
        if not (DATA_DIR / filename).exists():
            missing.append(filename)

    if missing:
        return jsonify({
            'status': 'unhealthy',
            'missing_files': missing
        }), 500

    # Vérifier taille historique (optionnel)
    history_file = DATA_DIR / 'planning_placements_history.csv'
    history_size = len(history_file.read_text().splitlines()) if history_file.exists() else 0

    return jsonify({
        'status': 'healthy',
        'version': '2.0',
        'data_dir': str(DATA_DIR),
        'history_entries': history_size - 1  # - header
    }), 200
```

**Test** :
```bash
curl http://localhost:5000/health
```

---

## FIN DES SPÉCIFICATIONS COMPLÈTES

**Version** : 2.0 Final
**Date** : 2025-10-30
**Statut** : Prêt pour implémentation

**Résumé des Nouveautés** :
- 🆕 Système d'apprentissage intelligent (scoring 4 critères)
- 🆕 Fichier `planning_placements_history.csv` (append-only)
- 🆕 Module `smart_scorer.py` (calcul scores 0-100)
- 🆕 Module `placement_logger.py` (enregistrement historique)
- 🆕 Drag & drop interactif avec SortableJS
- 🆕 Recalcul dynamique contraintes (alternance + temps_morts)
- 🆕 Endpoint `/planning/generate-auto` (génération avec scoring)
- 🆕 Transparence scoring (affichage scores dans réponse API)

**Différences Clés vs Anciennes Spécifications** :
- ✅ Tâches récurrentes (~80) utilisées comme pauses (pas respiratoires)
- ✅ Scoring automatique pour sélection tâches récurrentes
- ✅ Historique placements pour apprentissage
- ✅ Drag & drop avec recalcul local (pas serveur)
- ✅ Colonnes extensibles MOOD/ENERGY/WEATHER (futur)

**Prêt à Implémenter** : OUI

**Prochaine Étape** : Commencer Phase 1 (Backend modules smart_scorer.py et placement_logger.py)
