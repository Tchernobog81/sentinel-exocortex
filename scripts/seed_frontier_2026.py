#!/usr/bin/env python3
"""Faits réels 2026 à haut signal (sources: ARC Prize, BenchLM, Quanta, Science, labs).
Catégorie 🔵 COGNITION (IA/recherche). Upsert par id, verrouillé, rejouable."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT = "🔵 COGNITION"

# (year, label, who, desc, url, tipping)
EVENTS = [
    (2026.23, "Lancement d'ARC-AGI-3 (Y Combinator, 25 mars 2026)", "ARC Prize Foundation",
     "Nouveau benchmark agentique (jeux 2D interactifs). Aperçu 30 jours : humains 100 %, meilleurs modèles frontier < 0,4 %.",
     "https://arcprize.org/", True),
    (2026.28, "Une conjecture mathématique de 42 ans résolue en 12 h par IA", "Quanta Magazine (13 avril 2026)",
     "Un agent IA a démontré en 12 heures une conjecture ouverte depuis 42 ans — la recherche mathématique autonome accélère.",
     "https://www.quantamagazine.org/", True),
    (2026.35, "Réfutation Lean-vérifiée de la conjecture d'Erdős (1946)", "OpenAI (mai 2026)",
     "Contre-exemple de la conjecture de distance unité d'Erdős, vérifié formellement en Lean et cosigné par 9 mathématiciens.",
     "https://openai.com/", True),
    (2026.5, "IA : 5 problèmes sur 6 résolus à l'Olympiade internationale de maths", "IMO 2026",
     "Performance niveau or olympique en raisonnement formel (suite d'AlphaProof, Nature 2024).",
     "https://www.nature.com/", True),
    (2026.55, "Agents IA résolvent des problèmes de maths ouverts (Science 2026)", "Tsoukalas et al., Science",
     "Des agents autonomes résolvent des problèmes ouverts de niveau recherche (article Science, 2026).",
     "https://www.science.org/", True),
    (2026.79, "Gemini 4 Argon : 97,5 % vérifiés sur ARC-AGI-3 (16 oct. 2026)", "Google DeepMind",
     "Deuxième labo à franchir 95 % sur ARC-AGI-3, « ultimate AGI proving ground » selon ARC Prize.",
     "https://arcprize.org/", True),
    (2026.87, "Claude Fable 5.2 en tête du leaderboard ARC-AGI-3 (81,2 %)", "BenchLM.ai (nov. 2026)",
     "Snapshot semi-privé du leaderboard ARC-AGI-3 : Fable 5.2 (XHigh) 81,2 %, devant Fable 5.2 High 79,3 %.",
     "https://benchlm.ai/", False),
    (2026.92, "Résultats officiels ARC Prize 2026 (4 déc. 2026)", "ARC Prize Foundation",
     "Clôture de l'édition 2026 du benchmark ARC-AGI-3 et annonce des gagnants.",
     "https://arcprize.org/", True),
]


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    index = {}
    for e in data:
        e.setdefault("id", eid(e.get("label", ""), e.get("year", 0), e.get("whoWhat")))
        index[e["id"]] = e
    added = 0
    v = 45000
    for year, label, who, desc, url, tipping in EVENTS:
        e = {
            "id": eid(label, year, who), "year": year, "value": v, "label": label,
            "category": CAT, "whoWhat": who, "description": desc, "url": url,
            "timestamp": f"2026-{int((year % 1) * 12) + 1:02d}-15T00:00:00",
            "tipping": tipping, "s_curve_phase": 4,
            "pharmakon_remedy_percent": 60, "pharmakon_poison_percent": 40,
            "convergences": "IA + mathématiques + physique + benchmarks vérifiés",
            "grand_filter_analysis": "Capacité de raisonnement autonome mesurée, pas seulement bavardage.",
            "final_note": "Le benchmark monte, le suspense aussi.",
        }
        v += 500
        index[e["id"]] = {**index.get(e["id"], {}), **e}
        added += 1
    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(f"+ {added} événements frontier 2026, total {len(out)}")


if __name__ == "__main__":
    main()
