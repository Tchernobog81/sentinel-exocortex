#!/usr/bin/env python3
"""Rescan fiction complet : romans, manga, BD, films, séries (1863-2023).
Chaque œuvre est liée à sa réalisation réelle (realYear côté fiction, predictedBy côté réel).
Ancres réelles recherchées par sous-chaîne, créées si absentes. Upsert par id, verrouillé."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT_FICTION = "🔮 IMAGINAIRE"

# (œuvre, auteur, année, medium, ancre réelle existante OU None, si None: (label réel, année, catégorie, desc))
PAIRS = [
    ("Paris au XXe siècle", "Jules Verne", 1863, "roman", None, ("Visioconférence de masse (Zoom)", 2020, "🔴 RÉSEAU", "Verne prédit le « téléphote » : visioconférence mondiale de masse.")),
    ("Vingt mille lieues sous les mers", "Jules Verne", 1870, "roman", None, ("USS Nautilus, 1er sous-marin nucléaire", 1954, "🟡 HARDWARE", "Premier SNLE opérationnel, propulsé par réacteur nucléaire.")),
    ("L'Homme invisible", "H.G. Wells", 1897, "roman", None, ("Camouflage optique (métamatériaux)", 2006, "🟡 HARDWARE", "Métamatériaux à indice négatif rendant un objet quasi invisible.")),
    ("Le Maître du Haut Château", "Philip K. Dick", 1962, "roman", "Suprématie Quantique", None),
    ("Snow Crash", "Neal Stephenson", 1992, "roman", "Métavers (Facebook/Meta)", None),
    ("Le Diamant de l'âge (The Diamond Age)", "Neal Stephenson", 1995, "roman", None, ("Impression 3D industrielle", 2015, "🟡 HARDWARE", "Fabrication additive à l'échelle industrielle (nanofab).")),
    ("Metropolis", "Fritz Lang", 1927, "film", "Boston Dynamics Atlas", None),
    ("2001, L'Odyssée de l'espace", "Kubrick / Clarke", 1968, "film", "IBM Watson", None),
    ("Blade Runner", "Ridley Scott", 1982, "film", "Boston Dynamics Atlas", None),
    ("Tron", "Steven Lisberger", 1982, "film", "Métavers (Facebook/Meta)", None),
    ("WarGames", "John Badham", 1983, "film", "Stuxnet", None),
    ("Terminator", "James Cameron", 1984, "film", "Boston Dynamics Atlas", None),
    ("RoboCop", "Paul Verhoeven", 1987, "film", "Spot, robot quadrupède commercial", None),
    ("Total Recall", "Paul Verhoeven", 1990, "film", "Neuralink (Humain)", None),
    ("Retour vers le futur", "Robert Zemeckis", 1985, "film", "Waymo (Taxi autonome)", None),
    ("Minority Report", "Steven Spielberg", 2002, "film", "Police prédictive algorithmique", None),
    ("I, Robot", "Alex Proyas", 2004, "film", "Unimate, 1er robot industriel", None),
    ("A.I. Intelligence artificielle", "Steven Spielberg", 2001, "film", "Alexa / Siri", None),
    ("Wall-E", "Andrew Stanton", 2008, "film", "Roomba, robot domestique autonome", None),
    ("Avatar", "James Cameron", 2009, "film", None, ("Exosquelette militaire (Raytheon XOS 2)", 2010, "🟡 HARDWARE", "Exosquelette motorisé pour soldats, testé par l'US Army.")),
    ("Interstellar", "Christopher Nolan", 2014, "film", "Image du trou noir M87*", None),
    ("Seul sur Mars (The Martian)", "Ridley Scott", 2015, "film", "Curiosity sur Mars", None),
    ("Premier Contact (Arrival)", "Denis Villeneuve", 2016, "film", None, ("Traduction automatique neuronale", 2016, "🔵 COGNITION", "Traduction neuronale en temps réel (Google Translate/DeepL).")),
    ("Ghost in the Shell", "Mamoru Oshii", 1995, "manga/film", None, ("Lunettes de réalité augmentée (Google Glass)", 2013, "🔴 RÉSEAU", "Lunettes AR grand public avec surcouche numérique.")),
    ("Akira", "Katsuhiro Otomo", 1988, "manga/film", None, ("JO de Tokyo (2020, reportés 2021)", 2021, "🏛️ POLITIQUE", "Akira situe Neo-Tokyo aux JO 2020 ; Tokyo les accueille (reportés à 2021).")),
    ("Psycho-Pass", "Production I.G", 2012, "anime", "Police prédictive algorithmique", None),
    ("Doraemon", "Fujiko Fujio", 1969, "manga", "Roomba, robot domestique autonome", None),
    ("Valérian et Laureline", "Mézières / Christin", 1967, "BD", "Apollo 11 (Premier pas sur la Lune)", None),
    ("Le Secret de l'Espadon (Blake et Mortimer)", "Edgar P. Jacobs", 1950, "BD", None, ("USS Nautilus, 1er sous-marin nucléaire", 1954, "🟡 HARDWARE", "Le sous-marin nucléaire de Jacobs préfigure le Nautilus.")),
    ("Black Mirror", "Charlie Brooker", 2011, "série", "Piratage du DNC", None),
    ("Her", "Spike Jonze", 2013, "film", "Alexa / Siri", None),
    ("Ex Machina", "Alex Garland", 2014, "film", "Grand modèle de langage (LLM)", None),
    ("Transcendence", "Wally Pfister", 2014, "film", "Grand modèle de langage (LLM)", None),
    ("Chappie", "Neill Blomkamp", 2015, "film", "Boston Dynamics Atlas", None),
    ("Westworld", "Jonathan Nolan", 2016, "série", "Boston Dynamics Atlas", None),
    ("Surrogates", "Jonathan Mostow", 2009, "film", "Boston Dynamics Atlas", None),
    ("Elysium", "Neill Blomkamp", 2013, "film", None, ("Exosquelette médical (Ekso Bionics)", 2010, "🟡 HARDWARE", "Exosquelettes médicaux pour la rééducation motrice.")),
    ("Moon", "Duncan Jones", 2009, "film", None, ("SpaceX : 1er étage de fusée réutilisé", 2015, "🟣 ESPACE", "SpaceX récupère et réutilise le 1er étage d'une fusée orbitale.")),
    ("District 9", "Neill Blomkamp", 2009, "film", "Drones militaires armés", None),
    ("Lucy", "Luc Besson", 2014, "film", "Neuralink (Humain)", None),
    ("The Last of Us", "Druckmann / Mazin", 2020, "série", "COVID-19 (modélisation épidémiologique)", None),
    ("Severance", "Ben Stiller", 2022, "série", None, ("Paiement biométrique de masse (Amazon One)", 2020, "🔴 RÉSEAU", "Paiement par empreinte palmaire dans les commerces.")),
    ("Upload", "Greg Berlanti", 2020, "série", "Mind Uploading (Pilote)", None),
    ("Don't Look Up", "Adam McKay", 2021, "film", None, ("DART : déviation d'astéroïde (NASA)", 2022, "🟣 ESPACE", "La sonde DART percute un astéroïde et modifie son orbite.")),
    ("Dune", "Denis Villeneuve", 2021, "film", "EU AI Act", None),
    ("The Creator", "Gareth Edwards", 2023, "film", "DALL-E 2", None),
    ("Mission Impossible : Dead Reckoning", "Christopher McQuarrie", 2023, "film", None, ("Deepfakes vidéo par IA générative", 2023, "🔵 COGNITION", "Vidéos truquées indiscernables générées par IA (deepfakes).")),
    ("V pour Vendetta", "James McTeigue", 2005, "film", "PRISM (surveillance de masse)", None),
    ("Contagion", "Steven Soderbergh", 2011, "film", "COVID-19 (modélisation épidémiologique)", None),
    ("28 jours plus tard", "Danny Boyle", 2002, "film", "COVID-19 (modélisation épidémiologique)", None),
    ("World War Z", "Marc Forster", 2013, "film", "COVID-19 (modélisation épidémiologique)", None),
    ("L'Effet papillon (The Butterfly Effect)", "Eric Bress", 2004, "film", "Suprématie Quantique", None),
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
    events = list(index.values())

    def find_event(label):
        l = label.lower()
        for e in events:
            if e.get("label", "").lower() == l:
                return e
        for e in events:
            if l in e.get("label", "").lower():
                return e
        return None

    added = linked = 0
    for work, author, year, medium, real_label, create in PAIRS:
        real = find_event(real_label) if real_label else None
        if real is None and create:
            rl, ry, rcat, rdesc = create
            real = {
                "id": eid(rl, ry, "Réalité"), "year": ry, "value": 30000 + int(ry) % 1000,
                "label": rl, "category": rcat, "whoWhat": "Réalité",
                "description": rdesc, "url": "#",
                "timestamp": f"{int(ry)}-06-01T00:00:00", "tipping": True,
                "s_curve_phase": 4, "pharmakon_remedy_percent": 60, "pharmakon_poison_percent": 40,
                "convergences": "Prédiction de la fiction réalisée",
                "grand_filter_analysis": "La fiction comme banc d'essai de l'avenir.",
                "final_note": "Réalisé.",
            }
            index[real["id"]] = real
            events.append(real)
        fe = {
            "id": eid(work, year, author), "year": year, "value": 500 + int(year) % 900,
            "label": work, "category": CAT_FICTION, "whoWhat": author,
            "description": f"{medium.capitalize()} ({year}) — {author}.",
            "url": "https://fr.wikipedia.org/wiki/" + work.split(" (")[0].replace(" ", "_"),
            "timestamp": f"{int(year)}-06-01T00:00:00", "tipping": False,
            "s_curve_phase": 2, "pharmakon_remedy_percent": 50, "pharmakon_poison_percent": 50,
            "convergences": f"Fiction ({medium}) + réalisation technologique",
            "grand_filter_analysis": "La fiction comme prophétie auto-réalisatrice ou avertissement.",
            "final_note": "La SF avait prévenu.",
        }
        if real is not None:
            fe["realYear"] = real["year"]
            pb = real.get("predictedBy") or []
            if work not in pb:
                pb.append(work)
            real["predictedBy"] = pb
            linked += 1
        index[fe["id"]] = {**index.get(fe["id"], {}), **fe}
        events = list(index.values())
        added += 1

    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    fic = [e for e in out if e.get("category") == CAT_FICTION]
    last = max(fic, key=lambda e: e["year"])
    print(f"+ {added} œuvres, {linked} liées | total {len(out)} | fiction {len(fic)} (realYear: {sum(1 for e in fic if e.get('realYear'))}) | dernière fiction: {last['label']} {last['year']}")


if __name__ == "__main__":
    main()
