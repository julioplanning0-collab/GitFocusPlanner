# 🚀 QuickStart - Interface Frontend V3 Pure

**Date**: 2025-11-06
**Branch**: v3-linear-timeline-pure
**Phase**: 7 - Frontend complet avec drag & drop natif HTML5

---

## 📦 Fichiers Créés

### 1. **webapp_v3_pure/templates/gitfocus_v3.html**
Interface HTML complète avec:
- Header avec status serveur + sélecteur heure début planning
- Système de tabs (3 onglets: Pomodoro, Pauses, Récurrentes)
- Drag & drop zones natif HTML5 (2 colonnes)
- Actions bar avec boutons Générer + Export
- Timeline display avec statistiques
- Toast notifications

### 2. **webapp_v3_pure/static/css/gitfocus_v3.css**
Styles complets avec:
- Variables CSS (couleurs, spacing, shadows)
- Layout responsive (grid + flexbox)
- Drag & drop styling (hover effects, visual feedback)
- Timeline display (colors par type)
- Animations (pulse, slideIn)
- Mobile responsive (@media queries)

### 3. **webapp_v3_pure/static/js/gitfocus_v3.js**
Logique JavaScript vanilla avec:
- State management (selectedPomodoroIds, selectedPauseIds ordonnés avec duplicatas)
- Init planning start time (now + 15min, arrondi 5min)
- Drag & drop natif HTML5 (dragstart, dragover, drop)
- API calls (load tasks, generate planning, export CSV)
- Timeline rendering (colored slots)
- Toast notifications

---

## 🎯 Fonctionnalités Implémentées

### Onglet 1: Pomodoro
- ☑️ Checkboxes pour sélection
- ☑️ Boutons "Tout sélectionner" / "Tout désélectionner"
- ☑️ Affichage durée + catégorie
- ☑️ Highlight des tâches sélectionnées

### Onglet 2: Pauses (Drag & Drop)
- ☑️ 2 colonnes: Disponibles | Sélectionnées
- ☑️ Drag & drop natif HTML5 (NO external libs)
- ☑️ Ordre préservé dans séquence sélectionnée
- ☑️ Duplicatas autorisés (glisser plusieurs fois même pause)
- ☑️ Bouton "Vider" pour effacer séquence
- ☑️ Options: Câlins (every 2 pauses), Clopes (every Xmin work)

### Onglet 3: Récurrentes
- ☑️ Toggle switches ON/OFF
- ☑️ Affichage recurrence_type
- ☑️ Boutons "Tout activer" / "Tout désactiver"
- ☑️ Filtre IS_PAUSE=0 (exclut pauses)

### Actions
- ☑️ Générer Planning (validation + POST /api/v3/planning/generate)
- ☑️ Export CSV (POST /api/v3/planning/export)
- ☑️ Summary sélection (compteurs Pomodoros, Pauses, Récurrentes)

### Timeline Display
- ☑️ Statistiques (total pomodoros, pauses, temps travail/pause)
- ☑️ Timeline visuelle avec couleurs par type:
  - Rouge: POMODORO
  - Bleu: PAUSE
  - Vert: CALIN
  - Orange: CLOPE
  - Violet: RECURRENT
  - Gris: OBSTACLE/TEMPS_MORT
- ☑️ Badges pomodoro index (1/3, 2/3...)
- ☑️ Warning si tâche décalée

---

## 🚀 Démarrage

### 1. Vérifier que le serveur V3 tourne
```bash
cd C:\Users\juli0\AndroidStudioProjects\GitfocusPlanner
python -m webapp_v3_pure.server_v3
```

### 2. Ouvrir l'interface
```
http://localhost:5001/gitfocus-v3
```

### 3. Workflow utilisateur
1. **Header**: Vérifier l'heure de début planning (auto: now + 15min)
2. **Onglet Pomodoro**: Cocher les tâches à inclure
3. **Onglet Pauses**: Glisser les pauses dans la zone sélectionnée (ordre important)
4. **Onglet Récurrentes**: Activer les tâches récurrentes souhaitées
5. **Actions Bar**: Cliquer "Générer Planning"
6. **Timeline**: Voir le planning généré avec statistiques
7. **Export**: Cliquer "Export CSV" pour sauvegarder

---

## 🎨 Architecture Frontend

### State Management
```javascript
state = {
    planningStartTime: Date,           // now + 15min, rounded to 5min
    currentDate: "YYYY-MM-DD",

    pomodoroTasks: [],                 // Loaded from API
    pauseTasks: [],                    // IS_PAUSE=1
    recurrentTasks: [],                // IS_PAUSE=0
    obstacles: [],                     // temps_morts for date

    selectedPomodoroIds: ["TASK001"],  // Checkboxes
    selectedPauseIds: ["REC001", "REC003", "REC001"],  // ORDERED + duplicates
    enabledRecurrentIds: ["REC006"],   // Toggles

    calinEnabled: true,
    clopeEnabled: false,
    clopeInterval: 120,

    currentPlanning: null              // Generated planning for export
}
```

### Drag & Drop Flow
```javascript
// HTML5 API (NO sortable.js, NO react-beautiful-dnd)
1. dragstart → Store dragged item ID
2. dragover → Prevent default + show drop zone highlight
3. drop → Add pause ID to state.selectedPauseIds array (allows duplicates)
4. renderSelectedPauses() → Re-render with order numbers (1., 2., 3....)
```

### API Calls
```javascript
// Load tasks (parallel)
GET /api/v3/tasks/pomodoro
GET /api/v3/tasks/recurrent?pause_only=true
GET /api/v3/tasks/recurrent?exclude_pauses=true
GET /api/v3/temps-morts?date=2025-11-06

// Generate planning
POST /api/v3/planning/generate
Body: {
    date, planning_start_time,
    pomodoro_ids, pause_ids (ordered), recurrent_ids,
    calin_enabled, clope_enabled, clope_interval_min
}

// Export CSV
POST /api/v3/planning/export
Body: { date, planning }
```

---

## ✅ Architecture 2-Step Comprise

### Frontend envoie juste les IDs ordonnés
```javascript
pause_ids: ["REC001", "REC003", "REC001"]  // Ordre + duplicatas
```

### Backend fait tout le reste
- STEP 1: ORDERING (construction séquence)
  - Expand Pomodoros (75min → 3x 25min)
  - Alternate Pomodoros & Pauses (cycle through pause_ids)
  - Insert Calins (every 2 pauses)
  - Insert Clopes (every Xmin work)

- STEP 2: TIME CALCULATION
  - Convert temps_morts to obstacles (minutes relatives)
  - rebuildTimeline() → Calculate all minuteOffsets
  - findNextFreeSlot() → Collision detection

- STEP 3: DISPLAY FORMAT
  - Convert minuteOffsets to absolute times
  - Return JSON with heure_debut, heure_fin

---

## 🧪 Tests Manuels

### Test 1: Load Page
- ✅ Status dot devient vert (online)
- ✅ Heure début planning affichée (now + 15min)
- ✅ 3 onglets chargés avec données
- ✅ Compteurs à 0

### Test 2: Sélection Pomodoro
- ✅ Cocher 2-3 tâches
- ✅ Compteur Pomodoro augmente
- ✅ Tasks highlight en bleu
- ✅ "Tout sélectionner" fonctionne

### Test 3: Drag & Drop Pauses
- ✅ Glisser pause depuis "Disponibles" vers "Sélectionnées"
- ✅ Pause apparaît avec numéro (1., 2., 3...)
- ✅ Glisser même pause 2x → duplicata OK
- ✅ Bouton "Vider" efface tout
- ✅ Compteur Pauses augmente

### Test 4: Récurrentes
- ✅ Toggle ON/OFF fonctionne
- ✅ Task highlight quand active
- ✅ Compteur Récurrentes augmente
- ✅ "Tout activer/désactiver" fonctionne

### Test 5: Génération Planning
- ✅ Sans sélection → Warning "Sélectionner Pomodoro"
- ✅ Avec sélections → Planning généré
- ✅ Timeline s'affiche avec couleurs
- ✅ Statistiques affichées
- ✅ Bouton Export activé

### Test 6: Export CSV
- ✅ Bouton désactivé avant génération
- ✅ Après génération → Export réussit
- ✅ Toast affiche chemin fichier
- ✅ CSV créé dans data/prod_data/

---

## 🐛 Troubleshooting

### Styles ne chargent pas
```bash
# Vérifier chemin static
ls webapp_v3_pure/static/css/gitfocus_v3.css

# Vérifier console browser (F12) pour erreurs 404
# URL attendue: http://localhost:5001/static/css/gitfocus_v3.css
```

### Drag & drop ne fonctionne pas
```javascript
// Vérifier dans console browser (F12):
// - Événement dragstart déclenché?
// - draggedItem set?
// - Drop zone détecte drop?

// Debug: ajouter console.log dans handleDragStart, handleDrop
```

### Planning ne génère pas
```javascript
// Vérifier console browser (F12):
// - Requête POST envoyée?
// - Payload correct?
// - Response 200 ou erreur?

// Vérifier console serveur:
// - Erreur backend?
// - CSV files manquants?
```

### Timeline ne s'affiche pas
```javascript
// Vérifier dans displayPlanning():
// - data.planning est array?
// - Slots ont heure_debut, heure_fin, type, task_name?

// Vérifier CSS:
// - .timeline-slot existe?
// - .type-pomodoro, .type-pause avec couleurs?
```

---

## 📋 Checklist GUARD_V3

### Architecture V3 Pure
- ✅ Utilise API REST (NO direct CSV access)
- ✅ Drag & drop natif HTML5 (NO external libs)
- ✅ Vanilla JavaScript (NO jQuery, NO React)
- ✅ État local géré côté frontend
- ✅ Backend fait ORDERING + TIME CALCULATION

### Isolation Code
- ✅ Aucun import depuis V2 code
- ✅ Fichiers dans webapp_v3_pure/ SEULEMENT
- ✅ API V3 endpoints (/api/v3/*)

### Données
- ✅ selectedPauseIds = ORDERED array with duplicates
- ✅ Frontend envoie juste IDs, backend calcule tout
- ✅ Types colors: pomodoro (rouge), pause (bleu), calin (vert)

---

## 🎉 Prochaines Étapes

### Phase 7 - Complète ✅
- [x] HTML template avec 3 tabs
- [x] CSS responsive avec drag & drop styling
- [x] JavaScript avec HTML5 drag & drop
- [x] API integration (load, generate, export)
- [x] Timeline display avec colors

### Phase 8 - Améliorations Futures (optionnelles)
- [ ] Reordering dans zone sélectionnée (drag within same zone)
- [ ] Persistance selections (localStorage)
- [ ] Undo/Redo
- [ ] Keyboard shortcuts
- [ ] Dark mode
- [ ] Animations avancées

---

**INTERFACE FRONTEND V3 PURE - COMPLÈTE ET FONCTIONNELLE**

Date: 2025-11-06
Version: V3.0 Pure
Branch: v3-linear-timeline-pure
Status: Ready for testing
