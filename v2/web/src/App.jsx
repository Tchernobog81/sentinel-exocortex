import { useEffect, useMemo, useState } from 'react';
import { Landmark, Zap, ShieldCheck, BrainCircuit, Radio } from 'lucide-react';
import { useSSE } from './api.js';
import LoomCore, { LOOM_VERSION } from './tabs/LoomCore.jsx';
import NelaSubstrat from './tabs/NelaSubstrat.jsx';
import SteriNet from './tabs/SteriNet.jsx';
import FiltreMemetique from './tabs/FiltreMemetique.jsx';

const TABS = [
  { id: 'core', label: 'LOOM CORE', icon: Landmark },
  { id: 'nela', label: 'NELA SUBSTRAT', icon: Zap },
  { id: 'steri', label: 'STERI-NET & RAG', icon: ShieldCheck },
  { id: 'filtre', label: 'FILTRE MÉMÉTIQUE', icon: BrainCircuit },
];

export default function App() {
  const [tab, setTab] = useState('core');
  // Raccourcis clavier : Touch 1-4 pour naviguer entre les onglets (hors champ de saisie)
  useEffect(() => {
    const onKey = (ev) => {
      if (ev.target && /input|textarea|select/i.test(ev.target.tagName)) return;
      const map = { '1': 'core', '2': 'nela', '3': 'steri', '4': 'filtre' };
      if (map[ev.key]) setTab(map[ev.key]);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);
  const [filters, setFilters] = useState({});            // {cat: bool} — filtres catégories onglet 1
  const [memetic, setMemetic] = useState({ noiseRatio: 30, smoothWindow: 3, clockAlpha: 0.22 }); // onglet 4 -> partagé
  const { data, connected, mode } = useSSE('/api/stream', null, 5000);
  const { data: tel, connected: telOn } = useSSE('/api/telemetry/stream', null, 4000);

  const envelope = data || { apocalypse_clock_seconds: 85, singularity_index: 0.915, events: [] };
  const events = envelope.events || [];

  const filtered = useMemo(() => {
    const off = Object.keys(filters).filter(k => filters[k] === false);
    let evs = off.length ? events.filter(e => !off.includes(e.category)) : events;
    if (memetic.noiseRatio < 100) {
      // ratio bruit marketing / signal cinétique : on garde les signaux cinétiques + une fraction du reste
      const kinetic = evs.filter(e => e.is_kinetic_signal);
      const rest = evs.filter(e => !e.is_kinetic_signal);
      const keep = Math.round(rest.length * (100 - memetic.noiseRatio) / 100);
      evs = [...kinetic, ...rest.slice(0, keep)];
    }
    return evs;
  }, [events, filters, memetic.noiseRatio]);

  return (
    <div className="h-full flex flex-col p-3 gap-3">
      {/* barre d'onglets */}
      <header className="panel flex items-center gap-2 px-3 py-2 shrink-0">
        <div className="amber-text font-black tracking-widest text-sm mr-2">THE LOOM <span className="text-neon-cyan">V{LOOM_VERSION}</span></div>
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} className={`tab-btn flex items-center gap-2 ${tab === t.id ? 'active' : ''}`} onClick={() => setTab(t.id)}>
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-3 text-[10px]">
          <span className={`flex items-center gap-1 ${connected ? 'text-neon-green' : 'text-neon-red'}`}>
            <Radio size={12} className={connected ? 'animate-pulse' : ''} /> {mode === 'static' ? 'POLL' : 'SSE'} {connected ? 'LIVE' : 'OFF'}
          </span>
          <span className={telOn ? 'text-neon-cyan' : 'text-zinc-500'}>TEL {telOn ? 'LIVE' : 'OFF'}</span>
          {envelope.fallback && <span className="red-text">· DONNÉES D'URGENCE</span>}
          <span className="text-zinc-500">AIR-GAP {tel?.airgap === false ? <b className="red-text">OUVERT</b> : <b className="text-neon-green">ON</b>}</span>
        </div>
      </header>

      {/* contenu */}
      <main className="flex-1 min-h-0">
        {tab === 'core' && <LoomCore envelope={envelope} events={filtered} allEvents={events} filters={filters} setFilters={setFilters} clockSmooth={memetic.smoothWindow} clockAlpha={memetic.clockAlpha} lastScan={tel?.last_scan || tel?.ts} />}
        {tab === 'nela' && <NelaSubstrat tel={tel} />}
        {tab === 'steri' && <SteriNet />}
        {tab === 'filtre' && <FiltreMemetique memetic={memetic} setMemetic={setMemetic} events={events} />}
      </main>
    </div>
  );
}
