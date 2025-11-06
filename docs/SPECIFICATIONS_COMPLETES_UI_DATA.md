# Spécifications Complètes - Interface & Données

**Date**: 2025-11-05
**Version**: 3.0
**Objectif**: Documentation exhaustive de TOUS les aspects (UI, CSV, comportements, styles)

---

## 📐 TABLE DES MATIÈRES

1. [Interface Web - Layout Général](#1-interface-web---layout-général)
2. [Onglet Pomodoro - Détails](#2-onglet-pomodoro---détails)
3. [Onglet Pauses - Détails](#3-onglet-pauses---détails)
4. [Onglet Tâches Récurrentes - Détails](#4-onglet-tâches-récurrentes---détails)
5. [Planning Généré - Affichage](#5-planning-généré---affichage)
6. [Fichiers CSV - Structure Complète](#6-fichiers-csv---structure-complète)
7. [Fichiers JSON - Configuration](#7-fichiers-json---configuration)
8. [Couleurs & Styles - Charte Graphique](#8-couleurs--styles---charte-graphique)
9. [Interactions Utilisateur - Workflows](#9-interactions-utilisateur---workflows)
10. [États & Transitions - Machine à États](#10-états--transitions---machine-à-états)

---

## 1️⃣ INTERFACE WEB - Layout Général

### 1.1 Structure HTML Globale

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER                                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ GitFocus Planner V2                                      │ │
│ │ Version serveur: 2025-11-05 14:32:15    [Aide] [Config]│ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ CONTROLS BAR                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Date: [2025-11-05 ▼]  Heure départ: [14:00]            │ │
│ │ [Recalculer Planning]                                    │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ MAIN CONTENT (2 COLONNES)                                   │
│ ┌──────────────────────────┬────────────────────────────┐   │
│ │ LEFT PANEL (70%)         │ RIGHT PANEL (30%)          │   │
│ │                          │                            │   │
│ │ ┌──────────────────────┐ │ ┌────────────────────────┐ │   │
│ │ │ ONGLETS              │ │ │ PLANNING GÉNÉRÉ        │ │   │
│ │ │ ┌──────────────────┐ │ │ │                        │ │   │
│ │ │ │ [Pomodoro]       │ │ │ │ 10:00-10:25 Tâche 1   │ │   │
│ │ │ │ [Pauses]         │ │ │ │ 10:25-10:35 Pause     │ │   │
│ │ │ │ [Récurrentes]    │ │ │ │ ...                    │ │   │
│ │ │ └──────────────────┘ │ │ │                        │ │   │
│ │ │                      │ │ │                        │ │   │
│ │ │ <CONTENU ONGLET>     │ │ │                        │ │   │
│ │ │                      │ │ │                        │ │   │
│ │ └──────────────────────┘ │ └────────────────────────┘ │   │
│ └──────────────────────────┴────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│ FOOTER                                                       │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Statistiques: 8 Pomodoros | 120 min travail | 40 min   │ │
│ │ pauses | Temps libre: 180 min                           │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Dimensions & Responsive

**Desktop (> 1200px)**:
- Layout: 2 colonnes (70% / 30%)
- Largeur minimale: 1200px
- Hauteur: 100vh (pleine hauteur écran)
- Scroll: Vertical sur onglets si contenu dépasse

**Tablet (768px - 1200px)**:
- Layout: 2 colonnes (60% / 40%)
- Onglets peuvent être réduits (bouton collapse)

**Mobile (< 768px)**:
- Layout: 1 colonne (onglets au-dessus, planning en-dessous)
- Onglets: Accordéon (1 seul ouvert à la fois)
- Planning: Largeur 100%

### 1.3 Header - Barre Supérieure

**Contenu**:
```html
<div class="header">
    <div class="logo">
        <h1>GitFocus Planner V2</h1>
        <span class="version-badge">Timeline Linéaire</span>
    </div>
    <div class="server-info">
        <span class="server-version">
            Serveur: <span id="server-timestamp">2025-11-05 14:32:15</span>
        </span>
    </div>
    <div class="header-actions">
        <button class="btn-icon" id="help-btn" title="Aide">
            <i class="icon-help">?</i>
        </button>
        <button class="btn-icon" id="config-btn" title="Configuration">
            <i class="icon-settings">⚙</i>
        </button>
    </div>
</div>
```

**Style**:
- Fond: `#1e293b` (bleu foncé)
- Texte: `#ffffff` (blanc)
- Hauteur: `60px`
- Padding: `0 20px`
- Ombre: `0 2px 4px rgba(0,0,0,0.1)`

**Server Timestamp**:
- Mis à jour automatiquement toutes les 60 secondes (fetch `/api/v2/gitfocus/health`)
- Format: `YYYY-MM-DD HH:MM:SS`
- But: Confirmer que le serveur est à jour (évite cache navigateur)

### 1.4 Controls Bar - Barre de Contrôle

**Contenu**:
```html
<div class="controls-bar">
    <div class="date-control">
        <label for="planning-date">Date :</label>
        <input type="date" id="planning-date" value="2025-11-05">
    </div>

    <div class="time-control">
        <label for="planning-start-time">Heure de départ :</label>
        <input type="time" id="planning-start-time" value="14:00">
        <button class="btn-sm" id="auto-time-btn" title="Recalculer automatiquement">
            🔄 Auto
        </button>
    </div>

    <div class="action-buttons">
        <button class="btn btn-primary" id="generate-planning-btn">
            Générer Planning
        </button>
        <button class="btn btn-secondary" id="export-csv-btn" disabled>
            Exporter CSV
        </button>
    </div>
</div>
```

**Style**:
- Fond: `#f8fafc` (gris clair)
- Hauteur: `50px`
- Padding: `10px 20px`
- Display: `flex`, `justify-content: space-between`, `align-items: center`

**Comportement**:
- **Date Input**: Change automatiquement les données chargées (temps_morts, tâches planifiées)
- **Time Input**: Peut être modifié manuellement, clique "Auto" pour recalculer (now + 15min)
- **Bouton "Générer Planning"**: Toujours actif (même si 0 tâches sélectionnées)
- **Bouton "Exporter CSV"**: Désactivé (`disabled`) si planning vide, activé après génération

---

## 2️⃣ ONGLET POMODORO - Détails

### 2.1 Layout Onglet Pomodoro

```
┌──────────────────────────────────────────────────────────┐
│ ONGLET: POMODORO                              [+ Nouvelle]│
├──────────────────────────────────────────────────────────┤
│ Filtres:                                                  │
│ [Catégorie: Toutes ▼] [Priorité: Toutes ▼] [Recherche...│
├──────────────────────────────────────────────────────────┤
│ LISTE DES TÂCHES (Scrollable)                            │
│ ┌────────────────────────────────────────────────────────┤
│ │ ☐ [P1] Révision mathématiques                  75 min │
│ │     Catégorie: Études > Mathématiques                 │
│ │     [✏️ Éditer] [🗑️ Supprimer]                        │
│ ├────────────────────────────────────────────────────────┤
│ │ ☑ [P2] Rapport de projet                      50 min │
│ │     Catégorie: Travail > Documentation                │
│ │     [✏️ Éditer] [🗑️ Supprimer]                        │
│ ├────────────────────────────────────────────────────────┤
│ │ ☐ [P3] Lecture documentation API              25 min │
│ │     Catégorie: Développement > Backend                │
│ │     [✏️ Éditer] [🗑️ Supprimer]                        │
│ └────────────────────────────────────────────────────────┘
├──────────────────────────────────────────────────────────┤
│ Sélection: 2 tâches | Total: 125 min (5 Pomodoros)      │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Carte Tâche - Structure HTML

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
        <div class="task-description" title="Description complète">
            Réviser chapitres 3 et 4 (algèbre linéaire)
        </div>
    </div>

    <div class="task-actions">
        <button class="btn-icon" title="Éditer" onclick="editPomodoroTask('TASK001')">
            ✏️
        </button>
        <button class="btn-icon btn-danger" title="Supprimer" onclick="deletePomodoroTask('TASK001')">
            🗑️
        </button>
    </div>
</div>
```

### 2.3 Couleurs Priorités

**Badge Priorité**:
- **P1 (Haute)**: `background: #dc2626` (rouge), `color: #ffffff`
- **P2 (Moyenne)**: `background: #f59e0b` (orange), `color: #ffffff`
- **P3 (Basse)**: `background: #3b82f6` (bleu), `color: #ffffff`

**Style Badge**:
```css
.priority-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: 700;
    margin-right: 8px;
}
```

### 2.4 Modal Création/Édition Tâche

**Layout Modal**:
```html
<div class="modal" id="edit-pomodoro-modal">
    <div class="modal-content">
        <div class="modal-header">
            <h2>Éditer Tâche Pomodoro</h2>
            <button class="close-btn">&times;</button>
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
                    <input type="number" id="task-duration" min="1" step="1" required>
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
                    <select id="task-category">
                        <option value="">-- Choisir --</option>
                        <option value="Études">Études</option>
                        <option value="Travail">Travail</option>
                        <!-- Populated dynamically -->
                    </select>
                    <button class="btn-icon" title="Ajouter catégorie">+</button>
                </div>

                <div class="form-group">
                    <label for="task-subcategory">Sous-catégorie *</label>
                    <select id="task-subcategory">
                        <option value="">-- Choisir --</option>
                        <!-- Populated based on category -->
                    </select>
                    <button class="btn-icon" title="Ajouter sous-catégorie">+</button>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="task-deadline">Deadline</label>
                    <input type="date" id="task-deadline">
                </div>

                <div class="form-group">
                    <label for="task-fixed-start">Heure fixe</label>
                    <input type="time" id="task-fixed-start">
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button class="btn btn-secondary" onclick="closeModal()">
                Annuler
            </button>
            <button class="btn btn-primary" onclick="savePomodoroTask()">
                Sauvegarder
            </button>
        </div>
    </div>
</div>
```

**Validation Temps Réel**:
- **Durée modifiée**: Affiche automatiquement `Math.ceil(durée / 25)` Pomodoros
- **Catégorie modifiée**: Recharge sous-catégories associées
- **Champs requis vides**: Bouton "Sauvegarder" désactivé

---

## 3️⃣ ONGLET PAUSES - Détails

### 3.1 Layout Onglet Pauses (2 Colonnes)

```
┌───────────────────────────────────────────────────────────────┐
│ ONGLET: PAUSES                                                 │
├───────────────────────────┬───────────────────────────────────┤
│ TÂCHES DISPONIBLES        │ PAUSES SÉLECTIONNÉES              │
│ (Source)                  │ (Ordre d'alternance)              │
├───────────────────────────┼───────────────────────────────────┤
│ Recherche: [...]          │ [📌 Épingler tout] [🗑️ Vider]    │
├───────────────────────────┼───────────────────────────────────┤
│ Catégorie: Respiration    │ ⚠️ Ordre important : glisser-     │
│ ┌───────────────────────┐ │ déposer pour réorganiser          │
│ │ 🫁 Méditation         │ │ ┌─────────────────────────────┐   │
│ │ 10 min                │ │ │ 📌 🫁 Méditation           │   │
│ │ DRAG →                │ │ │ 10 min                     │   │
│ └───────────────────────┘ │ │ [🗑️]                       │   │
│ ┌───────────────────────┐ │ ├─────────────────────────────┤   │
│ │ 🌬️ Respiration        │ │ │ 🌬️ Respiration profonde   │   │
│ │ profonde              │ │ │ 5 min                      │   │
│ │ 5 min                 │ │ │ [🗑️]                       │   │
│ │ DRAG →                │ │ ├─────────────────────────────┤   │
│ └───────────────────────┘ │ │ 🌬️ Respiration profonde   │   │
│ ┌───────────────────────┐ │ │ 5 min (duplicata)          │   │
│ │ 🚶 Marche rapide      │ │ │ [🗑️]                       │   │
│ │ 15 min                │ │ ├─────────────────────────────┤   │
│ │ DRAG →                │ │ │ 🚶 Marche rapide           │   │
│ └───────────────────────┘ │ │ 15 min                     │   │
│                           │ │ [🗑️]                       │   │
│ Catégorie: Câlins         │ └─────────────────────────────┘   │
│ ┌───────────────────────┐ │                                   │
│ │ 💙 Câlin              │ │ Total: 4 pauses                   │
│ │ 10 min                │ │ Durée totale: 40 min              │
│ │ DRAG →                │ │                                   │
│ └───────────────────────┘ │ [Envoyer vers planning]           │
└───────────────────────────┴───────────────────────────────────┘
```

### 3.2 Carte Pause - Structure HTML

**Panel Gauche (Source)**:
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

**Panel Droit (Sélection)**:
```html
<div class="pause-selected-item" draggable="true" data-task-id="R010" data-index="0">
    <div class="pin-btn" onclick="togglePin(this)" title="Épingler">
        📌
    </div>
    <div class="pause-icon">🫁</div>
    <div class="pause-info">
        <div class="pause-name">Méditation</div>
        <div class="pause-duration">10 min</div>
    </div>
    <div class="pause-actions">
        <button class="btn-icon btn-danger" onclick="removePause(0)">🗑️</button>
    </div>
    <div class="drag-handle">⋮⋮</div>
</div>
```

### 3.3 États Visuels Drag & Drop

**Pendant le Drag (Source)**:
```css
.pause-source-item.dragging {
    opacity: 0.5;
    cursor: grabbing;
    transform: scale(1.05);
}
```

**Zone de Drop (Sélection)**:
```css
.pause-selected-panel.drag-over {
    background: #eff6ff; /* Bleu clair */
    border: 2px dashed #3b82f6;
}
```

**Indicateur d'Insertion** (ligne bleue entre 2 pauses):
```html
<div class="drop-indicator" style="top: 120px;"></div>
```
```css
.drop-indicator {
    position: absolute;
    left: 0;
    right: 0;
    height: 2px;
    background: #3b82f6;
    transition: top 0.2s;
}
```

### 3.4 Bouton "Envoyer vers planning"

**Style Bouton**:
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

**État Désactivé**:
- Désactivé si: `pauses sélectionnées.length === 0`
- Tooltip: "Glissez au moins 1 pause pour continuer"

### 3.5 Épinglage Visuel

**Pause Épinglée**:
```css
.pause-selected-item.pinned {
    border-left: 4px solid #2563eb;
    background: linear-gradient(to right, #eff6ff 0%, #ffffff 100%);
}

.pause-selected-item.pinned .pin-btn {
    color: #2563eb;
    font-weight: bold;
}
```

**Tooltip Épinglage**:
- Hover sur 📌: "Épingler (reste après refresh)"
- Épinglé: "Désépingler"

---

## 4️⃣ ONGLET TÂCHES RÉCURRENTES - Détails

### 4.1 Layout Onglet Récurrentes

```
┌──────────────────────────────────────────────────────────┐
│ ONGLET: TÂCHES RÉCURRENTES                    [+ Nouvelle]│
├──────────────────────────────────────────────────────────┤
│ Filtres: [Actives uniquement ☑] [Catégorie: Toutes ▼]   │
├──────────────────────────────────────────────────────────┤
│ LISTE DES TÂCHES RÉCURRENTES (Scrollable)                │
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
│ ├────────────────────────────────────────────────────────┤
│ │ [ON] 🚿 Nettoyer salle de bain                 20 min │
│ │      Récurrence: Tous les 3 jours                     │
│ │      Prochaine: 2025-11-07                            │
│ │      [✏️ Éditer] [🗑️ Supprimer]                       │
│ └────────────────────────────────────────────────────────┘
├──────────────────────────────────────────────────────────┤
│ Total: 20 tâches | Actives: 12                           │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Toggle Switch Actif/Inactif

**HTML Toggle**:
```html
<label class="toggle-switch">
    <input type="checkbox" checked onchange="toggleRecurrentTask('REC001')">
    <span class="toggle-slider"></span>
</label>
```

**Style Toggle**:
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

---

## 5️⃣ PLANNING GÉNÉRÉ - Affichage

### 5.1 Layout Planning (Panel Droit)

```
┌────────────────────────────────────────┐
│ PLANNING GÉNÉRÉ                  [🔄]  │
├────────────────────────────────────────┤
│ ⏱️ 10:00 - 10:25 │ Révision maths │ 25'│
│                   (1/3) 🟡             │
├────────────────────────────────────────┤
│ ⏱️ 10:25 - 10:35 │ Méditation     │ 10'│
│                   🔵                   │
├────────────────────────────────────────┤
│ ⏱️ 10:35 - 11:00 │ Révision maths │ 25'│
│                   (2/3) 🟡             │
├────────────────────────────────────────┤
│ ⏱️ 11:00 - 11:05 │ Respiration    │  5'│
│                   profonde 🔵           │
├────────────────────────────────────────┤
│ ⏱️ 11:05 - 11:30 │ Révision maths │ 25'│
│                   (3/3) 🟡             │
├────────────────────────────────────────┤
│ ⏱️ 11:30 - 12:00 │ RDV médical 📅 │ 30'│
│                   (Planifié) ⚠️        │
├────────────────────────────────────────┤
│ ⏱️ 12:00 - 13:00 │ TEMPS MORT 🚫  │ 60'│
│                   Déjeuner             │
└────────────────────────────────────────┘
```

### 5.2 Slot Planning - Structure HTML

**Ligne Très Fine (30px hauteur)** :
```html
<div class="planning-slot slot-pomodoro" data-slot-id="0">
    <div class="slot-time">10:00 - 10:25</div>
    <div class="slot-name">
        Révision maths
        <span class="pomodoro-index">(1/3)</span>
    </div>
    <div class="slot-duration">25'</div>
    <div class="slot-type-indicator">🟡</div>
</div>
```

**Style Slot** (TRÈS COMPACT):
```css
.planning-slot {
    display: grid;
    grid-template-columns: 100px 1fr 40px 30px;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
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

### 5.3 Types de Slots - Couleurs & Styles

**Pomodoro (Travail)**:
```css
.slot-pomodoro {
    background: linear-gradient(to right, #fef3c7 0%, #fefce8 100%);
    border-left-color: #f59e0b;
}
.slot-pomodoro .slot-type-indicator::after {
    content: '🟡'; /* Cercle jaune */
}
```

**Respiration (Pause)**:
```css
.slot-respiration {
    background: linear-gradient(to right, #dbeafe 0%, #eff6ff 100%);
    border-left-color: #3b82f6;
}
.slot-respiration .slot-type-indicator::after {
    content: '🔵'; /* Cercle bleu */
}
```

**Câlin**:
```css
.slot-calin {
    background: linear-gradient(to right, #fce7f3 0%, #fdf2f8 100%);
    border-left-color: #ec4899;
}
.slot-calin .slot-type-indicator::after {
    content: '💙'; /* Cœur bleu */
}
```

**Clope**:
```css
.slot-clope {
    background: linear-gradient(to right, #f3f4f6 0%, #f9fafb 100%);
    border-left-color: #6b7280;
}
.slot-clope .slot-type-indicator::after {
    content: '🚬'; /* Cigarette */
}
```

**Tâche Planifiée**:
```css
.slot-planned {
    background: linear-gradient(to right, #fef3c7 0%, #fefce8 100%);
    border-left-color: #f59e0b;
    border: 1px solid #f59e0b;
}
.slot-planned .slot-type-indicator::after {
    content: '📅'; /* Calendrier */
}
```

**Tâche Planifiée Replanifiée** (badge supplémentaire):
```html
<div class="slot-name">
    RDV médical
    <span class="rescheduled-badge" title="Prévu à 11:00, placé à 11:30">⚠️</span>
</div>
```
```css
.rescheduled-badge {
    margin-left: 4px;
    color: #f59e0b;
    font-size: 1em;
}
```

**Temps Mort**:
```css
.slot-temps_mort {
    background: linear-gradient(to right, #f3f4f6 0%, #e5e7eb 100%);
    border-left-color: #dc2626;
    opacity: 0.8;
}
.slot-temps_mort .slot-type-indicator::after {
    content: '🚫'; /* Interdit */
}
```

**Buffer "Bientôt temps mort"**:
```css
.slot-buffer {
    background: linear-gradient(to right, #fef3c7 0%, #fefce8 100%);
    border-left-color: #f59e0b;
    font-style: italic;
    opacity: 0.7;
}
.slot-buffer .slot-type-indicator::after {
    content: '⏳'; /* Sablier */
}
```

### 5.4 Statistiques Footer

**HTML Stats**:
```html
<div class="planning-stats">
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
</div>
```

**Style Stats**:
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

## 6️⃣ FICHIERS CSV - Structure Complète

### 6.1 LISTE_MERE.v2.csv (Tâches Pomodoro)

**Format**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
```

**Exemple**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
"TASK001";"Révision mathématiques";"Chapitres 3 et 4 algèbre linéaire";"Études";"Mathématiques";"75";"75";"1";"urgent,examen";"algèbre,matrices";"";"";"15.11.25";"";"";""
"TASK002";"Rapport de projet";"Rédiger section résultats";"Travail";"Documentation";"50";"50";"2";"travail";"rapport,doc";"TASK001";"Attendre validation chef";"20.11.25";"";"";""
```

**Colonnes Détaillées**:

| Colonne | Type | Obligatoire | Description | Exemple |
|---------|------|-------------|-------------|---------|
| ID | string | ✅ | Format: `TASK` + 3 chiffres | `TASK001` |
| NAME | string | ✅ | Titre tâche (max 100 car) | `"Révision maths"` |
| DESCRIPTION | string | ❌ | Description détaillée | `"Chapitres 3-4"` |
| CATEGORY | string | ✅ | Catégorie principale | `"Études"` |
| SUB_CATEGORY | string | ✅ | Sous-catégorie | `"Mathématiques"` |
| DURATION_MIN | int | ✅ | Durée totale estimée | `75` |
| REMAINING_MIN | int | ✅ | Durée restante (≤ DURATION) | `75` |
| PRIORITY | int | ✅ | 1=Haute, 2=Moyenne, 3=Basse | `1` |
| TAGS | string | ❌ | Tags séparés par virgules | `"urgent,exam"` |
| KEYWORDS | string | ❌ | Mots-clés recherche | `"algèbre"` |
| DEPENDENCIES | string | ❌ | IDs tâches dépendantes | `"TASK002"` |
| NOTES | string | ❌ | Notes libres | `"Voir prof"` |
| DEADLINE | string | ❌ | Format DD.MM.YY | `"15.11.25"` |
| FIXED_START | string | ❌ | Format HH:MM (RDV fixe) | `"14:30"` |
| PLANNED_START | string | ❌ | Format DD.MM.YY HH:MM | `"05.11.25 14:00"` |
| STATUS | string | ❌ | `todo`, `in_progress`, `done` | `""` (vide = todo) |

**Règles Validation**:
- `REMAINING_MIN` ≤ `DURATION_MIN` (sinon: erreur)
- Si `FIXED_START` rempli → Tâche de type FIXED (non déplaçable)
- Si `PLANNED_START` rempli → Tâche de type PLANNED (flexible)
- `PRIORITY` ∈ {1, 2, 3} (sinon: défaut 3)

### 6.2 TACHES_RESPIRATOIRES.v2.csv → FUSIONNÉ dans TACHES_RECURRENTES.v2.csv

**⚠️ MIGRATION 2025-11-05**: Les tâches respiratoires sont maintenant dans `TACHES_RECURRENTES.v2.csv`

**Ancien format** (TACHES_RESPIRATOIRES.v2.csv - OBSOLÈTE):
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REPEAT_INTERVAL_MIN";"LAST_DONE_TIMESTAMP";"LAST_DONE_DATE";"EARLIEST_TIME";"LATEST_TIME";"IDEAL_TIME";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"STATUS";"EXPORT_COUNT"
```

**Nouveau format** (TACHES_RECURRENTES.v2.csv):
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE"
```

**Exemple**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"RECURRENCE_TYPE";"RECURRENCE_INTERVAL";"LAST_DONE_DATE";"NEXT_DUE_DATE";"PRIORITY";"STATUS";"IS_ACTIVE"
"R010";"Méditation";"Méditation guidée 10 min";"Respiration";"Méditation";"10";"daily";"1";"2025-11-04";"2025-11-05";"2";"";"1"
"R018";"Respiration profonde";"Exercices respiration profonde";"Respiration";"Exercices";"5";"daily";"1";"2025-11-04";"2025-11-05";"2";"";"1"
"REC001";"Arroser plantes";"Arrosage plantes appartement";"Entretien";"Plantes";"10";"interval";"2";"2025-11-04";"2025-11-06";"3";"";"1"
```

**Colonnes Détaillées**:

| Colonne | Type | Obligatoire | Description | Exemple |
|---------|------|-------------|-------------|---------|
| ID | string | ✅ | Format: `R` + 3 chiffres OU `REC` + 3 chiffres | `R010`, `REC001` |
| NAME | string | ✅ | Nom tâche | `"Méditation"` |
| DESCRIPTION | string | ❌ | Description | `"Méditation guidée 10 min"` |
| CATEGORY | string | ✅ | Catégorie | `"Respiration"`, `"Entretien"` |
| SUB_CATEGORY | string | ✅ | Sous-catégorie | `"Méditation"`, `"Plantes"` |
| DURATION_MIN | int | ✅ | Durée | `10` |
| RECURRENCE_TYPE | string | ✅ | `daily`, `weekly`, `monthly`, `interval` | `"daily"` |
| RECURRENCE_INTERVAL | int | ✅ | Nb jours (si `interval`) ou jour semaine | `2` (tous les 2 jours) |
| LAST_DONE_DATE | string | ❌ | Format YYYY-MM-DD | `"2025-11-04"` |
| NEXT_DUE_DATE | string | ❌ | Format YYYY-MM-DD | `"2025-11-05"` |
| PRIORITY | int | ✅ | 1, 2, ou 3 | `2` |
| STATUS | string | ❌ | `todo`, `done` | `""` |
| IS_ACTIVE | int | ✅ | 0=Inactif, 1=Actif | `1` |

**Règles Validation**:
- `IS_ACTIVE` ∈ {0, 1} (requis)
- Si `RECURRENCE_TYPE = "interval"` → `RECURRENCE_INTERVAL` = nb jours (≥ 1)
- Si `RECURRENCE_TYPE = "weekly"` → `RECURRENCE_INTERVAL` = jour semaine (1=Lundi, 7=Dimanche)

### 6.3 TACHES_PLANIFIEES.v2.csv (Tâches avec heure fixe)

**Format**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
```

**Exemple**:
```csv
"ID";"NAME";"DESCRIPTION";"CATEGORY";"SUB_CATEGORY";"DURATION_MIN";"REMAINING_MIN";"PRIORITY";"TAGS";"KEYWORDS";"DEPENDENCIES";"NOTES";"DEADLINE";"FIXED_START";"PLANNED_START";"STATUS"
"PLAN001";"RDV dentiste";"Détartrage annuel";"Santé";"Médical";"30";"30";"1";"rdv";"";"";"Amener carte vitale";"05.11.25";"";"05.11.25 14:30";""
"PLAN002";"Cours en ligne Python";"Formation Udemy";"Formation";"Python";"45";"45";"2";"formation";"python";"";"";"05.11.25";"";"05.11.25 10:00";""
```

**Différence avec LISTE_MERE**:
- Colonne `PLANNED_START` obligatoirement remplie
- Format: `DD.MM.YY HH:MM` (ex: `"05.11.25 14:30"`)
- Ces tâches seront automatiquement intégrées dans le planning à l'heure demandée (ou plus proche possible)

### 6.4 temps_morts.csv (Créneaux bloqués)

**Format**:
```csv
"DATE";"HEURE_DEBUT";"HEURE_FIN";"TYPE";"TITRE"
```

**Exemple**:
```csv
"DATE";"HEURE_DEBUT";"HEURE_FIN";"TYPE";"TITRE"
"2025-11-05";"00:00";"06:30";"dodo";"Sommeil"
"2025-11-05";"12:00";"13:00";"repas";"Déjeuner"
"2025-11-05";"18:00";"19:00";"repas";"Dîner"
"2025-11-05";"22:00";"23:59";"dodo";"Préparation sommeil"
```

**Colonnes**:

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| DATE | string | Format ISO YYYY-MM-DD | `"2025-11-05"` |
| HEURE_DEBUT | string | Format HH:MM (24h) | `"14:00"` |
| HEURE_FIN | string | Format HH:MM (24h) | `"15:30"` |
| TYPE | string | Catégorie (libre) | `"dodo"`, `"repas"`, `"rdv"` |
| TITRE | string | Nom affiché | `"Déjeuner"` |

**Règles**:
- `HEURE_FIN` > `HEURE_DEBUT` (sinon: erreur)
- Créneaux peuvent chevaucher (priorité au premier dans le CSV)
- Filtrés par `DATE` lors du chargement

### 6.5 categories.csv (Catégories centralisées)

**Format**:
```csv
"CATEGORY";"SUB_CATEGORY"
```

**Exemple**:
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

**Utilisation**:
- Dropdowns catégories chargés depuis ce fichier
- Ajout rapide via bouton "+" (modal popup)
- Partagé entre TOUS types de tâches (Pomodoro, Respiratoires, Récurrentes, Planifiées)

### 6.6 planned.csv (Planning exporté)

**Format**:
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"KIND";"ORIGINAL_TIME"
```

**Exemple**:
```csv
"ID";"NAME";"DATE";"HEURE_DEBUT";"HEURE_FIN";"DURATION_MIN";"KIND";"ORIGINAL_TIME"
"TASK001";"Révision maths";"2025-11-05";"10:00";"10:25";"25";"pomodoro";""
"R010";"Méditation";"2025-11-05";"10:25";"10:35";"10";"respiration";""
"PLAN001";"RDV dentiste";"2025-11-05";"14:30";"15:00";"30";"planned";"14:30"
"AUTO_CLOPE";"Pause cigarette";"2025-11-05";"12:00";"12:05";"5";"clope";""
"TEMPS_MORT";"Déjeuner";"2025-11-05";"12:30";"13:30";"60";"temps_mort";""
```

**Colonnes**:

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| ID | string | ID tâche source (ou AUTO pour clopes/câlins) | `"TASK001"`, `"AUTO_CLOPE"` |
| NAME | string | Nom tâche | `"Révision maths"` |
| DATE | string | Date (YYYY-MM-DD) | `"2025-11-05"` |
| HEURE_DEBUT | string | Heure début (HH:MM) | `"10:00"` |
| HEURE_FIN | string | Heure fin (HH:MM) | `"10:25"` |
| DURATION_MIN | int | Durée en minutes | `25` |
| KIND | string | Type: `pomodoro`, `respiration`, `planned`, `calin`, `clope`, `temps_mort` | `"pomodoro"` |
| ORIGINAL_TIME | string | Heure initialement prévue (si replanifié) | `"14:00"` (si placé à 14:30) |

**Comportement Écrasement**:
- À chaque export: fichier **écrasé** (pas append)
- Contient UNIQUEMENT le dernier planning généré

### 6.7 respiration_planning_history.csv (Historique cumulatif)

**Format**:
```csv
"ID";"NAME";"DATE";"PLANNED_TIME";"DURATION_MIN";"EXPORT_TIMESTAMP"
```

**Exemple**:
```csv
"ID";"NAME";"DATE";"PLANNED_TIME";"DURATION_MIN";"EXPORT_TIMESTAMP"
"R010";"Méditation";"2025-11-04";"10:30";"10";"2025-11-04T09:15:23"
"R018";"Respiration profonde";"2025-11-04";"11:00";"5";"2025-11-04T09:15:23"
"R010";"Méditation";"2025-11-05";"10:25";"10";"2025-11-05T08:42:11"
"R018";"Respiration profonde";"2025-11-05";"11:00";"5";"2025-11-05T08:42:11"
```

**Comportement Append**:
- À chaque export: nouvelles lignes **ajoutées** (append)
- Permet analyse statistique (tâches les plus utilisées, heures préférées, etc.)

---

## 7️⃣ FICHIERS JSON - Configuration

### 7.1 planning_state.json (État utilisateur)

**Contenu**:
```json
{
  "current_date": "2025-11-05",
  "planning_start_time": "14:00",
  "selected_pomodoro_ids": ["TASK001", "TASK002", "TASK003"],
  "selected_respiration_ids": ["R010", "R018", "R018"],
  "calin_enabled": true,
  "clope_enabled": true,
  "clope_interval_min": 120,
  "last_updated": "2025-11-05T14:32:15"
}
```

**Mise à jour**:
- À chaque modification de sélection (Pomodoro ou Respiration)
- À chaque changement d'options (Câlins, Clopes)
- Écriture atomique (temp file + rename)

### 7.2 pinned_pauses.json (Pauses épinglées)

**Contenu**:
```json
{
  "pinned_ids": ["R010", "R018", "R022"],
  "last_updated": "2025-11-05T10:15:00"
}
```

**Comportement**:
- Sauvegardé à chaque épinglage/désépinglage
- Chargé au démarrage de l'onglet Pauses
- Les IDs épinglés apparaissent automatiquement dans la liste sélectionnée

### 7.3 user_config.json (Configuration générale)

**Contenu**:
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

**Paramètres**:

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| clopes_interval_min | int | 120 | Intervalle entre clopes (minutes) |
| calin_duration_min | int | 10 | Durée câlins (minutes) |
| default_pomodoro_duration | int | 25 | Durée Pomodoro par défaut |
| planning_start_auto_calculate | bool | true | Calculer automatiquement heure départ |
| theme | string | "light" | Thème UI (`light`, `dark`) |
| language | string | "fr" | Langue (`fr`, `en`) |

---

## 8️⃣ COULEURS & STYLES - Charte Graphique

### 8.1 Palette de Couleurs Principales

**Couleurs Fonctionnelles**:
```css
:root {
    /* Primary (Bleu) */
    --color-primary-50: #eff6ff;
    --color-primary-100: #dbeafe;
    --color-primary-500: #3b82f6;
    --color-primary-700: #2563eb;

    /* Warning (Orange) */
    --color-warning-50: #fef3c7;
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
    --color-rose-500: #ec4899;
}
```

**Attribution Types de Tâches**:
| Type | Couleur Principale | Bordure | Fond |
|------|-------------------|---------|------|
| Pomodoro | Jaune (`#f59e0b`) | `#f59e0b` | `#fef3c7` |
| Respiration | Bleu (`#3b82f6`) | `#3b82f6` | `#dbeafe` |
| Câlin | Rose (`#ec4899`) | `#ec4899` | `#fce7f3` |
| Clope | Gris (`#6b7280`) | `#6b7280` | `#f3f4f6` |
| Planned | Jaune (`#f59e0b`) | `#f59e0b` | `#fef3c7` + bordure `1px` |
| Temps Mort | Rouge (`#dc2626`) | `#dc2626` | `#f3f4f6` |
| Buffer | Orange (`#f59e0b`) | `#f59e0b` | `#fef3c7` (opacité 0.7) |

### 8.2 Typographie

**Polices**:
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
```

**Hiérarchie**:
```css
h1 {
    font-size: 2em; /* 32px */
    font-weight: 700;
}

h2 {
    font-size: 1.5em; /* 24px */
    font-weight: 600;
}

h3 {
    font-size: 1.25em; /* 20px */
    font-weight: 600;
}

.small {
    font-size: 0.875em; /* 14px */
}

.text-xs {
    font-size: 0.75em; /* 12px */
}
```

### 8.3 Spacing (Espacement)

**Système 4px**:
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

**Usage**:
- Padding cartes: `var(--space-4)` (16px)
- Gap flex/grid: `var(--space-3)` (12px)
- Margin entre sections: `var(--space-6)` (24px)

### 8.4 Ombres (Shadows)

**Niveaux d'élévation**:
```css
:root {
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}
```

**Usage**:
- Cartes: `box-shadow: var(--shadow-md);`
- Modals: `box-shadow: var(--shadow-xl);`
- Hover: `box-shadow: var(--shadow-lg);`

### 8.5 Animations & Transitions

**Durées Standard**:
```css
:root {
    --transition-fast: 0.15s;
    --transition-base: 0.3s;
    --transition-slow: 0.5s;
}
```

**Courbes d'Animation**:
```css
:root {
    --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
    --ease-out: cubic-bezier(0, 0, 0.2, 1);
    --ease-in: cubic-bezier(0.4, 0, 1, 1);
}
```

**Exemple Hover**:
```css
.planning-slot {
    transition: all var(--transition-base) var(--ease-out);
}

.planning-slot:hover {
    transform: translateX(5px);
    box-shadow: var(--shadow-md);
}
```

---

## 9️⃣ INTERACTIONS UTILISATEUR - Workflows

### 9.1 Workflow Principal - Génération Planning

**Étapes**:
1. **Utilisateur charge la page**
   - Auto-calcul heure départ (now + 15min, arrondi à 5)
   - Chargement état sauvegardé (`planning_state.json`)
   - Pré-sélection tâches Pomodoro (si état existe)

2. **Utilisateur sélectionne date**
   - Event: `change` sur `<input type="date">`
   - Action: Recharger `temps_morts.csv` pour la nouvelle date
   - Action: Recharger `TACHES_PLANIFIEES.v2.csv` pour la nouvelle date
   - Action: Effacer planning actuel (panel droit vide)

3. **Utilisateur coche tâches Pomodoro**
   - Event: `change` sur checkboxes
   - Action: Ajouter/retirer ID de `state.selectedPomodoroIds`
   - Action: Mettre à jour compteur "X tâches | Y min (Z Pomodoros)"
   - Action: Sauvegarder état (`POST /api/v2/gitfocus/state`)

4. **Utilisateur ouvre onglet Pauses**
   - Action: Charger pauses épinglées (`GET /api/v2/gitfocus/pinned-pauses`)
   - Action: Afficher pauses épinglées dans panel droit

5. **Utilisateur drag & drop pauses**
   - Event: `dragstart`, `dragover`, `drop`
   - Action: Ajouter pause à liste sélectionnée
   - Action: Autoriser duplicatas (glisser 2x la même pause)
   - Action: Afficher compteur "X pauses | Y min"

6. **Utilisateur clique "Envoyer vers planning"**
   - Action: Construire `state.selectedRespirationIds` (ordre préservé)
   - Action: Sauvegarder état (`POST /api/v2/gitfocus/state`)
   - Action: Afficher notification "Pauses ajoutées au planning"

7. **Utilisateur clique "Générer Planning"**
   - Action: Appeler `POST /api/v2/gitfocus/planning/generate`
   - Body:
     ```json
     {
       "date": "2025-11-05",
       "planning_start_time": "14:00",
       "pomodoro_ids": ["TASK001", "TASK002"],
       "respiration_ids": ["R010", "R018", "R018"],
       "calin_enabled": true,
       "clope_enabled": true,
       "clope_interval_min": 120
     }
     ```
   - Attente: Spinner/loader affiché
   - Succès: Planning affiché dans panel droit
   - Succès: Statistiques mises à jour (footer)
   - Succès: Bouton "Exporter CSV" activé

8. **Utilisateur clique "Exporter CSV"**
   - Action: Écrire `planned.csv` sur serveur
   - Action: Mettre à jour `respiration_planning_history.csv` (append)
   - Action: Incrémenter `EXPORT_COUNT` dans `TACHES_RESPIRATOIRES.v2.csv`
   - Action: Afficher notification "Planning exporté"

### 9.2 Workflow Secondaire - Modification Heure Départ

**Étapes**:
1. **Utilisateur modifie input heure**
   - Event: `change` sur `<input type="time">`
   - Action: Mettre à jour `state.planningStartTime`

2. **Utilisateur clique "Recalculer"** (ou bouton Auto)
   - Action: Recalculer obstacles (temps_morts en minutes relatives)
   - Action: Appeler `rebuildTimeline()` (recalcul minuteOffsets)
   - Action: Rafraîchir affichage planning

### 9.3 Workflow Tertiaire - Épinglage Pauses

**Étapes**:
1. **Utilisateur clique icône 📌 sur pause**
   - Event: `click` sur `.pin-btn`
   - Action: Toggle état épinglé (visuel: bordure bleue)
   - Action: Sauvegarder immédiatement (`POST /api/v2/gitfocus/pinned-pauses`)

2. **Utilisateur refresh page**
   - Action: Charger pauses épinglées (`GET /api/v2/gitfocus/pinned-pauses`)
   - Action: Restaurer pauses dans panel droit (ordre préservé)

---

## 🔟 ÉTATS & TRANSITIONS - Machine à États

### 10.1 États du Planning

**État 1: VIDE** (initial)
- Planning panel: Vide (message "Sélectionnez des tâches et générez le planning")
- Bouton "Générer Planning": Actif (autorisé même si 0 tâches)
- Bouton "Exporter CSV": Désactivé

**État 2: GENERATING** (en cours de génération)
- Planning panel: Spinner/loader
- Bouton "Générer Planning": Désactivé (pas de double-click)
- Bouton "Exporter CSV": Désactivé

**État 3: GENERATED** (planning généré)
- Planning panel: Liste slots affichée
- Bouton "Générer Planning": Actif (régénération autorisée)
- Bouton "Exporter CSV": Actif

**État 4: ERROR** (erreur génération)
- Planning panel: Message d'erreur (fond rouge)
- Bouton "Générer Planning": Actif (retry autorisé)
- Bouton "Exporter CSV": Désactivé

### 10.2 Diagramme de Transitions

```
VIDE
  │
  ├─ User clicks "Générer Planning" ──→ GENERATING
  │
GENERATING
  │
  ├─ API success ──→ GENERATED
  ├─ API error ──→ ERROR
  │
GENERATED
  │
  ├─ User clicks "Générer Planning" again ──→ GENERATING
  ├─ User clicks "Exporter CSV" ──→ GENERATED (state unchanged)
  ├─ User modifies selections ──→ VIDE (planning cleared)
  │
ERROR
  │
  ├─ User clicks "Générer Planning" (retry) ──→ GENERATING
```

### 10.3 Variables d'État JavaScript

```javascript
const state = {
    // Planning generation
    planningStartTime: Date,          // ex: new Date('2025-11-05T14:00:00')
    planningStatus: 'empty',          // 'empty' | 'generating' | 'generated' | 'error'

    // Selections
    selectedPomodoroIds: [],          // ex: ['TASK001', 'TASK002']
    selectedRespirationIds: [],       // ex: ['R010', 'R018', 'R018'] (duplicates allowed)

    // Options
    calinEnabled: false,
    clopeEnabled: false,
    clopeIntervalMin: 120,

    // Data loaded
    pomodoroTasks: [],                // Loaded from LISTE_MERE.v2.csv
    recurrentTasks: [],               // Loaded from TACHES_RECURRENTES.v2.csv
    plannedTasks: [],                 // Loaded from TACHES_PLANIFIEES.v2.csv

    // Timeline (linear system)
    timeline: {
        tasks: [],                    // [{minuteOffset, duration, type, ...}]
        obstacles: []                 // [{startMinute, endMinute, type, ...}]
    },

    // Generated planning (display format)
    generatedPlanning: [],            // [{date, heure_debut, heure_fin, task_name, ...}]
    statistics: {}                    // {total_work_min, total_pause_min, ...}
};
```

---

## ✅ CHECKLIST FINALE - Couverture Documentation

- [✅] Layout général interface (header, controls, 2 colonnes)
- [✅] Onglet Pomodoro (carte tâche, modal édition, filtres)
- [✅] Onglet Pauses (2 colonnes, drag & drop, épinglage)
- [✅] Onglet Récurrentes (toggle switch, liste)
- [✅] Planning généré (slots fins, couleurs par type, statistiques)
- [✅] Structure complète LISTE_MERE.v2.csv (16 colonnes)
- [✅] Structure complète TACHES_RECURRENTES.v2.csv (fusion respirations)
- [✅] Structure complète TACHES_PLANIFIEES.v2.csv
- [✅] Structure complète temps_morts.csv
- [✅] Structure complète categories.csv
- [✅] Structure complète planned.csv (export)
- [✅] Structure complète respiration_planning_history.csv
- [✅] Fichiers JSON config (planning_state, pinned_pauses, user_config)
- [✅] Charte graphique (couleurs, typographie, spacing, ombres, animations)
- [✅] Workflows utilisateur (génération planning, modification heure, épinglage)
- [✅] Machine à états (VIDE → GENERATING → GENERATED → ERROR)

---

**Document créé le**: 2025-11-05
**Auteur**: Claude (Anthropic)
**Supervision**: Julio
**Version**: 3.0 Complète
**Lignes**: 1500+
**Statut**: Prêt pour implémentation

---

## 📝 NOTES FINALES

Ce document contient **TOUTES** les spécifications nécessaires pour implémenter l'interface et la structure de données sans ambiguïté. Combiné avec:

1. `PLAN_REFONTE_V3.md` - Phases d'implémentation détaillées
2. `FLUX_PLANNING_LINEAR.md` - Algorithme de génération (12 étapes)
3. `TIMELINE_LINEAR_SPEC_BACKUP.md` - Fonctions timeline (récupérées de git)
4. `CLARIFICATIONS_LOGIQUE_V3.md` - Questions à résoudre

Vous avez une documentation **exhaustive et sans ambiguïté** pour démarrer l'implémentation V3.

**Prochaine étape suggérée**: Répondre aux 5 questions CRITIQUES de `CLARIFICATIONS_LOGIQUE_V3.md` pour débloquer les phases 0-3 du plan.
