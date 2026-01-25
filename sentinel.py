import requests
import json
import os
import datetime
import random

# --- CONFIGURATION SÉCURISÉE ---
# On récupère l'URL depuis les secrets GitHub
CLOUD_URL = os.environ.get("CLOUD_URL")

if not CLOUD_URL:
    raise Exception("❌ ERREUR : La variable CLOUD_URL est vide. Vérifie tes Secrets GitHub.")

# --- 1. GÉNÉRATEUR D'EVENT (SIMULATION AVANCÉE) ---
def scan_for_singularity_events():
    print("🔎 Scan des fréquences du futur...")
    
    # Pour le test, on génère une date future proche
    today = datetime.date.today()
    future_year = today.year + round(random.uniform(0.1, 2.0), 2) # Entre maintenant et dans 2 ans
    
    events_pool = [
        {"l": "GPT-5 Release", "c": "🔵 INTELLIGENCE", "d": "Capacités de raisonnement avancées confirmées."},
        {"l": "Fusion Ignition", "c": "🟡 SUBSTRAT", "d": "Gain net d'énergie stable pendant 10 sec."},
        {"l": "Boston Dynamics Home", "c": "🟣 EXTENSION", "d": "Commercialisation massive du robot domestique."},
        {"l": "Deepfake Senator", "c": "☢️ RISQUES", "d": "Scandale politique majeur causé par IA."}
    ]
    
    choice = random.choice(events_pool)
    
    new_event = {
        "year": future_year, 
        "value": random.randint(150000, 200000), 
        "label": f"TEST: {choice['l']}", # Je mets TEST pour que tu le repères
        "category": choice['c'], 
        "whoWhat": "Sentinel Bot", 
        "description": choice['d'],
        "realYear": None 
    }
    
    return new_event

# --- 2. RÉCUPÉRATION ---
def get_current_loom():
    print("📥 Téléchargement de la base...")
    try:
        response = requests.get(CLOUD_URL)
        return response.json()
    except Exception as e:
        print(f"Erreur download: {e}")
        return []

# --- 3. INJECTION ---
def update_loom():
    try:
        current_data = get_current_loom()
        print(f"✅ Base chargée : {len(current_data)} entrées.")

        intel = scan_for_singularity_events()
        
        # Vérification doublon (basique)
        exists = any(item.get('label') == intel['label'] for item in current_data)
        
        if not exists:
            current_data.append(intel)
            print(f"🆕 Injection : {intel['label']} ({intel['year']})")
            
            headers = {'Content-Type': 'text/plain;charset=utf-8'}
            response = requests.post(CLOUD_URL, data=json.dumps(current_data), headers=headers)
            
            res_json = response.json()
            if res_json.get('result') == 'success':
                print(f"🚀 SUCCESS : Base mise à jour ({res_json.get('count')} items).")
            else:
                print(f"❌ Erreur Google : {res_json}")
        else:
            print("⏸️ Événement déjà connu. Pas d'injection.")

    except Exception as e:
        print(f"⚠️ CRASH SENTINEL : {e}")
        # On ne raise pas l'erreur pour ne pas faire échouer le workflow brutalement, 
        # mais on pourrait si on veut une alerte mail.

if __name__ == "__main__":
    update_loom()
