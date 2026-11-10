#!/usr/bin/env python3
"""13e courbe 🤖 ROBOTIQUE : jalons réels + liens fiction→réalité (predictedBy/realYear).
Upsert par id, verrouillé, rejouable."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT_ROBOT = "🤖 ROBOTIQUE"
CAT_FICTION = "🔮 IMAGINAIRE"

# jalons réels : (year, label, who, desc, url, tipping)
ROBOTS = [
    (1495, "Chevalier mécanique de Léonard", "Léonard de Vinci", "Premier automate humanoïde documenté (design).", "https://fr.wikipedia.org/wiki/L%C3%A9onard_de_Vinci", False),
    (1738, "Canard digesteur de Vaucanson", "Jacques de Vaucanson", "Automate mécanique animé, prouesse de l'ingénierie du XVIIIe.", "https://fr.wikipedia.org/wiki/Canard_digesteur", False),
    (1920, "Le mot « robot » (R.U.R.)", "Karel Čapek", "La pièce R.U.R. invente le mot robot (travail forcé tchèque) : robots esclaves.", "https://fr.wikipedia.org/wiki/R.U.R.", True),
    (1954, "Unimate, 1er robot industriel", "George Devol", "Premier bras robotique programmable, précurseur de la robotique industrielle.", "https://fr.wikipedia.org/wiki/Unimate", True),
    (1961, "Unimate déployé chez General Motors", "General Motors", "Premier robot industriel en production (soudure par points).", "https://en.wikipedia.org/wiki/Unimate", True),
    (1966, "Shakey, 1er robot « intelligent »", "Stanford Research Institute", "Premier robot mobile percevant et raisonnant sur son environnement.", "https://en.wikipedia.org/wiki/Shakey_the_robot", False),
    (1999, "AIBO, robot animal de compagnie", "Sony", "Premier robot domestique à succès commercial (apprentissage machine embarqué).", "https://en.wikipedia.org/wiki/Aibo", False),
    (2000, "ASIMO, humanoïde bipède", "Honda", "Robot humanoïde le plus avancé de son époque (marche, course, interaction).", "https://en.wikipedia.org/wiki/ASIMO", True),
    (2002, "Roomba, robot domestique autonome", "iRobot", "Aspirateur autonome : la robotique entre dans les foyers.", "https://en.wikipedia.org/wiki/Roomba", False),
    (2013, "Atlas, humanoïde hydraulique", "Boston Dynamics", "Robot capable de courir, sauter et se relever après une chute.", "https://en.wikipedia.org/wiki/Boston_Dynamics#Atlas", True),
    (2016, "Sophia, robot « citoyen »", "Hanson Robotics", "Premier robot à obtenir une citoyenneté (Arabie saoudite) : symbole médiatique.", "https://en.wikipedia.org/wiki/Sophia_(robot)", False),
    (2020, "Spot, robot quadrupède commercial", "Boston Dynamics", "Chien robot déployé en industrie (inspection, sites dangereux).", "https://en.wikipedia.org/wiki/Spot_(robot)", True),
    (2021, "Optimus, robot humanoïde Tesla", "Tesla", "Tesla annonce un humanoïde généraliste pour l'usine et le domicile.", "https://en.wikipedia.org/wiki/Tesla_Optimus", False),
    (2024, "Figure 01, humanoïde industriel", "Figure AI", "Humanoïde déployé en usine BMW (assemblage automobile).", "https://en.wikipedia.org/wiki/Figure_AI", False),
]

# fiction -> réalisation : (work, author, fyear, real_label, pitch)
FICTION_LINKS = [
    ("Metropolis (robot Maria)", "Fritz Lang", 1927, "Atlas, humanoïde hydraulique", "Le robot humanoïde de Metropolis préfigure les androïdes modernes."),
    ("R.U.R. (robots révoltés)", "Karel Čapek", 1920, "Unimate, 1er robot industriel", "La révolte des robots de Čapek préfigure l'automatisation industrielle."),
    ("Astro Boy", "Osamu Tezuka", 1952, "ASIMO, humanoïde bipède", "Astro Boy préfigure le robot humanoïde gentil et agile."),
    ("I, Robot (lois des robots)", "Isaac Asimov", 1950, "Unimate, 1er robot industriel", "Les trois lois d'Asimov encadrent la robotique réelle."),
    ("Terminator (T-800)", "James Cameron", 1984, "Atlas, humanoïde hydraulique", "Le T-800 préfigure les machines autonomes mobiles."),
    ("RoboCop", "Paul Verhoeven", 1987, "Spot, robot quadrupède commercial", "La police robotisée préfigure les robots d'intervention."),
    ("Iron Man (exosquelette)", "Marvel", 2008, "Figure 01, humanoïde industriel", "L'armure high-tech préfigure les exosquelettes industriels."),
    ("2001, Odyssée (HAL 9000)", "Arthur C. Clarke", 1968, "ASIMO, humanoïde bipède", "HAL préfigure l'automate doté d'intelligence embarquée."),
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
    by_label = {e.get("label", "").lower(): e for e in index.values()}
    added = 0
    v = 2000
    for year, label, who, desc, url, tipping in ROBOTS:
        e = {
            "id": eid(label, year, who), "year": year, "value": v, "label": label,
            "category": CAT_ROBOT, "whoWhat": who, "description": desc, "url": url,
            "timestamp": f"{int(year)}-06-01T00:00:00", "tipping": tipping,
            "s_curve_phase": 1 if year < 1950 else (3 if year < 2000 else 4),
            "pharmakon_remedy_percent": 55, "pharmakon_poison_percent": 45,
            "convergences": "Robotique + IA + capteurs + actionneurs + cloud", "grand_filter_analysis": "Automatisation du travail et de la guerre.",
            "final_note": "Ils travaillent pour nous. Enfin, pour l'instant.",
        }
        v += 700
        index[e["id"]] = {**index.get(e["id"], {}), **e}
        by_label[label.lower()] = index[e["id"]]
        added += 1
    for work, author, fyear, real_label, pitch in FICTION_LINKS:
        fe = {
            "id": eid(work, fyear, author), "year": fyear, "value": 1500, "label": work,
            "category": CAT_FICTION, "whoWhat": author, "description": pitch,
            "url": "https://fr.wikipedia.org/wiki/" + work.split(" (")[0].replace(" ", "_"),
            "timestamp": f"{int(fyear)}-06-01T00:00:00", "tipping": False,
            "s_curve_phase": 2, "pharmakon_remedy_percent": 50, "pharmakon_poison_percent": 50,
            "convergences": "Fiction + robotique + IA", "grand_filter_analysis": "La fiction comme avertissement.",
            "final_note": "On avait prévenu.",
        }
        rl = real_label.lower()
        real = by_label.get(rl)
        if real is not None:
            fe["realYear"] = real.get("year")
            pb = real.get("predictedBy") or []
            if work not in pb:
                pb.append(work)
            real["predictedBy"] = pb
        index[fe["id"]] = {**index.get(fe["id"], {}), **fe}
        added += 1
    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    cats = sorted({e.get("category") for e in out})
    print(f"+ {added} events robotique/fiction, total {len(out)}, {len(cats)} catégories: {cats}")


if __name__ == "__main__":
    main()
