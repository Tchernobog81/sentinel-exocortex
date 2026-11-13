import { useEffect, useState } from 'react';
import { SlidersHorizontal, Activity, TerminalSquare, Save } from 'lucide-react';

const DEFAULT_PROMPT = [
  '[PROMPT DE VEILLE — Sentinel Exocortex / The Loom]',
  'FOCUS STRICT : faits avérés sourcés liés à la singularité / course à l\'AGI (étude AI2027 en priorité),',
  'compute, autonomie des agents, modèles frontier (ARC-AGI), risques existentiels, cyber, espace, régulation.',
  'Corroborer 2+ sources de confiance (domaines primaires fiables). Un événement = une année RÉELLE. Ignorer les faits divers sans lien.',
].join('\n');

// Onglet 4 — FILTRE MÉMÉTIQUE : ratio bruit marketing / signal cinétique + lissage horloge apocalypse + encard prompt agent
export default function FiltreMemetique({ memetic, setMemetic, events }) {
  const kinetic = (events || []).filter(e => e.is_kinetic_signal).length;
  const total = (events || []).length;
  const ratio = total ? Math.round((kinetic / total) * 100) : 0;

  // encard éditable : prompt de l'agent de veille, renvoyé au serveur local (agent_prompt.txt)
  const [prompt, setPrompt] = useState('');
  const [promptStatus, setPromptStatus] = useState('');
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch('api/prompt?cb=' + Date.now(), { cache: 'no-store' });
        if (!r.ok) throw new Error('no-server');
        const j = await r.json();
        setPrompt(j.prompt || DEFAULT_PROMPT);
        setPromptStatus(j.custom ? 'prompt actuel (agent_prompt.txt)' : 'prompt par défaut (fichier absent)');
      } catch {
        // mode Pages (statique) : lire agent_prompt.txt publié, sinon localStorage, sinon défaut
        try {
          const r2 = await fetch('agent_prompt.txt?cb=' + Date.now(), { cache: 'no-store' });
          if (r2.ok) { setPrompt(await r2.text()); setPromptStatus('agent_prompt.txt (dépôt) — à renvoyer via le serveur local pour appliquer à l\'agent'); return; }
        } catch {}
        setPrompt(localStorage.getItem('loom_agent_prompt') || DEFAULT_PROMPT);
        setPromptStatus('mode Pages (serveur local absent) : édition en localStorage');
      }
    })();
  }, []);
  const savePrompt = async () => {
    setPromptStatus('envoi…');
    try {
      const r = await fetch('api/prompt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt }) });
      if (!r.ok) throw new Error('http ' + r.status);
      const j = await r.json();
      setPromptStatus(j.ok ? `OK — renvoyé à l'agent (${j.path}, ${j.chars} car.) — appliqué au prochain cycle (≤ 5 min)` : 'KO: ' + (j.error || ''));
    } catch {
      localStorage.setItem('loom_agent_prompt', prompt);
      setPromptStatus("mode Pages : sauvegardé en localStorage — à copier dans agent_prompt.txt sur le Mac pour l'appliquer à l'agent");
    }
  };

  return (
    <div className="h-full grid grid-cols-2 grid-rows-[auto_auto_minmax(0,1fr)] gap-3 min-h-0">
      <div className="panel p-4">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-3"><Activity size={12} /> RATIO BRUIT MARKETING / SIGNAL CINÉTIQUE</div>
        <div className="text-4xl font-black amber-text mb-1">{100 - memetic.noiseRatio}<span className="text-sm text-zinc-500">% signal</span></div>
        <div className="text-[11px] text-zinc-400 mb-4">{kinetic}/{total} événements sont des signaux cinétiques (tipping/vérifiés) → ratio actuel mesuré: {ratio}%</div>
        <label className="text-[10px] text-zinc-500 flex justify-between"><span>filtrer le bruit marketing</span><span>{memetic.noiseRatio}%</span></label>
        <input type="range" min="0" max="100" value={memetic.noiseRatio} className="w-full"
               onChange={e => setMemetic(m => ({ ...m, noiseRatio: +e.target.value }))} />
        <div className="text-[10px] text-zinc-600 mt-1">Appliqué au flux et à la courbe de l'onglet LOOM CORE (les signaux cinétiques sont toujours conservés).</div>
      </div>

      <div className="panel p-4">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-3"><SlidersHorizontal size={12} /> LISissage HORLOGE DE L'APOCALYPSE</div>
        <div className="text-[11px] text-zinc-400 mb-4">Fenêtre de moyenne glissante (en réglages) appliquée au compte à rebours affiché dans LOOM CORE :</div>
        <label className="text-[10px] text-zinc-500 flex justify-between"><span>fenêtre de lissage</span><span>{memetic.smoothWindow} réglages</span></label>
        <input type="range" min="1" max="10" value={memetic.smoothWindow} className="w-full"
               onChange={e => setMemetic(m => ({ ...m, smoothWindow: +e.target.value }))} />
        <label className="text-[10px] text-zinc-500 flex justify-between mt-2"><span>EMA de la courbe (alpha)</span><span>{Number(memetic.clockAlpha ?? 0.22).toFixed(2)}</span></label>
        <input type="range" min="0.05" max="0.6" step="0.01" value={memetic.clockAlpha ?? 0.22} className="w-full"
               onChange={e => setMemetic(m => ({ ...m, clockAlpha: +e.target.value }))} />
        <div className="text-[10px] text-zinc-600 mt-3">V2.8.0 : la courbe ⏰ tracée = buckets (1 pt/jour récent, 1 pt/mois, 1 pt/an) + EMA(alpha) + interpolation monotone — plus de dents de scie. {(events || []).filter(e => e.doomsday_minutes != null).length} réglages officiels → marqueurs alignés sur la courbe lissée, valeurs brutes dans le détail.</div>
      </div>

      {/* Métriques : benchmark d'alignement & vitesse de régression logicielle */}
      <div className="panel p-4 col-span-2">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-3"><Activity size={12} /> MÉTRIQUES DE RÉGRESSION & ALIGNEMENT</div>
        {(() => {
          const now = new Date().getFullYear() + new Date().getMonth() / 12;
          const all = events || [];
          const recent = all.filter(e => (e.year || 0) >= now - 1 && (e.year || 0) <= now + 0.05);
          const verified = recent.filter(e => e.verified !== false).length;
          const aligned = recent.length ? (verified / recent.length) : 0;
          const last12 = all.filter(e => (e.year || 0) >= now - 1);
          const velocity = last12.length; // événements/12 mois
          return (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-[10px] text-zinc-500 uppercase mb-1">Benchmark d'alignement (faits vérifiés)</div>
                <div className="text-2xl font-black text-neon-cyan">{(aligned * 100).toFixed(1)}%</div>
                <div className="h-2 rounded-full bg-zinc-800 overflow-hidden mt-1">
                  <div className="h-full bg-cyan-400" style={{ width: `${aligned * 100}%` }} />
                </div>
                <div className="text-[9px] text-zinc-600 mt-1">{verified}/{recent.length} sur 12 mois glissants</div>
              </div>
              <div>
                <div className="text-[10px] text-zinc-500 uppercase mb-1">Vitesse de régression logicielle (événements/12 mois)</div>
                <div className="text-2xl font-black amber-text">{velocity}</div>
                <div className="h-2 rounded-full bg-zinc-800 overflow-hidden mt-1">
                  <div className="h-full bg-amber-400" style={{ width: `${Math.min(100, velocity)}%` }} />
                </div>
                <div className="text-[9px] text-zinc-600 mt-1">Signaux intégrés à la courbe sur la dernière année</div>
              </div>
            </div>
          );
        })()}
      </div>

      {/* encard éditable : prompt utilisé par l'agent local pour ses recherches — modifiable et renvoyé à l'agent */}
      <div className="panel p-4 col-span-2 flex flex-col min-h-0">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-1">
          <TerminalSquare size={12} /> ENCARD — PROMPT DE L'AGENT DE VEILLE (éditable)
        </div>
        <div className="text-[10px] text-zinc-500 mb-2">
          Ce texte est écrit dans <span className="font-mono text-zinc-400">agent_prompt.txt</span> (racine du dépôt) et relu par le sentinel à chaque cycle (~5 min) :
          il pilote la pertinence des recherches (focus AI2027 / faits vérifiés) ; le fact-check est durci côté sources : corroboration par 2+ domaines de confiance distincts (presse tech reconnue, CERT/CVE, status pages fournisseurs, arXiv/Nature…), une URL seulement joignable ne suffit pas.
        </div>
        <textarea value={prompt} onChange={e => setPrompt(e.target.value)} spellCheck={false}
                  className="flex-1 min-h-[110px] bg-black/40 border border-cyan-500/30 rounded-md p-2 text-[11px] font-mono text-zinc-200 focus:border-cyan-400 focus:outline-none resize-y" />
        <div className="flex items-center gap-2 mt-2 shrink-0">
          <button onClick={savePrompt} className="tab-btn active flex items-center gap-1.5 !text-[10px]"><Save size={12} /> Envoyer à l'agent</button>
          <span className="text-[10px] text-zinc-500 truncate">{promptStatus}</span>
          <span className="ml-auto text-[10px] text-zinc-600 shrink-0">{prompt.length} car.</span>
        </div>
      </div>
    </div>
  );
}
