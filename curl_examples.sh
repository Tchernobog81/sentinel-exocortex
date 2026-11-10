#!/bin/bash
# Exemples de requêtes pour tester l'intégration Google Drive
# Remplacez YOUR_CLOUD_URL par votre URL de déploiement

CLOUD_URL="https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"

echo "🔗 EXEMPLES D'INTÉGRATION GOOGLE DRIVE"
echo "========================================"
echo ""

# TEST 1: Récupérer les données
echo "1️⃣  GET - Récupérer les données"
echo "curl -X GET '$CLOUD_URL'"
echo ""

# TEST 2: Envoyer un nouvel événement
echo "2️⃣  POST - Envoyer un nouvel événement"
echo ""
echo "curl -X POST '$CLOUD_URL' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{
  \"strands\": [
    {
      \"name\": \"🔵 INTELLIGENCE (IA)\",
      \"color\": \"#3b82f6\",
      \"events\": [
        {
          \"year\": 2026.06,
          \"weight\": 9,
          \"value\": 40000,
          \"label\": \"Mon Événement\",
          \"whoWhat\": \"Source\",
          \"how\": \"Description complète\",
          \"img\": \"https://...\",
          \"realYear\": 2030.5,
          \"tipping\": true
        }
      ]
    }
  ]
}'"
echo ""

# TEST 3: Exemple avec jq (parsing JSON)
echo "3️⃣  GET + Parsing avec jq"
echo "curl -s '$CLOUD_URL' | jq '.strands[0].events | length'"
echo ""

# TEST 4: Envoyer depuis un fichier JSON
echo "4️⃣  POST depuis un fichier JSON"
echo "curl -X POST '$CLOUD_URL' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d @loom_data.json"
echo ""

# TEST 5: Valider avec http (HTTPie)
echo "5️⃣  Avec HTTPie (plus lisible)"
echo "http GET $CLOUD_URL"
echo ""

# TEST 6: Automatisation - Envoyer tous les jours à 14h
echo "6️⃣  Cron job - Envoyer chaque jour à 14h"
echo ""
echo "Ajouter à crontab -e:"
echo "0 14 * * * curl -X POST 'YOUR_CLOUD_URL' -H 'Content-Type: application/json' -d @loom_data.json"
echo ""

# TEST 7: PowerShell (Windows)
echo "7️⃣  PowerShell (Windows)"
echo ""
echo "\$url = 'YOUR_CLOUD_URL'"
echo "\$data = Get-Content 'loom_data.json' -Raw | ConvertFrom-Json"
echo "\$json = ConvertTo-Json \$data"
echo "Invoke-WebRequest -Uri \$url -Method POST -Body \$json -ContentType 'application/json'"
echo ""

# TEST 8: Python avec requests
echo "8️⃣  Python"
echo ""
echo "import requests, json"
echo "with open('loom_data.json') as f:"
echo "    data = json.load(f)"
echo "requests.post('YOUR_CLOUD_URL', json=data)"
echo ""

# TEST 9: JavaScript / Fetch API
echo "9️⃣  JavaScript"
echo ""
echo "fetch('YOUR_CLOUD_URL')"
echo "  .then(r => r.json())"
echo "  .then(data => console.log(data))"
echo ""

echo "==========================================="
echo ""
echo "📋 INSTRUCTIONS:"
echo "1. Remplacez YOUR_CLOUD_URL par votre URL de déploiement"
echo "2. Assurez-vous que CLOUD_URL est accessible (Status 200)"
echo "3. Vérifiez que le JSON est bien formé"
echo ""
echo "📚 Documentation complète: GOOGLE_DRIVE_SETUP.md"
