#!/bin/bash
# Script pour lancer Sentinel en mode continu

echo "🔄 Démarrage de Sentinel en mode continu..."
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

echo "🎯 Exécution en mode continu (Ctrl+C pour arrêter)..."
echo "🕒 Intervalle de scan: 1 heure"

python -c "from sentinel import continuous_scan; continuous_scan()"
