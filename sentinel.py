import json
import os
import time
import datetime
import random
import logging
import zlib
from typing import List, Dict, Any

try:
    import requests
    import feedparser
    from dotenv import load_dotenv
except ImportError as e:
    print(f"ERREUR CRITIQUE : Module manquant ({e.name}).")
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

def categorize_text(text: str) -> str:
    """Tente de classifier un texte en fonction de mots-clés."""
    text = text.lower()
    if "noosphere" in text or "teilhard" in text or "kardashev" in text:
        return "✨ NOOSPHÈRE"
    if any(k in text for k in ["quantum", "chip", "gpu", "hardware", "moore", "nvidia"]):
        return "🟡 HARDWARE"
    if any(k in text for k in ["gpt", "model", "reasoning", "agi", "cognitive", "openai", "anthropic"]):
        return "🔵 COGNITION"
    if any(k in text for k in ["dna", "crispr", "biotech", "neuralink", "organoid"]):
        return "🟢 BIOTECH"
    if any(k in text for k in ["space", "rocket", "mars", "starship", "spacex"]):
        return "🟣 ESPACE"
    if any(k in text for k in ["risk", "danger", "regulation", "bias", "threat", "law", "doomsday"]):
        return "☢️ ENTROPIE"
    return "🔴 RÉSEAU" # Catégorie par défaut pour les news générales, internet, etc.

def analyze_event(entry_title: str, entry_summary: str, entry_url: str, entry_source: str) -> Dict[str, Any]:
    """
    Analyse un événement brut (ex: article de news) et le transforme
    en un objet de données enrichi selon les directives v117.
    Cette fonction est pour les NOUVEAUX événements.
    """
    logging.info(f"[ANALYSE] Analyse Pharmakon de : '{entry_title}'")

    full_text = entry_title + " " + entry_summary
    category = categorize_text(full_text)

    # --- Simulation de l'analyse v117 ---
    s_curve_phase = random.randint(1, 5)
    pharmakon_remedy = random.randint(20, 80)
    pharmakon_poison = 100 - pharmakon_remedy

    convergences_pool = ["Croise le risque de régulation", "Accélère la course au hardware", "Impacte la souveraineté des données", "Aucune convergence majeure détectée"]
    grand_filter_pool = ["Faible risque de filtre", "Pourrait être un petit filtre", "Augmente la complexité systémique"]
    final_note_pool = ["Et une autre tuile.", "Fascinant et terrifiant.", "On en reparlera en pleurant.", "Le futur est décidément mal écrit."]

    today = datetime.date.today()
    event_year = today.year + (today.month / 12)

    return {
        # Core data
        "year": round(event_year, 3),
        "value": random.randint(20000, 50000),
        "label": entry_title,
        "category": category,
        "whoWhat": entry_source,
        "description": entry_summary,
        "url": entry_url,
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": random.random() > 0.8, # 20% chance of being a tipping point

        # v117 Pharmakon Analysis
        "s_curve_phase": s_curve_phase,
        "pharmakon_remedy_percent": pharmakon_remedy,
        "pharmakon_poison_percent": pharmakon_poison,
        "convergences": random.choice(convergences_pool),
        "grand_filter_analysis": random.choice(grand_filter_pool),
        "final_note": random.choice(final_note_pool)
    }

def enrich_event_if_needed(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Vérifie si un événement a déjà une analyse v117. Si non, il la simule
    de manière plausible en se basant sur l'année et la catégorie.
    Cette fonction est pour les événements HISTORIQUES.
    """
    # Si l'événement a déjà une analyse, on ne touche à rien.
    if "s_curve_phase" in event and event.get("s_curve_phase") is not None:
        return event

    logging.info(f"[ENRICH] Enrichissement de l'événement historique : '{event.get('label')}'")

    year = event.get("year", 1900)
    category = event.get("category", "DEFAUT")

    # 0. Déterminisme (Idem inject_data.py)
    seed_val = zlib.crc32(event.get('label', '').encode('utf-8'))
    random.seed(seed_val)

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
    remedy = max(5, min(95, remedy)) # Borne les valeurs pour éviter les extrêmes 0/100
    poison = 100 - remedy

    # 3. Ajout des champs d'analyse
    event["s_curve_phase"] = s_curve_phase
    event["pharmakon_remedy_percent"] = remedy
    event["pharmakon_poison_percent"] = poison
    # On ne remplace pas les champs existants s'ils sont déjà là (ex: "how" devient "description")
    event["description"] = event.get("description") or event.get("how") or "Description non disponible."
    event["convergences"] = event.get("convergences") or "Analyse simulée : N/A"
    event["grand_filter_analysis"] = event.get("grand_filter_analysis") or "Analyse simulée : N/A"
    event["final_note"] = event.get("final_note") or "Note finale simulée."

    random.seed() # Reset

    return event

def scan_google_news_rss() -> Dict[str, Any] | None:
    """
    Scanne le flux RSS de Google News sur la singularité.
    Chaque article trouvé est passé à `analyze_event` pour une analyse complète.
    """
    logging.info("[SCAN] Scan du flux Google News RSS...")
    # URL pour les actualités en français sur "technological singularity" OR "artificial general intelligence"
    RSS_URL = "https://news.google.com/rss/search?q=%22technological+singularity%22+OR+%22artificial+general+intelligence%22&hl=fr&gl=FR&ceid=FR:fr"

    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        logging.info("... Aucun article trouvé dans le flux RSS.")
        return None

    latest_entry = feed.entries[0] # On prend le plus récent

    return analyze_event(
        entry_title=latest_entry.title,
        entry_summary=latest_entry.summary,
        entry_url=latest_entry.link,
        entry_source=latest_entry.source.get('title', 'Google News')
    )

def scan_doomsday_clock() -> Dict[str, Any]:
    """Crée un événement statique pour l'Horloge de l'Apocalypse."""
    logging.info("[SCAN] Vérification de l'Horloge de l'Apocalypse...")
    # Basé sur la mise à jour de Janvier 2025. [5, 15, 16, 24]
    return {
        "year": 2025.08,
        "value": 48000,
        "label": "Horloge de l'Apocalypse : 89 secondes",
        "category": "☢️ ENTROPIE",
        "whoWhat": "Bulletin of the Atomic Scientists",
        "description": "L'humanité se rapproche de la catastrophe mondiale. Les raisons incluent l'échec à maîtriser les risques nucléaires, les menaces climatiques, le développement non régulé de l'IA, les menaces biologiques et la propagation de la désinformation.",
        "url": "https://thebulletin.org/doomsday-clock/current-time/",
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": True,
        "s_curve_phase": 5,
        "pharmakon_remedy_percent": 5,
        "pharmakon_poison_percent": 95,
        "convergences": "Convergence de toutes les menaces existentielles.",
        "grand_filter_analysis": "C'est littéralement l'indicateur du Grand Filtre.",
        "final_note": "Tic, tac. On se sent plus en sécurité, n'est-ce pas ?"
    }

def scan_simulator() -> Dict[str, Any] | None:
    """
    Simule une veille technologique.
    TODO: Remplacer par une vraie source (flux RSS, API, etc.)
    """
    logging.info("[SCAN] Scan des signaux faibles (Zeitgeist v117)...")

    # Simule une probabilité de découverte
    if random.random() > 0.66:
        logging.info("... Aucun signal significatif détecté ce cycle.")
        return None

    # Pool d'événements plausibles alignés sur la v117
    events_pool = [
        {"l": "Progrès vers la Civilisation Type 1 (Fusion)", "s": "Un nouveau réacteur atteint un Q-plasma de 5 pendant 100 secondes."},
        {"l": "Concept de Noosphère dans le débat public", "s": "Un article viral relance le débat sur la conscience collective planétaire."},
        {"l": "GPT-5 atteint un raisonnement de niveau humain", "s": "Des tests en aveugle montrent des capacités de planification et de créativité indiscernables."},
        {"l": "Puce neuromorphique dépassant le cerveau humain en densité", "s": "Une nouvelle architecture matérielle permet une efficacité énergétique 1000x supérieure."},
    ]

    choice = random.choice(events_pool)

    return analyze_event(
        entry_title=choice['l'],
        entry_summary=choice['s'],
        entry_url="#",
        entry_source="Sentinel Simulator"
    )

def scan_singularity_stage() -> Dict[str, Any] | None:
    """Crée un événement pour matérialiser le stade d'avancement vers la singularité."""
    logging.info("[SCAN] Évaluation du stade de la Singularité...")

    stage = round(random.uniform(0.7, 0.8), 3)

    return analyze_event(
        entry_title=f"Stade Singularité : {stage}",
        entry_summary=f"Évaluation du niveau de proximité global avec une singularité technologique. La valeur de {stage} indique une phase d'accélération avancée, où les signaux faibles deviennent des tendances lourdes.",
        entry_url="#",
        entry_source="Cortex Loom Analysis"
    )


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
    """Exécute un cycle complet de veille, d'enrichissement et d'injection."""
    if not CLOUD_URL:
        logging.critical("[CRITICAL] CLOUD_URL n'est pas définie dans le fichier .env. Arrêt de l'agent.")
        return False
    try:
        # --- ÉTAPE 1: Récupération des données ---
        current_data = get_current_loom()
        if not current_data:
            logging.warning("La base de données est vide ou inaccessible. Cycle interrompu pour le moment.")
            return True # On réessaiera plus tard

        # --- ÉTAPE 2: Enrichissement des données historiques ---
        # On s'assure que chaque événement possède une analyse v117.
        needs_update = False
        processed_data = []
        enriched_count = 0
        for event in current_data:
            original_event_json = json.dumps(event, sort_keys=True)
            enriched_event = enrich_event_if_needed(event)
            processed_data.append(enriched_event)
            enriched_event_json = json.dumps(enriched_event, sort_keys=True)
            if original_event_json != enriched_event_json:
                needs_update = True
                enriched_count += 1
        
        if needs_update:
            logging.info(f"Analyse simulée ajoutée à {enriched_count} événement(s) historique(s).")

        # --- ÉTAPE 3: Scan pour de nouveaux événements ---
        all_new_intel = []

        intel_clock = scan_doomsday_clock()
        if intel_clock: all_new_intel.append(intel_clock)

        intel_stage = scan_singularity_stage()
        if intel_stage: all_new_intel.append(intel_stage)

        if SCAN_MODE == "RSS_NEWS":
            intel_general = scan_google_news_rss()
        else:
            intel_general = scan_simulator()
        if intel_general: all_new_intel.append(intel_general)

        injected_count = 0
        for new_intel in all_new_intel:
            is_duplicate = any(item.get('label') == new_intel['label'] for item in processed_data)
            if is_duplicate:
                logging.info(f"[PAUSE] Doublon détecté ('{new_intel['label']}'). Pas d'injection.")
                continue

            logging.info(f"[NEW] Injection de : '{new_intel['label']}' (Année: {new_intel['year']:.2f})")
            processed_data.append(new_intel)
            injected_count += 1
            needs_update = True

        # --- ÉTAPE 4: Sauvegarde si nécessaire ---
        if needs_update:
            post_updated_loom(processed_data)
        else:
            logging.info("[PAUSE] Aucun nouvel événement ou enrichissement à traiter.")

    except Exception as e:
        logging.error(f"[FATAL] ERREUR INATTENDUE dans le cycle Sentinel : {e}", exc_info=True)
    return True

if __name__ == "__main__":
    logging.info(f"--- SENTINEL EXOCORTEX v117 --- MODE: {SCAN_MODE} ---")

    if SINGLE_RUN:
        logging.info("Mode SINGLE_RUN activé (GitHub Actions). Exécution unique.")
        run_sentinel_cycle()
        exit(0)

    while True:
        should_continue = run_sentinel_cycle()
        if not should_continue: break
        logging.info(f"[SLEEP] En veille pour {SCAN_INTERVAL} secondes...")
        time.sleep(SCAN_INTERVAL)