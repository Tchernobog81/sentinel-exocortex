import requests
import json
import os
from dotenv import load_dotenv

# Charge la configuration
load_dotenv()
CLOUD_URL = os.environ.get("CLOUD_URL")
DATA_FILE = "loom_consolidated_v102.json"

def inject_massive_data():
    print("--- INJECTION DE DONNÉES (SEED) ---")
    
    if not CLOUD_URL:
        print("❌ ERREUR: CLOUD_URL manquante dans le fichier .env")
        return

    if not os.path.exists(DATA_FILE):
        print(f"❌ ERREUR: Fichier de données '{DATA_FILE}' introuvable.")
        return

    print(f"📂 Lecture de {DATA_FILE}...")
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"📦 Préparation de l'envoi de {len(data)} événements...")
        
        # Envoi au script Google
        headers = {'Content-Type': 'application/json'}
        response = requests.post(CLOUD_URL, data=json.dumps(data), headers=headers, timeout=60)
        
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get('status') == 'ok' or res_json.get('result') == 'success':
                print(f"✅ SUCCÈS ! Base de données écrasée et mise à jour.")
                print(f"   Items: {res_json.get('items') or res_json.get('count')}")
                print(f"   Timestamp: {res_json.get('timestamp') or 'N/A'}")
            else:
                print(f"⚠️ Erreur logique serveur: {res_json}")
        else:
            print(f"❌ Erreur HTTP: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"💥 Exception: {e}")

if __name__ == "__main__":
    inject_massive_data()