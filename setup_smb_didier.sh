#!/bin/bash
# Script pour créer le partage SMB 'didier_share' sur /Volumes/Didier/
# À exécuter avec : chmod +x setup_smb_didier.sh && ./setup_smb_didier.sh

echo "=========================================="
echo "🔧 Configuration du partage SMB 'didier_share'"
echo "=========================================="
echo ""

# Étape 1 : Créer le dossier
echo "📁 Création du dossier /Volumes/Didier/didier_share..."
sudo mkdir -p /Volumes/Didier/didier_share
if [ $? -ne 0 ]; then
    echo "❌ Échec de la création du dossier"
    exit 1
fi

# Étape 2 : Définir les permissions
echo "🔐 Configuration des permissions..."
sudo chown $(whoami):staff /Volumes/Didier/didier_share
sudo chmod 775 /Volumes/Didier/didier_share

# Étape 3 : Activer le service SMB
echo "🌐 Activation du service SMB..."
sudo launchctl load -w /System/Library/LaunchDaemons/com.apple.smbd.plist

# Étape 4 : Ajouter le partage
echo "🔗 Ajout du partage 'didier_share'..."
sudo sharing -a /Volumes/Didier/didier_share -n didier_share

# Étape 5 : Vérification
echo ""
echo "✅ Configuration terminée!"
echo ""
echo "📋 Résumé :"
sharing | grep didier_share

echo ""
echo "🌐 Pour accéder depuis Windows (Surface) :"
echo "   1. Ouvre l'Explorateur de fichiers (Win+E)"
MY_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}')
echo "   2. Dans la barre d'adresse, tape : \\\\$MY_IP\didier_share"
echo ""
echo "💡 Si ça ne marche pas :"
echo "   - Vérifie que le pare-feu autorise le port 445"
echo "   - Utilise l'IP : $MY_IP"
echo "   - Nom d'utilisateur : $(whoami)"
echo "   - Mot de passe : [ton mot de passe Mac]"
echo ""
echo "✨ Le partage est prêt à être testé depuis ta Surface!"
