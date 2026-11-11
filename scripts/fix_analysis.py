#!/usr/bin/env python3
"""Remplace les champs d'analyse placeholder ('simulée', 'N/A', vide) par une matrice
curatoriale par catégorie, variée par hash du label (déterministe, toujours renseigné)."""
import fcntl
import json
import zlib
from pathlib import Path

DATA = Path('/Users/tcherno/sentinel-exocortex/loom_data.json')

MATRIX = {
    "COGNITION": [
        ("IA + compute + régulation +军事化", "Alignement et course à la puissance de calcul : le vrai filtre est politique.",
         "L'IA avance plus vite que nos garde-fous."),
        ("Modèles + données + infrastructre énergétique", "La contrainte devient l'énergie et les puces, pas les idées.",
         "On entraîne des modèles sur nos propres débris numériques."),
        ("Agents autonomes + outils + sécurité", "L'autonomie sans supervision est un filtre en soi.",
         "Un agent qui agit tout seul, c'est déjà de la science-fiction opérationnelle."),
    ],
    "HARDWARE": [
        ("Loi de Moore + matériaux + énergie", "La miniaturisation bute sur la physique et les terres rares.",
         "Encore un nanomètre de gagné. Jusqu'au mur."),
        ("Silicium + photonique + neuromorphique", "Le hardware décide de la vitesse de toute la pile technologique.",
         "La puce est le nouveau pétrole."),
    ],
    "RÉSEAU": [
        ("Internet + décentralisation + chiffrement", "La connectivité globale redessine le pouvoir et la surveillance.",
         "Tout le monde est connecté, personne n'est d'accord."),
        ("5G/6G + satellites + IoT", "La couverture totale rend l'offline presque illégal.",
         "Même la Lune aura bientôt le wifi."),
    ],
    "ESPACE": [
        ("Propulsion + robotique + ressources in-situ", "L'espace devient une économie, pas seulement un rêve.",
         "Mars ou crève — version poésie."),
        ("Lanceurs réutilisables + stations + minage", "Le coût à l'orbite s'effondre, la ruée commence.",
         "On privatise l'orbite basse."),
    ],
    "BIOTECH": [
        ("Génétique + IA + nanotechnologies", "Le vivant devient programmable : médecine et risques existentiels montent ensemble.",
         "On édite le vivant comme du code."),
    ],
    "MÉDECINE": [
        ("Génomique + IA diagnostique + robots chirurgicaux", "La médecine devient prédictive et personnalisée.",
         "Le médecin de demain est un algorithme avec un stéthoscope."),
        ("Antiviraux + vaccins à ARNm + longévité", "L'espérance de vie grimpe, les inégalités de santé aussi.",
         "Vivre plus longtemps, c'est bien. Ensemble, c'est mieux."),
    ],
    "POLITIQUE": [
        ("Législation + souveraineté numérique + société civile", "Les États rattrapent la tech par la régulation.",
         "La loi arrive toujours en retard, mais elle arrive."),
    ],
    "ENTROPIE": [
        ("Complexité systémique + interdépendance + cascades", "Plus c'est connecté, plus ça casse en cascade.",
         "Tout est relié, donc tout peut tomber."),
    ],
    "HORLOGE": [
        ("Nucléaire + climat + IA + bio + désinformation", "Toutes les menaces convergent vers minuit.",
         "L'aiguille ne ment pas : elle avance quand les dirigeants n'agissent pas."),
    ],
    "RISQUES CYBER": [
        ("Attaquants + surface d'attaque + IA offensive", "La cyberguerre est permanente et industrialisée.",
         "Le prochain conflit commencera par un écran noir."),
    ],
    "ROBOTIQUE": [
        ("Actionneurs + perception + autonomie énergétique", "Les robots sortent des usines pour le monde réel.",
         "Ils font le café. Bientôt ils feront nos choix."),
    ],
    "IMAGINAIRE": [
        ("Fiction + anticipation + culture populaire", "La fiction teste les futurs avant qu'ils n'arrivent.",
         "La SF avait prévenu. Encore une fois."),
    ],
    "NOOSPHÈRE": [
        ("Médias + mèmes + conscience collective", "L'opinion mondiale se forme en temps réel, bien ou mal.",
         "L'humanité pense à voix haute, 24/7."),
    ],
    "SINGULARITÉ": [
        ("IA forte + nanotech + bio-ingénierie + compute", "La convergence accélère vers un point de non-retour.",
         "La courbe monte. Accrochez-vous."),
    ],
}


def cat_key(cat):
    for k in MATRIX:
        if k in (cat or ""):
            return k
    return "RÉSEAU"


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    fixed = 0
    for e in data:
        variants = MATRIX[cat_key(e.get("category"))]
        seed = zlib.crc32((e.get("label") or "").encode("utf-8"))
        conv, gf, note = variants[seed % len(variants)]
        for k, v in (("convergences", conv), ("grand_filter_analysis", gf), ("final_note", note)):
            cur = (e.get(k) or "").strip().lower()
            if len(cur) < 10 or "simul" in cur or "n/a" in cur:
                e[k] = v
                fixed += 1
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    left = sum(1 for e in data for k in ("convergences", "grand_filter_analysis", "final_note")
               if len((e.get(k) or "").strip()) < 10 or "simul" in (e.get(k) or "").lower() or "n/a" in (e.get(k) or "").lower())
    print(f"{fixed} champs réparés, placeholder restants: {left}")


if __name__ == "__main__":
    main()
