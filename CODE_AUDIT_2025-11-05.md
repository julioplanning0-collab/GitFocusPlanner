# Audit du Code - GitFocus Planner V2

**Date**: 2025-11-05
**Document de référence**: `REFONTE_V2_SUMMARY.md`
**Objectif**: Vérifier cohérence entre spécifications et implémentation

---

## ✅ POINTS CONFORMES

### 1. Architecture Backend-First
**Spécification** (lignes 23-30):
> Backend: 100% de la logique de planning (algorithme complet)

**Code actuel**: ✅ CONFORME
- `planning_generator.py` contient toute la logique
- Frontend envoie seulement les sélections
- Tests confirment que le backend génère le planning complet

---

### 2. Support respiration_ids avec duplicatas
**Spécification** (lignes 62-74):
> Variable `selectedRespirationIds` (peut contenir duplicatas)

**Code actuel**: ✅ CONFORME
- `gitfocus_v2.js:273` - `state.selectedRespirationIds.push(taskId)` permet duplicatas
- `planning_generator.py:105-113` - Préserve les duplicatas lors du chargement
- Alternance cycle à travers les IDs fournis

---

### 3. Calcul automatique start_time
**Spécification** (lignes 72):
> Fonction `calculateStartTime()`: now + 15min arrondi à 5

**Code actuel**: ✅ CONFORME
- `gitfocus_v2.js:683-705` - Implémentation exacte
- Arrondi au multiple de 5 supérieur
- Gestion overflow (58 → 00 heure suivante)

---

### 4. Phase 4 - Pauses Cigarettes
**Spécification** (lignes 104-118):
> Nouvelle fonction `_insert_clopes()` avec compteur cumulatif

**Code actuel**: ✅ CONFORME
- `planning_generator.py:656-713` - Fonction complète
- Compteur cumulé de TOUS les slots
- Insertion à intervalle configurable
- Réajustement automatique des heures

---

### 5. Phase 4 - Câlins
**Spécification** (lignes 119-130):
> Logique intégrée dans `_generate_base_planning()`, 1 tous les 2 respirations

**Code actuel**: ✅ CONFORME
- `planning_generator.py:556-592` - Compteur respiration_count
- Insertion AVANT la respiration quand `count % 2 == 0`
- Type de slot: 'calin'

---

### 6. Phase 4 - Pauses Consécutives
**Spécification** (lignes 131-140):
> Appel conditionnel de `repair_consecutive_work_tasks()`

**Code actuel**: ✅ CONFORME
- `planning_generator.py:228-232` - Logique conditionnelle exacte
- Skip réparation si `allow_consecutive_pauses=True`

---

### 7. Types de slots générés
**Spécification** (lignes 151-158):
> 6 types: pomodoro, respiration, clope, calin, recurrent, planned

**Code actuel**: ✅ CONFORME
- Tous les types sont générés correctement
- Distinction claire dans le code

---

### 8. Pipeline de génération (12 étapes)
**Spécification** (lignes 213-239):
> Séquence précise des opérations

**Code actuel**: ✅ CONFORME
- Toutes les étapes présentes dans le bon ordre
- Logs DEBUG pour chaque étape majeure

---

## ⚠️ POINTS NON-CONFORMES

### 1. ❌ CRITIQUE: Fallback vers recurrent tasks désactivé

**Spécification** (lignes 81-88):
```
- ✅ Logique chargement tâches respiratoires:
  - Préserve duplicatas dans `respiration_ids`
  - Cycle à travers IDs fournis pour alternance
- ✅ Détection automatique type de pause:
  - Si `respiration_ids` fourni → type='respiration'
  - Sinon → fallback vers recurrent tasks avec scoring  ← CRUCIAL
```

**Code actuel** (`planning_generator.py:160-167`):
```python
if selected_respiration:
    logger.info("🔍 DEBUG: Using manually selected respiration tasks for alternance")
    pause_tasks = selected_respiration
    recurrent_task_scores = []  # No scoring needed
else:
    logger.info("🔍 DEBUG: No respiration tasks selected, planning will contain ONLY Pomodoros (no pauses)")
    pause_tasks = []  # ❌ ERREUR: Devrait fallback vers recurrent tasks
    recurrent_task_scores = []
```

**Problème**:
- La spec dit: "Sinon → fallback vers recurrent tasks avec scoring"
- Le code actuel: `pause_tasks = []` (pas de fallback)
- Résultat: Quand aucune respiration sélectionnée → planning sans alternance (SEULEMENT Pomodoros)

**Historique de ce changement**:
- Commit `4cd7b73` (2025-11-05): "fix: remove automatic recurrent task insertion, user must manually select pause tasks"
- Raison: Réponse à demande utilisateur "pas d'insertion automatique"
- Impact: Modification du comportement par rapport à la spec originale

**État actuel**:
- ✅ Conforme à la demande utilisateur récente
- ❌ Non-conforme à la spécification REFONTE_V2_SUMMARY.md

---

## 🔍 ANALYSE DÉTAILLÉE: Logique d'Alternance

### Comportement Spécifié (Original)

**Scénario 1**: Utilisateur sélectionne 3 Pomodoros + 2 Respirations
- Résultat: Alternance Pomodoro → Respiration
- Type de pause: 'respiration'

**Scénario 2**: Utilisateur sélectionne 3 Pomodoros + 0 Respirations
- Résultat: Alternance Pomodoro → Recurrent (sélection intelligente top N)
- Type de pause: 'recurrent'
- Scoring basé sur `smart_scorer.py`

**Scénario 3**: Utilisateur active "Autoriser Pauses Consécutives"
- Résultat: Respiration → Respiration autorisée (pas de réparation)

### Comportement Actuel (Post-commit 4cd7b73)

**Scénario 1**: Utilisateur sélectionne 3 Pomodoros + 2 Respirations
- Résultat: ✅ Alternance Pomodoro → Respiration (CONFORME)

**Scénario 2**: Utilisateur sélectionne 3 Pomodoros + 0 Respirations
- Résultat: ❌ SEULEMENT Pomodoros (pas d'alternance, pas de pauses)
- Type de pause: Aucun
- Scoring: Non utilisé

**Scénario 3**: Utilisateur active "Autoriser Pauses Consécutives"
- Résultat: ✅ N/A si pas de respirations sélectionnées

---

## 📊 Conformité Globale

| Catégorie | Points vérifiés | Conformes | Non-conformes | Score |
|-----------|----------------|-----------|---------------|-------|
| Architecture | 1 | 1 | 0 | 100% |
| Phase 3 (respiration_ids) | 2 | 1 | 1 | 50% |
| Phase 4 (advanced options) | 3 | 3 | 0 | 100% |
| Types de slots | 1 | 1 | 0 | 100% |
| Pipeline génération | 1 | 1 | 0 | 100% |
| **TOTAL** | **8** | **7** | **1** | **87.5%** |

---

## 🎯 RECOMMANDATIONS

### Option A: Mettre à jour la spécification (Recommandé)

**Action**: Modifier `REFONTE_V2_SUMMARY.md` pour refléter le nouveau comportement
- Ligne 83-88: Supprimer mention du "fallback vers recurrent tasks"
- Ajouter: "Si aucune respiration sélectionnée → planning SEULEMENT Pomodoros (mode Focus)"
- Rationale: Comportement actuel plus intuitif (user a le contrôle total)

**Avantages**:
- Aucun changement de code nécessaire
- Comportement actuel plus simple et prévisible
- User contrôle explicite (pas de "magie")

**Inconvénients**:
- Modification de la spec après implémentation (pas idéal)
- Perte d'une fonctionnalité (alternance automatique intelligente)

---

### Option B: Restaurer le fallback vers recurrent tasks

**Action**: Modifier `planning_generator.py` pour restaurer le comportement spécifié
```python
else:
    logger.info("🔍 DEBUG: No respiration tasks provided, using intelligent recurrent task selection")
    from backend.planning_engine.smart_scorer import score_all_recurrent_tasks

    scored_tasks = score_all_recurrent_tasks(all_recurrent, date, planning_history, done_history)

    # Select top N
    top_scored = scored_tasks[:max_recurrent_tasks]
    pause_tasks = [st['task'] for st in top_scored]
    recurrent_task_scores = [
        {'task_id': st['task']['id'], 'task_name': st['task']['name'], 'score': st['score']}
        for st in top_scored
    ]

    logger.info(f"Selected top {len(pause_tasks)} recurrent tasks (scores: {[st['score'] for st in top_scored]})")
```

**Avantages**:
- Conforme à la spec originale
- Fonctionnalité intelligente (scoring automatique)
- Alternance garantie (pas de planning 100% travail)

**Inconvénients**:
- User perd le contrôle (insertion automatique)
- Peut surprendre l'utilisateur (tâches non demandées)
- Nécessite que `smart_scorer.py` existe et fonctionne

---

### Option C: Ajouter un paramètre de configuration

**Action**: Ajouter `auto_insert_pauses: bool = True` dans l'API
```python
def generate_planning_auto(
    ...
    auto_insert_pauses: bool = True  # 🆕 Nouveau paramètre
):
    if selected_respiration:
        pause_tasks = selected_respiration
    else:
        if auto_insert_pauses:
            # Fallback vers recurrent tasks (comportement original)
            scored_tasks = score_all_recurrent_tasks(...)
            pause_tasks = [st['task'] for st in top_scored]
        else:
            # Mode Focus (comportement actuel)
            pause_tasks = []
```

**Avantages**:
- Meilleur des deux mondes
- User peut choisir le comportement
- Rétro-compatibilité (défaut = True)

**Inconvénients**:
- Complexité accrue (1 paramètre de plus)
- UI doit exposer ce choix (checkbox supplémentaire)

---

## 🔧 AUTRES OBSERVATIONS

### 1. Modules référencés mais non vérifiés

**`smart_scorer.py`**:
- Référencé dans la spec (ligne 166)
- Utilisé pour scoring intelligent des recurrent tasks
- Non audité dans ce rapport (assume qu'il existe et fonctionne)

**`task_integrator.py`**:
- Référencé dans la spec (ligne 274)
- Contient `repair_consecutive_work_tasks()`
- Non audité dans ce rapport

---

### 2. Migration respirations → recurrents

**Observation**: Les tâches respiratoires ont été fusionnées dans `TACHES_RECURRENTES.v2.csv`
- Commit: `8f2a995` (2025-11-05)
- Impact: Fichier `TACHES_RESPIRATOIRES.v2.csv` supprimé
- État: ⚠️ Spec ne mentionne pas cette migration

**Recommandation**: Mettre à jour `REFONTE_V2_SUMMARY.md` avec section "Migration 2025-11-05"

---

### 3. Système d'onglets

**Observation**: Interface à onglets créée pour séparer les types de tâches
- Commit: `59ac245` (2025-11-05)
- Impact: Tâches récurrentes isolées dans onglet dédié
- État: ⚠️ Spec ne mentionne pas cette fonctionnalité

**Recommandation**: Ajouter section "UI Improvements" dans la spec

---

## ✅ CONCLUSION

**Conformité globale**: 87.5% (7/8 points conformes)

**Point critique non-conforme**: Fallback automatique vers recurrent tasks désactivé

**Recommandation**: **Option A** (Mettre à jour la spec)
- Raison: Comportement actuel plus intuitif et voulu par l'utilisateur
- Action: Documenter changement dans spec + ajouter section migrations

**Actions immédiates**:
1. Décider: Option A, B, ou C
2. Si Option A: Mettre à jour `REFONTE_V2_SUMMARY.md`
3. Si Option B: Restaurer code commit `4cd7b73`
4. Si Option C: Implémenter nouveau paramètre `auto_insert_pauses`

---

**Auditeur**: Claude (Anthropic)
**Date de l'audit**: 2025-11-05
**Version du code**: commit `59ac245`
**Version de la spec**: REFONTE_V2_SUMMARY.md (dernière MAJ 2025-11-04)
