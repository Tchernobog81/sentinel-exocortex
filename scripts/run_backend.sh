#!/bin/bash
# Script pour lancer le backend FastAPI

echo "🚀 Démarrage du backend Cortex Loom..."
cd "$(dirname "$0")/.."

# Vérifier si le venv existe
if [ ! -d "backend/venv" ]; then
    echo "🐍 Création de l'environnement virtuel..."
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Activer le venv et lancer
cd backend
source venv/bin/activate

# Lancer avec Uvicorn (gunicorn si disponible, sinon uvicorn simple)
echo "🌐 Backend démarré sur http://0.0.0.0:8000"
echo "📊 API disponible à /api/data"
echo "📖 Docs disponibles à /api/docs"
echo "⏹️ Appuyez sur Ctrl+C pour arrêter"

if venv/bin/gunicorn --version >/dev/null 2>&1; then
    exec venv/bin/gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 main:app
else
    exec venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000
fi
