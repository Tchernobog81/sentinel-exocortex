import { useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Radio, X, ArrowLeftRight } from 'lucide-react';

export const LOOM_VERSION = '2.1.5';

// Onglet 1 — LOOM CORE (V2.1.2) : le chart s'initialise UNE fois (le zoom utilisateur est préservé
// entre les rafraîchissements SSE), les séries sont mises à jour en douceur.
export default function LoomCore({ envelope, events, allEvents, filters, setFilters, clockSmooth }) {
  const chartRef = useRef(null);
  const wrapRef = useRef(null);
  const boxRef = useRef(null);
  const eventsRef = useRef(events);
  const hiddenRef = useRef({});
  const [selected, setSelected] = useState(null);
  const [hover, setHover] = useState(null);
  const [hiddenGroups, setHiddenGroups] = useState({});
  window.__selectEvent = (ev) => setSelected(ev); // hook de test

  const nowYear = new Date().getFullYear() + new Date().getMonth() / 12;

  // ---- horloge de l'apocalypse : lissage glissant (paramètre onglet 4) ----
  const clockSeries = useMemo(() => {
    return (allEvents || []).filter(e => e.doomsday_minutes != null).sort((a, b) => a.year - b.year)
      .map(e => ({ year: e.year, seconds: Math.round(e.doomsday_minutes * 60) }));
  }, [allEvents]);
  const smoothed = useMemo(() => {
    if (!clockSeries.length) return envelope.apocalypse_clock_seconds ?? 85;
    const w = Math.max(1, clockSmooth | 0);
    const tail = clockSeries.slice(-w).map(c => c.seconds);
    return Math.round(tail.reduce((a, b) => a + b, 0) / tail.length) || clockSeries[clockSeries.length - 1].seconds;
  }, [clockSeries, envelope.apocalypse_clock_seconds, clockSmooth]);

  const groups = useMemo(() => {
    const g = {};
    for (const e of events) g[e.group] = e.groupColor;
    return g;
  }, [events]);

  // ---- INIT du chart : une seule fois (le zoom survit aux rafraîchissements) ----
  useEffect(() => {
    if (!boxRef.current || chartRef.current) return;
    const chart = echarts.init(boxRef.current, null, { renderer: 'canvas' });
    chartRef.current = chart;
    window.__loomChart = chart;

    const XMIN = -2700, XMAX = 2110;
    // vue initiale centrée sur aujourd'hui (±60 ans)
    const nowFrac = (nowYear - XMIN) / (XMAX - XMIN);
    const half = 60 / (XMAX - XMIN);
    const start = Math.max(0, Math.min(100, (nowFrac - half) * 100));
    const end = Math.max(0, Math.min(100, (nowFrac + half) * 100));
    let xWin = (XMAX - XMIN) * (end - start) / 100;

    chart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 400,
      tooltip: { show: false },
      legend: { show: false },
      toolbox: { right: 12, top: 6, itemSize: 16, feature: { dataZoom: { xAxisIndex: 0, yAxisIndex: 'none', title: { zoom: 'Zoom', back: 'Reset zoom' } }, restore: { title: "Vue d'aujourd'hui" } } },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, zoomOnMouseWheel: true, moveOnMouseWheel: false, zoomOnMouseMove: false, start, end },
        { type: 'slider', xAxisIndex: 0, bottom: 2, height: 16, filterMode: 'none', start, end },
      ],
      grid: { left: 50, right: 30, top: 40, bottom: 34 },
      xAxis: { type: 'value', min: XMIN, max: XMAX, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' },
        axisLabel: {
          color: '#6b7280', fontSize: 10, hideOverlap: true,
          // zoom temporel : années -> mois -> jours (fenêtre courante relue à chaque formatage)
          formatter: v => {
            try {
              const dzs = chart.getOption().dataZoom || [];
              const dz = dzs.find(d => d.type === 'inside') || dzs[0];
              if (dz && dz.start != null) xWin = (XMAX - XMIN) * (dz.end - dz.start) / 100;
            } catch {}
            const range = xWin;
            const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
            if (range > 25) return String(Math.floor(v));
            if (range > 2) { const y = Math.floor(v); const m = Math.max(0, Math.min(11, Math.floor((v - y) * 12))); return `${MOIS[m]} ${String(y).slice(2)}`; }
            const y = Math.floor(v), frac = v - y, d = new Date(y, 0, 1 + Math.floor(frac * 365));
            return `${String(d.getDate()).padStart(2, '0')}/${MOIS[d.getMonth()]}/${String(y).slice(2)}`;
          },
        } },
      yAxis: [
        { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
        // axe caché pour l'horloge de l'apocalypse (échelle "danger" distincte)
        { type: 'value', show: false, min: 0, max: 50000 },
      ],
      series: [],
    }, { notMerge: true });

    // clic -> popup détail : même picking au pixel près que le survol (le proxy
    // chart.on('click') ne se déclenche que sur un symbole exact)
    const pickNearest = (zx, zy) => {
      let best = null, bd = 22 * 22;
      for (const ev of eventsRef.current) {
        if (hiddenRef.current[ev.group]) continue;
        const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [ev.year, ev.value]);
        const d = (px[0] - zx) ** 2 + (px[1] - zy) ** 2;
        if (d < bd) { bd = d; best = ev; }
      }
      return best;
    };
    chart.getZr().on('click', e => {
      const zx = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
      const hit = pickNearest(zx, zy);
      if (hit) setSelected(hit);
    });

    // survol : picking manuel au pixel près (seuil 20 px), branché sur ZRENDER
    // (chart.on('mousemove') ne se déclenche QUE sur un élément dessiné -> bulle fantôme)
    let raf = 0;
    chart.getZr().on('mousemove', e => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const zx = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
        const hit = pickNearest(zx, zy);
        if (hit) {
          const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [hit.year, hit.value]);
          setHover({ x: px[0], y: px[1], ev: hit });
        } else setHover(null);
      });
    });
    chart.getZr().on('globalout', () => setHover(null));
    chart.getDom().addEventListener('mouseleave', () => setHover(null));

    // fenêtre courante (années) + Y ajusté aux données réelles visibles (comme V1 : le décollage est visible)
    const winRange = () => {
      try {
        const dzs = chart.getOption().dataZoom || [];
        const dz = dzs.find(d => d.type === 'inside') || dzs[0];
        if (dz && dz.start != null) return (XMAX - XMIN) * (dz.end - dz.start) / 100;
      } catch {}
      return XMAX - XMIN;
    };
    const fitYToWindow = () => {
      try {
        const dzs = chart.getOption().dataZoom || [];
        const dz = dzs.find(d => d.type === 'inside') || dzs[0];
        const x0 = XMIN + ((dz?.start ?? 0) / 100) * (XMAX - XMIN);
        const x1 = XMIN + ((dz?.end ?? 100) / 100) * (XMAX - XMIN);
        let hi = 0, lo = Infinity;
        for (const ev of eventsRef.current) {
          if ((ev.year || 0) > nowYear + 0.05) continue;            // prévisions hors Y-fit
          if (/horloge/i.test(ev.group || '')) continue;            // horloge sur son propre axe
          if (hiddenRef.current[ev.group]) continue;
          if ((ev.year || 0) >= x0 && (ev.year || 0) <= x1) { hi = Math.max(hi, ev.value || 0); lo = Math.min(lo, ev.value || 0); }
        }
        if (hi > 0) chart.setOption({ yAxis: { min: Math.max(0, Math.floor(lo * 0.9)), max: Math.round(hi * 1.05) } });
      } catch {}
    };
    // ticks : toutes les années -> TOUS les mois -> les jours (minInterval selon la fenêtre)
    const applyTickInterval = () => {
      const r = winRange();
      let minInterval;
      if (r > 24) minInterval = Math.max(1, Math.round(r / 8));
      else if (r > 4) minInterval = 1;            // une graduation par an
      else if (r > 1.5) minInterval = 1 / 12;      // TOUS les mois
      else minInterval = 7 / 365;                 // jour par jour (hebdo minimum)
      try { chart.setOption({ xAxis: { minInterval } }); } catch {}
    };
    let dzT = 0;
    chart.on('datazoom', () => {
      clearTimeout(dzT);
      dzT = setTimeout(() => { applyTickInterval(); fitYToWindow(); }, 120);
    });
    window.__fitY = fitYToWindow; // l'update des séries relance le Y-fit (zoom préservé)
    window.__ticks = applyTickInterval;
    setTimeout(() => { applyTickInterval(); fitYToWindow(); }, 250);

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(boxRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- MISE À JOUR des séries (préserve le zoom/pan utilisateur) ----
  useEffect(() => {
    eventsRef.current = events;
    hiddenRef.current = hiddenGroups;
    const chart = chartRef.current;
    if (!chart) return;
    const byGroup = {};
    for (const e of events) {
      if (hiddenGroups[e.group]) continue;
      (byGroup[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);
    }
    const series = [];
    for (const [name, g] of Object.entries(byGroup)) {
      const pts = g.data;
      const yIdx = /horloge/i.test(name) ? 1 : 0; // horloge sur axe caché (le décollage J reste lisible)
      // courbe en J reliée (style V1) : points réels triés par année ; les prévisions restent des points
      const real = pts.filter(e => (e.year || 0) <= nowYear + 0.05).sort((a, b) => a.year - b.year);
      if (real.length > 1) {
        series.push({
          name, type: 'line', smooth: 0.45, showSymbol: false, z: 5, yAxisIndex: yIdx,
          lineStyle: { color: g.color, width: 3, opacity: 0.9, shadowColor: g.color, shadowBlur: 8 },
          areaStyle: { color: g.color, opacity: 0.06 },
          data: real.map(e => [e.year, e.value]),
        });
      }
      series.push({
        name, type: 'scatter', z: 3, yAxisIndex: yIdx,
        symbolSize: d => (d[3]?.tipping ? 10 : 5),
        itemStyle: { color: g.color, opacity: 0.95, borderColor: '#050508', borderWidth: 1 },
        emphasis: { scale: 1.6 },
        // étiquette MINIMALE sur les POI principaux, anti-recouvrement par hideOverlap
        label: {
          show: true, position: 'top', fontSize: 9, color: '#cbd5e1',
          formatter: d => (d[3]?.tipping ? `${String(d[2]).slice(0, 18)}…` : ''),
          rotate: 28, distance: 5,
        },
        labelLayout: { hideOverlap: true, moveToEnd: () => {} },
        data: pts.map(e => [e.year, e.value, e.title, e]),
      });
    }
    if (series.length) {
      // ligne pointillée verticale à la date du jour (comme V1)
      series[0].markLine = {
        silent: true, symbol: 'none', z: 2,
        lineStyle: { color: '#fbbf24', type: 'dashed', width: 1.5, opacity: 0.85 },
        label: { color: '#fbbf24', fontSize: 9, position: 'insideEndTop', formatter: 'MAINTENANT' },
        data: [{ xAxis: nowYear }],
      };
    }
    chart.setOption({ series }, { lazyUpdate: true, notMerge: false });
    setTimeout(() => { try { chart.getOption().onFitY?.(); } catch {} }, 0);
    window.__fitY && window.__fitY();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, hiddenGroups]);

  // ---- saut vers un événement (lien ⇄ ou flux) ----
  const jumpToEvent = (target) => {
    const chart = chartRef.current;
    if (chart && target?.year != null) {
      const xa = chart.getOption().xAxis[0];
      const f = (target.year - xa.min) / (xa.max - xa.min);
      const half = 0.06;
      chart.dispatchAction({ type: 'dataZoom', start: Math.max(0, Math.min(100, (f - half) * 100)), end: Math.max(0, Math.min(100, (f + half) * 100)) });
    }
    setSelected(target);
  };
  const jumpToLabel = (label, yearHint) => {
    const cands = (allEvents || []).filter(e => e.title === label);
    if (!cands.length) return;
    const target = yearHint != null
      ? cands.slice().sort((a, b) => Math.abs((a.year || 0) - yearHint) - Math.abs((b.year || 0) - yearHint))[0]
      : (cands.find(e => e.realYear || e.predictedBy?.length) || cands[0]);
    jumpToEvent(target);
  };

  // ---- flux entrant : faits réels vérifiés de l'année en cours, antichrono, sans stamps "année seule" ----
  const effTs = e => {
    const y = Math.floor(e.year || 1970);
    const d = new Date(e.timestamp);
    if (!isNaN(d.getTime()) && y >= nowYear - 1) return d;
    return new Date(y, 0, 1);
  };
  const feed = useMemo(() => {
    const base = events
      .filter(e => !/fiction|horloge/i.test(e.category) && e.verified !== false && (e.year || 0) >= nowYear - 1 && (e.year || 0) <= nowYear + 0.05)
      .map(e => ({ e, t: effTs(e) }))
      .sort((a, b) => b.t - a.t);
    // liste REMPLIE : les 30 derniers événements antichronologiques de l'année en cours
    return base.slice(0, 30).map(x => x.e);
  }, [events]);
  const lastMaj = useMemo(() => {
    let mx = null;
    for (const e of events) {
      if ((e.year || 0) < nowYear - 1 || (e.year || 0) > nowYear + 1) continue;
      const d = new Date(e.timestamp);
      if (isNaN(d.getTime()) || d > new Date()) continue;
      if (!mx || d > mx) mx = d;
    }
    return mx ? `${String(mx.getHours()).padStart(2, '0')}:${String(mx.getMinutes()).padStart(2, '0')}` : '--:--';
  }, [events]);
  // date véridique : timestamp réel (avec heure) sinon mois dérivé honnêtement de la fraction d'année
  const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  const fmtTs = e => {
    const d = new Date(e.timestamp);
    if (!isNaN(d.getTime()) && (d.getHours() !== 0 || d.getMinutes() !== 0)) {
      if (d.getFullYear() === new Date().getFullYear()) return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
      return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }
    const y = Math.floor(e.year || 0), m = Math.max(0, Math.min(11, Math.floor(((e.year || 0) - y) * 12)));
    return `${MOIS[m]} ${y}`;
  };

  // bulle de survol : centrée AU-DESSUS du point, trait vertical court qui la rattache au point
  const bubbleH = 36;
  const hb = hover ? (() => {
    const wrapW = wrapRef.current?.clientWidth || 800;
    return { bx: Math.max(4, Math.min(hover.x - 110, wrapW - 290)), by: Math.max(6, hover.y - bubbleH - 26) };
  })() : null;

  return (
    <div className="h-full grid grid-cols-[300px_1fr] gap-3 min-h-0">
      {/* panneau gauche : flux */}
      <aside className="panel p-3 overflow-y-auto min-h-0">
        <div className="flex items-center gap-2 text-neon-cyan text-[10px] tracking-widest mb-2">
          <Radio size={12} className="animate-pulse" /> FLUX ENTRANT · MAJ {lastMaj}
        </div>
        <ul className="space-y-1.5">
          {feed.map(e => (
            <li key={e.id} className="text-[11px] leading-snug cursor-pointer hover:bg-cyan-500/10 rounded px-1 py-0.5"
                onClick={() => jumpToEvent(e)} title={e.title}>
              <span style={{ color: e.groupColor }}>●</span>{' '}
              <span className="text-zinc-500">[{fmtTs(e)}]</span>{' '}
              {e.title}
            </li>
          ))}
        </ul>
      </aside>

      {/* zone centrale */}
      <section className="flex flex-col gap-3 min-h-0">
        <div className="panel px-4 py-2 flex items-center gap-4 shrink-0 flex-wrap">
          <div className="flex items-center gap-2">
            <Clock3 size={16} className="red-text" />
            <div>
              <div className="red-text font-black text-2xl leading-none">{smoothed}<span className="text-xs ml-1">s</span></div>
              <div className="text-[9px] text-zinc-500 uppercase tracking-widest">avant minuit · lissage {clockSmooth}</div>
            </div>
          </div>
          <div className="text-[10px] text-zinc-400">Singularité: <b className="amber-text">{(envelope.singularity_index ?? 0).toFixed(3)}</b></div>

        </div>

        {/* légende custom : pastilles à la couleur des courbes */}
        <div className="panel px-3 py-1.5 flex items-center gap-2 flex-wrap shrink-0">
          {Object.entries(groups).map(([g, color]) => (
            <span key={g} className="chip flex items-center gap-1.5" title={g}
                  style={hiddenGroups[g] ? { opacity: 0.35 } : { borderColor: color, color }}
                  onClick={() => setHiddenGroups(h => ({ ...h, [g]: !h[g] }))}>
              <span style={{ background: color, boxShadow: `0 0 6px ${color}` }} className="inline-block w-2.5 h-2.5 rounded-full" /> {g}
            </span>
          ))}
        </div>

        {/* graphique + bulle de survol */}
        <div ref={wrapRef} className="relative flex-1 min-h-0">
          <div ref={boxRef} className="panel absolute inset-0" />
          {hover && hb && (
            <>
              <div style={{ position: 'absolute', left: hover.x, top: hb.by + bubbleH - 2, width: 1.5,
                height: Math.max(6, hover.y - (hb.by + bubbleH)), background: hover.ev.groupColor,
                boxShadow: `0 0 6px ${hover.ev.groupColor}`, pointerEvents: 'none', zIndex: 30 }} />
              <div className="bubble absolute px-2.5 py-1.5 text-[10px] font-bold pointer-events-none z-40"
                   style={{ left: hb.bx, top: hb.by, borderColor: hover.ev.groupColor, color: hover.ev.groupColor, borderRadius: 12 }}>
                {hover.ev.title} <span className="text-zinc-500">({Math.floor(hover.ev.year)})</span>
              </div>
            </>
          )}
        </div>
      </section>

      {/* popup détail façon V1 + liens ⇄ */}
      {selected && (
        <div className="fixed inset-0 z-[5000] flex items-center justify-center bg-black/60" onClick={() => setSelected(null)}>
          <div className="bubble relative w-[90%] max-w-[600px] max-h-[82vh] overflow-y-auto p-6"
               style={{ borderColor: selected.groupColor, boxShadow: `0 0 40px ${selected.groupColor}33` }}
               onClick={e => e.stopPropagation()}>
            <button onClick={() => setSelected(null)} className="absolute top-3 right-3 text-zinc-500 hover:text-white text-2xl leading-none"><X size={18} /></button>
            <h2 className="text-xl font-black uppercase pr-8" style={{ color: selected.groupColor }}>{selected.title}</h2>
            <div className="flex gap-4 text-[10px] text-zinc-500 uppercase mt-1 mb-3 border-b border-zinc-800 pb-2 flex-wrap">
              <span>Source: <b className="text-zinc-300">{selected.source || 'N/A'}</b></span>
              <span>Date: <b className="text-zinc-300">{Math.floor(selected.year)}</b></span>
              <span>Catégorie: <b className="text-zinc-300">{selected.category}</b></span>
              <span>Impact: <b className="text-zinc-300">{selected.impact_score}</b></span>
            </div>
            <div className="flex gap-2 flex-wrap mb-3">
              {selected.realLabel && (
                <button className="chip on flex items-center gap-1" style={{ borderColor: selected.groupColor, color: selected.groupColor }}
                        onClick={() => jumpToLabel(selected.realLabel, selected.realYear)}>
                  <ArrowLeftRight size={11} /> réalisé : {selected.realLabel} ({Math.floor(selected.realYear)})
                </button>
              )}
              {(selected.predictedBy || []).map(t => (
                <button key={t} className="chip on flex items-center gap-1" style={{ borderColor: selected.groupColor, color: selected.groupColor }}
                        onClick={() => jumpToLabel(t)}>
                  <ArrowLeftRight size={11} /> prédit par : {t}
                </button>
              ))}
            </div>
            <p className="text-sm text-zinc-300 italic leading-relaxed">{selected.description || 'Pas de description.'}</p>
            <div className="mt-3 text-[9px] text-zinc-700 font-mono">{selected.group} · {selected.id}</div>
          </div>
        </div>
      )}
    </div>
  );
}
