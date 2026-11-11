# THE LOOM V2 — Dashboard de prospective & télémétrie (air-gap)

Refonte V2 du dashboard : backend **Node.js 20+ / Fastify** (SSE temps réel) + frontend **Vite + React 18 + TailwindCSS + Apache ECharts + lucide-react**, 100 % hors-ligne (aucun CDN, tout est bundlé en local par le build).

## Lancer le dashboard

```bash
# 1) installer + builder le frontend (une fois, ou après chaque modif du front)
cd v2/web && npm install && npm run build && cd ../..

# 2) démarrer le serveur (API + SSE + télémétrie), bind 127.0.0.1 uniquement (air-gap)
cd v2/server && npm install && node index.js
# → http://127.0.0.1:8787
```

Raccourci depuis la racine du repo :

```bash
npm --prefix v2/web install && npm --prefix v2/web run build && npm --prefix v2/server install && node v2/server/index.js
```

Variables d'environnement : `LOOM_PORT` (défaut 8787), `LOOM_HOST` (défaut 127.0.0.1), `LOOM_DATA` (défaut `../loom_data.json`), `OLLAMA_URL` (défaut http://127.0.0.1:11434), `EXO_URL` (défaut http://127.0.0.1:5000), `RAG_DIR` (défaut `.vibe/knowledge`).

## Architecture

```
v2/
├── server/            # Fastify — sert v2/web/dist + API
│   └── index.js       #   GET /api/data (enveloppe V2), /api/events (legacy),
│                      #   GET /api/stream (SSE, push à chaque changement de loom_data.json),
│                      #   GET /api/telemetry + /api/telemetry/stream (SSE 2 s, systeminformation),
│                      #   GET /api/rag (docs vectorisés, quarantaine), POST /api/purge (VRAM)
└── web/               # Vite + React + Tailwind + ECharts + lucide-react
    └── src/
        ├── App.jsx            # 4 onglets + état partagé + hooks SSE
        ├── api.js             # useSSE (EventSource + fallback polling)
        └── tabs/
            ├── LoomCore.jsx       # 🏛️ LOOM CORE : horloge apocalypse lissée, filtres, J-curve ECharts, flux SSE
            ├── NelaSubstrat.jsx   # ⚡ NELA SUBSTRAT : jauges RAM/VRAM/temp, J/action, air-gap, démons Ollama/Exo
            ├── SteriNet.jsx       # 🛡️ STERI-NET & RAG : base RAG, quarantaine, Purge VRAM
            └── FiltreMemetique.jsx# 🧠 FILTRE MÉMÉTIQUE : ratio bruit/signal, lissage horloge
```

## Modèle de données

`loom_data.json` (racine du repo, format V1 en tableau plat) est servi via `/api/data` dans l'enveloppe V2 :

```json
{
  "apocalypse_clock_seconds": 85,
  "singularity_index": 0.573,
  "nela_status": { "airgap": true, "joules_per_action_score": "Optimal", "active_engine": "Ollama" },
  "events": [
    { "id": "...", "timestamp": "...", "year": 2026, "category": "IA", "group": "🧠 IA & COGNITION",
      "title": "...", "impact_score": 0.95, "is_kinetic_signal": true, "value": 45000, ... }
  ]
}
```

## Tests

`node /tmp/pwtest/v2test.js http://127.0.0.1:8787/` → V2 OK (13 checks : 4 onglets, ECharts, SSE live, télémétrie, purge, lissage propagé, 0 requête externe, 0 pageerror).
