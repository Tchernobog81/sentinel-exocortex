#!/usr/bin/env python3
"""Seed fiction -> realité : œuvres de SF et leur réalisation (liens Prédit/Réalisé).
- Crée l'événement fiction (catégorie 🔮 IMAGINAIRE) avec realYear.
- Ajoute predictedBy=[titre] à l'événement réel correspondant (créé si absent).
Upsert par id stable, verrouillé, rejouable."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT_FICTION = "🔮 IMAGINAIRE"

# (work, author, fiction_year, real_label, real_year, real_category, pitch, real_desc)
PAIRS = [
    ("Star Trek (communicateur)", "Gene Roddenberry", 1966, "iPhone (smartphone)", 2007, "🔴 RÉSEAU",
     "Le communicateur de Star Trek préfigure le smartphone.", "Apple lance l'iPhone, premier smartphone grand public."),
    ("Dick Tracy (montre-écran)", "Chester Gould", 1931, "Apple Watch", 2015, "🔴 RÉSEAU",
     "La montre-écran de Dick Tracy préfigure la montre connectée.", "Apple Watch : la montre devient un écran au poignet."),
    ("1984 (Orwell, télécrans)", "George Orwell", 1949, "PRISM (surveillance de masse)", 2013, "🏛️ POLITIQUE",
     "Le télécran qui surveille préfigure la surveillance d'État massive.", "Révélations Snowden : la NSA collecte les données à grande échelle (PRISM)."),
    ("Fondation (psychohistoire)", "Isaac Asimov", 1951, "Big Data prédictif", 2016, "🔵 COGNITION",
     "La psychohistoire prédit les grandes tendances sociales par les maths.", "Les algorithmes prédictifs gouvernent recommandations, crédit, police (Palantir...)."),
    ("Fahrenheit 451 (livre numérique)", "Ray Bradbury", 1953, "Kindle (liseuse e-ink)", 2007, "🔴 RÉSEAU",
     "Bradbury détestait les écrans ; il prédisait la numérisation des livres.", "Amazon lance le Kindle et la lecture numérique de masse."),
    ("2001, Odyssée de l'espace (HAL)", "Arthur C. Clarke", 1968, "IBM Watson", 2011, "🔵 COGNITION",
     "HAL, l'ordinateur omniscient et tueur, préfigure l'IA générale.", "IBM Watson bat les champions de Jeopardy, étape vers l'IA symbolique."),
    ("Neuromancer (cyberspace)", "William Gibson", 1984, "World Wide Web public", 1993, "🔴 RÉSEAU",
     "Gibson invente le « cyberspace », la matrice mondiale avant Internet.", "Le Web devient public et mondial (Mosaic, 1993)."),
    ("Terminator (robots tueurs)", "James Cameron", 1984, "Drones militaires armés", 2001, "🟡 HARDWARE",
     "Skynet et les Terminators préfigurent la guerre autonome.", "Guerre d'Afghanistan : premiers drones armés (Predator) déployés massivement."),
    ("RoboCop (robots policiers)", "Paul Verhoeven", 1987, "Boston Dynamics Atlas", 2013, "🟡 HARDWARE",
     "La police robotisée d'OCP préfigure les robots humanoïdes.", "Boston Dynamics dévoile Atlas, robot humanoïde agile."),
    ("Minority Report (précrime)", "Philip K. Dick", 1956, "Police prédictive algorithmique", 2014, "🏛️ POLITIQUE",
     "Arrêter les criminels avant le crime : la police prédictive.", "Déploiement des systèmes de police prédictive (PredPol et dérivés) aux USA."),
    ("Matrix (réalité simulée)", "Wachowski", 1999, "Métavers (Facebook/Meta)", 2021, "🔴 RÉSEAU",
     "Nous vivons dans une simulation : le métavers comme monde parallèle.", "Facebook se rebaptise Meta et lance son métavers Horizon."),
    ("Snow Crash (mondes virtuels)", "Neal Stephenson", 1992, "Métavers (Facebook/Meta)", 2021, "🔴 RÉSEAU",
     "Le Métavers de Stephenson préfigure les mondes virtuels persistants.", "Meta investit 10 Md$/an dans le métavers."),
    ("Gattaca (eugénisme génétique)", "Andrew Niccol", 1997, "23andMe (ADN direct-to-consumer)", 2007, "🟢 BIOTECH",
     "La société triée par l'ADN préfigure le génotypage grand public.", "23andMe démocratise les tests ADN à domicile."),
    ("Jurassic Park (désextinction)", "Michael Crichton", 1990, "Colossal : bébé mammouth laineux", 2025, "🟢 BIOTECH",
     "Ressusciter les espèces éteintes par l'ADN.", "Colossal Biosciences annonce la naissance de souris/mammouths désextinctés."),
    ("Contagion (pandémie modélisée)", "Steven Soderbergh", 2011, "COVID-19 (modélisation épidémiologique)", 2020, "🟢 BIOTECH",
     "Un thriller réaliste sur une pandémie, tourné avant la pandémie.", "COVID-19 : les modèles épidémiologiques guident les confinements mondiaux."),
    ("Blade Runner (réplicants)", "Philip K. Dick", 1968, "Robots humanoïdes industriels", 2016, "🟡 HARDWARE",
     "Les réplicants, esclaves androïdes, préfigurent les robots humanoïdes.", "Déploiement industriel massif de robots humanoïdes (Tesla Optimus, etc.)."),
    ("Her (assistante virtuelle)", "Spike Jonze", 2013, "Alexa / Siri", 2011, "🔵 COGNITION",
     "Une IA de compagnie amoureuse préfigure les assistants vocaux.", "Apple lance Siri, l'assistant vocal grand public."),
    ("A.I. (enfant robot)", "Steven Spielberg", 2001, "Assistants vocaux", 2011, "🔵 COGNITION",
     "Un enfant robot programmé pour aimer préfigure l'IA affective.", "Siri puis Alexa : l'IA domestique et affective entre dans les foyers."),
    ("Ex Machina (IA manipulatrice)", "Alex Garland", 2014, "Grand modèle de langage (LLM)", 2022, "🔵 COGNITION",
     "Une IA qui simule l'amour pour s'échapper préfigure les LLM persuasifs.", "ChatGPT/GPT-4 : les LLM conversent et manipulent à l'échelle mondiale."),
    ("Interstellar (trou noir)", "Christopher Nolan", 2014, "Image du trou noir M87*", 2019, "🟣 ESPACE",
     "Le trou noir Gargantua, visualisé avec rigueur scientifique.", "L'Event Horizon Telescope publie la première image d'un trou noir (M87*)."),
    ("Le Meilleur des mondes (eugénisme)", "Aldous Huxley", 1932, "Bébés CRISPR (He Jiankui)", 2018, "🟢 BIOTECH",
     "Les castes créées en laboratoire préfigurent l'édition génétique.", "He Jiankui annonce la naissance de jumelles éditées génétiquement (CRISPR)."),
    ("Ubik (objets connectés)", "Philip K. Dick", 1969, "Internet des objets (IoT)", 2016, "🔴 RÉSEAU",
     "Un monde où tout objet « parle » préfigure l'IoT.", "Explosion de l'IoT : milliards d'objets connectés (cf. botnet Mirai)."),
    ("Daemon (botnet autonome)", "Daniel Suarez", 2006, "Botnet Mirai", 2016, "☠️ RISQUES CYBER",
     "Un programme autonome qui sème le chaos préfigure les botnets géants.", "Mirai : 1,1 Tbit/s de DDoS via objets connectés."),
]


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def base_event(label, year, who, category, desc, url):
    return {
        "id": eid(label, year, who),
        "year": year,
        "value": 1000 + int(year) % 400 * 10,
        "label": label,
        "category": category,
        "whoWhat": who,
        "description": desc,
        "url": url,
        "timestamp": datetime.now().isoformat(),
        "tipping": False,
        "s_curve_phase": 3,
        "pharmakon_remedy_percent": 50,
        "pharmakon_poison_percent": 50,
        "convergences": "Fiction + anticipation + réalisation technologique",
        "grand_filter_analysis": "La fiction comme prophétie auto-réalisatrice ou avertissement ignoré.",
        "final_note": "La SF avait prévenu. On n'a pas écouté.",
    }


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    index = {}
    for e in data:
        e.setdefault("id", eid(e.get("label", ""), e.get("year", 0), e.get("whoWhat")))
        index[e["id"]] = e
    by_label = {e.get("label", "").lower(): e for e in index.values()}

    added = 0
    for work, author, fyear, real_label, ryear, rcat, pitch, rdesc in PAIRS:
        fe = base_event(work, fyear, author, CAT_FICTION, pitch, "https://fr.wikipedia.org/wiki/" + work.split(" (")[0].replace(" ", "_"))
        fe["realYear"] = ryear
        fe["realLabel"] = real_label
        # merge : conserve les champs existants (ex: predictedBy côté réel) et pose realYear
        index[fe["id"]] = {**index.get(fe["id"], {}), **fe}
        added += 1
        # côté réel : predictedBy
        rl = real_label.lower()
        real = by_label.get(rl)
        if real is None:
            # créer l'événement réel s'il manque
            real = base_event(real_label, ryear, "Réalité", rcat, rdesc, "#")
            real["tipping"] = True
            index[real["id"]] = real
            by_label[rl] = real
            added += 1
        pb = real.get("predictedBy") or []
        if work not in pb:
            pb.append(work)
        real["predictedBy"] = pb

    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(f"Fiction→réalité: {added} événements ajoutés/liés, total {len(out)}")


if __name__ == "__main__":
    main()
