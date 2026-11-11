import { useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Filter, Radio, X, ArrowLeftRight } from 'lucide-react';

export const LOOM_VERSION = '2.1.0';

// Onglet 1 — LOOM CORE (V2.1) : vue centrée sur aujourd'hui, courbes J reliées (style V1),
// étiquettes minimales anti-recouvrement, popup détail façon V1 au clic + liens ⇄ prédit/réalisé
export default function LoomCore({ envelope, events, allEvents, filters, setFilters, clockSmooth }) {
  const chartRef = useRef(null);
  const wrapRef = useRef(null);
  const boxRef = useRef(null);
  const [selected, setSelected] = useState(null);   // événement dont la popup est ouverte
  const [hover, setHover] = useState(null);          // {x, y (px dans le wrap), ev}
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

  const cats = useMemo(() => [...new Set((allEvents || []).map(e => e.category))], [allEvents]);
  const groups = useMemo(() => {
    const g = {};
    for (const e of events) g[e.group] = e.groupColor;
    return g;
  }, [events]);

  // ---- J-curve ECharts ----
  useEffect(() => {
    if (!boxRef.current) return;
    const chart = echarts.init(boxRef.current, null, { renderer: 'canvas' });
    chartRef.current = chart;
    window.__loomChart = chart;

    const XMIN = -2700, XMAX = 2110;
    const byGroup = {};
    for (const e of events) {
      if (hiddenGroups[e.group]) continue;
      (byGroup[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);
    }
    const series = [];
    for (const [name, g] of Object.entries(byGroup)) {
      const pts = g.data;
      // courbe en J reliée (style V1) : tous les points RÉELS, triés par année, lissée.
      // Seuls les événements futurs (prévisions) sont exclus de la ligne.
      const real = pts.filter(e => (e.year || 0) <= nowYear + 0.05).sort((a, b) => a.year - b.year);
      if (real.length > 1) {
        series.push({
          name, type: 'line', smooth: 0.45, showSymbol: false, z: 1,
          lineStyle: { color: g.color, width: 2, opacity: 0.75 },
          areaStyle: { color: g.color, opacity: 0.06 },
          data: real.map(e => [e.year, e.value]),
        });
      }
      series.push({
        name, type: 'scatter', z: 3,
        symbolSize: d => (d[3]?.tipping ? 11 : 6),
        itemStyle: { color: g.color, opacity: 0.95, borderColor: '#050508', borderWidth: 1 },
        emphasis: { scale: 1.6 },
        // étiquette MINIMALE sur les POI principaux (tipping), anti-recouvrement par hideOverlap
        label: {
          show: true, position: 'top', fontSize: 9, color: '#cbd5e1',
          formatter: d => (d[3]?.tipping ? `${String(d[2]).slice(0, 22)}…` : ''),
        },
        labelLayout: { hideOverlap: true },
        data: pts.map(e => [e.year, e.value, e.title, e]),
      });
    }

    // vue initiale CENTRÉE SUR AUJOURD'HUI (±60 ans), zoom molette + slider + restore
    const nowFrac = (nowYear - XMIN) / (XMAX - XMIN);
    const half = 60 / (XMAX - XMIN);
    const start = Math.max(0, Math.min(100, (nowFrac - half) * 100));
    const end = Math.max(0, Math.min(100, (nowFrac + half) * 100));

    chart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 600,
      tooltip: { show: false },
      legend: { show: false },
      toolbox: { right: 12, top: 6, itemSize: 16, feature: { dataZoom: { xAxisIndex: 0, yAxisIndex: 'none', title: { zoom: 'Zoom', back: 'Reset zoom' } }, restore: { title: 'Vue complète' } } },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, zoomOnMouseWheel: true, moveOnMouseWheel: false, zoomOnMouseMove: false, start, end },
        { type: 'slider', xAxisIndex: 0, bottom: 2, height: 16, filterMode: 'none', start, end },
      ],
      grid: { left: 50, right: 30, top: 40, bottom: 34 },
      xAxis: { type: 'value', min: XMIN, max: XMAX, axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' } },
      yAxis: { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
      series,
    }, { notMerge: true });

    // clic -> popup détail (box façon V1)
    chart.on('click', p => { if (p.data?.[3]) setSelected(p.data[3]); });

    // survol : picking manuel au pixel près
    let raf = 0;
    const evsRef = { current: events };
    evsRef.current = events;
    chart.on('mousemove', e => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const zx = e.event.zrX ?? e.event.offsetX, zy = e.event.zrY ?? e.event.offsetY;
        let best = null, bd = 20 * 20;
        for (const ev of evsRef.current) {
          if (hiddenGroups[ev.group]) continue;
          const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [ev.year, ev.value]);
          const d = (px[0] - zx) ** 2 + (px[1] - zy) ** 2;
          if (d < bd) { bd = d; best = { x: px[0], y: px[1], ev }; }
        }
        setHover(best);
      });
    });
    chart.on('mouseout', () => setHover(null));

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(boxRef.current);
    return () => { ro.disconnect(); chart.dispose(); chartRef.current = null; window.__loomChart = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, hiddenGroups]);

  // ---- saut vers un événement (lien ⇄ ou flux) : centre le zoom dessus + ouvre sa popup ----
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

  // ---- flux entrant : faits réels vérifiés de l'année en cours, antichrono ----
  const effTs = e => {
    const y = Math.floor(e.year || 1970);
    const d = new Date(e.timestamp);
    if (!isNaN(d.getTime()) && y >= nowYear - 1) return d;
    return new Date(y, 0, 1);
  };
  const feed = useMemo(() => {
    return events
      .filter(e => !/fiction|horloge/i.test(e.category) && e.verified !== false && (e.year || 0) >= nowYear - 1 && (e.year || 0) <= nowYear + 0.05)
      .map(e => ({ e, t: effTs(e) }))
      .sort((a, b) => b.t - a.t)
      .slice(0, 30)
      .map(x => x.e);
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
  const fmtTs = e => {
    const d = effTs(e);
    if (d.getMonth() === 0 && d.getDate() === 1 && d.getHours() === 0 && d.getMinutes() === 0 && Math.abs(d.getFullYear() - (e.year || 0)) < 1) return String(Math.floor(e.year));
    return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  // géométrie du trait bulle de survol -> point
  const hb = hover ? { bx: Math.min(hover.x + 16, (wrapRef.current?.clientWidth || 800) - 280), by: Math.max(hover.y - 46, 8) } : null;
  const line = hover && hb ? (() => {
    const dx = hover.x - hb.bx, dy = hover.y - hb.by;
    return { w: Math.hypot(dx, dy), r: Math.atan2(dy, dx) };
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
          <div className="flex items-center gap-1 flex-wrap">
            <Filter size={12} className="text-zinc-500" />
            {cats.map(c => (
              <span key={c} className={`chip ${filters[c] === false ? 'opacity-40' : 'on'}`} onClick={() => setFilters(f => ({ ...f, [c]: f[c] === false ? true : false }))}>{c}</span>
            ))}
          </div>
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
              <div style={{ position: 'absolute', left: hb.bx, top: hb.by, width: line.w, height: 1,
                background: hover.ev.groupColor, boxShadow: `0 0 6px ${hover.ev.groupColor}`,
                transform: `rotate(${line.r}rad)`, transformOrigin: 'left center', pointerEvents: 'none', zIndex: 30 }} />
              <div className="bubble absolute px-2.5 py-1.5 text-[10px] font-bold pointer-events-none z-40"
                   style={{ left: hb.bx, top: hb.by, borderColor: hover.ev.groupColor, color: hover.ev.groupColor, borderRadius: 12 }}>
                {hover.ev.title} <span className="text-zinc-500">({Math.floor(hover.ev.year)})</span>
              </div>
            </>
          )}
        </div>
      </section>

      {/* popup détail façon V1 (box centrée, couleur de la courbe, liens ⇄) */}
      {selected && (
        <div className="fixed inset-0 z-[5000] flex items-center justify-center bg-black/60" onClick={() => setSelected(null)}>
          <div className="bubble relative w-[90%] max-w-[600px] max-h-[82vh] overflow-y-auto p-6"
               style={{ borderColor: selected.groupColor, boxShadow: `0 0 40px ${selected.groupColor}33` }}
               onClick={e => e.stopPropagation()}>
            <button onClick={() => setSelected(null)} className="absolute top-3 right-3 text-zinc-500 hover:text-white text-2xl leading-none"><X size={18} /></button>
            <h2 className="text-xl font-black uppercase pr-8" style={{ color: selected.groupColor }}>{selected.title}</h2>
            <div className="flex gap-4 text-[10px] text-zinc-500 uppercase mt-1 mb-3 border-b border-zinc-800 pb-2">
              <span>Source: <b className="text-zinc-300">{selected.source || 'N/A'}</b></span>
              <span>Date: <b className="text-zinc-300">{Math.floor(selected.year)}</b></span>
              <span>Catégorie: <b className="text-zinc-300">{selected.category}</b></span>
              <span>Impact: <b className="text-zinc-300">{selected.impact_score}</b></span>
            </div>
            {/* liens ⇄ prédit <-> réalisé */}
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
