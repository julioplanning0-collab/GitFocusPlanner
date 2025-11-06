# Clarifications de la Logique V3 - Questions & Réponses

**Date**: 2025-11-05
**Objectif**: Lever TOUTES les ambiguïtés avant l'implémentation

---

## 🎯 STRUCTURE DU DOCUMENT

Ce document pose des questions précises sur chaque aspect ambigu du système. Chaque question attend une réponse claire avant l'implémentation.

---

## 1️⃣ ONGLET PAUSES - Interface Drag & Drop

### Question 1.1: Layout exact de l'onglet

**Question**: Comment est organisé l'onglet Pauses ?

**Options**:
- A) 2 colonnes verticales (gauche = source, droite = sélection)
- B) 2 lignes horizontales (haut = source, bas = sélection)
- C) Autre layout ?

**Réponse attendue**: [A/B/C + description si C]

---

### Question 1.2: Actions disponibles sur les tâches sélectionnées

**Question**: Que peut faire l'utilisateur dans la liste "Pauses sélectionnées" ?

**Options possibles** (cocher toutes celles qui s'appliquent):
- [ ] Supprimer une pause (bouton X ou drag vers poubelle)
- [ ] Réorganiser l'ordre par drag & drop
- [ ] Dupliquer une pause (clic ou bouton +)
- [ ] Épingler une pause (icône punaise pour persister)
- [ ] Éditer la durée d'une pause
- [ ] Autre ?

**Réponse attendue**: Liste des actions + icônes/boutons à afficher

---

### Question 1.3: Comportement du bouton "Envoyer vers planning"

**Question**: Que se passe-t-il exactement quand on clique "Envoyer vers planning" ?

**Scénarios à clarifier**:

**Scénario A**: Onglet Pauses ouvert, liste de pauses sélectionnées remplie
- Utilisateur clique "Envoyer vers planning"
- → Que se passe-t-il ?
  - a) Génère IMMÉDIATEMENT le planning (Pomodoros + Pauses)
  - b) Ajoute seulement les pauses à la timeline, l'utilisateur doit encore cliquer "Générer planning"
  - c) Autre ?

**Scénario B**: Utilisateur modifie la liste de pauses APRÈS avoir généré le planning
- → Le planning se régénère automatiquement ?
- → Ou faut-il cliquer à nouveau "Envoyer vers planning" ?

**Réponse attendue**: Scénario A [a/b/c] + Scénario B [auto/manuel]

---

### Question 1.4: Persistance des pauses sélectionnées

**Question**: Quand les pauses sélectionnées sont-elles sauvegardées sur le serveur ?

**Options**:
- A) À chaque modification (drag, suppression, ajout)
- B) Seulement quand utilisateur clique "Envoyer vers planning"
- C) Seulement quand utilisateur clique un bouton "Sauvegarder"
- D) Jamais (seulement en mémoire, perdu au refresh)

**Réponse attendue**: [A/B/C/D]

---

### Question 1.5: Épinglage (pinned tasks)

**Question**: Comment fonctionne l'épinglage ?

**Clarifications nécessaires**:
- Icône pour épingler ? (punaise 📌, étoile ⭐, autre ?)
- Visuel différent pour tâches épinglées ? (bordure bleue, fond coloré ?)
- Les tâches épinglées restent TOUJOURS dans la liste sélectionnée, même après refresh ?
- Peut-on désépingler ? (clic sur l'icône toggle on/off ?)
- Les tâches épinglées peuvent être supprimées de la liste sélectionnée ?

**Réponse attendue**: Description complète du comportement

---

## 2️⃣ GÉNÉRATION DU PLANNING - Boutons et Actions

### Question 2.1: Boutons disponibles

**Question**: Quels boutons l'utilisateur voit-il dans l'interface planning ?

**Liste actuelle supposée**:
1. "Initialiser le planning" (onglet Pomodoro)
2. "Générer planning" (onglet Pomodoro)
3. "Envoyer vers planning" (onglet Pauses)
4. "Recalculer planning" (à côté de l'heure de départ)
5. "Exporter CSV"

**Questions**:
- Ces 5 boutons existent-ils tous ?
- Quelle est la DIFFÉRENCE entre "Initialiser" et "Générer" ?
- "Recalculer" est-il automatique ou manuel ?
- Autre boutons manquants ?

**Réponse attendue**: Liste complète des boutons + action de chacun

---

### Question 2.2: Workflow complet utilisateur

**Question**: Dans quel ORDRE l'utilisateur doit-il cliquer pour générer un planning ?

**Workflow supposé**:
1. Sélectionner date
2. Sélectionner tâches Pomodoro (checkboxes)
3. Aller dans onglet Pauses
4. Drag & drop pauses vers liste sélectionnée
5. Cliquer "Envoyer vers planning"
6. Cliquer "Générer planning" (ou automatique ?)
7. Planning s'affiche

**Est-ce correct ?** Si non, donner le workflow exact.

**Réponse attendue**: Liste numérotée des étapes

---

### Question 2.3: Modification du planning généré

**Question**: Peut-on modifier le planning APRÈS génération ?

**Options**:
- A) Non, le planning est figé, faut régénérer si changement
- B) Oui, on peut drag & drop les slots pour réorganiser
- C) Oui, on peut supprimer des slots (bouton X)
- D) Oui, on peut éditer l'heure de début d'un slot (input)
- E) Autre ?

**Si B/C/D/E**: Comment la timeline est-elle mise à jour ?
- Appel automatique de `rebuildTimeline()` ?
- Recalcul complet ou juste ajustement local ?

**Réponse attendue**: Liste des actions possibles + mécanisme de mise à jour

---

## 3️⃣ AFFICHAGE DU PLANNING - Lignes Très Fines

### Question 3.1: Hauteur exacte des lignes

**Question**: "Très fines verticalement" signifie quelle hauteur ?

**Options**:
- A) 20px (ultra-compact)
- B) 30px (compact)
- C) 40px (standard)
- D) Variable selon le type de tâche
- E) Autre ?

**Réponse attendue**: Hauteur en pixels

---

### Question 3.2: Affichage tout sur une ligne

**Question**: Comment afficher TOUTES les infos sur une seule ligne ?

**Informations à afficher**:
- Heure début - Heure fin
- Nom de la tâche
- Durée (min)
- Index Pomodoro (1/3, 2/3...) si applicable
- Badge "Replanifiée" si applicable
- Icône type de tâche ?

**Layout proposé** (exemple):
```
[10:00-10:25] Révision maths (25 min) [1/3]
```

**Est-ce correct ?** Si non, donner le format exact.

**Réponse attendue**: Template exact avec toutes les infos

---

### Question 3.3: Drag & drop dans le planning

**Question**: Les lignes du planning sont-elles draggables APRÈS génération ?

**Si OUI**:
- Peut-on déplacer n'importe quelle tâche ?
- Ou seulement certaines (pas les temps_morts, pas les FIXED) ?
- Quand on drag une ligne, comment choisir la nouvelle position ?
  - a) Drop sur une autre ligne (swap)
  - b) Drop dans un espace (insertion)
  - c) Drop sur une poubelle (suppression)
- La timeline est recalculée automatiquement après drop ?

**Si NON**:
- Le planning est en lecture seule après génération ?
- Pour modifier, faut-il changer les sélections et régénérer ?

**Réponse attendue**: OUI/NON + détails si OUI

---

## 4️⃣ TEMPS RELATIF - Système de Calcul

### Question 4.1: Point zéro et multi-jours

**Question**: Le système supporte-t-il les plannings multi-jours ?

**Scénario**:
- planningStartTime = 2025-11-05 22:00 (10pm)
- Planning contient 10 Pomodoros (250 min = 4h10)
- → Dernière tâche se termine à 2025-11-06 02:10 (2am jour suivant)

**Questions**:
- Le système gère-t-il ce cas ?
- Les temps_morts du jour suivant sont-ils chargés automatiquement ?
- L'affichage montre-t-il la date pour chaque slot ?

**Réponse attendue**: OUI/NON + gestion de la transition jour suivant

---

### Question 4.2: Temps négatifs (heures passées)

**Question**: Que se passe-t-il si planningStartTime est dans le futur mais temps_morts dans le passé ?

**Scénario**:
- planningStartTime = 2025-11-05 14:00 (minute 0)
- temps_mort: 2025-11-05 12:00-13:00 (déjeuner)
- → temps_mort a `startMinute = -120` (2h AVANT le point zéro)

**Questions**:
- Ce temps_mort est-il filtré (ignoré) ?
- Ou est-il conservé dans state.timeline.obstacles ?
- Si conservé, affecte-t-il le placement des tâches ?

**Réponse attendue**: Filtré/Conservé + logique si conservé

---

## 5️⃣ COLLISIONS ET OBSTACLES

### Question 5.1: Priorités en cas de conflit

**Question**: Quelle est la PRIORITÉ EXACTE des obstacles ?

**Flux indique** (ÉTAPE 10):
1. Temps_mort (priorité absolue)
2. Tâche planifiée (priorité secondaire)
3. Pomodoro/Respiration (placés dans les trous)

**Mais que se passe-t-il si** :
- Tâche planifiée prévue à 14:00-14:30
- Temps_mort existe à 14:00-15:00
- → Que devient la tâche planifiée ?

**Options**:
- A) Tâche planifiée repoussée APRÈS le temps_mort (15:00)
- B) Tâche planifiée placée AVANT le temps_mort (si espace)
- C) Tâche planifiée annulée (pas affichée)
- D) Autre ?

**Réponse du flux** (ligne 144): "Placer le temps_mort en premier, placer la tâche planifiée juste après, **pas de respiration** entre"

**MAIS**: Comment gérer le cas où l'espace APRÈS le temps_mort est occupé par un Pomodoro déjà placé ?

**Réponse attendue**: Algorithme précis de résolution de conflit

---

### Question 5.2: Slot "Bientôt temps mort"

**Question**: Les slots "Bientôt temps mort" doivent-ils être affichés ?

**Contexte** (ÉTAPE 10.1 du flux):
> Si trou < durée d'une tâche, insérer slot "Bientôt temps mort"

**Questions**:
- Ce slot est-il visible dans le planning affiché ?
- Quelle couleur/style ? (gris clair ? orange ?)
- Affiche-t-il une info-bulle ? (ex: "Temps mort dans 10 min")
- Peut-on cliquer dessus pour voir le temps_mort concerné ?
- Est-il draggable ou supprimable ?

**Réponse attendue**: OUI/NON affiché + style si affiché

---

### Question 5.3: Tâche planifiée pendant temps mort

**Question**: Le flux dit (ligne 144):
> "Si tâche planifiée pendant temps_mort: placer temps_mort, puis tâche planifiée après, **pas de respiration** entre"

**Cela signifie**:
- Normalement: Pomodoro → Respiration → Pomodoro → Respiration
- Mais si temps_mort suivi de tâche planifiée: Temps_mort → Tâche planifiée (PAS de respiration)
- → L'alternance est CASSÉE temporairement ?

**Questions**:
- Après la tâche planifiée, l'alternance reprend-elle normalement ?
- Ou faut-il "sauter" la respiration qui aurait dû être entre temps_mort et tâche planifiée ?
- Exemple concret souhaité

**Réponse attendue**: OUI alternance cassée + exemple avec 5 tâches

---

## 6️⃣ RESPIRATIONS - Cycling et Duplicatas

### Question 6.1: Cycling quand nb Pomodoros >> nb Respirations

**Question**: Que se passe-t-il avec 81 Pomodoros et 3 respirations ?

**Calcul**:
- 81 Pomodoros
- 3 respirations: [R1, R2, R3]
- → Cycling: R1, R2, R3, R1, R2, R3... (27 fois chaque)

**Questions**:
- C'est bien ce comportement ?
- Les 3 respirations sont affichées 27 fois CHACUNE dans le planning final ?
- Pas de limite au nombre de fois qu'une respiration peut être réutilisée ?

**Réponse attendue**: OUI/NON + limite si applicable

---

### Question 6.2: Duplicatas intentionnels

**Question**: L'utilisateur peut drag 3 fois la même respiration dans l'onglet Pauses ?

**Scénario**:
- Utilisateur drag "Méditation (10 min)" 3 fois dans la liste sélectionnée
- → Liste sélectionnée: [Méditation, Méditation, Méditation]

**Questions**:
- C'est autorisé ?
- Si autorisé, quel est le comportement de cycling ?
  - Exemple: 6 Pomodoros + [Méd, Méd, Méd]
  - → Alternance: P1, Méd, P2, Méd, P3, Méd, P4, Méd, P5, Méd, P6, Méd ?
  - Ou: P1, Méd, P2, Méd, P3, Méd, P4, Méd, P5, Méd, P6, Méd (loop recommence: Méd) ?

**Réponse attendue**: Autorisé OUI/NON + comportement si autorisé

---

## 7️⃣ CÂLINS ET CLOPES - Insertion

### Question 7.1: Câlins - Pattern exact

**Question**: Le flux dit "1 câlin tous les 2 respirations, AVANT la respiration"

**Exemple** (ÉTAPE 6 du flux, ligne 183):
```
Pomodoro 1
Respiration 1
Pomodoro 2
Câlin ← Inséré AVANT respiration 2
Respiration 2
```

**MAIS**: "Tous les 2 respirations" signifie quoi exactement ?

**Interprétation A**:
- Compteur de respirations: 0
- Respiration 1 → compteur = 1 (pas de câlin)
- Respiration 2 → compteur = 2 (câlin AVANT)
- Respiration 3 → compteur = 3 (pas de câlin)
- Respiration 4 → compteur = 4 (câlin AVANT)

**Interprétation B**:
- Respiration 1 → pas de câlin
- Respiration 2 → câlin APRÈS (entre R2 et P3)
- Respiration 3 → pas de câlin
- Respiration 4 → câlin APRÈS

**Réponse du flux** (ligne 167): `if (respirationCount % 2 === 0)` → Interprétation A correcte

**Mais ligne 172 dit**: "Insère câlin AVANT cette respiration"

**CONFUSION**: Le câlin est inséré AVANT la 2ème respiration, ou APRÈS ?

**Exemple souhaité**:
```
P1 (index 0)
R1 (index 1) → compteur = 1
P2 (index 2)
<CÂLIN ICI (index 3) ?> OU <CÂLIN ICI (index 4) ?>
R2 (index 4 ou 3) → compteur = 2
```

**Réponse attendue**: Exemple avec indices exacts (0, 1, 2, 3...)

---

### Question 7.2: Clopes - Cumul exact

**Question**: Le flux dit "cumul TOUTES les tâches (Pomodoros + Respirations + Câlins)"

**Mais**: Les clopes elles-mêmes comptent-elles dans le cumul ?

**Scénario**:
- Intervalle clope = 120 min
- Planning: P(25) + R(10) + P(25) + R(10) + P(25) + R(10) + P(25) + R(10)
- Cumul après 4 Pomodoros + 4 Respirations = 100 + 40 = 140 min ≥ 120 min
- → Clope insérée (5 min)
- **Question**: Le cumul redémarre à 0 ou à 5 min (durée de la clope) ?

**Options**:
- A) Cumul = 0 après clope (clope ne compte pas)
- B) Cumul = 5 après clope (clope compte)

**Réponse du flux** (ligne 225): `cumulativeDuration = 0` → Option A correcte

**MAIS**: Que se passe-t-il si on insère un câlin juste après la clope ?
- Clope (5 min) → cumul = 0
- Câlin (10 min) → cumul = 10
- Respiration (5 min) → cumul = 15
- ...

**Est-ce correct ?**

**Réponse attendue**: OUI/NON + clarification si NON

---

### Question 7.3: Ordre d'insertion Câlins vs Clopes

**Question**: Si câlin ET clope doivent être insérés au même endroit, qui vient en premier ?

**Scénario**:
- Compteur respirations = 2 (câlin doit être inséré AVANT R2)
- Cumul durée = 120 min (clope doit être insérée)
- → Quelle séquence ?

**Option A**: P → Câlin → Clope → R
**Option B**: P → Clope → Câlin → R
**Option C**: Impossible (algorithme garantit qu'ils ne se chevauchent jamais)

**Réponse attendue**: [A/B/C] + explication

---

## 8️⃣ BACKEND vs FRONTEND - Responsabilités

### Question 8.1: Où se fait le calcul du planning ?

**Question**: Qui calcule le planning, le backend ou le frontend ?

**Architecture actuelle** (CLAUDE.md ligne 13):
> Backend: 100% de la logique de planning

**MAIS**: Le PLAN_REFONTE_V3.md propose des fonctions JavaScript frontend (`rebuildTimeline()`, `buildPomodoroList()`, etc.)

**CONFUSION**: Le calcul se fait-il:
- A) 100% backend (Python) → Frontend affiche seulement
- B) 100% frontend (JavaScript) → Backend stocke seulement
- C) Hybride (Frontend prépare, Backend finalise)

**Réponse attendue**: [A/B/C] + justification

---

### Question 8.2: Format d'échange API

**Question**: Quel est le format JSON échangé entre frontend et backend ?

**Supposé actuellement**:

**Frontend → Backend** (génération planning):
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

**Backend → Frontend** (planning généré):
```json
{
  "success": true,
  "planning": [
    {
      "date": "2025-11-05",
      "heure_debut": "14:00",
      "heure_fin": "14:25",
      "task_name": "Révision maths",
      "task_id": "TASK001",
      "type": "pomodoro",
      "duration_min": 25,
      "pomodoro_index": 1,
      "pomodoro_total": 3
    },
    ...
  ],
  "statistics": {
    "total_work_min": 300,
    "total_pause_min": 60,
    ...
  }
}
```

**Est-ce correct ?** Si non, donner le format exact.

**Réponse attendue**: Validation OUI/NON + format si NON

---

## 9️⃣ PERSISTANCE - Ce qui est sauvegardé

### Question 9.1: Quelles données persistent sur le serveur ?

**Liste supposée**:
1. `planning_state.json` - Date + sélections utilisateur (Pomodoro IDs, Respiration IDs)
2. `pinned_pauses.json` - IDs des pauses épinglées
3. `user_config.json` - Intervalle clopes
4. Fichiers CSV sources (LISTE_MERE, TACHES_RESPIRATOIRES, etc.)

**Questions**:
- Cette liste est-elle complète ?
- Manque-t-il quelque chose ?
- Le planning GÉNÉRÉ lui-même est-il sauvegardé ? (fichier `planned.csv` ?)

**Réponse attendue**: Liste complète des fichiers persistés

---

### Question 9.2: Synchronisation cross-device

**Question**: Si utilisateur ouvre l'app sur 2 navigateurs différents, que se passe-t-il ?

**Scénario**:
1. Navigateur A: Utilisateur sélectionne 3 Pomodoros, génère planning
2. → `planning_state.json` sauvegardé sur serveur
3. Navigateur B: Utilisateur ouvre la page
4. → Que voit-il ?

**Options**:
- A) Voit les mêmes 3 Pomodoros sélectionnés (state chargé depuis serveur)
- B) Voit une page vierge (state local seulement)
- C) Voit le dernier planning généré (CSV chargé)
- D) Autre ?

**Réponse attendue**: [A/B/C/D] + mécanisme de sync

---

## 🔟 EDGE CASES - Cas Particuliers

### Question 10.1: 0 Pomodoros sélectionnés

**Question**: Que se passe-t-il si utilisateur sélectionne 0 Pomodoros ?

**Options**:
- A) Erreur affichée ("Sélectionnez au moins 1 tâche")
- B) Planning vide généré
- C) Mode "Pauses seules" activé automatiquement (si respirations sélectionnées)
- D) Autre ?

**Réponse attendue**: [A/B/C/D]

---

### Question 10.2: 0 Respirations sélectionnées

**Question**: Déjà couvert dans le flux → Mode Focus (seulement Pomodoros)

**MAIS**: Les câlins et clopes sont-ils insérés quand même ?

**Scénario**:
- 5 Pomodoros (125 min)
- 0 Respirations
- Câlins activés
- Clopes activés (intervalle 120 min)

**Résultat attendu**:
```
P1 (0-25)
P2 (25-50)
P3 (50-75)
P4 (75-100)
P5 (100-125)
Clope (125-130) ← Inséré car cumul ≥ 120 min ?
```

**Ou**: Clopes NE SONT PAS insérés car algorithme nécessite respirations ?

**Réponse attendue**: Comportement exact avec exemple

---

### Question 10.3: Tous les créneaux occupés (temps_morts)

**Question**: Que se passe-t-il si TOUTE la journée est bloquée par des temps_morts ?

**Scénario**:
- Date: 2025-11-05
- planningStartTime: 10:00
- temps_morts: 00:00-06:30 (dodo), 12:00-13:00 (déjeuner), 18:00-24:00 (soirée)
- Créneaux libres: 06:30-12:00 (5h30), 13:00-18:00 (5h)
- Utilisateur sélectionne 20 Pomodoros (500 min = 8h20)

**Résultat attendu**:
- A) Tous les Pomodoros sont placés (débordent sur jour suivant)
- B) Seulement les Pomodoros qui tiennent dans les créneaux libres (10-12 Pomodoros)
- C) Erreur affichée ("Pas assez de temps libre")

**Flux dit** (ligne 155): "Le planning s'arrête à la fin du dernier Pomodoro"

**MAIS**: Cela signifie quoi si on manque de place ?
- Tous les Pomodoros sont placés quand même (ignorent limite jour) ?
- Ou seulement ceux qui tiennent ?

**Réponse attendue**: [A/B/C] + gestion débordement jour suivant

---

### Question 10.4: Intervalle clope = 0

**Question**: Que se passe-t-il si utilisateur entre intervalle = 0 ?

**Options**:
- A) Validation frontend ("Intervalle doit être > 0")
- B) Accepté, mais 0 clope insérée (division par zéro évitée)
- C) Une clope après CHAQUE tâche
- D) Autre ?

**Réponse attendue**: [A/B/C/D]

---

## 📊 RÉCAPITULATIF - Questions par Priorité

### Priorité CRITIQUE (bloque l'implémentation)

1. **Question 1.3**: Comportement exact du bouton "Envoyer vers planning"
2. **Question 2.2**: Workflow complet utilisateur (ordre des clics)
3. **Question 7.1**: Câlins - pattern exact (AVANT ou APRÈS ?)
4. **Question 8.1**: Backend vs Frontend - Qui calcule le planning ?
5. **Question 8.2**: Format JSON API exacte

### Priorité HAUTE (impacte l'architecture)

6. **Question 1.1**: Layout onglet Pauses (2 colonnes ou autre)
7. **Question 1.2**: Actions disponibles sur pauses sélectionnées
8. **Question 2.3**: Planning modifiable après génération ?
9. **Question 3.3**: Drag & drop dans planning généré ?
10. **Question 5.1**: Résolution conflit tâche planifiée + temps_mort

### Priorité MOYENNE (impacte l'UX)

11. **Question 1.4**: Quand sauvegarder pauses sélectionnées ?
12. **Question 1.5**: Comportement épinglage exact
13. **Question 3.2**: Format affichage ligne (toutes infos sur 1 ligne)
14. **Question 5.2**: Slot "Bientôt temps mort" affiché ?
15. **Question 9.2**: Synchronisation cross-device

### Priorité BASSE (edge cases)

16. **Question 4.1**: Support multi-jours
17. **Question 4.2**: Temps négatifs (temps_morts passés)
18. **Question 6.1**: Cycling illimité ?
19. **Question 10.2**: Clopes sans respirations ?
20. **Question 10.3**: Débordement jour suivant

---

## ✅ PROCHAINES ÉTAPES

1. **Utilisateur répond aux 5 questions CRITIQUES** → Permet de commencer PHASE 0-3
2. **Utilisateur répond aux 5 questions HAUTE** → Permet PHASE 4-7
3. **Utilisateur répond aux 5 questions MOYENNE** → Permet PHASE 8-12
4. **Utilisateur répond aux 5 questions BASSE** (optionnel) → Robustesse edge cases

**Objectif**: 0 ambiguïté avant d'écrire la première ligne de code

---

**Document créé le**: 2025-11-05
**Auteur**: Claude (Anthropic)
**Supervision**: Julio
**Statut**: En attente de réponses
