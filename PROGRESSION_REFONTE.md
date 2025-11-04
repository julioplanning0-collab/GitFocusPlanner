# Progression Refonte Planning V2

## 📅 Date: 2025-11-04

---

## ✅ Phase 0: Préparation (COMPLÈTE)

### Branches Git
- ✅ `backup-before-refonte-planning`: Sauvegarde complète (92 fichiers)
- ✅ `refonte-planning-v2`: Branche de travail active

### Tests de Régression
- ✅ **test_api_refonte.py**: 10/10 tests passent ⭐
  - Health endpoint OK
  - GET Pomodoro tasks OK (structure validée)
  - GET Respiration tasks OK (tri par popularité validé)
  - GET Recurrent tasks OK (filtre active_only validé)
  - Fichiers de données présents OK

- ⚠️ **test_planning_refonte.py**: 11/17 tests passent (Selenium)
  - Échecs attendus: IDs HTML pas encore ajustés
  - Base de référence établie

**Commit**: `backup-before-refonte-planning` (initial state)

---

## ✅ Phase 1: Nettoyage Code Obsolète (COMPLÈTE)

### Fonctions Supprimées
1. ✅ **addRecurrentTaskToPlanning()** (112 lignes)
   - Raison: Gestion des tâches récurrentes déplacée vers backend
   - Impact: Simplification du code client

2. ✅ **repairAlternationViolations()** (77 lignes)
   - Raison: Alternance Pomodoro/Pause gérée par backend
   - Impact: Suppression de la logique complexe de réparation

3. ✅ **recalculateTimesAfterReorder()** (29 lignes)
   - Raison: Calcul des heures géré par backend
   - Impact: Backend retourne des heures absolues calculées

### Modifications Associées
- ✅ `handleDrop()`: Appels commentés, TODO ajouté pour appel backend
- ✅ `handleDeleteSlot()`: Appel commenté, TODO ajouté pour appel backend

### Résultats
- **Lignes supprimées**: ~220 lignes
- **Fichier gitfocus_v2.js**: 872 → 760 lignes

**Commit**: `c891313` - "refactor: Phase 0 et 1 - Tests de régression + Nettoyage code obsolète"

---

## ✅ Phase 3: Support respiration_ids + start_time (COMPLÈTE)

### Modifications Frontend (gitfocus_v2.js)
- ✅ Ajouté `planningStartTime` (HH:MM format)
- ✅ Ajouté `respirationTasks` (liste disponible)
- ✅ Ajouté `selectedRespirationIds` (peut contenir duplicatas)
- ✅ Créé `loadRespirationTasks()`: Charge tâches respiratoires depuis API
- ✅ Créé `renderRespirationTasks()`: Affichage avec compteurs (x2, x3...)
- ✅ Créé `toggleRespirationSelection()`: Sélection avec duplicatas
- ✅ Créé `calculateStartTime()`: now + 15min arrondi à 5
- ✅ Modifié `generatePlanning()` pour envoyer `start_time` et `respiration_task_ids`

### Modifications Backend (planning_generator.py)
- ✅ Modifié signature `generate_planning_auto()`:
  - Ajouté paramètre `start_time: Optional[str]`
  - Ajouté paramètre `respiration_ids: Optional[List[str]]`
- ✅ Implémenté logique de chargement des tâches respiratoires
  - Préserve les duplicatas dans `respiration_ids`
  - Cycle à travers les IDs fournis pour l'alternance
- ✅ Implémenté détection automatique du type de pause:
  - Si `respiration_ids` fourni → type='respiration'
  - Sinon → fallback vers recurrent tasks avec scoring
- ✅ Modifié `_generate_base_planning()`:
  - Renommé paramètre `recurrent_tasks` → `pause_tasks`
  - Détection automatique du type (respiration vs recurrent)
  - Utilise le type détecté dans les slots générés

### Tests Effectués
- ✅ Test avec `respiration_ids` → alternance Pomodoro/Respiration
- ✅ Test sans `respiration_ids` → fallback vers recurrent tasks
- ✅ Vérification des duplicatas → même ID apparaît plusieurs fois
- ✅ Vérification des types → 'respiration' vs 'recurrent' vs 'pause'

**Résultat**: Phase 3 100% fonctionnelle ✅

---

## 📋 Phase 4: Nouvelles Fonctionnalités (PLANIFIÉ)

### Fonctionnalités à Implémenter
1. **Clopes** (cigarette breaks)
   - Intervalle configurable (défaut: 120 min)
   - Compter TOUTES les durées (Pomodoros + Respirations + Câlins)
   - Insertion automatique dans le planning

2. **Câlins**
   - 1 câlin tous les 2 respirations
   - Insertion dans la liste alternée

3. **Pauses Consécutives**
   - Mode optionnel (checkbox)
   - Permet d'avoir plusieurs pauses sans Pomodoros entre elles

### API Changes
- Ajouter paramètres optionnels:
  - `enable_clopes`: boolean
  - `clopes_interval_min`: number (défaut 120)
  - `enable_calins`: boolean
  - `pauses_consecutives`: boolean

---

## 🎯 Phase 5: Tests (PLANIFIÉ)

### Tests à Exécuter
- [ ] Re-run `test_api_refonte.py` (doit toujours passer)
- [ ] Créer nouveaux tests pour respirations
- [ ] Tester génération planning avec respirations manuelles
- [ ] Tester start_time calculation
- [ ] Tests d'intégration backend

---

## 📝 Phase 6: Documentation (PLANIFIÉ)

### Documents à Créer/Mettre à Jour
- [ ] `CLAUDE.md`: Mettre à jour architecture
- [ ] `SPECIFICATIONS_COMPLETES_V2.md`: Documenter nouveau flux
- [ ] README: Instructions d'utilisation
- [ ] Commit message détaillé final

---

## 📊 Métriques

### Code Nettoyé
- Lignes supprimées: ~220
- Fonctions obsolètes supprimées: 3
- Fichier réduit de: 13% (872 → 760 lignes)

### Tests
- Tests API passant: 10/10 (100%)
- Tests Selenium: 11/17 (65%, échecs attendus)

### Commits
- Total commits sur branche: 1
- Derniercommit: `c891313`

---

## 🔧 Architecture Cible

### Frontend (Client-Side)
**Responsabilités**:
- Affichage UI
- Sélection des tâches (Pomodoro, Respirations)
- Envoi des sélections au backend
- Affichage du planning retourné
- Drag&drop (déclenchera appel backend pour régénérer)

**Ne fait PLUS**:
- ❌ Calculs de planning
- ❌ Gestion d'alternance
- ❌ Calculs de temps
- ❌ Intégration d'obstacles (temps_morts)

### Backend (Server-Side)
**Responsabilités**:
- Génération complète du planning
- Alternance Pomodoro/Respiration
- Insertion câlins (1/2 respirations)
- Insertion clopes (intervalle configurable)
- Gestion temps_morts
- Intégration tâches planifiées
- Calcul des heures absolues
- Retour planning avec statistiques

**Algorithme** (12 étapes selon flux utilisateur):
1. Calculer heure de départ (now + 15min arrondi à 5)
2. Construire liste alternée Pomodoros/Respirations
3. Ajouter câlins (1 tous les 2 respirations)
4. Ajouter clopes (intervalle configurable)
5. Charger temps_morts et tâches planifiées
6. Convertir en timeline avec insertion d'obstacles
7. Gérer "Bientôt temps mort" (gaps)
8. Gérer collisions tâches planifiées
9. Arrêter au dernier Pomodoro
10-12. Calculs finaux et statistiques

---

## 🚀 Prochaines Actions Immédiates

1. **Créer `renderRespirationTasks()`**
2. **Ajouter section HTML pour respirations**
3. **Implémenter `calculateStartTime()`**
4. **Modifier backend pour accepter nouveaux paramètres**
5. **Tester le flux complet**

---

**Dernière mise à jour**: 2025-11-04 18:50 UTC
**Branche active**: `refonte-planning-v2`
**Status**: Phase 3 en cours (40% complété)
