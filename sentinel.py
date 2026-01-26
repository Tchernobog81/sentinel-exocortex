import requests
import json
import os
import time
import datetime
import random
import logging
from typing import List, Dict, Any
import feedparser

try:
    from dotenv import load_dotenv
except ImportError:
    print("ERREUR CRITIQUE : Module 'python-dotenv' manquant.")
    print("--> Veuillez exécuter : pip install -r requirements.txt")
    exit(1)

# --- CONFIGURATION ---
load_dotenv() # Charge les variables depuis le fichier .env

CLOUD_URL = os.environ.get("CLOUD_URL")
# Convertir l'intervalle en entier, avec une valeur par défaut de 3600s (1h)
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", 3600))
# Mode "Single Run" pour GitHub Actions (évite la boucle infinie)
SINGLE_RUN = os.environ.get("SINGLE_RUN", "false").lower() == "true"
# Mode de scan : SIMULATOR (défaut) ou RSS_NEWS
SCAN_MODE = os.environ.get("SCAN_MODE", "SIMULATOR")

# Configuration du Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel.log", encoding='utf-8'), # Sauvegarde les logs dans un fichier
        logging.StreamHandler() # Affiche les logs dans la console
    ]
)

# --- 1. AGENTS DE VEILLE ---

def classify_entry(title: str, summary: str) -> str:
    """Tente de classifier un article en fonction de mots-clés."""
    text = (title + " " + summary).lower()
    if any(k in text for k in ["quantum", "chip", "gpu", "hardware", "moore", "nvidia"]):
        return "🟡 HARDWARE"
    if any(k in text for k in ["gpt", "model", "reasoning", "agi", "cognitive", "openai", "anthropic"]):
        return "🔵 COGNITION"
    if any(k in text for k in ["dna", "crispr", "biotech", "neuralink", "organoid"]):
        return "🟢 BIOTECH"
    if any(k in text for k in ["space", "rocket", "mars", "starship", "spacex"]):
        return "🟣 ESPACE"
    if any(k in text for k in ["risk", "danger", "regulation", "bias", "threat", "law"]):
        return "☢️ ENTROPIE"
    return "🔴 RÉSEAU" # Catégorie par défaut pour les news générales, internet, etc.

def scan_google_news_rss() -> Dict[str, Any] | None:
    """Scanne le flux RSS de Google News sur la singularité."""
    logging.info("[SCAN] Scan du flux Google News RSS...")
    # URL pour les actualités en français sur "technological singularity" OR "artificial general intelligence"
    RSS_URL = "https://news.google.com/rss/search?q=%22technological+singularity%22+OR+%22artificial+general+intelligence%22&hl=fr&gl=FR&ceid=FR:fr"
    
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        logging.info("... Aucun article trouvé dans le flux RSS.")
        return None

    latest_entry = feed.entries[0] # On prend le plus récent
    
    today = datetime.date.today()
    # On place l'événement dans l'année en cours
    event_year = today.year + (today.month / 12)

    return {
        "year": round(event_year, 3),
        "value": random.randint(20000, 50000), # Valeur Y aléatoire pour le moment
        "label": latest_entry.title,
        "category": classify_entry(latest_entry.title, latest_entry.summary),
        "whoWhat": latest_entry.source.get('title', 'Google News'),
        "description": latest_entry.summary,
        "url": latest_entry.link,
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": False
    }

def scan_simulator() -> Dict[str, Any] | None:
    """
    Simule une veille technologique.
    TODO: Remplacer par une vraie source (flux RSS, API, etc.)
    """
    logging.info("[SCAN] Scan des signaux faibles (Zeitgeist)...")

    today = datetime.date.today()
    # Génère une date dans le futur proche (entre maintenant et +1.5 ans)
    future_year = today.year + round(random.uniform(0.01, 1.5), 3)

    # Pool d'événements plausibles (Simulation de "headlines")
    events_pool = [
        {"l": "GPT-5 (Reasoning Alpha)", "c": "🔵 COGNITION", "d": "Capacités de planification multi-étapes démontrées en labo."},
        {"l": "Qubit Stable (100ms)", "c": "🟡 HARDWARE", "d": "Franchissement du seuil de correction d'erreur."},
        {"l": "Optimus (Usine Pilote)", "c": "🟣 ESPACE", "d": "Déploiement de 500 unités autonomes chez Tesla."},
        {"l": "Régulation IA Globale", "c": "🔴 RÉSEAU", "d": "Accord préliminaire ONU sur le contrôle des modèles frontières."},
        {"l": "Organoïde Connecté", "c": "🟢 BIOTECH", "d": "Première interface bidirectionnelle silicium-neurones biologiques."},
        {"l": "Deepfake Krach Boursier", "c": "☢️ ENTROPIE", "d": "Flash crash causé par une vidéo synthétique d'un dirigeant."}
    ]

    # Simule une probabilité de découverte (1 chance sur 3 par cycle pour l'exemple)
    if random.random() > 0.66:
        logging.info("... Aucun signal significatif détecté ce cycle.")
        return None

    choice = random.choice(events_pool)

    # Création de l'objet événement au format v102
    return {
        "year": future_year,
        "value": random.randint(15000, 45000), # Valeur Y pour le graphique
        "label": choice['l'],
        "category": choice['c'],
        "whoWhat": "Sentinel AI",
        "description": choice['d'],
        "timestamp": datetime.datetime.now().isoformat(), # Timestamp de la découverte
        "tipping": False # Par défaut, un événement n'est pas un point d'inflexion
    }

# --- 2. COMMUNICATION AVEC LE LOOM (CLOUD) ---
def get_current_loom() -> List[Dict]:
    """Récupère la base de données actuelle depuis le Google Apps Script."""
    try:
        response = requests.get(CLOUD_URL, timeout=20)
        response.raise_for_status() # Lève une exception pour les codes d'erreur HTTP (4xx, 5xx)
        data = response.json()
        if isinstance(data, list):
            logging.info(f"[CLOUD] Base de données récupérée ({len(data)} items).")
            return data
        else:
            logging.warning("Format de données inattendu (pas une liste). Initialisation avec une liste vide.")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"[ERROR] Erreur réseau lors de la récupération: {e}")
        return [] # Retourne une liste vide pour ne pas crasher le cycle
    except json.JSONDecodeError as e:
        logging.error(f"[ERROR] Erreur de parsing JSON lors de la récupération: {e}")
        return []

def post_updated_loom(data: List[Dict]):
    """Poste la base de données mise à jour vers le Google Apps Script."""
    try:
        headers = {'Content-Type': 'text/plain;charset=utf-8'}
        response = requests.post(CLOUD_URL, data=json.dumps(data, ensure_ascii=False), headers=headers, timeout=45)
        response.raise_for_status()
        res_json = response.json()
        if res_json.get('status') == 'ok' or res_json.get('result') == 'success':
            count = res_json.get('items') or res_json.get('count')
            logging.info(f"[SUCCESS] Base de données mise à jour ({count} items).")
        else:
            logging.error(f"[ERROR] Erreur retournée par Google Script : {res_json.get('message') or res_json}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[ERROR] Erreur réseau lors de l'envoi: {e}")
    except json.JSONDecodeError as e:
        logging.error(f"[ERROR] Erreur de parsing JSON dans la réponse du serveur: {e}")

# --- 3. CYCLE PRINCIPAL DE L'AGENT ---
def run_sentinel_cycle():
    """Exécute un cycle complet de veille et d'injection."""
    if not CLOUD_URL:
        logging.critical("[CRITICAL] CLOUD_URL n'est pas définie dans le fichier .env. Arrêt de l'agent.")
        return False # Signal pour arrêter la boucle principale
    try:
        if SCAN_MODE == "RSS_NEWS":
            new_intel = scan_google_news_rss()
        else:
            new_intel = scan_simulator()

        if not new_intel: return True

        current_data = get_current_loom()
        is_duplicate = any(item.get('label') == new_intel['label'] for item in current_data)
        if is_duplicate:
            logging.info(f"[PAUSE] Doublon détecté ('{new_intel['label']}'). Pas d'injection.")
            return True
        logging.info(f"[NEW] Injection de : '{new_intel['label']}' (Année: {new_intel['year']:.2f})")
        current_data.append(new_intel)
        post_updated_loom(current_data)
    except Exception as e:
        logging.error(f"[FATAL] ERREUR INATTENDUE dans le cycle Sentinel : {e}", exc_info=True)
    return True

if __name__ == "__main__":
    logging.info(f"--- SENTINEL EXOCORTEX v109 --- MODE: {SCAN_MODE} ---")
    
    if SINGLE_RUN:
        logging.info("Mode SINGLE_RUN activé (GitHub Actions). Exécution unique.")
        run_sentinel_cycle()
        exit(0)

    while True:
        should_continue = run_sentinel_cycle()
        if not should_continue: break
        logging.info(f"[SLEEP] En veille pour {SCAN_INTERVAL} secondes...")
        time.sleep(SCAN_INTERVAL)