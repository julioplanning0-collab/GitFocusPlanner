# Guide d'Utilisation - Nouvelle Structure Docs

## 🎯 Problème Résolu

**Avant** : 358 Ko de docs (12,000 lignes) → contexte explosé constamment
**Après** : 3 fichiers ultra-condensés (~500 lignes total) → contexte maîtrisé

---

## 📁 Nouvelle Structure

```
GitfocusPlanner/
├── CLAUDE_CONCIS.md      # 170 lignes - Vue projet + architecture
├── ESSENTIALS_V3.md      # 280 lignes - V3 implementation guide
├── QUICKREF.md           # 60 lignes  - Commandes & patterns fréquents
│
└── docs_archive/         # NE PAS CHARGER EN CONTEXTE
    ├── SPECIFICATIONS_COMPLETE_V3.md  # 2723 lignes - Full specs
    ├── PLAN_REFONTE_V3.md             # 1724 lignes - Migration plan
    └── [autres docs...]               # Total: 12,000 lignes
```

---

## 🚀 Workflow avec Claude CLI

### Démarrer une session (TOUJOURS)

```bash
# 1. Créer custom command
mkdir -p .claude/commands

# 2. Setup command
cat > .claude/commands/start.md << 'EOF'
Read QUICKREF.md first.
If complex V3 feature: read ESSENTIALS_V3.md.
Never load files from docs_archive/ unless explicitly asked.
EOF

# 3. Démarrer session
claude
/start  # Charge seulement QUICKREF.md
```

### Pendant la session

**Pour tâche simple** (bug fix, small feature) :
```bash
# Juste QUICKREF suffit
/start
"Fix CSV encoding error in data_loader.py"
```

**Pour tâche V3 complexe** :
```bash
/start
"Read ESSENTIALS_V3.md then implement rebuildTimeline() function"
```

**Si besoin architecture complète** :
```bash
/start
"Read CLAUDE_CONCIS.md then explain planning pipeline"
```

**JAMAIS faire** :
```bash
# ❌ MAUVAIS - explose le contexte
"Read all docs then implement feature"
"Load SPECIFICATIONS_COMPLETE_V3.md"
```

### Gérer le contexte (CRITIQUE)

**Utilise /clear AGRESSIVEMENT** :
```bash
# Après chaque micro-tâche (1-3 messages)
User: "Fix data_loader encoding bug"
Claude: [fixes bug]
User: "/clear"  # ← IMPORTANT

# Nouvelle tâche
User: "/start"
User: "Now implement rebuildTimeline()"
```

**Utilise /compact strategiquement** :
```bash
# Quand tu DOIS garder contexte entre 2 tâches liées
/compact Keep: rebuildTimeline implementation, collision detection logic, minuteOffset calculations

# Puis continue
"Now implement findNextFreeSlot() using same approach"
```

**Monitorage** :
```bash
/status  # Check context usage régulièrement
```

---

## 🎯 Stratégies par Type de Tâche

### Bug Fix Urgent
```bash
claude
/start
"Bug: [description]. Check QUICKREF for relevant patterns"
[Claude fixes]
/clear  # Immédiatement après
```

### Feature V3 Simple (1 fonction)
```bash
claude
/start
"Read ESSENTIALS_V3.md section 'Construction Timeline'"
"Implement buildPomodoroList()"
[Claude implémente]
/clear  # Après test réussi
```

### Feature V3 Complexe (plusieurs fonctions liées)
```bash
claude
/start
"Read ESSENTIALS_V3.md completely"
"Create plan.md for implementing STEP 1: ORDERING"
[Claude crée plan]
/clear

# Pour chaque item du plan
/start
"Read plan.md item 1, implement buildPomodoroList()"
[Claude implémente]
"Test in browser, verify works"
/clear

/start
"Read plan.md item 2, implement buildRespirationList()"
[Claude implémente]
/clear

# etc...
```

### Debug Session Longue
```bash
claude
/start
"Read ESSENTIALS_V3.md + QUICKREF.md"
"Debug why minuteOffsets are incorrect"
[Investigation...]

# Si session > 5 messages
/compact Keep: bug hypothesis (collision detection fails when...), test cases tried, minuteOffset calculation logic

"Continue debugging with focus on findNextFreeSlot()"
[Plus d'investigation]
/clear  # Dès que bug fixé
```

---

## 💡 Best Practices Spécifiques

### 1. Découpage Micro-Tâches
```bash
# ❌ MAUVAIS (trop large)
"Implement all V3 ordering functions"

# ✅ BON (micro-tâches)
"Implement buildPomodoroList() only"  # /clear après
"Implement buildRespirationList() only"  # /clear après
"Implement alternatePomodoresRespiration() only"  # /clear après
```

### 2. Plan.md pour Grosse Feature
```bash
# Demander à Claude de créer un plan
"Read ESSENTIALS_V3.md, create plan.md for implementing STEP 1: ORDERING"

# Claude crée plan.md avec items numérotés
# Ensuite : 1 item = 1 session avec /clear entre

/start
"Read plan.md item 1"
[implémente]
/clear

/start
"Read plan.md item 2"
[implémente]
/clear
```

### 3. Custom Commands pour Tâches Répétitives
```bash
# Créer commande pour debug V3
cat > .claude/commands/debug-v3.md << 'EOF'
Read QUICKREF.md.
Focus on V3 timeline debugging.
Key functions: rebuildTimeline, findNextFreeSlot, hasCollision.
Check minuteOffsets are sequential and respect obstacles.
EOF

# Utiliser
/debug-v3
"minuteOffsets are wrong after inserting calins"
```

---

## 📊 Métriques de Succès

**Avant nouvelle structure** :
- Contexte explosé : toutes les 5-10 messages
- Oublie règles projet : constamment
- Vitesse : bloqué depuis des semaines

**Après nouvelle structure** (attendu) :
- Contexte maîtrisé : /clear toutes les 1-3 tâches
- Règles respectées : QUICKREF toujours chargé
- Vitesse : 2x plus rapide (comme tu disais)

---

## 🚨 Signaux d'Alerte

Si Claude fait ces erreurs, c'est que le contexte déborde :

**Signaux** :
- Oublie règles CSV (délimiteur, encoding)
- Oublie architecture 2-step (ORDERING vs TIME CALCULATION)
- Suggère imports Pydantic (interdit dans backend/)
- Oublie atomic writes
- Mélange frontend/backend responsibilities

**Action** :
```bash
/clear  # Immédiat
/start
"Read QUICKREF.md again and [repeat last request]"
```

---

## 🎓 Progression Recommandée

**Jour 1-2** : Habitue-toi au workflow
- Utilise seulement QUICKREF.md
- /clear après CHAQUE tâche
- Petits bug fixes pour pratiquer

**Jour 3-5** : Attaque features V3
- ESSENTIALS_V3.md + plan.md approach
- Découpe en micro-tâches
- /clear agressif maintenu

**Jour 6+** : Autonomie complète
- Tu sais quand lire quelle doc
- /clear devient réflexe
- Vitesse x2 atteinte

---

## 🔧 Troubleshooting

**"Claude charge quand même les gros docs"**
```bash
# Créer .claude/CLAUDE.md global
cat > ~/.claude/CLAUDE.md << 'EOF'
NEVER load files from docs_archive/ unless explicitly requested.
ALWAYS start by reading QUICKREF.md.
For V3 features, read ESSENTIALS_V3.md if needed.
CRITICAL: Use /clear after every 1-3 tasks.
EOF
```

**"Je dois quand même lire les specs complètes parfois"**
```bash
# OK, mais pas en contexte avec code
/clear  # Vide tout d'abord
"Read docs_archive/SPECIFICATIONS_COMPLETE_V3.md section on collision detection"
"Summarize in 10 bullet points"
[Claude résume]
"Save summary to collision_rules.md"
/clear  # Immédiat après résumé

# Ensuite code avec résumé seulement
/start
"Read collision_rules.md and implement hasCollision()"
```

**"Contexte explose encore"**
- Check /status régulièrement
- /clear encore PLUS souvent (après 1 message si nécessaire)
- Réduis taille des tâches encore plus
- Utilise /compact avec instructions très précises

---

**TL;DR** :
1. Toujours démarrer avec `/start` (charge QUICKREF)
2. Tâches V3 complexes : lire ESSENTIALS_V3.md
3. `/clear` après 1-3 messages (AGRESSIF)
4. Plan.md pour grosse feature, découpe en items
5. JAMAIS charger docs_archive/ sauf résumé ponctuel

**Ta vitesse x2 est atteignable si tu suis ce workflow strictement.**
