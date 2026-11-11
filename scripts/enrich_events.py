#!/usr/bin/env python3
"""Enrichissement de masse des événements pauvres (sans description / sans source).
LLM local Ollama (hermes3:8b) par lots de 8 -> JSON {label: {description, whoWhat}}.
Fallback par catégorie si le LLM échoue. Verrouillé, idempotent.
Usage: backend/venv/bin/python scripts/enrich_events.py [--max N]"""
import fcntl
import json
import os
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "hermes3:8b")

FALLBACK = {
    "COGNITION": ("Avancée majeure de l'intelligence artificielle.", "Communauté scientifique"),
    "HARDWARE": ("Progrès matériel marquant.", "Industrie / laboratoires"),
    "RÉSEAU": ("Étape clé des réseaux et de la communication.", "Industrie / institutions"),
    "ESPACE": ("Jalon de l'exploration spatiale.", "Agence spatiale"),
    "BIOTECH": ("Avancée en biotechnologie.", "Laboratoire / industrie"),
    "MÉDECINE": ("Progrès médical majeur.", "Médecine / recherche"),
    "POLITIQUE": ("Événement politique structurant.", "Institutions"),
    "ENTROPIE": ("Crise ou risque systémique majeur.", "Observateurs internationaux"),
    "RISQUES CYBER": ("Cyberattaque majeure.", "CERT / sécurité"),
    "ROBOTIQUE": ("Jalon de la robotique.", "Industrie / laboratoires"),
    "IMAGINAIRE": ("Œuvre de fiction influente.", "Auteur / studio"),
    "NOOSPHÈRE": ("Tournant de la conscience collective.", "Médias / penseurs"),
    "SINGULARITÉ": ("Étape vers la singularité technologique.", "Cortex Loom Analysis"),
}


def cat_key(cat):
    for k in FALLBACK:
        if k in (cat or ""):
            return k
    return "RÉSEAU"


def enrich_batch(items):
    """items: list of (label, year, category). Retourne dict label -> (desc, who)."""
    listing = "\n".join(f"- {l} | {y} | {c}" for l, y, c in items)
    prompt = f"""Tu es un documentaliste encyclopédique francophone. Pour chaque événement ci-dessous,
donne une description factuelle précise (1-2 phrases, ~200 caractères) et la source/acteur (whoWhat).
Réponds UNIQUEMENT en JSON valide : {{"<label>": {{"description": "...", "whoWhat": "..."}}, ...}}
Liste :
{listing}"""
    try:
        r = requests.post(f"{OLLAMA_URL}/api/chat", json={
            "model": MODEL, "stream": False,
            "messages": [{"role": "user", "content": prompt}],
        }, timeout=180)
        r.raise_for_status()
        txt = r.json()["message"]["content"]
        m = re.search(r"\{.*\}", txt, re.S)
        data = json.loads(m.group(0)) if m else {}
        out = {}
        for l, y, c in items:
            v = data.get(l) or {}
            out[l] = (v.get("description") or "", v.get("whoWhat") or "")
        return out
    except Exception as e:
        print(f"  LLM batch KO ({e}), fallback catégorie")
        return {l: FALLBACK[cat_key(c)] for l, y, c in items}


def main():
    maxn = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10000
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    todo = [e for e in data
            if len((e.get("description") or "").strip()) < 30
            or (e.get("whoWhat") or "").strip() in ("", "?", "N/A", "Réalité")]
    todo = todo[:maxn]
    print(f"{len(todo)} événements à enrichir")
    B = 8
    done = 0
    for i in range(0, len(todo), B):
        batch = todo[i:i + B]
        items = [(e["label"], e.get("year"), e.get("category", "")) for e in batch]
        res = enrich_batch(items)
        for e in batch:
            desc, who = res.get(e["label"], ("", ""))
            if len((e.get("description") or "").strip()) < 30 and desc:
                e["description"] = desc.strip()
            if (e.get("whoWhat") or "").strip() in ("", "?", "N/A", "Réalité") and who:
                e["whoWhat"] = who.strip()
            done += 1
        print(f"  lot {i//B + 1}: {done}/{len(todo)}", flush=True)
        # sauvegarde incrémentale (résistant aux timeouts)
        tmp = DATA.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(DATA)
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    miss = sum(1 for e in data if len((e.get("description") or "").strip()) < 30)
    print(f"terminé. descriptions restantes < 30 car.: {miss}")


if __name__ == "__main__":
    main()
