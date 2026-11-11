#!/usr/bin/env python3
"""Remplit les trous des courbes : jalons intermédiaires RÉELS par catégorie (histoire continue).
Ignore ceux dont le label existe déjà. Verrouillé, idempotent."""
import fcntl
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"

# (year, label, who, category, desc)
EVENTS = [
    # INDUSTRIE & ROBOTS (HARDWARE/ROBOTIQUE) — combler 850 -> 1942
    (500, "Moulin à eau (Persia)", "Ingénieurs persans", "🟡 HARDWARE", "Première machine hydraulique industrielle connue."),
    (1180, "Moulin à vent (Europe)", "Croisés / ingénieurs européens", "🟡 HARDWARE", "Moulin à vent à axe horizontal : mécanisation de la mouture."),
    (1280, "Lunettes (Venise)", "Alessandro della Spina", "🟡 HARDWARE", "Premières lunettes correctrices produites à Venise."),
    (1440, "Imprimerie (Gutenberg)", "Johannes Gutenberg", "🟡 HARDWARE", "Caractères mobiles métalliques : imprimerie de masse."),
    (1712, "Machine à vapeur atmosphérique (Newcomen)", "Thomas Newcomen", "🟡 HARDWARE", "Première machine à vapeur industrielle (pompage des mines)."),
    (1735, "Chronomètre de marine H4 (Harrison)", "John Harrison", "🟡 HARDWARE", "Mesure de la longitude en mer : navigation de précision."),
    (1769, "Machine à vapeur (Watt)", "James Watt", "🟡 HARDWARE", "Condenseur séparé : la vapeur devient moteur universel."),
    (1804, "Locomotive à vapeur (Trevithick)", "Richard Trevithick", "🟡 HARDWARE", "Première locomotive ferroviaire."),
    (1839, "Photographie (daguerréotype)", "Louis Daguerre", "🟡 HARDWARE", "Première image photographique fixée."),
    (1844, "Télégraphe électrique (Morse)", "Samuel Morse", "🟡 HARDWARE", "Première ligne longue distance : « What hath God wrought »."),
    (1876, "Téléphone (Bell)", "Alexander Graham Bell", "🟡 HARDWARE", "Transmission électrique de la voix."),
    (1879, "Ampoule à incandescence (Edison)", "Thomas Edison", "🟡 HARDWARE", "Éclairage électrique domestique."),
    (1886, "Automobile (Benz Patent-Motorwagen)", "Karl Benz", "🟡 HARDWARE", "Premier véhicule à moteur à combustion."),
    (1895, "Radio (Marconi)", "Guglielmo Marconi", "🟡 HARDWARE", "Télégraphie sans fil transatlantique."),
    (1913, "Chaîne de montage (Ford)", "Henry Ford", "🟡 HARDWARE", "Production de masse automobile."),
    (1927, "Télévision mécanique (Baird)", "John Logie Baird", "🟡 HARDWARE", "Première transmission d'image télévisée."),
    (1947, "Transistor (Bell Labs)", "Bardeen, Brattain, Shockley", "🟡 HARDWARE", "Le composant qui remplace le tube à vide."),
    (1958, "Circuit intégré (Kilby/Noyce)", "Jack Kilby / Robert Noyce", "🟡 HARDWARE", "Plusieurs transistors sur une seule puce."),
    (1960, "Laser (Maiman)", "Theodore Maiman", "🟡 HARDWARE", "Lumière cohérente amplifiée : mesure, communication, chirurgie."),
    (1969, "ARPANET (1er nœud UCLA)", "ARPA / UCLA", "🔴 RÉSEAU", "Premier réseau informatique à commutation de paquets."),
    (1971, "Microprocesseur (Intel 4004)", "Intel", "🟡 HARDWARE", "Toute la puissance d'un ordinateur sur une puce."),
    (1981, "PC IBM", "IBM", "🟡 HARDWARE", "L'ordinateur personnel entre dans les bureaux et les foyers."),
    (1983, "Impression 3D (stéréolithographie, Chuck Hull)", "3D Systems", "🟡 HARDWARE", "Fabrication additive : on imprime des objets."),
    (1989, "World Wide Web (Tim Berners-Lee)", "Tim Berners-Lee (CERN)", "🔴 RÉSEAU", "HTTP/HTML/URL : le Web devient public."),
    # ESPACE
    (1903, "Vol motorisé (Wright)", "Frères Wright", "🟣 ESPACE", "Premier vol contrôlé plus lourd que l'air."),
    (1927, "Traversée Atlantique en avion (Lindbergh)", "Charles Lindbergh", "🟣 ESPACE", "New York-Paris sans escale."),
    (1944, "Fusée V2 (von Braun)", "Wernher von Braun", "🟣 ESPACE", "Premier engin à atteindre l'espace (100 km)."),
    (1957, "Spoutnik 1", "URSS", "🟣 ESPACE", "Premier satellite artificiel en orbite."),
    (1961, "Premier homme dans l'espace (Gagarine)", "Youri Gagarine", "🟣 ESPACE", "Vostok 1 : 108 minutes en orbite."),
    (1969, "Apollo 11 (premier pas sur la Lune)", "Neil Armstrong", "🟣 ESPACE", "« Un petit pas pour l'homme... »"),
    (1971, "Saliout 1 (1re station spatiale)", "URSS", "🟣 ESPACE", "Première station spatiale habitée."),
    (1981, "Navette spatiale Columbia (1er vol)", "NASA", "🟣 ESPACE", "Premier vaisseau spatial réutilisable."),
    (1990, "Hubble en orbite", "NASA/ESA", "🟣 ESPACE", "Télescope spatial : images de l'univers profond."),
    (1998, "ISS (début assemblage)", "NASA/Roscosmos/ESA", "🟣 ESPACE", "Station spatiale internationale."),
    (2012, "Curiosity sur Mars", "NASA JPL", "🟣 ESPACE", "Premier labo mobile martien."),
    (2015, "New Horizons survole Pluton", "NASA", "🟣 ESPACE", "Premières images rapprochées de Pluton."),
    (2021, "Perseverance + Ingenuity sur Mars", "NASA JPL", "🟣 ESPACE", "Premier hélicoptère sur une autre planète."),
    (2022, "JWST (James Webb) en orbite L2", "NASA/ESA/CSA", "🟣 ESPACE", "Télescope infrarouge : premières galaxies de l'univers."),
    # IA & COGNITION
    (1943, "Perceptron (McCulloch & Pitts)", "McCulloch & Pitts", "🔵 COGNITION", "Premier modèle mathématique du neurone artificiel."),
    (1950, "Test de Turing", "Alan Turing", "🔵 COGNITION", "« Les machines peuvent-elles penser ? »"),
    (1956, "Conférence de Dartmouth (l'IA est nommée)", "John McCarthy et al.", "🔵 COGNITION", "Acte de naissance du domaine « intelligence artificielle »."),
    (1957, "Perceptron (Rosenblatt)", "Frank Rosenblatt", "🔵 COGNITION", "Premier réseau de neurones apprenant."),
    (1959, "LISP (langage IA)", "John McCarthy", "🔵 COGNITION", "Langage de référence du symbolic AI."),
    (1966, "ELIZA (chatbot)", "Joseph Weizenbaum", "🔵 COGNITION", "Premier programme conversant."),
    (1972, "PROLOG", "Alain Colmerauer", "🔵 COGNITION", "Langage de logique et raisonnement automatique."),
    (1986, "Rétropropagation (Rumelhart)", "Rumelhart, Hinton, Williams", "🔵 COGNITION", "L'apprentissage profond redevient viable."),
    (1997, "Deep Blue bat Kasparov", "IBM", "🔵 COGNITION", "L'échiquier tombe : première victoire machine sur champion du monde."),
    (2011, "IBM Watson gagne Jeopardy", "IBM", "🔵 COGNITION", "Compréhension du langage naturel en quiz."),
    (2016, "AlphaGo bat Lee Sedol", "DeepMind", "🔵 COGNITION", "Le Go tombe à son tour : intuition machine au plus haut niveau."),
    (2017, "Transformer (Attention is all you need)", "Vaswani et al. (Google)", "🔵 COGNITION", "Architecture qui fonde tous les LLM modernes."),
    (2018, "BERT / GPT-1", "Google / OpenAI", "🔵 COGNITION", "Préentraînement génératif + compréhension bidirectionnelle."),
    (2020, "GPT-3 (175 Md paramètres)", "OpenAI", "🔵 COGNITION", "Few-shot learning à grande échelle."),
    (2022, "ChatGPT / LLM grand public", "OpenAI", "🔵 COGNITION", "L'IA conversante entre dans la vie de milliards de personnes."),
    # VIVANT & SANTÉ
    (1928, "Pénicilline (Fleming)", "Alexander Fleming", "💊 MÉDECINE", "Premier antibiotique."),
    (1944, "Premier rein artificiel (Kolf)", "Willem Kolf", "💊 MÉDECINE", "Dialyse : sauver l'insuffisance rénale."),
    (1952, "Pompe cœur-poumon (Gibbon)", "John Gibbon", "💊 MÉDECINE", "Première chirurgie à cœur ouvert."),
    (1953, "Double hélice ADN (Watson & Crick)", "Watson & Crick", "💊 MÉDECINE", "Structure de l'hérédité élucidée."),
    (1967, "Première transplantation cardiaque (Barnard)", "Christiaan Barnard", "💊 MÉDECINE", "Le cœur humain transplanté pour la première fois."),
    (1978, "Premier bébé né de FIV (Louise Brown)", "Edwards & Steptoe", "🟢 BIOTECH", "Fécondation in vitro : la reproduction médicalisée."),
    (1983, "PCR (amplification ADN)", "Kary Mullis", "🟢 BIOTECH", "Copier l'ADN à volonté : génétique moléculaire."),
    (1990, "Projet Génome humain lancé", "NIH/DOE", "🟢 BIOTECH", "Lire les 3 milliards de lettres de l'ADN humain."),
    (1996, "Dolly (1er mammifère cloné)", "Roslin Institute", "🟢 BIOTECH", "Clonage d'un mammifère adulte."),
    (2003, "Génome humain complet", "Consortium public", "🟢 BIOTECH", "Séquence de référence de l'espèce humaine."),
    (2007, "iPS (cellules souches pluripotentes induites)", "Shinya Yamanaka", "🟢 BIOTECH", "Reprogrammer une cellule adulte en souche : médecine régénérative."),
    (2012, "CRISPR-Cas9", "Charpentier & Doudna", "🟢 BIOTECH", "Édition génomique programmable."),
    (2020, "Vaccins ARNm (COVID-19)", "BioNTech/Pfizer, Moderna", "💊 MÉDECINE", "Plateforme ARNm déployée à l'échelle mondiale en mois."),
    # NOOSPHÈRE & RÉSEAUX
    (1876, "Téléphone (Bell)", "Alexander Graham Bell", "🔴 RÉSEAU", "Voix à distance."),
    (1920, "Première radio commerciale (KDKA)", "Westinghouse", "🔴 RÉSEAU", "Médias de masse."),
    (1946, "ENIAC (1er ordinateur électronique)", "Eckert & Mauchly", "🔴 RÉSEAU", "18 000 tubes à vide, 5 000 calculs/s."),
    (1969, "ARPANET", "ARPA", "🔴 RÉSEAU", "Ancêtre d'Internet."),
    (1989, "Web (CERN)", "Tim Berners-Lee", "🔴 RÉSEAU", "Le document hypertexte mondial."),
    (1991, "Linux (noyau open source)", "Linus Torvalds", "🔴 RÉSEAU", "Le logiciel libre devient infrastructure mondiale."),
    (1995, "Java / JavaScript", "Sun / Netscape", "🔴 RÉSEAU", "Le Web devient programmable et interactif."),
    (2004, "Facebook (réseau social de masse)", "Mark Zuckerberg", "🔴 RÉSEAU", "800 millions d'utilisateurs en 8 ans."),
    (2007, "iPhone (smartphone tactile)", "Apple", "🔴 RÉSEAU", "Internet dans la poche de tout le monde."),
    (2010, "4G (déploiement mondial)", "Opérateurs", "🔴 RÉSEAU", "Internet mobile haut débit."),
    # POLITIQUE
    (1945, "ONU fondée", "Nations unies", "🏛️ POLITIQUE", "Ordre international d'après-guerre."),
    (1948, "Déclaration universelle des droits de l'homme", "ONU", "🏛️ POLITIQUE", "Droits fondamentaux universels."),
    (1957, "Traité de Rome (CEE)", "6 États européens", "🏛️ POLITIQUE", "Marché commun européen."),
    (1989, "Chute du mur de Berlin", "Peuples d'Europe de l'Est", "🏛️ POLITIQUE", "Fin de la guerre froide."),
    (1992, "Sommet de Rio (développement durable)", "ONU", "🏛️ POLITIQUE", "Première conscience écologique mondiale institutionnalisée."),
    (1997, "Protocole de Kyoto", "ONU", "🏛️ POLITIQUE", "Premier traité climat à objectifs chiffrés."),
    (2015, "Accord de Paris (COP21)", "195 États", "🏛️ POLITIQUE", "Objectif +1,5/+2 °C."),
    (2024, "EU AI Act adopté", "Union européenne", "🏛️ POLITIQUE", "Première grande loi sur l'IA (approche par risque)."),
    # ENTROPIE & CYBER
    (1988, "Ver Morris", "Robert Tappan Morris", "☠️ RISQUES CYBER", "Premier ver de masse sur Internet (~10% des machines)."),
    (2000, "ILOVEYOU", "Onel de Guzman", "☠️ RISQUES CYBER", "45 M machines en quelques jours."),
    (2007, "Cyberattaques contre l'Estonie", "Botnets", "☠️ RISQUES CYBER", "Première cyberguerre d'État documentée."),
    (2010, "Stuxnet", "NSA / renseignement israélien", "☠️ RISQUES CYBER", "Première cyberarme (centrifugeuses iraniennes)."),
    (2017, "WannaCry", "Lazarus (Corée du Nord)", "☠️ RISQUES CYBER", "Ransomware mondial (EternalBlue) : 200 000 machines, 150 pays."),
    (2017, "NotPetya", "Sandworm (GRU)", "☠️ RISQUES CYBER", "10 Md$ de dégâts, pire cyberattaque de l'histoire."),
    (2020, "SolarWinds (supply chain)", "Cozy Bear (SVR)", "☠️ RISQUES CYBER", "18 000 organisations compromises via Orion."),
    (2021, "Colonial Pipeline (ransomware)", "DarkSide", "☠️ RISQUES CYBER", "Plus grand oléoduc US paralysé."),
    (1988, "Premier pare-feu commercial", "DEC", "☠️ RISQUES CYBER", "Sécurité réseau : naissance du pare-feu."),
    # NOOSPHÈRE (médias/mèmes)
    (1450, "Imprimerie (Gutenberg)", "Johannes Gutenberg", "✨ NOOSPHÈRE", "Diffusion de masse du savoir imprimé."),
    (1837, "Photographie (daguerréotype)", "Daguerre & Niépce", "✨ NOOSPHÈRE", "L'image devient reproductible à l'infini."),
    (1920, "Radio commerciale", "KDKA Pittsburgh", "✨ NOOSPHÈRE", "Un média de masse dans chaque foyer."),
    (1936, "BBC (1re TV régulière)", "BBC", "✨ NOOSPHÈRE", "Télévision de masse."),
    (1969, "ARPANET", "ARPA", "✨ NOOSPHÈRE", "Les machines commencent à parler entre elles."),
    (2004, "Facebook", "Mark Zuckerberg", "✨ NOOSPHÈRE", "Réseau social planétaire."),
    (2006, "Twitter (microblogging)", "Jack Dorsey", "✨ NOOSPHÈRE", "Le temps réel mondial en 140 caractères."),
    (2010, "Instagram (photo mobile)", "Kevin Systrom", "✨ NOOSPHÈRE", "L'image totale."),
    (2016, "TikTok (vidéo courte algorithmique)", "ByteDance", "✨ NOOSPHÈRE", "L'attention mondiale pilotée par algorithme."),
    # SINGULARITÉ (estimations)
    (2015, "Stade Singularité estimé 0.5", "Cortex Loom Analysis", "⚪ SINGULARITÉ", "Début de la phase d'accélération."),
    (2020, "Stade Singularité estimé 0.65", "Cortex Loom Analysis", "⚪ SINGULARITÉ", "Accélération des LLM."),
]


def eid(label, year, who):
    key = f"{label.strip().lower()}|{round(float(year), 2)}|{(who or '').strip().lower()}"
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    have = {e.get("label", "").lower() for e in data}
    added = 0
    for year, label, who, cat, desc in EVENTS:
        if label.lower() in have:
            continue
        e = {
            "id": eid(label, year, who), "year": year, "value": 1000, "label": label,
            "category": cat, "whoWhat": who, "description": desc,
            "url": "#", "timestamp": f"{int(year)}-06-01T00:00:00", "tipping": False,
            "s_curve_phase": 1 if year < 1900 else (2 if year < 1980 else 3),
            "pharmakon_remedy_percent": 60, "pharmakon_poison_percent": 40,
            "convergences": "Jalon historique intermédiaire",
            "grand_filter_analysis": "Étape de la chaîne technologique.",
            "final_note": "Le fil se resserre.",
        }
        data.append(e)
        have.add(label.lower())
        added += 1
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(f"+ {added} jalons intermédiaires, total {len(data)}")
    # rapport des plus grands trous par groupe
    import math
    GROUP_OF = {}
    for cat, grp in [('🟡 HARDWARE','⚙️ INDUSTRIE & ROBOTS'),('🤖 ROBOTIQUE','⚙️ INDUSTRIE & ROBOTS'),('🟣 ESPACE','🚀 ESPACE'),('🔵 COGNITION','🧠 IA & COGNITION'),('⚪ SINGULARITÉ','🧠 IA & COGNITION'),('✨ NOOSPHÈRE','🌍 NOOSPHÈRE & RÉSEAUX'),('🔴 RÉSEAU','🌍 NOOSPHÈRE & RÉSEAUX'),('🟢 BIOTECH','🧬 VIVANT & SANTÉ'),('💊 MÉDECINE','🧬 VIVANT & SANTÉ'),('🏛️ POLITIQUE','🏛️ POLITIQUE'),('☢️ ENTROPIE','☢️ ENTROPIE & CYBER'),('☠️ RISQUES CYBER','☢️ ENTROPIE & CYBER'),('🔮 IMAGINAIRE','🎬 FICTION')]:
        GROUP_OF[cat] = grp
    import collections
    gy = collections.defaultdict(list)
    for e in data:
        if e.get("year", 0) <= 2026.9:
            gy[GROUP_OF.get(e.get("category"), e.get("category"))].append(e["year"])
    for g, ys in gy.items():
        ys.sort()
        gaps = [(ys[i+1]-ys[i], ys[i], ys[i+1]) for i in range(len(ys)-1)]
        mg = max(gaps) if gaps else (0,0,0)
        print(f"  {g}: max trou {mg[0]:.0f} ans ({mg[1]:.0f} -> {mg[2]:.0f})")


if __name__ == "__main__":
    main()
