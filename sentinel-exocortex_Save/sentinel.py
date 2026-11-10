import requests
import json
import os
import datetime
import random

# --- CONFIGURATION ---
CLOUD_URL = os.environ.get("CLOUD_URL")
if not CLOUD_URL: raise Exception("❌ CLOUD_URL manquante.")

# --- 1. SIMULATION D'UN AGENT DE VEILLE ---
# (À remplacer plus tard par une vraie API de recherche)
def scan_for_singularity_events():
    print("🔎 Scan des signaux faibles...")
    
    today = datetime.date.today()
    # Génère une date dans le futur proche (entre demain et +18 mois)
    future_year = today.year + round(random.uniform(0.01, 1.5), 3)
    
    # Pool d'événements plausibles pour la simulation
    events_pool = [
        {"l": "GPT-5 (Reasoning Alpha)", "c": "🔵 INTELLIGENCE", "d": "Capacités de planification multi-étapes démontrées en labo."},
        {"l": "Qubit Stable (100ms)", "c": "🟡 SUBSTRAT", "d": "Franchissement du seuil de correction d'erreur."},
        {"l": "Optimus (Usine Pilote)", "c": "🟣 EXTENSION", "d": "Déploiement de 500 unités autonomes chez Tesla."},
        {"l": "Régulation IA Globale", "c": "🔴 MATRICE", "d": "Accord préliminaire ONU sur le contrôle des modèles frontières."},
        {"l": "Organoïde Connecté", "c": "🟢 VIVANT", "d": "Première interface bidirectionnelle silicium-neurones biologiques."},
        {"l": "Deepfake Krach Boursier", "c": "☢️ RISQUES", "d": "Flash crash causé par une vidéo synthétique d'un dirigeant."}
    ]
    
    choice = random.choice(events_pool)
    
    new_event = {
        "year": future_year,
        # Valeur Y aléatoire pour le placer sur le graphique log
        "value": random.randint(150000, 350000), 
        "label": choice['l'], # Nom propre, sans préfixe TEST
        "category": choice['c'], 
        "whoWhat": "Sentinel Watch", 
        "description": choice['d'],
        "realYear": None 
    }
    
    return new_event

# --- 2. RÉCUPÉRATION ---
def get_current_loom():
    try:
        response = requests.get(CLOUD_URL, timeout=10)
        return response.json()
    except Exception as e:
        print(f"⚠️ Erreur download (sera écrasé): {e}")
        return []

# --- 3. INJECTION ---
def update_loom():
    try:
        current_data = get_current_loom()
        intel = scan_for_singularity_events()
        
        # Vérification simple de doublon sur le label
        exists = any(item.get('label') == intel['label'] for item in current_data)
        
        if not exists:
            current_data.append(intel)
            print(f"🆕 Injection : {intel['label']} ({intel['year']:.2f})")
            
            headers = {'Content-Type': 'text/plain;charset=utf-8'}
            # Timeout plus long pour l'upload
            response = requests.post(CLOUD_URL, data=json.dumps(current_data), headers=headers, timeout=30)
            
            res_json = response.json()
            if res_json.get('result') == 'success':
                print(f"🚀 SUCCESS : Base à jour ({res_json.get('count')} items).")
            else:
                print(f"❌ Erreur Google Script : {res_json}")
        else:
            print(f"⏸️ Doublon détecté ({intel['label']}). Pas d'injection.")

    except Exception as e:
        print(f"⚠️ CRASH SENTINEL : {e}")

if __name__ == "__main__":
    update_loom()
