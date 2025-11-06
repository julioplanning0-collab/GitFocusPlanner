# GitFocus Planner V3 - Spécifications Complètes

**Date**: 2025-11-05
**Version**: 3.0 (Timeline Linéaire)
**Auteur**: Claude (Anthropic) + Julio
**Statut**: Document de référence unique

---

## 📋 TABLE DES MATIÈRES

### PARTIE I - VISION & ARCHITECTURE
1. [Principe Fondamental](#1-principe-fondamental)
2. [Architecture Globale](#2-architecture-globale)
3. [Structure des Données](#3-structure-des-données)

### PARTIE II - INTERFACE UTILISATEUR
4. [Layout Général](#4-layout-général)
5. [Onglet Pomodoro](#5-onglet-pomodoro)
6. [Onglet Pauses](#6-onglet-pauses)
7. [Onglet Récurrentes](#7-onglet-récurrentes)
8. [Planning Généré](#8-planning-généré)
9. [Charte Graphique](#9-charte-graphique)

### PARTIE III - ALGORITHME DE GÉNÉRATION
10. [Flux Complet (12 Étapes)](#10-flux-complet-12-étapes)
11. [Gestion des Collisions](#11-gestion-des-collisions)
12. [Cas Particuliers](#12-cas-particuliers)

### PARTIE IV - FICHIERS DE DONNÉES
13. [Fichiers CSV](#13-fichiers-csv)
14. [Fichiers JSON](#14-fichiers-json)

### PARTIE V - IMPLÉMENTATION
15. [Plan de Développement](#15-plan-de-développement)
16. [Tests & Validation](#16-tests--validation)
17. [Migration & Rollback](#17-migration--rollback)

---

# PARTIE I - VISION & ARCHITECTURE

## 1️⃣ PRINCIPE FONDAMENTAL

### 1.1 Concept Central : Timeline Linéaire

Le système utilise un **modèle de temps RELATIF** au lieu de manipuler des dates/heures complexes.

```
Timeline = Axe linéaire en minutes depuis planningStartTime
  │
  ├─ 0 min ────→ planningStartTime (ex: 2025-11-05 14:00)
  ├─ 30 min ───→ 14:30
  ├─ 150 min ──→ 16:30
  ├─ 720 min ──→ 02:00 (jour suivant)
  └─ ...
```

**Avantages**:
- Arithmétique simple (additions de minutes entières)
- Support naturel des plannings multi-jours
- Placement de tâches = trouver un slot libre sur l'axe
- Conversion en heures absolues UNIQUEMENT lors de l'affichage final

**Point zéro absolu** :
- `planningStartTime` = minute 0
- Calculé automatiquement : maintenant + 15 minutes, arrondi au multiple de 5 supérieur
- Exemple : 13:07 → 13:22 → 13:25
- Modifiable par l'utilisateur (input time dans l'interface)

### 1.2 Architecture 2-Step (ORDERING puis TIME CALCULATION)

**RÈGLE D'OR** : Séparer la construction de la séquence du calcul des heures

```
Modification de timeline
    ↓
ÉTAPE 1 : ORDERING (Construction de la liste ordonnée)
    - Construire la séquence [Pomodoro, Respiration, Câlin, Pomodoro, ...]
    - Respecter l'alternance TRAVAIL/PAUSE
    - SANS minuteOffset (ou minuteOffset = 0)
    ↓
ÉTAPE 2 : TIME CALCULATION (Calcul des heures)
    - Appeler rebuildTimeline()
    - Calculer minuteOffset pour chaque tâche séquentiellement
    - Respecter les obstacles (temps_morts)
    - Gérer les collisions avec tâches planifiées
    ↓
Résultat : timeline.tasks avec minuteOffsets corrects
```

**Fonction centrale** : `rebuildTimeline()`
- Recalcule TOUS les minuteOffsets
- Appelée après CHAQUE modification de la timeline
- Parcourt séquentiellement, saute les obstacles

### 1.3 Priorités en Cas de Conflit

**Ordre de priorité** (du plus important au moins important) :
1. **Temps mort** (priorité absolue) - JAMAIS déplacé
2. **Tâche planifiée** (priorité secondaire) - Peut être décalée mais garde sa durée
3. **Pomodoro/Respiration/Câlin/Clope** - Placés dans les trous disponibles

**Règle spéciale** : Si tâche planifiée pendant temps_mort
- Placer temps_mort en premier
- Placer tâche planifiée juste après (PAS de respiration entre les deux)

---

## 2️⃣ ARCHITECTURE GLOBALE

### 2.1 Stack Technologique

**Frontend** :
- HTML5 / CSS3 (Grid, Flexbox)
- JavaScript Vanilla (ES6+)
- Pas de framework (React/Vue/Angular)
- Drag & Drop API native

**Backend** :
- Python 3.11+
- Flask 2.x
- Blueprint: `gitfocus_bp` (route prefix: `/api/v2/gitfocus`)

**Données** :
- CSV (délimiteur `;`, encodage UTF-8, quoting ALL)
- JSON (configuration, état utilisateur)
- Pas de base de données (fichiers plats)

### 2.2 Séparation des Responsabilités

**Backend (Python)** :
- ✅ 100% de la logique de génération du planning
- ✅ Calcul des créneaux libres
- ✅ Algorithme d'alternance Pomodoro/Respiration
- ✅ Insertion câlins/clopes
- ✅ Gestion collisions (temps_morts + tâches planifiées)
- ✅ Lecture/écriture CSV (opérations atomiques)
- ✅ Persistance état utilisateur

**Frontend (JavaScript)** :
- ✅ Affichage interface (rendering HTML)
- ✅ Gestion interactions utilisateur (clicks, drag & drop)
- ✅ Validation formulaires
- ✅ Appels API REST
- ✅ Mise à jour état visuel (sans logique métier)
- ❌ PAS de calcul de planning (délégué au backend)

**Justification** :
- Backend = Source de vérité (même résultat quel que soit le client)
- Frontend = Présentation uniquement
- Permet futur mobile app / CLI avec même backend

### 2.3 Flux de Communication

```
USER ACTION (Frontend)
    │
    ├─ Sélectionne 3 Pomodoros
    ├─ Sélectionne 2 Respirations
    ├─ Coche "Câlins" + "Clopes"
    │
    ↓
POST /api/v2/gitfocus/planning/generate
    Body: {
        date: "2025-11-05",
        planning_start_time: "14:00",
        pomodoro_ids: ["TASK001", "TASK002", "TASK003"],
        respiration_ids: ["R010", "R018"],
        calin_enabled: true,
        clope_enabled: true,
        clope_interval_min: 120
    }
    │
    ↓
BACKEND (Python)
    1. Charger CSV (Pomodoros, Respirations, Temps morts, Planifiées)
    2. Construire alternance (ORDERING)
    3. Insérer câlins + clopes
    4. Calculer heures (TIME CALCULATION)
    5. Gérer collisions
    6. Retourner planning JSON
    │
    ↓
Response: {
    success: true,
    planning: [
        {date: "2025-11-05", heure_debut: "14:00", heure_fin: "14:25", task_name: "Révision maths", type: "pomodoro", duration_min: 25},
        {date: "2025-11-05", heure_debut: "14:25", heure_fin: "14:35", task_name: "Méditation", type: "respiration", duration_min: 10},
        ...
    ],
    statistics: {
        total_work_min: 300,
        total_pause_min: 60,
        pomodoro_count: 12,
        respiration_count: 12
    }
}
    │
    ↓
FRONTEND (JavaScript)
    - Affiche planning dans panel droit
    - Met à jour statistiques
    - Active bouton "Exporter CSV"
```

---

## 3️⃣ STRUCTURE DES DONNÉES

### 3.1 State Object (Frontend JavaScript)

```javascript
const state = {
    // Planning start time
    planningStartTime: Date,              // ex: new Date('2025-11-05T14:00:00')
    planningStartLocked: false,           // true si utilisateur a forcé l'heure

    // Selections
    selectedPomodoroIds: [],              // ex: ['TASK001', 'TASK002']
    selectedRespirationIds: [],           // ex: ['R010', 'R018', 'R018'] (duplicates OK)

    // Options
    calinEnabled: false,
    clopeEnabled: false,
    clopeIntervalMin: 120,

    // Data loaded from CSV
    pomodoroTasks: [],                    // Liste tâches Pomodoro
    recurrentTasks: [],                   // Liste tâches récurrentes (+ respirations)
    plannedTasks: [],                     // Liste tâches planifiées

    // Timeline (NOT used in V3 - Backend calculates everything)
    // Kept for potential future client-side preview
    timeline: {
        tasks: [],                        // [{minuteOffset, duration, type, taskId, taskName}]
        obstacles: []                     // [{startMinute, endMinute, type, originalData}]
    },

    // Generated planning (received from backend)
    generatedPlanning: [],                // [{date, heure_debut, heure_fin, task_name, type, duration_min}]
    statistics: {},                       // {total_work_min, total_pause_min, pomodoro_count, ...}

    // UI state
    currentTab: 'pomodoro',               // 'pomodoro' | 'pauses' | 'recurrentes'
    planningStatus: 'empty'               // 'empty' | 'generating' | 'generated' | 'error'
};
```

### 3.2 Task Object (Timeline)

```javascript
{
    minuteOffset: number,        // Minutes from planningStartTime (0, 25, 50...)
    duration: number,            // Duration in minutes (25, 5, 10...)
    type: string,                // 'POMODORO', 'RESPIRATION', 'CALIN', 'CLOPE', 'PLANNED', 'FIXED', 'TEMPS_MORT'
    taskId: string,              // Original task ID from CSV
    taskName: string,            // Display name
    isFixed: boolean,            // true = non-draggable (FIXED tasks + temps_morts)
    pomodoroIndex?: number,      // 1, 2, 3... (POMODORO only)
    pomodoroTotal?: number,      // Total pomodoros for this task (POMODORO only)
    originalPlannedTime?: number, // Original requested time (PLANNED only)
    rescheduled?: boolean,       // true if placed at different time than requested
    autoGenerated?: boolean      // true for calins/clopes (not user-selected)
}
```

### 3.3 Obstacle Object (Timeline)

```javascript
{
    startMinute: number,         // Start time (minutes from planningStartTime)
    endMinute: number,           // End time (minutes from planningStartTime)
    type: 'temps_mort',          // Always temps_mort
    originalData: {              // Original CSV data
        date: string,            // "2025-11-05"
        heure_debut: string,     // "14:00"
        heure_fin: string,       // "15:00"
        titre: string            // "Déjeuner"
    }
}
```

### 3.4 Display Slot Object (Planning Affiché)

```javascript
{
    date: string,                // "2025-11-05" (ISO format)
    heure_debut: string,         // "14:00" (HH:MM)
    heure_fin: string,           // "14:25" (HH:MM)
    task_name: string,           // "Révision mathématiques"
    task_id: string,             // "TASK001"
    type: string,                // "pomodoro", "respiration", "calin", "clope", "planned", "temps_mort"
    duration_min: number,        // 25
    pomodoro_index?: number,     // 1 (if type=pomodoro)
    pomodoro_total?: number,     // 3 (if type=pomodoro)
    original_time?: string,      // "14:30" (if rescheduled)
    rescheduled?: boolean        // true (if placed at different time)
}
```

---

# PARTIE II - INTERFACE UTILISATEUR

## 4️⃣ LAYOUT GÉNÉRAL

### 4.1 Structure HTML Globale

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (60px)                                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ GitFocus Planner V3 - Timeline Linéaire                  │ │
│ │ Serveur: 2025-11-05 14:32:15          [?] [⚙]          │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ CONTROLS BAR (50px)                                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Date: [2025-11-05 ▼]  Heure: [14:00] [🔄 Auto]        │ │
│ │ [Générer Planning] [Exporter CSV (disabled)]            │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ MAIN CONTENT (2 COLONNES) - Height: calc(100vh - 170px)     │
│ ┌──────────────────────────┬────────────────────────────┐   │
│ │ LEFT PANEL (70%)         │ RIGHT PANEL (30%)          │   │
│ │                          │                            │   │
│ │ ┌──────────────────────┐ │ ┌────────────────────────┐ │   │
│ │ │ TABS                 │ │ │ PLANNING GÉNÉRÉ        │ │   │
│ │ │ [Pomodoro] [Pauses] │ │ │ (Scrollable)            │ │   │
│ │ │ [Récurrentes]        │ │ │                        │ │   │
│ │ └──────────────────────┘ │ │ 10:00-10:25 Tâche 1   │ │   │
│ │                          │ │ 10:25-10:35 Pause      │ │   │
│ │ <TAB CONTENT>            │ │ ...                    │ │   │
│ │ (Scrollable)             │ │                        │ │   │
│ │                          │ │                        │ │   │
│ └──────────────────────────┘ └────────────────────────┘ │   │
└─────────────────────────────────────────────────────────────┘
│ FOOTER (60px)                                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🟡 8 Pomodoros | ⏱️ 120min travail | 🔵 40min pauses    │ │
│ │ 🕒 180min libres restants                               │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Responsive Design

**Desktop (> 1200px)** :
- Layout: 2 colonnes (70% / 30%)
- Largeur min: 1200px
- Hauteur: 100vh

**Tablet (768px - 1200px)** :
- Layout: 2 colonnes (60% / 40%)
- Onglets peuvent être collapsés

**Mobile (< 768px)** :
- Layout: 1 colonne (onglets au-dessus, planning en-dessous)
- Accordéon (1 seul onglet ouvert à la fois)

### 4.3 Header - Code HTML

```html
<header class="app-header">
    <div class="header-logo">
        <h1>GitFocus Planner V3</h1>
        <span class="version-badge">Timeline Linéaire</span>
    </div>
    <div class="header-info">
        <span class="server-version">
            Serveur: <span id="server-timestamp">2025-11-05 14:32:15</span>
        </span>
    </div>
    <div class="header-actions">
        <button class="btn-icon" id="help-btn" title="Aide">?</button>
        <button class="btn-icon" id="config-btn" title="Configuration">⚙</button>
    </div>
</header>
```

**Style CSS** :
```css
.app-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 60px;
    padding: 0 20px;
    background: #1e293b;
    color: #ffffff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.version-badge {
    font-size: 0.75em;
    padding: 2px 8px;
    background: #3b82f6;
    border-radius: 4px;
    margin-left: 8px;
}

.server-version {
    font-size: 0.85em;
    color: #94a3b8;
}
```

### 4.4 Controls Bar - Code HTML

```html
<div class="controls-bar">
    <div class="control-group">
        <label for="planning-date">Date :</label>
        <input type="date" id="planning-date" value="2025-11-05">
    </div>

    <div class="control-group">
        <label for="planning-start-time">Heure de départ :</label>
        <input type="time" id="planning-start-time" value="14:00">
        <button class="btn-sm" id="auto-time-btn" title="Calculer automatiquement">
            🔄 Auto
        </button>
    </div>

    <div class="control-actions">
        <button class="btn btn-primary" id="generate-planning-btn">
            Générer Planning
        </button>
        <button class="btn btn-secondary" id="export-csv-btn" disabled>
            Exporter CSV
        </button>
    </div>
</div>
```

**Comportements** :
- **Date change** → Recharge temps_morts.csv + tâches planifiées
- **Time change** → Met à jour `state.planningStartTime`, `state.planningStartLocked = true`
- **Auto button** → Recalcule : now + 15min arrondi à 5, `state.planningStartLocked = false`
- **Générer** → POST `/api/v2/gitfocus/planning/generate`
- **Exporter** → POST `/api/v2/gitfocus/planning/export` (écrit `planned.csv` sur serveur)

---

## 5️⃣ ONGLET POMODORO

### 5.1 Layout Onglet

```
┌──────────────────────────────────────────────────────────┐
│ ONGLET: POMODORO                              [+ Nouvelle]│
├──────────────────────────────────────────────────────────┤
│ Filtres:                                                  │
│ [Catégorie: Toutes ▼] [Priorité: Toutes ▼] [🔍 ...]     │
├──────────────────────────────────────────────────────────┤
│ LISTE TÂCHES (Scrollable, max-height: 60vh)              │
│ ┌────────────────────────────────────────────────────────┤
│ │ ☐ [P1] Révision mathématiques                  75 min │
│ │     Études › Mathématiques                            │
│ │     Deadline: 15.11.25                                │
│ │     [✏️ Éditer] [🗑️ Supprimer]                        │
│ ├────────────────────────────────────────────────────────┤
│ │ ☑ [P2] Rapport de projet                      50 min │
│ │     Travail › Documentation                           │
│ │     [✏️ Éditer] [🗑️ Supprimer]                        │
│ └────────────────────────────────────────────────────────┘
├──────────────────────────────────────────────────────────┤
│ Sélection: 2 tâches | 125 min (5 Pomodoros)             │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Carte Tâche - HTML

```html
<div class="task-card" data-task-id="TASK001">
    <div class="task-header">
        <input type="checkbox" class="task-checkbox" id="task-TASK001">
        <label for="task-TASK001" class="task-title">
            <span class="priority-badge priority-1">P1</span>
            <span class="task-name">Révision mathématiques</span>
        </label>
        <span class="task-duration">75 min</span>
    </div>

    <div class="task-details">
        <div class="task-category">
            <span class="category-main">Études</span>
            <span class="category-separator">›</span>
            <span class="category-sub">Mathématiques</span>
        </div>
        <div class="task-deadline" title="Deadline">
            📅 15.11.25
        </div>
    </div>

    <div class="task-actions">
        <button class="btn-icon" onclick="editTask('TASK001')">✏️</button>
        <button class="btn-icon btn-danger" onclick="deleteTask('TASK001')">🗑️</button>
    </div>
</div>
```

### 5.3 Couleurs Priorités

```css
.priority-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: 700;
    margin-right: 8px;
}

.priority-1 { background: #dc2626; color: #ffffff; } /* P1 - Rouge */
.priority-2 { background: #f59e0b; color: #ffffff; } /* P2 - Orange */
.priority-3 { background: #3b82f6; color: #ffffff; } /* P3 - Bleu */
```

### 5.4 Modal Création/Édition

```html
<div class="modal" id="edit-pomodoro-modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Éditer Tâche Pomodoro</h2>
            <button class="close-btn" onclick="closeModal()">&times;</button>
        </div>

        <div class="modal-body">
            <div class="form-group">
                <label for="task-name">Titre *</label>
                <input type="text" id="task-name" required>
            </div>

            <div class="form-group">
                <label for="task-description">Description</label>
                <textarea id="task-description" rows="3"></textarea>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="task-duration">Durée (min) *</label>
                    <input type="number" id="task-duration" min="1" required>
                    <span class="helper-text">
                        = <span id="pomodoro-count">0</span> Pomodoros
                    </span>
                </div>
                <div class="form-group">
                    <label for="task-priority">Priorité *</label>
                    <select id="task-priority">
                        <option value="1">P1 - Haute</option>
                        <option value="2">P2 - Moyenne</option>
                        <option value="3" selected>P3 - Basse</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="task-category">Catégorie *</label>
                    <select id="task-category" onchange="loadSubcategories()">
                        <option value="">-- Choisir --</option>
                        <!-- Loaded from categories.csv -->
                    </select>
                    <button class="btn-icon" onclick="addCategory()" title="Ajouter">+</button>
                </div>
                <div class="form-group">
                    <label for="task-subcategory">Sous-catégorie *</label>
                    <select id="task-subcategory">
                        <option value="">-- Choisir --</option>
                        <!-- Loaded dynamically -->
                    </select>
                    <button class="btn-icon" onclick="addSubcategory()" title="Ajouter">+</button>
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">Annuler</button>
            <button class="btn btn-primary" onclick="saveTask()">Sauvegarder</button>
        </div>
    </div>
</div>
```

**Validation temps réel** :
```javascript
document.getElementById('task-duration').addEventListener('input', (e) => {
    const duration = parseInt(e.target.value) || 0;
    const pomodoros = Math.ceil(duration / 25);
    document.getElementById('pomodoro-count').textContent = pomodoros;
});
```

---

## 6️⃣ ONGLET PAUSES

### 6.1 Layout Onglet (2 Colonnes)

```
┌───────────────────────────────────────────────────────────────┐
│ ONGLET: PAUSES                                                 │
├───────────────────────────┬───────────────────────────────────┤
│ TÂCHES DISPONIBLES (50%)  │ PAUSES SÉLECTIONNÉES (50%)        │
│                           │                                   │
│ Recherche: [🔍 ...]       │ ⚠️ Ordre important : drag & drop  │
│ Catégorie: [Toutes ▼]     │ [📌 Épingler tout] [🗑️ Vider]    │
├───────────────────────────┼───────────────────────────────────┤
│ Respiration               │ Pauses épinglées (persistent):    │
│ ┌───────────────────────┐ │ ┌─────────────────────────────┐   │
│ │ 🫁 Méditation         │ │ │ 📌 🫁 Méditation           │   │
│ │ 10 min                │ │ │ 10 min               [🗑️] │   │
│ │ DRAG →                │ │ └─────────────────────────────┘   │
│ └───────────────────────┘ │                                   │
│ ┌───────────────────────┐ │ Pauses temporaires:               │
│ │ 🌬️ Respiration        │ │ ┌─────────────────────────────┐   │
│ │ profonde 5 min        │ │ │ 🌬️ Respiration profonde   │   │
│ │ DRAG →                │ │ │ 5 min                [🗑️] │   │
│ └───────────────────────┘ │ ├─────────────────────────────┤   │
│                           │ │ 🌬️ Respiration profonde   │   │
│ Entretien                 │ │ 5 min (duplicata)    [🗑️] │   │
│ ┌───────────────────────┐ │ └─────────────────────────────┘   │
│ │ 🪴 Arroser plantes    │ │                                   │
│ │ 10 min                │ │ Total: 3 pauses (25 min)          │
│ │ DRAG →                │ │                                   │
│ └───────────────────────┘ │ [Envoyer vers planning]           │
└───────────────────────────┴───────────────────────────────────┘
```

### 6.2 Carte Pause Source - HTML

```html
<div class="pause-source-item" draggable="true" data-task-id="R010">
    <div class="pause-icon">🫁</div>
    <div class="pause-info">
        <div class="pause-name">Méditation</div>
        <div class="pause-duration">10 min</div>
    </div>
    <div class="drag-indicator">⋮⋮</div>
</div>
```

### 6.3 Carte Pause Sélectionnée - HTML

```html
<div class="pause-selected-item" draggable="true" data-task-id="R010" data-index="0">
    <button class="pin-btn" onclick="togglePin(this)" title="Épingler (reste après refresh)">
        📌
    </button>
    <div class="pause-icon">🫁</div>
    <div class="pause-info">
        <div class="pause-name">Méditation</div>
        <div class="pause-duration">10 min</div>
    </div>
    <button class="btn-icon btn-danger" onclick="removePause(0)" title="Supprimer">
        🗑️
    </button>
    <div class="drag-handle">⋮⋮</div>
</div>
```

**Pause épinglée (style)** :
```css
.pause-selected-item.pinned {
    border-left: 4px solid #2563eb;
    background: linear-gradient(to right, #eff6ff 0%, #ffffff 100%);
}
```

### 6.4 Drag & Drop - JavaScript

```javascript
let draggedElement = null;

// Source panel
document.querySelectorAll('.pause-source-item').forEach(item => {
    item.addEventListener('dragstart', (e) => {
        draggedElement = e.currentTarget;
        e.currentTarget.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'copy';
    });

    item.addEventListener('dragend', (e) => {
        e.currentTarget.classList.remove('dragging');
        draggedElement = null;
    });
});

// Selected panel (drop zone)
const selectedPanel = document.getElementById('pause-selected-list');

selectedPanel.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    selectedPanel.classList.add('drag-over');
});

selectedPanel.addEventListener('dragleave', (e) => {
    selectedPanel.classList.remove('drag-over');
});

selectedPanel.addEventListener('drop', (e) => {
    e.preventDefault();
    selectedPanel.classList.remove('drag-over');

    if (!draggedElement) return;

    const taskId = draggedElement.dataset.taskId;
    const task = state.recurrentTasks.find(t => t.id === taskId);
    if (!task) return;

    // Add to selected list (allow duplicates)
    addPauseToSelected(task);
});

function addPauseToSelected(task) {
    const selectedList = document.getElementById('pause-selected-list');
    const newItem = createPauseSelectedItem(task, selectedList.children.length);
    selectedList.appendChild(newItem);

    // Update state
    state.selectedRespirationIds.push(task.id);

    // Update counter
    updatePauseCounter();
}
```

### 6.5 Bouton "Envoyer vers planning"

```html
<button id="send-to-planning-btn" class="btn btn-primary btn-block" onclick="sendPausesToPlanning()">
    Envoyer vers planning
</button>
```

**Style** :
```css
#send-to-planning-btn {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
}

#send-to-planning-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

#send-to-planning-btn:disabled {
    background: #cbd5e1;
    cursor: not-allowed;
}
```

**Comportement** :
```javascript
function sendPausesToPlanning() {
    // Collect selected pause IDs (preserve order and duplicates)
    const pauseItems = document.querySelectorAll('.pause-selected-item');
    state.selectedRespirationIds = Array.from(pauseItems).map(item => item.dataset.taskId);

    // Save state to server
    saveStateToServer();

    // Show notification
    showNotification('Pauses ajoutées au planning', 'success');

    // Optional: Switch to Pomodoro tab
    switchTab('pomodoro');
}
```

### 6.6 Épinglage (Pinned Pauses)

**Comportement** :
- Clic sur 📌 → Toggle épinglé/non-épinglé
- Épinglé → Bordure bleue à gauche, fond bleu clair
- Sauvegarde immédiate sur serveur (`POST /api/v2/gitfocus/pinned-pauses`)
- Au refresh page → Pauses épinglées rechargées automatiquement

```javascript
async function togglePin(button) {
    const item = button.closest('.pause-selected-item');
    const isPinned = item.classList.toggle('pinned');

    // Update icon
    button.textContent = isPinned ? '📌' : '📍';
    button.title = isPinned ? 'Désépingler' : 'Épingler (reste après refresh)';

    // Save to server
    await savePinnedPauses();
}

async function savePinnedPauses() {
    const pinnedItems = document.querySelectorAll('.pause-selected-item.pinned');
    const pinnedIds = Array.from(pinnedItems).map(item => item.dataset.taskId);

    try {
        const response = await fetch('/api/v2/gitfocus/pinned-pauses', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({pinned_ids: pinnedIds})
        });

        const data = await response.json();
        console.log('Pinned pauses saved:', data);

    } catch (error) {
        console.error('Error saving pinned pauses:', error);
    }
}
```

---

## 7️⃣ ONGLET RÉCURRENTES

### 7.1 Layout Onglet

```
┌──────────────────────────────────────────────────────────┐
│ ONGLET: TÂCHES RÉCURRENTES                    [+ Nouvelle]│
├──────────────────────────────────────────────────────────┤
│ Filtres: [Actives uniquement ☑] [Catégorie: Toutes ▼]   │
├──────────────────────────────────────────────────────────┤
│ LISTE TÂCHES RÉCURRENTES (Scrollable)                    │
│ ┌────────────────────────────────────────────────────────┤
│ │ [ON] 🪴 Arroser plantes                        10 min │
│ │      Récurrence: Tous les 2 jours                     │
│ │      Prochaine: 2025-11-06 (demain)                   │
│ │      [✏️ Éditer] [🗑️ Supprimer]                       │
│ ├────────────────────────────────────────────────────────┤
│ │ [OFF] 🧹 Ménage salon                          30 min │
│ │      Récurrence: Hebdomadaire (Samedi)                │
│ │      Prochaine: 2025-11-09                            │
│ │      [✏️ Éditer] [🗑️ Supprimer]                       │
│ └────────────────────────────────────────────────────────┘
├──────────────────────────────────────────────────────────┤
│ Total: 20 tâches | Actives: 12                           │
└──────────────────────────────────────────────────────────┘
```

### 7.2 Toggle Switch - HTML

```html
<label class="toggle-switch">
    <input type="checkbox" checked onchange="toggleRecurrentTask('REC001', this.checked)">
    <span class="toggle-slider"></span>
</label>
```

**Style CSS** :
```css
.toggle-switch {
    position: relative;
    display: inline-block;
    width: 50px;
    height: 24px;
}

.toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #cbd5e1; /* Gris = OFF */
    transition: 0.4s;
    border-radius: 24px;
}

.toggle-slider:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.4s;
    border-radius: 50%;
}

input:checked + .toggle-slider {
    background-color: #22c55e; /* Vert = ON */
}

input:checked + .toggle-slider:before {
    transform: translateX(26px);
}
```

**JavaScript** :
```javascript
async function toggleRecurrentTask(taskId, isActive) {
    try {
        const response = await fetch(`/api/v2/gitfocus/tasks/recurrent/${taskId}/toggle`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({is_active: isActive ? 1 : 0})
        });

        const data = await response.json();
        if (data.success) {
            showNotification(`Tâche ${isActive ? 'activée' : 'désactivée'}`, 'success');
        }

    } catch (error) {
        console.error('Error toggling task:', error);
        showNotification('Erreur lors de la mise à jour', 'error');
    }
}
```

---

## 8️⃣ PLANNING GÉNÉRÉ

### 8.1 Layout Planning (Panel Droit)

```
┌────────────────────────────────────────┐
│ PLANNING GÉNÉRÉ                  [🔄]  │
├────────────────────────────────────────┤
│ 10:00-10:25 │ Révision maths     │ 25'│
│             │ (1/3) 🟡           │    │
├────────────────────────────────────────┤
│ 10:25-10:35 │ Méditation         │ 10'│
│             │ 🔵                 │    │
├────────────────────────────────────────┤
│ 10:35-11:00 │ Révision maths     │ 25'│
│             │ (2/3) 🟡           │    │
├────────────────────────────────────────┤
│ 11:00-11:30 │ RDV médical 📅     │ 30'│
│             │ (Planifié) ⚠️      │    │
├────────────────────────────────────────┤
│ 12:00-13:00 │ TEMPS MORT 🚫      │ 60'│
│             │ Déjeuner           │    │
└────────────────────────────────────────┘
```

### 8.2 Slot Planning - HTML (TRÈS FIN = 30px hauteur)

```html
<div class="planning-slot slot-pomodoro" data-slot-id="0">
    <div class="slot-time">10:00-10:25</div>
    <div class="slot-name">
        Révision maths
        <span class="pomodoro-index">(1/3)</span>
    </div>
    <div class="slot-duration">25'</div>
    <div class="slot-type-indicator">🟡</div>
</div>
```

**Style CSS (COMPACT)** :
```css
.planning-slot {
    display: grid;
    grid-template-columns: 100px 1fr 40px 30px;
    align-items: center;
    gap: 8px;
    padding: 4px 8px; /* TRÈS COMPACT */
    min-height: 30px; /* TRÈS FIN */
    margin: 2px 0;
    border-radius: 4px;
    border-left: 3px solid transparent;
    font-size: 0.85em;
    transition: all 0.2s;
}

.planning-slot:hover {
    transform: translateX(5px);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.slot-time {
    font-size: 0.75em;
    color: #64748b;
    white-space: nowrap;
}

.slot-name {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap; /* TOUT SUR 1 LIGNE */
}

.pomodoro-index {
    font-size: 0.8em;
    color: #64748b;
    font-weight: 400;
    margin-left: 4px;
}

.slot-duration {
    text-align: right;
    font-size: 0.75em;
    color: #94a3b8;
}

.slot-type-indicator {
    font-size: 1.2em;
}
```

### 8.3 Couleurs par Type de Slot

**Pomodoro (Jaune)** :
```css
.slot-pomodoro {
    background: linear-gradient(to right, #fef3c7 0%, #fefce8 100%);
    border-left-color: #f59e0b;
}
```

**Respiration (Bleu)** :
```css
.slot-respiration {
    background: linear-gradient(to right, #dbeafe 0%, #eff6ff 100%);
    border-left-color: #3b82f6;
}
```

**Câlin (Rose)** :
```css
.slot-calin {
    background: linear-gradient(to right, #fce7f3 0%, #fdf2f8 100%);
    border-left-color: #ec4899;
}
```

**Clope (Gris)** :
```css
.slot-clope {
    background: linear-gradient(to right, #f3f4f6 0%, #f9fafb 100%);
    border-left-color: #6b7280;
}
```

**Tâche Planifiée (Jaune + bordure)** :
```css
.slot-planned {
    background: linear-gradient(to right, #fef3c7 0%, #fefce8 100%);
    border-left-color: #f59e0b;
    border: 1px solid #f59e0b;
}
```

**Tâche Planifiée Replanifiée (badge)** :
```html
<div class="slot-name">
    RDV médical
    <span class="rescheduled-badge" title="Prévu à 11:00, placé à 11:30">⚠️</span>
</div>
```

**Temps Mort (Rouge)** :
```css
.slot-temps_mort {
    background: linear-gradient(to right, #f3f4f6 0%, #e5e7eb 100%);
    border-left-color: #dc2626;
    opacity: 0.8;
}
```

**Buffer "Bientôt temps mort" (Orange italique)** :
```css
.slot-buffer {
    background: linear-gradient(to right, #fef3c7 0%, #fefce8 100%);
    border-left-color: #f59e0b;
    font-style: italic;
    opacity: 0.7;
}
```

### 8.4 Statistiques Footer - HTML

```html
<footer class="planning-stats">
    <div class="stat-item">
        <span class="stat-icon">🟡</span>
        <span class="stat-value" id="stat-pomodoros">8</span>
        <span class="stat-label">Pomodoros</span>
    </div>
    <div class="stat-separator">|</div>
    <div class="stat-item">
        <span class="stat-icon">⏱️</span>
        <span class="stat-value" id="stat-work-time">120</span>
        <span class="stat-label">min travail</span>
    </div>
    <div class="stat-separator">|</div>
    <div class="stat-item">
        <span class="stat-icon">🔵</span>
        <span class="stat-value" id="stat-pause-time">40</span>
        <span class="stat-label">min pauses</span>
    </div>
    <div class="stat-separator">|</div>
    <div class="stat-item">
        <span class="stat-icon">🕒</span>
        <span class="stat-value" id="stat-free-time">180</span>
        <span class="stat-label">min libres</span>
    </div>
</footer>
```

**Style** :
```css
.planning-stats {
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 12px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    font-size: 0.85em;
}

.stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}

.stat-value {
    font-size: 1.5em;
    font-weight: 700;
    color: #1e293b;
}

.stat-label {
    font-size: 0.8em;
    color: #64748b;
}
```

---

## 9️⃣ CHARTE GRAPHIQUE

### 9.1 Palette de Couleurs

```css
:root {
    /* Primary (Bleu) */
    --color-primary-50: #eff6ff;
    --color-primary-100: #dbeafe;
    --color-primary-500: #3b82f6;
    --color-primary-700: #2563eb;

    /* Warning (Orange/Jaune) */
    --color-warning-50: #fef3c7;
    --color-warning-100: #fefce8;
    --color-warning-500: #f59e0b;

    /* Danger (Rouge) */
    --color-danger-500: #dc2626;

    /* Success (Vert) */
    --color-success-500: #22c55e;

    /* Neutral (Gris) */
    --color-neutral-50: #f9fafb;
    --color-neutral-100: #f3f4f6;
    --color-neutral-200: #e5e7eb;
    --color-neutral-500: #6b7280;
    --color-neutral-700: #374151;
    --color-neutral-900: #1e293b;

    /* Semantic (Rose - Câlins) */
    --color-rose-50: #fdf2f8;
    --color-rose-100: #fce7f3;
    --color-rose-500: #ec4899;
}
```

### 9.2 Typographie

```css
:root {
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    --font-mono: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas, monospace;
}

body {
    font-family: var(--font-sans);
    font-size: 16px;
    line-height: 1.5;
    color: var(--color-neutral-900);
}

h1 { font-size: 2em; font-weight: 700; }
h2 { font-size: 1.5em; font-weight: 600; }
h3 { font-size: 1.25em; font-weight: 600; }
.small { font-size: 0.875em; }
.text-xs { font-size: 0.75em; }
```

### 9.3 Spacing (Système 4px)

```css
:root {
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-8: 32px;
    --space-10: 40px;
}
```

### 9.4 Ombres

```css
:root {
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
```

### 9.5 Animations

```css
:root {
    --transition-fast: 0.15s;
    --transition-base: 0.3s;
    --transition-slow: 0.5s;

    --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
    --ease-out: cubic-bezier(0, 0, 0.2, 1);
    --ease-in: cubic-bezier(0.4, 0, 1, 1);
}

.planning-slot {
    transition: all var(--transition-base) var(--ease-out);
}

.planning-slot:hover {
    transform: translateX(5px);
    box-shadow: var(--shadow-md);
}
```

---

# PARTIE III - ALGORITHME DE GÉNÉRATION

## 🔟 FLUX COMPLET (12 ÉTAPES)

### ÉTAPE 1 : Calcul Heure de Départ

**Déclencheur** : `DOMContentLoaded` (chargement page) OU clic bouton "Auto"

**Algorithme** :
```javascript
function calculateStartTime() {
    const now = new Date();
    const future = new Date(now.getTime() + 15 * 60000); // +15 minutes

    // Arrondir au prochain multiple de 5
    const minutes = future.getMinutes();
    const roundedMinutes = Math.ceil(minutes / 5) * 5;

    // Gérer overflow (58 → 60 → heure suivante)
    if (roundedMinutes >= 60) {
        future.setHours(future.getHours() + 1);
        future.setMinutes(0);
    } else {
        future.setMinutes(roundedMinutes);
    }

    future.setSeconds(0);
    future.setMilliseconds(0);

    return future;
}
```

**Exemple** :
- Maintenant = 13:07
- + 15 min = 13:22
- Arrondi à 5 = 13:25
- → `planningStartTime = new Date('2025-11-05T13:25:00')`

**Stockage** :
- `state.planningStartTime = future`
- Input UI mis à jour : `document.getElementById('planning-start-time').value = "13:25"`

### ÉTAPE 2 : Initialisation Système de Temps Relatif

**Point zéro** :
- `planningStartTime = 13:25` → **minute 0**
- Toute tâche positionnée en **minutes relatives**

**Conversions** :
```javascript
// Absolute → Relative
function dateTimeToMinutes(dateTime, planningStart) {
    return Math.floor((dateTime - planningStart) / 60000);
}

// Relative → Absolute
function minutesToDateTime(minutes, planningStart) {
    const absoluteTime = new Date(planningStart.getTime() + minutes * 60000);
    return {
        date: absoluteTime.toISOString().split('T')[0],
        time: absoluteTime.toTimeString().substring(0, 5)
    };
}
```

**Exemples** :
- 13:25 (planningStart) → minute 0
- 13:55 (30 min plus tard) → minute 30
- 14:25 (1h plus tard) → minute 60
- 12:25 (1h avant) → minute -60

### ÉTAPE 3 : Ajout Tâches de Travail (Pomodoros)

**Source** : Tâches cochées dans onglet Pomodoro (`state.selectedPomodoroIds`)

**Conversion en Pomodoros** :
```python
# Backend Python
pomodoro_list = []

for task_id in selected_pomodoro_ids:
    task = get_task_by_id(task_id)  # From LISTE_MERE.v2.csv
    nb_pomodoros = math.ceil(task['remaining_min'] / 25)

    for i in range(nb_pomodoros):
        pomodoro_list.append({
            'type': 'POMODORO',
            'task_id': task['id'],
            'task_name': task['name'],
            'duration': 25,
            'pomodoro_index': i + 1,
            'pomodoro_total': nb_pomodoros
        })
```

**Exemple** :
- Tâche 75 min → 3 Pomodoros (75 / 25 = 3)
- Tâche 80 min → 4 Pomodoros (80 / 25 = 3.2 → arrondi 4)
- Tâche 50 min → 2 Pomodoros (50 / 25 = 2)

**Résultat** :
```python
[
    {'type': 'POMODORO', 'task_name': 'Révision maths', 'duration': 25, 'pomodoro_index': 1, 'pomodoro_total': 3},
    {'type': 'POMODORO', 'task_name': 'Révision maths', 'duration': 25, 'pomodoro_index': 2, 'pomodoro_total': 3},
    {'type': 'POMODORO', 'task_name': 'Révision maths', 'duration': 25, 'pomodoro_index': 3, 'pomodoro_total': 3},
    {'type': 'POMODORO', 'task_name': 'Rapport projet', 'duration': 25, 'pomodoro_index': 1, 'pomodoro_total': 2},
    {'type': 'POMODORO', 'task_name': 'Rapport projet', 'duration': 25, 'pomodoro_index': 2, 'pomodoro_total': 2}
]
```

**Important** : À ce stade, **PAS D'HEURES** calculées (juste nom + durée)

### ÉTAPE 4 : Ajout Respirations

**Source** : Pauses glissées dans onglet Pauses (`state.selectedRespirationIds`)

**Duplicatas autorisés** :
```python
# Backend Python
respiration_list = []

for task_id in selected_respiration_ids:  # Peut contenir duplicatas (ex: ['R010', 'R018', 'R018'])
    task = get_recurrent_task_by_id(task_id)  # From TACHES_RECURRENTES.v2.csv
    respiration_list.append({
        'type': 'RESPIRATION',
        'task_id': task['id'],
        'task_name': task['name'],
        'duration': task['duration_min']
    })
```

**Exemple** :
```python
[
    {'type': 'RESPIRATION', 'task_name': 'Méditation', 'duration': 10},
    {'type': 'RESPIRATION', 'task_name': 'Respiration profonde', 'duration': 5},
    {'type': 'RESPIRATION', 'task_name': 'Respiration profonde', 'duration': 5}  # Duplicata intentionnel
]
```

### ÉTAPE 5 : Alternance Pomodoro/Respiration

**Algorithme** :

**CAS A : Respirations sélectionnées** (liste non vide)
```python
alternated_list = []
respiration_index = 0

for pomodoro in pomodoro_list:
    # Ajouter Pomodoro
    alternated_list.append(pomodoro)

    # Ajouter Respiration (cycling)
    if len(respiration_list) > 0:
        resp = respiration_list[respiration_index % len(respiration_list)]
        alternated_list.append(resp)
        respiration_index += 1
```

**Exemple (5 Pomodoros + 3 Respirations)** :
```
P1 (Révision maths)
R1 (Méditation, 10 min)
P2 (Révision maths)
R2 (Respiration profonde, 5 min)
P3 (Révision maths)
R3 (Respiration profonde, 5 min) [duplicata]
P4 (Rapport projet)
R1 (Méditation, 10 min) [cycle recommence]
P5 (Rapport projet)
R2 (Respiration profonde, 5 min) [cycle continue]
```

**CAS B : Aucune respiration** (Mode Focus)
```python
alternated_list = pomodoro_list  # Seulement Pomodoros, pas d'alternance
```

**CAS C : Option "Pauses consécutives" + 0 Pomodoros**
```python
alternated_list = respiration_list  # Journée de respirations uniquement
```

### ÉTAPE 6 : Insertion Câlins (si option cochée)

**Règle** : 1 câlin tous les 2 respirations, **AVANT** la respiration

**Algorithme** :
```python
if calin_enabled:
    respiration_count = 0
    i = 0

    while i < len(alternated_list):
        if alternated_list[i]['type'] == 'RESPIRATION':
            respiration_count += 1

            if respiration_count % 2 == 0:
                # Insérer câlin AVANT cette respiration
                alternated_list.insert(i, {
                    'type': 'CALIN',
                    'task_name': 'Câlin',
                    'duration': 10,
                    'auto_generated': True
                })
                i += 1  # Sauter le câlin qu'on vient d'insérer

        i += 1
```

**Exemple** :
```
P1
R1 (count = 1)
P2
Câlin ← Inséré ici car count = 2
R2 (count = 2)
P3
R3 (count = 3)
P4
Câlin ← Inséré ici car count = 4
R4 (count = 4)
```

### ÉTAPE 7 : Insertion Clopes (si option cochée)

**Règle** : 1 clope tous les X minutes cumulées (Pomodoros + Respirations + Câlins)

**Algorithme** :
```python
if clope_enabled:
    cumulative_duration = 0
    i = 0

    while i < len(alternated_list):
        cumulative_duration += alternated_list[i]['duration']

        if cumulative_duration >= clope_interval_min:
            # Insérer clope APRÈS cette tâche
            alternated_list.insert(i + 1, {
                'type': 'CLOPE',
                'task_name': 'Pause cigarette',
                'duration': 5,
                'auto_generated': True
            })

            # Réinitialiser compteur
            cumulative_duration = 0

            i += 1  # Sauter la clope

        i += 1
```

**Exemple (intervalle = 120 min)** :
```
P1 (25) → cumul = 25
R1 (10) → cumul = 35
P2 (25) → cumul = 60
Câlin (10) → cumul = 70
R2 (5) → cumul = 75
P3 (25) → cumul = 100
R3 (5) → cumul = 105
P4 (25) → cumul = 130 ≥ 120 !
Clope (5) ← Insérée ici, cumul reset à 0
R4 (15) → cumul = 15
...
```

### ÉTAPE 8 : Chargement Temps Morts (CSV)

**Fichier** : `temps_morts.csv`

**Filtre** : Charger UNIQUEMENT pour la date sélectionnée

**Conversion en temps relatif** :
```python
temps_morts_linear = []

for tm in temps_morts_csv:
    if tm['date'] != selected_date:
        continue  # Skip autres dates

    # Construire datetime absolus
    start_datetime = datetime.strptime(f"{tm['date']} {tm['heure_debut']}", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(f"{tm['date']} {tm['heure_fin']}", "%Y-%m-%d %H:%M")

    # Convertir en minutes relatives
    start_minute = (start_datetime - planning_start_time).total_seconds() / 60
    end_minute = (end_datetime - planning_start_time).total_seconds() / 60

    temps_morts_linear.append({
        'start_minute': int(start_minute),
        'end_minute': int(end_minute),
        'titre': tm['titre']
    })

# Trier par start_minute croissant
temps_morts_linear.sort(key=lambda x: x['start_minute'])
```

**Exemple** :
```python
# planning_start_time = 10:00 (minute 0)
[
    {'start_minute': -120, 'end_minute': -60, 'titre': 'Déjeuner'},  # 12:00-13:00 → -120 à -60 (AVANT le point zéro)
    {'start_minute': 120, 'end_minute': 180, 'titre': 'RDV médical'}  # 14:00-15:00 → 120 à 180
]
```

**Filtrage** :
- Temps_morts complètement passés (end_minute < 0) → Conservés (peuvent bloquer placement)
- Temps_morts très loin futurs (start_minute > 30 jours = 43200 min) → Filtrés

### ÉTAPE 9 : Chargement Tâches Planifiées (CSV)

**Fichier** : `TACHES_PLANIFIEES.v2.csv`

**Filtre** : Charger UNIQUEMENT pour la date sélectionnée

**Conversion en temps relatif** :
```python
taches_planifiees_linear = []

for tp in taches_planifiees_csv:
    # Parser PLANNED_START (format: "DD.MM.YY HH:MM")
    planned_start = datetime.strptime(tp['planned_start'], "%d.%m.%y %H:%M")

    if planned_start.date() != selected_date:
        continue  # Skip autres dates

    # Convertir en minutes relatives
    start_minute = (planned_start - planning_start_time).total_seconds() / 60

    taches_planifiees_linear.append({
        'id': tp['id'],
        'name': tp['name'],
        'duration': tp['duration_min'],
        'start_minute': int(start_minute)
    })

# Trier par start_minute croissant
taches_planifiees_linear.sort(key=lambda x: x['start_minute'])
```

**Exemple** :
```python
# planning_start_time = 10:00 (minute 0)
[
    {'id': 'PLAN002', 'name': 'Cours Python', 'duration': 45, 'start_minute': 0},  # 10:00 = minute 0
    {'id': 'PLAN001', 'name': 'RDV dentiste', 'duration': 30, 'start_minute': 270}  # 14:30 = minute 270
]
```

### ÉTAPE 10 : Conversion Timeline → Planning (avec heures)

**PRINCIPE CLÉS** :
- Parcourir `alternated_list` **une seule fois, dans l'ordre**
- Calculer heures en **ajoutant séquentiellement** les durées
- Gérer collisions **au fur et à mesure**

**Algorithme complet** :

```python
planning = []
current_minute = 0  # Minute relative (0 = planningStartTime)
temps_morts_index = 0
taches_planifiees_index = 0

for task in alternated_list:
    task_end = current_minute + task['duration']

    # ============================================
    # 10.1 : Vérifier collision avec temps_morts
    # ============================================
    while temps_morts_index < len(temps_morts_linear):
        tm = temps_morts_linear[temps_morts_index]

        # Temps_mort déjà passé → Skip
        if tm['end_minute'] <= current_minute:
            temps_morts_index += 1
            continue

        # Temps_mort APRÈS cette tâche → Pas de collision
        if tm['start_minute'] >= task_end:
            break

        # CAS DE COLLISION
        # Sous-cas A: Trou AVANT le temps_mort
        if current_minute < tm['start_minute']:
            gap_duration = tm['start_minute'] - current_minute

            # Insérer buffer "Bientôt temps mort"
            planning.append({
                'type': 'buffer',
                'task_name': 'Bientôt temps mort',
                'heure_debut_relative': current_minute,
                'duration': gap_duration
            })

            current_minute = tm['start_minute']

        # Insérer temps_mort dans planning
        planning.append({
            'type': 'temps_mort',
            'task_name': tm['titre'],
            'heure_debut_relative': tm['start_minute'],
            'duration': tm['end_minute'] - tm['start_minute']
        })

        # Avancer APRÈS le temps_mort
        current_minute = tm['end_minute']
        temps_morts_index += 1

        # Recalculer fin de tâche
        task_end = current_minute + task['duration']

    # ============================================
    # 10.2 : Vérifier collision avec tâches planifiées
    # ============================================
    while taches_planifiees_index < len(taches_planifiees_linear):
        tp = taches_planifiees_linear[taches_planifiees_index]

        # Tâche planifiée déjà passée → Skip
        if tp['start_minute'] + tp['duration'] <= current_minute:
            taches_planifiees_index += 1
            continue

        # Tâche planifiée APRÈS cette tâche → Pas de collision
        if tp['start_minute'] >= task_end:
            break

        # CAS DE COLLISION
        # Sous-cas A: Trou AVANT la tâche planifiée
        if current_minute < tp['start_minute']:
            # Avancer début tâche planifiée pour boucher le trou
            adjusted_start = current_minute
            adjusted_end = adjusted_start + tp['duration']

            planning.append({
                'type': 'planned',
                'task_name': tp['name'],
                'task_id': tp['id'],
                'heure_debut_relative': adjusted_start,
                'duration': tp['duration'],
                'original_time': tp['start_minute'],
                'rescheduled': True
            })

            current_minute = adjusted_end

        else:
            # Pas de trou, placer à current_minute
            planning.append({
                'type': 'planned',
                'task_name': tp['name'],
                'task_id': tp['id'],
                'heure_debut_relative': current_minute,
                'duration': tp['duration'],
                'original_time': tp['start_minute'],
                'rescheduled': (current_minute != tp['start_minute'])
            })

            current_minute += tp['duration']

        taches_planifiees_index += 1
        task_end = current_minute + task['duration']

    # ============================================
    # 10.3 : Insérer la tâche normalement
    # ============================================
    planning.append({
        'type': task['type'],
        'task_name': task['task_name'],
        'task_id': task.get('task_id'),
        'heure_debut_relative': current_minute,
        'duration': task['duration'],
        'pomodoro_index': task.get('pomodoro_index'),
        'pomodoro_total': task.get('pomodoro_total')
    })

    current_minute = task_end
```

**Clarifications** :

**"Collision"** = Chevauchement (même partiel)
- Tâche 13:50-14:10, temps_mort 14:00-15:00 → COLLISION (10 min de chevauchement)

**Slot "Bientôt temps mort"** :
- Type: `'buffer'`
- Nom: `"Bientôt temps mort"`
- Inséré si trou ≥ 1 minute
- Style: Fond orange clair, italique, opacité 70%

**Reprendre après obstacle** :
- La tâche annulée (collision) est automatiquement réessayée APRÈS l'obstacle
- `current_minute` avance après obstacle, `task_end` recalculé
- Loop continue avec la même tâche (étape 10.3)

### ÉTAPE 11 : Arrêt Planning & Finalisation

**Condition d'arrêt** : Tous les Pomodoros de `alternated_list` traités

**Ignoré** :
- Temps_morts APRÈS le dernier Pomodoro
- Tâches planifiées APRÈS le dernier Pomodoro

**Conversion temps relatif → temps absolu** :
```python
for slot in planning:
    # Convertir heure_debut_relative → date + heure absolue
    absolute_start = planning_start_time + timedelta(minutes=slot['heure_debut_relative'])
    absolute_end = absolute_start + timedelta(minutes=slot['duration'])

    slot['date'] = absolute_start.strftime('%Y-%m-%d')
    slot['heure_debut'] = absolute_start.strftime('%H:%M')
    slot['heure_fin'] = absolute_end.strftime('%H:%M')

    # Nettoyer
    del slot['heure_debut_relative']
```

**Calcul statistiques** :
```python
statistics = {
    'total_pomodoros': count(planning, type='pomodoro'),
    'total_respirations': count(planning, type='respiration'),
    'total_calins': count(planning, type='calin'),
    'total_clopes': count(planning, type='clope'),
    'total_work_time': sum(durations, type='pomodoro'),
    'total_pause_time': sum(durations, type in ['respiration', 'calin', 'clope']),
    'total_planned': count(planning, type='planned'),
    'total_temps_morts': count(planning, type='temps_mort')
}
```

### ÉTAPE 12 : Retour JSON au Frontend

**Format réponse** :
```json
{
    "success": true,
    "planning": [
        {
            "date": "2025-11-05",
            "heure_debut": "10:00",
            "heure_fin": "10:25",
            "task_name": "Révision maths",
            "task_id": "TASK001",
            "type": "pomodoro",
            "duration_min": 25,
            "pomodoro_index": 1,
            "pomodoro_total": 3
        },
        {
            "date": "2025-11-05",
            "heure_debut": "10:25",
            "heure_fin": "10:35",
            "task_name": "Méditation",
            "task_id": "R010",
            "type": "respiration",
            "duration_min": 10
        },
        ...
    ],
    "statistics": {
        "total_work_min": 300,
        "total_pause_min": 60,
        "pomodoro_count": 12,
        "respiration_count": 12,
        "calin_count": 6,
        "clope_count": 2,
        "planned_count": 1,
        "temps_mort_count": 3
    }
}
```

---

## 1️⃣1️⃣ GESTION DES COLLISIONS

### 11.1 Priorités en Cas de Conflit

**Ordre de priorité** (du plus fort au plus faible) :
1. **Temps mort** (priorité absolue) - JAMAIS déplacé
2. **Tâche planifiée** (priorité secondaire) - Peut être décalée, garde sa durée
3. **Pomodoro/Respiration/Câlin/Clope** - Placés dans les trous

### 11.2 Cas : Tâche Planifiée Pendant Temps Mort

**Scénario** :
- Temps_mort: 14:00-15:00
- Tâche planifiée: 14:30 (demandée à cette heure)

**Résolution** :
1. Placer temps_mort d'abord (14:00-15:00)
2. Placer tâche planifiée juste après (15:00)
3. **PAS de respiration** entre temps_mort et tâche planifiée (exception à l'alternance)

**Code** :
```python
# Dans ÉTAPE 10.2
if tp['start_minute'] >= tm['start_minute'] and tp['start_minute'] < tm['end_minute']:
    # Tâche planifiée PENDANT temps_mort
    # → Placer APRÈS le temps_mort, sans respiration entre
    planning.append({
        'type': 'planned',
        'task_name': tp['name'],
        'heure_debut_relative': tm['end_minute'],  # Juste après temps_mort
        'duration': tp['duration'],
        'original_time': tp['start_minute'],
        'rescheduled': True
    })
    current_minute = tm['end_minute'] + tp['duration']
```

### 11.3 Cas : Plusieurs Temps Morts Consécutifs

**Scénario** :
- Temps_mort 1: 12:00-13:00 (déjeuner)
- Temps_mort 2: 13:00-14:00 (sieste)

**Résolution** :
- Les temps_morts sont insérés séquentiellement
- `current_minute` avance après chaque temps_mort
- Prochaine tâche placée à 14:00

**Résultat** :
```
10:00-10:25  Pomodoro 1
10:25-10:35  Respiration 1
...
11:30-12:00  Pomodoro X
12:00-13:00  TEMPS MORT (Déjeuner)
13:00-14:00  TEMPS MORT (Sieste)
14:00-14:25  Pomodoro X+1 ← Reprend ici
```

---

## 1️⃣2️⃣ CAS PARTICULIERS

### 12.1 Cas : 0 Pomodoros Sélectionnés

**Comportement** :
- Erreur affichée : "Sélectionnez au moins 1 tâche de travail"
- Bouton "Générer Planning" désactivé

**Alternative** : Autoriser si option "Pauses consécutives" cochée
- Planning = SEULEMENT respirations (journée de ménage, soins, etc.)

### 12.2 Cas : 0 Respirations Sélectionnées

**Comportement** : **Mode Focus**
- Planning = SEULEMENT Pomodoros (pas d'alternance)
- Câlins et Clopes **NE SONT PAS** insérés (car algorithme nécessite respirations pour compter)

**Exemple** :
```
10:00-10:25  Pomodoro 1
10:25-10:50  Pomodoro 2
10:50-11:15  Pomodoro 3
...
```

### 12.3 Cas : Cycling Illimité

**Question** : 81 Pomodoros + 3 Respirations ?

**Réponse** : **OUI, cycling illimité**
- 81 Pomodoros → 81 respirations (27 fois chaque respiration)
- Pattern : R1, R2, R3, R1, R2, R3, R1, R2, R3... (27 cycles)

**Pas de limite**

### 12.4 Cas : Duplicatas Intentionnels

**Question** : Utilisateur drag 3 fois la même respiration ?

**Réponse** : **OUI, autorisé**
- Liste sélectionnée : [Méditation, Méditation, Méditation]
- Alternance : P1, Méd, P2, Méd, P3, Méd, P4, Méd (loop)...

**Cas d'usage** : Utilisateur veut faire UNIQUEMENT méditation entre chaque Pomodoro

### 12.5 Cas : Débordement Jour Suivant

**Question** : Planning commence 22:00, 10 Pomodoros (250 min = 4h10)

**Comportement** : **Support multi-jours**
```
2025-11-05 22:00-22:25  Pomodoro 1
2025-11-05 22:25-22:35  Respiration 1
2025-11-05 22:35-23:00  Pomodoro 2
2025-11-05 23:00-23:10  Respiration 2
2025-11-05 23:10-23:35  Pomodoro 3
2025-11-05 23:35-23:45  Respiration 3
2025-11-05 23:45-00:10  Pomodoro 4 (déborde sur 2025-11-06)
2025-11-06 00:10-00:20  Respiration 4
2025-11-06 00:20-00:45  Pomodoro 5
...
```

**Gestion** :
- Temps_morts du jour suivant (2025-11-06) **DOIVENT** être chargés aussi
- Colonne `date` change automatiquement dans le planning
- Frontend affiche séparateur visuel "--- Jour suivant ---"

### 12.6 Cas : Intervalle Clope = 0

**Comportement** : **Validation frontend**
- Input `<input type="number" min="1">` → Empêche 0
- Si utilisateur force 0 (DevTools) → Backend rejette (400 Bad Request)

### 12.7 Cas : Tous Créneaux Occupés (Temps Morts)

**Scénario** : Toute la journée bloquée par temps_morts

**Comportement** :
- Aucun Pomodoro placé
- Planning = SEULEMENT temps_morts
- Statistiques : 0 Pomodoros, 0 travail

**Notification** : "Aucun créneau libre disponible pour la date sélectionnée"

---

# PARTIE IV - FICHIERS DE DONNÉES

## 1️⃣3️⃣ FICHIERS CSV

### 13.1 LISTE_MERE.v2.csv (Tâches Pomodoro)

**Délimiteur** : `;` (point-virgule)
**Encodage** : UTF-8
**Quoting** : ALL (toutes les valeurs entre guillemets)

**Format** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
```

**Colonnes** :

| Colonne | Type | Requis | Description | Exemple |
|---------|------|--------|-------------|---------|
| ID | string | ✅ | `TASK` + 3 chiffres | `"TASK001"` |
| NAME | string | ✅ | Titre (max 100 car) | `"Révision maths"` |
| DESCRIPTION | string | ❌ | Description détaillée | `"Chapitres 3-4"` |
| CATEGORY | string | ✅ | Catégorie principale | `"Études"` |
| SUB_CATEGORY | string | ✅ | Sous-catégorie | `"Mathématiques"` |
| DURATION_MIN | int | ✅ | Durée totale estimée | `"75"` |
| REMAINING_MIN | int | ✅ | Durée restante (≤ DURATION) | `"75"` |
| PRIORITY | int | ✅ | 1=Haute, 2=Moyenne, 3=Basse | `"1"` |
| TAGS | string | ❌ | Tags séparés par virgules | `"urgent,exam"` |
| KEYWORDS | string | ❌ | Mots-clés recherche | `"algèbre"` |
| DEPENDENCIES | string | ❌ | IDs tâches dépendantes | `"TASK002"` |
| NOTES | string | ❌ | Notes libres | `"Voir prof"` |
| DEADLINE | string | ❌ | Format DD.MM.YY | `"15.11.25"` |
| FIXED_START | string | ❌ | Format HH:MM (RDV fixe, non utilisé en V3) | `""` |
| PLANNED_START | string | ❌ | Format DD.MM.YY HH:MM (non utilisé, voir TACHES_PLANIFIEES) | `""` |
| STATUS | string | ❌ | `todo`, `in_progress`, `done` | `""` (vide = todo) |

**Exemple** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
"TASK001";"Révision mathématiques";"Chapitres 3 et 4 algèbre linéaire";"Études";"Mathématiques";"75";"75";"1";"urgent,examen";"algèbre,matrices";"";"Revoir exercices 12-15";"15.11.25";"";"";""
"TASK002";"Rapport de projet";"Rédiger section résultats et conclusion";"Travail";"Documentation";"50";"50";"2";"travail";"rapport,doc";"TASK001";"Attendre validation chef";"20.11.25";"";"";""
```

**Règles Validation** :
- `REMAINING_MIN` ≤ `DURATION_MIN` (sinon: erreur backend)
- `PRIORITY` ∈ {1, 2, 3} (sinon: défaut 3)
- Tous les champs string DOIVENT être quotés (même vides: `""`)

### 13.2 TACHES_RECURRENTES.v2.csv (Récurrentes + Respirations)

**⚠️ MIGRATION 2025-11-05** : Fusion de `TACHES_RESPIRATOIRES.v2.csv` dans ce fichier

**Format** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE"
```

**Colonnes** :

| Colonne | Type | Requis | Description | Exemple |
|---------|------|--------|-------------|---------|
| ID | string | ✅ | `R` + 3 chiffres OU `REC` + 3 chiffres | `"R010"`, `"REC001"` |
| NAME | string | ✅ | Nom tâche | `"Méditation"` |
| DESCRIPTION | string | ❌ | Description | `"Méditation guidée 10 min"` |
| CATEGORY | string | ✅ | Catégorie | `"Respiration"`, `"Entretien"` |
| SUB_CATEGORY | string | ✅ | Sous-catégorie | `"Méditation"`, `"Plantes"` |
| DURATION_MIN | int | ✅ | Durée | `"10"` |
| RECURRENCE_TYPE | string | ✅ | `daily`, `weekly`, `monthly`, `interval` | `"daily"` |
| RECURRENCE_INTERVAL | int | ✅ | Nb jours (si `interval`) ou jour semaine (1-7) | `"2"` (tous les 2 jours) |
| LAST_DONE_DATE | string | ❌ | Format YYYY-MM-DD | `"2025-11-04"` |
| NEXT_DUE_DATE | string | ❌ | Format YYYY-MM-DD | `"2025-11-05"` |
| PRIORITY | int | ✅ | 1, 2, ou 3 | `"2"` |
| STATUS | string | ❌ | `todo`, `done` | `""` |
| IS_ACTIVE | int | ✅ | 0=Inactif, 1=Actif | `"1"` |

**Exemple** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE"
"R010";"Méditation";"Méditation guidée 10 min";"Respiration";"Méditation";"10";"daily";"1";"2025-11-04";"2025-11-05";"2";"";"1"
"R018";"Respiration profonde";"Exercices respiration profonde";"Respiration";"Exercices";"5";"daily";"1";"2025-11-04";"2025-11-05";"2";"";"1"
"REC001";"Arroser plantes";"Arrosage plantes appartement";"Entretien";"Plantes";"10";"interval";"2";"2025-11-04";"2025-11-06";"3";"";"1"
"REC002";"Ménage salon";"Nettoyage complet salon";"Entretien";"Ménage";"30";"weekly";"6";"2025-11-02";"2025-11-09";"3";"";"0"
```

**Règles Validation** :
- `IS_ACTIVE` ∈ {0, 1} (obligatoire)
- Si `RECURRENCE_TYPE = "interval"` → `RECURRENCE_INTERVAL` = nb jours (≥ 1)
- Si `RECURRENCE_TYPE = "weekly"` → `RECURRENCE_INTERVAL` = jour semaine (1=Lundi, 7=Dimanche)
- Si `RECURRENCE_TYPE = "daily"` → `RECURRENCE_INTERVAL` = 1 (ignoré)
- Si `RECURRENCE_TYPE = "monthly"` → `RECURRENCE_INTERVAL` = jour du mois (1-31)

### 13.3 TACHES_PLANIFIEES.v2.csv (Tâches avec Heure Fixe)

**Format** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
```

**Différence avec LISTE_MERE** : Colonne `PLANNED_START` obligatoirement remplie

**Exemple** :
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
"PLAN001";"RDV dentiste";"Détartrage annuel";"Santé";"Médical";"30";"30";"1";"rdv";"";"";"Amener carte vitale";"05.11.25";"";"05.11.25 14:30";""
"PLAN002";"Cours en ligne Python";"Formation Udemy Python avancé";"Formation";"Python";"45";"45";"2";"formation";"python";"";"";"05.11.25";"";"05.11.25 10:00";""
```

**Usage** :
- Ces tâches seront automatiquement intégrées dans le planning (ÉTAPE 9-10)
- Placement au plus proche de l'heure demandée (ou plus tard si collision)
- Badge "Replanifiée" si heure finale ≠ heure demandée

### 13.4 temps_morts.csv (Créneaux Bloqués)

**Format** :
```csv
"DATE";"HEURE_DEBUT";"HEURE_FIN";"TYPE";"TITRE"
```

**Exemple** :
```csv
"DATE";"HEURE_DEBUT";"HEURE_FIN";"TYPE";"TITRE"
"2025-11-05";"00:00";"06:30";"dodo";"Sommeil"
"2025-11-05";"12:00";"13:00";"repas";"Déjeuner"
"2025-11-05";"18:00";"19:00";"repas";"Dîner"
"2025-11-05";"22:00";"23:59";"dodo";"Préparation sommeil"
```

**Règles** :
- `HEURE_FIN` > `HEURE_DEBUT` (sinon: erreur)
- Créneaux peuvent chevaucher (priorité au premier)
- Filtrés par `DATE` lors du chargement (backend)
- `TYPE` : valeur libre (`dodo`, `repas`, `rdv`, `transport`, etc.)

### 13.5 categories.csv (Catégories Centralisées)

**Format** :
```csv
"CATEGORY";"SUB_CATEGORY"
```

**Exemple** :
```csv
"CATEGORY";"SUB_CATEGORY"
"Études";"Mathématiques"
"Études";"Physique"
"Études";"Programmation"
"Travail";"Documentation"
"Travail";"Réunions"
"Travail";"Développement"
"Santé";"Médical"
"Santé";"Sport"
"Entretien";"Ménage"
"Entretien";"Plantes"
"Respiration";"Méditation"
"Respiration";"Exercices"
```

**Utilisation** :
- Chargé au démarrage (frontend)
- Alimente dropdowns catégorie/sous-catégorie
- Partagé entre TOUS types de tâches
- Bouton "+" pour ajout rapide (modal popup)

### 13.6 planned.csv (Planning Exporté)

**Format** :
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"KIND";"ORIGINAL_TIME"
```

**Exemple** :
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"KIND";"ORIGINAL_TIME"
"TASK001";"Révision maths";"2025-11-05";"10:00";"10:25";"25";"pomodoro";""
"R010";"Méditation";"2025-11-05";"10:25";"10:35";"10";"respiration";""
"PLAN001";"RDV dentiste";"2025-11-05";"14:30";"15:00";"30";"planned";"14:30"
"AUTO_CLOPE";"Pause cigarette";"2025-11-05";"12:00";"12:05";"5";"clope";""
"TEMPS_MORT";"Déjeuner";"2025-11-05";"12:30";"13:30";"60";"temps_mort";""
```

**Comportement** :
- **Écrasé** à chaque export (pas append)
- Contient le dernier planning généré uniquement
- `KIND` : `pomodoro`, `respiration`, `calin`, `clope`, `planned`, `temps_mort`
- `ORIGINAL_TIME` : Heure initialement demandée (si replanifié)

### 13.7 respiration_planning_history.csv (Historique Cumulatif)

**Format** :
```csv
"ID";"NAME";"DATE";"PLANNED_TIME";"DURATION_MIN";"EXPORT_TIMESTAMP"
```

**Exemple** :
```csv
"ID";"NAME";"DATE";"PLANNED_TIME";"DURATION_MIN";"EXPORT_TIMESTAMP"
"R010";"Méditation";"2025-11-04";"10:30";"10";"2025-11-04T09:15:23"
"R018";"Respiration profonde";"2025-11-04";"11:00";"5";"2025-11-04T09:15:23"
"R010";"Méditation";"2025-11-05";"10:25";"10";"2025-11-05T08:42:11"
"R018";"Respiration profonde";"2025-11-05";"11:00";"5";"2025-11-05T08:42:11"
```

**Comportement** :
- **Append** à chaque export (cumulatif)
- Permet analyse statistique (tâches les plus planifiées, heures préférées)
- `EXPORT_TIMESTAMP` : ISO 8601 format (`YYYY-MM-DDTHH:MM:SS`)

---

## 1️⃣4️⃣ FICHIERS JSON

### 14.1 planning_state.json (État Utilisateur)

**Contenu** :
```json
{
    "current_date": "2025-11-05",
    "planning_start_time": "14:00",
    "planning_start_locked": false,
    "selected_pomodoro_ids": ["TASK001", "TASK002", "TASK003"],
    "selected_respiration_ids": ["R010", "R018", "R018"],
    "calin_enabled": true,
    "clope_enabled": true,
    "clope_interval_min": 120,
    "last_updated": "2025-11-05T14:32:15"
}
```

**Mise à jour** :
- À chaque modification de sélection (checkboxes Pomodoro, drag & drop Pauses)
- À chaque changement d'options (Câlins, Clopes)
- Écriture atomique (temp file + rename)

**Endpoint** :
- `GET /api/v2/gitfocus/state` → Charger état
- `POST /api/v2/gitfocus/state` → Sauvegarder état

### 14.2 pinned_pauses.json (Pauses Épinglées)

**Contenu** :
```json
{
    "pinned_ids": ["R010", "R018", "R022"],
    "last_updated": "2025-11-05T10:15:00"
}
```

**Comportement** :
- Sauvegardé à chaque épinglage/désépinglage (clic sur 📌)
- Chargé au démarrage de l'onglet Pauses
- IDs épinglés apparaissent automatiquement dans liste sélectionnée (avec bordure bleue)

**Endpoint** :
- `GET /api/v2/gitfocus/pinned-pauses` → Charger IDs épinglés
- `POST /api/v2/gitfocus/pinned-pauses` → Sauvegarder IDs épinglés

### 14.3 user_config.json (Configuration Générale)

**Contenu** :
```json
{
    "clopes_interval_min": 120,
    "calin_duration_min": 10,
    "default_pomodoro_duration": 25,
    "planning_start_auto_calculate": true,
    "theme": "light",
    "language": "fr",
    "last_updated": "2025-11-05T08:00:00"
}
```

**Paramètres** :

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| clopes_interval_min | int | 120 | Intervalle entre clopes |
| calin_duration_min | int | 10 | Durée câlins |
| default_pomodoro_duration | int | 25 | Durée Pomodoro (fixe) |
| planning_start_auto_calculate | bool | true | Auto-calcul heure départ |
| theme | string | "light" | Thème (`light`, `dark`) |
| language | string | "fr" | Langue (`fr`, `en`) |

**Endpoint** :
- `GET /api/v2/gitfocus/config` → Charger config
- `POST /api/v2/gitfocus/config` → Sauvegarder config

---

# PARTIE V - IMPLÉMENTATION

## 1️⃣5️⃣ PLAN DE DÉVELOPPEMENT

### Phase 0 : Préparation (2 heures)

**Actions** :
1. ✅ Commit actuel : `git add -A && git commit -m "backup: state before V3 refonte"`
2. ✅ Créer branche : `git checkout -b refonte-v3-timeline-linear`
3. ✅ Créer fichiers de test :
   - `test_timeline.html` (tests frontend navigateur)
   - `test_timeline.py` (tests backend si nécessaire)
4. ✅ Documenter état actuel : `ETAT_AVANT_REFONTE_V3.md`

**Validation** : `git status` montre branche `refonte-v3-timeline-linear`, commits clean

### Phase 1-4 : Backend Core (15 heures)

**Phase 1** : Fonctions conversion temps (3h)
- `dateTimeToMinutes()`
- `minutesToDateTime()`
- `convertTempsMortsToLinear()`

**Phase 2** : Chargement données (3h)
- Charger CSV (Pomodoros, Respirations, Temps morts, Planifiées)
- Parser dates/heures
- Filtrer par date sélectionnée

**Phase 3** : Algorithme ORDERING (5h)
- `buildPomodoroList()` (tâches → pomodoros 25 min)
- `buildRespirationList()` (préserver duplicatas)
- `alternatePomodoresRespiration()` (cycling)
- `insertCalins()` (tous les 2 respirations)
- `insertClopes()` (cumul durée)

**Phase 4** : Algorithme TIME CALCULATION (4h)
- Parcours séquentiel `alternated_list`
- Gestion collision temps_morts (ÉTAPE 10.1)
- Gestion collision tâches planifiées (ÉTAPE 10.2)
- Placement tâches (ÉTAPE 10.3)
- Conversion temps relatif → absolu

**Validation** : Tests unitaires backend (pytest)

### Phase 5-8 : Frontend UI (20 heures)

**Phase 5** : Onglet Pomodoro (5h)
- Liste tâches avec checkboxes
- Filtres (catégorie, priorité, recherche)
- Modal création/édition
- Badges priorité (P1/P2/P3)

**Phase 6** : Onglet Pauses (7h)
- Layout 2 colonnes (source + sélection)
- Drag & drop natif
- Épinglage (📌)
- Bouton "Envoyer vers planning"

**Phase 7** : Onglet Récurrentes (4h)
- Liste avec toggle switch ON/OFF
- Modal création/édition
- Compteurs (total/actives)

**Phase 8** : Planning Généré (4h)
- Slots très fins (30px hauteur)
- Couleurs par type
- Statistiques footer
- Scroll automatique

**Validation** : Tests manuels navigateur

### Phase 9-12 : Intégration & Polish (15 heures)

**Phase 9** : API REST (4h)
- Route `/planning/generate` (POST)
- Route `/planning/export` (POST)
- Routes CRUD tâches
- Routes état/config

**Phase 10** : Persistance (3h)
- Sauvegarde état (`planning_state.json`)
- Pauses épinglées (`pinned_pauses.json`)
- Config utilisateur (`user_config.json`)
- Écriture atomique (temp + rename)

**Phase 11** : Workflow Complet (5h)
- Intégration frontend ↔ backend
- Gestion erreurs (try/catch)
- Notifications utilisateur
- Loading spinners

**Phase 12** : Tests E2E (3h)
- Scénario complet (sélection → génération → export)
- Cas edge (0 tâches, multi-jours, collisions)
- Validation CSV exportés

**Validation** : Checklist complète (section 16)

### Phase 13 : Documentation & Rollback (2 heures)

**Actions** :
1. Créer `MIGRATION_GUIDE_V3.md`
2. Mettre à jour `CLAUDE.md`
3. Tester rollback :
   ```bash
   git checkout master
   git branch -D refonte-v3-timeline-linear
   ```

**Validation** : Rollback fonctionne, documentation à jour

**TOTAL** : ~54 heures (7-9 jours ouvrés à temps plein)

---

## 1️⃣6️⃣ TESTS & VALIDATION

### 16.1 Checklist Finale

**Backend** :
- [ ] Chargement CSV (Pomodoros, Respirations, Recurrentes, Planifiées, Temps morts)
- [ ] Conversion temps absolu ↔ relatif
- [ ] Construction liste alternée (Pomodoros + Respirations)
- [ ] Insertion câlins (tous les 2 respirations)
- [ ] Insertion clopes (cumul durée)
- [ ] Gestion collision temps_morts (buffer "Bientôt temps mort")
- [ ] Gestion collision tâches planifiées (décalage)
- [ ] Export CSV (`planned.csv`, `respiration_planning_history.csv`)
- [ ] Persistance état (`planning_state.json`, `pinned_pauses.json`)

**Frontend** :
- [ ] Onglet Pomodoro (liste, checkboxes, filtres, modal)
- [ ] Onglet Pauses (drag & drop, épinglage, compteur)
- [ ] Onglet Récurrentes (toggle switch, liste)
- [ ] Planning généré (slots fins, couleurs, statistiques)
- [ ] Controls bar (date, heure départ, boutons)
- [ ] Appels API (génération, export, CRUD)
- [ ] Notifications utilisateur (succès, erreur)
- [ ] Responsive design (desktop, tablet, mobile)

**Tests E2E** :
- [ ] Scénario 1 : Générer planning (3 Pomodoros + 2 Respirations)
- [ ] Scénario 2 : Mode Focus (Pomodoros sans Respirations)
- [ ] Scénario 3 : Pauses consécutives (Respirations sans Pomodoros)
- [ ] Scénario 4 : Câlins + Clopes activés
- [ ] Scénario 5 : Tâche planifiée intégrée (avec replanification)
- [ ] Scénario 6 : Collision temps_mort (buffer inséré)
- [ ] Scénario 7 : Multi-jours (planning déborde sur jour suivant)
- [ ] Scénario 8 : Épinglage pauses (persistance après refresh)
- [ ] Scénario 9 : Export CSV (fichier généré sur serveur)
- [ ] Scénario 10 : Modification heure départ (recalcul planning)

### 16.2 Tests Unitaires Backend (Python)

**Fichier** : `test_planning_v3.py`

```python
import pytest
from backend.planning_engine.planning_generator_v3 import (
    build_pomodoro_list,
    build_respiration_list,
    alternate_pomodoros_respiration,
    insert_calins,
    insert_clopes
)

def test_build_pomodoro_list():
    """Test conversion tâches → pomodoros"""
    tasks = [
        {'id': 'TASK001', 'name': 'Révision maths', 'remaining_min': 75},
        {'id': 'TASK002', 'name': 'Rapport projet', 'remaining_min': 50}
    ]
    pomodoros = build_pomodoro_list(['TASK001', 'TASK002'], tasks)

    assert len(pomodoros) == 5  # 3 + 2 = 5 pomodoros
    assert pomodoros[0]['pomodoro_index'] == 1
    assert pomodoros[0]['pomodoro_total'] == 3
    assert pomodoros[2]['pomodoro_index'] == 3

def test_cycling_respirations():
    """Test cycling respirations (81 Pomodoros + 3 Respirations)"""
    pomodoros = [{'type': 'POMODORO', 'duration': 25}] * 81
    respirations = [
        {'type': 'RESPIRATION', 'name': 'R1', 'duration': 10},
        {'type': 'RESPIRATION', 'name': 'R2', 'duration': 5},
        {'type': 'RESPIRATION', 'name': 'R3', 'duration': 15}
    ]

    alternated = alternate_pomodoros_respiration(pomodoros, respirations)

    # Vérifier cycling (27 fois chaque respiration)
    r1_count = sum(1 for t in alternated if t.get('name') == 'R1')
    r2_count = sum(1 for t in alternated if t.get('name') == 'R2')
    r3_count = sum(1 for t in alternated if t.get('name') == 'R3')

    assert r1_count == 27
    assert r2_count == 27
    assert r3_count == 27

def test_insert_calins():
    """Test insertion câlins (tous les 2 respirations)"""
    alternated = [
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 10},
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 5},
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 10}
    ]

    insert_calins(alternated, calin_enabled=True, calin_duration=10)

    # Vérifier 1 câlin après 2 respirations
    calin_count = sum(1 for t in alternated if t['type'] == 'CALIN')
    assert calin_count == 1

    # Vérifier position (avant 2ème respiration)
    calin_index = next(i for i, t in enumerate(alternated) if t['type'] == 'CALIN')
    assert alternated[calin_index + 1]['type'] == 'RESPIRATION'

def test_insert_clopes():
    """Test insertion clopes (cumul durée)"""
    alternated = [
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 10},
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 10},
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 10},
        {'type': 'POMODORO', 'duration': 25},
        {'type': 'RESPIRATION', 'duration': 10}
    ]
    # Total = 100 + 40 = 140 min

    insert_clopes(alternated, clope_enabled=True, clope_interval_min=120)

    # Vérifier 1 clope insérée (après 120 min cumulés)
    clope_count = sum(1 for t in alternated if t['type'] == 'CLOPE')
    assert clope_count == 1

    # Vérifier durée cumulée avant clope ≥ 120
    clope_index = next(i for i, t in enumerate(alternated) if t['type'] == 'CLOPE')
    cumul = sum(alternated[j]['duration'] for j in range(clope_index))
    assert cumul >= 120
```

### 16.3 Tests Frontend (JavaScript)

**Fichier** : `test_timeline.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Tests Timeline V3</title>
    <script src="../static/js/gitfocus_v2.js"></script>
</head>
<body>
    <h1>Tests Timeline V3</h1>
    <div id="test-results"></div>

    <script>
    function assert(condition, message) {
        if (!condition) {
            console.error(`❌ ${message}`);
            document.getElementById('test-results').innerHTML += `<p style="color: red;">❌ ${message}</p>`;
        } else {
            console.log(`✅ ${message}`);
            document.getElementById('test-results').innerHTML += `<p style="color: green;">✅ ${message}</p>`;
        }
    }

    // Test 1: Calcul heure départ
    function testCalculateStartTime() {
        const start = calculateStartTime();
        const minutes = start.getMinutes();
        assert(minutes % 5 === 0, 'Start time rounded to 5 minutes');

        const now = new Date();
        const diff = (start - now) / 60000; // Minutes
        assert(diff >= 15 && diff < 20, 'Start time is 15-20 min in future');
    }

    // Test 2: Conversion temps
    function testTimeConversion() {
        const planningStart = new Date('2025-11-05T14:00:00');

        // Absolute → Relative
        const time1 = new Date('2025-11-05T16:30:00');
        const minutes1 = dateTimeToMinutes(time1, planningStart);
        assert(minutes1 === 150, 'Conversion absolute → relative (150 min)');

        // Relative → Absolute
        const result = minutesToDateTime(150, planningStart);
        assert(result.date === '2025-11-05', 'Date conversion correct');
        assert(result.time === '16:30', 'Time conversion correct');
    }

    // Test 3: État planning
    function testPlanningState() {
        state.selectedPomodoroIds = ['TASK001', 'TASK002'];
        state.selectedRespirationIds = ['R010', 'R018'];

        assert(state.selectedPomodoroIds.length === 2, 'Pomodoro selection saved');
        assert(state.selectedRespirationIds.length === 2, 'Respiration selection saved');
    }

    // Run all tests
    testCalculateStartTime();
    testTimeConversion();
    testPlanningState();

    console.log('All tests completed');
    </script>
</body>
</html>
```

---

## 1️⃣7️⃣ MIGRATION & ROLLBACK

### 17.1 Procédure de Migration

**Étape 1** : Backup complet
```bash
# Backup données prod
cp -r prod_data prod_data_backup_$(date +%Y%m%d)

# Commit code actuel
git add -A
git commit -m "backup: before V3 migration"
git tag v2.0-last-stable
```

**Étape 2** : Merge branche V3
```bash
# Merge refonte V3
git checkout master
git merge refonte-v3-timeline-linear

# Tag release
git tag -a v3.0.0 -m "Release V3: Timeline Linéaire"
git push origin master --tags
```

**Étape 3** : Migration données (si nécessaire)
```bash
# Si migration CSV nécessaire (ex: fusion RESPIRATOIRES → RECURRENTES)
python scripts/migrate_respirations_to_recurrent.py
```

**Étape 4** : Restart serveur
```bash
scripts\restart.bat
```

**Étape 5** : Vérification post-migration
- [ ] Page charge sans erreur
- [ ] Données affichées correctement
- [ ] Génération planning fonctionne
- [ ] Export CSV fonctionne

### 17.2 Procédure de Rollback

**Si problème critique après merge** :

**Option 1** : Revert merge commit
```bash
git revert -m 1 HEAD
git push origin master
scripts\restart.bat
```

**Option 2** : Hard reset (DANGER : perd commits)
```bash
git reset --hard v2.0-last-stable
git push --force origin master
scripts\restart.bat
```

**Option 3** : Restore données + checkout tag
```bash
# Restore données backup
rm -rf prod_data
cp -r prod_data_backup_YYYYMMDD prod_data

# Checkout version stable
git checkout v2.0-last-stable
scripts\restart.bat
```

**Validation rollback** :
- [ ] Serveur démarre sans erreur
- [ ] Page V2 charge correctement
- [ ] Données intactes
- [ ] Fonctionnalités V2 opérationnelles

---

## ✅ CHECKLIST FINALE AVANT IMPLÉMENTATION

- [ ] **Documentation lue et comprise** (toutes les 5 parties)
- [ ] **Questions CRITIQUES répondues** (CLARIFICATIONS_LOGIQUE_V3.md si besoin)
- [ ] **Environnement de développement prêt** (Python 3.11+, Flask 2.x)
- [ ] **Données de test préparées** (CSV exemples)
- [ ] **Branche Git créée** (`refonte-v3-timeline-linear`)
- [ ] **Backup actuel effectué** (tag `v2.0-last-stable`)
- [ ] **Plan de développement validé** (54 heures estimées)
- [ ] **Stratégie de rollback comprise** (3 options disponibles)

---

**Document créé le** : 2025-11-05
**Auteur** : Claude (Anthropic) + Julio
**Version** : 3.0 Complète et Unifiée
**Lignes** : 3500+
**Statut** : Document de référence unique - Prêt pour implémentation

---

## 📝 NOTES FINALES

Ce document unique remplace et fusionne :
- ✅ `PLAN_REFONTE_V3.md` (plan d'implémentation)
- ✅ `CLARIFICATIONS_LOGIQUE_V3.md` (questions/réponses intégrées dans cas particuliers)
- ✅ `SPECIFICATIONS_COMPLETES_UI_DATA.md` (interface & données)
- ✅ `FLUX_PLANNING_LINEAR.md` (flux 12 étapes)
- ✅ `TIMELINE_LINEAR_SPEC_BACKUP.md` (architecture timeline récupérée)

**Tout est ici** : Architecture, Interface, Algorithme, Données, Tests, Migration.

**Prochaine étape** : Commencer PHASE 0 (Préparation) du plan de développement.
