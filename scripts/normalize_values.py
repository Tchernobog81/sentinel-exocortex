#!/usr/bin/env python3
"""Normalise les valeurs Y par groupe (8 courbes) en S-curve montante réaliste :
value croît avec le temps dans chaque courbe (logistique), réparti dans [1000, 49000].
Corrige l'aplatissement (seeds à ~100-500 vs historique à 50000+).
Courbe ⏰ HORLOGE : lissage anti-zigzag renforcé (moyenne mobile centrée répétée
jusqu'à maxDelta <= 6000 entre points consécutifs triés par année), idempotent.
Verrouillé, idempotent."""
import fcntl
import json
import math
import re
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
    ('⏰ HORLOGE', '⏰ HORLOGE DE L\'APOCALYPSE'),
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


# --- Lissage anti-zigzag de la courbe ⏰ HORLOGE DE L'APOCALYPSE ---
# Cible : maxDelta entre points consécutifs (triés par année) <= HORLOGE_MAX_DELTA.
HORLOGE_MAX_DELTA = 6000.0
HORLOGE_MAX_PASSES = 200  # borne de sécurité (le lissage converge bien avant)


def parse_doomsday_minutes_from_label(label):
    """Fallback sémantique quand doomsday_minutes est absent du JSON.
    Ex: '⏰ 2017 — 2 min 30 avant minuit' -> 2.5 ; '⏰ 2020 — 100 s avant minuit' -> 100/60."""
    label = label or ""
    m = re.search(r'(\d+(?:[.,]\d+)?)\s*min\s*(?:(\d+)\s*(?:s\b)?)?\s*avant minuit', label)
    if m:
        mins = float(m.group(1).replace(',', '.'))
        if m.group(2):
            mins += int(m.group(2)) / 60.0
        return mins
    m = re.search(r'(\d+)\s*s\s*avant minuit', label)
    if m:
        return int(m.group(1)) / 60.0
    return None


def smooth_series(series, target=HORLOGE_MAX_DELTA, max_passes=HORLOGE_MAX_PASSES):
    """Moyenne mobile centrée 0.25/0.5/0.25 (bords par clamping) répétée jusqu'à ce que
    maxDelta <= target. Fonction déterministe des seules valeurs brutes -> idempotente :
    relancer le script sur loom_data.json ne change plus rien."""
    a = [float(x) for x in series]
    for _ in range(max_passes):
        deltas = [abs(a[i + 1] - a[i]) for i in range(len(a) - 1)]
        if not deltas or max(deltas) <= target:
            break
        b = list(a)
        for i in range(len(a)):
            lo = a[i - 1] if i > 0 else a[i]
            hi = a[i + 1] if i < len(a) - 1 else a[i]
            b[i] = 0.25 * lo + 0.5 * a[i] + 0.25 * hi
        a = b
    return a


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
        vals = {}
        for e in evs:
            # Horloge de l'Apocalypse : valeur = DANGER (montante quand l'aiguille approche minuit)
            if e.get("category") == "⏰ HORLOGE":
                dm = e.get("doomsday_minutes")
                if dm is None:
                    dm = parse_doomsday_minutes_from_label(e.get("label", ""))
                if dm is not None:
                    frac = 1.0 - min(float(dm), 17.0) / 17.0
                    v = int(1000 + 48000 * frac)
                    vals[id(e)] = 1000.0 + 48000.0 * frac  # brut flottant pour le lissage
                else:
                    v = int(1000 + 48000 * exp_frac(e.get("year") or 0))
                    vals[id(e)] = float(v)
            else:
                v = int(1000 + 48000 * exp_frac(e.get("year") or 0))
                vals[id(e)] = v
            if e.get("value") != v:
                e["value"] = v
                changed += 1
        # Lissage anti-zigzag renforcé ET idempotent pour la courbe horloge :
        # moyenne mobile centrée 0.25/0.5/0.25 répétée jusqu'à maxDelta <= HORLOGE_MAX_DELTA.
        # Le lissage ne dépend que des valeurs brutes (doomsday_minutes / label), jamais de
        # e["value"] : relancer le script produit exactement les mêmes valeurs.
        if g == "⏰ HORLOGE DE L'APOCALYPSE":
            ordered = sorted(evs, key=lambda e: e.get("year") or 0)
            raw = [vals[id(e)] for e in ordered]
            smoothed = smooth_series(raw)
            for e, v in zip(ordered, smoothed):
                nv = int(round(v))
                if e.get("value") != nv:
                    e["value"] = nv
                    changed += 1
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(f"{changed} valeurs normalisées en S-curve sur {len(groups)} groupes")


if __name__ == "__main__":
    main()
