import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Radio, X, ArrowLeftRight } from 'lucide-react';

export const LOOM_VERSION = '2.4.0';

// ordonnée d'un événement : valeur tech (J-curve) ou secondes avant minuit pour l'horloge
const yOf = e => /horloge/i.test(e.group || '') ? Math.round((e.doomsday_minutes ?? 0) * 60) : (e.value ?? 0);
const axisOf = e => /horloge/i.test(e.group || '') ? 1 : 0;

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
  const [search, setSearch] = useState('');
  const [kineticOnly, setKineticOnly] = useState(false);
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
    for (const e of (allEvents || events)) g[e.group] = e.groupColor;
    return g;
  }, [allEvents, events]);

  // ---- INIT du chart : une seule fois (le zoom survit aux rafraîchissements) ----
  useEffect(() => {
    if (!boxRef.current || chartRef.current) return;
    const chart = echarts.init(boxRef.current, null, { renderer: 'canvas' });
    chartRef.current = chart;
    window.__loomChart = chart;

    const XMIN = -2700, XMAX = 2110;
    // V2.4.0 : vue initiale = PLAGE COMPLÈTE (comme V1) — l'asymptote exponentielle est réaliste
    // (plate pendant des millénaires, verticale à la fin) et les 9 courbes ne se superposent pas.
    // En ±60 ans autour d'aujourd'hui + Y-fit étiré, tout formait une diagonale régulière superposée.
    const start = 0, end = 100;
    let xWin = XMAX - XMIN;

    chart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 400,
      tooltip: { show: false },
      legend: { show: false },
      toolbox: { right: 12, top: 6, itemSize: 16, feature: { dataZoom: { xAxisIndex: 0, yAxisIndex: 'none', title: { zoom: 'Zoom', back: 'Reset zoom' } }, restore: { title: "Vue d'ensemble" } } },
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, zoomOnMouseWheel: true, moveOnMouseWheel: false, zoomOnMouseMove: false, start, end },
        { type: 'slider', xAxisIndex: 0, bottom: 2, height: 16, filterMode: 'none', start, end },
      ],
      grid: { left: 50, right: 30, top: 40, bottom: 34 },
      xAxis: { type: 'value', min: XMIN, max: XMAX, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' },
        // ligne pointillée verticale à la date du jour (comme V1) — sur l'axe, elle survit aux MAJ de séries
        markLine: {
          silent: true, symbol: 'none', z: 2,
          lineStyle: { color: '#fbbf24', type: 'dashed', width: 1.5, opacity: 0.85 },
          label: { color: '#fbbf24', fontSize: 9, position: 'insideEndTop', formatter: 'MAINTENANT' },
          data: [{ xAxis: nowYear }],
        },
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
        // axe caché pour l'horloge de l'apocalypse : échelle "secondes avant minuit", INVERSÉ
        // (moins de temps restant = plus haut = plus de danger) ; plage ajustée aux données (V2.3.0)
        { type: 'value', show: false, min: 0, max: 60 * 60 * 24, inverse: true },
      ],
      series: [],
    }, { notMerge: true });

    // clic -> popup détail : même picking au pixel près que le survol (le proxy
    // chart.on('click') ne se déclenche que sur un symbole exact)
    const pickNearest = (zx, zy) => {
      let best = null, bd = 24 * 24;
      for (const ev of eventsRef.current) {
        if (hiddenRef.current[ev.group]) continue;
        // chaque groupe sur SON axe : l'horloge vit sur l'axe caché 1 (V2.3.0 : ses POI étaient inpiquables)
        const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: axisOf(ev) }, [ev.year, yOf(ev)]);
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

    // survol : picking manuel au pixel près (seuil 24 px), branché sur ZRENDER
    // (chart.on('mousemove') ne se déclenche QUE sur un élément dessiné -> bulle fantôme)
    let raf = 0;
    chart.getZr().on('mousemove', e => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const zx = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
        const hit = pickNearest(zx, zy);
        if (hit) {
          const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: axisOf(hit) }, [hit.year, yOf(hit)]);
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
    for (const e of events) (byGroup[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);
    const series = [];
    // V2.3.0 : 2 séries par groupe, NOMS STABLES (groupe / groupe+' · prédictions') même quand le
    // groupe est masqué (data vide) — sinon le merge ECharts par nom conserve les anciennes séries
    // et la courbe reste affichée. Une seule série ligne par groupe (points+ligne+étiquettes) :
    // avant, line et scatter partageaient le même nom et ECharts fusionnait -> une seule ligne à l'écran.
    for (const [name, g] of Object.entries(byGroup)) {
      const hidden = !!hiddenGroups[name];
      const isClock = /horloge/i.test(name);
      const yIdx = isClock ? 1 : 0; // horloge sur axe caché inversé (le décollage J reste lisible)
      const pts = hidden ? [] : g.data;
      // courbe en J reliée (style V1) : points réels triés par année ; les prévisions restent des points
      const real = pts.filter(e => (e.year || 0) <= nowYear + 0.05).sort((a, b) => a.year - b.year);
      const future = pts.filter(e => (e.year || 0) > nowYear + 0.05).sort((a, b) => a.year - b.year);
      series.push({
        name, type: 'line', yAxisIndex: yIdx, z: 4,
        showSymbol: true, symbol: 'circle',
        symbolSize: d => (d[3]?.tipping ? 9 : 4),
        // segments quasi droits (hockey stick de Kurzweil : l'asymptote vient des données, pas du lissage)
        smooth: isClock ? 0.4 : 0.12, // l'horloge est adoucie (plus de zigzags verticaux agressifs)
        // V2.4.0 : un FIL fin semi-transparent (style V1 : width 1.5, alpha 0.7) — lisible en zone dense
        lineStyle: { color: g.color, width: 1.5, opacity: hidden ? 0 : 0.75, shadowColor: g.color, shadowBlur: 3 },
        itemStyle: { color: g.color, opacity: hidden ? 0 : 0.95, borderColor: '#050508', borderWidth: 1 },
        areaStyle: { color: g.color, opacity: 0.05 },
        emphasis: { scale: 1.7 },
        label: {
          show: true, position: 'top', fontSize: 9, color: '#cbd5e1',
          formatter: d => (d[3]?.tipping ? `${String(d[2]).slice(0, 18)}…` : ''),
          rotate: 28, distance: 6,
        },
        labelLayout: { hideOverlap: true },
        data: real.map(e => [e.year, yOf(e), e.title, e]),
      });
      series.push({
        name: name + ' · prédictions', type: 'scatter', yAxisIndex: yIdx, z: 3,
        symbol: 'diamond', symbolSize: 6,
        itemStyle: { color: g.color, opacity: hidden ? 0 : 0.55, borderColor: '#050508', borderWidth: 1 },
        data: future.map(e => [e.year, yOf(e), e.title, e]),
      });
    }
    // plage de l'axe caché de l'horloge ajustée aux secondes réelles (axe inversé : 0 s = tout en haut)
    const clockSecs = (allEvents || []).filter(e => /horloge/i.test(e.group || '') && e.doomsday_minutes != null)
      .map(e => Math.round(e.doomsday_minutes * 60));
    const clockMax = clockSecs.length ? Math.max(...clockSecs) : 3600;
    chart.setOption({ series, yAxis: [{}, { min: 0, max: Math.round(clockMax * 1.15) }] }, { lazyUpdate: true, notMerge: false });
    window.__fitY && window.__fitY();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, hiddenGroups, allEvents]);

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

  // ---- flux entrant : NOUVEAUTÉS récentes uniquement, antichronologique, DATES RÉELLES ----
  // V2.4.0 : le timestamp brut n'est fiable que s'il est cohérent avec l'année de l'événement ;
  // sinon c'est un horodatage d'INGESTION (ex: CPI 2002 stampé 11/11/2026) -> on dérive la date
  // honnêtement de l'année fractionnaire. Le flux n'affiche que les faits RÉCENTS (45 jours).
  const realDate = e => {
    const raw = new Date(e.timestamp);
    const y = e.year || 0, yi = Math.floor(y);
    if (!isNaN(raw.getTime()) && raw.getFullYear() > 0 && Math.abs(raw.getFullYear() - yi) <= 1) return raw;
    const frac = y - yi;
    return new Date(yi, Math.min(11, Math.floor(frac * 12)), 1 + Math.floor((frac * 12 % 1) * 28));
  };
  const tsCoherent = e => {
    const raw = new Date(e.timestamp);
    return !isNaN(raw.getTime()) && raw.getFullYear() > 0 && Math.abs(raw.getFullYear() - Math.floor(e.year || 0)) <= 1;
  };
  const feed = useMemo(() => {
    const now = new Date();
    const from = new Date(now.getTime() - 45 * 24 * 3600e3); // 45 derniers jours = vraies nouveautés
    const base = (allEvents || events)
      .filter(e => !/fiction|horloge/i.test(e.category || '') && e.verified !== false)
      .map(e => ({ e, t: realDate(e) }))
      .filter(x => !isNaN(x.t) && x.t >= from && x.t <= new Date(now.getTime() + 6 * 3600e3)) // pas d'annonces du futur
      .sort((a, b) => b.t - a.t); // antichronologique strict
    return base.slice(0, 60).map(x => x.e)
      .filter(e => (!kineticOnly || e.is_kinetic_signal) && (!search || (e.title || '').toLowerCase().includes(search.toLowerCase())));
  }, [allEvents, events, search, kineticOnly]);
  // dernière mise à jour = horodatage d'ingestion le plus récent parmi TOUS les événements (flux non filtré)
  const lastMaj = useMemo(() => {
    const now = new Date();
    let mx = null;
    for (const e of (allEvents || events)) {
      const d = new Date(e.timestamp);
      if (isNaN(d.getTime()) || d > now) continue;
      if (!mx || d > mx) mx = d;
    }
    if (!mx) return { txt: '--:--', full: '' };
    const dd = String(mx.getDate()).padStart(2, '0'), mm = String(mx.getMonth() + 1).padStart(2, '0');
    const hh = String(mx.getHours()).padStart(2, '0'), mi = String(mx.getMinutes()).padStart(2, '0');
    return { txt: `${dd}/${mm} ${hh}:${mi}`, full: `${dd}/${mm}/${mx.getFullYear()} ${hh}:${mi}:${String(mx.getSeconds()).padStart(2, '0')}` };
  }, [allEvents, events]);
  // date affichée = date RÉELLE de l'événement : JJ/MM/AAAA HH:MM si timestamp cohérent, sinon JJ/MM/AAAA dérivé
  const fmtTs = e => {
    const d = realDate(e);
    if (isNaN(d.getTime())) return String(Math.floor(e.year || 0));
    const dd = String(d.getDate()).padStart(2, '0'), mm = String(d.getMonth() + 1).padStart(2, '0'), yy = d.getFullYear();
    if (tsCoherent(e)) {
      const raw = new Date(e.timestamp);
      if (raw.getHours() !== 0 || raw.getMinutes() !== 0 || raw.getSeconds() !== 0)
        return `${dd}/${mm}/${yy} ${String(raw.getHours()).padStart(2, '0')}:${String(raw.getMinutes()).padStart(2, '0')}`;
    }
    return `${dd}/${mm}/${yy}`;
  };

  // bulle de survol + connecteur ORGANIQUE : la taille réelle de la bulle est mesurée (ref),
  // et le trait est une courbe de Bézier quadratique du POI vers le bord de la bulle le plus proche
  const bubbleRef = useRef(null);
  const [bubbleSize, setBubbleSize] = useState({ w: 240, h: 34 });
  useLayoutEffect(() => {
    if (bubbleRef.current) {
      const r = bubbleRef.current.getBoundingClientRect();
      setBubbleSize({ w: r.width, h: r.height });
    }
  }, [hover]);
  const hb = hover ? (() => {
    const wrapW = wrapRef.current?.clientWidth || 800;
    const above = hover.y > bubbleSize.h + 56; // bulle au-dessus, sinon en dessous du POI
    const by = above ? hover.y - bubbleSize.h - 26 : hover.y + 22;
    const bx = Math.max(4, Math.min(hover.x - bubbleSize.w / 2, wrapW - bubbleSize.w - 8));
    return { bx, by, above };
  })() : null;
  // ancre = centre du bord de la bulle tourné vers le POI ; la courbe plie latéralement (organique)
  const connector = hover && hb ? (() => {
    const ax = hb.bx + bubbleSize.w / 2;
    const ay = hb.above ? hb.by + bubbleSize.h : hb.by;
    const mx = (hover.x + ax) / 2, my = (hover.y + ay) / 2;
    const dx = ax - hover.x, dy = ay - hover.y;
    const len = Math.hypot(dx, dy) || 1;
    const bend = Math.min(28, len * 0.28);
    const cx = mx + (-dy / len) * bend, cy = my + (dx / len) * bend;
    return `M ${hover.x.toFixed(1)} ${hover.y.toFixed(1)} Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${ax.toFixed(1)} ${ay.toFixed(1)}`;
  })() : null;

  return (
    <div className="h-full grid grid-cols-[300px_1fr] gap-3 min-h-0">
      {/* panneau gauche : flux */}
      <aside className="panel p-3 overflow-y-auto min-h-0">
        <div className="flex items-center gap-2 text-neon-cyan text-[10px] tracking-widest mb-2"
             title={lastMaj.full ? `Dernière mise à jour : ${lastMaj.full}` : 'Aucune donnée datée'}>
          <Radio size={12} className="animate-pulse" /> FLUX ENTRANT · MAJ {lastMaj.txt}
        </div>
        {/* barre de recherche + filtre de gravité */}
        <div className="flex items-center gap-1.5 mb-2">
          <input value={search} onChange={ev => setSearch(ev.target.value)} placeholder="Rechercher dans le flux…"
                 className="flex-1 bg-transparent border border-cyan-500/30 rounded-md px-2 py-1 text-[10px] text-zinc-200 focus:border-cyan-400 focus:outline-none"
                 style={{ background: 'rgba(0,20,26,0.6)' }} />
          <span className={`chip ${kineticOnly ? 'on' : 'opacity-50'} shrink-0`} title="Signaux cinétiques uniquement"
                onClick={() => setKineticOnly(k => !k)}>⚡</span>
        </div>
        {feed.length === 0 && <div className="text-[11px] text-zinc-600 italic mb-2">Aucun fait récent — veille en pause.</div>}
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

        {/* légende custom : pastilles à la couleur des courbes — clic = allumage/extinction de LA courbe */}
        <div className="panel px-3 py-1.5 flex items-center gap-2 flex-wrap shrink-0">
          <span className="chip flex items-center gap-1.5" title="Tout allumer / tout éteindre (Singularité = toutes les courbes)"
                style={Object.keys(groups).every(g => !hiddenGroups[g]) ? { borderColor: '#fbbf24', color: '#fbbf24' } : { opacity: 0.4 }}
                onClick={() => {
                  const hideAll = Object.keys(groups).some(g => !hiddenGroups[g]);
                  setHiddenGroups(Object.fromEntries(Object.keys(groups).map(g => [g, hideAll])));
                }}>
            <span className="inline-block w-2.5 h-2.5 rounded-full"
                  style={{ background: 'conic-gradient(#fbbf24,#8b5cf6,#3b82f6,#0ea5e9,#10b981,#d946ef,#f97316,#f472b6,#ef4444,#fbbf24)', boxShadow: '0 0 6px #fbbf24' }} />
            ✦ SINGULARITÉ
          </span>
          {Object.entries(groups).map(([g, color]) => (
            <span key={g} className="chip flex items-center gap-1.5" title={`${hiddenGroups[g] ? 'Afficher' : 'Masquer'} la courbe ${g}`}
                  style={hiddenGroups[g] ? { opacity: 0.35 } : { borderColor: color, color }}
                  onClick={() => setHiddenGroups(h => ({ ...h, [g]: !h[g] }))}>
              <span style={{ background: color, boxShadow: `0 0 6px ${color}` }} className="inline-block w-2.5 h-2.5 rounded-full" /> {g}
            </span>
          ))}
        </div>

        {/* graphique + bulle de survol reliée au POI par une courbe organique */}
        <div ref={wrapRef} className="relative flex-1 min-h-0">
          <div ref={boxRef} className="panel absolute inset-0" />
          {hover && hb && connector && (
            <svg className="loom-connector absolute inset-0 pointer-events-none" style={{ zIndex: 30 }} width="100%" height="100%">
              <path d={connector} fill="none" stroke={hover.ev.groupColor} strokeWidth={1.6} strokeLinecap="round"
                    style={{ filter: `drop-shadow(0 0 5px ${hover.ev.groupColor})` }} />
              <circle cx={hover.x} cy={hover.y} r={3.5} fill={hover.ev.groupColor}
                      style={{ filter: `drop-shadow(0 0 6px ${hover.ev.groupColor})` }} />
            </svg>
          )}
          {hover && hb && (
            <div ref={bubbleRef} className="bubble absolute px-2.5 py-1.5 text-[10px] font-bold pointer-events-none z-40"
                 style={{ left: hb.bx, top: hb.by, borderColor: hover.ev.groupColor, color: hover.ev.groupColor, borderRadius: 12 }}>
              {hover.ev.title} <span className="text-zinc-500">({Math.floor(hover.ev.year)})</span>
            </div>
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
            <div className="flex gap-3 items-center flex-wrap text-[10px] text-zinc-500 uppercase mt-1 mb-2">
              <span>Source: <b className="text-zinc-300">{selected.source || 'N/A'}</b></span>
              <span className="font-mono">ID: <b className="text-zinc-400">{selected.id}</b></span>
              <span>Timestamp: <b className="text-zinc-400 font-mono">{new Date(selected.timestamp).toLocaleString('fr-FR')} ({new Date(selected.timestamp).toISOString().slice(0, 16)}Z)</b></span>
              <span className={`px-2 py-0.5 rounded border ${selected.is_kinetic_signal ? 'border-red-500/60 text-red-400' : 'border-zinc-700 text-zinc-500'}`}>
                {selected.is_kinetic_signal ? '⟡ IMPACT CINÉTIQUE : OUI' : 'IMPACT CINÉTIQUE : NON'}
              </span>
            </div>
            {/* Jauge Pharmakon : Remède | Poison */}
            <div className="mb-3">
              <div className="flex justify-between text-[9px] uppercase mb-0.5">
                <span className="text-emerald-400">Remède {selected.remedy ?? 50}%</span>
                <span className="text-red-400">Poison {selected.poison ?? 50}%</span>
              </div>
              <div className="flex h-3 rounded-full overflow-hidden border border-zinc-800">
                <div className="h-full bg-emerald-500" style={{ width: `${selected.remedy ?? 50}%` }} />
                <div className="h-full bg-red-500" style={{ width: `${selected.poison ?? 50}%` }} />
              </div>
            </div>
            {/* Position sur la courbe en S (1-5) */}
            <div className="flex items-center gap-2 text-[10px] text-zinc-500 uppercase mb-2">
              <span>Courbe en S :</span>
              <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map(n => (
                  <span key={n} className={`inline-block w-4 h-4 rounded text-center text-[9px] leading-4 border ${n === (selected.sCurve ?? 3) ? 'border-neon-cyan text-neon-cyan bg-cyan-500/20' : 'border-zinc-800 text-zinc-600'}`}>{n}</span>
                ))}
              </div>
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
            {/* Convergences & Grand Filtre + recommandation tactique NELA */}
            {/* Convergences & Grand Filtre + recommandation tactique NELA (toujours renseignés) */}
            <div className="mt-3 pt-2 border-t border-zinc-800 text-[11px] leading-relaxed">
              <div><b className="text-neon-cyan uppercase text-[9px]">Convergences :</b> <span className="text-zinc-400">{selected.convergences || `Convergence ${selected.category} — signal intégré à la J-curve (groupe ${selected.group}).`}</span></div>
              {selected.grandFilter && <div><b className="text-amber-400 uppercase text-[9px]">Grand Filtre :</b> <span className="text-zinc-400">{selected.grandFilter}</span></div>}
              <div className="mt-1 text-zinc-500"><b className="uppercase text-[9px]">Recommandation tactique NELA :</b> prioriser la veille sur « {selected.title.slice(0, 24)}… », corroboration 2+ sources, impact estimé {(selected.impact_score ?? 0) >= 0.5 ? 'élevé' : 'modéré'}.</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
