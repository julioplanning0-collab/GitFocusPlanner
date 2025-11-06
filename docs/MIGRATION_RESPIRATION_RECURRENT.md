# Migration: Tâches Respiratoires → Tâches Récurrentes

**Date**: 2025-11-05
**Commit**: 8f2a995

---

## ✅ ÉTAPE 1: Migration des Données (TERMINÉ)

### Ce qui a été fait:

1. **Script de migration créé**: `migrate_respiration_to_recurrent.py`
   - Lit TACHES_RESPIRATOIRES.v2.csv
   - Convertit au format TACHES_RECURRENTES.v2.csv
   - Ajoute les 9 tâches au fichier récurrent
   - Backup créé: `TACHES_RESPIRATOIRES.v2.csv.backup`
   - Fichier original supprimé

2. **Résultat**:
   - 9 tâches respiratoires converties
   - Fichier TACHES_RECURRENTES.v2.csv: maintenant 97 tâches (88 + 9)
   - IDs préservés: R010, R018, R019, R020, R021, R022, R023, R028, R029

3. **Mapping appliqué**:
   ```
   REPEAT_INTERVAL_MIN → RECURRENCE_TYPE + RECURRENCE_INTERVAL
   >= 10080 min (7 jours) → weekly, 7
   >= 1440 min (1 jour)   → daily, 1
   < 1440 min             → daily, 1
   ```

---

## 🔄 ÉTAPE 2: Refactoring du Code (À FAIRE)

Les anciennes "tâches respiratoires" sont maintenant un sous-ensemble des tâches récurrentes.
**Nouveau concept**: Les tâches récurrentes avec `DURATION_MIN <= 20` sont des **pause tasks** (respirations).

### Fichiers à modifier:

#### 1. **backend/planning_engine/data_loader.py**
- ❌ Supprimer: `load_respiration_tasks()`
- ✅ Modifier: `load_recurrent_tasks()` pour accepter un filtre optionnel `pause_only=False`
  ```python
  def load_recurrent_tasks(csv_path: Path, active_only: bool = False, pause_only: bool = False) -> List[Dict]:
      """
      Load recurrent tasks.

      Args:
          pause_only: If True, only return tasks with DURATION_MIN <= 20 (pause tasks)
      """
      tasks = _safe_read_csv(csv_path)

      if active_only:
          tasks = [t for t in tasks if _safe_int(t.get('IS_ACTIVE', '0')) == 1]

      if pause_only:
          tasks = [t for t in tasks if _safe_int(t.get('DURATION_MIN', '0')) <= 20]

      return tasks
  ```

#### 2. **backend/planning_engine/data_writer.py**
- ❌ Supprimer: `increment_respiration_export_count()` (si existe)
- ✅ Créer: `increment_recurrent_export_count()` (générique pour toutes les tâches récurrentes)

#### 3. **backend/planning_engine/planning_generator.py**
- ✅ Modifier: Ligne 102-116 (chargement respiration tasks)
  ```python
  # AVANT:
  if respiration_ids:
      all_respiration = load_respiration_tasks(...)
      selected_respiration = [...]

  # APRÈS:
  if respiration_ids:
      all_pauses = load_recurrent_tasks(..., active_only=True, pause_only=True)
      selected_pauses = [...]
  ```

- ✅ Renommer les variables:
  - `selected_respiration` → `selected_pauses`
  - `respiration_ids` → `pause_ids` (ou garder `respiration_ids` pour rétro-compatibilité API)

#### 4. **webapp/api/routes_gitfocus_v2.py**

**Option A: Garder l'API actuelle (rétro-compatibilité)**
- ✅ Modifier: `GET /tasks/respiration` pour charger depuis `TACHES_RECURRENTES.v2.csv` avec filtre `pause_only=True`
  ```python
  @gitfocus_bp.route('/tasks/respiration', methods=['GET'])
  def get_respiration_tasks():
      """Get pause tasks (recurrent tasks with duration <= 20 min)."""
      try:
          tasks = load_recurrent_tasks(
              Config.DATA_DIR / 'TACHES_RECURRENTES.v2.csv',
              active_only=True,
              pause_only=True
          )
          return jsonify({'success': True, 'tasks': tasks, 'count': len(tasks)})
      except Exception as e:
          return jsonify({'success': False, 'error': str(e)}), 500
  ```

**Option B: Nouvelle API (recommandé)**
- ✅ Ajouter: `GET /tasks/recurrent?pause_only=true`
- ⚠️ Marquer comme déprécié: `GET /tasks/respiration` (garder pour rétro-compatibilité)

#### 5. **webapp/static/js/gitfocus_v2.js**

**Si Option A (garder API actuelle)**:
- ✅ Pas de changement nécessaire (l'endpoint `/tasks/respiration` fonctionne toujours)

**Si Option B (nouvelle API)**:
- ✅ Modifier: Ligne 74-83 (`loadRespirationTasks()`)
  ```javascript
  async function loadRespirationTasks() {
      try {
          const data = await apiCall('/tasks/recurrent?pause_only=true');
          state.respirationTasks = data.tasks || [];
          renderRespirationTasks();
      } catch (error) {
          console.error('Failed to load pause tasks:', error);
          state.respirationTasks = [];
          renderRespirationTasks();
      }
  }
  ```

#### 6. **webapp/templates/gitfocus_v2.html**

**Option 1: Garder l'interface actuelle**
- Aucun changement (section "Tâches Respiratoires" reste)

**Option 2: Renommer la section**
- ✅ Modifier: Ligne 58-73
  ```html
  <h3>🟢 Tâches de Pause (Courtes)</h3>
  <span class="badge badge-info">Cliquez pour ajouter (duplicatas autorisés)</span>
  ```

---

## 🎯 ÉTAPE 3: Tests (À FAIRE)

### Tests à exécuter:

1. **Test de chargement**:
   ```bash
   curl http://localhost:5000/api/v2/gitfocus/tasks/respiration
   # Doit retourner les 9 anciennes tâches respiratoires (R010-R029)
   ```

2. **Test de génération de planning**:
   ```bash
   curl -X POST http://localhost:5000/api/v2/gitfocus/planning/generate-auto \
        -H "Content-Type: application/json" \
        -d '{
          "date": "2025-11-06",
          "pomodoro_task_ids": ["1", "2"],
          "respiration_task_ids": ["R010", "R018", "R019"]
        }'
   # Doit générer un planning avec les 3 pauses sélectionnées
   ```

3. **Test de l'interface**:
   - Ouvrir http://localhost:5000/api/v2/gitfocus/interface
   - Section "Tâches Respiratoires" doit afficher 9 tâches
   - Sélectionner des tâches et générer planning → Doit fonctionner

---

## 🔍 VÉRIFICATIONS CRITIQUES

### Fichiers CSV à vérifier:

1. **TACHES_RECURRENTES.v2.csv**:
   ```bash
   # Vérifier que les 9 tâches R010-R029 sont présentes
   grep -E "^\"R0(10|18|19|20|21|22|23|28|29)\"" prod_data/TACHES_RECURRENTES.v2.csv
   ```

2. **TACHES_RESPIRATOIRES.v2.csv**:
   ```bash
   # Vérifier que le fichier n'existe plus
   ls prod_data/TACHES_RESPIRATOIRES.v2.csv
   # Résultat attendu: "Le fichier spécifié est introuvable"
   ```

3. **Backup**:
   ```bash
   # Vérifier que le backup existe
   ls prod_data/TACHES_RESPIRATOIRES.v2.csv.backup
   # Résultat attendu: fichier existe
   ```

### Endpoints API à tester:

- `GET /tasks/respiration` → Doit retourner les 9 tâches de pause
- `GET /tasks/recurrent` → Doit retourner 97 tâches
- `GET /tasks/recurrent?pause_only=true` → Doit retourner 9 tâches (si implémenté)

---

## 📋 CHECKLIST DE MIGRATION

- [x] **Données**: Merger CSV files
- [x] **Backup**: Créer backup respiration file
- [x] **Commit**: Commit data migration
- [ ] **Backend**: Modifier data_loader.py
- [ ] **Backend**: Modifier planning_generator.py
- [ ] **API**: Modifier routes_gitfocus_v2.py
- [ ] **Frontend**: Tester interface (pas de changement nécessaire si Option A)
- [ ] **Tests**: Exécuter tests de non-régression
- [ ] **Commit**: Commit code refactoring
- [ ] **Documentation**: Mettre à jour CLAUDE.md

---

## 💡 RECOMMANDATION

**Option recommandée**: **Option A (Garder API actuelle)**

**Pourquoi**:
1. Rétro-compatibilité totale avec frontend existant
2. Aucun changement nécessaire dans JavaScript/HTML
3. L'endpoint `/tasks/respiration` reste fonctionnel (charge depuis recurrent avec filtre)
4. Moins de risque de régression
5. L'utilisateur ne voit aucune différence

**Implémentation minimale**:
- Modifier seulement `data_loader.py` et `routes_gitfocus_v2.py`
- Garder tout le reste identique
- Tests minimaux nécessaires

---

## 🚨 POINTS D'ATTENTION

1. **Types de tâches dans le planning**:
   - Les anciennes "respiration" tasks doivent toujours avoir `type='respiration'` dans le planning
   - Même si elles viennent du fichier recurrent
   - Distinction: `type='respiration'` (pause sélectionnée) vs `type='recurrent'` (tâche ménagère/etc.)

2. **ID Format**:
   - Les IDs commençant par "R0" (R010-R029) sont des pauses
   - Les IDs commençant par "REC" (REC001-REC090) sont des récurrentes classiques
   - Cette distinction peut être utilisée pour le filtrage

3. **Duration**:
   - Pauses: `DURATION_MIN <= 20`
   - Récurrentes classiques: `DURATION_MIN >= 5` (généralement 5 min)
   - Utiliser cette distinction pour le filtre `pause_only`

---

## 📝 COMMIT MESSAGES SUGGÉRÉS

```bash
# Prochains commits:
git commit -m "refactor: merge respiration tasks into recurrent system (backend)"
git commit -m "refactor: update API to load respiration from recurrent file"
git commit -m "test: add tests for merged respiration/recurrent tasks"
git commit -m "docs: update CLAUDE.md with unified task system"
```

---

**Status actuel**: ✅ ÉTAPE 1 terminée, prêt pour ÉTAPE 2
**Prochaine action**: Modifier `data_loader.py` pour ajouter `pause_only` filter
