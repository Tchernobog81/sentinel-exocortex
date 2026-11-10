#!/bin/bash
# Script d'installation et de configuration rapide pour Cortex Loom

echo "=========================================="
echo "🚀 Installation de Cortex Loom"
echo "=========================================="
echo ""

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé!"
    echo "Installez Python 3.10+ depuis https://www.python.org"
    exit 1
fi

echo "✅ Python trouvé : $(python3 --version)"
echo ""

# Vérifier pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip non trouvé!"
    echo "Installez pip avec : python3 -m ensurepip --upgrade"
    exit 1
fi

echo "✅ pip trouvé : $(pip3 --version)"
echo ""

# Créer les venv pour backend et sentinel
echo "🐍 Création des environnements virtuels..."

# Backend
if [ ! -d "backend/venv" ]; then
    echo "  - Création de backend/venv..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo "  ✅ backend/venv créé"
else
    echo "  ⏭️ backend/venv existe déjà"
fi

# Sentinel
if [ ! -d "sentinel/venv" ]; then
    echo "  - Création de sentinel/venv..."
    cd sentinel
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
    echo "  ✅ sentinel/venv créé"
else
    echo "  ⏭️ sentinel/venv existe déjà"
fi

echo ""
echo "✅ Installation terminée!"
echo ""
echo "=========================================="
echo "📋 Prochaines étapes :"
echo "=========================================="
echo ""
echo "1. Copier le fichier de configuration :"
echo "   cp .env.example .env"
echo ""
echo "2. Éditer .env pour personnaliser (optionnel) :"
echo "   nano .env"
echo ""
echo "3. Lancer le backend FastAPI :"
echo "   ./scripts/run_backend.sh"
echo ""
echo "4. Dans un autre terminal, lancer Sentinel :"
echo "   ./scripts/run_sentinel.sh"
echo ""
echo "5. Ouvrir index.html dans ton navigateur"
echo ""
echo "=========================================="
echo "💡 Commandes utiles :"
echo "=========================================="
echo ""
echo "  - Backend (dev) : cd backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Backend (prod): ./scripts/run_backend.sh"
echo "  - Sentinel (once): ./scripts/run_sentinel.sh"
echo "  - Sentinel (loop): ./scripts/run_continuous.sh"
echo ""
echo "✅ Prêt à démarrer!"
