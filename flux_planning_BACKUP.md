# Flux Complet de Génération du Planning - GitFocus V2

## PHASE 1: INITIALISATION (au chargement de la page)

### 1.1 Calcul de l'heure de départ (DOMContentLoaded)
- Calculer: Heure actuelle + 15 minutes
- Arrondir au multiple de 5 supérieur
- **Exemple**: 13:07 → 13:22 → 13:25
- Stocker cette valeur dans le champ `planning-start-time`
- Initialiser `state.planningStartTime` avec cette valeur

### 1.2 Point de référence temporel
- `planningStartTime` = minute 0 (le point zéro absolu)
- Tout le système utilise des **minutes RELATIVES** à ce point
- **Exemple**: Si planningStartTime = 13:25, alors:
  - 13:25 = minute 0
  - 14:25 = minute 60
  - 12:25 = minute -60

### 1.3 Chargement des données sources (en mémoire, pas encore insérées)
- Charger `temps_morts.csv` pour la date sélectionnée
- Charger `TACHES_PLANIFIEES.v2.csv` pour la date sélectionnée
- Convertir chaque temps_mort et tâche planifiée en coordonnées relatives (minutes depuis planningStartTime)
- Stocker dans `state.tempsMorts` et `state.plannedTasks`

---

## PHASE 2: CONSTRUCTION DE LA LISTE DE TÂCHES (quand utilisateur clique "Générer Planning")

### 2.1 Ajout des Pomodoros (tâches de travail)
- Pour chaque tâche Pomodoro sélectionnée:
  - Calculer nombre de Pomodoros = `Math.ceil(durée / 25)`
  - Ajouter chaque Pomodoro dans `timeline.tasks` avec:
    - `type: 'POMODORO'`
    - `taskName: nom_tache`
    - `duration: 25` (minutes)
    - `pomodoroIndex: n` et `pomodoroTotal: total`
  - **Pas d'heure** à ce stade, juste nom + durée

### 2.2 Ajout des Respirations
- Pour chaque respiration sélectionnée (avec compteur x2, x3...):
  - Ajouter la respiration `n` fois dans `state.respirationStaging`
  - Stocker: `taskId` (ID de la respiration)

### 2.3 Alternance Pomodoro/Respiration
- Créer une nouvelle liste ordonnée:
  - Prendre 1 Pomodoro
  - Prendre 1 Respiration (cycling si nécessaire)
  - Répéter jusqu'à épuisement des Pomodoros
- **Cycling des respirations**: Si on manque de respirations, recommencer depuis le début de la liste
  - Exemple: [R1, R2, R3] → Pomo1, R1, Pomo2, R2, Pomo3, R3, Pomo4, R1, Pomo5, R2...
- Si option "pauses consécutives" cochée: permettre de générer un planning SANS Pomodoros (uniquement respirations)

### 2.4 Ajout des Câlins (si case cochée)
- Insérer 1 câlin toutes les 2 respirations
- **Pattern**: Respiration, Respiration, Câlin, Respiration, Respiration, Câlin...
- Durée câlin: définie dans `state.recurrentTasks` (type CALIN)

### 2.5 Ajout des Clopes (si case cochée)
- **Interface**:
  - Case à cocher "Clopes"
  - Si cochée: demander intervalle (défaut: 120 minutes, modifiable)
  - Sauvegarder l'intervalle sur le serveur (persistance cross-device)
  - La prochaine fois que la case est cochée: reprendre cette valeur

- **Logique d'insertion**:
  - Parcourir la liste ordonnée (Pomodoros + Respirations + Câlins)
  - Additionner les durées depuis le début
  - Quand la somme atteint l'intervalle prévu: insérer 1 clope
  - Repartir de cette clope pour calculer la prochaine
  - **Important**: Compter TOUTES les tâches (y compris les câlins qui ont été ajoutés)

- **Exemple** (intervalle = 120 min):
  - Pomo1 (25) = 25 total
  - Resp1 (5) = 30 total
  - Pomo2 (25) = 55 total
  - Resp2 (5) = 60 total
  - Câlin (10) = 70 total
  - Pomo3 (25) = 95 total
  - Resp3 (5) = 100 total
  - Pomo4 (25) = 125 total → **CLOPE insérée ici**
  - Clope (5) = 0 (reset compteur)
  - Resp4 (5) = 5 total
  - ...

---

## PHASE 3: CONVERSION EN PLANNING HORAIRE (avec insertion des obstacles)

### 3.1 Variables initiales
- `currentMinute = 0` (relatif à planningStartTime)
- `currentDate = date sélectionnée`
- `timeline.tasks` = liste ordonnée construite en Phase 2

### 3.2 Parcours séquentiel avec gestion des obstacles

Pour chaque tâche de `timeline.tasks`:

#### 3.2.1 Calculer la position cible
- `heureDebut = currentMinute` (relatif)
- `heureFin = currentMinute + durée`

#### 3.2.2 Vérifier collision avec TEMPS MORTS
Pour chaque temps_mort dans `state.tempsMorts`:

**Si la tâche chevauche un temps_mort**:
- **Cas A**: Il y a un trou avant le temps_mort
  - Exemple: currentMinute = 10:35, temps_mort commence à 10:40
  - **Action**: Insérer une tâche "Bientôt temps mort" de 10:35 à 10:40
  - Insérer le temps_mort dans la timeline
  - Avancer `currentMinute` à la fin du temps_mort
  - **Recommencer** le placement de la tâche actuelle

- **Cas B**: La tâche se termine pile au début du temps_mort
  - Exemple: currentMinute = 10:15, tâche de 25 min se termine à 10:40, temps_mort commence à 10:40
  - **Action**: Placer la tâche normalement (10:15-10:40)
  - Insérer le temps_mort (10:40-14:00)
  - Avancer `currentMinute` à la fin du temps_mort (14:00)

**Si pas de collision**: Continuer

#### 3.2.3 Vérifier collision avec TÂCHES PLANIFIÉES
Pour chaque tâche planifiée dans `state.plannedTasks`:

**Si la tâche chevauche une tâche planifiée**:
- **Cas A**: Il y a un trou avant la tâche planifiée
  - Exemple: currentMinute = 14:20, tâche planifiée commence à 14:30
  - **Action**:
    - Avancer le début de la tâche planifiée à 14:20 (pour boucher le trou)
    - Garder la fin prévue inchangée (exemple: 15:00)
    - Durée effective = fin - nouveau début (15:00 - 14:20 = 40 min au lieu de 30 min)
  - Insérer la tâche planifiée avec nouveau début
  - Avancer `currentMinute` à la fin de la tâche planifiée
  - **Recommencer** le placement de la tâche actuelle

- **Cas B**: La tâche se termine pile au début de la tâche planifiée
  - **Action**: Placer la tâche normalement
  - Insérer la tâche planifiée
  - Avancer `currentMinute` à la fin de la tâche planifiée

**Si pas de collision**: Continuer

#### 3.2.4 Cas spécial: Tâche planifiée pendant un temps mort
- Si une tâche planifiée est prévue pendant un temps mort (exemple: tâche à 14:30, temps_mort 14:00-15:00):
  - Placer le temps_mort en premier (priorité absolue)
  - Placer la tâche planifiée juste après le temps_mort (15:00)
  - **Pas de respiration** entre le temps_mort et la tâche planifiée

#### 3.2.5 Placement final de la tâche
- Si aucune collision: placer la tâche à `currentMinute`
- Assigner `minuteOffset = currentMinute` à la tâche
- Avancer `currentMinute` de la durée de la tâche

### 3.3 Fin du planning
- Le planning s'arrête à la fin du dernier Pomodoro
- **Ignorer** tous les temps_morts et tâches planifiées qui arrivent après la dernière Pomodoro
- Ne pas les afficher

---

## PHASE 4: CONVERSION EN FORMAT D'AFFICHAGE

### 4.1 Pour chaque tâche dans `timeline.tasks`
- Convertir `minuteOffset` en heure absolue:
  - `heureAbsolue = planningStartTime + (minuteOffset * 60000)`
- Formater en `HH:MM`
- Créer un slot d'affichage:
  ```javascript
  {
    date: 'YYYY-MM-DD',
    heure_debut: 'HH:MM',
    heure_fin: 'HH:MM',
    task_name: 'Nom de la tâche',
    type: 'pomodoro|respiration|temps_mort|planned|calin|clope',
    duration_min: 25
  }
  ```

### 4.2 Tri chronologique
- Trier tous les slots par `heure_debut` croissante
- Afficher dans l'interface

---

## RÈGLES IMPORTANTES

### Priorités en cas de conflit
1. **Temps mort** (priorité absolue)
2. **Tâche planifiée** (priorité secondaire)
3. **Pomodoro/Respiration/Câlin/Clope** (placés dans les trous)

### Cycling des respirations
- Si on manque de respirations, recommencer depuis le début de la liste
- Continuer jusqu'à épuisement des Pomodoros

### Tâche "Bientôt temps mort"
- Insérée automatiquement si trou < durée d'une tâche normale
- Type: `'bientot_temps_mort'`
- Nom: `"Bientôt temps mort"`
- Durée: taille du trou (en minutes)

### Option "Pauses consécutives"
- Si cochée: permet de générer un planning avec UNIQUEMENT des respirations (pas de Pomodoros)
- Cas d'usage: journée de ménage, journée de soins personnels, etc.

### Suppression de l'auto-ajout des tâches planifiées
- **IMPORTANT**: Retirer le code qui ajoutait automatiquement les tâches planifiées lors de "Initialiser le planning"
- Les tâches planifiées sont maintenant insérées UNIQUEMENT pendant la Phase 3 (conversion en planning horaire)
- **Supprimer physiquement** ce code (pas de commentaire)

---

## RÉSUMÉ DES ÉTAPES

1. ✅ Initialisation: calcul heure de départ + chargement données
2. ✅ Construction liste: Pomodoros → Respirations → Alternance → Câlins → Clopes
3. ✅ Conversion horaire: parcours séquentiel + insertion obstacles + gestion collisions
4. ✅ Affichage: conversion en format UI + tri chronologique

---

**Date de création**: 2025-11-04
**Version**: 2.0
**Auteur**: Julio + Claude
