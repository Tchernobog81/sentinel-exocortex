#!/usr/bin/env python3
"""Cohérence des liens fiction<->réel, direction autoritaire réel -> fiction :
pour chaque événement réel avec predictedBy=[œuvres], on retrouve l'œuvre (label exact
puis sous-chaîne) et on pose realYear=real.year + realLabel=real.label côté fiction.
Corrige les realYear incohérents (ex: Gattaca -> 2027 au lieu de 23andMe 2007).
Verrouillé, idempotent."""
import fcntl
import json
from pathlib import Path

DATA = Path('/Users/tcherno/sentinel-exocortex/loom_data.json')
CAT_FICTION = '🔮 IMAGINAIRE'


def main():
    lock = open(str(DATA) + '.lock', 'a+')
    fcntl.flock(lock, fcntl.LOCK_EX)
    data = json.loads(DATA.read_text(encoding='utf-8'))
    by_label = {e.get('label', '').lower(): e for e in data}

    def find_fiction(title):
        t = title.lower()
        if t in by_label:
            return by_label[t]
        for k, e in by_label.items():
            if t in k and e.get('category') == CAT_FICTION:
                return e
        return None

    fixed = 0
    for real in data:
        for work in real.get('predictedBy') or []:
            f = find_fiction(work)
            if f is None:
                continue
            if f.get('realYear') != real.get('year') or f.get('realLabel') != real.get('label'):
                f['realYear'] = real.get('year')
                f['realLabel'] = real.get('label')
                fixed += 1
    tmp = DATA.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(DATA)
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    fic = [e for e in data if e.get('category') == CAT_FICTION]
    print(f'{fixed} liens corrigés | fictions: {len(fic)}, avec realLabel: {sum(1 for e in fic if e.get("realLabel"))}')
    g = find_fiction('Bienvenue à Gattaca')
    print('Gattaca ->', g.get('realLabel'), g.get('realYear'))


if __name__ == '__main__':
    main()
