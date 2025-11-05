# Flux de Génération du Planning - Système Linéaire

**Date**: 2025-11-05
**Version**: 2.0 (Refonte complète avec système de temps relatif)

---

## 🎯 PRINCIPE FONDAMENTAL

Le système utilise un **modèle de temps RELATIF** :
- **Point zéro absolu** = `planningStartTime` (heure calculée au chargement de la page, maintenant + 15 minutes arrondi à 5 minutes
- L'utlilisateur a un champ ou il peut forcer une autre heure de départ, par exemple s'il établit le planning du lendemain
- Toutes les durées sont exprimées en **minutes RELATIVES** à ce point
- Conversion en heures absolues UNIQUEMENT lors de l'insertion finale dans le planning

---

## 📋 FLUX COMPLET - 12 ÉTAPES

### ÉTAPE 1 : Calcul de l'heure de départ (DOMContentLoaded)

**Déclencheur** : Chargement de la page (`DOMContentLoaded`)

**Algorithme** :
```javascript
1. Récupérer l'heure actuelle
2. Ajouter 15 minutes
3. Arrondir au multiple de 5 SUPÉRIEUR

Exemple : 13:07 → 13:22 → 13:25
```

**Résultat** : Variable `planningStartTime` (format HH:MM, ex: "13:25"), modifiable par l'utilisateur avec une boite de dialogue rapide

**Point zéro** : Cette heure devient la minute 0 du système relatif

---

### ÉTAPE 2 : Initialisation du système de temps relatif

**Concept** :
- `planningStartTime = 13:25` → minute 0
- Toute tâche ajoutée sera positionnée en minutes relatives
- Exemple : Pomodoro à la minute 30 = 13:55 en temps absolu

**Avantages** :
- Calculs simples (additions de durées)
- Pas de gestion complexe des heures
- Conversion finale en une seule passe

---

### ÉTAPE 3 : Ajout des tâches de travail (Pomodoros)

**Source** : Tâches sélectionnées par l'utilisateur (checkboxes onglet Pomodoro)

**Format de sortie** :
```javascript
taskList = [
  {type: 'pomodoro', name: 'Révision maths', duration: 75, task_id: 'TASK001'},
  {type: 'pomodoro', name: 'Rapport projet', duration: 50, task_id: 'TASK002'},
  {type: 'pomodoro', name: 'Lecture doc', duration: 25, task_id: 'TASK003'}
]
```

**Conversion en Pomodoros** :
- 1 Pomodoro = 25 minutes
- Tâche de 75 min = 3 Pomodoros
- si tache 80 minutes, 4 pomodoros de 25 minutes
- Chaque Pomodoro garde le même `task_id` et `name`


**Résultat** :
```javascript
pomodoroList = [
  {type: 'pomodoro', name: 'Révision maths', duration: 25, task_id: 'TASK001'},
  {type: 'pomodoro', name: 'Révision maths', duration: 25, task_id: 'TASK001'},
  {type: 'pomodoro', name: 'Révision maths', duration: 25, task_id: 'TASK001'},
  {type: 'pomodoro', name: 'Rapport projet', duration: 25, task_id: 'TASK002'},
  {type: 'pomodoro', name: 'Rapport projet', duration: 25, task_id: 'TASK002'},
  {type: 'pomodoro', name: 'Lecture doc', duration: 25, task_id: 'TASK003'}
]
```

---

### ÉTAPE 4 : Ajout des respirations

**Source** : Tâches sélectionnées par l'utilisateur (onglet Pauses, avec compteurs x2, x3...)
quand on entre dans l'onglet Pauses, on voit la liste des taches récurrentes sélectionnées à droite et la liste source des taches récurrentes à gauche
Les taches peuvent etre déplacées par drag ou supprimées
Un bouton envoyer vers le planning ajoute toutes ces pauses à la timeline qui compte le temps depuis le point zéro

**Format de sortie** :
```javascript
respirationList = [
  {type: 'respiration', name: 'Méditation', duration: 10, task_id: 'R010'},
  {type: 'respiration', name: 'Respiration profonde', duration: 5, task_id: 'R018'},
  {type: 'respiration', name: 'Respiration profonde', duration: 5, task_id: 'R018'}, // Duplicata
  {type: 'respiration', name: 'Marche rapide', duration: 15, task_id: 'R022'}
]
```

**Note** : Les duplicatas sont PRÉSERVÉS (sélection multiple autorisée)

**Cas particulier** : Si aucune respiration sélectionnée → `respirationList = []`

---

### ÉTAPE 5 : Alternance Pomodoro/Respiration

**Algorithme** :

**CAS A : Respirations sélectionnées** (liste non vide)
```javascript
alternatedList = []
respirationIndex = 0

for (let i = 0; i < pomodoroList.length; i++) {
  // Ajoute Pomodoro
  alternatedList.push(pomodoroList[i])

  // Ajoute Respiration (cycling)
  alternatedList.push(respirationList[respirationIndex])
  respirationIndex = (respirationIndex + 1) % respirationList.length // Retour au début
}
```

**Résultat exemple** :
```
Pomodoro 1 (Révision maths, 25 min)
Respiration 1 (Méditation, 10 min)
Pomodoro 2 (Révision maths, 25 min)
Respiration 2 (Respiration profonde, 5 min)
Pomodoro 3 (Révision maths, 25 min)
Respiration 3 (Respiration profonde, 5 min) [duplicata]
Pomodoro 4 (Rapport projet, 25 min)
Respiration 4 (Marche rapide, 15 min)
Pomodoro 5 (Rapport projet, 25 min)
Respiration 1 (Méditation, 10 min) [cycle recommence]
...
```

**CAS B : Aucune respiration** (Mode Focus)
```javascript
alternatedList = pomodoroList // Seulement les Pomodoros
```

**CAS C : Option "Pauses consécutives" cochée + Aucun Pomodoro**
```javascript
alternatedList = respirationList // Seulement les respirations (journée de ménage)
```

---

### ÉTAPE 6 : Insertion des câlins (si option cochée)

**Condition** : Checkbox "Câlins" cochée

**Règle** : 1 câlin tous les 2 respirations

**Algorithme** :
```javascript
respirationCount = 0

for (let i = 0; i < alternatedList.length; i++) {
  if (alternatedList[i].type === 'respiration') {
    respirationCount++

    if (respirationCount % 2 === 0) {
      // Insère câlin AVANT cette respiration
      alternatedList.splice(i, 0, {
        type: 'calin',
        name: 'Câlin',
        duration: 10
      })
      i++ // Ajuste l'index après insertion
    }
  }
}
```

**Résultat exemple** :
```
Pomodoro 1
Respiration 1
Pomodoro 2
Câlin (10 min) ← Inséré AVANT respiration 2
Respiration 2
Pomodoro 3
Respiration 3
Pomodoro 4
Câlin (10 min) ← Inséré AVANT respiration 4
Respiration 4
```

---

### ÉTAPE 7 : Insertion des clopes (si option cochée)

**Interface** :
- Checkbox "Pauses cigarettes"
- Input "Intervalle" (défaut: 120 minutes, modifiable)
- **Persistance serveur** : La valeur modifiée est sauvegardée et restaurée (même sur navigateur distant)

**Règle** : 1 clope tous les X minutes de travail cumulé (Pomodoros + Respirations + Câlins)

**Algorithme** :
```javascript
cumulativeDuration = 0
clopesInterval = 120 // Ou valeur sauvegardée sur le serveur

for (let i = 0; i < alternatedList.length; i++) {
  cumulativeDuration += alternatedList[i].duration

  if (cumulativeDuration >= clopesInterval) {
    // Insère clope APRÈS cette tâche
    alternatedList.splice(i + 1, 0, {
      type: 'clope',
      name: 'Pause cigarette',
      duration: 5
    })

    // Réinitialise compteur
    cumulativeDuration = 0

    i++ // Ajuste l'index après insertion
  }
}
```

**Résultat exemple** (intervalle = 120 min) :
```
Pomodoro 1 (25) → cumul = 25
Respiration 1 (10) → cumul = 35
Pomodoro 2 (25) → cumul = 60
Câlin (10) → cumul = 70
Respiration 2 (5) → cumul = 75
Pomodoro 3 (25) → cumul = 100
Respiration 3 (5) → cumul = 105
Pomodoro 4 (25) → cumul = 130 ≥ 120 !
Clope (5) ← Insérée, cumul réinitialisé à 0
Respiration 4 (15) → cumul = 15
...
```

**Note** : Les clopes peuvent décaler légèrement les câlins, c'est accepté.

---

### ÉTAPE 8 : Chargement temps_morts (CSV)

**Fichier** : `prod_data/temps_morts.csv`

**Format** :
```csv
"DATE";"HEURE DEBUT";"HEURE FIN";"TITRE"
"2025-11-05";"14:00";"15:00";"RDV médical"
"2025-11-05";"12:00";"13:00";"Déjeuner"
```

**Filtre** : Charger UNIQUEMENT les temps_morts pour la date sélectionnée

**Conversion en temps relatif** :
```javascript
// planningStartTime = "10:00" (minute 0)
tempsMorts = [
  {debut_relatif: 120, fin_relatif: 180, titre: "RDV médical"}, // 14:00-15:00 → 120-180 min
  {debut_relatif: 60, fin_relatif: 120, titre: "Déjeuner"}      // 12:00-13:00 → 60-120 min
]
```

**Tri** : Par ordre croissant de `debut_relatif`

**Important** : Les temps_morts sont chargés mais **PAS encore insérés** dans le planning

---

### ÉTAPE 9 : Chargement tâches planifiées (CSV)

**Fichier** : `prod_data/TACHES_PLANIFIEES.v2.csv`

**Format** :
```csv
"ID";"NAME";"DURATION_MIN";"PLANNED_START";...
"PLAN001";"Cours en ligne";"45";"05.11.25 15:00"
"PLAN002";"Réunion équipe";"30";"05.11.25 10:30"
```

**Filtre** : Charger UNIQUEMENT les tâches pour la date sélectionnée

**Conversion en temps relatif** :
```javascript
// planningStartTime = "10:00" (minute 0)
tachesPlannifiees = [
  {id: 'PLAN001', name: 'Cours en ligne', duration: 45, debut_relatif: 300}, // 15:00 → 300 min
  {id: 'PLAN002', name: 'Réunion équipe', duration: 30, debut_relatif: 30}   // 10:30 → 30 min
]
```

**Tri** : Par ordre croissant de `debut_relatif`

**Important** : Les tâches planifiées sont chargées mais **PAS encore insérées** dans le planning

---

### ÉTAPE 10 : Conversion de la timeline en planning avec heures réelles

**PRINCIPE CLÉS** :
- La `alternatedList` contient des tâches **SANS heures** (juste nom + durée)
- On parcourt cette liste **UNE SEULE FOIS, dans l'ordre**
- On calcule les heures en **ajoutant séquentiellement** les durées
- On gère les collisions avec temps_morts au fur et à mesure

**Algorithme détaillé** :

```javascript
planning = []
currentTime = 0 // Minute relative (0 = planningStartTime)
tempsMortsIndex = 0
tachesPlannifieesIndex = 0

// Boucle principale : traite TOUTES les tâches de alternatedList
for (let i = 0; i < alternatedList.length; i++) {
  let task = alternatedList[i]
  let taskEnd = currentTime + task.duration

  // ============================================
  // ÉTAPE 10.1 : Vérifier collision avec temps_morts
  // ============================================
  while (tempsMortsIndex < tempsMorts.length) {
    let tm = tempsMorts[tempsMortsIndex]

    // Si le temps_mort est AVANT currentTime, on l'ignore (déjà passé)
    if (tm.fin_relatif <= currentTime) {
      tempsMortsIndex++
      continue
    }

    // Si le temps_mort est APRÈS cette tâche, pas de collision
    if (tm.debut_relatif >= taskEnd) {
      break // Sortir de la boucle while, traiter la tâche normalement
    }

    // CAS DE COLLISION : La tâche mord sur le temps_mort
    // (taskEnd > tm.debut_relatif ET currentTime < tm.fin_relatif)

    // Sous-cas A: Il y a un trou AVANT le temps_mort
    if (currentTime < tm.debut_relatif) {
      let gapDuration = tm.debut_relatif - currentTime

      // Insère slot "bientôt temps mort" pour boucher le trou
      planning.push({
        type: 'buffer',
        name: 'Bientôt temps mort',
        heure_debut_relative: currentTime,
        duration: gapDuration
      })

      // Avance currentTime jusqu'au début du temps_mort
      currentTime = tm.debut_relatif
    }

    // Insère le temps_mort dans le planning
    planning.push({
      type: 'temps_mort',
      name: tm.titre,
      heure_debut_relative: tm.debut_relatif,
      duration: tm.fin_relatif - tm.debut_relatif
    })

    // Avance currentTime APRÈS le temps_mort
    currentTime = tm.fin_relatif
    tempsMortsIndex++

    // Recalcule la fin de la tâche (car currentTime a changé)
    taskEnd = currentTime + task.duration

    // Continue la boucle while pour vérifier le prochain temps_mort
  }

  // ============================================
  // ÉTAPE 10.2 : Vérifier collision avec tâches planifiées
  // ============================================
  while (tachesPlannifieesIndex < tachesPlannifiees.length) {
    let tp = tachesPlannifiees[tachesPlannifieesIndex]

    // Si la tâche planifiée est AVANT currentTime, on l'ignore (déjà passée)
    if (tp.debut_relatif + tp.duration <= currentTime) {
      tachesPlannifieesIndex++
      continue
    }

    // Si la tâche planifiée est APRÈS cette tâche, pas de collision
    if (tp.debut_relatif >= taskEnd) {
      break // Sortir de la boucle while, traiter la tâche normalement
    }

    // CAS DE COLLISION : La tâche mord sur la tâche planifiée
    // (taskEnd > tp.debut_relatif ET currentTime < tp.debut_relatif + tp.duration)

    // Sous-cas A: Il y a un trou AVANT la tâche planifiée
    if (currentTime < tp.debut_relatif) {
      // Avancer le début de la tâche planifiée pour boucher le trou
      let adjustedStart = currentTime
      let adjustedEnd = adjustedStart + tp.duration

      // Insère la tâche planifiée (garde SA durée, change son début)
      planning.push({
        type: 'planned',
        name: tp.name,
        task_id: tp.id,
        heure_debut_relative: adjustedStart,
        duration: tp.duration,
        original_time: tp.debut_relatif, // Pour badge "Replanifiée"
        rescheduled: true // Début changé
      })

      // Avance currentTime APRÈS la tâche planifiée
      currentTime = adjustedEnd
    } else {
      // Pas de trou, la tâche planifiée commence exactement à currentTime
      planning.push({
        type: 'planned',
        name: tp.name,
        task_id: tp.id,
        heure_debut_relative: currentTime,
        duration: tp.duration,
        original_time: tp.debut_relatif,
        rescheduled: (currentTime !== tp.debut_relatif)
      })

      // Avance currentTime APRÈS la tâche planifiée
      currentTime += tp.duration
    }

    tachesPlannifieesIndex++

    // Recalcule la fin de la tâche (car currentTime a changé)
    taskEnd = currentTime + task.duration

    // Continue la boucle while pour vérifier la prochaine tâche planifiée
  }

  // ============================================
  // ÉTAPE 10.3 : Insérer la tâche normalement (pas de collision)
  // ============================================
  planning.push({
    type: task.type,
    name: task.name,
    task_id: task.task_id,
    heure_debut_relative: currentTime,
    duration: task.duration
  })

  // Avance currentTime pour la prochaine tâche
  currentTime = taskEnd
}
```

**Clarifications** :

**"Mord"** = Chevauchement (même partiel)
- Tâche 13:50-14:10, temps_mort 14:00-15:00 → La tâche MORD (10 min de chevauchement)

**Slot "bientôt temps mort"** :
- Type : `'buffer'`
- Nom : `"Bientôt temps mort"`
- Couleur : Gris clair
- Inséré si trou ≥ 1 minute

**Reprendre après temps_mort** :
- La tâche qui a été annulée (collision) est automatiquement réessayée APRÈS le temps_mort
- `currentTime` avance après le temps_mort, `taskEnd` est recalculé
- La boucle principale continue avec la même tâche (qui sera insérée à l'étape 10.3)

**Reprendre après tâche planifiée** :
- Même logique : `currentTime` avance, `taskEnd` recalculé
- La tâche de `alternatedList` sera insérée après la tâche planifiée

**Important** : Les tâches planifiées sont insérées **PENDANT** la conversion (pas après)

---

### ÉTAPE 11 : Arrêt du planning et finalisation

**Condition d'arrêt** : Lorsque tous les Pomodoros de `alternatedList` ont été traités

**Ignoré** :
- Temps_morts APRÈS le dernier Pomodoro
- Tâches planifiées APRÈS le dernier Pomodoro

**Conversion temps relatif → temps absolu** :

```javascript
for (let slot of planning) {
  // Convertir heure_debut_relative en HH:MM
  let absoluteStart = addMinutes(planningStartTime, slot.heure_debut_relative)
  let absoluteEnd = addMinutes(absoluteStart, slot.duration)

  slot.heure_debut = absoluteStart // "10:00"
  slot.heure_fin = absoluteEnd      // "10:25"

  delete slot.heure_debut_relative // Nettoyer
}
```

**Calcul statistiques** :
```javascript
statistics = {
  total_pomodoros: count(planning, type='pomodoro'),
  total_respirations: count(planning, type='respiration'),
  total_calins: count(planning, type='calin'),
  total_clopes: count(planning, type='clope'),
  total_work_time: sum(durations, type='pomodoro'),
  total_pause_time: sum(durations, type=['respiration','calin','clope']),
  total_planned: count(planning, type='planned'),
  total_temps_morts: count(planning, type='temps_mort')
}
```

---

## 🎛️ OPTIONS SPÉCIALES

### Option "Pauses consécutives"

**Effet** : Désactive l'alternance stricte Pomodoro/Respiration

**Usage** :
- Permet de générer un planning SANS Pomodoros (journée de ménage, respirations consécutives)
- Si cochée + aucun Pomodoro sélectionné → `alternatedList = respirationList`

---

## 🗑️ CODE À SUPPRIMER

**Fonctionnalité obsolète** : Initialisation automatique du planning avec tâches planifiées

**Action** : Supprimer physiquement (PAS commenter) :
- Tout code qui charge/insère automatiquement les tâches planifiées lors du clic "Initialiser planning"
- Les tâches planifiées doivent être insérées UNIQUEMENT via l'étape 11 du flux

**Fichiers à vérifier** :
- `webapp/static/js/gitfocus_v2.js` (fonction d'initialisation)
- Toute autre référence à l'auto-insertion de tâches planifiées

---

## 📊 EXEMPLE COMPLET

### Données d'entrée

**Date** : 2025-11-05
**Heure calculée** : 10:00 (planningStartTime)

**Pomodoros sélectionnés** :
- Révision maths (75 min = 3 Pomodoros)
- Rapport projet (50 min = 2 Pomodoros)

**Respirations sélectionnées** :
- Méditation (10 min) x1
- Respiration profonde (5 min) x2 (duplicata)

**Options** :
- ✅ Câlins activés
- ✅ Clopes activés (intervalle: 120 min)
- ❌ Pauses consécutives

**Temps_morts** :
- 12:00-13:00 : Déjeuner

**Tâches planifiées** :
- 11:30 : Réunion (30 min)

---

### Résultat attendu

```
10:00-10:25 | Pomodoro (Révision maths)          [0-25 min relatif]
10:25-10:35 | Respiration (Méditation)           [25-35 min]
10:35-11:00 | Pomodoro (Révision maths)          [35-60 min]
11:00-11:05 | Respiration (Respiration profonde) [60-65 min]
11:05-11:30 | Pomodoro (Révision maths)          [65-90 min]
11:30-12:00 | Tâche planifiée (Réunion) 📅       [90-120 min] (avancée de 11:30 → bouche trou)
12:00-13:00 | TEMPS MORT (Déjeuner) ⛔           [120-180 min]
13:00-13:25 | Pomodoro (Rapport projet)          [180-205 min]
13:25-13:35 | Câlin 💙                           [205-215 min] (inséré car 2ème respiration)
13:35-13:40 | Respiration (Respiration profonde) [215-220 min] (2ème occurrence = duplicata)
13:40-14:05 | Pomodoro (Rapport projet)          [220-245 min]
14:05-14:10 | Clope 🚬                           [245-250 min] (cumul ≥ 120 min depuis dernière clope)
```

**Statistiques** :
- 5 Pomodoros (125 min)
- 3 Respirations (20 min)
- 1 Câlin (10 min)
- 1 Clope (5 min)
- 1 Tâche planifiée (30 min)
- 1 Temps mort (60 min)
- **Total** : 250 min (4h10)

---

## 🔧 IMPLÉMENTATION TECHNIQUE

### Persistance de l'intervalle clopes (serveur)

**Endpoint à créer** :
```
POST /api/v2/gitfocus/config/clopes-interval
Body: {"interval_min": 120}

GET /api/v2/gitfocus/config/clopes-interval
Response: {"interval_min": 120}
```

**Fichier de stockage** :
```
prod_data/user_config.json
{
  "clopes_interval_min": 120
}
```

**Comportement** :
- Au chargement de la page : Récupérer la valeur sauvegardée via GET
- À la modification : Sauvegarder via POST (immédiatement, pas au clic "Générer")
- Accessible depuis tous les navigateurs (synchronisation automatique)

---

## ✅ CHECKLIST DE VALIDATION

Avant de considérer l'implémentation comme complète, vérifier :

- [ ] Calcul automatique planningStartTime (heure actuelle + 15 min arrondi à 5)
- [ ] Système de temps relatif fonctionnel (minute 0 = planningStartTime)
- [ ] Conversion Pomodoros (tâches → multiple de 25 min)
- [ ] Alternance Pomodoro/Respiration (cycling des respirations)
- [ ] Mode Focus fonctionnel (0 respirations → seulement Pomodoros)
- [ ] Insertion câlins (1 tous les 2 respirations, AVANT la respiration)
- [ ] Insertion clopes (cumul tous types de tâches, intervalle configurable)
- [ ] Persistance serveur de l'intervalle clopes
- [ ] Gestion temps_morts (slot "bientôt temps mort" si trou ≥ 1 min)
- [ ] Gestion tâches planifiées (avancement début, garde durée)
- [ ] Priorité temps_mort > tâche planifiée (si conflit)
- [ ] Arrêt après dernier Pomodoro (ignore tout après)
- [ ] Conversion temps relatif → temps absolu (HH:MM)
- [ ] Calcul statistiques (totaux par type)
- [ ] Suppression code auto-insertion tâches planifiées (physiquement, pas commenté)
- [ ] Option "Pauses consécutives" fonctionnelle (permet respirations seules)

---

**Document créé le** : 2025-11-05
**Auteur** : Claude (Anthropic)
**Supervision** : Julio
**Version du code** : V2 Refonte (commit e09bd0b)
