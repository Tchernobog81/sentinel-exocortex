#!/usr/bin/env python3
"""Liens fiction<->réel systématiques :
- Paire Manon des sources (Pagnol) <-> Guerres de l'Eau (Climat) 2050.
- Appariement conservateur : toute fiction sans realYear est reliée à l'événement réel
  le plus proche (token commun significatif, real.year >= fiction.year et <= fiction.year+90).
Upsert par id, verrouillé, rejouable."""
import fcntl
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT_FICTION = "🔮 IMAGINAIRE"
STOPWORDS = {"le", "la", "les", "de", "des", "du", "un", "une", "et", "en", "au", "aux", "the", "a", "of", "in", "et", "film", "roman", "livre"}


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def tokens(text):
    return {t for t in re.findall(r"[a-zà-ÿ]{4,}", (text or "").lower()) if t not in STOPWORDS}


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    index = {}
    for e in data:
        e.setdefault("id", eid(e.get("label", ""), e.get("year", 0), e.get("whoWhat")))
        index[e["id"]] = e
    events = list(index.values())

    # 1) Paire Manon des sources <-> Guerres de l'Eau
    water = next((e for e in events if "guerre" in e["label"].lower() and "eau" in e["label"].lower()), None)
    manon = {
        "id": eid("Manon des sources (Pagnol)", 1929, "Marcel Pagnol"),
        "year": 1929, "value": 2100, "label": "Manon des sources (Pagnol)",
        "category": CAT_FICTION, "whoWhat": "Marcel Pagnol",
        "description": "Roman (1929, film 1952) : la guerre de l'eau entre villages de Provence — conflit autour de la source.",
        "url": "https://fr.wikipedia.org/wiki/Manon_des_sources",
        "timestamp": "1929-06-01T00:00:00", "tipping": False,
        "s_curve_phase": 2, "pharmakon_remedy_percent": 40, "pharmakon_poison_percent": 60,
        "convergences": "Eau + climat + conflits territoriaux",
        "grand_filter_analysis": "La fiction préfigure les guerres de ressource (eau) du XXIe siècle.",
        "final_note": "L'eau, prochain or bleu.",
    }
    if water:
        manon["realYear"] = water["year"]
        pb = water.get("predictedBy") or []
        if manon["label"] not in pb:
            pb.append(manon["label"])
        water["predictedBy"] = pb
        print(f"lien Manon -> {water['label']} ({water['year']})")
    index[manon["id"]] = {**index.get(manon["id"], {}), **manon}
    events = list(index.values())

    # 2) Appariement manuel des classiques sans realYear (fiction label -> real label)
    MANUAL_PAIRS = [
        ("De la Terre à la Lune", "Apollo 11"),
        ("R.U.R. (Robot)", "Unimate, 1er robot industriel"),
        ("Le Meilleur des mondes", "Bébés CRISPR"),
        ("Lois de la Robotique", "Unimate, 1er robot industriel"),
        ("1984", "PRISM"),
        ("Star Trek (Série)", "iPhone (smartphone)"),
        ("Do Androids Dream?", "Boston Dynamics Atlas"),
        ("2001 L'Odyssée", "IBM Watson"),
        ("Blade Runner", "Boston Dynamics Atlas"),
        ("Tron", "Métavers (Facebook/Meta)"),
        ("WarGames", "Stuxnet"),
        ("Neuromancien", "World Wide Web public"),
        ("Retour vers le Futur II", "Waymo (Taxi autonome)"),
        ("Retour vers le Futur", "Waymo (Taxi autonome)"),
        ("Une Forme de Guerre", "Drones militaires armés"),
        ("Les Simpson", "Boson de Higgs"),
        ("Excession", "Bitcoin (Genesis Block)"),
        ("Bienvenue à Gattaca", "23andMe"),
        ("Minority Report", "Police prédictive algorithmique"),
        ("Black Mirror", "Piratage du DNC"),
        ("Her", "Alexa / Siri"),
        ("Ex Machina", "Grand modèle de langage (LLM)"),
        ("The Expanse", "SpaceX Fondé"),
        ("La Nuit des temps", "Boson de Higgs"),
    ]
    by_label_lower = {e.get("label", "").lower(): e for e in events}
    def find_event(label):
        l = label.lower()
        if l in by_label_lower:
            return by_label_lower[l]
        for k, e in by_label_lower.items():
            if l in k:
                return e
        return None
    manual_linked = 0
    for fic_label, real_label in MANUAL_PAIRS:
        f = find_event(fic_label)
        r = find_event(real_label)
        if not f or not r:
            print(f"  !! introuvable: {fic_label} ou {real_label}")
            continue
        if not f.get("realYear"):
            f["realYear"] = r["year"]
            manual_linked += 1
        pb = r.get("predictedBy") or []
        if f["label"] not in pb:
            pb.append(f["label"])
        r["predictedBy"] = pb
    print(f"liens manuels: {manual_linked} fictions liées, {len(MANUAL_PAIRS)} paires traitées")

    # 3) Appariement conservateur des fictions sans realYear
    fictions = [e for e in events if e.get("category") == CAT_FICTION and not e.get("realYear")]
    reals = [e for e in events if e.get("category") != CAT_FICTION]
    linked = 0
    for f in fictions:
        ftok = tokens(f["label"] + " " + f.get("description", ""))
        if len(ftok) < 2:
            continue
        best, bestscore = None, 0
        for r in reals:
            if not (f["year"] <= r["year"] <= f["year"] + 90):
                continue
            rtok = tokens(r["label"] + " " + r.get("description", ""))
            score = len(ftok & rtok)
            if score > bestscore:
                best, bestscore = r, score
        if best and bestscore >= 2:
            f["realYear"] = best["year"]
            pb = best.get("predictedBy") or []
            if f["label"] not in pb:
                pb.append(f["label"])
            best["predictedBy"] = pb
            linked += 1
    print(f"auto-liens: {linked} fictions reliées à un réel")

    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    fic = [e for e in out if e.get("category") == CAT_FICTION]
    print(f"total {len(out)} | fiction {len(fic)} | avec realYear: {sum(1 for e in fic if e.get('realYear'))} | réels avec predictedBy: {sum(1 for e in out if e.get('predictedBy'))}")


if __name__ == "__main__":
    main()
