import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Radio, X, ArrowLeftRight } from 'lucide-react';

export const LOOM_VERSION = '2.5.0';

// V2.5.0 — LANES : chaque groupe a sa propre bande horizontale, normalisée sur ses propres
// min/max (les `value` brutes sont corrélées à l'année -> toutes les courbes s'alignaient sinon).
// La courbe ✦ SINGULARITÉ = synthèse (moyenne globale des valeurs par année), bande du haut.
const geomRef = { current: { laneOf: {}, normOf: {}, laneNames: [], nLanes: 1 } };
const rawVal = e => /horloge/i.test(e.group || '') ? Math.round((e.doomsday_minutes ?? 0) * 60) : (e.value ?? 0);
const yOf = e => {
  const g = geomRef.current;
  const lane = g.laneOf[e.group] ?? 0;
  const n = g.normOf[e.group] || { min: 0, max: 1 };
  const isClock = /horloge/i.test(e.group || '');
  let norm = n.max > n.min ? (rawVal(e) - n.min) / (n.max - n.min) : 0.5;
  if (isClock) norm = 1 - norm; // horloge : moins de secondes avant minuit = plus haut (danger)
  return lane + 0.08 + 0.84 * Math.max(0, Math.min(1, norm));
};
const laneY = (laneName, v, min, max) => {
  const g = geomRef.current;
  const lane = g.laneOf[laneName] ?? 0;
  const norm = max > min ? (v - min) / (max - min) : 0.5;
  return lane + 0.08 + 0.84 * Math.max(0, Math.min(1, norm));
};

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
      toolbox: { right: 40, top: 6, itemSize: 16, feature: { dataZoom: { xAxisIndex: 0, yAxisIndex: 'none', title: { zoom: 'Zoom', back: 'Reset zoom' } }, restore: { title: "Vue d'ensemble" } } },
      // V2.5.0 : manipulable horizontalement ET verticalement — molette = zoom X, Maj+molette = zoom Y,
      // drag = panoramique X+Y, sliders X (bas) et Y (droite)
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, yAxisIndex: 'none', zoomOnMouseWheel: true, moveOnMouseWheel: false, moveOnMouseMove: true, zoomOnMouseMove: false, start, end },
        { type: 'inside', xAxisIndex: 'none', yAxisIndex: 0, zoomOnMouseWheel: 'shift', moveOnMouseWheel: false, moveOnMouseMove: false, zoomOnMouseMove: false, start, end },
        { type: 'slider', xAxisIndex: 0, bottom: 2, height: 16, filterMode: 'none', start, end },
        { type: 'slider', yAxisIndex: 0, right: 4, width: 14, filterMode: 'none', start, end },
      ],
      grid: { left: 118, right: 40, top: 40, bottom: 34 },
      xAxis: { type: 'value', min: XMIN, max: XMAX, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' },
        // ligne pointillée verticale à la date du jour (comme V1) — sur l'axe, elle survit aux MAJ de séries
        markLine: {
          silent: true, symbol: 'none', z: 2,
          lineStyle: { color: '#fbbf24', type: 'dashed', width: 2, opacity: 0.95 },
          label: { color: '#fbbf24', fontSize: 9, position: 'insideStartTop', formatter: 'MAINTENANT', backgroundColor: 'rgba(9,13,22,0.85)', padding: [2, 5] },
          data: [{ xAxis: nowYear }],
        },
        axisLabel: {
          color: '#6b7280', fontSize: 10, hideOverlap: true,
          // zoom temporel : TOUTES les années -> TOUS les mois -> TOUS les jours (fenêtre relue à chaque formatage)
          formatter: v => {
            try {
              const dzs = chart.getOption().dataZoom || [];
              const dz = dzs.find(d => d.type === 'inside') || dzs[0];
              if (dz && dz.start != null) xWin = (XMAX - XMIN) * (dz.end - dz.start) / 100;
            } catch {}
            const range = xWin;
            const MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
            if (range > 24) return String(Math.floor(v));
            if (range > 2) { const y = Math.floor(v); const m = Math.max(0, Math.min(11, Math.floor((v - y) * 12))); return `${MOIS[m]} ${String(y).slice(2)}`; }
            const y = Math.floor(v), frac = v - y, d = new Date(y, 0, 1 + Math.floor(frac * 365));
            return `${String(d.getDate()).padStart(2, '0')}/${MOIS[d.getMonth()]}/${String(y).slice(2)}`;
          },
        } },
      // axe Y unique en LANES : une bande par groupe (noms affichés), synthèse ✦ SINGULARITÉ en haut
      yAxis: {
        type: 'value', splitNumber: 10, // un tick par lane -> tous les noms de catégories affichés
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.07)', type: 'dashed' } },
        axisLabel: {
          color: '#6b7280', fontSize: 8, interval: 0, hideOverlap: false,
          formatter: v => { const names = geomRef.current.laneNames; const i = Math.round(v); return (i >= 0 && i < names.length) ? names[i] : ''; },
        },
      },
      series: [],
    }, { notMerge: true });

    // clic -> popup détail : même picking au pixel près que le survol (le proxy
    // chart.on('click') ne se déclenche que sur un symbole exact). V2.5.0 : on ignore le clic
    // si c'était un drag (panoramique), sinon le drawer s'ouvre après chaque déplacement.
    const pickNearest = (zx, zy) => {
      let best = null, bd = 24 * 24;
      for (const ev of eventsRef.current) {
        if (hiddenRef.current[ev.group]) continue;
        // axe unique en lanes (V2.5.0) : tous les POI sont projetés avec yOf(ev)
        const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [ev.year, yOf(ev)]);
        const d = (px[0] - zx) ** 2 + (px[1] - zy) ** 2;
        if (d < bd) { bd = d; best = ev; }
      }
      return best;
    };
    let downX = 0, downY = 0, dragged = false;
    chart.getZr().on('mousedown', e => {
      downX = e.zrX ?? e.offsetX ?? 0; downY = e.zrY ?? e.offsetY ?? 0; dragged = false;
    });
    chart.getZr().on('click', e => {
      if (dragged) return; // c'était un panoramique, pas un clic
      const zx = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
      const hit = pickNearest(zx, zy);
      if (hit) setSelected(hit);
    });

    // survol : picking manuel au pixel près (seuil 24 px), branché sur ZRENDER
    // (chart.on('mousemove') ne se déclenche QUE sur un élément dessiné -> bulle fantôme)
    let raf = 0;
    chart.getZr().on('mousemove', e => {
      const zx0 = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy0 = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
      if (Math.hypot(zx0 - downX, zy0 - downY) > 6) dragged = true;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const hit = pickNearest(zx0, zy0);
        if (hit) {
          const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [hit.year, yOf(hit)]);
          setHover({ x: px[0], y: px[1], ev: hit });
        } else setHover(null);
      });
    });
    chart.getZr().on('globalout', () => setHover(null));
    chart.getDom().addEventListener('mouseleave', () => setHover(null));

    // fenêtre courante (années)
    const winRange = () => {
      try {
        const dzs = chart.getOption().dataZoom || [];
        const dz = dzs.find(d => d.type === 'inside' && d.xAxisIndex !== 'none') || dzs[0];
        if (dz && dz.start != null) return (XMAX - XMIN) * (dz.end - dz.start) / 100;
      } catch {}
      return XMAX - XMIN;
    };
    // ticks au fil du zoom : TOUTES les années -> TOUS les mois -> TOUS les jours
    const applyTickInterval = () => {
      const r = winRange();
      let minInterval;
      if (r > 24) minInterval = 1;        // toutes les années
      else if (r > 2) minInterval = 1 / 12; // tous les mois
      else minInterval = 1 / 365;           // tous les jours
      try { chart.setOption({ xAxis: { minInterval } }); } catch {}
    };
    let dzT = 0;
    chart.on('datazoom', () => {
      clearTimeout(dzT);
      dzT = setTimeout(() => { applyTickInterval(); }, 120);
    });
    window.__ticks = applyTickInterval;
    setTimeout(() => { applyTickInterval(); }, 250);

    const ro = new ResizeObserver(() => chart.resize());
    ro.observe(boxRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- MISE À JOUR des séries (préserve le zoom/pan utilisateur) ----
  const lastNLanesRef = useRef(0);
  useEffect(() => {
    eventsRef.current = events;
    hiddenRef.current = hiddenGroups;
    const chart = chartRef.current;
    if (!chart) return;
    const byGroup = {};
    for (const e of events) (byGroup[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);

    // V2.5.0 — géométrie des LANES : ordre stable des groupes + synthèse ✦ SINGULARITÉ en dernière bande
    const laneNames = Object.keys(byGroup).sort();
    laneNames.push('✦ SINGULARITÉ');
    const laneOf = {}; laneNames.forEach((n, i) => laneOf[n] = i);
    const normOf = {};
    for (const [name, g] of Object.entries(byGroup)) {
      const vals = g.data.map(e => rawVal(e)).filter(Number.isFinite);
      normOf[name] = vals.length ? { min: Math.min(...vals), max: Math.max(...vals) } : { min: 0, max: 1 };
    }
    // synthèse globale : moyenne des valeurs par année sur TOUS les événements
    const byYear = {};
    for (const e of events) { const y = Math.floor(e.year || 0); (byYear[y] ||= []).push(e.value ?? 0); }
    const synPts = Object.entries(byYear).map(([y, vals]) => ({ y: +y, v: vals.reduce((a, b) => a + b, 0) / vals.length })).sort((a, b) => a.y - b.y);
    // normalisation de la synthèse sur les années RÉELLES : la courbe occupe toute sa lane (vrai hockey stick)
    const synRealVals = synPts.filter(p => p.y <= nowYear + 0.05).map(p => p.v);
    const allVals = synRealVals.length ? synRealVals : synPts.map(p => p.v);
    normOf['✦ SINGULARITÉ'] = allVals.length ? { min: Math.min(...allVals), max: Math.max(...allVals) } : { min: 0, max: 1 };
    geomRef.current = { laneOf, normOf, laneNames, nLanes: laneNames.length };
    window.__geom = geomRef.current; // hook de test
    // fige l'axe Y (0..nLanes) seulement si le nombre de lanes change → le pan/zoom Y de l'utilisateur est préservé
    if (lastNLanesRef.current !== laneNames.length) {
      lastNLanesRef.current = laneNames.length;
      chart.setOption({ yAxis: { min: -0.05, max: laneNames.length + 0.05 } });
    }

    const series = [];
    // 2 séries par groupe, NOMS STABLES (même masqué → data vide, sinon le merge ECharts garde l'ancienne courbe)
    for (const [name, g] of Object.entries(byGroup)) {
      const hidden = !!hiddenGroups[name];
      const isClock = /horloge/i.test(name);
      const pts = hidden ? [] : g.data;
      // courbe reliée : points réels triés par année ; les prévisions restent des points (losanges)
      const real = pts.filter(e => (e.year || 0) <= nowYear + 0.05).sort((a, b) => a.year - b.year);
      const future = pts.filter(e => (e.year || 0) > nowYear + 0.05).sort((a, b) => a.year - b.year);
      series.push({
        name, type: 'line', z: 4,
        showSymbol: true, symbol: 'circle',
        symbolSize: d => (d[3]?.tipping ? 9 : 4),
        smooth: isClock ? 0.4 : 0.12, // horloge adoucie ; sinon segments quasi droits (hockey stick des données)
        lineStyle: { color: g.color, width: 1.5, opacity: hidden ? 0 : 0.75, shadowColor: g.color, shadowBlur: 3 },
        itemStyle: { color: g.color, opacity: hidden ? 0 : 0.95, borderColor: '#050508', borderWidth: 1 },
        areaStyle: { color: g.color, opacity: 0.05 },
        emphasis: { scale: 1.7 },
        label: { show: true, position: 'top', fontSize: 9, color: '#cbd5e1', formatter: d => (d[3]?.tipping ? `${String(d[2]).slice(0, 18)}…` : ''), rotate: 28, distance: 6 },
        labelLayout: { hideOverlap: true },
        data: real.map(e => [e.year, yOf(e), e.title, e]),
      });
      series.push({
        name: name + ' · prédictions', type: 'scatter', z: 3,
        symbol: 'diamond', symbolSize: 6,
        itemStyle: { color: g.color, opacity: hidden ? 0 : 0.55, borderColor: '#050508', borderWidth: 1 },
        data: future.map(e => [e.year, yOf(e), e.title, e]),
      });
    }
    // courbe de SYNTHÈSE ✦ SINGULARITÉ (bande du haut, blanche, plus épaisse) — le vrai hockey stick global
    const synReal = synPts.filter(p => p.y <= nowYear + 0.05);
    const synFut = synPts.filter(p => p.y > nowYear + 0.05);
    const synY = p => laneY('✦ SINGULARITÉ', p.v, normOf['✦ SINGULARITÉ'].min, normOf['✦ SINGULARITÉ'].max);
    if (synReal.length > 1) {
      series.push({
        name: '✦ SINGULARITÉ', type: 'line', z: 6,
        showSymbol: true, symbol: 'circle', symbolSize: 5, smooth: 0.15,
        lineStyle: { color: '#f8fafc', width: 2.5, opacity: 0.95, shadowColor: '#f8fafc', shadowBlur: 10 },
        itemStyle: { color: '#f8fafc', borderColor: '#050508', borderWidth: 1 },
        areaStyle: { color: '#f8fafc', opacity: 0.08 },
        data: synReal.map(p => [p.y, synY(p), `Singularité ${p.y}`, null]),
      });
    }
    if (synFut.length) {
      series.push({
        name: '✦ SINGULARITÉ · prédictions', type: 'scatter', z: 5,
        symbol: 'diamond', symbolSize: 6,
        itemStyle: { color: '#f8fafc', opacity: 0.6, borderColor: '#050508', borderWidth: 1 },
        data: synFut.map(p => [p.y, synY(p), `Singularité ${p.y}`, null]),
      });
    }
    chart.setOption({ series }, { lazyUpdate: true, notMerge: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, hiddenGroups, allEvents]);

  // ---- saut vers un événement (lien ⇄ ou flux) ----
  const jumpToEvent = (target) => {
    const chart = chartRef.current;
    if (chart && target?.year != null) {
      const xo = chart.getOption().xAxis;
      const xa = Array.isArray(xo) ? xo[0] : xo;
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
                onClick={() => jumpToEvent(e)}
                title={`Événement : ${fmtTs(e)} · ingéré le ${isNaN(new Date(e.timestamp).getTime()) ? '—' : new Date(e.timestamp).toLocaleString('fr-FR')}`}>
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
              <span>Événement : <b className="text-zinc-300">{fmtTs(selected)}</b></span>
              <span>Découvert/ingéré : <b className="text-zinc-400 font-mono">{isNaN(new Date(selected.timestamp).getTime()) ? '—' : new Date(selected.timestamp).toLocaleString('fr-FR')}</b></span>
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
