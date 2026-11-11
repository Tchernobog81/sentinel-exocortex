#!/usr/bin/env python3
"""Remplissage massif v2 : jalons intermédiaires réels entre les gros jalons, pour TOUTES
les courbes (objectif: plus de trou > ~80 ans après 800 ap. J.-C., et Antiquité peuplée:
miroirs d'Archimède, abacus, astrolabe, sémaphores...). Ignore les labels existants."""
import fcntl
import hashlib
import json
import os
from pathlib import Path

DATA = Path('/Users/tcherno/sentinel-exocortex/loom_data.json')

# (year, label, who, category, desc, tipping)
E = [
    # --- Antiquité / haut Moyen Âge (INDUSTRIE, NOOSPHÈRE, RÉSEAU) ---
    (-500, "Boulier (Chine)", "Anciens Chinois", "🟡 HARDWARE", "Premier outil de calcul机械isé.", False),
    (-214, "Miroirs d'Archimède (défense de Syracuse)", "Archimède", "🟡 HARDWARE", "Rayons solaires concentrés sur les voiles romaines : arme optique antique.", True),
    (-125, "Mécanisme d'Anticythère", "Grecs (anonyme)", "🟡 HARDWARE", "Premier ordinateur analogique : engrenages de bronze pour l'astronomie.", True),
    (60, "Æolipile (Héron d'Alexandrie)", "Héron d'Alexandrie", "🟡 HARDWARE", "Première machine à vapeur documentée.", False),
    (105, "Papier (Cai Lun)", "Chine Han", "🔴 RÉSEAU", "Invention du papier : révolution de l'écriture.", True),
    (850, "Poudre à canon (Chine)", "Alchimistes chinois", "☢️ ENTROPIE", "Première poudre noire.", False),
    (900, "Moulin à vent vertical (Persia)", "Ingénieurs persans", "🟡 HARDWARE", "Moulins à vent pour moudre le grain.", False),
    (1000, "Boussole magnétique (Chine)", "Alchimistes chinois", "🟡 HARDWARE", "Navigation de précision.", True),
    (1088, "Horloge à eau (Su Song)", "Su Song (Chine)", "🟡 HARDWARE", "Première horloge astronomique à échappement.", False),
    # --- 1100-1440 : communication optique et imprimerie ---
    (1180, "Moulin à vent horizontal (Europe)", "Croisés", "🟡 HARDWARE", "Mécanisation agricole européenne.", False),
    (1280, "Lunettes (Venise)", "Alessandro della Spina", "🟡 HARDWARE", "Optique corrective.", False),
    (1340, "Horloge mécanique (Europe)", "Maîtres horlogers", "🟡 HARDWARE", "Temps mécanique mesurable.", False),
    (1440, "Imprimerie (Gutenberg)", "Johannes Gutenberg", "🟡 HARDWARE", "Caractères mobiles : diffusion de masse.", True),
    (1455, "Bible de Gutenberg imprimée", "Gutenberg", "✨ NOOSPHÈRE", "Premier livre imprimé à grande échelle.", False),
    # --- 1500-1875 : sémaphores, télégraphe optique, signaux ---
    (1684, "Télégraphe optique de Chappe (sémaphore)", "Claude Chappe", "🔴 RÉSEAU", "Ligne Paris-Lille en sémaphores : 225 km en minutes.", True),
    (1793, "Sémaphores sur toute la France (Chappe)", "Claude Chappe", "🔴 RÉSEAU", "Réseau national de télégraphe optique (~500 tours).", False),
    (1832, "Télégraphe électrique à aiguilles (Cooke & Wheatstone)", "Cooke & Wheatstone", "🔴 RÉSEAU", "Premier télégraphe électrique commercial (chemin de fer).", False),
    (1837, "Code Morse brevetté", "Samuel Morse", "🔴 RÉSEAU", "Alphabet points-traits pour le télégraphe.", False),
    (1844, "Ligne télégraphique Washington-Baltimore", "Samuel Morse", "🔴 RÉSEAU", "« What hath God wrought » : première liaison longue distance.", True),
    (1851, "Premier câble télégraphique sous-marin (Douvres-Calais)", "Submarine Telegraph Co", "🔴 RÉSEAU", "Le monde se câble sous la mer.", True),
    (1858, "Câble transatlantique (Cyrus Field)", "Cyrus Field", "🔴 RÉSEAU", "Première communication transatlantique (lente mais réelle).", True),
    (1866, "Câble transatlantique permanent (SS Great Eastern)", "William Thomson (Lord Kelvin)", "🔴 RÉSEAU", "L'Atlantique câblé définitivement.", False),
    (1876, "Téléphone (Bell)", "Alexander Graham Bell", "🔴 RÉSEAU", "Voix électrique à distance.", True),
    # signaux de fumée historiques
    (-1200, "Signaux de fumée (Chine antique)", "Garnisons chinoises", "🔴 RÉSEAU", "Transmission de messages par panaches de fumée sur la Grande Muraille.", False),
    (1812, "Signaux de fumée (UK, côte sud)", "Amiral Home Popham", "🔴 RÉSEAU", "Réseau de sémaphores à fumée britannique anti-Napoléon.", False),
    # --- INDUSTRIE 1700-1940 ---
    (1712, "Machine à vapeur atmosphérique (Newcomen)", "Thomas Newcomen", "🟡 HARDWARE", "Pompage des mines par la vapeur.", False),
    (1769, "Machine à vapeur à condenseur (Watt)", "James Watt", "🟡 HARDWARE", "Rendement x3 : moteur universel.", True),
    (1804, "Locomotive (Trevithick)", "Richard Trevithick", "🟡 HARDWARE", "Chemin de fer naissant.", False),
    (1814, "Première locomotive à vapeur régulière (Blucher)", "George Stephenson", "🟡 HARDWARE", "L'ère ferroviaire commence.", False),
    (1825, "Ligne Liverpool-Manchester (1re ligne publique)", "George Stephenson", "🟡 HARDWARE", "Premier service ferroviaire public de voyageurs.", True),
    (1830, "Première usine électrique (dynamo, Pixii)", "Hippolyte Pixii", "🟡 HARDWARE", "L'électricité devient industrielle.", False),
    (1839, "Daguerréotype", "Louis Daguerre", "🟡 HARDWARE", "Image fixe.", False),
    (1844, "Moteur électrique (Jacobi)", "Moritz von Jacobi", "🟡 HARDWARE", "Moteur électrique alimenté par piles.", False),
    (1866, "Dynamo (Siemens, Gramme)", "Werner von Siemens / Zénobe Gramme", "🟡 HARDWARE", "Auto-excitation : la dynamo produit son propre courant.", True),
    (1879, "Ampoule à filament de carbone (Edison/Swan)", "Edison / Swan", "🟡 HARDWARE", "Éclairage électrique durable.", True),
    (1882, "Première centrale électrique (Edison, Pearl Street)", "Edison Electric Light Co", "🟡 HARDWARE", "Réseau électrique urbain.", True),
    (1886, "Automobile (Benz)", "Karl Benz", "🟡 HARDWARE", "Moteur à combustion mobile.", False),
    (1888, "Moteur à courant alternatif (Tesla)", "Nikola Tesla", "🟡 HARDWARE", "Le courant alternatif gagne la guerre des courants.", True),
    (1895, "Cinématographe (Lumière)", "Frères Lumière", "✨ NOOSPHÈRE", "Projection publique : le cinéma naît.", True),
    (1903, "Vol des Wright", "Frères Wright", "🟣 ESPACE", "Vol motorisé contrôlé.", True),
    (1908, "Ford T (production de masse)", "Henry Ford", "🟡 HARDWARE", "La voiture pour tous.", True),
    (1913, "Chaîne de montage (Ford)", "Henry Ford", "🟡 HARDWARE", "Une voiture toutes les 93 minutes.", False),
    (1920, "Première émission radio régulière (KDKA)", "Westinghouse", "✨ NOOSPHÈRE", "Média de masse en temps réel.", False),
    (1927, "Télévision mécanique (Baird)", "John Logie Baird", "✨ NOOSPHÈRE", "Image télévisée.", False),
    (1936, "TV électronique régulière (BBC)", "BBC / EMI", "✨ NOOSPHÈRE", "Télévision électronique de masse.", False),
    (1939, "Moteur à réaction (Heinkel He 178)", "Hans von Ohain", "🟣 ESPACE", "Premier avion à réaction.", False),
    # --- ESPACE 1940-1970 ---
    (1944, "V2 (von Braun)", "Wernher von Braun", "🟣 ESPACE", "Premier missile balistique, 100 km d'altitude.", True),
    (1947, "Mur du son franchi (Yeager, X-1)", "Chuck Yeager", "🟣 ESPACE", "Mach 1.06.", False),
    (1957, "Spoutnik 1", "URSS", "🟣 ESPACE", "Premier satellite.", True),
    (1958, "NASA fondée", "USA", "🟣 ESPACE", "Course à l'espace institutionnalisée.", False),
    (1961, "Gagarine (1er homme dans l'espace)", "Youri Gagarine", "🟣 ESPACE", "Vostok 1.", True),
    (1965, "Première sortie extravéhiculaire (Leonov)", "Alexeï Leonov", "🟣 ESPACE", "L'homme marche dans l'espace.", False),
    (1969, "Apollo 11 (Lune)", "Armstrong / Aldrin / Collins", "🟣 ESPACE", "Premier pas sur la Lune.", True),
    # --- IA & COGNITION 1940-2010 ---
    (1943, "Neurone formel (McCulloch & Pitts)", "McCulloch & Pitts", "🔵 COGNITION", "Modèle mathématique du neurone.", False),
    (1948, "Cybernétique (Wiener)", "Norbert Wiener", "🔵 COGNITION", "Science du contrôle et de la communication.", False),
    (1950, "Test de Turing", "Alan Turing", "🔵 COGNITION", "« Les machines peuvent-elles penser ? »", True),
    (1956, "Conférence de Dartmouth", "McCarthy et al.", "🔵 COGNITION", "Naissance du terme « intelligence artificielle ».", True),
    (1958, "Perceptron (Rosenblatt)", "Frank Rosenblatt", "🔵 COGNITION", "Réseau de neurones apprenant.", False),
    (1966, "ELIZA", "Joseph Weizenbaum", "🔵 COGNITION", "Premier chatbot.", False),
    (1969, "ARPANET (4 nœuds)", "ARPA", "🔴 RÉSEAU", "Internet naît.", True),
    (1973, "Protocole TCP/IP (Kahn & Cerf)", "Vint Cerf / Bob Kahn", "🔴 RÉSEAU", "Internet tel qu'on le connaît.", True),
    (1983, "ARPANET passe à TCP/IP", "ARPA", "🔴 RÉSEAU", "Naissance d'Internet.", True),
    (1989, "World Wide Web (Berners-Lee, CERN)", "Tim Berners-Lee", "🔴 RÉSEAU", "Le Web public.", True),
    (1991, "Linux 0.01", "Linus Torvalds", "🔴 RÉSEAU", "Noyau open source universel.", False),
    (1995, "JavaScript (Netscape)", "Brendan Eich", "🔴 RÉSEAU", "Le Web devient applicatif.", False),
    (1997, "Deep Blue bat Kasparov", "IBM", "🔵 COGNITION", "Échecs : la machine bat le champion du monde.", True),
    (2005, "DARPA Grand Challenge (Stanley)", "Stanford", "🤖 ROBOTIQUE", "Première voiture autonome en désert (213 km).", True),
    (2011, "Watson gagne Jeopardy", "IBM", "🔵 COGNITION", "Compréhension du langage naturel.", False),
    # --- RÉSEAU/NOOSPHÈRE 1990-2020 ---
    (1994, "Amazon fondé", "Jeff Bezos", "🔴 RÉSEAU", "Commerce en ligne de masse.", False),
    (1998, "Google fondé", "Page & Brin", "🔴 RÉSEAU", "Le moteur de recherche qui indexe le Web.", True),
    (2004, "Facebook", "Mark Zuckerberg", "🔴 RÉSEAU", "Réseau social planétaire.", True),
    (2005, "YouTube", "Chad Hurley et al.", "✨ NOOSPHÈRE", "La vidéo de masse.", True),
    (2007, "iPhone", "Apple", "🔴 RÉSEAU", "Internet dans la poche.", True),
    (2010, "Instagram", "Systrom & Krieger", "✨ NOOSPHÈRE", "La photo mobile de masse.", False),
    (2010, "4G (déploiement)", "Opérateurs", "🔴 RÉSEAU", "Internet mobile haut débit.", False),
    (2016, "TikTok (Musical.ly rebaptisé)", "ByteDance", "✨ NOOSPHÈRE", "Vidéo courte algorithmique mondiale.", False),
    # --- VIVANT & SANTÉ 1800-2010 ---
    (1846, "Anesthésie générale (Morton, éther)", "William Morton", "💊 MÉDECINE", "Chirurgie sans douleur.", True),
    (1865, "Antisepsie (Lister, acide phénique)", "Joseph Lister", "💊 MÉDECINE", "La mortalité chirurgicale s'effondre.", True),
    (1882, "Bacille de la tuberculose (Koch)", "Robert Koch", "💊 MÉDECINE", "Postulats de Koch.", False),
    (1895, "Rayons X (Röntgen)", "Wilhelm Röntgen", "💊 MÉDECINE", "Voir à travers le corps.", True),
    (1901, "Groupes sanguins ABO (Landsteiner)", "Karl Landsteiner", "💊 MÉDECINE", "Transfusions sûres.", False),
    (1921, "Insuline isolée (Banting & Best)", "Banting & Best", "💊 MÉDECINE", "Le diabète devient traitable.", True),
    (1928, "Pénicilline (Fleming)", "Alexander Fleming", "💊 MÉDECINE", "Ère des antibiotiques.", True),
    (1944, "Dialyse (rein artificiel, Kolf)", "Willem Kolf", "💊 MÉDECINE", "Survie de l'insuffisance rénale.", False),
    (1953, "Double hélice ADN", "Watson & Crick", "🟢 BIOTECH", "Structure de l'hérédité.", True),
    (1955, "Vaccin polio (Salk)", "Jonas Salk", "💊 MÉDECINE", "Première vaccination de masse.", True),
    (1967, "1re transplantation cardiaque (Barnard)", "Christiaan Barnard", "💊 MÉDECINE", "Cœur humain transplanté.", True),
    (1977, "IRM", "Damadian / Lauterbur", "💊 MÉDECINE", "Imagerie du corps vivant.", False),
    (1978, "1er bébé FIV (Louise Brown)", "Edwards & Steptoe", "🟢 BIOTECH", "Fécondation in vitro.", True),
    (1983, "PCR (Mullis)", "Kary Mullis", "🟢 BIOTECH", "Amplification de l'ADN.", True),
    (1983, "VIH identifié", "Montagnier / Barré-Sinoussi", "💊 MÉDECINE", "Le virus du sida isolé.", True),
    (1996, "Dolly (clonage)", "Roslin Institute", "🟢 BIOTECH", "Mammifère cloné adulte.", False),
    (2003, "Génome humain complet", "Consortium public", "🟢 BIOTECH", "Lecture des 3 Md de lettres.", True),
    (2007, "iPS (Yamanaka)", "Shinya Yamanaka", "🟢 BIOTECH", "Cellules adultes reprogrammées en souches.", True),
    # --- POLITIQUE jalons ---
    (1945, "ONU", "51 États", "🏛️ POLITIQUE", "Ordre mondial d'après-guerre.", False),
    (1948, "DUDH", "ONU", "🏛️ POLITIQUE", "Droits de l'homme universels.", False),
    (1957, "Traité de Rome (CEE)", "6 États", "🏛️ POLITIQUE", "Europe économique.", False),
    (1989, "Chute du mur de Berlin", "Europe de l'Est", "🏛️ POLITIQUE", "Fin de la guerre froide.", True),
    (1992, "Sommet de Rio", "ONU", "🏛️ POLITIQUE", "Développement durable mondial.", False),
    (1997, "Protocole de Kyoto", "ONU", "🏛️ POLITIQUE", "Climat : objectifs chiffrés.", False),
    (2015, "Accord de Paris (COP21)", "195 États", "🏛️ POLITIQUE", "+1,5/+2 °C.", True),
    (2016, "Brexit voté", "Royaume-Uni", "🏛️ POLITIQUE", "Première sortie de l'UE.", False),
    (2024, "EU AI Act", "Union européenne", "🏛️ POLITIQUE", "Première loi majeure sur l'IA.", True),
    # --- ENTROPIE/CYBER intermédiaires ---
    (1971, "Premier virus informatique (Creeper)", "Bob Thomas (BBN)", "☠️ RISQUES CYBER", "« I'M THE CREEPER: CATCH ME IF YOU CAN ».", False),
    (1988, "Ver Morris", "Robert Tappan Morris", "☠️ RISQUES CYBER", "10% d'Internet infecté en 24h.", True),
    (1999, "Melissa", "David L. Smith", "☠️ RISQUES CYBER", "Macro-virus par e-mail.", False),
    (2000, "ILOVEYOU", "Onel de Guzman", "☠️ RISQUES CYBER", "45 M machines.", True),
    (2003, "SQL Slammer", "inconnu", "☠️ RISQUES CYBER", "75 000 victimes en 10 min.", False),
    (2010, "Stuxnet", "NSA / Israël", "☠️ RISQUES CYBER", "Cyberarme sur centrifugeuses.", True),
    (2017, "WannaCry", "Lazarus", "☠️ RISQUES CYBER", "Ransomware mondial.", True),
    (2017, "NotPetya", "Sandworm", "☠️ RISQUES CYBER", "10 Md$ de dégâts.", True),
    (2020, "SolarWinds", "Cozy Bear", "☠️ RISQUES CYBER", "Supply chain compromise.", True),
    (2021, "Log4Shell", "divers", "☠️ RISQUES CYBER", "Zero-day omniprésent.", True),
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
    for year, label, who, cat, desc, tip in E:
        if label.lower() in have:
            continue
        data.append({
            "id": eid(label, year, who), "year": year, "value": 1000, "label": label,
            "category": cat, "whoWhat": who, "description": desc, "url": "#",
            "timestamp": f"{int(year)}-06-01T00:00:00" if year < 2000 else datetime.now().isoformat(),
            "tipping": tip,
            "s_curve_phase": 1 if year < 1500 else (2 if year < 1900 else 3),
            "pharmakon_remedy_percent": 55, "pharmakon_poison_percent": 45,
            "convergences": "Jalon intermédiaire de la courbe",
            "grand_filter_analysis": "Étape de la chaîne technologique.",
            "final_note": "Le fil se resserre.",
        })
        have.add(label.lower())
        added += 1
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(f"+ {added} jalons, total {len(data)}")


if __name__ == "__main__":
    from datetime import datetime
    main()
