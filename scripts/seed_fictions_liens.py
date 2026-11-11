#!/usr/bin/env python3
"""v172 : fictions d'avant Frankenstein (depuis -2100) + réparation des liens fiction->réel.
- Ajoute ~12 oeuvres/essais fictionnels et philosophiques antérieurs à 1818, avec lien
  realLabel/realYear vers l'événement réel correspondant quand cohérent.
- Répare les liens morts ou imprécis (Star Wars -> 'Horloge: 3 min' supprimé en v171, etc.)
  et pose le predictedBy réciproque sur l'événement réel.
Idempotent, verrouillé."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

DATA = Path('/Users/tcherno/sentinel-exocortex/loom_data.json')
CAT = "🔮 IMAGINAIRE"

# (year, label, who, description, tipping, realLabel or None)
FICTIONS = [
    (-2100, "Épopée de Gilgamesh", "Sumer (anonyme)", "Premier récit écrit connu : Gilgamesh cherche la vie éternelle et échoue — la quête d'immortalité hante l'humanité depuis l'écriture.", True, "iPS (Yamanaka)"),
    (-800, "L'Odyssée (Talos, automate de bronze)", "Homère", "Talos, géant de bronze qui garde la Crète : première machine autonome de la littérature.", True, "Unimate, 1er robot industriel"),
    (-700, "Théogonie (Prométhée vole le feu)", "Hésiode", "Le Titan vole le feu des dieux pour les hommes : origine mythique de la maîtrise de l'énergie.", True, "Chicago Pile-1"),
    (-380, "La République (cité idéale gouvernée par la raison)", "Platon", "Philosophie politique : une cité gouvernée par des philosophes-rois — rêve d'une gouvernance rationnelle.", False, "Projet Cybersyn"),
    (-170, "Histoires vraies (voyage sur la Lune)", "Lucien de Samosate", "Premier texte de science-fiction connu : voyage sur la Lune, guerre entre habitants du Soleil et de la Lune.", True, "Apollo 11 (Lune)"),
    (875, "Les Mille et Une Nuits (tapis volant, lampe merveilleuse)", "Anonyme (Perse/Arabe)", "Objets merveilleux : tapis volant, lampe exauçant les vœux — le désir de voler et de commander la matière.", False, "Vol des Wright"),
    (1320, "La Divine Comédie (Enfer, Purgatoire, Paradis)", "Dante Alighieri", "Cartographie de l'au-delà et de la transcendance — l'humanité contemple déjà l'infini.", False, None),
    (1516, "L'Utopie (île société idéale)", "Thomas More", "Société sans propriété privée ni monnaie : essai fondateur de la pensée sociale réformatrice.", True, "Revenu Universel (Pilotes)"),
    (1602, "La Cité du Soleil", "Tommaso Campanella", "Cité théocratique gouvernée par le savoir : un essai utopique pré-industriel.", False, None),
    (1627, "La Nouvelle Atlantique (Maison de Salomon)", "Francis Bacon", "Institut de recherche dédié au savoir universel « pour le soulagement de la condition humaine » : la science organisée comme moteur du progrès.", True, "World Wide Web (Berners-Lee, CERN)"),
    (1657, "L'Autre Monde (voyage dans la Lune et le Soleil)", "Cyrano de Bergerac", "Voyage lunaire en fusée à ressorts, société solaire : anticipation spatiale et utopique.", True, "Apollo 11 (Lune)"),
    (1726, "Voyages de Gulliver (Laputa, île volante)", "Jonathan Swift", "L'île volante de Laputa et les Houyhnhnms rationnels : satire du progrès et de la raison dévoyée.", False, "Vol des Wright"),
    (1752, "Micromégas (géants de Sirius, voyage interplanétaire)", "Voltaire", "Des êtres de taille stellaire voyagent de planète en planète : la SF cosmique et la relativité des grandeurs.", True, "Perseverance + Ingenuity sur Mars"),
    (1651, "Léviathan (l'État comme machine de paix)", "Thomas Hobbes", "Essai philo : le Léviathan artificiel qui dompte la violence naturelle — la machine étatique comme artefact.", False, None),
]

# réparations de liens (fiction label -> (realLabel, realYear))
LIENS = {
    "Star Wars": ("Navette spatiale Columbia (1er vol)", 1981.0),
    "Vingt mille lieues sous les mers": ("USS Nautilus, 1er sous-marin nucléaire", 1954.0),
    "I, Robot": ("Unimate, 1er robot industriel", 1954.0),
    "Dune": ("Deep Blue bat Kasparov", 1997.3),
    "Blade Runner": ("Atlas (Boston Dynamics)", 2013.0),
    "Tron": ("Métavers (Facebook/Meta)", 2021.0),
    "WarGames": ("Stuxnet", 2010.5),
    "Terminator": ("AlexNet", 2012.7),
    "Retour vers le Futur": ("DARPA Grand Challenge (Stanley)", 2005.0),
    "Ghost in the Shell": ("Neuralink (Humain)", 2024.1),
    "Minority Report": ("Police prédictive algorithmique", 2014.0),
    "Black Mirror": ("Big Data prédictif", 2016.0),
}


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def link(fic, real_label, real_year, data):
    """Pose realLabel/realYear sur la fiction et predictedBy réciproque sur TOUS les
    événements portant ce label (doublons compris)."""
    fic["realLabel"] = real_label
    fic["realYear"] = real_year
    hits = [e for e in data if e.get("label") == real_label and abs((e.get("year") or 0) - real_year) < 1.0]
    for e in hits:
        pb = e.get("predictedBy") or []
        if fic["label"] not in pb:
            pb.append(fic["label"])
        e["predictedBy"] = pb
    return hits[0] if hits else None


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    by_label = {}
    for e in data:
        by_label.setdefault(e.get("label"), []).append(e)
    have = {e.get("label", "").lower() for e in data}
    now = datetime.now().isoformat()
    added = 0

    for year, label, who, desc, tip, real in FICTIONS:
        if label.lower() in have:
            fic = by_label[label][0]
            if real and not fic.get("realLabel"):
                link(fic, real, next(e["year"] for e in data if e.get("label") == real), data)
            continue
        fic = {
            "id": eid(label, year, who), "year": float(year), "value": 1000, "label": label,
            "category": CAT, "whoWhat": who, "description": desc, "url": "#",
            "timestamp": f"{int(year)}-06-01T00:00:00" if year < 1900 else now,
            "tipping": tip, "s_curve_phase": 1,
            "pharmakon_remedy_percent": 50, "pharmakon_poison_percent": 50,
            "convergences": "La fiction teste les futurs avant qu'ils n'arrivent.",
            "grand_filter_analysis": "Œuvre fondatrice de l'imaginaire collectif.",
            "final_note": "Déjà écrit, déjà prédit.",
        }
        if real:
            tgt = next((e for e in data if e.get("label") == real), None)
            if tgt:
                link(fic, real, tgt["year"], data)
        data.append(fic)
        have.add(label.lower())
        added += 1

    fixed = 0
    for fic_label, (real_label, real_year) in LIENS.items():
        for fic in by_label.get(fic_label, []):
            if fic.get("category") != CAT:
                continue
            old = fic.get("realLabel")
            tgt = link(fic, real_label, real_year, data)
            if tgt is not None:
                fixed += 1
                if old != real_label:
                    print(f"  lien: {fic_label} : {old!r} -> {real_label!r}")

    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    n_fic = sum(1 for e in data if e.get("category") == CAT)
    print(f"+ {added} fictions antiques, {fixed} liens réparés, fictions: {n_fic}, total {len(data)}")


if __name__ == "__main__":
    main()
