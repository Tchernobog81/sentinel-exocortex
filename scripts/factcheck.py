#!/usr/bin/env python3
"""Fact-check des données existantes :
- supprime les événements FUTURS sans description (claims non sourcés, ex: 'Starship Mars 2026') ;
- les événements futurs sourcés restent (seront rendus en pointillés 'prévisions').
Verrouillé, idempotent."""
import fcntl
import json
from datetime import date
from pathlib import Path

DATA = Path('/Users/tcherno/sentinel-exocortex/loom_data.json')
now = date.today().year + date.today().month / 12

lock = open(str(DATA) + '.lock', 'a+')
fcntl.flock(lock, fcntl.LOCK_EX)
data = json.loads(DATA.read_text(encoding='utf-8'))
before = len(data)
kept = []
removed = []
for e in data:
    y = e.get('year') or 0
    desc = (e.get('description') or '').strip()
    if y > now + 0.05 and len(desc) < 30:
        removed.append(e['label'])
        continue
    kept.append(e)
tmp = DATA.with_suffix('.tmp')
tmp.write_text(json.dumps(kept, indent=2, ensure_ascii=False), encoding='utf-8')
tmp.replace(DATA)
fcntl.flock(lock, fcntl.LOCK_UN)
lock.close()
print(f'{before} -> {len(kept)} events; claims futurs non sourcés supprimés: {removed}')
