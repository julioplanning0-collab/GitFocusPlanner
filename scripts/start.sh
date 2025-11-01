#!/bin/bash

# Script de démarrage pour GitFocus Planner (Linux/Mac)

echo "================================================"
echo "  GitFocus Planner - Démarrage"
echo "================================================"
echo ""

# Trouve l'IP locale
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    IP=$(hostname -I | awk '{print $1}')
elif [[ "$OSTYPE" == "darwin"* ]]; then
    IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
else
    IP="localhost"
fi

# Note sur MQTT (optionnel)
echo "[INFO] MQTT Broker optionnel"
echo "  Si vous voulez l'intégration Android:"
echo "  - Installer Mosquitto: sudo apt install mosquitto (Linux)"
echo "  - Ou: brew install mosquitto (macOS)"
echo "  - Lancer: mosquitto -v"
echo ""

# Démarre le serveur Flask
echo "Démarrage du serveur web..."
echo ""
echo "Serveur accessible sur:"
echo "  - Local:  http://localhost:5000"
echo "  - Mobile: http://$IP:5000"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter"
echo ""

# Change vers le répertoire racine du projet
cd "$(dirname "$0")/.."

# Active l'environnement virtuel et lance le serveur
source webapp/venv/bin/activate
python -m webapp.server
