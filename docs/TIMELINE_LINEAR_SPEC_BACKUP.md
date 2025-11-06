# Spécification - Timeline Linéaire (Nouvelle Logique)

**Date**: 2025-11-01
**Version**: 2.0
**Statut**: Documentation du système qui a été accidentellement supprimé lors du nettoyage

---

## 🎯 Vue d'ensemble

La **timeline linéaire** est le système de planification NEW qui devait remplacer l'ancien "planning intelligent". Au lieu de manipuler des chaînes de date/heure complexes, elle utilise un **système de minutes depuis le début du planning**.

### Concept Central

```
Timeline = Axe linéaire en minutes depuis planningStartTime
  │
  ├─ 0 min ────→ planningStartTime (ex: 2025-11-01 14:00)
  ├─ 30 min ───→ 14:30
  ├─ 150 min ──→ 16:30
  ├─ 720 min ──→ 02:00 (jour suivant)
  └─ ...
```

**Avantages**:
- Arithmétique simple (minutes entières au lieu de parsing de dates)
- Supporte les plannings multi-jours naturellement
- Placement de tâches = trouver un slot libre sur l'axe linéaire

---

## 📊 Structure de Données

### State Object (JavaScript)

```javascript
const state = {
    // Planning start time (paramétrable par utilisateur)
    planningStartTime: Date,        // Ex: 2025-11-01T14:00:00
    planningStartLocked: boolean,   // Si true, utilisateur ne peut pas changer l'heure

    // Timeline linéaire
    timeline: {
        // Tâches placées sur la timeline
        tasks: [
            {
                minuteOffset: number,      // Minutes depuis planningStartTime
                duration: number,          // Durée en minutes
                type: string,              // 'FIXED', 'PLANNED', 'POMODORO', 'RESPIRATION'
                taskId: string,            // ID de la tâche source
                taskName: string,          // Nom affiché
                isFixed: boolean,          // Si true, non déplaçable
                pomodoroIndex: number,     // (POMODORO uniquement) 1, 2, 3...
                pomodoroTotal: number,     // (POMODORO uniquement) Total de pomodoros
                originalFixedTime: number, // (FIXED uniquement) Heure demandée originale
                originalPlannedTime: number // (PLANNED uniquement) Heure préférée originale
            }
        ],

        // Obstacles (temps morts convertis)
        obstacles: [
            {
                startMinute: number,       // Début de l'obstacle (minutes depuis planningStartTime)
                endMinute: number,         // Fin de l'obstacle
                type: string,              // 'temps_mort'
                originalData: object       // Données CSV originales {date, heure_debut, heure_fin, titre}
            }
        ]
    }
}
```

---

## 🔧 Fonctions de Conversion

### `dateTimeToMinutes(dateTime, planningStart)`

Convertit une Date JavaScript en minutes depuis le début du planning.

```javascript
// Exemple
const planningStart = new Date('2025-11-01T14:00:00');
const someTime = new Date('2025-11-01T16:30:00');
const minutes = dateTimeToMinutes(someTime, planningStart);
// Résultat: 150 (2h30 = 150 minutes)
```

**Calcul**: `Math.floor((dateTime - planningStart) / 60000)`

**Supporte les jours suivants**:
```javascript
const nextDay = new Date('2025-11-02T02:00:00');
const minutes = dateTimeToMinutes(nextDay, planningStart);
// Résultat: 720 (14:00 → 02:00 = 12h = 720 minutes)
```

### `minutesToDateTime(minutes, planningStart)`

Conversion inverse: minutes → {date, time}

```javascript
const result = minutesToDateTime(150, planningStart);
// Résultat: {date: '2025-11-01', time: '16:30'}
```

### `convertTempsMortsToLinear(tempsMorts, planningStart)`

Convertit le CSV `temps_morts.csv` en obstacles sur la timeline.

**Entrée** (CSV):
```csv
DATE;HEURE_DEBUT;HEURE_FIN;TYPE;TITRE
2025-11-01;00:00;06:30;dodo;dodo
2025-11-01;16:30;17:30;bain;bain
```

**Sortie** (obstacles):
```javascript
[
    {
        startMinute: -840,  // 00:00 = 14h avant planningStart (14:00)
        endMinute: -450,    // 06:30
        type: 'temps_mort',
        originalData: {date: '2025-11-01', heure_debut: '00:00', ...}
    },
    {
        startMinute: 150,   // 16:30 = 2h30 après planningStart
        endMinute: 210,     // 17:30
        type: 'temps_mort',
        originalData: {date: '2025-11-01', heure_debut: '16:30', ...}
    }
]
```

**Filtrage**:
- Ignore les temps morts complètement passés (endMinute < 0)
- Ignore les temps morts trop loin dans le futur (> 30 jours = 43200 minutes)

---

## 🚀 Initialisation du Planning

### Étape 1: `initializePlanningStart()`

**Logique**:
1. Calculer `now + 15 minutes`
2. Arrondir au prochain multiple de 5 minutes
3. Stocker dans `state.planningStartTime`

**Exemple**:
```
Heure actuelle: 13:42
+ 15 min: 13:57
Arrondi à 5min: 14:00
→ planningStartTime = 2025-11-01T14:00:00
```

### Étape 2: `initializeTimelineObstacles()`

**Logique**:
1. Charger `temps_morts.csv` pour la date actuelle + 2 jours suivants (multi-day support)
2. Appeler `convertTempsMortsToLinear(state.tempsMorts, state.planningStartTime)`
3. Stocker dans `state.timeline.obstacles`

### Étape 3: Placement des tâches FIXED et PLANNED

**Ordre de priorité**:
1. Tâches **FIXED** d'abord (fixes, non déplaçables)
2. Tâches **PLANNED** ensuite (flexibles)
3. Utilisateur ajoute manuellement **POMODORO** et **RESPIRATION** après

---

## 📍 Algorithme de Placement

### `findNextFreeSlot(startMinute, durationMinutes, timeline)`

**Objectif**: Trouver le prochain créneau libre qui ne chevauche ni obstacles ni tâches FIXED/PLANNED.

**Paramètres**:
- `startMinute`: Position de départ souhaitée (minutes depuis planningStart)
- `durationMinutes`: Durée de la tâche à placer
- `timeline`: {tasks: [], obstacles: []}

**Retour**:
- `number`: Position (minuteOffset) du prochain créneau libre
- `null`: Aucun créneau trouvé dans la limite de recherche (30 jours)

**Algorithme**:

```
candidateStart = startMinute
TANT QUE candidateStart < 30 jours:
    candidateEnd = candidateStart + durationMinutes

    POUR chaque obstacle dans timeline.obstacles:
        SI [candidateStart, candidateEnd] chevauche obstacle:
            jumpTo = obstacle.endMinute
            CONTINUER

    POUR chaque task FIXED ou PLANNED dans timeline.tasks:
        SI [candidateStart, candidateEnd] chevauche task:
            jumpTo = task.minuteOffset + task.duration
            CONTINUER

    SI aucun chevauchement:
        RETOURNER candidateStart

    candidateStart = jumpTo

RETOURNER null (pas de slot trouvé)
```

**Détection de chevauchement**:

Deux intervalles [A_start, A_end] et [B_start, B_end] se chevauchent si:
1. `A_start >= B_start AND A_start < B_end` (A démarre dans B)
2. `A_end > B_start AND A_end <= B_end` (A finit dans B)
3. `A_start < B_start AND A_end > B_end` (A contient B)

---

## 🎨 Types de Tâches et Placement

### 1. Tâches FIXED (RDV fixes)

**Source**: `TACHES_PLANIFIEES.v2.csv` avec `FIXED_START` rempli

**Fonction**: `addFixedTaskToPlanning(fixedTask)`

**Comportement**:
1. Convertir `fixed_start` en `minuteOffset`
2. Vérifier si conflit avec un **obstacle (temps_mort uniquement)**
3. Si conflit détecté:
   - Essayer de placer **AVANT** le temps mort (si espace suffisant)
   - Sinon placer **APRÈS** le temps mort
   - Ajouter `"(fixed HH:MM, conflit)"` au nom de la tâche
4. Placer la tâche à `minuteOffset` calculé

**Propriétés**:
- `type: 'FIXED'`
- `isFixed: true` (non déplaçable par drag & drop)
- **ÉCRASE** les tâches PLANNED/POMODORO/RESPIRATION (pas les obstacles)

**Exemple**:

```javascript
// Tâche FIXED demandée à 15:00 (minuteOffset = 60)
// Obstacle (bain) existe à [60, 90] (15:00-15:30)

Résultat:
- Si espace avant: placer à minuteOffset = 30 (14:30-15:00)
- Sinon: placer à minuteOffset = 90 (15:30-16:00)
- Nom: "RDV dentiste (fixed 15:00, conflit)"
```

### 2. Tâches PLANNED (Tâches flexibles)

**Source**: `TACHES_PLANIFIEES.v2.csv` avec `PLANNED_START` rempli

**Fonction**: `addPlannedTaskToPlanning(plannedTask)`

**Comportement**:
1. Convertir `planned_start` en `preferredMinute`
2. Appeler `findNextFreeSlot(preferredMinute, duration, timeline)`
3. Placer à la position retournée (peut être différente de `preferredMinute`)
4. Stocker `originalPlannedTime` pour affichage

**Propriétés**:
- `type: 'PLANNED'`
- `isFixed: false`
- **Peut être poussée** par FIXED et obstacles
- **Bloque** les tâches suivantes (POMODORO/RESPIRATION)

**Exemple**:

```javascript
// Tâche PLANNED préférée à 14:30 (minuteOffset = 30), durée 60 min
// Obstacle existe à [30, 60] (14:30-15:00)

Résultat via findNextFreeSlot:
- Placement effectif: minuteOffset = 60 (15:00-16:00)
- originalPlannedTime = 30 (mémorisé pour affichage)
- Affichage: "⚠️ Décalée de 14:30 → 15:00"
```

### 3. Tâches POMODORO (Travail)

**Source**: Utilisateur clique sur une tâche dans `LISTE_MERE.v2.csv`

**Fonction**: `addWorkTaskToPlanning(workTask, startMinute)`

**Comportement**:
1. Utiliser `remaining_min` (pas `duration_min`)
2. Découper en pomodoros de 25 minutes
3. Placer chaque pomodoro via `findNextFreeSlot()`
4. Si échec de placement: **ROLLBACK** (supprimer les pomodoros déjà placés)

**Propriétés**:
- `type: 'POMODORO'`
- `isFixed: false`
- `pomodoroIndex: 1, 2, 3...`
- `pomodoroTotal: N`

**Exemple**:

```javascript
// Tâche de 75 minutes → 3 pomodoros (25 + 25 + 25)
// startMinute = 0 (début du planning)

Placement:
1. Pomodoro 1: findNextFreeSlot(0, 25) → 0-25
2. Pomodoro 2: findNextFreeSlot(25, 25) → 25-50
3. Pomodoro 3: findNextFreeSlot(50, 25) → 50-75

Résultat:
- 3 tâches dans timeline.tasks
- Affichage: "Tâche X (1/3)", "Tâche X (2/3)", "Tâche X (3/3)"
```

### 4. Tâches RESPIRATION (Récurrentes)

**Source**: Utilisateur clique sur une tâche dans `TACHES_RECURRENTES.v2.csv`

**Fonction**: `sendRespirationsToPlanning()` (Nouvelle architecture 2-step)

**Comportement**:
1. **ÉTAPE 1 - ORDERING** (Construction de la liste ordonnée):
   - Récupérer tous les Pomodoros de la timeline
   - Pour chaque Pomodoro, ajouter une Respiration après
   - **LOOPING**: Si plus de Pomodoros que de respirations sélectionnées, réutiliser les respirations via modulo `respirationIndex % state.respirationStaging.length`
   - Construire la liste avec `minuteOffset: 0` (placeholders)

2. **ÉTAPE 2 - TIME CALCULATION**:
   - Appeler `rebuildTimeline()` pour recalculer tous les minuteOffsets
   - rebuildTimeline() parcourt séquentiellement et respecte les obstacles

**Propriétés**:
- `type: 'RESPIRATION'`
- `isFixed: false`
- **Alternance garantie par construction** (Pomo → Resp → Pomo → Resp)
- **Catégories considérées comme PAUSE**: RESPIRATION, RECURRENT, CLOPE, CALIN

**Exemple avec looping**:
```javascript
// 81 Pomodoros + 3 respirations sélectionnées ["R_001", "R_005", "R_012"]
// Résultat: 81 respirations placées (27 fois chaque respiration)
// Pomo 1 → R_001
// Pomo 2 → R_005
// Pomo 3 → R_012
// Pomo 4 → R_001 (loop)
// Pomo 5 → R_005 (loop)
// ...
```

---

## 🏗️ Architecture 2-Step (Nouvelle - 2025-11-04)

### Principe Central

**RÈGLE D'OR**: À chaque modification de la timeline, séparer ORDERING et TIME CALCULATION.

```
Modification de timeline
    ↓
ÉTAPE 1: ORDERING
    - Construire liste ordonnée (tasks dans le bon ordre)
    - Respecter alternance TRAVAIL/PAUSE
    - Pas de minuteOffset (ou minuteOffset = 0)
    ↓
ÉTAPE 2: TIME CALCULATION
    - Appeler rebuildTimeline()
    - Calculer minuteOffset séquentiellement
    - Respecter obstacles (temps_morts)
    ↓
Résultat: timeline.tasks avec minuteOffsets corrects
```

### `rebuildTimeline()` - Fonction Centrale

**Objectif**: Recalculer TOUS les minuteOffsets après modification de l'ordre.

**Algorithme**:
```javascript
function rebuildTimeline() {
    // ÉTAPE 1: Build ORDERED list (preserve current order)
    const sortedTasks = [...state.timeline.tasks].sort((a, b) => a.minuteOffset - b.minuteOffset);

    const orderedTasks = sortedTasks.map(task => ({
        duration: task.duration,
        type: task.type,
        taskId: task.taskId,
        taskName: task.taskName,
        isFixed: task.isFixed || false,
        autoGenerated: task.autoGenerated || false
    }));

    // ÉTAPE 2: Calculate minuteOffset for each task
    let currentMinute = state.planningStartTime ?
        (state.planningStartTime.getHours() * 60 + state.planningStartTime.getMinutes()) : 0;

    for (const task of orderedTasks) {
        // Skip obstacles (temps_morts)
        let skipObstacle = true;
        while (skipObstacle) {
            skipObstacle = false;

            for (const obstacle of state.timeline.obstacles) {
                const taskEnd = currentMinute + task.duration;

                // Check overlap: currentMinute < obstacle.endMinute AND taskEnd > obstacle.startMinute
                if (currentMinute < obstacle.endMinute && taskEnd > obstacle.startMinute) {
                    console.log(`  Skipping obstacle ${obstacle.startMinute}-${obstacle.endMinute}`);
                    currentMinute = obstacle.endMinute;
                    skipObstacle = true;
                    break;
                }
            }
        }

        // Assign time
        task.minuteOffset = currentMinute;
        currentMinute += task.duration;
    }

    // Replace timeline
    state.timeline.tasks = orderedTasks;
}
```

### Fonctions Utilisant rebuildTimeline()

**TOUTES ces fonctions DOIVENT appeler rebuildTimeline() après modification**:

1. `sendRespirationsToPlanning()` ✅ (déjà implémenté)
2. `addWorkTaskToPlanning()` ⏳ (à modifier)
3. `handleDeleteSlot()` ⏳ (à modifier)
4. `toggleTaskSelection()` ⏳ (à modifier)
5. Handlers drag & drop ⏳ (à implémenter)

**Pattern à suivre**:
```javascript
function anyTimelineModification() {
    // 1. Modify state.timeline.tasks (add/remove/reorder)
    state.timeline.tasks.push(newTask);  // Example

    // 2. Call central rebuild
    rebuildTimeline();

    // 3. Refresh display
    refreshPlanningDisplay();
}
```

---

## 🖼️ Affichage et Export

### `convertTimelineToDisplayFormat()`

**Objectif**: Convertir la timeline linéaire en format affichable (date + heure).

**Processus**:

1. **Convertir tasks**:
```javascript
POUR chaque task dans timeline.tasks:
    startDateTime = minutesToDateTime(task.minuteOffset, planningStartTime)
    endDateTime = minutesToDateTime(task.minuteOffset + task.duration, planningStartTime)

    displaySlot = {
        date: startDateTime.date,           // "2025-11-01"
        heure_debut: startDateTime.time,    // "14:30"
        heure_fin: endDateTime.time,        // "15:00"
        task_name: task.taskName,
        type: task.type.toLowerCase(),      // "pomodoro", "planned", "respiration"
        duration_min: task.duration
    }
```

2. **Convertir obstacles**:
```javascript
POUR chaque obstacle dans timeline.obstacles:
    startDateTime = minutesToDateTime(obstacle.startMinute, planningStartTime)
    endDateTime = minutesToDateTime(obstacle.endMinute, planningStartTime)

    displaySlot = {
        date: startDateTime.date,
        heure_debut: startDateTime.time,
        heure_fin: endDateTime.time,
        task_name: obstacle.originalData.titre,
        type: 'temps_mort',  // Affiché en gris dans le CSS
        duration_min: obstacle.endMinute - obstacle.startMinute
    }
```

3. **Trier par date + heure**
4. **Calculer statistiques**:
   - `work_minutes`: Somme des durées (POMODORO + FIXED + PLANNED)
   - `pause_minutes`: Somme des durées (RESPIRATION)
   - `total_slots`: Nombre de tâches

### Export CSV

**Format**: `ID;NAME;DURATION_MIN;KIND`

```javascript
POUR chaque displaySlot:
    csvRow = {
        ID: task.taskId,
        NAME: task.taskName,
        DURATION_MIN: task.duration,
        KIND: task.type  // 'POMODORO', 'PLANNED', 'RESPIRATION', 'temps_mort'
    }
```

---

## 🔄 Que se passe-t-il quand on déplace une tâche ?

**Note**: Cette fonctionnalité n'était pas complètement implémentée dans le backup, mais voici la logique prévue.

### Drag & Drop (Prévu mais non implémenté)

**Comportement attendu**:

1. **Utilisateur fait glisser une tâche**:
   - Capturer `minuteOffset` de destination
   - Vérifier si le nouveau slot est libre (appeler `findNextFreeSlot`)
   - Si libre: mettre à jour `task.minuteOffset`
   - Si occupé: afficher erreur ou snapping au prochain slot libre

2. **Tâches FIXED ne peuvent pas être déplacées**:
   - Vérifier `task.isFixed === true`
   - Si true: bloquer le drag & drop

3. **Décalage en cascade** (optionnel):
   - Si déplacement d'une tâche PLANNED crée un trou
   - Déplacer automatiquement les tâches suivantes vers le haut

**Implémentation non trouvée dans le backup** → Fonctionnalité à implémenter.

---

## 🧪 Tests Unitaires

Le backup contient des fonctions de test complètes:

### `testConversionFunctions()`

Tests de:
- `dateTimeToMinutes()` (même jour)
- `dateTimeToMinutes()` (jour suivant)
- `minutesToDateTime()` (conversion inverse)
- `convertTempsMortsToLinear()` (obstacles)

### `testInitialization()`

Tests de:
- `initializePlanningStart()` (arrondi à 5min)
- `initializeTimelineObstacles()` (chargement obstacles)

### `testTaskPlacement()`

Tests de:
- `findNextFreeSlot()` (sans obstacle)
- `findNextFreeSlot()` (avec obstacle)
- `addWorkTaskToPlanning()` (découpage en pomodoros)
- `addRecurrentTaskToPlanning()` (placement simple)
- `addFixedTaskToPlanning()` (gestion conflits)

### `testDisplayConversion()`

Tests de:
- `convertTimelineToDisplayFormat()` (conversion complète)
- Statistiques calculées
- Tri chronologique

**Exécution**: Ouvrir console navigateur → `testConversionFunctions()`, etc.

---

## 📝 Récapitulatif

### Ce qui a été supprimé par erreur

Lors du nettoyage, **TOUTES** les fonctions suivantes ont été supprimées alors qu'elles auraient dû être conservées:

**Conversion**:
- `dateTimeToMinutes()`
- `minutesToDateTime()`
- `convertTempsMortsToLinear()`

**Initialisation**:
- `initializePlanningStart()`
- `initializeTimelineObstacles()`

**Placement**:
- `findNextFreeSlot()`
- `addWorkTaskToPlanning()`
- `addRecurrentTaskToPlanning()`
- `addFixedTaskToPlanning()`
- `addPlannedTaskToPlanning()`

**Affichage**:
- `convertTimelineToDisplayFormat()`
- `calculateStatsFromTimeline()`
- `refreshPlanningDisplay()`

**Tests**:
- `testConversionFunctions()`
- `testInitialization()`
- `testTaskPlacement()`
- `testDisplayConversion()`

**Handlers**:
- `generatePlanning()` (version NEW avec timeline)
- `handleDeleteSlot()` (suppression de tâche du planning)

### Ce qui doit être conservé

**CRUD Tasks** (déjà nettoyé, OK):
- `loadPomodoroTasks()`, `loadRecurrentTasks()`
- `editPomodoroTask()`, `editRecurrentTask()`
- `deletePomodoroTask()`, `deleteRecurrentTask()`
- `undoDeletePomodoroTask()`, `undoDeleteRecurrentTask()`
- Modals de création/édition

**Nouvelle timeline** (à restaurer):
- Toutes les fonctions listées ci-dessus

---

## 🎯 Action Requise

**Option 1: Restaurer depuis le backup**

Copier depuis `gitfocus_v2.js.cleaned` toutes les fonctions timeline listées ci-dessus.

**Option 2: Refonte propre**

Réécrire les fonctions timeline en suivant cette spec, en TypeScript si possible, avec:
- Interfaces claires pour `Task`, `Obstacle`, `Timeline`
- Tests unitaires Jest/Vitest
- Documentation JSDoc complète

---

**Fin de la spécification**
