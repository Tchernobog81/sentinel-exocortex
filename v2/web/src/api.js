// Hooks data — 100 % local. Deux modes :
//  - "server" : serveur Node local (127.0.0.1:8787) -> SSE /api/stream + /api/telemetry/stream
//  - "static" : GitHub Pages -> polling de loom_data.json / telemetry.json / rag.json (poussés par l'agent local)
import { useEffect, useRef, useState } from 'react';

const BASE = './'; // base relative : marche à la racine (serveur local) et sous /sentinel-exocortex/ (Pages)

let modePromise = null;
export function detectMode() {
  if (!modePromise) {
    modePromise = fetch(BASE + 'api/data', { cache: 'no-store' })
      .then(r => (r.ok ? 'server' : 'static'))
      .catch(() => 'static');
  }
  return modePromise;
}

// ---- mapping statique V1 -> enveloppe V2 (miroir de v2/server/lib.mjs) ----
const CAT_FILTER = {
  '🔵 COGNITION': 'IA', '⚪ SINGULARITÉ': 'IA', '☠️ RISQUES CYBER': 'Cyber', '☢️ ENTROPIE': 'Cyber',
  '🟢 BIOTECH': 'Vivant', '💊 MÉDECINE': 'Vivant', '🟣 ESPACE': 'Espace',
  '🟡 HARDWARE': 'Physique', '🤖 ROBOTIQUE': 'Physique', '🏛️ POLITIQUE': 'Politique',
  '⏰ HORLOGE': 'Horloge', '🔮 IMAGINAIRE': 'Fiction', '✨ NOOSPHÈRE': 'Réseau', '🔴 RÉSEAU': 'Réseau',
};
const GROUP_COLOR = {
  '⚙️ INDUSTRIE & ROBOTS': '#fbbf24', '🚀 ESPACE': '#8b5cf6', '🧠 IA & COGNITION': '#3b82f6',
  '🌍 NOOSPHÈRE & RÉSEAUX': '#0ea5e9', '🧬 VIVANT & SANTÉ': '#10b981', '🏛️ POLITIQUE': '#d946ef',
  '☢️ ENTROPIE & CYBER': '#f97316', '🎬 FICTION': '#f472b6', "⏰ HORLOGE DE L'APOCALYPSE": '#ef4444',
};
const GROUP_OF = {};
for (const [c, g] of Object.entries({
  '🟡 HARDWARE': '⚙️ INDUSTRIE & ROBOTS', '🤖 ROBOTIQUE': '⚙️ INDUSTRIE & ROBOTS', '🟣 ESPACE': '🚀 ESPACE',
  '🔵 COGNITION': '🧠 IA & COGNITION', '⚪ SINGULARITÉ': '🧠 IA & COGNITION',
  '✨ NOOSPHÈRE': '🌍 NOOSPHÈRE & RÉSEAUX', '🔴 RÉSEAU': '🌍 NOOSPHÈRE & RÉSEAUX',
  '🟢 BIOTECH': '🧬 VIVANT & SANTÉ', '💊 MÉDECINE': '🧬 VIVANT & SANTÉ', '🏛️ POLITIQUE': '🏛️ POLITIQUE',
  '☢️ ENTROPIE': '☢️ ENTROPIE & CYBER', '☠️ RISQUES CYBER': '☢️ ENTROPIE & CYBER',
  '🔮 IMAGINAIRE': '🎬 FICTION', '⏰ HORLOGE': "⏰ HORLOGE DE L'APOCALYPSE",
})) GROUP_OF[c] = g;

export function mapEnvelope(events) {
  const clocks = events.filter(e => e.category === '⏰ HORLOGE' && e.doomsday_minutes != null).sort((a, b) => (b.year || 0) - (a.year || 0));
  const apocalypse_clock_seconds = clocks.length ? Math.round(clocks[0].doomsday_minutes * 60) : 85;
  const nowY = new Date().getFullYear();
  const tip = events.filter(e => e.tipping && (e.year || 0) <= nowY + 1);
  const recency = events.length ? tip.reduce((a, e) => a + Math.min(1, Math.max(0, ((e.year || 0) + 2100) / 4200)), 0) / events.length : 0;
  const singularity_index = Math.round(Math.min(1, 0.35 + 0.65 * recency) * 1000) / 1000;
  return {
    apocalypse_clock_seconds,
    singularity_index,
    nela_status: { airgap: true, joules_per_action_score: 'Optimal', active_engine: 'Ollama' },
    generated_at: new Date().toISOString(),
    events: events.map(e => {
      const group = GROUP_OF[e.category] || e.category || 'AUTRE';
      return {
        id: e.id || `evt-${e.year}-${(e.label || '').slice(0, 12)}`,
        timestamp: e.timestamp || new Date((e.year || 1970), 0, 1).toISOString(),
        year: e.year, category: CAT_FILTER[e.category] || e.category || 'Autre', group,
        groupColor: GROUP_COLOR[group] || '#9ca3af', title: e.label, description: e.description || '',
        url: e.url || '', source: e.whoWhat || '',
        impact_score: Math.round(Math.min(1, (e.value || 1000) / 49000) * 100) / 100,
        value: e.value, is_kinetic_signal: !!(e.tipping || e.verified), tipping: !!e.tipping,
        verified: e.verified !== false, doomsday_minutes: e.doomsday_minutes ?? null,
        realYear: e.realYear ?? null, realLabel: e.realLabel ?? null,
        predictedBy: Array.isArray(e.predictedBy) ? e.predictedBy : [],
      };
    }),
  };
}

export function useSSE(url, onMessage, pollMs = 5000) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const [mode, setMode] = useState(null);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;
  const dataRef = useRef(null);

  useEffect(() => {
    let es = null, iv = null, cancelled = false;
    const isTelemetry = url.includes('telemetry');
    const apiPath = isTelemetry ? 'api/telemetry' : 'api/data';
    const staticFile = isTelemetry ? 'telemetry.json' : 'loom_data.json';

    (async () => {
      const m = await detectMode();
      if (cancelled) return;
      setMode(m);

      if (m === 'server') {
        try {
          es = new EventSource(BASE + url);
          es.onopen = () => setConnected(true);
          es.onmessage = ev => {
            try { const j = JSON.parse(ev.data); dataRef.current = j; setData(j); setConnected(true); onMessageRef.current?.(j); } catch {}
          };
          es.onerror = () => { if (!dataRef.current) setConnected(false); };
        } catch { setConnected(false); }
      }

      const tick = async () => {
        try {
          let r = await fetch(BASE + apiPath + '?cb=' + Date.now(), { cache: 'no-store' });
          if (!r.ok) r = await fetch(BASE + staticFile + '?cb=' + Date.now(), { cache: 'no-store' });
          if (!r.ok) { if (isTelemetry) setConnected(false); return; }
          let j = await r.json();
          if (!isTelemetry && Array.isArray(j)) j = mapEnvelope(j);
          dataRef.current = j;
          setData(j);
          setConnected(true);
          onMessageRef.current?.(j);
        } catch { if (!dataRef.current) setConnected(false); }
      };
      await tick();
      iv = setInterval(tick, m === 'server' ? pollMs : Math.max(pollMs, 8000));
    })();

    return () => { cancelled = true; es?.close(); clearInterval(iv); };
  }, [url, pollMs]);

  return { data, connected, mode };
}

// RAG : server -> /api/rag, static -> rag.json
export async function fetchRag() {
  const m = await detectMode();
  try {
    let r = await fetch(BASE + 'api/rag?cb=' + Date.now(), { cache: 'no-store' });
    if (!r.ok) r = await fetch(BASE + 'rag.json?cb=' + Date.now(), { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch {}
  return null;
}

// Purge VRAM : ne marche que si le serveur local tourne (127.0.0.1:8787)
export async function purgeVram() {
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), 20000);
    const r = await fetch('http://127.0.0.1:8787/api/purge', { method: 'POST', signal: ctl.signal });
    clearTimeout(t);
    if (r.ok) return await r.json();
    throw new Error('HTTP ' + r.status);
  } catch (e) {
    return { ok: false, error: 'serveur local non détecté sur 127.0.0.1:8787 — lance `node v2/server/index.js` pour activer la purge' };
  }
}
