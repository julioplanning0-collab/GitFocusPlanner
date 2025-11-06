# SPECIFICATIONS INTERFACE V3 - GITFOCUS PLANNER

**Date**: 2025-11-05
**Version**: 3.0
**Architecture**: Interface web à 2 onglets (Planning + Tâches Récurrentes)

---

## VUE D'ENSEMBLE

L'interface V3 est composée de **2 onglets principaux** :

1. **Onglet "Planning"** - Pour organiser les tâches Pomodoro avec horaires fixes
2. **Onglet "Tâches Récurrentes"** - Pour gérer des tâches quotidiennes sans horaires fixes

---

## ONGLET 1: PLANNING

### Description
Cet onglet affiche un planning chronologique avec des créneaux horaires (de 06:00 à 00:00).

### Contenu
- **Timeline verticale** avec horaires
- **Tâches Pomodoro** (25 min) avec nom + catégorie
- **Pauses** (durée variable) entre les Pomodoros
- **Temps morts** (créneaux bloqués, ex: réunions)

### Actions
- **Générer le planning** : Bouton qui appelle l'API `/api/planning/generate`
- **Exporter en CSV** : Bouton qui exporte le planning généré

### Données affichées
Chaque tâche affiche :
- Heure de début - Heure de fin
- Nom de la tâche
- Type (work / pause / recurrent)
- Durée (en minutes)

---

## ONGLET 2: TÂCHES RÉCURRENTES

### Description
Cet onglet permet de gérer une **liste de tâches quotidiennes** (sans horaires fixes) qu'on peut ajouter manuellement au planning.

### Structure

#### Section 1: Bibliothèque de tâches récurrentes (gauche)

**Organisation hiérarchique** :
```
📁 Catégorie 1 (ex: Hygiène)
  📁 Sous-catégorie 1.1 (ex: Matin)
    ✓ Tâche 1 (Douche - 15 min)
    ✓ Tâche 2 (Brossage dents - 5 min)
  📁 Sous-catégorie 1.2 (ex: Soir)
    ✓ Tâche 3 (Routine soir - 10 min)

📁 Catégorie 2 (ex: Ménage)
  📁 Sous-catégorie 2.1 (ex: Quotidien)
    ✓ Tâche 4 (Vaisselle - 20 min)
    ✓ Tâche 5 (Rangement - 15 min)
```

**Fonctionnalités** :
- Affichage arborescent (catégorie > sous-catégorie > tâches)
- Click sur une tâche → **Ajoute** la tâche à la liste sélectionnée (droite)
- Peut ajouter **plusieurs fois la même tâche** (ex: "Vaisselle" × 3)
- Boutons **Éditer** et **Supprimer** sur chaque tâche

#### Section 2: Liste des tâches sélectionnées (droite)

**Contenu** :
- Liste ordonnée des tâches récurrentes sélectionnées pour la journée
- Chaque item affiche : **Nom** + **Durée** (ex: "Douche - 15 min")
- Possibilité d'ajouter la même tâche plusieurs fois

**Fonctionnalités** :
- **Drag & Drop** : Réorganiser l'ordre des tâches
- **Bouton "×"** : Supprimer une tâche de la liste
- **Bouton "Générer Planning"** : Envoie la liste à l'API pour créer le planning

---

## FLUX UTILISATEUR

### Workflow Tâches Récurrentes

1. **Ajout de tâches** :
   - User clique sur "Tâches Récurrentes" (onglet)
   - User parcourt les catégories/sous-catégories
   - User clique sur "Douche - 15 min" → **Ajoute** à la liste sélectionnée
   - User clique à nouveau sur "Douche - 15 min" → **Ajoute une 2ème fois**

2. **Réorganisation** :
   - User utilise **Drag & Drop** pour réordonner les tâches
   - Exemple : Déplacer "Douche" en premier, puis "Petit-déjeuner", etc.

3. **Génération du planning** :
   - User clique sur **"Générer Planning"**
   - API `/api/planning/generate` est appelée avec :
     - Date
     - Heure de début du planning
     - Liste des tâches récurrentes sélectionnées (avec ordre)
   - Backend génère un planning chronologique en alternant work/pause
   - Frontend affiche le planning dans l'**Onglet "Planning"**

### Workflow Planning

1. User bascule sur l'onglet **"Planning"**
2. Timeline affiche les tâches générées avec horaires
3. User peut **Exporter en CSV** pour utilisation externe

---

## DONNÉES CSV

### Fichier source: `TACHES_RECURRENTES.v2.csv`

**Format** :
```csv
ID;NAME;DESCRIPTION;CATEGORY;SUB_CATEGORY;DURATION_MIN;RECURRENCE_TYPE;RECURRENCE_INTERVAL;LAST_DONE_DATE;NEXT_DUE_DATE;PRIORITY;STATUS;IS_ACTIVE
REC001;Douche;Douche matinale;Hygiène;Matin;15;daily;1;2025-11-04;2025-11-05;1;todo;1
REC002;Vaisselle;Laver la vaisselle;Ménage;Quotidien;20;daily;1;2025-11-04;2025-11-05;2;todo;1
```

**Champs utilisés par l'interface** :
- `ID` : Identifiant unique (REC001, REC002, ...)
- `NAME` : Nom de la tâche (ex: "Douche")
- `CATEGORY` : Catégorie principale (ex: "Hygiène")
- `SUB_CATEGORY` : Sous-catégorie (ex: "Matin")
- `DURATION_MIN` : Durée en minutes (15, 20, ...)
- `IS_ACTIVE` : 0 ou 1 (seules les tâches actives sont affichées)

---

## API ENDPOINTS UTILISÉS

### GET `/api/planning/tasks/pomodoro`
Récupère la liste des tâches Pomodoro (work tasks).

**Response** :
```json
{
  "success": true,
  "data": [
    {
      "id": "TASK001",
      "name": "Réviser mathématiques",
      "duration": 25,
      "category": "Études"
    }
  ]
}
```

### POST `/api/planning/generate`
Génère le planning chronologique.

**Request** :
```json
{
  "date": "2025-11-05",
  "planningStartTime": "08:00",
  "selectedRecurrentIds": ["REC001", "REC002", "REC001"]
}
```

**Response** :
```json
{
  "success": true,
  "data": {
    "timeline": [
      {
        "type": "recurrent",
        "name": "Douche",
        "start_time": "08:00",
        "end_time": "08:15",
        "duration": 15
      },
      {
        "type": "pause",
        "name": "Pause",
        "start_time": "08:15",
        "end_time": "08:20",
        "duration": 5
      },
      {
        "type": "recurrent",
        "name": "Vaisselle",
        "start_time": "08:20",
        "end_time": "08:40",
        "duration": 20
      }
    ],
    "statistics": {
      "total_recurrent_minutes": 50,
      "total_pause_minutes": 5,
      "task_count": 3
    }
  }
}
```

### POST `/api/planning/export`
Exporte le planning en CSV.

**Request** :
```json
{
  "date": "2025-11-05",
  "timeline": [ ... ]
}
```

**Response** :
```json
{
  "success": true,
  "data": {
    "csv_path": "prod_data/planned.csv",
    "task_count": 15
  }
}
```

---

## MAQUETTE INTERFACE

### Onglet "Tâches Récurrentes"

```
┌─────────────────────────────────────────────────────────────────┐
│ [Planning] [Tâches Récurrentes ✓]                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────┐  ┌───────────────────────────┐   │
│  │ BIBLIOTHÈQUE             │  │ TÂCHES SÉLECTIONNÉES       │   │
│  │                          │  │                            │   │
│  │ 📁 Hygiène               │  │ 1. Douche - 15 min     [×] │   │
│  │   📁 Matin               │  │ 2. Vaisselle - 20 min  [×] │   │
│  │     ✓ Douche - 15 min    │  │ 3. Douche - 15 min     [×] │   │
│  │     ✓ Brossage - 5 min   │  │                            │   │
│  │   📁 Soir                │  │ [Générer Planning]          │   │
│  │     ✓ Routine - 10 min   │  │                            │   │
│  │                          │  │                            │   │
│  │ 📁 Ménage                │  │                            │   │
│  │   📁 Quotidien           │  │                            │   │
│  │     ✓ Vaisselle - 20 min │  │                            │   │
│  │     ✓ Rangement - 15 min │  │                            │   │
│  │                          │  │                            │   │
│  │ [+ Nouvelle tâche]       │  │                            │   │
│  └──────────────────────────┘  └───────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Onglet "Planning"

```
┌─────────────────────────────────────────────────────────────────┐
│ [Planning ✓] [Tâches Récurrentes]                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Date: [05/11/2025 ▼]  Heure début: [08:00]  [Générer]          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 08:00 - 08:15  │ Douche (Hygiène)          │ 15 min    │    │
│  │ 08:15 - 08:20  │ Pause                     │  5 min    │    │
│  │ 08:20 - 08:40  │ Vaisselle (Ménage)        │ 20 min    │    │
│  │ 08:40 - 08:45  │ Pause                     │  5 min    │    │
│  │ 08:45 - 09:00  │ Douche (Hygiène)          │ 15 min    │    │
│  │ 09:00 - 09:05  │ Pause                     │  5 min    │    │
│  │ ...                                                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  [Exporter CSV]                                                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## INTERACTIONS UTILISATEUR

### Drag & Drop

**Bibliothèque HTML5** : Utiliser l'API native `draggable`

**Événements** :
- `dragstart` : Commence le drag
- `dragover` : Survole une zone de drop
- `drop` : Lâche l'élément

**Implémentation** :
```javascript
// Exemple simplifié
item.addEventListener('dragstart', (e) => {
  e.dataTransfer.setData('task-id', item.dataset.id);
});

dropZone.addEventListener('drop', (e) => {
  const taskId = e.dataTransfer.getData('task-id');
  // Réorganiser la liste
});
```

### Click sur tâche récurrente

**Action** : Ajouter la tâche à la liste sélectionnée

**Code** :
```javascript
taskItem.addEventListener('click', () => {
  selectedTasks.push({
    id: task.id,
    name: task.name,
    duration: task.duration_min,
    category: task.category
  });
  renderSelectedTasks();
});
```

---

## STYLES CSS

### Couleurs

- **Background principal** : `#f9fafb` (gris très clair)
- **Panneau gauche** : `#ffffff` (blanc)
- **Panneau droit** : `#f3f4f6` (gris clair)
- **Tâche récurrente** : `#dbeafe` (bleu clair)
- **Pause** : `#fef3c7` (jaune clair)
- **Bordures** : `#e5e7eb` (gris moyen)

### Layout

- **Grid 2 colonnes** : `60% (bibliothèque)` + `40% (liste sélectionnée)`
- **Gap** : `20px`
- **Padding** : `16px`

---

## RÈGLES DE VALIDATION

### Tâche récurrente valide

- `NAME` : Non vide
- `DURATION_MIN` : > 0
- `CATEGORY` : Non vide
- `SUB_CATEGORY` : Non vide
- `IS_ACTIVE` : = 1

### Planning valide

- Au moins 1 tâche sélectionnée
- `date` : Format `YYYY-MM-DD`
- `planningStartTime` : Format `HH:MM`

---

## MESSAGES D'ERREUR

### Erreurs possibles

1. **Aucune tâche sélectionnée** : "Veuillez sélectionner au moins une tâche récurrente"
2. **Date invalide** : "Format de date invalide (YYYY-MM-DD attendu)"
3. **Heure invalide** : "Format d'heure invalide (HH:MM attendu)"
4. **Erreur API** : "Erreur lors de la génération du planning : {message}"

---

## ÉVOLUTIONS FUTURES

### Phase 2
- **Recherche** dans la bibliothèque de tâches
- **Filtres** par catégorie
- **Favoris** : Marquer des tâches comme favorites

### Phase 3
- **Templates de journée** : Sauvegarder une liste de tâches pour réutilisation
- **Import/Export** de listes de tâches
- **Statistiques** : Temps passé par catégorie

---

**Fin des spécifications**
