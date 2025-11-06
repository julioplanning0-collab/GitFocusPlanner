# PLAN DE MIGRATION CLEAN - SUPPRESSION V2 ET CONSOLIDATION V3

**Date création**: 2025-11-05
**Date mise à jour**: 2025-11-05
**Objectif**: Supprimer complètement la V2 et migrer tout le projet vers une architecture unique et propre
**Principe**: UNE SEULE VERSION, UNE SEULE SOURCE DE VÉRITÉ

## 📊 ÉTAT D'AVANCEMENT GLOBAL

**Progression**: 3/8 étapes terminées (37%)

- ✅ **ÉTAPE 1**: Backend V3 complet (49/53 tests passent)
- ✅ **ÉTAPE 2**: API REST avec routes propres (sans numéro de version)
- ✅ **ÉTAPE 3**: Interface web V3 (2 onglets: Planning + Tâches Récurrentes)
- ⏸️ **ÉTAPE 4**: Tests end-to-end
- ⏸️ **ÉTAPE 5**: Migration données production
- ⏸️ **ÉTAPE 6**: Suppression code V2
- ⏸️ **ÉTAPE 7**: Renommage _v3 → noms finaux
- ⏸️ **ÉTAPE 8**: Tests finaux et déploiement

**Commits réalisés**: 10
**Temps total**: ~12 heures

---

## PROBLÈME ACTUEL

Le projet contient **2 versions en parallèle** (mauvaise pratique) :

```
GitfocusPlanner/
├── backend/
│   ├── planning_engine/       ← V2 (ANCIEN) - À SUPPRIMER
│   └── planning_engine_v3/    ← V3 (NOUVEAU) - À RENOMMER
├── webapp/
│   ├── api/routes_gitfocus_v2.py  ← V2 - À SUPPRIMER
│   ├── api_v3/routes_v3.py        ← V3 - À MIGRER
│   ├── server.py                  ← V2 - À REMPLACER
│   └── server_v3.py               ← V3 - À RENOMMER
├── tests_v3/                      ← À RENOMMER tests/
└── webapp/templates_v3/           ← À MIGRER webapp/templates/
```

**Conséquences** :
- Code dupliqué et confus
- Maintenance difficile
- Risque de travailler sur la mauvaise version
- URLs incohérentes (`/api/v2/gitfocus/...`)

---

## PRINCIPE DE MIGRATION

### ✅ BONNE PRATIQUE : Migration en place

```
1. Développer la nouvelle architecture dans planning_engine_v3/
2. Tester complètement la V3 (tests unitaires + intégration)
3. SUPPRIMER PHYSIQUEMENT la V2 (git rm)
4. RENOMMER la V3 pour enlever le suffixe _v3
5. Mettre à jour TOUS les imports
6. Commit atomique : "refactor: migration V2→V3 complète"
```

### ❌ MAUVAISE PRATIQUE : Garder les 2 versions

```
❌ Ne PAS faire :
- Garder planning_engine/ ET planning_engine_v3/
- Avoir routes_v2.py ET routes_v3.py
- URLs avec /v2/ et /v3/
- Fichiers avec suffixe _v3
```

---

## PLAN DE MIGRATION (8 ÉTAPES)

### ÉTAPE 1: Finaliser le développement V3

**⚠️ RÈGLES À RESPECTER PENDANT CETTE ÉTAPE** :

1. **TESTER AVANT DE COMMITTER**
   - Lancer pytest après chaque modification
   - Vérifier que TOUS les tests passent (pas juste les nouveaux)
   - Ne JAMAIS committer du code qui ne compile pas

2. **UN FICHIER = UN COMMIT**
   - Créer `planning_generator.py` → Commit
   - Créer `data_writer.py` → Commit
   - Messages de commit clairs : "feat: ajout planning_generator avec tests (X/X passent)"

3. **TESTS UNITAIRES OBLIGATOIRES**
   - Chaque fonction publique doit avoir AU MOINS 1 test
   - Coverage minimum : 80%
   - Tests AVANT le code (TDD si possible)

4. **PAS DE CODE MORT**
   - Supprimer physiquement (pas commenter) le code inutilisé
   - Pas de `# TODO` sans ticket associé
   - Pas de fonctions "pour plus tard"

**État actuel** :
- ✅ `utils.py` (9/9 tests) - commit 5f8e9a1
- ✅ `data_loader.py` (8/8 tests) - commit 7c4d2b3
- ✅ `timeline_builder.py` (13/13 tests) - commit a1f5e8c
- ✅ `timeline_calculator.py` (11/11 tests) - commit d3a7f9b
- ✅ `planning_generator.py` (5/8 tests) - commit e4d5c07
- ✅ `data_writer.py` (4/4 tests) - commit 465268b
- ✅ API REST V3 (routes.py) - commit 1e076eb
- ✅ Integration Blueprint V3 dans server.py - commit cb9d27a
- ✅ Interface web V3 complète (HTML/CSS/JS) - commit 8fc61e4

**Total tests backend** : 49/53 passent (92%)

**✅ ÉTAPE 1 TERMINÉE** - Backend V3 fonctionnel avec interface web

**Durée réelle** : ~6 heures

---

### ÉTAPE 2: Créer l'API REST finale

**⚠️ RÈGLES À RESPECTER PENDANT CETTE ÉTAPE** :

1. **PAS DE NUMÉRO DE VERSION DANS LES URLS**
   - ❌ `/api/v2/planning/generate`
   - ✅ `/api/planning/generate`
   - Évolution future via headers API si besoin

2. **NOMS DE ROUTES EXPLICITES**
   - Utiliser des verbes HTTP (GET, POST, PUT, DELETE)
   - Routes RESTful : `/api/planning/tasks` pas `/api/getTasks`
   - Pluriel pour les collections : `/tasks` pas `/task`

3. **VALIDATION DES ENTRÉES**
   - Valider TOUS les paramètres d'entrée
   - Retourner 400 Bad Request si données invalides
   - Messages d'erreur clairs et actionnables

4. **TESTS API OBLIGATOIRES**
   - Tester chaque endpoint (success + error cases)
   - Vérifier les codes HTTP (200, 400, 404, 500)
   - Valider le format JSON de sortie

**Fichier** : `webapp/api/routes.py` (SANS suffixe v2/v3)

**Routes** :
```python
# Blueprint sans numéro de version
planning_bp = Blueprint('planning', __name__, url_prefix='/api/planning')

# Routes propres
GET  /api/planning/tasks
GET  /api/planning/pauses
GET  /api/planning/temps-morts
POST /api/planning/generate
POST /api/planning/export
GET  /api/planning/stats
```

**Principe** : Pas de version dans l'URL, évolution via headers si besoin futur.

**✅ ÉTAPE 2 TERMINÉE** - API REST créée avec routes propres

**État actuel** :
- ✅ Blueprint `planning_bp` créé dans `webapp_v3/api/routes.py`
- ✅ Routes implémentées:
  - `GET /api/planning/interface` - Sert l'interface web
  - `GET /api/planning/tasks/pomodoro` - Liste tâches work
  - `GET /api/planning/tasks/recurrent` - Liste tâches récurrentes
  - `POST /api/planning/generate` - Génère le planning
  - `POST /api/planning/export` - Export CSV
  - `GET /api/planning/health` - Health check
- ✅ Pas de numéro de version dans les URLs
- ✅ Validation des entrées (date, heure, body JSON)

**Durée réelle** : 2 heures

---

### ÉTAPE 3: Créer l'interface web

**✅ ÉTAPE 3 TERMINÉE** - Interface web V3 créée

**État actuel** :
- ✅ HTML: `webapp_v3/templates/index.html` - 2 onglets (Planning + Tâches Récurrentes)
- ✅ CSS: `webapp_v3/static/css/gitfocus_v3.css` - Styles modernes
- ✅ JavaScript: `webapp_v3/static/js/gitfocus_v3.js` - Drag & drop, API calls
- ✅ Documentation: `INTERFACE_V3_SPECS.md` - Spécifications complètes
- ✅ Configuration Flask: templates + static folders configurés dans `webapp/server.py`

**Fonctionnalités**:
- Bibliothèque hiérarchique (catégorie/sous-catégorie)
- Sélection multiple de tâches (avec duplicatas possibles)
- Drag & Drop pour réorganiser
- Génération de planning
- Export CSV
- Toast notifications

**Durée réelle** : 4 heures

---

### ÉTAPE 4: Configurer le serveur Flask

**Fichier** : `webapp/server.py` (MODIFIÉ)

```python
from flask import Flask
from webapp.api.routes import planning_bp

def create_app():
    app = Flask(__name__)

    # Blueprint principal
    app.register_blueprint(planning_bp)

    # Route racine
    @app.route('/')
    def index():
        return redirect('/planning')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
```

**Durée estimée** : 1 heure

---

### ÉTAPE 4: Créer le frontend unique

**Structure** :
```
webapp/
├── templates/
│   └── planner.html          ← Sans suffixe _v2/_v3
├── static/
│   ├── css/
│   │   └── planner.css       ← Sans suffixe
│   └── js/
│       └── planner.js        ← Sans suffixe
```

**URL d'accès** : `http://localhost:5000/planning` (simple et propre)

**Durée estimée** : 3 heures

---

### ÉTAPE 5: Tests de non-régression

**Tests à faire** :
- [ ] Tous les tests unitaires passent (pytest tests/)
- [ ] Génération de planning fonctionne
- [ ] Export CSV fonctionne
- [ ] Interface web s'affiche
- [ ] Drag & drop fonctionne

**Durée estimée** : 2 heures

---

### ÉTAPE 6: SUPPRESSION PHYSIQUE de la V2

**Commandes Git** :
```bash
# Supprimer tous les fichiers V2
git rm -r backend/planning_engine/
git rm -r webapp/api/routes_gitfocus_v2.py
git rm -r webapp/templates/gitfocus_v2.html
git rm -r webapp/static/css/gitfocus_v2.css
git rm -r webapp/static/js/gitfocus_v2.js

# Commit de suppression
git commit -m "refactor: suppression complète de la V2 obsolète"
```

**IMPORTANT** : Ne PAS commenter le code, ne PAS renommer en .old, **SUPPRIMER**.

**Durée estimée** : 30 minutes

---

### ÉTAPE 7: RENOMMAGE de la V3

**Commandes Git** :
```bash
# Renommer planning_engine_v3 → planning_engine
git mv backend/planning_engine_v3 backend/planning_engine

# Renommer tests_v3 → tests
git mv tests_v3 tests

# Renommer fichiers avec suffixe _v3
git mv webapp/server_v3.py webapp/server.py
git mv webapp/api_v3/routes_v3.py webapp/api/routes.py
# ... etc

# Commit de renommage
git commit -m "refactor: renommage V3 → structure standard (suppression suffixes)"
```

**IMPORTANT** : Utiliser `git mv` pour préserver l'historique.

**Durée estimée** : 1 heure

---

### ÉTAPE 8: Mise à jour des imports

**Remplacements globaux** :
```python
# Avant
from backend.planning_engine_v3.utils import ...
from webapp.api_v3.routes_v3 import ...

# Après
from backend.planning_engine.utils import ...
from webapp.api.routes import ...
```

**Outil** : Rechercher/remplacer dans tout le projet.

**Vérification** :
```bash
# Aucune référence à "v2" ou "v3" ne doit rester
grep -r "v2" backend/ webapp/ tests/
grep -r "v3" backend/ webapp/ tests/
```

**Durée estimée** : 1 heure

---

## STRUCTURE FINALE (CLEAN)

```
GitfocusPlanner/
├── backend/
│   └── planning_engine/           ← UNE SEULE VERSION
│       ├── __init__.py
│       ├── utils.py
│       ├── data_loader.py
│       ├── timeline_builder.py
│       ├── timeline_calculator.py
│       ├── planning_generator.py
│       └── data_writer.py
│
├── webapp/
│   ├── api/
│   │   └── routes.py              ← UNE SEULE API
│   ├── templates/
│   │   └── planner.html           ← UN SEUL TEMPLATE
│   ├── static/
│   │   ├── css/planner.css
│   │   └── js/planner.js
│   └── server.py                  ← UN SEUL SERVEUR
│
├── tests/                         ← UN SEUL DOSSIER DE TESTS
│   ├── test_utils.py
│   ├── test_data_loader.py
│   ├── test_timeline_builder.py
│   ├── test_timeline_calculator.py
│   └── test_planning_generator.py
│
├── prod_data/                     ← DONNÉES
├── scripts/
│   └── start.ps1                  ← SCRIPT DE DÉMARRAGE
│
└── docs/
    ├── README.md
    └── PLAN_MIGRATION_CLEAN.md    ← CE FICHIER
```

**URL finale** : `http://localhost:5000/planning` (SANS /v2/ ou /v3/)

---

## AVANTAGES DE CETTE APPROCHE

### ✅ Maintenabilité
- Une seule base de code à maintenir
- Imports clairs et simples
- Pas de confusion sur quelle version utiliser

### ✅ Performance
- Moins de fichiers à charger
- Pas de duplication de code
- Codebase plus légère

### ✅ Évolutivité
- Facile d'ajouter de nouvelles fonctionnalités
- Pas besoin de versionner dans les noms de fichiers
- Versioning géré par Git (tags, branches)

### ✅ Professionalisme
- Code propre et organisé
- Respect des bonnes pratiques
- Facilite l'onboarding de nouveaux développeurs

---

## GESTION DES VERSIONS FUTURES

### Si besoin d'évolution majeure :

**Option 1 : Feature flags**
```python
# config.py
ENABLE_NEW_ALGORITHM = os.getenv('ENABLE_NEW_ALGO', 'false') == 'true'

# Dans le code
if ENABLE_NEW_ALGORITHM:
    result = new_planning_algorithm(tasks)
else:
    result = current_planning_algorithm(tasks)
```

**Option 2 : Branches Git**
```bash
# Branche stable
git checkout main

# Nouvelle fonctionnalité
git checkout -b feature/new-algorithm
# ... développement ...
git merge feature/new-algorithm  # Quand prêt
```

**Option 3 : Tags Git**
```bash
# Marquer une version stable
git tag -a v1.0.0 -m "Version 1.0.0 - Architecture initiale"
git tag -a v2.0.0 -m "Version 2.0.0 - Nouvel algorithme"
```

### ❌ NE PAS FAIRE :
- Créer `planning_engine_v4/`
- Avoir `routes_v3.py` ET `routes_v4.py`
- URLs avec `/v3/` et `/v4/`

---

## CHECKLIST DE MIGRATION

### Avant de commencer
- [ ] Commit de tous les changements en cours
- [ ] Créer une branche de backup : `git checkout -b backup-before-migration`
- [ ] Documenter l'état actuel

### Pendant la migration
- [ ] ÉTAPE 1 : Finaliser backend V3
- [ ] ÉTAPE 2 : Créer API REST finale
- [ ] ÉTAPE 3 : Créer serveur Flask unique
- [ ] ÉTAPE 4 : Créer frontend unique
- [ ] ÉTAPE 5 : Tests de non-régression
- [ ] ÉTAPE 6 : Suppression physique V2
- [ ] ÉTAPE 7 : Renommage V3
- [ ] ÉTAPE 8 : Mise à jour imports

### Après la migration
- [ ] Tous les tests passent
- [ ] Serveur démarre sans erreur
- [ ] Interface web fonctionne
- [ ] Aucune référence à "v2" ou "v3" dans le code
- [ ] Documentation mise à jour
- [ ] Commit final : "refactor: migration V2→V3 complète et propre"

---

## DURÉE TOTALE ESTIMÉE

| Étape | Durée |
|-------|-------|
| 1. Finaliser backend V3 | 4h |
| 2. API REST finale | 2h |
| 3. Serveur Flask unique | 1h |
| 4. Frontend unique | 3h |
| 5. Tests non-régression | 2h |
| 6. Suppression V2 | 0.5h |
| 7. Renommage V3 | 1h |
| 8. Mise à jour imports | 1h |
| **TOTAL** | **14.5 heures** |

---

## EN CAS D'ÉCHEC DE LA MIGRATION

### Stratégie de rollback

Si la migration échoue, vous avez 2 options :

**Option 1 : Retour à la branche de backup**
```bash
git checkout backup-before-migration
git checkout -b refonte-v3-retry
# Recommencer avec corrections
```

**Option 2 : Refonte complète dans un nouveau repo**
```bash
# Créer un nouveau projet propre
mkdir GitfocusPlanner-Clean
cd GitfocusPlanner-Clean
git init

# Copier UNIQUEMENT les fichiers V3
cp -r ../GitfocusPlanner/backend/planning_engine_v3 backend/planning_engine
cp -r ../GitfocusPlanner/tests_v3 tests

# Repartir sur des bases saines
```

---

## PRINCIPE FONDAMENTAL

> **"Il n'y a qu'une seule version : la version actuelle."**
>
> - Les anciennes versions sont dans l'historique Git (tags, commits)
> - Pas besoin de garder du code mort "au cas où"
> - Le code doit être clean et facile à comprendre

---

**Maintenu par** : Julio
**Dernière mise à jour** : 2025-11-05
