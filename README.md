# GitFocus Planner V2

**Application Web de Planning Pomodoro avec Apprentissage Intelligent**

Version 2.0 - Système d'apprentissage automatique pour sélection intelligente des tâches récurrentes.

---

## 🎯 Nouveautés V2

### Système d'Apprentissage Intelligent 🆕
- **Scoring automatique 4 critères** (0-100 points):
  - 50% Récurrence DUE (urgence - tâches en retard prioritaires)
  - 20% Fréquence jour semaine (habitudes - lundi → arrosage plantes)
  - 15% Fréquence globale (popularité - tâches souvent utilisées)
  - 15% Récence (actualité - tâches récentes pertinentes)

- **Historique append-only** (`planning_placements_history.csv`)
  - Enregistre chaque planification de tâche récurrente
  - Permet analyse statistique des habitudes
  - Colonnes extensibles (MOOD, ENERGY, WEATHER) pour évolution future

- **Sélection automatique**
  - Choix des 10 meilleures tâches récurrentes parmi ~80 disponibles
  - Système s'améliore avec le temps (plus d'historique = meilleure précision)

### Architecture Backend-First
- Backend fait TOUT (logique métier, scoring, génération planning)
- Frontend = présentation UNIQUEMENT (pas de logique)
- API REST complète (28 endpoints)

---

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.11+
- Flask 2.x
- Données CSV dans `prod_data/`

### Installation

```bash
# Activer environnement virtuel
webapp\venv\Scripts\activate  # Windows
source webapp/venv/bin/activate  # Linux/Mac

# Installer dépendances
pip install flask

# Démarrer serveur
python -m webapp.server
```

### Accès

- **Interface Web**: http://localhost:5000/api/v2/gitfocus/interface
- **Health Check**: http://localhost:5000/health
- **API Docs**: Voir `SPECIFICATIONS_COMPLETES_V2.md`

---

## 📂 Structure Projet

```
GitfocusPlanner/
├── backend/
│   └── planning_engine/
│       ├── data_loader.py         # Lecture CSV (+ historiques)
│       ├── data_writer.py         # Écriture atomique CSV
│       ├── slot_calculator.py     # Calcul créneaux libres
│       ├── smart_scorer.py        # 🆕 Scoring intelligent
│       ├── placement_logger.py    # 🆕 Enregistrement historique
│       ├── task_integrator.py     # Intégration tâches spéciales
│       └── planning_generator.py  # Orchestrateur principal
│
├── webapp/
│   ├── server.py                  # Application Flask
│   ├── config.py                  # Configuration
│   └── api/
│       └── routes_gitfocus_v2.py  # 28 endpoints REST API
│
├── prod_data/                     # Données CSV
│   ├── LISTE_MERE.v2.csv         # Tâches Pomodoro (travail)
│   ├── TACHES_RECURRENTES.v2.csv # 🎯 ~80 tâches (pauses intelligentes)
│   ├── TACHES_RESPIRATOIRES.v2.csv
│   ├── TACHES_PLANIFIEES.v2.csv
│   ├── temps_morts.csv
│   ├── categories.csv
│   ├── done_v2.csv               # Historique exécution (Android)
│   ├── planned.csv               # Planning exporté
│   └── planning_placements_history.csv  # 🆕 Apprentissage
│
├── scripts/
│   ├── start.bat                  # Démarrage Windows
│   └── stop.ps1                   # Arrêt Windows
│
├── CLAUDE.md                      # Bonnes pratiques développement
├── SPECIFICATIONS_COMPLETES_V2.md # Spécifications complètes
└── README.md                      # Ce fichier
```

---

## 🔑 API Endpoints Principaux

### Planning (🆕 Endpoints V2)

**POST** `/api/v2/gitfocus/planning/generate-auto`
- Génération automatique avec scoring intelligent
- Body: `{"date": "2025-10-30", "pomodoro_task_ids": ["1", "2"], "max_recurrent_tasks": 10}`
- Retourne planning complet + scores transparents

**POST** `/api/v2/gitfocus/planning/export`
- Export CSV + enregistrement historique apprentissage
- Body: `{"date": "2025-10-30", "planning": [...]}`
- Side effects: `planned.csv` + `planning_placements_history.csv`

### Données

- **GET** `/api/v2/gitfocus/tasks/pomodoro` - Tâches Pomodoro
- **GET** `/api/v2/gitfocus/tasks/recurrent` - Tâches récurrentes (~80)
- **GET** `/api/v2/gitfocus/tasks/planned?date=YYYY-MM-DD` - Tâches planifiées
- **GET** `/api/v2/gitfocus/categories` - Catégories
- **GET** `/api/v2/gitfocus/stats/history` - Statistiques historique

### CRUD Complet

Tous types de tâches: `POST`, `PUT`, `DELETE` disponibles.

Voir `SPECIFICATIONS_COMPLETES_V2.md` pour détails complets.

---

## 📊 Workflow Utilisateur

1. **Sélectionner tâches Pomodoro** (travail)
   → Cocher 2-3 tâches de travail

2. **Générer planning automatiquement** 🆕
   → Système sélectionne automatiquement top 10 tâches récurrentes via scoring
   → Alternance stricte Pomodoro ↔ Tâche récurrente

3. **Éditer visuellement** (optionnel)
   → Drag & drop pour réorganiser
   → Contraintes recalculées automatiquement

4. **Exporter CSV**
   → Planning écrit dans `planned.csv`
   → Historique enregistré pour apprentissage 🆕

5. **Application Android lit et exécute**
   → Écrit `done_v2.csv` lors de complétion
   → Système apprend des exécutions réelles

---

## 🧠 Évolution du Système d'Apprentissage

### Mois 1 (Historique Vide)
- Scoring basé principalement sur récurrence DUE (urgence)
- Tâches triées par urgence uniquement

### Mois 2 (~60 exports)
- Détection de patterns simples
- "Nettoyer caisse chat" souvent le matin

### Mois 6 (~360 exports)
- Patterns clairs: "Arroser plantes" → 80% lundi 08:00-09:00
- Suggestions pertinentes automatiques

### Année 1+ (>700 exports)
- Système très précis, adapté aux habitudes
- Possibilité extensions (MOOD, ENERGY, WEATHER)

---

## ⚙️ Configuration

Variables d'environnement (optionnelles):

```bash
DATA_DIR=C:\...\prod_data  # Chemin données CSV
HOST=0.0.0.0                # Hôte serveur
PORT=5000                   # Port serveur
DEBUG=True                  # Mode debug
LOG_LEVEL=INFO              # Niveau logs
```

---

## 📖 Documentation Complète

- **Spécifications**: `SPECIFICATIONS_COMPLETES_V2.md` (2050 lignes)
- **Bonnes pratiques**: `CLAUDE.md`
- **Algorithmes détaillés**: Voir Section 6 des spécifications

---

## 🛠️ Bonnes Pratiques Appliquées

✅ **Pas de rustines** - Toujours traiter la cause racine
✅ **Écriture atomique** - Temp file + rename (protection corruption)
✅ **Fail fast** - Messages d'erreur clairs
✅ **Logging complet** - DEBUG/INFO/WARNING/ERROR
✅ **Séparation stricte** - Backend logique / Frontend présentation
✅ **CSV UTF-8** - Encodage strict, délimiteur `;`

---

## 📝 Auteur & Version

- **Version**: 2.0 (Apprentissage Intelligent)
- **Date**: 2025-10-30
- **Architecture**: Backend-first, REST API, Learning System

---

## 🎁 Prochaines Évolutions

- [ ] Interface web drag & drop (SortableJS)
- [ ] Colonnes contextuelles (MOOD, ENERGY, WEATHER)
- [ ] Visualisation statistiques apprentissage
- [ ] Tests unitaires complets
- [ ] Docker deployment

**Le système est prêt pour utilisation et apprentissage!** 🚀
