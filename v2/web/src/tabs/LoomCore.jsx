import { useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Filter, Radio } from 'lucide-react';

// Onglet 1 — LOOM CORE : horloge apocalypse (compte à rebours lissé), filtres, J-curve ECharts (courbes + points), flux SSE
export default function LoomCore({ envelope, events, allEvents, filters, setFilters, clockSmooth }) {
  const chartRef = useRef(null);
  const wrapRef = useRef(null);
  const boxRef = useRef(null);
  const [selected, setSelected] = useState(null);
  const [hover, setHover] = useState(null);          // {x, y (px dans le wrap), ev}
  const [hiddenGroups, setHiddenGroups] = useState({});

  // ---- horloge de l'apocalypse : lissage glissant (paramètre onglet 4) ----
  const clockSeries = useMemo(() => {
    const cs = (allEvents || []).filter(e => e.doomsday_minutes != null).sort((a, b) => a.year - b.year);
    return cs.map(e => ({ year: e.year, seconds: Math.round(e.doomsday_minutes * 60), title: e.title }));
  }, [allEvents]);
  const smoothed = useMemo(() => {
    if (!clockSeries.length) return envelope.apocalypse_clock_seconds ?? 85;
    const w = Math.max(1, clockSmooth | 0);
    const tail = clockSeries.slice(-w).map(c => c.seconds);
    return Math.round(tail.reduce((a, b) => a + b, 0) / tail.length) || clockSeries[clockSeries.length - 1].seconds;
  }, [clockSeries, envelope.apocalypse_clock_seconds, clockSmooth]);

  const cats = useMemo(() => [...new Set((allEvents || []).map(e => e.category))], [allEvents]);

  // ---- groupes (pour légende pastilles colorées) ----
  const groups = useMemo(() => {
    const g = {};
    for (const e of events) g[e.group] = e.groupColor;
    return g;
  }, [events]);

  // ---- J-curve ECharts : scatter (points) + line (courbe en J lissée) par groupe ----
  useEffect(() => {
    if (!boxRef.current) return;
    const chart = echarts.init(boxRef.current, null, { renderer: 'canvas' });
    chartRef.current = chart;
    window.__loomChart = chart; // debug/tests

    const byGroup = {};
    for (const e of events) {
      if (hiddenGroups[e.group]) continue;
      (byGroup[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);
    }
    const series = [];
    for (const [name, g] of Object.entries(byGroup)) {
      const pts = g.data;
      // courbe en J (ligne lissée) — sous les points
      if (pts.length > 1) {
        series.push({
          name, type: 'line', smooth: 0.45, showSymbol: false, z: 1,
          lineStyle: { color: g.color, width: 1.5, opacity: 0.55 },
          areaStyle: { color: g.color, opacity: 0.05 },
          data: pts.map(e => [e.year, e.value]),
        });
      }
      // points
      series.push({
        name, type: 'scatter', z: 3,
        symbolSize: d => (d[3]?.tipping ? 11 : 6),
        itemStyle: { color: g.color, opacity: 0.95, borderColor: '#050508', borderWidth: 1 },
        emphasis: { scale: 1.6 },
        data: pts.map(e => [e.year, e.value, e.title, e]),
      });
    }

    chart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 600,
      tooltip: { show: false },   // bulle custom React (couleur courbe + trait vers le point)
      grid: { left: 50, right: 30, top: 40, bottom: 40 },
      xAxis: { type: 'value', min: -2700, max: 2110, axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' } },
      yAxis: { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
      series,
    }, { notMerge: true });

    chart.on('click', p => { if (p.data?.[3]) setSelected(p.data[3]); });
    // survol : picking manuel au pixel près (comme V1) — indépendant du type de série touché
    let raf = 0;
    const evsRef = { current: events };
    evsRef.current = events;
    chart.on('mousemove', e => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const zx = e.event.zrX ?? e.event.offsetX, zy = e.event.zrY ?? e.event.offsetY;
        let best = null, bd = 20 * 20; // seuil 20 px
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
    return () => { ro.disconnect(); chart.dispose(); chartRef.current = null; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, hiddenGroups]);

  // ---- flux entrant (SSE/poll, antichrono) ----
  const feed = useMemo(() => {
    return [...events].filter(e => e.timestamp).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 30);
  }, [events]);
  const fmtTs = e => {
    const d = new Date(e.timestamp);
    if (isNaN(d)) return String(Math.floor(e.year));
    if (d.getMonth() === 0 && d.getDate() === 1 && d.getHours() === 0 && d.getMinutes() === 0) return String(Math.floor(e.year));
    return d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
  };

  // géométrie du trait bulle -> point
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
          <Radio size={12} className="animate-pulse" /> FLUX ENTRANT · LIVE
        </div>
        <ul className="space-y-1.5">
          {feed.map(e => (
            <li key={e.id} className="text-[11px] leading-snug cursor-pointer hover:bg-cyan-500/10 rounded px-1 py-0.5"
                onClick={() => setSelected(e)} title={e.title}>
              <span style={{ color: e.groupColor }}>●</span>{' '}
              <span className="text-zinc-500">[{fmtTs(e)}]</span>{' '}
              {e.title}
            </li>
          ))}
        </ul>
      </aside>

      {/* zone centrale */}
      <section className="flex flex-col gap-3 min-h-0">
        {/* bandeau : horloge + filtres catégories */}
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

        {/* graphique J-curve + bulle de survol reliée au point */}
        <div ref={wrapRef} className="relative flex-1 min-h-0">
          <div ref={boxRef} className="panel absolute inset-0" />
          {hover && hb && (
            <>
              {/* trait bulle -> point */}
              <div style={{
                position: 'absolute', left: hb.bx, top: hb.by, width: line.w, height: 1,
                background: hover.ev.groupColor, boxShadow: `0 0 6px ${hover.ev.groupColor}`,
                transform: `rotate(${line.r}rad)`, transformOrigin: 'left center', pointerEvents: 'none', zIndex: 30,
              }} />
              {/* bulle */}
              <div className="bubble absolute px-2.5 py-1.5 text-[10px] font-bold pointer-events-none z-40"
                   style={{ left: hb.bx, top: hb.by, borderColor: hover.ev.groupColor, color: hover.ev.groupColor, borderRadius: 12 }}>
                {hover.ev.title} <span className="text-zinc-500">({Math.floor(hover.ev.year)})</span>
              </div>
            </>
          )}
        </div>

        {/* fiche événement sélectionné */}
        {selected && (
          <div className="bubble p-3 shrink-0 max-h-40 overflow-y-auto" style={{ borderColor: selected.groupColor }}>
            <div className="font-bold text-sm" style={{ color: selected.groupColor }}>{selected.title} <span className="text-zinc-500 text-xs">({Math.floor(selected.year)})</span></div>
            <div className="text-[10px] text-zinc-500">{selected.source} · {selected.category} · impact {selected.impact_score}</div>
            <p className="text-xs text-zinc-300 mt-1">{selected.description}</p>
          </div>
        )}
      </section>
    </div>
  );
}
