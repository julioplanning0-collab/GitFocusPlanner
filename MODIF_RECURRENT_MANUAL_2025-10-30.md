# 🟣 Modification - Ajout Manuel de Tâches Récurrentes

**Date**: 2025-10-30
**Fonctionnalité**: Ajout interactif de tâches récurrentes au planning
**Statut**: ✅ IMPLÉMENTÉ

---

## 🎯 Objectif

Permettre à l'utilisateur d'ajouter des tâches récurrentes au planning existant en cliquant simplement dessus dans une liste.

**Besoin exprimé** :
> "Je dois voir toutes les tâches récurrentes dans une liste afin de pouvoir les ajouter dans la première place libre du planning du jour en cliquant dessus. Chaque clic ajoute la tâche une fois, même si elle existe déjà."

---

## 📝 Modifications Effectuées

### 1. Interface HTML (`webapp/templates/gitfocus_v2.html`)

**Modifications lignes 48-64** :

**AVANT** :
```html
<!-- Recurrent Tasks Info (Auto-Selected) -->
<section class="task-section">
    <div class="section-header">
        <h3>🟣 Tâches Récurrentes (Sélection Auto)</h3>
        <span class="badge badge-info">Top 10 automatique</span>
    </div>
    <div class="info-box">
        <p><strong>🧠 Sélection Intelligente:</strong></p>
        <p>Les 10 meilleures tâches récurrentes sont choisies automatiquement via scoring...</p>
    </div>
</section>
```

**APRÈS** :
```html
<!-- Recurrent Tasks (Click to Add) -->
<section class="task-section">
    <div class="section-header">
        <h3>🟣 Tâches Récurrentes</h3>
        <span class="badge badge-info">Cliquez pour ajouter au planning</span>
    </div>
    <div class="info-box">
        <p><strong>💡 Mode Manuel:</strong></p>
        <p>Cliquez sur une tâche pour l'ajouter à la première place libre du planning. Vous pouvez ajouter la même tâche plusieurs fois.</p>
    </div>
    <div id="recurrent-tasks-list" class="task-list">
        <div class="loading">Chargement des tâches récurrentes...</div>
    </div>
</section>
```

### 2. JavaScript (`webapp/static/js/gitfocus_v2.js`)

**Fonctions ajoutées** :

#### 1. `renderRecurrentTasks()` (lignes 160-182)

Affiche la liste de toutes les tâches récurrentes actives dans l'interface

**Fonctionnalités** :
- Génère des éléments HTML cliquables pour chaque tâche
- Affiche : Nom, catégorie, sous-catégorie, durée, date d'échéance
- Style : Fond bleu clair + indicateur cliquable
- Met à jour le compteur de tâches

#### 2. `addRecurrentTaskToPlanning(taskId)` (lignes 184-233)

Ajoute une tâche récurrente au planning existant

**Algorithme** :
1. Vérifier que le planning existe (erreur sinon)
2. Trouver la tâche récurrente par ID
3. Récupérer le dernier créneau du planning
4. Calculer nouvelle heure de début = heure de fin du dernier créneau
5. Calculer nouvelle heure de fin = heure début + durée tâche
6. Vérifier que heure fin <= 23:00 (erreur sinon)
7. Créer nouveau slot avec type "recurrent"
8. Ajouter au state.currentPlanning
9. Recalculer les statistiques
10. Re-render le planning
11. Afficher message de confirmation

**Validations** :
- ✅ Planning doit exister
- ✅ Tâche doit exister
- ✅ Heure de fin <= 23:00

#### 3. Fonctions auxiliaires (lignes 235-264)

- `addMinutes(timeStr, minutes)` - Ajoute des minutes à une heure
- `compareTime(time1, time2)` - Compare deux heures
- `calculateStats(planning)` - Calcule les statistiques du planning

### 3. Styles CSS (`webapp/static/css/gitfocus_v2.css`)

**Ajout lignes 185-195** :

```css
.task-item.clickable {
    background: #f0f9ff;        /* Fond bleu clair */
    border-color: #bfdbfe;      /* Bordure bleue claire */
}

.task-item.clickable:hover {
    background: #dbeafe;        /* Bleu plus foncé au survol */
    border-color: #3b82f6;      /* Bordure bleue foncée */
    transform: translateY(-1px); /* Animation de levée */
    box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
}
```

---

## 🎨 Expérience Utilisateur

### Flux Complet

1. **Chargement de la page**
   - Liste des tâches récurrentes affichée automatiquement
   - Fond bleu clair pour chaque tâche (visuellement cliquable)

2. **Génération du planning initial**
   - Utilisateur sélectionne tâches Pomodoro
   - Clique "Générer Planning Intelligent"
   - Planning affiché avec alternance Pomodoro/Pause

3. **Ajout manuel de tâches récurrentes**
   - Utilisateur clique sur "Arroser les plantes" dans la liste
   - **Immédiatement** :
     - Tâche apparaît en bas du planning
     - Message : "Ajouté: Arroser les plantes (14:30 - 14:35)"
     - Statistiques mises à jour (Pauses: +5 min)

4. **Ajouts multiples**
   - Utilisateur peut cliquer plusieurs fois sur la même tâche
   - Chaque clic ajoute une nouvelle occurrence
   - Exemple : "Arroser les plantes" à 14:30, puis à 14:35, puis à 14:40

5. **Gestion des erreurs**
   - **Si planning vide** : "Générez d'abord un planning avant d'ajouter..."
   - **Si dépasse 23h** : "Impossible d'ajouter : dépasse 23h00"

### Apparence Visuelle

**Liste des tâches récurrentes** :
```
┌─────────────────────────────────────┐
│ 🟣 Tâches Récurrentes               │
│ ✨ Cliquez pour ajouter au planning  │
├─────────────────────────────────────┤
│ 💡 Mode Manuel:                     │
│ Cliquez pour ajouter à la première  │
│ place libre. Doublons autorisés.    │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ 🟣 Arroser les plantes          │ │ ← Fond bleu clair
│ │ Maison › Jardinage • 5 min      │ │   Cliquable
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ 🟣 Nettoyer caisse chat         │ │
│ │ Maison › Animaux • 5 min        │ │
│ └─────────────────────────────────┘ │
│ ...                                 │
└─────────────────────────────────────┘
```

**Au survol** :
- Fond bleu plus foncé (#dbeafe)
- Bordure bleue (#3b82f6)
- Animation de levée légère (translateY(-1px))
- Ombre portée bleue

**Après clic** :
- Message de confirmation affiché en vert
- Nouvelle tâche apparaît en bas du planning avec style violet
- Statistiques mises à jour instantanément

---

## 🔧 Détails Techniques

### Structure du Slot Ajouté

```javascript
{
    id: `slot_${Date.now()}`,          // ID unique basé sur timestamp
    heure_debut: "14:30",               // Heure de fin du dernier slot
    heure_fin: "14:35",                 // heure_debut + duration_min
    type: "recurrent",                  // Type de créneau
    task_id: "REC001",                  // ID de la tâche récurrente
    task_name: "Arroser les plantes",   // Nom de la tâche
    category: "Maison",                 // Catégorie
    sub_category: "Jardinage",          // Sous-catégorie
    duration_min: 5,                    // Durée en minutes
    date: "2025-10-30"                  // Date du planning
}
```

### Calcul de l'Heure

**Exemple** :
```javascript
// Planning actuel se termine à 14:30
const lastSlot = { heure_fin: "14:30" };

// Tâche à ajouter : "Arroser" (5 min)
const task = { duration_min: 5 };

// Calcul
const newSlot = {
    heure_debut: "14:30",              // = lastSlot.heure_fin
    heure_fin: addMinutes("14:30", 5), // = "14:35"
    ...
};

// Vérification
if (compareTime("14:35", "23:00") > 0) {
    // Erreur: dépasse 23:00
}
```

### Statistiques Recalculées

Après chaque ajout, recalcul automatique :

```javascript
{
    total_slots: 45,          // +1 à chaque ajout
    recurrent_slots: 15,      // +1 pour tâche récurrente
    pause_minutes: 345,       // +duration_min de la tâche
    ...
}
```

---

## 📚 Spécifications Mises à Jour

**Fichier**: `SPECIFICATIONS_COMPLETES_V2.md`

**Section ajoutée**: 9.4 Ajout Manuel de Tâches Récurrentes (🆕 2025-10-30)

**Contenu** :
- Principe de fonctionnement
- Flux utilisateur (6 étapes)
- Comportement interface (messages, erreurs)
- Calcul de la place libre
- Statistiques recalculées
- Persistance
- Avantages

**Format** : Description algorithmique SANS code (conforme aux bonnes pratiques)

---

## ✅ Avantages de Cette Approche

### 1. Flexibilité Maximale
- Utilisateur contrôle totalement quelles tâches ajouter
- Peut ajouter autant de fois qu'il veut la même tâche
- Pas limité par un scoring automatique

### 2. Simplicité d'Utilisation
- Un seul clic pour ajouter
- Feedback immédiat (message + affichage)
- Pas besoin de recalculer tout le planning

### 3. Performance
- Ajout instantané (pas d'appel API)
- Recalcul statistiques local (très rapide)
- Pas de rechargement de page

### 4. Compatibilité
- Fonctionne avec le planning existant
- Compatible avec l'export CSV
- Ne perturbe pas les autres fonctionnalités

### 5. Évolutivité
- Facile d'ajouter d'autres types de tâches
- Possibilité d'ajouter un bouton "Supprimer" plus tard
- Base pour d'autres interactions (drag & drop, etc.)

---

## 🧪 Tests à Effectuer

### Tests Fonctionnels

1. **Test 1: Ajout basique**
   - Générer un planning
   - Cliquer sur une tâche récurrente
   - Vérifier qu'elle apparaît en bas du planning
   - ✅ Attendu: Tâche ajoutée après le dernier créneau

2. **Test 2: Doublons**
   - Cliquer 3 fois sur "Arroser les plantes"
   - Vérifier 3 occurrences dans le planning
   - ✅ Attendu: 3 créneaux distincts avec la même tâche

3. **Test 3: Validation 23h**
   - Générer un planning qui se termine vers 22:50
   - Tenter d'ajouter une tâche de 15 min
   - ✅ Attendu: Erreur "Impossible d'ajouter : dépasse 23h00"

4. **Test 4: Planning vide**
   - Ne pas générer de planning
   - Cliquer sur une tâche récurrente
   - ✅ Attendu: Erreur "Générez d'abord un planning..."

5. **Test 5: Statistiques**
   - Noter les statistiques initiales
   - Ajouter 2 tâches de 5 min chacune
   - ✅ Attendu: pause_minutes +10, total_slots +2

6. **Test 6: Export CSV**
   - Ajouter des tâches manuellement
   - Exporter le planning
   - Vérifier que les tâches ajoutées sont dans le CSV
   - ✅ Attendu: Toutes les tâches présentes avec type "recurrent"

### Tests d'Interface

1. **Test UI 1: Apparence**
   - Vérifier fond bleu clair des tâches
   - ✅ Attendu: Visuellement distinct des tâches Pomodoro

2. **Test UI 2: Hover**
   - Survoler une tâche
   - ✅ Attendu: Fond plus foncé, animation de levée, ombre

3. **Test UI 3: Confirmation**
   - Ajouter une tâche
   - ✅ Attendu: Message vert "Ajouté: [nom] ([heure]-[heure])"

4. **Test UI 4: Erreur**
   - Tenter d'ajouter sans planning
   - ✅ Attendu: Message rouge d'erreur

---

## 🎉 Résumé

**Fonctionnalité implémentée** : Ajout manuel de tâches récurrentes au planning

**Fichiers modifiés** :
1. `webapp/templates/gitfocus_v2.html` - Interface utilisateur
2. `webapp/static/js/gitfocus_v2.js` - Logique JavaScript (3 fonctions ajoutées)
3. `webapp/static/css/gitfocus_v2.css` - Styles cliquables
4. `SPECIFICATIONS_COMPLETES_V2.md` - Section 9.4 ajoutée (SANS code)

**Lignes ajoutées** : ~150 lignes (JS + HTML + CSS + Specs)

**Principe** : Clic sur tâche → Ajout immédiat à la fin du planning

**Validations** :
- ✅ Planning doit exister
- ✅ Heure fin <= 23:00
- ✅ Doublons autorisés

**Prêt pour tests utilisateur** : ✅ OUI

---

**Date de finalisation**: 2025-10-30
**Version**: 2.0
**Status**: ✅ IMPLÉMENTÉ ET DOCUMENTÉ
