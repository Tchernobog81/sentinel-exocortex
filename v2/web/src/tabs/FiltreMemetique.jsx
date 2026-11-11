import { SlidersHorizontal, Activity } from 'lucide-react';

// Onglet 4 — FILTRE MÉMÉTIQUE : ratio bruit marketing / signal cinétique + lissage horloge apocalypse
export default function FiltreMemetique({ memetic, setMemetic, events }) {
  const kinetic = (events || []).filter(e => e.is_kinetic_signal).length;
  const total = (events || []).length;
  const ratio = total ? Math.round((kinetic / total) * 100) : 0;

  return (
    <div className="h-full grid grid-cols-2 gap-3 min-h-0">
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
        <div className="text-[10px] text-zinc-600 mt-3">Valeur brute (dernier réglage officiel) : {(events || []).filter(e => e.doomsday_minutes != null).length} points ⏰ — voir LOOM CORE pour le rendu lissé.</div>
      </div>
    </div>
  );
}
