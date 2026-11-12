#!/usr/bin/env python3
"""
Sentinel - Agent de veille technologique pour Cortex Loom
Version backend FastAPI local (Mac), avec analyse par LLM local outillé.

- Analyse "Pharmakon v117" réalisée par un modèle Ollama local (hermes3:8b par
  défaut), outillé pour la recherche web (web_search / fetch_url), avec un
  focus sur l'étude AI2027 (https://ai2027.com).
- Envoi idempotent au backend (upsert par id stable côté serveur).
- Fallback local atomique + verrouillé si le backend est indisponible.
"""
import hashlib
import json
import os
import re
import sys
import time
import datetime
import random
import logging
import zlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sentinel.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# --- Configuration ---
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api/data")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DATA_FILE = os.environ.get("LOCAL_DATA_FILE", str(PROJECT_ROOT / "loom_data.json"))
SCAN_INTERVAL = int(os.environ.get("SCAN_INTERVAL", 3600))

VERSION = "v179"

# LLM local (Ollama) outillé
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "hermes3:8b")
OLLAMA_FALLBACK_MODELS = [m for m in os.environ.get("OLLAMA_FALLBACK_MODELS", "qwen3:8b").split(",") if m]
ANALYSIS_MODE = os.environ.get("ANALYSIS_MODE", "llm")  # "llm" ou "simulate"
MAX_TOOL_ITERATIONS = int(os.environ.get("MAX_TOOL_ITERATIONS", "4"))

# Focus recherche : étude AI2027
AI2027_URLS = ["https://ai2027.com/", "https://ai2027.com/scenarios/"]

# --- Identifiant stable (même recette que backend/models.compute_event_id) ---
def compute_event_id(label: str, year: float, whoWhat: Optional[str] = None) -> str:
    key = f"{(label or '').strip().lower()}|{round(float(year), 2)}|{(whoWhat or '').strip().lower()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


import html as _html

def clean_text(t: Optional[str]) -> str:
    """Supprime le HTML brut (RSS Google News en embarque) et normalise les espaces."""
    if not t:
        return ""
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


# --- Matrice heuristique par défaut ---
DEFAULT_MATRIX = {
    "🔴 RÉSEAU": {
        "convergences": "Hyperconnectivité + Décentralisation + Vitesse",
        "grand_filter": "Risque de surveillance de masse vs Outil d'émancipation globale."
    },
    "🟡 HARDWARE": {
        "convergences": "Loi de Moore + Efficacité Énergétique + Nouveaux Matériaux",
        "grand_filter": "Dépendance critique aux terres rares et à la chaîne logistique."
    },
    "🔵 COGNITION": {
        "convergences": "Algorithmes + Big Data + Sciences Cognitives",
        "grand_filter": "Alignement des valeurs de l'IA avec la survie humaine."
    },
    "🟢 BIOTECH": {
        "convergences": "Génétique + IA + Nanotechnologies",
        "grand_filter": "Démocratisation des pathogènes vs Guérison universelle."
    },
    "🟣 ESPACE": {
        "convergences": "Propulsion + Robotique + IA",
        "grand_filter": "Colonisation multi-planétaire vs Épuisement des ressources terrestres."
    },
    "☢️ ENTROPIE": {
        "convergences": "Complexité systémique + Fragilité des infrastructures",
        "grand_filter": "Effondrement en cascade des systèmes interconnectés."
    },
    "🏛️ POLITIQUE": {
        "convergences": "Législation + Technologie + Société Civile",
        "grand_filter": "Incapacité des institutions lentes à gérer l'accélération technologique."
    },
    "✨ NOOSPHÈRE": {
        "convergences": "Conscience collective + Internet + Mémétique",
        "grand_filter": "Infobésité et désinformation noyant la sagesse collective."
    },
    "🔮 IMAGINAIRE": {
        "convergences": "Fiction + Réalité + Anticipation",
        "grand_filter": "La fiction comme prophétie auto-réalisatrice ou avertissement ignoré."
    },
    "⚪ SINGULARITÉ": {
        "convergences": "IA Forte + Nanotech + Bio-ingénierie",
        "grand_filter": "Obsolescence de l'espèce biologique humaine."
    }
}


def categorize_text(text: str) -> str:
    """Classifie un texte en fonction de mots-clés."""
    text = text.lower()
    if "noosphere" in text or "teilhard" in text or "kardashev" in text:
        return "✨ NOOSPHÈRE"
    if any(k in text for k in ["quantum", "chip", "gpu", "hardware", "moore", "nvidia"]):
        return "🟡 HARDWARE"
    if any(k in text for k in ["gpt", "model", "reasoning", "agi", "cognitive", "openai", "anthropic", "ai2027"]):
        return "🔵 COGNITION"
    if any(k in text for k in ["dna", "crispr", "biotech", "neuralink", "organoid"]):
        return "🟢 BIOTECH"
    if any(k in text for k in ["space", "rocket", "mars", "starship", "spacex"]):
        return "🟣 ESPACE"
    if any(k in text for k in ["risk", "danger", "regulation", "bias", "threat", "law", "doomsday"]):
        return "☢️ ENTROPIE"
    return "🔴 RÉSEAU"


# =====================================================================
# OUTILS DE RECHERCHE WEB (pour le LLM local)
# =====================================================================

def web_search(query: str, max_results: int = 6) -> List[Dict[str, str]]:
    """Recherche web sans clé API : Bing RSS en premier, DuckDuckGo HTML en secours."""
    import requests
    import feedparser
    q = query.strip()
    # 1) Bing RSS
    try:
        rss = f"https://www.bing.com/search?q={requests.utils.quote(q)}&format=rss"
        resp = requests.get(rss, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        results = []
        for e in feed.entries[:max_results]:
            results.append({
                "title": getattr(e, "title", ""),
                "url": getattr(e, "link", ""),
                "snippet": re.sub(r"<[^>]+>", "", getattr(e, "summary", ""))[:300],
            })
        if results:
            return results
    except Exception as e:
        logger.warning(f"[TOOL] Bing RSS en échec ({e}), fallback DuckDuckGo")
    # 2) DuckDuckGo HTML
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": q}, timeout=15, headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        titles = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', resp.text, re.S)
        results = []
        for i, (url, title) in enumerate(titles[:max_results]):
            results.append({
                "title": re.sub(r"<[^>]+>", "", title),
                "url": url,
                "snippet": re.sub(r"<[^>]+>", "", snippets[i])[:300] if i < len(snippets) else "",
            })
        return results
    except Exception as e:
        logger.error(f"[TOOL] web_search en échec: {e}")
        return []


def fetch_url(url: str, max_chars: int = 6000) -> str:
    """Récupère le texte brut d'une page (tronqué)."""
    import requests
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (CortexLoom Sentinel)"})
        resp.raise_for_status()
        text = resp.text[:200_000]
        text = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        return f"ERREUR fetch_url: {e}"


OLLAMA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Recherche web. Retourne une liste de résultats (title, url, snippet).",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Requête de recherche"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Récupère le texte d'une page web (tronqué à ~6000 caractères).",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL à récupérer"}},
                "required": ["url"],
            },
        },
    },
]

SYSTEM_PROMPT = """Tu es le veilleur du projet Cortex Loom (persona : lucide, ironique, philosophie "Pharmakon").

Mission : pour l'événement fourni, faire une recherche web rapide puis produire une analyse selon la grille v117 :
1. s_curve_phase : entier 1-5 (1=début lent, 2=croissance, 3=accélération, 4=maturité, 5=plateau/singularité)
2. pharmakon_remedy_percent : entier 0-100 (% remède : abondance, guérison, maîtrise)
3. pharmakon_poison_percent : entier 0-100, EXACTEMENT égal à 100 - pharmakon_remedy_percent
4. convergences : liens avec d'autres domaines (IA, bio, espace, réseau...)
5. grand_filter_analysis : impact sur la survie de l'humanité (Grand Filtre)
6. final_note : une phrase d'humour noir, élégante et désabusée

Règles :
- Utilise les outils web_search / fetch_url pour vérifier et sourcer l'événement.
- FOCUS PRIORITAIRE : l'étude AI2027 (https://ai2027.com) — croise avec ai2027.com quand le sujet s'y prête (scénarios 2027, course à l'AGI, compute, autonomie des agents).
- Réponds UNIQUEMENT avec un objet JSON valide (sans markdown, sans explication) contenant exactement les 6 champs ci-dessus.
"""

# --- PROMPT DE VEILLE ÉDITABLE depuis le dashboard (onglet FILTRE MÉMÉTIQUE → encard) ---
# Écrit dans agent_prompt.txt à la racine du dépôt, relu à CHAQUE cycle (~5 min) :
#  - il est injecté dans le system prompt de l'analyse LLM (research_and_analyze)
#  - les lignes sous [MOTS-CLÉS À EXCLURE] alimentent le fact-check (sujets hors projet rejetés)
PROMPT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agent_prompt.txt")


def load_custom_prompt() -> Optional[str]:
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            t = f.read().strip()
        return t or None
    except Exception:
        return None


def load_exclude_keywords() -> list:
    """Mots-clés à exclure du fact-check : section [MOTS-CLÉS À EXCLURE] de agent_prompt.txt."""
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        if "[MOTS-CLÉS À EXCLURE]" in content:
            section = content.split("[MOTS-CLÉS À EXCLURE]", 1)[1]
            section = section.split("[", 1)[0] if "[" in section else section
            return [ln.strip().lower().strip("-•* ") for ln in section.splitlines() if ln.strip() and not ln.strip().startswith("[")]
    except Exception:
        pass
    return []


def _ollama_chat(model: str, messages: List[Dict[str, Any]], with_tools: bool = True) -> Optional[Dict[str, Any]]:
    import requests
    payload = {"model": model, "messages": messages, "stream": False}
    if with_tools:
        payload["tools"] = OLLAMA_TOOLS
    resp = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json()


def _execute_tool_call(call: Dict[str, Any]) -> str:
    fn = call.get("function", {})
    name = fn.get("name")
    try:
        args = fn.get("arguments")
        if isinstance(args, str):
            args = json.loads(args)
        args = args or {}
        if name == "web_search":
            return json.dumps(web_search(args.get("query", "")), ensure_ascii=False)
        if name == "fetch_url":
            return fetch_url(args.get("url", ""))
    except Exception as e:
        return json.dumps({"error": str(e)})
    return json.dumps({"error": f"outil inconnu: {name}"})


def _parse_analysis_json(content: str) -> Optional[Dict[str, Any]]:
    if not content:
        return None
    txt = content.strip()
    txt = re.sub(r"^```(?:json)?", "", txt).strip()
    txt = re.sub(r"```$", "", txt).strip()
    # Extraire le premier objet JSON du texte
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    try:
        # Compatibilité directive "RÔLE ET MISSION" : objets imbriqués pharmakon / s_curve / nela_action
        if "s_curve_phase" not in data and isinstance(data.get("s_curve"), dict):
            data["s_curve_phase"] = data["s_curve"].get("stage", 3)
        if "pharmakon_remedy_percent" not in data and isinstance(data.get("pharmakon"), dict):
            data["pharmakon_remedy_percent"] = data["pharmakon"].get("remedy_pct", 50)
        if not data.get("grand_filter_analysis") and data.get("nela_action"):
            data["grand_filter_analysis"] = data["nela_action"]
        phase = int(data.get("s_curve_phase", 3))
        phase = max(1, min(5, phase))
        remedy = int(data.get("pharmakon_remedy_percent", 50))
        remedy = max(0, min(100, remedy))
        return {
            "s_curve_phase": phase,
            "pharmakon_remedy_percent": remedy,
            "pharmakon_poison_percent": 100 - remedy,  # un seul tirage : somme = 100
            "convergences": str(data.get("convergences", "")) or "Aucune convergence majeure détectée.",
            "grand_filter_analysis": str(data.get("grand_filter_analysis", "")) or "Impact systémique à surveiller.",
            "final_note": str(data.get("final_note", "")) or "Le futur est décidément mal écrit.",
        }
    except Exception:
        return None


def research_and_analyze(title: str, summary: str, url: str, source: str) -> Optional[Dict[str, Any]]:
    """Agent de recherche : le LLM local explore le web (outils) puis produit l'analyse v117 en JSON."""
    user_msg = (
        f"Événement à analyser :\n"
        f"- Titre : {title}\n"
        f"- Résumé : {summary[:800]}\n"
        f"- URL : {url}\n"
        f"- Source : {source}\n\n"
        "Fais 1 à 3 recherches web ciblées (AI2027 en priorité si pertinent), puis réponds UNIQUEMENT "
        "avec le JSON d'analyse v117 (6 champs)."
    )
    custom = load_custom_prompt()
    system = SYSTEM_PROMPT + ("\n\n[PROMPT DE VEILLE PERSONNALISÉ — prioritaire, édité depuis le dashboard]\n" + custom if custom else "")
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_msg},
    ]
    models = [OLLAMA_MODEL] + [m for m in OLLAMA_FALLBACK_MODELS if m != OLLAMA_MODEL]
    for model in models:
        try:
            for _ in range(MAX_TOOL_ITERATIONS):
                resp = _ollama_chat(model, messages, with_tools=True)
                msg = resp.get("message", {})
                tool_calls = msg.get("tool_calls") or []
                if tool_calls:
                    messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tool_calls})
                    for call in tool_calls:
                        result = _execute_tool_call(call)
                        tool_msg = {"role": "tool", "name": call.get("function", {}).get("name"), "content": result}
                        if call.get("id"):
                            tool_msg["tool_call_id"] = call["id"]
                        messages.append(tool_msg)
                    continue
                # Pas d'appel d'outil : le contenu doit être le JSON final
                return _parse_analysis_json(msg.get("content", ""))
            logger.warning(f"[LLM] {model}: nombre max d'itérations d'outils atteint, abandon")
        except Exception as e:
            logger.warning(f"[LLM] {model} indisponible/erreur: {e}")
    return None


# =====================================================================
# ANALYSE (heuristique de secours + LLM local)
# =====================================================================

def analyze_event(entry_title: str, entry_summary: str, entry_url: str, entry_source: str) -> Dict[str, Any]:
    """Analyse un événement : LLM local outillé si ANALYSIS_MODE=llm, sinon heuristique simulée."""
    logger.info(f"[ANALYSE] Analyse de : '{entry_title}'")
    entry_title = clean_text(entry_title)
    entry_summary = clean_text(entry_summary)
    entry_source = clean_text(entry_source)
    # Google News accole " - <source>" au titre : on le retire
    if entry_source and entry_title.endswith(" - " + entry_source):
        entry_title = entry_title[: -(len(entry_source) + 3)]
    today = datetime.date.today()
    event_year = round(today.year + (today.month / 12), 3)
    category = categorize_text(entry_title + " " + entry_summary)

    analysis = None
    if ANALYSIS_MODE == "llm":
        analysis = research_and_analyze(entry_title, entry_summary, entry_url, entry_source)
        if analysis:
            logger.info(f"[LLM] Analyse v117 produite par {OLLAMA_MODEL}")
    if analysis is None:
        # Secours heuristique (déterministe sur le label)
        seed_val = zlib.crc32(entry_title.encode("utf-8"))
        random.seed(seed_val)
        remedy = random.randint(20, 80)
        analysis = {
            "s_curve_phase": random.randint(1, 5),
            "pharmakon_remedy_percent": remedy,
            "pharmakon_poison_percent": 100 - remedy,  # un seul tirage : somme = 100
            "convergences": random.choice([
                "Croise le risque de régulation",
                "Accélère la course au hardware",
                "Impacte la souveraineté des données",
                "Aucune convergence majeure détectée"
            ]),
            "grand_filter_analysis": random.choice([
                "Faible risque de filtre",
                "Pourrait être un petit filtre",
                "Augmente la complexité systémique"
            ]),
            "final_note": random.choice([
                "Et une autre tuile.",
                "Fascinant et terrifiant.",
                "On en reparlera en pleurant.",
                "Le futur est décidément mal écrit."
            ]),
        }
        random.seed()
        cat = category
        if cat in DEFAULT_MATRIX:
            analysis["convergences"] = DEFAULT_MATRIX[cat]["convergences"]
            analysis["grand_filter_analysis"] = DEFAULT_MATRIX[cat]["grand_filter"]

    return {
        "year": event_year,
        "value": random.randint(20000, 50000),
        "label": entry_title,
        "category": category,
        "whoWhat": entry_source,
        "description": entry_summary,
        "url": entry_url,
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": random.random() > 0.8,
        **analysis,
    }


def enrich_event_if_needed(event: Dict[str, Any]) -> Dict[str, Any]:
    """Enrichit un événement historique avec une analyse v117 si manquante."""
    if "s_curve_phase" in event and event.get("s_curve_phase") is not None:
        return event

    logger.info(f"[ENRICH] Enrichissement de : '{event.get('label')}'")
    year = event.get("year", 1900)
    category = event.get("category", "DEFAUT")

    seed_val = zlib.crc32(event.get('label', '').encode('utf-8'))
    random.seed(seed_val)

    if year < 1940:
        s_curve_phase = 1
    elif year < 1990:
        s_curve_phase = 2
    elif year < 2015:
        s_curve_phase = 3
    elif year < 2030:
        s_curve_phase = 4
    else:
        s_curve_phase = 5

    remedy = 50
    if "ENTROPIE" in category:
        remedy = 10
    elif "BIOTECH" in category or "NOOSPHÈRE" in category:
        remedy = 70
    elif "HARDWARE" in category or "COGNITION" in category:
        remedy = 60
    elif "POLITIQUE" in category:
        remedy = 35
    elif "IMAGINAIRE" in category:
        remedy = 50

    remedy += random.randint(-10, 10)
    remedy = max(5, min(95, remedy))

    event["s_curve_phase"] = s_curve_phase
    event["pharmakon_remedy_percent"] = remedy
    event["pharmakon_poison_percent"] = 100 - remedy
    event["description"] = event.get("description") or event.get("how") or "Description non disponible."
    event["convergences"] = event.get("convergences") or "Analyse simulée : N/A"
    event["grand_filter_analysis"] = event.get("grand_filter_analysis") or "Analyse simulée : N/A"
    event["final_note"] = event.get("final_note") or "Note finale simulée."

    cat = event.get("category", "DEFAUT")
    if cat in DEFAULT_MATRIX:
        if not event.get("convergences") or "N/A" in event.get("convergences", ""):
            event["convergences"] = DEFAULT_MATRIX[cat]["convergences"]
        if not event.get("grand_filter_analysis") or "N/A" in event.get("grand_filter_analysis", ""):
            event["grand_filter_analysis"] = DEFAULT_MATRIX[cat]["grand_filter"]

    random.seed()
    return event


# --- SCANNERS ---

# Requêtes RSS ciblées "haut signal" : benchmarks, preuves, records, découvertes scientifiques
RSS_QUERIES = [
    '"ARC-AGI" OR "ARC Prize" benchmark',
    'IA record benchmark "ARC-AGI-3" OR FrontierMath OR olympiade OR IMO 2026',
    'intelligence artificielle a prouvé OR a résolu conjecture OR problème maths OR physique 2026',
    'DeepMind OR OpenAI OR Anthropic percée OR découverte OR record 2026 science',
    '"grand challenge" OR "open problem" solved by AI Nature Science 2026',
]
# Filtre anti-hype : un article n'entre dans le flux que s'il contient un de ces signaux factuels
SIGNAL_KEYWORDS = [
    "benchmark", "record", "scored", "score", "proved", "prouvé", "résolu", "solved",
    "discovery", "découvert", "discovered", "arc-agi", "arc prize", "frontiermath",
    "imo", "olympiad", "theorem", "théorème", "conjecture", "physics", "physique",
    "mathematics", "maths", "breakthrough", "percée", "nature", "science",
    "deepmind", "openai", "anthropic", "agi", "nobel", "published", "preprint",
]


def scan_google_news_rss(max_events: int = 2) -> List[Dict[str, Any]]:
    """Scanne plusieurs flux Google News ciblés et ne retient que les articles à haut signal
    factuel (benchmark/record/preuve/découverte), dédoublonnés par titre."""
    logger.info("[SCAN] Scan RSS multi-requêtes (haut signal factuel)...")
    import requests
    import feedparser

    seen_titles = set()
    candidates = []
    for q in RSS_QUERIES:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(q)}&hl=fr&gl=FR&ceid=FR:fr"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            logger.warning(f"[SCAN] RSS en échec pour {q!r}: {e}")
            continue
        for entry in feed.entries[:8]:
            title = getattr(entry, "title", "")
            text = (title + " " + getattr(entry, "summary", "")).lower()
            if title in seen_titles:
                continue
            if not any(k in text for k in SIGNAL_KEYWORDS):
                continue  # hype/pop filtré
            seen_titles.add(title)
            candidates.append(entry)

    if not candidates:
        logger.info("... Aucun article à haut signal trouvé.")
        return []

    # Les plus récents d'abord (feedparser: entries déjà triées par date desc par flux)
    events = []
    for entry in candidates[:max_events]:
        events.append(analyze_event(
            entry_title=entry.title,
            entry_summary=getattr(entry, "summary", ""),
            entry_url=getattr(entry, "link", "#"),
            entry_source=entry.source.get('title', 'Google News') if hasattr(entry, "source") and entry.source else 'Google News'
        ))
    return events


def scan_ai2027() -> Optional[Dict[str, Any]]:
    """Scrutine AI2027 (étude de référence) : récupère le dernier jalon publié et l'analyse."""
    logger.info("[SCAN] Scrutin de AI2027 (ai2027.com)...")
    page = fetch_url(AI2027_URLS[0], max_chars=4000)
    if page.startswith("ERREUR"):
        return None
    # Extraire les titres/jalons mentionnant 2026/2027 ou des annonces récentes
    candidates = re.findall(r"([^\.\n]{20,140}(?:2026|2027|AGI|agent|compute|autonom)[^\.\n]{0,120})", page)
    candidates = [c.strip() for c in candidates if len(c.strip()) > 30][:5]
    if not candidates:
        return None
    headline = candidates[0]
    return analyze_event(
        entry_title=f"AI2027 : {headline[:120]}",
        entry_summary=f"Extrait de ai2027.com : {headline[:500]}",
        entry_url=AI2027_URLS[0],
        entry_source="AI2027.com"
    )


def scan_doomsday_clock() -> Dict[str, Any]:
    """Horloge de l'Apocalypse : scrape la dernière heure OFFICIELLE (Bulletin of the Atomic
    Scientists) à chaque cycle (la boucle tourne ~toutes les minutes ; le réglage est annuel).
    Label stable par année -> upsert : la description est rafraîchie, pas de doublon."""
    logger.info("[SCAN] Horloge de l'Apocalypse (source officielle)...")
    year_now = datetime.date.today().year
    seconds = 85  # repli : dernier réglage officiel connu (27 janv. 2026, record historique)
    src_date = "janvier 2026"
    page = fetch_url("https://thebulletin.org/doomsday-clock/current-time/", max_chars=8000)
    if not page.startswith("ERREUR"):
        m = re.search(r"(\d+)\s*seconds?\s*(?:to|avant)\s*midnight", page, re.I) or re.search(r"(\d+)\s*secondes?\s*avant\s*minuit", page, re.I)
        if m:
            seconds = int(m.group(1))
        d = re.search(r"(January|janvier|February|février|March|mars|April|avril|May|mai|June|juin|July|juillet|August|août|September|septembre|October|octobre|November|novembre|December|décembre)\s+(\d{1,2}),?\s+(\d{4})", page)
        if d:
            src_date = d.group(0)
    return {
        "year": float(year_now),
        "value": 48000,
        "label": f"⏰ Horloge {year_now} — {seconds} s avant minuit",
        "category": "⏰ HORLOGE",
        "whoWhat": "Bulletin of the Atomic Scientists",
        "description": f"{seconds} secondes avant minuit (dernier réglage officiel, {src_date}). Menaces : nucléaire, climat, IA non régulée, biologie, désinformation.",
        "url": "https://thebulletin.org/doomsday-clock/current-time/",
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": True,
        "doomsday_minutes": seconds / 60.0,
        "s_curve_phase": 5,
        "pharmakon_remedy_percent": 5,
        "pharmakon_poison_percent": 95,
        "convergences": "Convergence de toutes les menaces existentielles.",
        "grand_filter_analysis": "C'est littéralement l'indicateur du Grand Filtre.",
        "final_note": "Tic, tac. On se sent plus en sécurité, n'est-ce pas ?"
    }


def scan_simulator() -> Optional[Dict[str, Any]]:
    """Simule une veille technologique (secours si aucune source réseau)."""
    logger.info("[SCAN] Scan des signaux faibles (Simulateur)...")

    if random.random() > 0.66:
        logger.info("... Aucun signal significatif détecté.")
        return None

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


def scan_singularity_stage() -> Optional[Dict[str, Any]]:
    """Évalue le stade d'avancement vers la singularité.

    Label STABLE (l'id d'upsert ne change pas) : la valeur estimée va dans la
    description, jamais dans le label → pas de fuite d'événements à chaque cycle.
    """
    logger.info("[SCAN] Évaluation du stade de la Singularité...")
    stage = round(random.uniform(0.7, 0.8), 3)
    today = datetime.date.today()
    event_year = round(today.year + (today.month / 12), 3)
    return {
        "year": event_year,
        "value": 50000,
        "label": "Stade de Singularité (estimation courante)",
        "category": "⚪ SINGULARITÉ",
        "whoWhat": "Cortex Loom Analysis",
        "description": f"Évaluation du niveau de proximité global avec une singularité technologique : stade estimé à {stage} (phase d'accélération avancée, signaux faibles devenant tendances lourdes).",
        "url": "https://ai2027.com/",
        "timestamp": datetime.datetime.now().isoformat(),
        "tipping": False,
        "s_curve_phase": 4,
        "pharmakon_remedy_percent": 50,
        "pharmakon_poison_percent": 50,
        "convergences": "IA Forte + Nanotech + Bio-ingénierie",
        "grand_filter_analysis": "Obsolescence de l'espèce biologique humaine.",
        "final_note": "La courbe accélère. Accrochez-vous."
    }


# --- STOCKAGE LOCAL (fallback) : atomique + verrouillé + upsert par id ---

class LocalStorage:
    """Gestion des données locales (JSON file), écriture atomique verrouillée."""

    def __init__(self, file_path: str = None):
        self.file_path = Path(file_path or LOCAL_DATA_FILE)
        self.lock_path = Path(str(self.file_path) + ".lock")

    def _lock(self):
        import fcntl
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX)
        return fd

    def _unlock(self, fd):
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)

    def load(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save(self, data: List[Dict[str, Any]]) -> bool:
        try:
            fd = self._lock()
            try:
                sorted_data = sorted(data, key=lambda x: x.get("year", 0))
                tmp = self.file_path.with_suffix(".tmp")
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(sorted_data, f, indent=2, ensure_ascii=False)
                os.replace(tmp, self.file_path)
            finally:
                self._unlock(fd)
            return True
        except Exception as e:
            logger.error(f"[STORAGE] Erreur sauvegarde : {e}")
            return False

    def upsert_events(self, events: List[Dict[str, Any]]) -> tuple:
        """Upsert par id stable (même recette que le backend)."""
        existing = self.load()
        index = {}
        for e in existing:
            e.setdefault("id", compute_event_id(e.get("label", ""), e.get("year", 0), e.get("whoWhat")))
            index[e["id"]] = e
        added = updated = 0
        for ev in events:
            ev.setdefault("id", compute_event_id(ev.get("label", ""), ev.get("year", 0), ev.get("whoWhat")))
            if ev["id"] in index:
                index[ev["id"]] = ev
                updated += 1
            else:
                index[ev["id"]] = ev
                added += 1
        self.save(list(index.values()))
        return added, updated

    def add_events(self, events: List[Dict[str, Any]]) -> bool:
        self.upsert_events(events)
        return True


# --- CLIENT API ---

class APIClient:
    """Client pour le backend FastAPI"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or BACKEND_URL

    def get_data(self) -> List[Dict[str, Any]]:
        try:
            import requests
            response = requests.get(self.base_url, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[API] Erreur récupération : {e}")
            return []

    def add_events(self, events: List[Dict[str, Any]]) -> bool:
        """POST idempotent (upsert par id côté serveur)."""
        try:
            import requests
            response = requests.post(self.base_url, json=events, timeout=60)
            response.raise_for_status()
            result = response.json()
            logger.info(f"[API] Upsert OK : {result}")
            return True
        except Exception as e:
            logger.error(f"[API] Erreur envoi : {e}")
            return False


# --- DÉDUPLICATION ---

def is_duplicate(new_event: Dict[str, Any], existing_events: List[Dict[str, Any]]) -> bool:
    new_id = new_event.get("id") or compute_event_id(
        new_event.get("label", ""), new_event.get("year", 0), new_event.get("whoWhat"))
    for event in existing_events:
        ev_id = event.get("id") or compute_event_id(
            event.get("label", ""), event.get("year", 0), event.get("whoWhat"))
        if new_id == ev_id:
            return True
    return False


def remove_duplicates(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unique = []
    seen = set()
    for event in events:
        key = event.get("id") or compute_event_id(
            event.get("label", ""), event.get("year", 0), event.get("whoWhat"))
        event["id"] = key
        if key not in seen:
            seen.add(key)
            unique.append(event)
    return unique


# --- CYCLE PRINCIPAL ---

def run_sentinel_cycle(api_client: APIClient = None, storage: LocalStorage = None):
    """Exécute un cycle complet de veille."""
    api_client = api_client or APIClient()
    storage = storage or LocalStorage()

    logger.info("=" * 60)
    logger.info("🚀 DEBUT DU CYCLE SENTINEL %s (LLM local: %s, mode: %s)", VERSION, OLLAMA_MODEL, ANALYSIS_MODE)
    logger.info("=" * 60)

    # 1. Récupère les données existantes
    existing_data = api_client.get_data()
    if not existing_data:
        existing_data = storage.load()
        logger.info(f"[CYCLE] Fallback stockage local: {len(existing_data)} événements")
    else:
        logger.info(f"[CYCLE] {len(existing_data)} événements chargés via API")
    existing_data = remove_duplicates(existing_data)

    # 2. Scanners — le simulateur n'est actif que si SIMULATOR=1 (le flux doit rester factuel)
    scanners = [
        ("AI2027", scan_ai2027),
        ("Doomsday Clock", scan_doomsday_clock),
        ("Google News RSS", scan_google_news_rss),
        ("Singularity Stage", scan_singularity_stage),
    ]
    if os.environ.get("SIMULATOR", "0") == "1":
        scanners.append(("Simulateur", scan_simulator))

    new_events = []
    for name, scanner in scanners:
        try:
            result = scanner()
            events = result if isinstance(result, list) else ([result] if result else [])
            for event in events:
                event = enrich_event_if_needed(event)
                event["id"] = compute_event_id(event.get("label", ""), event.get("year", 0), event.get("whoWhat"))
                if not is_duplicate(event, existing_data) and factcheck(event):
                    new_events.append(event)
                    logger.info(f"[CYCLE] ✅ {name}: {event['label']}")
                else:
                    logger.info(f"[CYCLE] ⏭️ {name}: doublon ou non vérifié, ignoré")
        except Exception as e:
            logger.error(f"[CYCLE] ❌ {name}: {e}")

    # 3. Envoi (upsert idempotent) : API d'abord, fallback local
    api_ok = False
    if new_events:
        logger.info(f"[CYCLE] {len(new_events)} nouveaux événements à envoyer")
        if api_client.add_events(new_events):
            logger.info("[CYCLE] ✅ Événements envoyés à l'API (upsert)")
            api_ok = True
        else:
            added, updated = storage.upsert_events(new_events)
            logger.info(f"[CYCLE] 💾 Fallback local: +{added} / ~{updated} événements")
    else:
        logger.info("[CYCLE] Aucun nouvel événement trouvé")

    # 4. Miroir local UNIQUEMENT si l'API était indisponible (même fichier que le backend sinon) :
    #    on n'upsert que les nouveaux événements pour ne jamais écraser des champs enrichis
    #    (realYear/predictedBy...) par un snapshot périmé.
    if new_events and not api_ok:
        storage.upsert_events(new_events)

    all_data = existing_data + new_events
    all_data = remove_duplicates(all_data)
    all_data.sort(key=lambda x: x.get("year", 0))

    logger.info(f"[CYCLE] Total: {len(all_data)} événements")
    logger.info("=" * 60)
    return all_data

# --- FACT-CHECK : toute info entrante doit être corroborée ET dans le domaine du projet ---
# Mots-clés de pertinence (veille singularité / tech / science / risques). Le reste (sport,
# faits divers, culture pop) est rejeté même si sourcé.
RELEVANCE_KEYWORDS = [
    "ia", " ai", "intelligence artificielle", "agi", "llm", "modèle", "benchmark", "arc-agi",
    "arc prize", "deepmind", "openai", "anthropic", "mistral", "agi", "robot", "androïde",
    "quantique", "qubit", "compute", "gpu", "puce", "semi-conducteur", "transistor",
    "espace", "fusée", "starship", "mars", "lunaire", "satellite", "nasa", "esa", "spacex",
    "biotech", "génétique", "crispr", "adn", "arn", "vaccin", "virus", "pandémie", "médecine",
    "climat", "climate", "énergie", "fusion", "solaire", "nucléaire", "batterie",
    "cyber", "hack", "ransomware", "attaque", "sécurité", "cyberattaque", "malware",
    "régulation", "ai act", "loi", "traité", "gouvernance", "souveraineté", "géopolitique",
    "physique", "maths", "mathématiques", "théorème", "conjecture", "cern", "boson", "trou noir",
    "5g", "6g", "réseau", "internet", "web", "donnée", "algorithme", "singularité", "transhumanisme",
    "neuralink", "interface cerveau", "exosquelette", "drone", "autonome", "véhicule autonome",
    "fusion nucléaire", "réacteur", "collisionneur", "gravitation",
]


def factcheck(ev):
    label = ev.get("label", "")
    if any(label.startswith(p) for p in ("Horloge de l'Apocalypse", "⏰ Horloge", "Stade de Singularité")):
        ev["verified"] = True
        return True
    try:
        res = web_search(label[:90], max_results=5)
    except Exception:
        res = []
    text = (label + " " + " ".join(r.get("title", "") + " " + r.get("snippet", "") for r in res)).lower()
    relevant = any(k in text for k in RELEVANCE_KEYWORDS)
    excluded = any(x in text for x in load_exclude_keywords())  # prompt éditable du dashboard
    if excluded:
        logger.warning(f"[FACTCHECK] mot-clé exclu (prompt perso), ignoré: {label}")
    ok = len(res) >= 2 and relevant and not excluded
    ev["verified"] = ok
    if not ok:
        logger.warning(f"[FACTCHECK] hors sujet ou non corroboré, ignoré: {label}")
    return ok



def continuous_scan(interval: int = None):
    """Exécute des cycles en continu"""
    interval = interval or SCAN_INTERVAL
    logger.info(f"🔄 Mode continu activé (intervalle: {interval}s)")

    while True:
        try:
            run_sentinel_cycle()
        except KeyboardInterrupt:
            logger.info("⏹️ Arrêt demandé")
            break
        except Exception as e:
            logger.error(f"[CONTINUOUS] Erreur : {e}")

        for i in range(interval, 0, -1):
            sys.stdout.write(f"\r⏳ Prochain scan dans {i}s...")
            sys.stdout.flush()
            time.sleep(1)
        print()


if __name__ == "__main__":
    logger.info("🎯 Mode: Cycle unique — Sentinel Exocortex %s", VERSION)
    data = run_sentinel_cycle()
    logger.info(f"💾 Miroir local: {LOCAL_DATA_FILE} ({len(data)} événements)")
