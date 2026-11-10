#!/usr/bin/env python3
"""Seed référentiel antique + courbe MÉDECINE + nettoyage des timestamps.

- Ajoute les inventions des origines (Anticythère ~-100 av. J.-C. -> 1440) en 🔴 RÉSEAU / 🟡 HARDWARE.
- Ajoute la 12e catégorie 💊 MÉDECINE (faits médicaux avérés, jalons historiques).
- Normalise les timestamps : tout événement historique (year < année courante - 1) avec un
  timestamp récent (artefact de seed) est daté de son année -> ne pollue plus le flux 12h.
Upsert par id stable, verrouillé, rejouable."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT_MED = "💊 MÉDECINE"

# (year, label, who, category, desc, url, tipping)
ANCIENT = [
    (-100, "Mécanisme d'Anticythère", "Grecs (anonyme)", "🟡 HARDWARE",
     "Premier ordinateur analogique connu : engrenages de bronze calculant les positions astronomiques.",
     "https://fr.wikipedia.org/wiki/Mécanisme_d'Anticythère", True),
    (-2600, "Irrigation et canaux (Égypte)", "Anciens Égyptiens", "🔴 RÉSEAU",
     "Systèmes d'irrigation à grande échelle fondant l'agriculture et l'État pharaonique.",
     "https://fr.wikipedia.org/wiki/Irrigation_de_l'Égypte_antique", False),
    (-600, "Papyrus et bibliothèque d'Alexandrie", "Égyptiens / Grecs", "🔴 RÉSEAU",
     "Fixation et transmission du savoir écrit à grande échelle (plus grande bibliothèque de l'Antiquité).",
     "https://fr.wikipedia.org/wiki/Bibliothèque_d'Alexandrie", True),
    (60, "Æolipile (machine à vapeur de Héron)", "Héron d'Alexandrie", "🟡 HARDWARE",
     "Première machine à vapeur documentée, restée sans application industrielle.",
     "https://fr.wikipedia.org/wiki/Æolipile", False),
    (105, "Papier (invention chinoise)", "Cai Lun (Chine Han)", "🔴 RÉSEAU",
     "Invention du papier : révolution de l'écriture et de la diffusion du savoir.",
     "https://fr.wikipedia.org/wiki/Papier#Histoire", True),
    (850, "Poudre à canon (Chine)", "Alchimistes chinois", "☢️ ENTROPIE",
     "Première composition explosive : bouleverse la guerre et les équilibres de puissance.",
     "https://fr.wikipedia.org/wiki/Poudre_à_canon", True),
    (1000, "Boussole (Chine)", "Alchimistes chinois", "🟡 HARDWARE",
     "Aiguille aimantée : navigation maritime et exploration mondiale.",
     "https://fr.wikipedia.org/wiki/Boussole", True),
    (1271, "Lunettes (Italie)", "Alessandro della Spina", "💊 MÉDECINE",
     "Premières lunettes correctrices : prolongent la vie utile des savants et artisans.",
     "https://fr.wikipedia.org/wiki/Lunettes", False),
    (1300, "Horloge mécanique (Europe)", "Maîtres horlogers européens", "🟡 HARDWARE",
     "Mesure mécanique du temps : synchronise villes, travail et échanges.",
     "https://fr.wikipedia.org/wiki/Horloge_mécanique", False),
    (1440, "Imprimerie à caractères mobiles", "Johannes Gutenberg", "🔴 RÉSEAU",
     "Diffusion de masse du savoir écrit en Europe.",
     "https://fr.wikipedia.org/wiki/Imprimerie", True),
]

MEDICINE = [
    (-400, "Corpus hippocratique (médecine rationnelle)", "Hippocrate", CAT_MED,
     "Fondation de la médecine comme observation rationnelle, séparée de la magie.",
     "https://fr.wikipedia.org/wiki/Hippocrate", True),
    (170, "Galien : circulation et anatomie", "Claude Galien", CAT_MED,
     "Première synthèse systématique de l'anatomie et de la physiologie (dominera 14 siècles).",
     "https://fr.wikipedia.org/wiki/Gallien", False),
    (1543, "De humani corporis fabrica (anatomie moderne)", "André Vésale", CAT_MED,
     "Réfutation des erreurs de Galien par dissection : naissance de l'anatomie moderne.",
     "https://fr.wikipedia.org/wiki/André_Vésale", True),
    (1628, "Circulation sanguine (Harvey)", "William Harvey", CAT_MED,
     "Démonstration expérimentale de la circulation du sang : première loi physiologique quantitative.",
     "https://fr.wikipedia.org/wiki/William_Harvey", True),
    (1796, "Vaccin contre la variole (Jenner)", "Edward Jenner", CAT_MED,
     "Première vaccination : sauve des centaines de millions de vies, fonde l'immunologie.",
     "https://fr.wikipedia.org/wiki/Variole", True),
    (1846, "Anesthésie générale (éther)", "William Morton", CAT_MED,
     "Première chirurgie sans douleur : la douleur n'est plus une fatalité opératoire.",
     "https://fr.wikipedia.org/wiki/Anesthésie", True),
    (1861, "Théorie microbienne (Pasteur)", "Louis Pasteur", CAT_MED,
     "Les microbes causent les maladies : révolution de l'hygiène, de la chirurgie et de la conservation.",
     "https://fr.wikipedia.org/wiki/Louis_Pasteur", True),
    (1882, "Bacille de la tuberculose (Koch)", "Robert Koch", CAT_MED,
     "Postulats de Koch : méthode scientifique pour lier un microbe à une maladie.",
     "https://fr.wikipedia.org/wiki/Robert_Koch", False),
    (1928, "Pénicilline (Fleming)", "Alexander Fleming", CAT_MED,
     "Premier antibiotique : l'ère des infections bactériennes traitables s'ouvre.",
     "https://fr.wikipedia.org/wiki/Pénicilline", True),
    (1953, "Structure en double hélice de l'ADN", "Watson & Crick", CAT_MED,
     "Le support moléculaire de l'hérédité est élucidé : la biologie moléculaire commence.",
     "https://fr.wikipedia.org/wiki/Structure_de_l'ADN", True),
    (1977, "IRM (imagerie par résonance magnétique)", "Raymond Damadian", CAT_MED,
     "Voir l'intérieur du corps sans radiation : révolution du diagnostic.",
     "https://fr.wikipedia.org/wiki/Imagerie_par_résonance_magnétique", False),
    (1983, "Virus VIH isolé", "Luc Montagnier / Françoise Barré-Sinoussi", CAT_MED,
     "Identification du rétrovirus responsable du sida : base des tests et des traitements.",
     "https://fr.wikipedia.org/wiki/Virus_de_l'immunodéficience_humaine", True),
    (2012, "CRISPR-Cas9 (édition génomique)", "Emmanuelle Charpentier & Jennifer Doudna", CAT_MED,
     "Ciseaux moléculaires programmables : l'ADN devient éditable à la demande.",
     "https://fr.wikipedia.org/wiki/Cas9", True),
    (2020, "Vaccins à ARN messager (COVID-19)", "BioNTech/Pfizer, Moderna", CAT_MED,
     "Premiers vaccins ARNm autorisés à grande échelle : plateforme vaccinale de nouvelle génération.",
     "https://fr.wikipedia.org/wiki/Vaccin_à_ARN", True),
]


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def base_event(label, year, who, category, desc, url, tipping):
    return {
        "id": eid(label, year, who),
        "year": year,
        "value": 100 + (int(year) % 500) * 4,
        "label": label,
        "category": category,
        "whoWhat": who,
        "description": desc,
        "url": url,
        "timestamp": f"{int(year)}-06-01T00:00:00" if year < 2000 else datetime.now().isoformat(),
        "tipping": tipping,
        "s_curve_phase": 1 if year < 1500 else (2 if year < 1800 else 3),
        "pharmakon_remedy_percent": 80 if category == CAT_MED else 60,
        "pharmakon_poison_percent": 20 if category == CAT_MED else 40,
        "convergences": "Médecine + génétique + informatique + matériaux" if category == CAT_MED else "Fondation des savoirs et des techniques",
        "grand_filter_analysis": "Longévité et résilience de l'espèce." if category == CAT_MED else "Base de toute accélération ultérieure.",
        "final_note": "Le début de tout, en fait.",
    }


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    index = {}
    for e in data:
        e.setdefault("id", eid(e.get("label", ""), e.get("year", 0), e.get("whoWhat")))
        index[e["id"]] = e

    added = 0
    for year, label, who, cat, desc, url, tipping in ANCIENT + MEDICINE:
        e = base_event(label, year, who, cat, desc, url, tipping)
        index[e["id"]] = {**index.get(e["id"], {}), **e}
        added += 1

    # Normalisation : les événements historiques ne doivent pas polluer le flux 12h
    now = datetime.now()
    fixed = 0
    for e in index.values():
        y = e.get("year", 0)
        ts = e.get("timestamp")
        if y < now.year - 1 and ts:
            try:
                t = datetime.fromisoformat(ts)
                if (now - t).total_seconds() < 12 * 3600 and t.year >= now.year - 1:
                    # timestamp artificiellement "maintenant" sur un event ancien -> backdate
                    e["timestamp"] = f"{int(y)}-06-01T00:00:00"
                    fixed += 1
            except ValueError:
                pass

    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    cats = sorted({e.get("category") for e in out})
    print(f"+ {added} événements (ancien/médecine), {fixed} timestamps normalisés, total {len(out)}, {len(cats)} catégories")
    print("min year:", out[0]["year"], out[0]["label"])


if __name__ == "__main__":
    main()
