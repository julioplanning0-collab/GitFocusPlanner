# GitFocus Planner - Notes de développement

## Accès Web

- **URL publique**: http://julioplanning0.duckdns.org:5000/gitfocus
- **URL locale**: http://localhost:5000/gitfocus
- **URL réseau local**: http://192.168.1.117:5000/gitfocus

## Architecture

### Backend
- Flask avec Blueprint (`gitfocus_bp`)
- Port: 5000
- Mode debug activé
- Auto-reload des templates

### Données
- **Source principale**: `C:\Users\juli0\AndroidStudioProjects\GitFocus_2\prod_data\`
  - `LISTE_MERE.v2.csv` - Liste des tâches principales
  - `TACHES_RESPIRATOIRES.v2.csv` - Tâches de respiration/pauses
  - `TACHES_RECURRENTES.v2.csv` - Tâches récurrentes (arrosage, ménage, etc.)
  - `TACHES_PLANIFIEES.v2.csv` - Tâches avec date/heure fixe (rendez-vous, événements)
  - `temps_morts.csv` - Plages horaires occupées
  - `planned.csv` - Planning exporté (généré)
  - `respiration_planning_history.csv` - **Historique complet** des planifications de tâches respiratoires
  - `categories.csv` - **Fichier centralisé des catégories et sous-catégories**

### Format des dates
- **temps_morts.csv**: Format ISO `YYYY-MM-DD` (ex: 2025-10-27)
- **LISTE_MERE.v2.csv**: Format `DD.MM.YY` (ex: 27.10.25)

### Format de l'historique
- **respiration_planning_history.csv**: Historique cumulatif des planifications
  - Colonnes: `ID;NAME;DATE;PLANNED_TIME;DURATION_MIN;EXPORT_TIMESTAMP`
  - Exemple: `R_001;Méditation;2025-10-27;10:30;10;2025-10-27T09:15:23`
  - Mode append: chaque export ajoute de nouvelles lignes sans écraser les anciennes
  - Permet l'analyse statistique des habitudes de planification

## Fonctionnalités

### Planning Pomodoro
- Sessions de travail: 25 minutes
- Pauses: durée variable selon tâche respiratoire sélectionnée (ou 5 min par défaut)
- Planning multi-jour avec sélecteur de date
- Drag & Drop pour réorganiser les tâches
- Filtrage automatique des créneaux passés pour aujourd'hui

### Export CSV
- Écriture sur le serveur uniquement (pas de téléchargement client)
- Fichier: `prod_data/planned.csv` (écrase le fichier existant à chaque export)
- Utile pour accès distant: le fichier reste sur le serveur
- Format avec colonne KIND (PLANNED/FIXED)
- Délimiteur: point-virgule (;)
- Encodage: UTF-8
- Réponse JSON avec confirmation du chemin et nombre de tâches

### Tâches respiratoires
- Sélection multiple avec compteur (x2, x3...)
- Permet les doublons
- IDs format: R_001, R_002, etc.
- **Tri par popularité**: Affichées par ordre décroissant de nombre d'exports
- Compteur d'exports (EXPORT_COUNT) incrémenté automatiquement à chaque export CSV

### Tâches récurrentes
- Gestion de tâches qui se répètent régulièrement (arrosage, ménage, etc.)
- Système actif/inactif avec toggle switch
- Types de récurrence: quotidien, hebdomadaire, mensuel
- Intervalle configurable (tous les X jours)
- IDs format: REC001, REC002, etc.
- 20 tâches pré-remplies (exemples domestiques)
- **Persistance de l'état**: Les tâches actives/inactives sont sauvegardées

### Tâches planifiées
- Tâches avec date et heure fixe (rendez-vous, événements, deadlines)
- **Intégration automatique**: Le backend intègre automatiquement les tâches planifiées dans le planning Pomodoro
- **Segmentation en Pomodoros**: Une tâche de 45 minutes devient 2 Pomodoros (25 min chacun)
- **Placement intelligent**: Remplace les Pomodoros les plus proches de l'heure planifiée
- **Détection de replanification**: Badge "Replanifiée" si l'heure finale diffère de l'heure initialement prévue
- **Format**: `PLANNED_START` = "DD.MM.YY HH:MM" (ex: "29.10.25 08:00")
- **Type d'affichage**: Fond jaune dans le planning, icône calendrier, numérotation des Pomodoros (1/2, 2/2)

### Interface utilisateur
- **Sections repliables**: Les 3 types de tâches sont dans des sections repliables (fermées par défaut)
- **Redimensionnement dynamique**: Click sur le chevron pour agrandir/réduire une section
  - **Premier click**: Déplie ET agrandit immédiatement (85% de l'espace, panel droit à 15%)
  - **Deuxième click**: Replie complètement et rétablit la vue normale
  - Click sur une autre section : Bascule automatiquement vers la nouvelle section
- **Compteurs**: Affichage du nombre de tâches et du nombre actif pour les récurrentes
- **Animations**: Transitions fluides (0.4s) pour tous les redimensionnements

### Gestion des catégories
- **Fichier unique** (`categories.csv`): Source centralisée pour toutes les catégories
- **Boutons d'ajout rapide**: Boutons "+" à côté de chaque menu déroulant
- **Ajout immédiat**: La catégorie est ajoutée à `categories.csv` dès validation (même si tâche non créée)
- **Auto-ajout**: Les catégories tapées lors de création/modification sont ajoutées automatiquement
- **Rafraîchissement automatique**: Les dropdowns se mettent à jour après chaque ajout
- **Cohérence garantie**: Même liste pour tâches Pomodoro, Respiratoires et Récurrentes

### Options Avancées (Phase 4)
**Section dédiée avec 3 nouvelles fonctionnalités optionnelles:**

#### 1. Pauses Cigarettes (Clopes) 🚬
- **Activation**: Checkbox "Pauses Cigarettes" + input intervalle (défaut: 120 min)
- **Comportement**: Insère automatiquement une pause cigarette (5 min) tous les X minutes
- **Comptage**: Suit la durée cumulée de TOUS les slots (Pomodoros + Respirations + Câlins)
- **Backend**: Fonction `_insert_clopes()` dans `planning_generator.py:594-651`
- **Logique**:
  - Compteur cumulatif réinitialisé après chaque insertion
  - Ajuste automatiquement les heures des slots suivants
  - Type de slot: `'clope'`

#### 2. Câlins 🤗
- **Activation**: Checkbox "Câlins (1 tous les 2 respirations)"
- **Comportement**: Insère automatiquement un câlin (10 min) tous les 2 respirations
- **Comptage**: Compteur `respiration_count` incrémenté après chaque respiration
- **Backend**: Logique intégrée dans `_generate_base_planning()` (lignes 552-588)
- **Logique**:
  - Vérification: `respiration_count % 2 == 0`
  - Insertion AVANT la respiration (pas après)
  - Type de slot: `'calin'`
- **Cas d'usage**: Alternance travail/pause avec moments de détente réguliers

#### 3. Pauses Consécutives 🔄
- **Activation**: Checkbox "Autoriser Pauses Consécutives"
- **Comportement**: Désactive l'alternance stricte Pomodoro/Pause
- **Backend**: Appel conditionnel de `repair_consecutive_work_tasks()` (lignes 228-232)
- **Logique**:
  - Si `allow_consecutive_pauses=False` (défaut): Alternance stricte forcée
  - Si `allow_consecutive_pauses=True`: Skip la réparation, permet Respiration → Respiration directement
- **Cas d'usage**: Périodes de pause prolongées (plusieurs respirations consécutives)

**Paramètres API** (`POST /api/v2/gitfocus/planning/generate-auto`):
```json
{
  "enable_clopes": false,          // Boolean
  "clopes_interval_min": 120,      // Number (30-300)
  "enable_calins": false,          // Boolean
  "allow_consecutive_pauses": false // Boolean
}
```

**Types de slots générés**:
- `'pomodoro'` - Tâche de travail (25 min)
- `'respiration'` - Tâche respiratoire (durée variable)
- `'clope'` - Pause cigarette automatique (5 min)
- `'calin'` - Pause câlin automatique (10 min)
- `'recurrent'` - Tâche récurrente
- `'planned'` - Tâche planifiée (date/heure fixe)

## Démarrage

### Méthode recommandée
```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
webapp\venv\Scripts\python.exe -m webapp.server
```

### Script start.bat
Note: Le script `scripts\start.bat` peut s'arrêter après un certain temps. Préférer la méthode directe ci-dessus.

## Modifications récentes

### 2025-11-05 - Migration CSV et Refonte Interface

#### Migration: Tâches Respiratoires → Tâches Récurrentes
**Objectif**: Simplifier l'architecture en fusionnant les deux types de tâches

**Changements**:
- ✅ 9 tâches respiratoires (R010-R029) migrées vers `TACHES_RECURRENTES.v2.csv`
- ✅ Fichier `TACHES_RESPIRATOIRES.v2.csv` supprimé (backup créé)
- ✅ Script de migration: `migrate_respiration_to_recurrent.py`
- ✅ Total: 97 tâches récurrentes (88 originales + 9 migrées)

**Note**: Le code backend n'a pas encore été refactorisé. L'API `/api/gitfocus/taches-respiratoires` continue de fonctionner en chargeant depuis le fichier récurrent.

#### Interface: Système d'Onglets
**Objectif**: Séparer visuellement les 3 types de tâches

**Changements**:
- ✅ Onglets: 🔴 Pomodoro | 🟢 Pauses | 🟣 Récurrentes
- ✅ Affichage conditionnel du contenu (un seul onglet visible à la fois)
- ✅ Les tâches récurrentes ne sont visibles QUE dans leur onglet dédié
- ✅ Styles CSS pour onglets actifs/inactifs

**Avantages**:
- Réduction du scroll vertical
- Séparation claire des types de tâches
- Interface plus organisée

#### Comportement: Mode Focus (Pas d'Insertion Automatique)
**Objectif**: Donner à l'utilisateur le contrôle total

**Changement critique** (commit 4cd7b73):
- **Avant**: Si aucune respiration sélectionnée → insertion automatique de recurrent tasks (scoring intelligent)
- **Après**: Si aucune respiration sélectionnée → **Mode Focus** (SEULEMENT Pomodoros, pas de pauses)

**Raison**: L'insertion automatique causait:
1. Planning commençant à 06:45 au lieu de l'heure choisie
2. Ajout de tâches non demandées
3. Comportement imprévisible

**Impact**:
- ✅ Contrôle total (sélection manuelle uniquement)
- ✅ Planning respecte l'heure de départ choisie
- ✅ Comportement prévisible
- ❌ Perte de l'alternance intelligente automatique

#### Améliorations Interface
**Changements multiples**:
- ✅ Input manuel pour heure de début (step=5 minutes)
- ✅ Cache busting automatique avec timestamp serveur
- ✅ Badge version serveur visible dans header (vert)
- ✅ Design compact des tâches du planning (réduction padding/marges)
- ✅ Suppression affichage scores récurrentes
- ✅ Bouton refresh régénère le planning avec nouvelle heure

**Commits**:
- `7ff2d96` - Input heure manuelle
- `037bffc` - Cache busting
- `5e5e5c4` - Badge version serveur
- `965020a` - Design compact
- `afe2887` - Suppression scores
- `627467a` - Bouton refresh
- `4cd7b73` - Désactivation fallback automatique
- `8f2a995` - Migration CSV
- `59ac245` - Système d'onglets

### 2025-11-04 - Phase 4: Options Avancées (Clopes, Câlins, Pauses Consécutives)
**Nouvelle fonctionnalité majeure: 3 options avancées pour personnaliser le planning**

**1. Pauses Cigarettes (Clopes)**
- Interface:
  - Checkbox "Pauses Cigarettes" avec input intervalle (défaut 120 min)
  - Toggle automatique pour afficher/masquer l'input intervalle
- Backend:
  - Nouvelle fonction `_insert_clopes()` (planning_generator.py:594-651)
  - Suit la durée cumulée de TOUS les slots (Pomodoros + Respirations + Câlins)
  - Insère pause cigarette (5 min) tous les X minutes (configurable: 30-300 min)
  - Ajuste automatiquement les heures des slots suivants
  - Type de slot: `'clope'`

**2. Câlins**
- Interface:
  - Checkbox "Câlins (1 tous les 2 respirations)"
- Backend:
  - Logique intégrée dans `_generate_base_planning()` (lignes 552-588)
  - Compteur `respiration_count` incrémenté après chaque respiration
  - Insertion d'un câlin (10 min) AVANT chaque 2ème respiration
  - Type de slot: `'calin'`

**3. Pauses Consécutives**
- Interface:
  - Checkbox "Autoriser Pauses Consécutives"
- Backend:
  - Modification de STEP 6 dans `generate_planning_auto()` (lignes 228-232)
  - Appel conditionnel de `repair_consecutive_work_tasks()`
  - Si activé: Skip la réparation, permet plusieurs pauses consécutives sans Pomodoros

**Paramètres API ajoutés**:
- `enable_clopes` (boolean, défaut: false)
- `clopes_interval_min` (number, défaut: 120, range: 30-300)
- `enable_calins` (boolean, défaut: false)
- `allow_consecutive_pauses` (boolean, défaut: false)

**Fichiers modifiés**:
- Frontend: `gitfocus_v2.html`, `gitfocus_v2.js`
- API: `routes_gitfocus_v2.py`
- Backend: `planning_generator.py` (3 fonctions modifiées, 1 nouvelle fonction)

**Commits**:
- `269bb7c` - Frontend et API
- `ac03199` - Backend complet
- `a6054a7` - Documentation

**Cas d'usage**:
- Clopes: Fumeurs réguliers qui ont besoin de pauses cigarettes à intervalles fixes
- Câlins: Alternance travail/pause avec moments de détente réguliers
- Pauses consécutives: Périodes de pause prolongées (méditation, exercices, etc.)

### 2025-10-30 - Fix critique: Calcul de créneaux et génération de planning
**Correction de 2 bugs majeurs empêchant l'utilisation de tout le temps disponible:**

**Bug 1: Calcul de créneaux incomplet (slot_calculator.py)**
- **Symptôme**: Planning s'arrêtait prématurément (~21h30 au lieu de minuit), seulement 6/8 Pomodoros planifiés
- **Cause racine**: Algorithme générait des créneaux alignés sur 30 min depuis 06:00, créant des trous pour fins de temps_morts non alignées (ex: 18:15)
- **Solution**: Réécriture complète avec approche "greedy" qui remplit séquentiellement tous les trous entre temps_morts
- **Résultat**: 12 créneaux consécutifs de 18:15 à minuit (au lieu de 11 avec trous)

**Code modifié (slot_calculator.py:40-104)**:
```python
# Nouvelle approche: remplir tous les "trous" entre temps_morts
# Sort temps_morts by start time
# Build blocked periods list
# Fill holes sequentially with 30-min slots
for tm_start, tm_end in blocked_periods:
    while current + timedelta(minutes=30) <= tm_start:
        free_slots.append({'heure_debut': current.strftime("%H:%M"), ...})
        current = slot_end
    current = tm_end  # Jump past temps_mort
```

**Bug 2: recalculate_times() cassait le travail du calcul de créneaux (planning_generator.py)**
- **Symptôme**: Premier slot commençait à 18:30 au lieu de 18:15 (perte de 15 min au début)
- **Cause racine**: `recalculate_times()` réécrivait toutes les heures en mode continu, effaçant le travail du calcul de créneaux
- **Solution**:
  1. Modifier `_generate_base_planning()` pour suivre le temps réel avec pointeur `current_time`
  2. Désactiver `recalculate_times()` sauf si tâches planifiées intégrées

**Code modifié (planning_generator.py:255-333)**:
```python
# Track current time instead of relying on slot indices
current_time = datetime.combine(target_date_obj, ...)

for i in range(nb_pomodoros):
    pomodoro_end = current_time + timedelta(minutes=25)
    planning.append({
        'heure_debut': current_time.strftime('%H:%M'),
        'heure_fin': pomodoro_end.strftime('%H:%M'),
        ...
    })
    current_time = pomodoro_end  # Advance time pointer
```

**Code modifié (planning_generator.py:167-172)**:
```python
# Only recalculate if we integrated planned tasks
if has_planned_tasks:
    planning = recalculate_times(planning, date, temps_morts)
else:
    logger.info("Skipping recalculate_times (times already correct)")
```

**Test validé (test_planning_generation.py)**:
- ✅ 8/8 Pomodoros planifiés (200 min) au lieu de 6/8
- ✅ Premier slot: 18:15 (au lieu de 18:30)
- ✅ Dernier slot: 23:10 (au lieu de 21:30)
- ✅ Utilisation complète du temps disponible jusqu'à minuit

**Fichiers modifiés:**
- `backend/planning_engine/slot_calculator.py` (lignes 40-136): Nouvelle logique de remplissage "greedy"
- `backend/planning_engine/planning_generator.py` (lignes 255-333): Suivi du temps réel avec pointeur
- `backend/planning_engine/planning_generator.py` (lignes 167-172): Désactivation conditionnelle de recalculate_times

**Impact utilisateur**: Le planning utilise maintenant **100% du temps disponible** jusqu'à minuit, maximisant le nombre de Pomodoros planifiés chaque jour.

### 2025-10-30 - Documentation planification partielle (multi-jours)
**Clarification importante du comportement de planification:**

Le système implémente une **planification partielle intentionnelle** - il n'est pas nécessaire que tous les Pomodoros d'une tâche soient planifiés le même jour.

**Comportement documenté:**
1. **Remplissage jusqu'à épuisement**: Le système planifie autant de Pomodoros que possible dans les créneaux disponibles (de l'heure actuelle/06h00 jusqu'à minuit)
2. **Arrêt automatique**: Lorsque tous les créneaux libres sont remplis, l'algorithme s'arrête, même si certaines tâches n'ont pas tous leurs Pomodoros planifiés
3. **Report automatique**: Le champ `remaining_min` dans LISTE_MERE.v2.csv n'est PAS modifié lors de la génération - les Pomodoros non planifiés seront automatiquement disponibles pour le planning du lendemain
4. **Gestion naturelle**: L'utilisateur génère un nouveau planning chaque jour, et le système réutilise automatiquement les tâches non terminées

**Exemple concret:**
- Tâche A: 75 min (3 Pomodoros) - Priorité 1
- Créneaux disponibles: 13 créneaux (6h30-10h40 + 18h15-minuit)
- Avec alternance Pomodoro/Récurrent: 2 créneaux par Pomodoro
- Résultat Jour 1: Seulement 3 Pomodoros planifiés (Tâche A complète)
- Résultat Jour 2: Les autres tâches seront planifiées

**Fichiers mis à jour:**
- `SPECIFICATIONS_COMPLETES_V2.md` (section ÉTAPE 4): Documentation détaillée du comportement de planification partielle
- Ajout de logs DEBUG (🔍) dans `planning_generator.py` et `routes_gitfocus_v2.py` pour tracer l'exécution

### 2025-10-30 - Fix script verify.py
**Résolution du problème de connexion lors du démarrage:**

Le script `scripts/verify.py` tentait de se connecter aux endpoints API **avant** le démarrage du serveur, causant des erreurs de connexion (HTTPConnectionPool errors).

**Solution implémentée:**
- **Mode par défaut** (pré-démarrage): Vérifie uniquement les fichiers CSV requis, ignore les endpoints API
- **Mode complet** (`--full` flag): Vérifie fichiers CSV + endpoints API (pour diagnostics post-démarrage)

**Utilisation:**
```bash
# Vérification pré-démarrage (utilisé par start.ps1)
python scripts/verify.py

# Vérification complète (serveur doit être démarré)
python scripts/verify.py --full
```

**Impact:**
- Le script `start.ps1` ne produit plus d'erreurs de connexion lors de la phase de vérification
- La vérification reste robuste avec le health check final de start.ps1 (ligne 107)

### 2025-10-29 - Système de tâches planifiées
**Nouvelle fonctionnalité d'intégration automatique:**

1. **Fichier CSV dédié** (`TACHES_PLANIFIEES.v2.csv`):
   - Format: ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;REMAINING_MIN;PRIORITY;TAGS;KEYWORDS;DEPENDENCIES;NOTES;DEADLINE;FIXED_START;PLANNED_START;STATUS
   - Colonne `PLANNED_START`: Date et heure fixe au format "DD.MM.YY HH:MM"
   - Permet de gérer des rendez-vous, événements, ou deadlines horaires

2. **Intégration automatique dans le planning** (backend):
   - Lors de la génération du planning (`POST /api/gitfocus/placer-taches`):
     - Le backend charge automatiquement les tâches planifiées pour la date cible
     - Calcule le nombre de Pomodoros nécessaires (durée ÷ 25 minutes, arrondi au supérieur)
     - Identifie les Pomodoros dans le planning générés qui sont les plus proches de l'heure planifiée
     - Remplace ces Pomodoros par la tâche planifiée
     - Marque si la tâche a été replanifiée (heure finale ≠ heure initiale)

3. **Algorithme de placement**:
   - Calcule la distance temporelle entre chaque Pomodoro généré et l'heure planifiée
   - Trie les Pomodoros par ordre croissant de distance
   - Prend les N Pomodoros les plus proches (N = nombre de Pomodoros nécessaires)
   - Conserve l'heure de début/fin des créneaux trouvés (respecte les temps_morts)

4. **Affichage dans le planning**:
   - Type: `planned` (distinct de `pomodoro`, `respiration`, `pause`)
   - Style: Fond jaune (#fef3c7), bordure orange (#f59e0b)
   - Icône: Calendrier avec coche
   - Numérotation: "(1/2)", "(2/2)" pour multi-Pomodoros
   - Badge "Replanifiée": Si `original_time` différent de `heure_debut`

5. **Routes API**:
   - `GET /api/gitfocus/taches-planifiees?date=YYYY-MM-DD` - Récupère les tâches planifiées (avec filtre par date)
   - `POST /api/gitfocus/create-planified-task` - Crée une nouvelle tâche planifiée
   - `PUT /api/gitfocus/update-planified-task/<id>` - Met à jour une tâche planifiée
   - `DELETE /api/gitfocus/delete-planified-task/<id>` - Supprime une tâche planifiée

**Architecture propre:**
- Toute la logique d'intégration est côté backend (pas de rustines JavaScript)
- Utilise les créneaux libres déjà calculés par `calculer_creneaux_libres()`
- Respecte automatiquement les temps_morts
- Garantit que les tâches planifiées sont placées au plus près de l'heure demandée

**Cas d'usage:**
- Rendez-vous médical à 14h30 (45 min) → 2 Pomodoros placés au plus près de 14h30
- Cours en ligne à 10h00 (25 min) → 1 Pomodoro placé à 10h00 si disponible
- Deadline de réunion à 16h00 mais temps_mort présent → Replanifié automatiquement avant ou après

### 2025-10-28 - Redimensionnement dynamique des sections
**Interface adaptative avec redimensionnement intelligent:**

1. **Comportement simple à 2 clics**:
   - **1er click** sur chevron: Déplie ET agrandit immédiatement (mode focus)
   - **2ème click** sur chevron: Replie et rétablit la vue normale
   - **Click sur autre section**: Bascule automatiquement le focus vers la nouvelle

2. **Mode focus agrandi**:
   - Section active: 70vh de hauteur (bordure bleue, fond surligné)
   - Panel gauche (tâches): 85% de l'espace
   - Panel droit (planning): 15% de l'espace (minimisé)
   - Autres sections: Réduites à 100px de hauteur (opacité 60%)

3. **Transitions fluides**:
   - Animations CSS de 0.4s pour tous les changements
   - Transform et opacity pour effets visuels doux
   - Grid-template-columns animé pour le redimensionnement

4. **Persistance intelligente**:
   - Variable `currentExpandedSection` suit la section agrandie
   - Click sur une autre section réinitialise automatiquement la précédente
   - Hover sur sections minimisées augmente leur opacité

**Cas d'usage:**
- Travailler intensivement sur la sélection de tâches Pomodoro
- Gérer une longue liste de tâches respiratoires
- Configurer plusieurs tâches récurrentes en même temps

### 2025-10-28 - Gestion centralisée des catégories
**Nouveau système de gestion des catégories:**

1. **Fichier centralisé** (`categories.csv`):
   - Format: `CATEGORY;SUB_CATEGORY`
   - Source unique pour toutes les catégories/sous-catégories
   - Partagé entre tâches Pomodoro, Respiratoires et Récurrentes
   - 29 combinaisons pré-remplies (7 catégories principales)

2. **Interface d'ajout rapide**:
   - Boutons "+" à côté de chaque menu déroulant catégorie/sous-catégorie
   - Modal dédié pour saisir rapidement une nouvelle combinaison
   - Mise à jour immédiate du fichier `categories.csv`
   - Rafraîchissement automatique des dropdowns après ajout

3. **Auto-complétion intelligente**:
   - Lors de création/modification de tâche, les nouvelles catégories s'ajoutent automatiquement
   - Même si la tâche n'est finalement pas créée, la catégorie reste disponible
   - Cohérence garantie entre tous les types de tâches

4. **Routes API**:
   - `GET /api/gitfocus/categories` - Récupère toutes les catégories
   - `POST /api/gitfocus/add-category` - Ajoute manuellement une catégorie/sous-catégorie

**Cas d'usage:**
- Ajouter rapidement "Études/Mathématiques" sans créer de tâche
- Préparer vos catégories avant de créer des tâches
- Maintenir une liste cohérente pour tous types de tâches

### 2025-10-27 - Système de tâches récurrentes
**Nouvelle fonctionnalité complète:**

1. **Fichier CSV dédié** (`TACHES_RECURRENTES.v2.csv`):
   - Format: ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;RECURRENCE_TYPE;RECURRENCE_INTERVAL;LAST_DONE_DATE;NEXT_DUE_DATE;PRIORITY;STATUS;IS_ACTIVE
   - 20 tâches d'exemple pré-remplies (arrosage, ménage, soins animaux, etc.)

2. **Interface utilisateur**:
   - Section repliable dédiée (fermée par défaut)
   - Toggle switch pour activer/désactiver chaque tâche
   - Modal de création/édition avec tous les champs de récurrence
   - Badges affichant le nombre total et le nombre de tâches actives
   - Boutons d'édition et de suppression

3. **Backend**:
   - Nouvelles routes API pour CRUD complet
   - Fonction toggle pour basculer l'état actif/inactif
   - Persistance automatique de l'état dans le CSV

4. **Sections repliables**:
   - Les 3 sections (Pomodoro, Respiratoires, Récurrentes) sont maintenant repliables
   - Toutes fermées par défaut pour réduire le défilement
   - Click sur l'en-tête pour ouvrir/fermer
   - Animations fluides

### 2025-10-27 - Validation des champs obligatoires
**Champs requis lors de la création/édition:**
- **Obligatoires** (avec astérisque *):
  - Titre (NAME)
  - Durée (DURATION_MIN)
  - Catégorie (CATEGORY)
  - Sous-catégorie (SUB_CATEGORY)

- **Optionnels** (peuvent être laissés vides):
  - Description
  - Priorité (valeur par défaut: 3 = Basse)
  - Deadline (format DD.MM.YY)
  - Heure de démarrage fixe (HH:MM)
  - Pour tâches respiratoires: Heures (la plus tôt, idéale, la plus tard)

**Comportement:**
- Validation frontend (HTML5) et backend (API)
- REMAINING_MIN automatiquement défini à DURATION_MIN pour les nouvelles tâches
- Priorité par défaut: P3 (Basse) si non spécifiée

### 2025-10-27 - Historique et analyse des tâches respiratoires
**Nouveau système de suivi et d'analyse:**

1. **Historique complet des planifications** (`respiration_planning_history.csv`):
   - Enregistre automatiquement chaque planification de tâche respiratoire
   - Données sauvegardées: ID, nom, date, heure planifiée, durée, timestamp d'export
   - Mode append: toutes les données sont conservées pour analyse future
   - Permet d'analyser vos habitudes: heures préférées, fréquence d'utilisation, etc.

2. **Tri par popularité** (compteur `EXPORT_COUNT`):
   - Compteur d'exports incrémenté automatiquement à chaque export CSV
   - Tri automatique: les tâches les plus utilisées apparaissent en premier
   - Facilite la sélection de vos tâches respiratoires favorites

**Cas d'usage:**
- Analyser à quelle heure vous planifiez habituellement vos pauses
- Identifier vos tâches respiratoires les plus utilisées
- Suivre l'évolution de vos habitudes de respiration/pause sur le long terme

### 2025-10-27 - Gestion complète des tâches
1. **Édition des tâches Pomodoro**:
   - Modal d'édition avec tous les champs (titre, description, durée, priorité, catégorie, sous-catégorie)
   - Champs deadline (format DD.MM.YY) et heure de démarrage fixe
   - Listes déroulantes auto-populées pour catégories/sous-catégories
   - Bouton de suppression intégré

2. **Création de tâches Pomodoro**:
   - Bouton "Nouvelle tâche" dans l'en-tête de la liste
   - Génération automatique d'ID séquentiel
   - Enregistrement direct dans LISTE_MERE.v2.csv

3. **Gestion des tâches respiratoires**:
   - Modal dédié pour créer/éditer les tâches respiratoires
   - Champs spécifiques: heure la plus tôt, idéale, la plus tard
   - Génération d'ID au format R_001, R_002, etc.
   - Boutons d'édition et de création

4. **Nouvelles routes API**:
   - `POST /api/gitfocus/create-task` - Créer tâche Pomodoro
   - `DELETE /api/gitfocus/delete-task/<id>` - Supprimer tâche Pomodoro
   - `POST /api/gitfocus/create-respiration-task` - Créer tâche respiratoire
   - `PUT /api/gitfocus/update-respiration-task/<id>` - Modifier tâche respiratoire
   - `DELETE /api/gitfocus/delete-respiration-task/<id>` - Supprimer tâche respiratoire

5. **Améliorations précédentes**:
   - Format dates temps_morts.csv: Support format ISO (YYYY-MM-DD) + DD.MM.YY
   - Calcul temps libre: Filtre créneaux passés + ajuste créneau en cours
   - Export CSV: Téléchargement client avec colonne KIND

## Troubleshooting

### Problèmes courants
- **Cache navigateur**: Faire Ctrl+F5 pour forcer le rechargement
- **Temps morts non affichés**: Vérifier le format de date dans temps_morts.csv
- **Export ne télécharge pas**: Vérifier que le JavaScript est bien rechargé (Ctrl+F5)
- **start.ps1 affiche erreurs de connexion**: ✅ **RÉSOLU (2025-10-30)** - Le script verify.py a été corrigé pour ne plus tenter de connexion avant le démarrage du serveur

## API Endpoints

### Lecture
- `GET /api/gitfocus/liste-mere` - Liste des tâches principales
- `GET /api/gitfocus/taches-respiratoires` - Tâches de respiration
- `GET /api/gitfocus/creneaux-libres?date=YYYY-MM-DD` - Créneaux libres pour une date

### Planification
- `POST /api/gitfocus/placer-taches` - Génère le planning
- `POST /api/gitfocus/export-planning` - Télécharge le CSV

### Tâches Pomodoro
- `POST /api/gitfocus/create-task` - Crée une nouvelle tâche
- `PUT /api/gitfocus/update-task/<task_id>` - Met à jour une tâche
- `DELETE /api/gitfocus/delete-task/<task_id>` - Supprime une tâche

### Tâches Respiratoires
- `POST /api/gitfocus/create-respiration-task` - Crée une tâche respiratoire
- `PUT /api/gitfocus/update-respiration-task/<task_id>` - Met à jour une tâche respiratoire
- `DELETE /api/gitfocus/delete-respiration-task/<task_id>` - Supprime une tâche respiratoire

### Tâches Récurrentes
- `GET /api/gitfocus/taches-recurrentes` - Liste des tâches récurrentes
- `POST /api/gitfocus/create-recurrent-task` - Crée une tâche récurrente
- `PUT /api/gitfocus/update-recurrent-task/<task_id>` - Met à jour une tâche récurrente
- `DELETE /api/gitfocus/delete-recurrent-task/<task_id>` - Supprime une tâche récurrente
- `PATCH /api/gitfocus/toggle-recurrent-task/<task_id>` - Bascule l'état actif/inactif

### Tâches Planifiées
- `GET /api/gitfocus/taches-planifiees?date=YYYY-MM-DD` - Liste des tâches planifiées (filtrables par date)
- `POST /api/gitfocus/create-planified-task` - Crée une tâche planifiée
- `PUT /api/gitfocus/update-planified-task/<task_id>` - Met à jour une tâche planifiée
- `DELETE /api/gitfocus/delete-planified-task/<task_id>` - Supprime une tâche planifiée

**Note**: L'intégration des tâches planifiées se fait automatiquement via `POST /api/gitfocus/placer-taches` (pas de route dédiée nécessaire)
