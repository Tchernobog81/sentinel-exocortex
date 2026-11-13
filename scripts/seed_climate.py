#!/usr/bin/env python3
"""Seed de la courbe 🌡️ CLIMAT & BIODIVERSITÉ : événements RÉELS et sourcés (histoire du climat,
biodiversité, extinctions), upsertés par id stable dans loom_data.json (API d'abord, fallback fichier).
La valeur `value` suit la tendance log-linéaire globale du Loom (interpolée sur les médianes par décennie)
pour ne pas déformer la synthèse ✦ SINGULARITÉ."""
import json, os, sys, math, statistics, collections, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "sentinel"))
sys.path.insert(0, str(ROOT / "backend"))

DATA_FILE = ROOT / "loom_data.json"
API = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000/api/data")
CAT = "🌡️ CLIMAT"

# (année, label, source, url, description, tipping)
EVENTS = [
    (-252, "Extinction de masse du Permien-Trias (252 Ma) : ~96 % des espèces marines disparaissent",
     "Science / Nature", "https://www.nature.com", "Plus grande extinction de masse de l'histoire de la vie, liée à un volcanisme massif (trapps de Sibérie) et au réchauffement extrême.", True),
    (-66, "Extinction Crétacé-Paléogène (66 Ma) : l'astéroïde de Chicxulub anéantit les dinosaures non aviens",
     "Science", "https://www.science.org", "Impact de 10 km + volcanisme du Deccan : ~75 % des espèces disparaissent, ouvrant la voie aux mammifères.", True),
    (1824, "Joseph Fourier théorise l'effet de serre atmosphérique",
     "Académie des sciences", "https://www.academie-sciences.fr", "Dans son mémoire sur les températures du globe, Fourier explique que l'atmosphère piège la chaleur (effet de serre).", False),
    (1856, "Eunice Foote démontre expérimentalement que le CO2 réchauffe l'atmosphère",
     "American Journal of Science", "https://www.aapt.org", "Première preuve expérimentale du rôle du CO2 dans le piégeage de la chaleur, présentée en 1856.", False),
    (1896, "Svante Arrhenius quantifie le réchauffement : un doublement du CO2 -> +5 à 6 °C",
     "Philosophical Magazine", "https://www.tandfonline.com", "Premier calcul de la sensibilité climatique, toujours dans la fourchette du GIEC actuel (~3 °C,ECS 2,5-4 °C).", True),
    (1938, "Guy Callendar relie hausse observée des températures et hausse du CO2 mesurée",
     "Quarterly Journal of the Royal Meteorological Society", "https://www.rmets.org", "Callendar publie la première courbe liant émissions industrielles de CO2 et réchauffement global observé.", False),
    (1958, "Début de la courbe de Keeling à Mauna Loa : CO2 atmosphérique à ~315 ppm",
     "Scripps CO2 Program / NOAA", "https://scrippsco2.ucsd.edu", "Mesure continue du CO2 : 315 ppm en 1958, contre ~280 ppm à l'ère préindustrielle.", True),
    (1972, "Rapport Meadows « The Limits to Growth » (Club de Rome)",
     "Club de Rome", "https://www.clubofrome.org", "Première modélisation systémique des limites planétaires (ressources, pollution, démographie).", True),
    (1972, "Conférence de Stockholm : création du PNUE, première conférence ONU sur l'environnement",
     "ONU / PNUE", "https://www.unep.org", "Naissance du droit international de l'environnement (principe de précaution, responsabilité commune).", False),
    (1979, "Rapport Charney (US National Academy of Sciences) : sensibilité climatique ~3 °C pour 2xCO2",
     "National Academy of Sciences", "https://www.nasonline.org", "Consensus scientifique précoce sur l'ampleur du réchauffement induit par les gaz à effet de serre.", True),
    (1987, "Protocole de Montréal : élimination des CFC pour protéger la couche d'ozone",
     "ONU", "https://www.unep.org", "Accord environnemental le plus ratifié de l'histoire ; la couche d'ozone se rétablit (2066 prévu pour l'Antarctique).", True),
    (1988, "Création du GIEC (IPCC) par l'ONU (OMM + PNUE)",
     "GIEC / ONU", "https://www.ipcc.ch", "Le GIEC évalue l'état des connaissances scientifiques sur le changement climatique.", True),
    (1992, "Sommet de la Terre à Rio : signature de la CCNUCC (climat) et de la Convention sur la biodiversité",
     "ONU", "https://unfccc.int", "Deux traités fondateurs : Convention-cadre sur les changements climatiques et Convention sur la diversité biologique.", True),
    (1997, "Protocole de Kyoto adopté : objectifs chiffrés de réduction des émissions pour les pays industrialisés",
     "ONU / CCNUCC", "https://unfccc.int/kyoto_protocol", "Premier traité avec objectifs contraignants (-5 % en moyenne 2008-2012 vs 1990).", False),
    (2007, "4e rapport du GIEC (AR4) : le réchauffement est « sans équivoque » ; GIEC et Al Gore Nobel de la paix",
     "GIEC", "https://www.ipcc.ch/report/ar4/", "Attribution à >90 % aux activités humaines ; le GIEC partage le Nobel de la paix 2007.", True),
    (2015, "Accord de Paris (COP21) : objectif +2 °C, effort vers +1,5 °C, neutralité carbone en 2e moitié de siècle",
     "ONU / CCNUCC", "https://unfccc.int/paris_agreement", "195 États s'engagent sur des contributions nationales (NDC) révisées tous les 5 ans.", True),
    (2018, "Rapport spécial du GIEC (SR15) : +1,5 °C dès 2030-2052 au rythme actuel ; il reste une fenêtre d'action",
     "GIEC", "https://www.ipcc.ch/sr15/", "Le GIEC chiffre les trajectoires compatibles 1,5 °C (réduction de 45 % des émissions d'ici 2030).", True),
    (2019, "Rapport IPBES : 1 million d'espèces animales et végétales menacées d'extinction",
     "IPBES", "https://www.ipbes.net", "Évaluation mondiale de la biodiversité : 25 % des espèces évaluées menacées, accélération sans précédent.", True),
    (2021, "COP26 Glasgow : pacte sur la sortie progressive du charbon, règles de l'article 6 de Paris",
     "ONU / CCNUCC", "https://ukcop26.org", "Premier texte COP mentionnant explicitement les énergies fossiles (charbon « phased down »).", False),
    (2022, "COP15 Kunming-Montréal : cadre mondial pour la biodiversité, objectif « 30x30 » (30 % des terres et mers protégées d'ici 2030)",
     "ONU / CDB", "https://www.cbd.int", "Accord historique pour la biodiversité, équivalent de Paris pour le vivant.", True),
    (2023, "2023 : année la plus chaude jamais enregistrée (+1,48 °C vs préindustriel) — Copernicus",
     "Copernicus / UE", "https://climate.copernicus.eu", "Record battu de loin ; banquise antarctique au plus bas historique (février 2023).", True),
    (2024, "2024 : nouvelle année record (+~1,6 °C) et 4e blanchissement corallien mondial déclaré par la NOAA",
     "Copernicus / NOAA", "https://www.noaa.gov", "Le blanchissement touche désormais >90 % des récifs évalués dans tous les bassins océaniques.", True),
    (2025, "COP30 à Belém (Brésil) : feuille de route de sortie des énergies fossiles et financement climatique",
     "ONU / CCNUCC", "https://cop30.brasil2025.br", "COP de la mise en œuvre : mécanismes de financement (fonds pertes et dommages opérationnel depuis 2023) et trajectoire fossile.", False),
]


def trend_value(year: float, data: list) -> int:
    """Interpole log-linéairement la médiane des `value` par décennie -> le point climat reste sur la tendance."""
    by = collections.defaultdict(list)
    for e in data:
        y = e.get("year")
        if isinstance(y, (int, float)) and isinstance(e.get("value"), (int, float)) and e.get("value", 0) > 0:
            by[int(y // 10) * 10].append(e["value"])
    pts = sorted((y, math.log(statistics.median(v))) for y, v in by.items() if v)
    if not pts:
        return 10000
    if year <= pts[0][0]:
        return int(math.exp(pts[0][1]))
    if year >= pts[-1][0]:
        return int(math.exp(pts[-1][1]))
    for (y0, l0), (y1, l1) in zip(pts, pts[1:]):
        if y0 <= year <= y1:
            t = (year - y0) / (y1 - y0) if y1 > y0 else 0
            return int(math.exp(l0 + t * (l1 - l0)))
    return 10000


def main():
    from sentinel import compute_event_id  # id stable identique au sentinel
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    existing_ids = {e.get("id") for e in data}
    now = datetime.datetime.now().isoformat()
    events = []
    for year, label, src, url, desc, tipping in EVENTS:
        eid = compute_event_id(label, year, src)
        if eid in existing_ids:
            print(f"déjà présent: {label[:60]}")
            continue
        y = float(year)
        events.append({
            "id": eid, "year": y, "value": trend_value(y, data), "label": label, "category": CAT,
            "whoWhat": src, "description": desc, "url": url, "timestamp": now,
            "tipping": tipping, "verified": True,
            "s_curve_phase": 1 if year < 1940 else 2 if year < 1990 else 3 if year < 2015 else 4,
            "pharmakon_remedy_percent": 30, "pharmakon_poison_percent": 70,
            "convergences": "Croise le front énergie/ressources et la géopolitique (COP, financements Nord-Sud).",
            "grand_filter_analysis": "Filtre climatique/énergétique : les trajectoires d'émission décident de la fenêtre d'action.",
        })
    print(f"{len(events)} événements climat à insérer")
    if not events:
        return
    try:
        import requests
        r = requests.post(API, json=events, timeout=60)
        r.raise_for_status()
        print("upsert API OK:", r.json())
        return
    except Exception as e:
        print("API indisponible, fallback fichier:", e)
    # fallback : upsert direct dans le fichier (id stable)
    index = {e.get("id"): e for e in data}
    for e in events:
        index[e["id"]] = e
    tmp = DATA_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(list(index.values()), indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, DATA_FILE)
    print(f"écrit {len(events)} événements dans {DATA_FILE}")


if __name__ == "__main__":
    main()
