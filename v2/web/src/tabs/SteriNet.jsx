import { useEffect, useState } from 'react';
import { Database, ShieldAlert, Trash2, RefreshCw } from 'lucide-react';

// Onglet 3 — STERI-NET & RAG : base de connaissances locale, quarantaine, purge VRAM
export default function SteriNet() {
  const [rag, setRag] = useState(null);
  const [purging, setPurging] = useState(false);
  const [purgeResult, setPurgeResult] = useState(null);

  const load = async () => { try { const r = await fetch('/api/rag'); if (r.ok) setRag(await r.json()); } catch {} };
  useEffect(() => { load(); const iv = setInterval(load, 5000); return () => clearInterval(iv); }, []);

  const purge = async () => {
    setPurging(true); setPurgeResult(null);
    try {
      const r = await fetch('/api/purge', { method: 'POST' });
      setPurgeResult(await r.json());
    } catch (e) { setPurgeResult({ ok: false, error: String(e) }); }
    setPurging(false);
  };

  return (
    <div className="h-full grid grid-cols-2 gap-3 min-h-0">
      {/* RAG */}
      <div className="panel p-3 overflow-y-auto min-h-0">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-2">
          <Database size={12} /> BASE RAG LOCALE <button onClick={load} className="ml-auto text-zinc-500 hover:text-white"><RefreshCw size={12} /></button>
        </div>
        <div className="grid grid-cols-3 gap-2 mb-3 text-center">
          <div className="bubble py-2"><div className="text-xl font-black amber-text">{rag?.documents ?? '—'}</div><div className="text-[9px] text-zinc-500">DOCS VECTORISÉS</div></div>
          <div className="bubble py-2"><div className="text-xl font-black text-neon-cyan">{rag?.db_mb ?? '—'} <span className="text-[10px]">Mo</span></div><div className="text-[9px] text-zinc-500">TAILLE DB</div></div>
          <div className="bubble py-2"><div className="text-xl font-black text-neon-green">{rag ? 'LOCALE' : '—'}</div><div className="text-[9px] text-zinc-500">ORIGINE</div></div>
        </div>
        <div className="text-[10px] text-zinc-500 mb-1">répertoire: {rag?.dir}</div>
        <ul className="text-[10px] text-zinc-400 space-y-0.5">
          {(rag?.files || []).slice(-15).reverse().map((f, i) => (
            <li key={i} className="flex justify-between"><span className="truncate max-w-[70%]">{f.name}</span><span className="text-zinc-600">{(f.size / 1024).toFixed(0)} Ko</span></li>
          ))}
        </ul>
      </div>

      {/* quarantaine + purge */}
      <div className="flex flex-col gap-3 min-h-0">
        <div className="panel p-3 flex-1 overflow-y-auto min-h-0">
          <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-red mb-2"><ShieldAlert size={12} /> QUARANTAINE — INSPECTION PROMPTS/TENSEURS</div>
          {(rag?.quarantine || []).length === 0 && <div className="text-[11px] text-zinc-600">Aucune entrée de quarantaine.</div>}
          <ul className="text-[10px] space-y-1">
            {(rag?.quarantine || []).slice(-30).reverse().map((q, i) => (
              <li key={i} className="border-l-2 border-red-500/60 pl-2 text-zinc-400">
                {q.ts || q.time || ''} <span className="text-zinc-600">{q.reason || q.event || ''}</span> <span className="text-zinc-500">{JSON.stringify(q.prompt || q.raw || q).slice(0, 90)}</span>
              </li>
            ))}
          </ul>
        </div>
        <button onClick={purge} disabled={purging}
          className="bubble px-4 py-3 text-sm font-bold flex items-center justify-center gap-2 hover:bg-red-500/10"
          style={{ borderColor: 'rgba(255,56,96,0.5)', color: '#ff3860' }}>
          <Trash2 size={16} /> {purging ? 'PURGE EN COURS…' : 'PURGE VRAM / HARD FLUSH'}
        </button>
        {purgeResult && (
          <div className={`bubble p-2 text-[10px] ${purgeResult.ok ? 'text-neon-green' : 'red-text'}`}>
            {purgeResult.ok ? 'Purge OK: ' + (purgeResult.actions || []).join(' · ') : 'Erreur: ' + purgeResult.error}
          </div>
        )}
      </div>
    </div>
  );
}
