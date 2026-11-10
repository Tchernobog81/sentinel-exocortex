"""
Test d'intégration Google Drive × Google Apps Script
Exécutez ce script pour valider votre configuration
"""

import requests
import json
from datetime import datetime

# À REMPLACER par votre URL de déploiement
CLOUD_URL = "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"

def test_get():
    """Test récupération des données"""
    print("\n🔵 TEST GET - Récupération des données")
    try:
        response = requests.get(CLOUD_URL)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Succès")
            print(f"   Strands: {len(data.get('strands', []))}")
            events = sum(len(s.get('events', [])) for s in data.get('strands', []))
            print(f"   Events: {events}")
            print(f"   Last Update: {data.get('metadata', {}).get('lastUpdate', 'N/A')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

def test_post():
    """Test envoi de données"""
    print("\n🟢 TEST POST - Envoi de données")
    
    new_event = {
        "year": 2026.06,
        "weight": 9,
        "value": 50000,
        "label": "Test Integration",
        "whoWhat": "Python Script",
        "how": "Validation de l'intégration Google Drive",
        "tipping": False
    }
    
    payload = {
        "strands": [
            {
                "name": "⚪ CONVERGENCE",
                "color": "#ffffff",
                "events": [new_event]
            }
        ]
    }
    
    try:
        response = requests.post(
            CLOUD_URL,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'ok':
                print(f"✅ Succès")
                print(f"   Items sauvegardés: {result.get('items')}")
                print(f"   Timestamp: {result.get('timestamp')}")
            else:
                print(f"❌ Erreur serveur: {result.get('message')}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

def test_validation():
    """Test validation de données malformées"""
    print("\n⚠️  TEST VALIDATION - Données invalides")
    
    bad_payload = {"invalid": "data"}
    
    try:
        response = requests.post(
            CLOUD_URL,
            data=json.dumps(bad_payload),
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
        if result.get('status') == 'error':
            print(f"✅ Validation correcte")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Validation échouée (aurait dû rejeter)")
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("🔗 TEST INTÉGRATION GOOGLE DRIVE × GOOGLE APPS SCRIPT")
    print("=" * 60)
    
    if CLOUD_URL == "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec":
        print("\n⚠️  ERREUR: Remplacez YOUR_DEPLOYMENT_ID par votre URL réelle!")
        print("   Voir GOOGLE_DRIVE_SETUP.md pour les instructions")
    else:
        test_get()
        test_post()
        test_validation()
    
    print("\n" + "=" * 60)
    print("Tests terminés")
    print("=" * 60)
