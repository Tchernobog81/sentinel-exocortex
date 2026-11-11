#!/usr/bin/env python3
"""v171 : courbe dédiée Horloge de l'Apocalypse (tous les réglages officiels 1947-2026 +
justifications du Bulletin) + jalons majeurs POLITIQUE (SDN, Westphalie, Magna Carta...).
- Recatégorise les anciens events "Horloge:" (☢️ ENTROPIE) en ⏰ HORLOGE (supprimés puis
  recréés canoniques, avec champ doomsday_minutes).
- Ajoute les réglages manquants (2019, 2021, 2022, 2024, 2025, 2026) et corrige 1960 (15 min).
Idempotent, verrouillé."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

DATA = Path('/Users/tcherno/sentinel-exocortex/loom_data.json')
CAT = "⏰ HORLOGE"

# (year, minutes_to_midnight as float, label, justification officielle)
CLOCK = [
    (1947, 7.0, "⏰ 1947 — 7 min avant minuit", "Création de l'horloge par le Bulletin of the Atomic Scientists (dessin de Martyl Langsdorf). Seule menace alors : l'arme nucléaire, monopole américain."),
    (1949, 3.0, "⏰ 1949 — 3 min avant minuit", "L'URSS teste sa première bombe A (RDS-1) : début de la course aux armements. « Nous ne conseillons pas aux Américains que le jour J est proche, mais ils ont raison d'être profondément alarmés. »"),
    (1953, 2.0, "⏰ 1953 — 2 min avant minuit", "Les États-Unis (oct. 1952) puis l'URSS testent la bombe H à neuf mois d'intervalle. Record de proximité jusqu'en 2017."),
    (1960, 15.0, "⏰ 1960 — 15 min avant minuit", "Coopération malgré la rhétorique : crise de Suez gérée, Pugwash, Année géophysique internationale. Point le plus sûr de la Guerre froide."),
    (1963, 12.0, "⏰ 1963 — 12 min avant minuit", "Traité d'interdiction partielle des essais nucléaires (PTBT) après la crise des missiles de Cuba : premier progrès concret de maîtrise de la course."),
    (1968, 7.0, "⏰ 1968 — 7 min avant minuit", "La France et la Chine entrent dans le club nucléaire ; guerres chaudes (Vietnam, Cachemire 1965, Six-Jours 1967) menacent de dégénérer."),
    (1969, 10.0, "⏰ 1969 — 10 min avant minuit", "Traité de non-prolifération (TNP) signé par presque tous les États ; espoir prudent de désarmement progressif."),
    (1972, 12.0, "⏰ 1972 — 12 min avant minuit", "Accords SALT I et ABM entre USA et URSS : parité recherchée, plafond sur les lanceurs et les antimissiles."),
    (1974, 9.0, "⏰ 1974 — 9 min avant minuit", "L'Inde teste sa bombe ; les MIRV multiplient les têtes ; les négociations SALT II stagnent."),
    (1980, 7.0, "⏰ 1980 — 7 min avant minuit", "« Dérive accélérée vers le désastre mondial » : échec de SALT II, crises des ressources, incapacité des institutions internationales."),
    (1981, 4.0, "⏰ 1981 — 4 min avant minuit", "Invasion soviétique de l'Afghanistan, élection de Reagan, boycott des JO de Moscou : la posture nucléaire américaine se durcit."),
    (1984, 3.0, "⏰ 1984 — 3 min avant minuit", "Dialogue USA-URSS quasiment rompu ; Reagan lance l'Initiative de défense stratégique (« Star Wars »). Point le plus critique de la Guerre froide."),
    (1988, 6.0, "⏰ 1988 — 6 min avant minuit", "Traité INF : première élimination d'une catégorie entière d'armes nucléaires (missiles intermédiaires européens)."),
    (1990, 10.0, "⏰ 1990 — 10 min avant minuit", "Chute du mur de Berlin ; révolutions de 1989 en Europe de l'Est : le risque de guerre nucléaire totale diminue fortement."),
    (1991, 17.0, "⏰ 1991 — 17 min avant minuit", "Fin officielle de la Guerre froide, signature de START I, désalerte unilatérale des forces : point le PLUS éloigné de minuit depuis 1947."),
    (1995, 14.0, "⏰ 1995 — 14 min avant minuit", "Incident de la fusée scientifique norvégienne (Yeltsin hésite à répliquer) ; plus de 40 000 armes toujours déployées ; matériaux fissiles mal sécurisés en ex-URSS."),
    (1998, 9.0, "⏰ 1998 — 9 min avant minuit", "Essais nucléaires de l'Inde puis du Pakistan à trois semaines d'intervalle : « symptôme de l'échec de la communauté internationale » sur la non-prolifération."),
    (2002, 7.0, "⏰ 2002 — 7 min avant minuit", "11 Septembre : crainte du nucléaire aux mains d'acteurs non étatiques ; matériaux fissiles non comptabilisés ; les USA rejettent plusieurs traités et retirent l'ABM."),
    (2007, 5.0, "⏰ 2007 — 5 min avant minuit", "Essai nucléaire nord-coréen ; le changement climatique entre officiellement dans les menaces prises en compte."),
    (2010, 6.0, "⏰ 2010 — 6 min avant minuit", "Nouveau traité START, coopération climatique (Copenhague/Cancun) : léger recul du danger."),
    (2012, 5.0, "⏰ 2012 — 5 min avant minuit", "Prolifération non résolue, modernisation des arsenaux, armes « tactiques » toujours déployées : l'action politique mondiale fait défaut."),
    (2015, 3.0, "⏰ 2015 — 3 min avant minuit", "Modernisation des arsenaux nucléaires et décarbonisation insuffisante : l'échec du leadership mondial rapproche minuit."),
    (2017, 2.5, "⏰ 2017 — 2 min 30 avant minuit", "Montée du nationalisme (Trump, Brexit), crise nord-coréenne, remise en cause des faits et désinformation : 150 secondes, du jamais vu."),
    (2018, 2.0, "⏰ 2018 — 2 min avant minuit", "Échec des dirigeants à traiter les menaces nucléaires et climatiques ; rhétorique « hyperbolique et provocante » USA-Corée du Nord."),
    (2019, 2.0, "⏰ 2019 — 2 min avant minuit (inchangé)", "Réglage inchangé : la guerre de l'information contre les démocraties aggrave les deux menaces existantes."),
    (2020, 100/60, "⏰ 2020 — 100 s avant minuit", "Retrait américain du traité INF, rivalité des superpuissances, climat qui s'aggrave, pandémie : passage en secondes pour la première fois."),
    (2021, 100/60, "⏰ 2021 — 100 s avant minuit (inchangé)", "Réglage inchangé : gestion de la COVID-19, désinformation et course aux armements toujours non traitées."),
    (2022, 100/60, "⏰ 2022 — 100 s avant minuit (inchangé)", "Réglage inchangé en janvier 2022 : tensions autour de l'Ukraine, climat et prolifération non traitées."),
    (2023, 90/60, "⏰ 2023 — 90 s avant minuit", "Invasion russe de l'Ukraine et risque d'escalade nucléaire, climat, menaces biologiques (Covid), désinformation et technologies disruptives."),
    (2024, 90/60, "⏰ 2024 — 90 s avant minuit (inchangé)", "Réglage inchangé : Ukraine, Gaza, année climatique la plus chaude, progrès de l'IA non régulée."),
    (2025, 89/60, "⏰ 2025 — 89 s avant minuit", "L'IA militaire et son usage sur les réseaux sociaux ajoutés comme nouveau facteur de risque."),
    (2026, 85/60, "⏰ 2026 — 85 s avant minuit", "27 janvier 2026 : RECORD historique — le plus proche de minuit depuis 1947. « Failure of leadership » : aucune action significative n'a repoussé l'horloge."),
]

# Jalons majeurs POLITIQUE manquants
POL = [
    (-1754, "Code d'Hammurabi", "Babylone", "Premier code de lois écrit connu : état de droit codifié."),
    (1215, "Magna Carta", "Angleterre (Jean sans Terre)", "Le roi est soumis à la loi : naissance des libertés fondamentales."),
    (1648, "Traité de Westphalie", "Saint-Empire / Europe", "Souveraineté des États et non-ingérence : acte fondateur du droit international moderne."),
    (1776, "Déclaration d'indépendance américaine", "13 colonies", "« Tous les hommes naissent libres et égaux » : première république moderne fondée sur des droits."),
    (1789, "Déclaration des droits de l'homme et du citoyen", "Révolution française", "Droits naturels, souveraineté populaire, laïcité des principes."),
    (1848, "Suffrage universel masculin (France)", "IIe République", "Vote pour tous les citoyens hommes : la démocratie de masse naît."),
    (1871, "Commune de Paris", "Insurgés parisiens", "Première tentative de gouvernement populaire autogéré ; réprimée dans le sang."),
    (1920, "Société des Nations", "28 États fondateurs (traité de Versailles)", "Première organisation mondiale de sécurité collective ; le multilatéralisme institutionnalisé."),
    (1946, "Dissolution de la Société des Nations", "SDN", "Échec relatif (absence des USA, montée des fascismes) ; ses agences deviennent l'ONU."),
    (1948, "Plan Marshall", "USA (George Marshall)", "13 Md$ pour reconstruire l'Europe et contenir l'expansion soviétique : soft power à grande échelle."),
    (1949, "OTAN", "12 États fondateurs", "Alliance militaire atlantique : dissuasion nucléaire collective."),
    (1955, "Conférence de Bandung", "29 États afro-asiatiques", "Naissance du mouvement des non-alignés et du « Tiers-Monde » politique."),
    (1975, "Acte final d'Helsinki (CSCE)", "35 États", "Détente : droits de l'homme liés à la sécurité européenne, reconnaissance des frontières."),
    (1992, "Traité de Maastricht", "12 États européens", "Union européenne, citoyenneté européenne, monnaie unique annoncée : fédéralisme en marche."),
    (1998, "Statut de Rome (CPI)", "120 États", "Première cour pénale internationale permanente : justice transnationale."),
    (2002, "Cour pénale internationale en vigueur", "CPI (La Haye)", "Juridiction permanente sur génocides, crimes contre l'humanité et crimes de guerre."),
]


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    # supprime les anciens events horloge (seront recréés canoniques)
    old = [e for e in data if e.get("label", "").startswith("Horloge:")]
    data = [e for e in data if not e.get("label", "").startswith("Horloge:")]
    # l'event sentinel "Horloge de l'Apocalypse YYYY" -> recatégorisé
    for e in data:
        if e.get("label", "").startswith("Horloge de l'Apocalypse"):
            e["category"] = CAT
            e["label"] = e["label"].replace("Horloge de l'Apocalypse", "⏰ Horloge")
    removed = len(old)

    have = {e.get("label", "").lower() for e in data}
    added = 0
    now = datetime.now().isoformat()

    def mk(year, label, who, cat, desc, tipping=True, minutes=None):
        nonlocal added
        if label.lower() in have:
            return
        e = {
            "id": eid(label, year, who), "year": float(year), "value": 1000, "label": label,
            "category": cat, "whoWhat": who, "description": desc,
            "url": "https://thebulletin.org/doomsday-clock/timeline/",
            "timestamp": f"{int(year)}-01-27T00:00:00" if year < 2000 else now,
            "tipping": tipping, "s_curve_phase": 5 if year >= 2000 else 3,
            "pharmakon_remedy_percent": 10, "pharmakon_poison_percent": 90,
            "convergences": "Convergence des menaces nucléaires, climatiques, biologiques et technologiques.",
            "grand_filter_analysis": "Indicateur synthétique de proximité du Grand Filtre.",
            "final_note": "L'aiguille avance vers minuit.",
        }
        if minutes is not None:
            e["doomsday_minutes"] = minutes
        data.append(e)
        have.add(label.lower())
        added += 1

    for year, minutes, label, just in CLOCK:
        mk(year, label, "Bulletin of the Atomic Scientists", CAT, just, True, minutes)
    for year, label, who, desc in POL:
        mk(year, label, who, "🏛️ POLITIQUE", desc, True, None)

    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    n_clock = sum(1 for e in data if e.get("category") == CAT)
    print(f"- {removed} anciens events horloge remplacés, + {added} events (horloge: {n_clock}), total {len(data)}")


if __name__ == "__main__":
    main()
