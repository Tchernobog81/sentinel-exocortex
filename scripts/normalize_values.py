#!/usr/bin/env python3
"""Normalise les valeurs Y par groupe (8 courbes) en S-curve montante réaliste :
value croît avec le temps dans chaque courbe (logistique), réparti dans [1000, 49000].
Corrige l'aplatissement (seeds à ~100-500 vs historique à 50000+).
Verrouillé, idempotent."""
import fcntl
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "loom_data.json"

GROUP_OF = {}
GROUPS = [
    ('🟡 HARDWARE', '⚙️ INDUSTRIE & ROBOTS'), ('🤖 ROBOTIQUE', '⚙️ INDUSTRIE & ROBOTS'),
    ('🟣 ESPACE', '🚀 ESPACE'),
    ('🔵 COGNITION', '🧠 IA & COGNITION'), ('⚪ SINGULARITÉ', '🧠 IA & COGNITION'),
    ('✨ NOOSPHÈRE', '🌍 NOOSPHÈRE & RÉSEAUX'), ('🔴 RÉSEAU', '🌍 NOOSPHÈRE & RÉSEAUX'),
    ('🟢 BIOTECH', '🧬 VIVANT & SANTÉ'), ('💊 MÉDECINE', '🧬 VIVANT & SANTÉ'),
    ('🏛️ POLITIQUE', '🏛️ POLITIQUE'),
    ('☢️ ENTROPIE', '☢️ ENTROPIE & CYBER'), ('☠️ RISQUES CYBER', '☢️ ENTROPIE & CYBER'),
    ('🔮 IMAGINAIRE', '🎬 FICTION'),
]
for cat, grp in GROUPS:
    GROUP_OF[cat] = grp


def s_curve(t):
    """Logistique centrée à 0.55 -> montée lente, puis franche, puis plateau (S réaliste)."""
    return 1.0 / (1.0 + math.exp(-8.0 * (t - 0.55)))


# Exponentielle "retours accélérés" (Kurzweil) : plate dans le passé, franche vers aujourd'hui.
# frac(year) = exp(a*(year - ymax)) avec a choisi pour ~2% en 1900 -> la montée verticale
# n'apparaît qu'à la toute fin, pas en 1940.
YMAX = 2105.0
A = math.log(50.0) / (YMAX - 1900.0)  # ~0.019


def exp_frac(year):
    return math.exp(A * (year - YMAX))


def main():
    lock = open(str(DATA) + ".lock", "a+")
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    groups = {}
    for e in data:
        g = GROUP_OF.get(e.get("category"), e.get("category", "AUTRE"))
        groups.setdefault(g, []).append(e)
    changed = 0
    for g, evs in groups.items():
        for e in evs:
            v = int(1000 + 48000 * exp_frac(e.get("year") or 0))
            if e.get("value") != v:
                e["value"] = v
                changed += 1
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(f"{changed} valeurs normalisées en S-curve sur {len(groups)} groupes")


if __name__ == "__main__":
    main()
