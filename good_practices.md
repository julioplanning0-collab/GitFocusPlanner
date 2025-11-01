# 📚 Bonnes Pratiques de Développement - GitFocus Planner V2

**Date de création**: 2025-10-30
**Version**: 2.0

---

## 🎯 Philosophie de Développement

Ce projet suit une discipline d'ingénierie stricte :

### Principes Fondamentaux

1. **Pas de raccourcis** : Toujours trouver la cause racine, jamais patcher les symptômes
2. **Pas d'échecs silencieux** : Logger toutes les erreurs clairement avec contexte
3. **Opérations atomiques** : Toutes les écritures de fichiers atomiques pour éviter la corruption
4. **Conversions explicites** : Ne jamais compter sur la coercition de types implicite
5. **Messages d'erreur clairs** : L'utilisateur a besoin d'informations actionnables
6. **Responsabilité unique** : Un changement par commit, séparation claire des responsabilités
7. **Dégradation gracieuse** : Données manquantes → afficher ce qui est disponible, logger l'erreur

---

## 🚀 Workflow de Modification de Code

**À suivre AVANT chaque changement de code** :

### 1. Lire les spécifications
- Consulter `SPECIFICATIONS_COMPLETES_V2.md`
- Vérifier la documentation existante

### 2. Rechercher le code existant
```bash
grep -r "function_name" backend/
```

### 3. Planifier le changement
- Documenter ce qui va être modifié
- **UN SEUL objectif par changement**

### 4. Identifier la cause racine
- Ne pas patcher les symptômes
- Corriger le vrai problème

### 5. Implémenter
- Changements petits et incrémentaux
- Tester immédiatement après chaque changement

### 6. Tester immédiatement
- Test API manuel ou test navigateur
- Vérifier que le changement fonctionne

### 7. Vérifier l'encodage
- S'assurer que le fichier est en UTF-8 après édition

### 8. **🆕 Supprimer le code obsolète**
- **Supprimer physiquement** le code devenu obsolète
- **NE JAMAIS** commenter le code obsolète
- Effacer complètement les fonctions, blocs, et variables non utilisés

### 9. Vérifier l'absence de duplication
```bash
grep -r "function_name" backend/
```

### 10. **🆕 Mettre à jour les spécifications**
- Mettre à jour `SPECIFICATIONS_COMPLETES_V2.md` avec la **nouvelle logique**
- **Décrire l'algorithme et les règles SANS code**
- Supprimer les exemples de code obsolètes dans les specs
- **Format recommandé** : Descriptions textuelles, listes à puces, étapes algorithmiques

**Exemple de bonne mise à jour de specs** :
```markdown
## ÉTAPE X : Nom de l'étape

**Nouvelle logique (2025-10-30)** : Description courte

**Règles** :
- Règle 1
- Règle 2

**Algorithme** :
1. Étape 1
2. Étape 2
3. Étape 3

**Cas limites** :
- Cas A → Comportement A
- Cas B → Comportement B
```

**❌ Mauvaise pratique** : Laisser du code Python obsolète dans les specs
**✅ Bonne pratique** : Remplacer par des descriptions algorithmiques

### 11. Mettre à jour la documentation
- Mettre à jour `CLAUDE.md` si l'architecture change
- Créer des fichiers de documentation dédiés si nécessaire (ex: `FIX_*.md`)

---

## ⚠️ Pièges Courants à Éviter

### 1. Erreurs d'Encodage
- **Toujours** spécifier `encoding='utf-8'` pour les opérations fichier
- Les CSV contiennent des caractères accentués (noms français)
- L'encodage par défaut dépend du système (cp1252 sur Windows)

```python
# ❌ MAUVAIS
with open(file_path, 'w') as f:
    ...

# ✅ BON
with open(file_path, 'w', encoding='utf-8') as f:
    ...
```

### 2. Écritures Non-Atomiques
- **Toujours** utiliser le pattern temp file + rename
- Les écritures directes risquent la corruption en cas de crash
- Les fichiers CSV sont des données critiques de l'utilisateur

```python
# ❌ MAUVAIS
with open(csv_path, 'w', encoding='utf-8') as f:
    writer.writerows(rows)

# ✅ BON
temp_file = csv_path.with_suffix('.tmp')
with open(temp_file, 'w', encoding='utf-8') as f:
    writer.writerows(rows)
temp_file.replace(csv_path)  # Atomique
```

### 3. Délimiteur CSV Incorrect
- **Toujours** utiliser `;` (point-virgule)
- La virgule `,` va casser le parsing (les noms de tâches contiennent des virgules)

```python
# ❌ MAUVAIS
writer = csv.DictWriter(f, fieldnames, delimiter=',')

# ✅ BON
writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
```

### 4. Confusion de Formats de Date
- **API** : `YYYY-MM-DD` (format ISO)
- **Saisie utilisateur** : `DD.MM.YY` (format français)
- **Toujours** convertir explicitement

```python
# ❌ MAUVAIS - Conversion implicite
date_str = "27.10.25"
dt = datetime.strptime(date_str, "%Y-%m-%d")  # Va échouer

# ✅ BON - Conversion explicite
from datetime import datetime

def parse_user_date(date_str: str) -> str:
    """Convert DD.MM.YY → YYYY-MM-DD"""
    dt = datetime.strptime(date_str, '%d.%m.%y')
    return dt.strftime('%Y-%m-%d')
```

### 5. Logs d'Erreurs Manquants
- **Toujours** logger les erreurs avec contexte
- Ne pas ignorer silencieusement les données invalides
- L'utilisateur doit savoir ce qui ne va pas pour corriger

```python
# ❌ MAUVAIS
try:
    value = int(row['duration'])
except ValueError:
    value = 0  # Silencieux

# ✅ BON
try:
    value = int(row['duration'])
except ValueError as e:
    logger.error(f"Invalid duration in row {row['id']}: {row['duration']}: {e}")
    value = 0  # Valeur par défaut
```

### 6. Chemins en Dur
- **Toujours** utiliser les objets `Path`
- Windows utilise `\`, Unix utilise `/`
- `Path` gère cela automatiquement

```python
# ❌ MAUVAIS
file_path = "C:\\Users\\juli0\\...\\data.csv"

# ✅ BON
from pathlib import Path
file_path = Path("C:/Users/juli0/.../data.csv")
# ou
file_path = Path(__file__).parent / "data" / "data.csv"
```

### 7. Fuites de Processus
- **Toujours** tuer les processus précédents avant de démarrer
- `scripts\start.bat` tue tous les processus Python d'abord
- Évite les conflits de port (port 5000)

### 8. **🆕 Code Obsolète Non Supprimé**
- **Jamais** commenter du code obsolète
- **Toujours** supprimer physiquement le code mort
- Les commentaires de code créent de la confusion et de la dette technique

```python
# ❌ MAUVAIS
# def old_function():
#     # Ancien code...
#     pass

def new_function():
    # Nouveau code...
    pass

# ✅ BON
def new_function():
    # Nouveau code...
    pass
```

### 9. **🆕 Specs avec Code Obsolète**
- **Jamais** laisser du code obsolète dans les spécifications
- **Toujours** remplacer par des descriptions algorithmiques
- Les specs doivent décrire la logique, pas l'implémentation

---

## 📐 Architecture et Séparation des Responsabilités

### Règles Critiques

1. **`backend/`** NE fait JAMAIS d'I/O directe
   - Lit via objets `Path`
   - Écrit via fonctions atomiques

2. **`webapp/api/`** gère HTTP/JSON
   - Délègue la logique à `backend/`

3. **Toutes les écritures CSV** DOIVENT utiliser opérations atomiques
   - Temp file + rename

4. **Tous les modèles de données** utilisent `List[Dict]`
   - PAS Pydantic
   - PAS dataclasses

---

## 🎭 Gestion des Erreurs

### Quand Échouer Fort (raise exception)
- Requête API invalide → 400 Bad Request
- Échec d'écriture fichier → 500 Internal Server Error
- Format de date invalide → 400 Bad Request

### Quand Dégrader Gracieusement (retourner données partielles + log)
- Fichier CSV non trouvé → Retourner `[]` + log WARNING
- Ligne CSV invalide → Ignorer ligne + log ERROR
- Erreur d'encodage → Re-encoder + retry + log INFO

### Pourquoi Cette Distinction ?
- **Erreurs utilisateur** (mauvaise requête API) → Échouer vite, retourner erreur claire
- **Erreurs de données** (CSV corrompu) → Afficher ce qui est disponible, permettre à l'utilisateur de corriger

---

## 📝 Standards de Code

### Format CSV
- **Délimiteur** : `;` (point-virgule, PAS virgule)
- **Quoting** : `csv.QUOTE_ALL` (tous les champs quotés)
- **Encodage** : `UTF-8` (PAS latin-1, PAS cp1252)
- **Fin de ligne** : `\n` (LF, pas CRLF)
- **Échappement** : `""` (guillemets doublés)

```csv
"ID";"NAME";"DURATION_MIN";"PRIORITY"
"TASK001";"Révision mathématiques";"25";"1"
"TASK002";"Pause café";"10";"3"
```

### Écritures Atomiques (OBLIGATOIRE)
```python
from pathlib import Path
import csv

def _atomic_write_csv(csv_path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    """Atomic CSV write to prevent corruption."""
    temp_file = csv_path.with_suffix('.tmp')

    # Écrire dans fichier temporaire
    with open(temp_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    # Renommage atomique (l'OS garantit l'atomicité)
    temp_file.replace(csv_path)
```

### Formats de Date
```python
# API : YYYY-MM-DD (ISO)
api_date = "2025-10-30"

# Saisie utilisateur : DD.MM.YY (français)
user_date = "30.10.25"

# Tâches planifiées : DD.MM.YY HH:MM
planned_time = "30.10.25 14:30"

# Conversion utilisateur → API
def parse_user_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, '%d.%m.%y')
    return dt.strftime('%Y-%m-%d')

# Conversion API → utilisateur
def format_user_date(iso_date: str) -> str:
    dt = datetime.strptime(iso_date, '%Y-%m-%d')
    return dt.strftime('%d.%m.%y')
```

---

## 🧪 Tests

### Tests Manuels Rapides

```bash
# Health check
curl http://localhost:5000/health

# Lister tâches
curl http://localhost:5000/api/v2/gitfocus/tasks/pomodoro

# Générer planning
curl -X POST http://localhost:5000/api/v2/gitfocus/planning/generate-auto \
  -H "Content-Type: application/json" \
  -d '{"date":"2025-10-30","pomodoro_ids":["1","2"],"max_recurrent_tasks":10}'
```

### Test de Non-Régression

Après chaque modification importante :
1. Tester génération planning pour aujourd'hui
2. Tester génération planning pour demain
3. Vérifier export CSV
4. Vérifier que le serveur démarre
5. Vérifier l'interface web

---

## 📚 Documentation

### Fichiers à Mettre à Jour

1. **`SPECIFICATIONS_COMPLETES_V2.md`** - Specs techniques (SANS code obsolète)
2. **`CLAUDE.md`** - Notes de développement
3. **`.claude/CLAUDE.md`** - Bonnes pratiques pour Claude Code
4. **`good_practices.md`** - Ce fichier
5. **`FIX_*.md`** - Documentation des corrections (si nécessaire)

### Format de Documentation de Correction

Créer un fichier `FIX_[NOM_BUG].md` pour chaque correction importante :

```markdown
# 🔧 Correction - [Titre du Bug]

**Date de correction**: YYYY-MM-DD
**Problème**: Description courte
**Statut**: ✅ RÉSOLU

## 📋 Symptôme Initial
[Description du comportement observé]

## 🔍 Investigation
[Étapes d'investigation et découvertes]

## ✅ Correction Appliquée
[Fichiers modifiés et changements effectués]

## 🧪 Tests de Validation
[Tests effectués et résultats]

## 🎯 Impact
[Fonctionnalités corrigées et fichiers modifiés]
```

---

## 🎉 Récapitulatif des Bonnes Pratiques

### ✅ À Faire Toujours

1. ✅ Spécifier `encoding='utf-8'` pour toutes les opérations fichier
2. ✅ Utiliser écritures atomiques (temp file + rename)
3. ✅ Utiliser délimiteur `;` pour CSV
4. ✅ Convertir explicitement les dates
5. ✅ Logger toutes les erreurs avec contexte
6. ✅ Utiliser objets `Path` pour les chemins
7. ✅ Tuer processus existants avant démarrage
8. ✅ **Supprimer physiquement le code obsolète**
9. ✅ **Mettre à jour les specs SANS code**
10. ✅ Tester immédiatement après changement
11. ✅ Documenter les changements importants

### ❌ À Ne Jamais Faire

1. ❌ Écrire directement dans un fichier sans pattern atomique
2. ❌ Utiliser virgule comme délimiteur CSV
3. ❌ Laisser du code obsolète commenté
4. ❌ Laisser du code obsolète dans les specs
5. ❌ Patcher les symptômes au lieu de corriger la cause racine
6. ❌ Ignorer silencieusement les erreurs
7. ❌ Hardcoder des chemins
8. ❌ Compter sur la coercition de types implicite

---

**Version**: 2.0
**Dernière mise à jour**: 2025-10-30
**Auteur**: Julio
**Projet**: GitFocus Planner V2
