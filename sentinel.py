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

    TODO: Remplacer l'analyse simulée par un appel à une IA externe en utilisant le prompt suivant :
    ---
    Tu es un veilleur technologique lucide et ironique, chargé de détecter les signaux faibles annonçant l'avènement parallèle de plusieurs singularités : mathématiques (preuves automatisées), physique (énergie infinie, quantique scalable), biologie (programmable, longévité), IA physique (embodied, world models), robotique (humanoïdes généralisables), et leurs convergences.
    Nous sommes dans l'ère des pharmakons : chaque avancée est à la fois remède et poison, messager ambivalent de la singularité.
    Pour tout événement, post, papier ou déclaration que je te soumets :

    1. Résume brièvement le signal et son contexte.
    2. Évalue sa position sur la courbe en S de la ou des singularités concernées (phase 1 à 5 : début lent, inflexion, accélération, plateau, déclin éventuel).
    3. Analyse-le comme pharmakon : attribue un pourcentage approximatif de potentiel médicamenteux (remède : abondance, guérison, maîtrise) et de potentiel toxique (poison : misalignment, perte de contrôle, amplification des égoïsmes humains, risque existentiel). Justifie précisément.
    4. Indique les convergences avec d'autres singularités et les risques/bénéfices pour l'humanité sur la crête du Grand Filtre.
    5. Termine par une note d'humour noir, élégante et désabusée, sans excès.

    Ton style : français précis, neutre, avec une ironie subtile et un soupçon de cynisme à la Desproges. Structure claire, sans anglicismes inutiles.
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
    """Exécute un cycle complet de veille et d'injection."""
    if not CLOUD_URL:
        logging.critical("[CRITICAL] CLOUD_URL n'est pas définie dans le fichier .env. Arrêt de l'agent.")
        return False # Signal pour arrêter la boucle principale
    try:
        all_new_intel = []

        # 1. Scan spécifique de l'horloge
        intel_clock = scan_doomsday_clock()
        if intel_clock:
            all_new_intel.append(intel_clock)

        # 2. Scan du stade de la singularité
        intel_stage = scan_singularity_stage()
        if intel_stage:
            all_new_intel.append(intel_stage)

        # 3. Scan général (mode RSS ou SIMULATOR)
        if SCAN_MODE == "RSS_NEWS":
            intel_general = scan_google_news_rss()
        else:
            intel_general = scan_simulator()

        if intel_general:
            all_new_intel.append(intel_general)

        if not all_new_intel:
            logging.info("[PAUSE] Aucun nouvel événement à traiter.")
            return True

        current_data = get_current_loom()

        injected_count = 0
        for new_intel in all_new_intel:
            is_duplicate = any(item.get('label') == new_intel['label'] for item in current_data)
            if is_duplicate:
                logging.info(f"[PAUSE] Doublon détecté ('{new_intel['label']}'). Pas d'injection.")
                continue

            logging.info(f"[NEW] Injection de : '{new_intel['label']}' (Année: {new_intel['year']:.2f})")
            current_data.append(new_intel)
            injected_count += 1

        if injected_count > 0:
            post_updated_loom(current_data)

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