// Lib commune V2 : enveloppe données + télémétrie + RAG (utilisée par index.js et export-static.mjs)
import fs from 'node:fs';
import path from 'node:path';
import { exec } from 'node:child_process';
import si from 'systeminformation';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(__dirname, '..', '..');
export const DATA_FILE = process.env.LOOM_DATA || path.join(ROOT, 'loom_data.json');
export const RAG_DIR = process.env.RAG_DIR || path.join(ROOT, '.vibe', 'knowledge');
export const QUARANTINE_LOG = path.join(__dirname, '..', 'data', 'quarantine.log');
export const OLLAMA_URL = process.env.OLLAMA_URL || 'http://127.0.0.1:11434';
export const EXO_URL = process.env.EXO_URL || 'http://127.0.0.1:5000';

export const CAT_FILTER = {
  '🔵 COGNITION': 'IA', '⚪ SINGULARITÉ': 'IA',
  '☠️ RISQUES CYBER': 'Cyber', '☢️ ENTROPIE': 'Cyber',
  '🟢 BIOTECH': 'Vivant', '💊 MÉDECINE': 'Vivant',
  '🟣 ESPACE': 'Espace',
  '🟡 HARDWARE': 'Physique', '🤖 ROBOTIQUE': 'Physique',
  '🏛️ POLITIQUE': 'Politique',
  '⏰ HORLOGE': 'Horloge',
  '🔮 IMAGINAIRE': 'Fiction',
  '✨ NOOSPHÈRE': 'Réseau', '🔴 RÉSEAU': 'Réseau',
};
export const GROUP_COLOR = {
  '⚙️ INDUSTRIE & ROBOTS': '#fbbf24', '🚀 ESPACE': '#8b5cf6', '🧠 IA & COGNITION': '#3b82f6',
  '🌍 NOOSPHÈRE & RÉSEAUX': '#0ea5e9', '🧬 VIVANT & SANTÉ': '#10b981', '🏛️ POLITIQUE': '#d946ef',
  '☢️ ENTROPIE & CYBER': '#f97316', '🎬 FICTION': '#f472b6', "⏰ HORLOGE DE L'APOCALYPSE": '#ef4444',
};
export const GROUP_OF = {};
{
  const G = [
    ['🟡 HARDWARE', '⚙️ INDUSTRIE & ROBOTS'], ['🤖 ROBOTIQUE', '⚙️ INDUSTRIE & ROBOTS'],
    ['🟣 ESPACE', '🚀 ESPACE'],
    ['🔵 COGNITION', '🧠 IA & COGNITION'], ['⚪ SINGULARITÉ', '🧠 IA & COGNITION'],
    ['✨ NOOSPHÈRE', '🌍 NOOSPHÈRE & RÉSEAUX'], ['🔴 RÉSEAU', '🌍 NOOSPHÈRE & RÉSEAUX'],
    ['🟢 BIOTECH', '🧬 VIVANT & SANTÉ'], ['💊 MÉDECINE', '🧬 VIVANT & SANTÉ'],
    ['🏛️ POLITIQUE', '🏛️ POLITIQUE'],
    ['☢️ ENTROPIE', '☢️ ENTROPIE & CYBER'], ['☠️ RISQUES CYBER', '☢️ ENTROPIE & CYBER'],
    ['🔮 IMAGINAIRE', '🎬 FICTION'],
    ['⏰ HORLOGE', "⏰ HORLOGE DE L'APOCALYPSE"],
  ];
  for (const [c, g] of G) GROUP_OF[c] = g;
}

export function readEvents() {
  try { return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')); } catch { return []; }
}

export function buildEnvelope() {
  const events = readEvents();
  const clocks = events.filter(e => e.category === '⏰ HORLOGE' && e.doomsday_minutes != null)
                       .sort((a, b) => (b.year || 0) - (a.year || 0));
  const apocalypse_clock_seconds = clocks.length ? Math.round(clocks[0].doomsday_minutes * 60) : 85;
  const tip = events.filter(e => e.tipping && (e.year || 0) <= new Date().getFullYear() + 1);
  const recency = events.length ? tip.reduce((a, e) => a + Math.min(1, Math.max(0, ((e.year || 0) + 2100) / 4200)), 0) / events.length : 0;
  const singularity_index = Math.round(Math.min(1, 0.35 + 0.65 * recency) * 1000) / 1000;
  const mapped = events.map(e => {
    const group = GROUP_OF[e.category] || e.category || 'AUTRE';
    return {
      id: e.id || `evt-${e.year}-${(e.label || '').slice(0, 12)}`,
      timestamp: e.timestamp || new Date((e.year || 1970), 0, 1).toISOString(),
      year: e.year,
      category: (CAT_FILTER[e.category] || e.category || 'Autre'),
      group,
      groupColor: GROUP_COLOR[group] || '#9ca3af',
      title: e.label,
      description: e.description || '',
      url: e.url || '',
      source: e.whoWhat || '',
      impact_score: Math.round(Math.min(1, (e.value || 1000) / 49000) * 100) / 100,
      value: e.value,
      is_kinetic_signal: !!(e.tipping || e.verified),
      tipping: !!e.tipping,
      verified: e.verified !== false,
      doomsday_minutes: e.doomsday_minutes ?? null,
      realYear: e.realYear ?? null, realLabel: e.realLabel ?? null,
      predictedBy: Array.isArray(e.predictedBy) ? e.predictedBy : [],
      remedy: e.pharmakon_remedy_percent ?? e.remedy_percent ?? 50, poison: e.pharmakon_poison_percent ?? e.poison_percent ?? 50,
      sCurve: e.s_curve_phase ?? 3, convergences: e.convergences || '', grandFilter: e.grand_filter_analysis || '',
    };
  });
  return { apocalypse_clock_seconds, singularity_index, nela_status: { airgap: true, joules_per_action_score: 'Optimal', active_engine: 'Ollama' }, generated_at: new Date().toISOString(), events: mapped };
}

async function probe(url, ms = 1200) {
  try {
    const ctl = new AbortController();
    const t = setTimeout(() => ctl.abort(), ms);
    const r = await fetch(url, { signal: ctl.signal });
    clearTimeout(t);
    return r.ok ? await r.json().catch(() => ({})) : null;
  } catch { return null; }
}

export async function telemetry() {
  const [mem, cpu, cpuTemp, graphics, fsSize, netConnsRaw, netStats] = await Promise.all([
    si.mem(), si.currentLoad(), si.cpuTemperature(), si.graphics(), si.fsSize(), si.networkConnections(), si.networkStats(),
  ]);
  let netConns = netConnsRaw || [];
  if (netConns.length === 0) {
    const lsof = await new Promise(res => exec('lsof -iTCP -sTCP:LISTEN -P -n 2>/dev/null', { maxBuffer: 1 << 20 }, (e, out) => res(out || '')));
    netConns = (lsof || '').split('\n').slice(1).filter(Boolean).map(l => {
      const p = l.trim().split(/\s+/);
      const m = (p[8] || '').match(/^(.+):(\d+)$/);
      return { state: 'LISTEN', localAddress: m ? m[1] : '', localPort: m ? +m[2] : 0, protocol: 'TCP', pid: +p[1] };
    }).filter(c => c.localPort);
  }
  const listeners = netConns.filter(c => c.state === 'LISTEN');
  const external = listeners.filter(c => {
    const l = (c.localAddress || '').toLowerCase();
    if (l === '127.0.0.1' || l === '::1' || l === 'localhost' || l === '' || l === '::ffff:127.0.0.1') return false;
    if (l === '*' || l === '0.0.0.0' || l === '::') return false;
    return true;
  });
  const ollamaTags = await probe(`${OLLAMA_URL}/api/tags`);
  const ollamaUp = !!ollamaTags;
  const ollamaModels = (ollamaTags?.models || []).map(m => ({ name: m.name, size: m.size }));
  const exo = await probe(`${EXO_URL}/v1/models`, 800);
  const loadedBytes = ollamaModels.reduce((a, m) => a + (m.size || 0), 0);
  const cpuLoad = cpu.currentLoad || 0;
  const joulesPerAction = loadedBytes ? Math.round((cpuLoad / 100) * (loadedBytes / 1e9) * 12 * 10) / 10 : 0;
  const score = joulesPerAction === 0 ? 'Optimal' : joulesPerAction < 5 ? 'Élevé' : 'Critique';
  const gpu = (graphics?.controllers || [])[0] || {};
  // Fallback VRAM (VM / Apple Silicon UMA) : system_profiler SPDisplaysDataType
  if (!gpu.vram) {
    const sp = await new Promise(res => exec('system_profiler SPDisplaysDataType 2>/dev/null', { maxBuffer: 1 << 20 }, (e, out) => res(out || '')));
    const mv = (sp || '').match(/VRAM[^:]*:\s*([\d.]+)\s*(GB|Go|MB|Mo)/i);
    const mdyn = (sp || '').match(/VRAM \(Dynamic, Max\):\s*([\d.]+)\s*(GB|Go)/i);
    const chip = (sp || '').match(/Chipset Model:\s*(.+)/i);
    if (mv) gpu.vram = Math.round(parseFloat(mv[1]) * (mv[2].toUpperCase().startsWith('G') ? 1024 : 1));
    else if (mdyn) gpu.vram = Math.round(parseFloat(mdyn[1]) * 1024);
    if (chip) gpu.name = (gpu.name || '') + ' ' + chip[1].trim();
    // Apple Silicon (M*) : pas de VRAM dédiée -> mémoire unifiée = RAM
    if (!gpu.vram && /apple m/i.test(gpu.name || '')) {
      gpu.vram = Math.round(mem.total / 1e6);
      gpu.vramUsed = Math.round((mem.used || mem.active || 0) / 1e6);
      gpu.uma = true;
    }
    if (gpu.vram && gpu.vramUsed == null) gpu.uma = true; // mémoire unifiée: used non mesurable -> UMA
  }
  // Température CPU : si pas de capteur SMC (VM), rester null -> le front affiche "n/a"
  const cpuTempVal = (cpuTemp && cpuTemp.max != null) ? cpuTemp.max : null;
  return {
    ts: new Date().toISOString(),
    airgap: external.length === 0,
    external_listeners: external.map(c => `${c.localAddress}:${c.localPort} (${c.protocol})`),
    open_ports: listeners.map(c => ({ port: c.localPort, addr: c.localAddress, proto: c.protocol, pid: c.pid })),
    mem: { used: mem.active, total: mem.total, pct: Math.round((mem.active / mem.total) * 100) },
    cpu: { load: Math.round(cpuLoad * 10) / 10, temp: cpuTempVal, cores: cpu.cpus?.length || null },
    gpu: { name: gpu.name || null, vram: gpu.vram || null, vramUsed: gpu.vramUsed ?? gpu.memoryUsed ?? null, uma: !!gpu.uma, temp: gpu.temperatureGpu || null },
    disk: (fsSize || []).map(d => ({ fs: d.fs, size: d.size, used: d.used, pct: Math.round(d.use) })),
    net: (netStats || [])[0] ? { rx: netStats[0].rx_bytes, tx: netStats[0].tx_bytes } : null,
    daemons: { ollama: { up: ollamaUp, url: OLLAMA_URL, models: ollamaModels }, exo: { up: !!exo, url: EXO_URL } },
    joules_per_action: joulesPerAction,
    joules_per_action_score: score,
    active_engine: ollamaUp ? 'Ollama' : (exo ? 'Exo' : 'Aucun'),
  };
}

export function ragStatus() {
  let docs = 0, bytes = 0, files = [];
  const walk = (dir) => {
    if (!fs.existsSync(dir)) return;
    for (const f of fs.readdirSync(dir)) {
      const p = path.join(dir, f);
      const st = fs.statSync(p);
      if (st.isDirectory()) walk(p);
      else if (/\.(db|sqlite|sqlite3|index|bin|jsonl|parquet|md|txt)$/i.test(f)) { docs++; bytes += st.size; files.push({ name: f, size: st.size, mtime: st.mtime }); }
    }
  };
  walk(RAG_DIR);
  let quarantine = [];
  if (fs.existsSync(QUARANTINE_LOG)) {
    quarantine = fs.readFileSync(QUARANTINE_LOG, 'utf8').split('\n').filter(Boolean).slice(-200).map(l => { try { return JSON.parse(l); } catch { return { raw: l }; } });
  }
  return { dir: RAG_DIR, documents: docs, bytes, db_mb: Math.round(bytes / 1e6 * 10) / 10, files: files.slice(-50), quarantine };
}

export async function purgeVram() {
  const actions = [];
  const tags = await probe(`${OLLAMA_URL}/api/tags`);
  for (const m of (tags?.models || [])) {
    try {
      await fetch(`${OLLAMA_URL}/api/generate`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ model: m.name, keep_alive: 0 }) });
      actions.push(`ollama unload ${m.name}`);
    } catch {}
  }
  await new Promise(res => exec('purge', () => res()));
  actions.push('macOS purge (mémoire inactive libérée)');
  return { ok: true, actions, at: new Date().toISOString() };
}
