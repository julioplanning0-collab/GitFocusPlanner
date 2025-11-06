# GitFocus Planner V2 - Spécifications Interface Web

**Version**: 2.0
**Date**: 2025-10-31
**Auteur**: Julio

---

## 🎯 Vue d'ensemble

Interface web pour générer des plannings Pomodoro intelligents avec :
- Alternance automatique travail ↔ pause
- Respect strict des temps_morts (jour 1 et jour 2)
- Multi-day planning (continue automatiquement sur le lendemain)
- Drag & drop pour réorganiser les tâches
- Suppression avec maintien de l'alternance

---

## 📐 Architecture

### Composants

```
webapp/
├── templates/
│   └── gitfocus_v2.html         # Interface HTML
├── static/
│   ├── js/
│   │   └── gitfocus_v2.js       # Logique frontend
│   └── css/
│       └── gitfocus_v2.css      # Styles
└── api/
    └── routes_gitfocus_v2.py    # Endpoints REST
```

### Stack Technique

- **Backend**: Flask + Python 3.13
- **Frontend**: Vanilla JavaScript (ES6+)
- **Styles**: CSS3 (variables CSS, flexbox, grid)
- **Format données**: JSON (API) + CSV (export)

---

## 🔧 Fonctionnalités Principales

### 1. Génération de Planning

**Endpoint**: `POST /api/v2/gitfocus/planning/generate-auto`

**Flux**:
1. Utilisateur sélectionne des tâches Pomodoro (checkboxes)
2. Clic sur "Générer Planning Intelligent"
3. Backend génère planning avec alternance Pomodoro ↔ Recurrent
4. Respect des temps_morts (jour 1 et jour 2)
5. Si jour 1 plein → continue sur jour 2 automatiquement
6. Affichage du planning avec séparateur de date

**Règles**:
- Jour = 06:00 → 23:59 (tronque à 23:59, pas de 24:00+)
- Alternance stricte : Travail → Pause → Travail → Pause
  - Types travail : `pomodoro`, `planned`, `recurrent`
  - Types pause : `respiration`, `pause`
- Respect des temps_morts **pour chaque jour**
- Multi-day : charge temps_morts jour 2 si nécessaire

**Exemple Planning Multi-Day**:
```
🔴 06:30 - Installer machine virtuelle (Pomodoro)  [Jour 1]
🟣 06:55 - Jeu avec Coco (Recurrent)
🔴 07:00 - Installer machine virtuelle (Pomodoro)
...
🔴 23:30 - debugger gitfocus web (Pomodoro)
🟣 23:55 - Brossage dentaire (Recurrent)

📅 2025-11-02  [Séparateur de date]

🔴 06:30 - fabriquer les cloches (Pomodoro)  [Jour 2, après temps mort 00:00-06:30]
🟣 06:55 - Jeu avec Coco (Recurrent)
```

---

### 2. Drag & Drop (Réorganisation)

**Comportement**:
- Glisser n'importe quel slot pour le déplacer
- Déposer sur un autre slot pour insérer avant
- Recalcul automatique des heures après drop
- Maintient l'alternance travail ↔ pause

**Implémentation**:
```javascript
// Chaque slot est draggable
<div class="planning-slot" draggable="true" data-slot-index="5">

// Événements
- dragstart: Marque le slot comme en cours de drag
- dragover: Affiche indicateur de drop (bordure bleue)
- drop: Réorganise le planning + recalcule heures
- dragend: Nettoie les classes CSS temporaires
```

**Limites**:
- Ne respecte PAS les temps_morts après drag & drop
- Pour respecter les temps_morts → cliquer "Générer Planning Intelligent"

---

### 3. Suppression de Tâches

**Comportement**:
- Bouton "✕" sur chaque slot
- Supprime le slot
- **Remonte les slots du même type** pour combler le trou
- Maintient l'alternance travail ↔ pause

**Algorithme de Remontée**:
```
1. Identifier type du slot supprimé (travail ou pause)
2. Trouver le prochain slot du même type
3. Le déplacer pour combler le trou
4. Répéter jusqu'à plus de slots du même type
5. Recalculer toutes les heures
```

**Exemple**:
```
Avant suppression:
[0] Pomodoro A
[1] Pause X
[2] Pomodoro B
[3] Pause Y
[4] Pomodoro C

Suppression de [1] Pause X:
[0] Pomodoro A
[1] Pomodoro B      ← Reste en place (type différent)
[2] Pause Y         ← Remonte pour combler le trou
[3] Pomodoro C

Résultat: Alternance maintenue
```

---

### 4. Ajout de Tâches Récurrentes

**Comportement**:
- Clic sur une tâche récurrente (panneau gauche)
- Remplace la première pause "default_pause"
- Si aucune pause disponible → ajoute à la fin
- Maintient l'alternance

**Note**: Actuellement régénère tout le planning via API

---

### 5. Affichage du Planning

**Structure**:
```
Slot:
┌─────────────────────────────────────┐
│ 🔴 06:30  Installer VM      25 min  │ ← Header
│ Pomodoro 1/3 • Informatique         │ ← Details
│                               [✕]   │ ← Delete button
└─────────────────────────────────────┘
```

**Types de slots** (couleurs):
- 🔴 Pomodoro (jaune)
- 🟣 Recurrent (violet)
- 🔵 Planned (bleu)
- 🟢 Respiration (vert)
- ⚪ Pause (gris)

**Séparateur de date**:
```
────────────────────────────────────
   📅 Samedi 2 novembre 2025
────────────────────────────────────
```

---

### 6. Export CSV

**Endpoint**: `POST /api/v2/gitfocus/planning/export`

**Format CSV**:
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"KIND";"ORIGINAL_TIME"
"1";"Installer machine virtuelle";"2025-11-01";"06:30";"06:55";"25";"pomodoro";""
"REC027";"Jeu avec Coco";"2025-11-01";"06:55";"07:00";"5";"recurrent";""
```

**Destination**: `prod_data/planned.csv`

**Side Effects**:
- Incrémente `EXPORT_COUNT` pour les tâches respiratoires
- Log placements pour apprentissage (scoring futur)

---

## 🚫 Contraintes Techniques

### Temps & Dates

1. **Format heures**: `HH:MM` (00:00 → 23:59)
   - ❌ Jamais 24:00, 25:00, etc.
   - ✅ Minuit = 00:00 du jour suivant

2. **Format dates**: `YYYY-MM-DD` (ISO 8601)
   - API et planning: `2025-11-01`
   - Affichage: "Vendredi 1 novembre 2025"

3. **Limites journalières**:
   - Début: 06:00 (ou heure actuelle si aujourd'hui)
   - Fin: 23:59:59 (tronque, ne continue pas sur jour suivant en heures >= 24h)

### Alternance Travail ↔ Pause

**Règle stricte**: Jamais deux tâches du même type consécutives

```javascript
const workTypes = new Set(['pomodoro', 'planned', 'recurrent']);
const pauseTypes = new Set(['respiration', 'pause']);

// Valide
[Pomodoro, Pause, Pomodoro, Respiration, Recurrent, Pause]

// Invalide
[Pomodoro, Pomodoro]  ❌ Deux travaux consécutifs
[Pause, Respiration]  ❌ Deux pauses consécutives
```

**Maintenance de l'alternance**:
- Génération: Backend insère automatiquement pauses entre Pomodoros
- Drag & drop: Frontend recalcule les heures (ne vérifie PAS alternance)
- Suppression: Frontend remonte slots du même type

### Temps Morts

**Définition**: Périodes bloquées (dodo, réunions, etc.)

**Respect**:
- ✅ Génération initiale (backend Python)
- ✅ Multi-day (charge temps_morts jour 2)
- ❌ Drag & drop local (ne vérifie pas)
- ❌ Suppression locale (ne vérifie pas)

**Pour forcer respect après modification**:
→ Cliquer "Générer Planning Intelligent"

---

## 🔄 Calcul des Heures

### Fonction `addMinutes()`

Gère le passage de minuit et changement de date:

```javascript
addMinutes("23:30", 60, "2025-11-01")
// → { time: "00:30", date: "2025-11-02" }

addMinutes("10:00", 25, "2025-11-01")
// → { time: "10:25", date: "2025-11-01" }
```

**Algorithme**:
1. Convertir heures en minutes totales
2. Calculer décalage de jours (`totalMinutes / 1440`)
3. Calculer heures dans la journée (`totalMinutes % 1440`)
4. Si changement de jour → calculer nouvelle date

### Recalcul après Modification

**Scénarios**:
1. **Drag & drop**: `recalculateTimesAfterReorder()`
   - Utilise heure de début du 1er slot
   - Calcule séquentiellement (slot[i].fin → slot[i+1].début)
   - Gère multi-day automatiquement

2. **Suppression**: `recalculateTimesAfterReorder()`
   - Même logique que drag & drop

3. **Ajout récurrent**: Régénère via API
   - Respect des temps_morts garanti

---

## 🎨 Interface Utilisateur

### Layout Desktop

```
┌────────────────────────────────────────────────────────┐
│  🎯 GitFocus Planner V2        📅 [Date] [Aujourd'hui] │
│                                     [🔄] [📊]          │
├──────────────────┬─────────────────────────────────────┤
│ 📋 Tâches        │ 📊 Planning Généré                  │
│                  │                                     │
│ 🔴 Pomodoro      │ Total: 72 slots                     │
│ ☐ Task 1         │ Travail: 1125 min                   │
│ ☐ Task 2         │ Pauses: 360 min                     │
│ ☐ Task 3         │                                     │
│                  │ 🔴 06:30 - Installer VM   [✕]       │
│ 🟣 Récurrentes   │ 🟣 06:55 - Jeu Coco       [✕]       │
│ • Jeu Coco       │ 🔴 07:00 - Installer VM   [✕]       │
│ • Brossage       │ ...                                 │
│ • Arrosage       │ ──────── 📅 2025-11-02 ────────     │
│                  │ 🔴 06:30 - Fabriquer      [✕]       │
│ [⚡ Générer]     │                                     │
│                  │ [📥 Exporter CSV]                   │
└──────────────────┴─────────────────────────────────────┘
```

### Layout Mobile

Onglets "📋 Tâches" / "📅 Planning"

---

## 🧪 Tests Manuels

### Test 1: Génération Basique
1. Ouvrir http://localhost:5000/api/v2/gitfocus/interface
2. Cocher 2-3 tâches Pomodoro
3. Cliquer "Générer Planning Intelligent"
4. Vérifier:
   - ✅ Alternance travail ↔ pause
   - ✅ Aucune heure >= 24:00
   - ✅ Respect des temps_morts

### Test 2: Multi-Day
1. Cocher toutes les tâches Pomodoro (3 tâches)
2. Générer planning
3. Vérifier:
   - ✅ Dernier slot jour 1 < 24:00
   - ✅ Séparateur de date apparaît
   - ✅ Jour 2 commence à 06:30 (après temps mort dodo)

### Test 3: Drag & Drop
1. Générer un planning
2. Glisser un Pomodoro vers le haut
3. Vérifier:
   - ✅ Slot se déplace
   - ✅ Heures recalculées
   - ✅ Pas d'heures >= 24:00

### Test 4: Suppression avec Alternance
1. Générer un planning
2. Supprimer une pause (🟣)
3. Vérifier:
   - ✅ Prochaine pause remonte
   - ✅ Pomodoros restent en place
   - ✅ Alternance maintenue

### Test 5: Export CSV
1. Générer planning
2. Cliquer "Exporter Planning"
3. Ouvrir `prod_data/planned.csv`
4. Vérifier:
   - ✅ Format correct (délimiteur `;`)
   - ✅ Aucune heure >= 24:00
   - ✅ Dates correctes (jour 1 et jour 2)

---

## 🐛 Problèmes Connus

### ⚠️ Limitations

1. **Drag & drop ne respecte pas temps_morts**
   - Solution: Régénérer via API après drag

2. **Suppression ne respecte pas temps_morts**
   - Solution: Régénérer via API après suppression

3. **Cache navigateur**
   - Symptôme: Affichage d'anciennes données
   - Solution: Hard refresh (Ctrl+F5)

### ✅ Bugs Corrigés

1. **Heures dépassant 24h** (2025-10-31)
   - Cause: `addMinutes()` ne gérait pas minuit
   - Fix: Ajout calcul modulo 1440 + gestion date

2. **Temps_morts jour 2 non respectés** (2025-10-31)
   - Cause: Multi-day chargeait temps_morts mais `calculate_free_slots()` les ignorait
   - Fix: Ajout logs + vérification chargement temps_morts

3. **Interface web affiche heures invalides** (2025-10-31)
   - Cause: JavaScript générait localement sans consulter API
   - Fix: `toggleTaskSelection()` appelle maintenant `generatePlanning()`

---

## 📚 Références

### Code Source
- Backend: `backend/planning_engine/planning_generator.py`
- Frontend: `webapp/static/js/gitfocus_v2.js`
- API: `webapp/api/routes_gitfocus_v2.py`

### Documentation
- Architecture: `SPECIFICATIONS_COMPLETES_V2.md`
- Bonnes pratiques: `good_practices.md`
- Instructions Claude: `.claude/CLAUDE.md`

---

**Version**: 2.0
**Dernière mise à jour**: 2025-10-31
**Auteur**: Julio + Claude Code
