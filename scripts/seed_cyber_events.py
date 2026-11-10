#!/usr/bin/env python3
"""Seed de la 11e courbe "☠️ RISQUES CYBER" : attaques cyber majeures, des origines à aujourd'hui.
Upsert par id stable dans loom_data.json (ne crée jamais de doublon)."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"
CAT = "☠️ RISQUES CYBER"

# (year, label, whoWhat, description, url, tipping)
EVENTS = [
    (1988.9, "Ver Morris (1ère cyberattaque de masse)", "Robert Tappan Morris",
     "Premier ver informatique à se propager via Internet : ~10% des machines connectées infectées (6000 serveurs).",
     "https://fr.wikipedia.org/wiki/Ver_Morris", True),
    (1999.2, "Virus Melissa", "David L. Smith",
     "Macro Word se propageant par e-mail ; paralysant des centaines de milliers de postes.",
     "https://fr.wikipedia.org/wiki/Melissa_(virus)", False),
    (2000.4, "ILOVEYOU", "Onel de Guzman",
     "Ver par e-mail « I love you » : 45 millions de machines infectées en quelques jours, milliards de dégâts.",
     "https://fr.wikipedia.org/wiki/ILOVEYOU", True),
    (2001.6, "Code Red", "Attaquants inconnus",
     "Ver ciblant les serveurs IIS de Microsoft : 359 000 serveurs infectés en 24h, défiguration de sites.",
     "https://fr.wikipedia.org/wiki/Code_Red_(ver)", False),
    (2003.1, "SQL Slammer", "Attaquants inconnus",
     "Ver sur Microsoft SQL Server : doublement de sa taille toutes les 8,5s ; 75 000 victimes en 10 min, saturation d'Internet.",
     "https://fr.wikipedia.org/wiki/SQL_Slammer", True),
    (2007.4, "Cyberattaques contre l'Estonie", "Suspects russes",
     "Première « cyberguerre » d'État documentée : botnets massifs contre banques, médias et gouvernement estonien.",
     "https://fr.wikipedia.org/wiki/Cyberattaques_de_2007_contre_l'Estonie", True),
    (2008.6, "Cyberattaques pendant la guerre de Géorgie", "Suspects russes",
     "DDoS coordonnés avec l'offensive militaire contre sites gouvernementaux géorgiens.",
     "https://en.wikipedia.org/wiki/Cyberattacks_during_the_Russo-Georgian_War", False),
    (2010.5, "Stuxnet", "NSA / renseignement israélien (révélé)",
     "Premier cyberarme connu : sabote les centrifugeuses iraniennes de Natanz via Siemens. Change la donne stratégique.",
     "https://fr.wikipedia.org/wiki/Stuxnet", True),
    (2011.2, "Piratage RSA SecurID", "APT (groupe chinois présumé)",
     "Vol des seeds des tokens SecurID, utilisé ensuite contre Lockheed Martin. Cas d'école de supply-chain attack.",
     "https://en.wikipedia.org/wiki/RSA_SecurID_hack", False),
    (2012.6, "Shamoon contre Saudi Aramco", "Groupe Cutting Sword of Justice",
     "Wiper effaçant 30 000 disques d'Aramco, 10% de l'approvisionnement pétrolier mondial menacé.",
     "https://en.wikipedia.org/wiki/Shamoon", False),
    (2014.9, "Piratage Sony Pictures", "Gardes rouges (Lazarus, Corée du Nord présumée)",
     "Vol massif de données + wiper en représailles du film « The Interview » ; première attribution publique à un État.",
     "https://fr.wikipedia.org/wiki/Piratage_de_Sony_Pictures", True),
    (2015.95, "BlackEnergy : coupure de courant en Ukraine", "Sandworm (GRU russe)",
     "Première coupure de courant causée par une cyberattaque : 230 000 foyers ukrainiens privés d'électricité (grid hack).",
     "https://en.wikipedia.org/wiki/BlackEnergy", True),
    (2016.8, "Botnet Mirai", "Paras Jha et al.",
     "Botnet d'objets connectés (caméras, DVR) : DDoS record de 1,1 Tbit/s contre Dyn, paralysant Twitter, Netflix, GitHub.",
     "https://fr.wikipedia.org/wiki/Mirai_(botnet)", True),
    (2016.85, "Piratage du DNC (élection US)", "Fancy Bear / Cozy Bear (GRU russe)",
     "Vol et fuite d'e-mails du parti démocrate américain pendant la présidentielle de 2016.",
     "https://en.wikipedia.org/wiki/Democratic_National_Committee_cyber_attack", False),
    (2017.4, "WannaCry", "Lazarus (Corée du Nord)",
     "Ransomware mondial exploitant EternalBlue (fuite NSA) : 200 000 machines dans 150 pays, NHS britannique paralysé.",
     "https://fr.wikipedia.org/wiki/WannaCry", True),
    (2017.5, "NotPetya", "Sandworm (GRU russe)",
     "Wiper déguisé en ransomware via mise à jour ukrainienne : 10 milliards $ de dégâts, Maersk, FedEx, Merck touchés.",
     "https://fr.wikipedia.org/wiki/NotPetya", True),
    (2017.7, "Fuite Equifax", "Attaquants chinois présumés",
     "Exploitation d'une faille Apache Struts non patchée : 147 millions de dossiers clients exposés.",
     "https://en.wikipedia.org/wiki/Equifax_data_breach", False),
    (2018.9, "Fuite Marriott (500 M clients)", "Attaquants attribués à la Chine",
     "Compromission de la base Starwood sur 4 ans : 500 millions de clients, passeports inclus.",
     "https://en.wikipedia.org/wiki/Marriott_data_breach", False),
    (2020.9, "SolarWinds (compromission de la supply chain)", "Cozy Bear (SVR russe)",
     "Compromission de la plateforme Orion : 18 000 organisations infectées dont ministères US et Microsoft.",
     "https://fr.wikipedia.org/wiki/Piratage_de_SolarWinds", True),
    (2021.9, "Log4Shell", "Attaquants divers",
     "Faille critique zero-day dans Log4j (bibliothèque omniprésente) : exploitation massive à l'échelle d'Internet en jours.",
     "https://fr.wikipedia.org/wiki/Log4j#Log4Shell", True),
    (2021.35, "Colonial Pipeline (ransomware)", "DarkSide",
     "Ransomware sur le plus grand oléoduc US : arrêt d'approvisionnement de la côte Est, rançon de 4,4 M$.",
     "https://en.wikipedia.org/wiki/Colonial_Pipeline_ransomware_attack", True),
    (2022.4, "Ransomware contre le Costa Rica", "Conti",
     "État d'urgence nationale déclaré : administration fiscale et douanes paralysées pendant des semaines.",
     "https://en.wikipedia.org/wiki/2022_Costa_Rica_ransomware_attack", False),
    (2023.4, "MOVEit (fuite de masse via Cleo)", "Cl0p (groupe russophone)",
     "Exploitation zero-day de MOVEit : plus de 2 600 organisations et 90 millions de personnes exposées (Shell, BBC, US DoE...).",
     "https://en.wikipedia.org/wiki/MOVEit_transfer#2023 MOVEit cyberattack", True),
    (2024.55, "Panne mondiale CrowdStrike", "CrowdStrike (erreur de config)",
     "Mise à jour défectueuse : 8,5 millions de machines Windows plantées, compagnies aériennes et hôpitaux paralysés.",
     "https://en.wikipedia.org/wiki/2024_CrowdStrike_incident", True),
    (2025.15, "Vol record Bybit (1,5 Md$)", "Lazarus (Corée du Nord)",
     "Vol de 1,5 milliard $ en cryptomonnaies sur la plateforme Bybit, via compromission de l'infrastructure de signature.",
     "https://en.wikipedia.org/wiki/Bybit_hack", True),
]


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def main():
    import fcntl
    lock_fd = None
    try:
        lock_fd = open(str(DATA) + ".lock", "a+")
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
    except OSError:
        lock_fd = None
    data = json.loads(DATA.read_text(encoding="utf-8"))
    index = {}
    for e in data:
        e.setdefault("id", eid(e.get("label", ""), e.get("year", 0), e.get("whoWhat")))
        index[e["id"]] = e
    added = 0
    v = 1000
    for year, label, who, desc, url, tipping in EVENTS:
        e = {
            "id": eid(label, year, who),
            "year": year,
            "value": v,
            "label": label,
            "category": CAT,
            "whoWhat": who,
            "description": desc,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "tipping": tipping,
            "s_curve_phase": 5 if year >= 2015 else (4 if year >= 2000 else 3),
            "pharmakon_remedy_percent": 5,
            "pharmakon_poison_percent": 95,
            "convergences": "Cyber + IA + géopolitique + supply chain",
            "grand_filter_analysis": "Fragilité des infrastructures critiques face aux acteurs étatiques et criminels.",
            "final_note": "Et on branche tout sur Internet. Génial.",
        }
        v += 800
        if e["id"] not in index:
            index[e["id"]] = e
            added += 1
        else:
            index[e["id"]].update(e)
    out = sorted(index.values(), key=lambda x: x.get("year", 0))
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
    print(f"☠️ RISQUES CYBER: {added} nouveaux événements ajoutés, total {len(out)}")


if __name__ == "__main__":
    main()
