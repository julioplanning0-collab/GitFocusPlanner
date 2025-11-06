# 🚀 DÉMARRAGE RAPIDE - GitFocus Planner V2

## ✅ Application Complète Créée!

**17 fichiers** créés (Backend + API + Interface Web)
- **Backend**: 8 modules Python (3,850+ lignes)
- **API REST**: 28 endpoints
- **Interface Web**: HTML + CSS + JavaScript

---

## 📋 Prérequis Vérifiés

✅ Structure backend complète
✅ API REST fonctionnelle
✅ Interface web responsive
✅ Système d'apprentissage intelligent
✅ Documentation complète

---

## 🎯 Démarrage en 3 Étapes

### 1. Lancement Automatique (RECOMMANDÉ)

**Méthode A - PowerShell (Meilleure expérience):**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

Le script PowerShell:
- ✅ Vérifie Python et tous les fichiers CSV
- ✅ Libère le port 5000 automatiquement
- ✅ Démarre le serveur Flask
- ✅ Vérifie que le serveur répond
- ✅ **Ouvre automatiquement le navigateur**
- ✅ Messages colorés et clairs

**Méthode B - Batch Windows (Alternative):**
```batch
scripts\start.bat
```

**Méthode C - Lancement racine (Simple):**

Double-cliquez sur `LANCEMENT.bat` à la racine du projet.

### 2. Lancement Manuel

**Option A - Direct:**
```bash
python -m webapp.server
```

**Option B - Avec vérification préalable:**
```bash
# Vérifier le système d'abord
python scripts\verify.py

# Puis démarrer
python -m webapp.server
```

### 3. Accéder à l'interface

Ouvrir dans le navigateur:
- **Interface Web**: http://localhost:5000/api/v2/gitfocus/interface
- **Health Check**: http://localhost:5000/health
- **Page d'accueil**: http://localhost:5000/

---

## 🧪 Test Rapide API

```bash
# Health check
curl http://localhost:5000/health

# Lister tâches Pomodoro
curl http://localhost:5000/api/v2/gitfocus/tasks/pomodoro

# Lister tâches récurrentes (actives)
curl "http://localhost:5000/api/v2/gitfocus/tasks/recurrent?active_only=true"

# Générer planning intelligent
curl -X POST http://localhost:5000/api/v2/gitfocus/planning/generate-auto \
  -H "Content-Type: application/json" \
  -d "{\"date\":\"2025-10-30\",\"pomodoro_task_ids\":[\"1\",\"2\"],\"max_recurrent_tasks\":10}"

# Stats historique apprentissage
curl http://localhost:5000/api/v2/gitfocus/stats/history
```

---

## 📊 Workflow Interface Web

1. **Ouvrir** http://localhost:5000/api/v2/gitfocus/interface

2. **Sélectionner** date (défaut = aujourd'hui)

3. **Cocher** 2-3 tâches Pomodoro (travail)

4. **Cliquer** "⚡ Générer Planning Intelligent"
   - Système sélectionne automatiquement top 10 tâches récurrentes
   - Affiche scores transparents (0-100 points)
   - Génère planning avec alternance stricte

5. **Vérifier** planning généré
   - 🔴 Pomodoro (travail)
   - 🟣 Récurrentes (pauses intelligentes)
   - Statistiques affichées

6. **Exporter** CSV
   - Écrit `planned.csv`
   - Enregistre historique pour apprentissage
   - Android app peut lire le fichier

7. **Consulter stats** (bouton 📊)
   - Voir nombre de placements enregistrés
   - Comprendre l'apprentissage

---

## 🆕 Système d'Apprentissage

### Comment ça marche ?

**Au fil du temps, le système apprend quelles tâches récurrentes vous planifiez à quelles heures.**

#### Scoring 4 Critères (0-100 points)
1. **50%** Récurrence DUE - Urgence (tâches en retard prioritaires)
2. **20%** Fréquence jour semaine - Habitudes (lundi → arrosage plantes)
3. **15%** Fréquence globale - Popularité (tâches souvent utilisées)
4. **15%** Récence - Actualité (tâches récentes pertinentes)

#### Évolution

- **Mois 1** → Scoring basé surtout sur urgence
- **Mois 2** → Détection patterns simples
- **Mois 6** → Patterns clairs (ex: "Arroser plantes" → 80% lundi 08:00)
- **Année 1+** → Système très précis, adapté à vos habitudes

**Fichier historique**: `prod_data/planning_placements_history.csv` (append-only, JAMAIS supprimer)

---

## 📁 Structure Projet

```
GitfocusPlanner/
├── backend/planning_engine/   # 8 modules (scoring, data, slots...)
├── webapp/                     # Flask app + API + templates
├── prod_data/                  # CSV files (données)
├── scripts/                    # Start/stop scripts
├── README.md                   # Documentation principale
├── SPECIFICATIONS_COMPLETES_V2.md  # Specs détaillées
├── CLAUDE.md                   # Bonnes pratiques
└── DEMARRAGE_RAPIDE.md        # Ce fichier
```

---

## ⚙️ Configuration (Optionnelle)

Variables d'environnement:

```bash
set DATA_DIR=C:\...\prod_data    # Chemin données CSV
set HOST=0.0.0.0                  # Hôte serveur
set PORT=5000                     # Port serveur
set DEBUG=True                    # Mode debug
set LOG_LEVEL=INFO                # Logs (DEBUG/INFO/WARNING/ERROR)
```

---

## ❌ Problèmes Courants

### Port 5000 déjà utilisé
```bash
# Windows
netstat -ano | findstr :5000
taskkill /F /PID <PID>
```

### Fichiers CSV manquants
```
RuntimeError: Missing required CSV files: [...]
```
→ Vérifier que tous les fichiers CSV existent dans `prod_data/`

### Encodage CSV incorrect
```
UnicodeDecodeError: 'utf-8' codec...
```
→ Le système re-encode automatiquement depuis latin-1 vers UTF-8

### Import Error
```
ModuleNotFoundError: No module named 'backend'
```
→ Lancer depuis la racine du projet: `python -m webapp.server`

---

## 📖 Documentation Complète

- **README.md** - Vue d'ensemble + architecture
- **SPECIFICATIONS_COMPLETES_V2.md** - Specs détaillées (2050 lignes)
- **CLAUDE.md** - Bonnes pratiques développement

---

## 🎁 Prochaines Améliorations (Optionnelles)

- [ ] Interface drag & drop (SortableJS) pour réorganiser planning
- [ ] Colonnes contextuelles (MOOD, ENERGY, WEATHER)
- [ ] Visualisation graphique statistiques apprentissage
- [ ] Tests unitaires complets
- [ ] Déploiement Docker

---

## ✅ Checklist Démarrage

- [ ] Tous les fichiers CSV présents dans `prod_data/`
- [ ] Serveur démarre sans erreur
- [ ] Health check répond (http://localhost:5000/health)
- [ ] Interface web accessible
- [ ] Tâches Pomodoro chargées
- [ ] Planning généré avec succès
- [ ] Export CSV fonctionne
- [ ] Historique enregistré (`planning_placements_history.csv`)

---

**🚀 L'application est prête! Bon planning intelligent!**

**Questions ou problèmes?**
- Consulter CLAUDE.md pour bonnes pratiques
- Consulter SPECIFICATIONS_COMPLETES_V2.md pour détails techniques
