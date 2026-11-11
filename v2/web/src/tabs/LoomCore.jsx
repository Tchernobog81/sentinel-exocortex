import { useEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Filter, Radio } from 'lucide-react';

// Onglet 1 — LOOM CORE : horloge apocalypse (compte à rebours lissé), filtres, J-curve ECharts, flux SSE
export default function LoomCore({ envelope, events, allEvents, filters, setFilters, clockSmooth }) {
  const chartRef = useRef(null);
  const boxRef = useRef(null);
  const [selected, setSelected] = useState(null);

  // ---- horloge de l'apocalypse : lissage glissant (paramètre onglet 4) ----
  const clockSeries = useMemo(() => {
    const cs = (allEvents || []).filter(e => e.doomsday_minutes != null).sort((a, b) => a.year - b.year);
    return cs.map(e => ({ year: e.year, seconds: Math.round(e.doomsday_minutes * 60), title: e.title }));
  }, [allEvents]);
  const smoothed = useMemo(() => {
    if (!clockSeries.length) return envelope.apocalypse_clock_seconds ?? 85;
    const w = Math.max(1, clockSmooth | 0);
    const last = clockSeries[clockSeries.length - 1].seconds;
    const tail = clockSeries.slice(-w).map(c => c.seconds);
    return Math.round(tail.reduce((a, b) => a + b, 0) / tail.length) || last;
  }, [clockSeries, envelope.apocalypse_clock_seconds, clockSmooth]);

  const cats = useMemo(() => [...new Set((allEvents || []).map(e => e.category))], [allEvents]);

  // ---- J-curve ECharts ----
  useEffect(() => {
    if (!boxRef.current) return;
    const chart = echarts.init(boxRef.current, null, { renderer: 'canvas' });
    chartRef.current = chart;
    const groups = {};
    for (const e of events) {
      (groups[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);
    }
    const series = Object.entries(groups).map(([name, g]) => ({
      name,
      type: 'scatter',
      symbolSize: e => (e[3]?.tipping ? 11 : 6),
      itemStyle: { color: g.color, opacity: 0.9, borderColor: '#050508', borderWidth: 1 },
      emphasis: { scale: 1.6 },
      data: g.data.map(e => [e.year, e.value, e.title, e]),
      // ligne de tendance en J (exponentielle) par groupe
      ...(g.data.length > 1 ? [{
        name: name + ' · tendance',
        type: 'line',
        smooth: 0.4,
        showSymbol: false,
        lineStyle: { color: g.color, width: 1.5, opacity: 0.55 },
        data: g.data.map(e => [e.year, e.value]),
        z: 1,
      }] : []),
    })).flat();
    chart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 600,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(3,6,10,0.96)',
        borderColor: '#00f0ff',
        textStyle: { color: '#e5e7eb', fontSize: 11, fontFamily: 'ui-monospace, monospace' },
        formatter: p => `<b style="color:${p.color}">${p.value[2]}</b><br/>${p.value[0]} · impact ${p.value[3]?.impact_score ?? '—'}<br/><span style="color:#8b949e">${(p.value[3]?.description || '').slice(0, 140)}</span>`,
      },
      legend: { type: 'scroll', top: 0, textStyle: { color: '#9ca3af', fontSize: 10 }, icon: 'circle', itemWidth: 8, itemHeight: 8 },
      grid: { left: 50, right: 30, top: 40, bottom: 40 },
      xAxis: { type: 'value', min: -2700, max: 2110, axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' } },
      yAxis: { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
      series,
    });
    chart.on('click', p => { if (p.value?.[3]) setSelected(p.value[3]); });
    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(boxRef.current);
    return () => { ro.disconnect(); chart.dispose(); chartRef.current = null; };
  }, [events]);

  // ---- flux entrant (SSE, antichrono) ----
  const feed = useMemo(() => {
    return [...events].filter(e => e.timestamp).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)).slice(0, 30);
  }, [events]);

  return (
    <div className="h-full grid grid-cols-[300px_1fr] gap-3 min-h-0">
      {/* panneau gauche : flux */}
      <aside className="panel p-3 overflow-y-auto min-h-0">
        <div className="flex items-center gap-2 text-neon-cyan text-[10px] tracking-widest mb-2">
          <Radio size={12} className="animate-pulse" /> FLUX ENTRANT · SSE
        </div>
        <ul className="space-y-1.5">
          {feed.map(e => (
            <li key={e.id} className="text-[11px] leading-snug cursor-pointer hover:bg-cyan-500/10 rounded px-1 py-0.5"
                onClick={() => setSelected(e)} title={e.title}>
              <span style={{ color: e.groupColor }}>●</span>{' '}
              <span className="text-zinc-500">[{(() => { const d = new Date(e.timestamp); return isNaN(d) ? Math.floor(e.year) : d.toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); })()}]</span>{' '}
              {e.title}
            </li>
          ))}
        </ul>
      </aside>

      {/* zone centrale */}
      <section className="flex flex-col gap-3 min-h-0">
        {/* bandeau : horloge + filtres */}
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

        {/* graphique J-curve */}
        <div ref={boxRef} className="panel flex-1 min-h-0" />

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
