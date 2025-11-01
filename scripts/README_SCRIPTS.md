# 🛠️ Scripts GitFocus Planner V2

Ce dossier contient les scripts de gestion du serveur.

---

## 📜 Scripts Disponibles

### ⚡ start.ps1 (RECOMMANDÉ)

**Script PowerShell complet et robuste**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

**Fonctionnalités**:
- ✅ Vérification Python (version affichée)
- ✅ Vérification de tous les fichiers CSV requis
- ✅ Arrêt automatique des processus Flask existants
- ✅ Vérification système complète (via verify.py)
- ✅ Démarrage serveur dans nouvelle fenêtre
- ✅ Health check automatique (avec retry)
- ✅ Ouverture automatique du navigateur
- ✅ Messages colorés et clairs
- ✅ Affichage PID du serveur

**Avantages**:
- Messages colorés (Cyan, Green, Yellow, Red)
- Gestion d'erreurs robuste
- Ouvre automatiquement le navigateur
- Affiche le PID du serveur pour debugging

---

### 📝 start.bat

**Script Batch Windows classique**

```batch
scripts\start.bat
```

**Fonctionnalités**:
- ✅ Vérification Python
- ✅ Vérification fichiers CSV requis
- ✅ Arrêt processus existants
- ✅ Vérification système (verify.py)
- ✅ Démarrage serveur
- ✅ Health check final

**Avantages**:
- Compatible avec tous les systèmes Windows
- Pas besoin de PowerShell
- Plus simple pour les utilisateurs non techniques

---

### 🔍 verify.py

**Script de vérification système**

```bash
python scripts\verify.py
```

**Fonctionnalités**:
- ✅ Vérification présence de tous les fichiers CSV
- ✅ Test de tous les endpoints API principaux
- ✅ Health check complet
- ✅ Affichage URLs d'accès

**Sortie**:
```
============================================================
 GitFocus Planner V2 - Vérification Système
============================================================

📁 Fichiers CSV requis:
  ✅ LISTE_MERE.v2.csv
  ✅ TACHES_RECURRENTES.v2.csv
  ✅ TACHES_RESPIRATOIRES.v2.csv
  ✅ TACHES_PLANIFIEES.v2.csv
  ✅ temps_morts.csv
  ✅ categories.csv
  ✅ done_v2.csv

🌐 Endpoints API:
✅ Health Check: OK
✅ Tâches Pomodoro: OK
✅ Tâches Récurrentes: OK
✅ Tâches Respiratoires: OK

============================================================
✅ SYSTÈME OPÉRATIONNEL
```

---

## 🚀 Quelle Méthode Utiliser?

### Utilisateurs Windows 10/11 (Recommandé)

**PowerShell** - `start.ps1`
- Meilleure expérience utilisateur
- Messages colorés
- Ouvre le navigateur automatiquement
- Affiche le PID pour debugging

### Utilisateurs Compatibilité

**Batch** - `start.bat`
- Compatible tous Windows
- Plus simple
- Moins de dépendances

### Pour Vérification Rapide

**Python** - `verify.py`
- Vérification sans démarrage
- Diagnostic rapide
- Utilisable dans scripts CI/CD

---

## 📋 Comparaison Détaillée

| Fonctionnalité | start.ps1 | start.bat | verify.py |
|----------------|-----------|-----------|-----------|
| **Vérification Python** | ✅ | ✅ | ❌ |
| **Vérification CSV** | ✅ (7 fichiers) | ✅ (3 fichiers) | ✅ (7 fichiers) |
| **Arrêt processus existants** | ✅ | ✅ | ❌ |
| **Vérification système** | ✅ (via verify.py) | ✅ (via verify.py) | ✅ |
| **Démarrage serveur** | ✅ | ✅ | ❌ |
| **Health check** | ✅ (avec retry) | ✅ | ✅ |
| **Ouverture navigateur** | ✅ | ❌ | ❌ |
| **Messages colorés** | ✅ | ❌ | ✅ (emojis) |
| **Affichage PID** | ✅ | ❌ | ❌ |
| **Gestion erreurs** | ✅✅ | ✅ | ✅ |

---

## 🔧 Dépannage

### PowerShell: "Execution Policy"

Si vous avez l'erreur:
```
... ne peut pas être chargé, car l'exécution de scripts est désactivée...
```

**Solution**:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start.ps1
```

Ou définir la politique de manière permanente (Admin):
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port 5000 Occupé

Les deux scripts tentent d'arrêter automatiquement les processus Flask existants.

Si le problème persiste:
```bash
# Vérifier quel processus occupe le port
netstat -ano | findstr :5000

# Tuer le processus (remplacer PID)
taskkill /F /PID <PID>
```

### Fichiers CSV Manquants

Les scripts vérifient automatiquement. Si erreur:
```
[ERREUR] Fichier manquant: prod_data\LISTE_MERE.v2.csv
```

→ Vérifier que tous les fichiers existent dans `prod_data/`

### Server Ne Démarre Pas

1. **Vérifier Python installé**:
   ```bash
   python --version
   ```
   → Doit afficher Python 3.11+

2. **Vérifier dépendances**:
   ```bash
   pip install flask
   ```

3. **Tester manuellement**:
   ```bash
   python -m webapp.server
   ```

---

## 📝 Notes Techniques

### start.ps1

- **Langage**: PowerShell 5.1+
- **Dépendances**: Python 3.11+, requests
- **Execution Policy**: Bypass recommandé
- **Encodage**: UTF-8

### start.bat

- **Langage**: Batch Windows
- **Dépendances**: Python 3.11+, requests
- **Compatibilité**: Windows XP+
- **Encodage**: ANSI/CP1252

### verify.py

- **Langage**: Python 3.11+
- **Dépendances**: requests
- **Encodage**: UTF-8 (forcé pour Windows)
- **Timeout**: 5 secondes par endpoint

---

## 🎯 Workflow Recommandé

### Démarrage Quotidien

```powershell
# Méthode 1: PowerShell (recommandé)
powershell -ExecutionPolicy Bypass -File scripts\start.ps1

# Méthode 2: Batch (alternative)
scripts\start.bat
```

### Vérification Rapide

```bash
python scripts\verify.py
```

### Démarrage Manuel

```bash
python -m webapp.server
```

---

## ✅ Tests Effectués

**Tous les scripts ont été testés et validés**:

- [x] **start.ps1** - ✅ Fonctionne parfaitement
  - Python vérifié: Python 3.13.5
  - Tous fichiers CSV présents
  - Port 5000 libéré
  - Système vérifié
  - Serveur démarré (PID 24988)
  - Health check: OK
  - Navigateur ouvert automatiquement

- [x] **start.bat** - ✅ Créé et fonctionnel
  - Même vérifications que start.ps1
  - Sans ouverture auto du navigateur

- [x] **verify.py** - ✅ Fonctionne parfaitement
  - Tous endpoints API testés
  - Affichage formaté avec emojis
  - Support UTF-8 Windows

---

**💡 Pour la meilleure expérience, utilisez `start.ps1`!**
