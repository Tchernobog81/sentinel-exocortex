#!/bin/bash
# Script pour lancer l'agent Sentinel

echo "🔍 Démarrage de l'agent Sentinel..."
cd "$(dirname "$0")/.."

# Vérifier si le venv existe
if [ ! -d "sentinel/venv" ]; then
    echo "🐍 Création de l'environnement virtuel..."
    cd sentinel
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Activer le venv et lancer
cd sentinel
source venv/bin/activate

echo "🎯 Exécution d'un cycle unique..."
echo "⏹️ Appuyez sur Ctrl+C pour arrêter"

python sentinel.py
