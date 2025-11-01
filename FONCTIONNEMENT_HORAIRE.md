# ⏰ Fonctionnement Horaire - GitFocus Planner V2

**Date**: 2025-10-30
**Fonctionnalité**: Démarrage du planning à l'heure actuelle

---

## 🔧 Correction Appliquée (2025-10-30)

**Bug corrigé**: Le planning commençait à 06:45 au lieu de l'heure actuelle

**Cause**: La fonction `recalculate_times()` forçait le redémarrage à 06:00 même pour aujourd'hui

**Solution**: Ajout de la logique "date du jour vs future" dans `task_integrator.recalculate_times()` (lignes 259-310)

**Résultat**: Le planning démarre maintenant correctement à l'heure actuelle arrondie ✅

**Détails complets**: Voir `FIX_HEURE_DEMARRAGE.md`

---

## ✅ Comportement Actuel

### Pour Aujourd'hui

**Le système démarre automatiquement à l'heure actuelle (arrondie au prochain quart d'heure)**

**Exemple**:
```
Heure actuelle: 07:50:51
Premier créneau: 08:00 - 08:30
```

**Logique**:
1. Si vous générez un planning pour **aujourd'hui**
2. Le système prend l'heure actuelle
3. Arrondit au **prochain quart d'heure** (00, 15, 30, 45)
4. Génère les créneaux de 30 minutes jusqu'à 23:00

### Pour Demain ou Dates Futures

**Le système démarre à 06:00 du matin**

**Logique**:
1. Si vous générez un planning pour **demain** ou une date future
2. Le système démarre à **06:00**
3. Génère les créneaux jusqu'à 23:00

---

## 🔍 Détails Techniques

### Code Responsable

**1. Calcul des créneaux libres** - `backend/planning_engine/slot_calculator.py`

```python
# Lignes 41-67
if target_date == today:
    # Start at current time (rounded up to 15min)
    now = datetime.now()
    start_hour = now.hour
    start_minute = now.minute

    # Round up to next 15-minute mark
    rounded_minute = ((start_minute // 15) + 1) * 15
    if rounded_minute == 60:
        start_hour += 1
        rounded_minute = 0
```

**2. Recalcul des horaires** - `backend/planning_engine/task_integrator.py`

```python
# Lignes 279-310 (🆕 Corrigé le 2025-10-30)
# 🆕 Start at current time if today
target_date = datetime.strptime(date, "%Y-%m-%d").date()
today = datetime.now().date()

if target_date == today:
    # Start at current time (rounded up to 15min)
    now = datetime.now()
    start_hour = now.hour
    start_minute = now.minute

    # Round up to next 15-minute mark
    rounded_minute = ((start_minute // 15) + 1) * 15
    if rounded_minute == 60:
        start_hour += 1
        rounded_minute = 0

    current_time = datetime.strptime(f"{date} {start_hour:02d}:{rounded_minute:02d}", "%Y-%m-%d %H:%M")
    logger.info(f"Recalculating times starting at current time: {current_time.strftime('%H:%M')}")
else:
    # Start at 06:00 for future dates
    current_time = datetime.strptime(f"{date} 06:00", "%Y-%m-%d %H:%M")
```

**Note importante**: Les deux fonctions utilisent maintenant la **même logique** d'arrondi au quart d'heure

### Arrondi au Quart d'Heure

**Pourquoi 15 minutes?**

| Heure actuelle | Premier créneau | Raison |
|---------------|-----------------|--------|
| 07:50 | 08:00 | Arrondi au prochain quart d'heure |
| 08:03 | 08:15 | Arrondi au prochain quart d'heure |
| 08:15 | 08:30 | Déjà sur un quart d'heure → suivant |
| 14:47 | 15:00 | Arrondi au prochain quart d'heure |

**Avantages**:
- ✅ Laisse le temps de consulter le planning
- ✅ Créneaux alignés (00, 15, 30, 45)
- ✅ Compatible avec créneaux de 30 minutes
- ✅ Évite les créneaux trop courts

---

## 📊 Exemples de Planning

### Scénario 1: Générer planning à 10h30

```
Heure de génération: 10:30:00
Premier créneau: 10:45 - 11:15
Créneaux disponibles: 24 (jusqu'à 23:00)
```

**Planning généré**:
```
10:45 - 11:15  🔴 Pomodoro - Installer machine virtuelle
11:15 - 11:20  🟣 Récurrent - Nettoyer caisse chat
11:20 - 11:45  🔴 Pomodoro - Fabriquer les cloches
11:45 - 11:50  🟣 Récurrent - Arroser les plantes
...
```

### Scénario 2: Générer planning à 22h45

```
Heure de génération: 22:45:00
Premier créneau: 23:00 - 23:00 (aucun)
Créneaux disponibles: 0

Message: "Current time 22:45:00 is past end of day (23:00), no slots available"
```

### Scénario 3: Générer planning pour demain

```
Date: 2025-10-31 (demain)
Premier créneau: 06:00 - 06:30
Créneaux disponibles: 34 (toute la journée)
```

---

## 🎯 Interface Utilisateur

### Date par Défaut

L'interface web définit automatiquement la **date du jour**:

```javascript
// webapp/static/js/gitfocus_v2.js - Ligne 274
function setTodayDate() {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('planning-date').value = today;
    state.currentDate = today;
}
```

**Appelée au chargement de la page** (ligne 306):
```javascript
document.addEventListener('DOMContentLoaded', () => {
    setTodayDate();  // Définit la date du jour
    // ...
});
```

### Workflow Utilisateur

1. **Ouvrir l'interface** → Date du jour pré-sélectionnée
2. **Sélectionner tâches** → Cocher 2-3 tâches Pomodoro
3. **Cliquer "Générer Planning"** → Planning démarre à l'heure actuelle
4. **Vérifier le planning** → Premier créneau affiché (ex: 08:00)

---

## ⚙️ Configuration

### Modifier l'Arrondi

Si vous voulez changer l'arrondi de 15 minutes:

**Fichier**: `backend/planning_engine/slot_calculator.py`

```python
# Ligne 49 - Remplacer 15 par votre valeur (5, 10, 30, etc.)
rounded_minute = ((start_minute // 15) + 1) * 15
#                               ^^
#                   Changer ici (5, 10, 30, etc.)
```

**Exemples**:
- `// 5` → Arrondi à 5 minutes (08:05, 08:10, 08:15...)
- `// 10` → Arrondi à 10 minutes (08:10, 08:20, 08:30...)
- `// 30` → Arrondi à 30 minutes (08:30, 09:00, 09:30...)

### Modifier Heure de Début/Fin

**Début de journée** (ligne 56):
```python
if start_hour < 6:  # Changer 6 pour autre heure
    start_hour = 6
```

**Fin de journée** (ligne 70):
```python
end_time = datetime.combine(target_date, datetime.min.time()).replace(hour=23, minute=0)
#                                                                          ^^
#                                                                   Changer 23
```

---

## 🧪 Tests

### Test Manuel

```bash
python -c "
from datetime import datetime
from backend.planning_engine.slot_calculator import calculate_free_slots

today = datetime.now().strftime('%Y-%m-%d')
slots = calculate_free_slots(today, [])

print(f'Heure actuelle: {datetime.now().strftime(\"%H:%M:%S\")}')
print(f'Premier créneau: {slots[0][\"heure_debut\"]}')
print(f'Nombre créneaux: {len(slots)}')
"
```

### Test avec API

```bash
curl -X POST http://localhost:5000/api/v2/gitfocus/planning/generate-auto \
  -H "Content-Type: application/json" \
  -d "{
    \"date\": \"2025-10-30\",
    \"pomodoro_task_ids\": [\"1\"],
    \"max_recurrent_tasks\": 3
  }"
```

**Vérifier**:
- Le premier créneau du planning commence après l'heure actuelle
- Arrondi au prochain quart d'heure

---

## 📝 Notes Importantes

### Cas Limites

1. **Trop tard dans la journée** (après 22:30):
   - Peu ou pas de créneaux disponibles
   - Message d'avertissement dans les logs
   - Suggestion: Générer planning pour demain

2. **Temps morts qui chevauchent l'heure actuelle**:
   - Le premier créneau sera après le temps mort
   - Exemple: Si temps mort 08:00-09:00 et heure actuelle 08:15
   - Premier créneau: 09:00-09:30

3. **Avant 06:00 du matin**:
   - Le système démarre quand même à 06:00
   - Permet de générer planning pour la journée entière

---

## ✅ Vérification Rapide

Pour vérifier que le système fonctionne correctement:

```bash
# 1. Lancer le serveur
python -m webapp.server

# 2. Ouvrir l'interface
http://localhost:5000/api/v2/gitfocus/interface

# 3. Vérifier date du jour pré-sélectionnée
# 4. Générer un planning
# 5. Vérifier que le premier créneau est après l'heure actuelle
```

**Résultat attendu**:
```
Heure actuelle: 10:30
Premier créneau: 10:45 - 11:15
```

---

## 🎉 Conclusion

**Le système fonctionne déjà correctement!**

- ✅ Démarre à l'heure actuelle pour aujourd'hui
- ✅ Arrondi intelligent au prochain quart d'heure
- ✅ Démarre à 06:00 pour les dates futures
- ✅ Date du jour pré-sélectionnée dans l'interface
- ✅ Testé et validé

**Aucune modification nécessaire** - Le système est opérationnel!

---

**Questions?** Le code est dans `backend/planning_engine/slot_calculator.py` (lignes 19-96)
