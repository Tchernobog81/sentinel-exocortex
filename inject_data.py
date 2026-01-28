import requests
import json
import os
import random

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERREUR CRITIQUE : Module 'python-dotenv' manquant.")
    print("--> Veuillez exécuter : pip install -r requirements.txt")
    exit(1)

# Charge la configuration
load_dotenv()
CLOUD_URL = os.environ.get("CLOUD_URL")
DATA_FILE = "loom_consolidated_v102.json"

def enrich_event_if_needed(event):
    """
    Enrichit un événement avec des données analytiques simulées (Pharmakon, S-Curve)
    si elles sont manquantes. Copié de sentinel.py pour cohérence.
    """
    if "s_curve_phase" in event and event.get("s_curve_phase") is not None:
        return event

    year = event.get("year", 1900)
    category = event.get("category", "DEFAUT")

    # 1. Simulation plausible de la phase de la courbe en S
    if year < 1940: s_curve_phase = 1
    elif year < 1990: s_curve_phase = 2
    elif year < 2015: s_curve_phase = 3
    elif year < 2030: s_curve_phase = 4
    else: s_curve_phase = 5

    # 2. Simulation plausible de l'analyse Pharmakon
    remedy = 50
    if "ENTROPIE" in category: remedy = 10
    elif "BIOTECH" in category or "NOOSPHÈRE" in category: remedy = 70
    elif "HARDWARE" in category or "COGNITION" in category: remedy = 60
    elif "POLITIQUE" in category: remedy = 35
    elif "IMAGINAIRE" in category: remedy = 50

    remedy += random.randint(-10, 10)
    remedy = max(5, min(95, remedy))
    poison = 100 - remedy

    # 3. Ajout des champs d'analyse
    event["s_curve_phase"] = s_curve_phase
    event["pharmakon_remedy_percent"] = remedy
    event["pharmakon_poison_percent"] = poison
    
    return event

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
            
        print(f"🧠 Enrichissement des données (Pharmakon/S-Curve)...")
        enriched_count = 0
        for event in data:
            enrich_event_if_needed(event)
            enriched_count += 1
            
        print(f"💾 Sauvegarde des données enrichies dans {DATA_FILE}...")
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
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