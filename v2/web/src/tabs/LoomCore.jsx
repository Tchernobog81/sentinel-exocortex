import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import * as echarts from 'echarts';
import { Clock3, Radio, X, ArrowLeftRight } from 'lucide-react';

export const LOOM_VERSION = '2.9.3';

// V2.8.0 — HORLOGE DE L'APOCALYPSE : time-bucketing X (1 pt/jour sur les 10 dernières années,
// 1 pt/mois depuis 1900, 1 pt/an avant, moyenne par bucket, tri strict) + EMA (alpha réglable,
// défaut 0.22) pour la ligne tracée (smooth 0.45 + smoothMonotone 'x') ; les marqueurs des
// réglages officiels sont projetés SUR la courbe lissée (alignés), les valeurs brutes restent
// dans le détail. Plus de dents de scie verticales.
// V2.7.0 — axe Y partagé, mais chaque catégorie a SA PROPRE COURBE : la donnée `value` étant
// corrélée à l'année (tous les POI s'alignaient strictement sur la synthèse), chaque catégorie
// est tracée en COURBE INDEXÉE : synthèse(year) × (part cumulée de la catégorie / part cumulée
// globale à cette année). Les catégories ont des formes réellement différentes (ex: FICTION
// ancienne -> au-dessus, IA récente -> en-dessous puis rattrape), enlacées autour de ✦ SINGULARITÉ
// avec laquelle elles convergent aujourd'hui (ratio = 1). L'horloge reste sur son axe caché inversé.
const synRef = { current: {} };   // année -> valeur moyenne globale (synthèse)
const clockEmaRef = { current: { pts: [], at: () => null } }; // courbe horloge EMA : pts [[x,y]...] + interpolation
const rRef = { current: {} };     // groupe -> { année -> ratio vs tendance globale }
const yOf = e => {
  if (/horloge/i.test(e.group || '')) {
    const at = clockEmaRef.current.at;
    const v = at ? at(e.year || 0) : null;
    return v ?? Math.round((e.doomsday_minutes ?? 0) * 60);
  }
  const yy = Math.floor(e.year || 0);
  const s = synRef.current[yy];
  if (s == null) return e.value ?? 0;
  const r = rRef.current[e.group]?.[yy] ?? 1;
  return s * r;
};
const axisOf = e => /horloge/i.test(e.group || '') ? 1 : 0;
const SYN_COLOR = '#f8fafc';
const XMIN = -2700, XMAX = 2110; // bornes de l'axe année (le futur, prévisions ~2100, reste navigable)

// Onglet 1 — LOOM CORE : le chart s'initialise UNE fois (le zoom utilisateur est préservé
// entre les rafraîchissements SSE), les séries sont mises à jour en douceur.
export default function LoomCore({ envelope, events, allEvents, filters, setFilters, clockSmooth, clockAlpha = 0.22, lastScan }) {
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
  const [nowPx, setNowPx] = useState(null); // position px de la ligne "jour courant" (surcouche HTML)
  const [vpWin, setVpWin] = useState({ x0: XMIN, x1: XMAX }); // fenêtre X visible (années) — pilote la densité des étiquettes (V2.9.3)
  const lastLabelW = useRef(0);
  window.__selectEvent = (ev) => setSelected(ev); // hook de test

  // V2.9.2 — viewport utilisateur persistant (indépendant des re-rendus / màj SSE / resize) :
  // { start, end } en % de l'axe X + hasUserInteracted. Tant que l'utilisateur n'a pas
  // zoomé/panné, la vue par défaut (0-100, "Aujourd'hui" visible) s'applique ; ensuite le
  // viewport est ré-appliqué après chaque setOption pour contrer tout reset interne d'ECharts.
  const userVpRef = useRef({ start: 0, end: 100, hasUserInteracted: false });
  const vpGuardRef = useRef(false); // true pendant un dispatch programmatique (évite de poser hasUserInteracted)
  const dragRef = useRef({ downX: 0, downY: 0, dragging: false, suppressClick: false });
  window.__userVp = userVpRef; // hook de test

  // V2.9.2 — reset UNIQUEMENT explicite (bouton "Aujourd'hui" ou double-clic dédié) :
  // retour à la vue par défaut zoom 1x (start 0, end 100).
  const resetViewport = () => {
    userVpRef.current = { start: 0, end: 100, hasUserInteracted: false };
    const chart = chartRef.current;
    if (!chart) return;
    vpGuardRef.current = true;
    chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 0, start: 0, end: 100 });
    chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 2, start: 0, end: 100 });
    setTimeout(() => { vpGuardRef.current = false; }, 60);
    window.__fitY && window.__fitY();
    window.__updateNow && window.__updateNow();
  };
  window.__resetVp = resetViewport; // hook de test

  const nowYear = new Date().getFullYear() + new Date().getMonth() / 12;

  // V2.8.2 : les occurrences médias regroupées dans un événement maître (mergedInto) sont masquées
  const allEvts = useMemo(() => (allEvents || events).filter(e => !e.mergedInto), [allEvents, events]);
  const evts = useMemo(() => events.filter(e => !e.mergedInto), [events]);

  // ---- horloge de l'apocalypse : lissage glissant (paramètre onglet 4) ----
  const clockSeries = useMemo(() => {
    return allEvts.filter(e => e.doomsday_minutes != null).sort((a, b) => a.year - b.year)
      .map(e => ({ year: e.year, seconds: Math.round(e.doomsday_minutes * 60) }));
  }, [allEvts]);
  const smoothed = useMemo(() => {
    if (!clockSeries.length) return envelope.apocalypse_clock_seconds ?? 85;
    const w = Math.max(1, clockSmooth | 0);
    const tail = clockSeries.slice(-w).map(c => c.seconds);
    return Math.round(tail.reduce((a, b) => a + b, 0) / tail.length) || clockSeries[clockSeries.length - 1].seconds;
  }, [clockSeries, envelope.apocalypse_clock_seconds, clockSmooth]);

  const groups = useMemo(() => {
    const g = {};
    for (const e of allEvts) g[e.group] = e.groupColor;
    return g;
  }, [allEvts]);

  // ---- INIT du chart : une seule fois (le zoom survit aux rafraîchissements) ----
  useEffect(() => {
    if (!boxRef.current || chartRef.current) return;
    const chart = echarts.init(boxRef.current, null, { renderer: 'canvas' });
    chartRef.current = chart;
    window.__loomChart = chart;

    // vue initiale = PLAGE COMPLÈTE (comme V1) — hockey stick réaliste
    const start = 0, end = 100;
    let xWin = XMAX - XMIN;

    chart.setOption({
      backgroundColor: 'transparent',
      animationDuration: 400,
      tooltip: { show: false },
      legend: { show: false },
      toolbox: { right: 40, top: 6, itemSize: 16, feature: { dataZoom: { xAxisIndex: 0, yAxisIndex: 'none', title: { zoom: 'Zoom', back: 'Reset zoom' } }, restore: { title: "Vue d'ensemble" } } },
      // manipulable horizontalement ET verticalement, et dans le futur :
      // molette = zoom X, Maj+molette = zoom Y, clic+move (drag) = panoramique X, sliders X (bas) et Y (droite)
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, yAxisIndex: 'none', zoomOnMouseWheel: true, moveOnMouseWheel: false, moveOnMouseMove: true, zoomOnMouseMove: false, filterMode: 'none', start, end },
        { type: 'inside', xAxisIndex: 'none', yAxisIndex: 0, zoomOnMouseWheel: 'shift', moveOnMouseWheel: false, moveOnMouseMove: false, zoomOnMouseMove: false, filterMode: 'none', start, end },
        { type: 'slider', xAxisIndex: 0, yAxisIndex: 'none', bottom: 2, height: 16, filterMode: 'none', start, end },
        { type: 'slider', xAxisIndex: 'none', yAxisIndex: 0, right: 4, width: 14, filterMode: 'none', start, end },
      ],
      grid: { left: 50, right: 40, top: 40, bottom: 34 },
      xAxis: { type: 'value', min: XMIN, max: XMAX, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, name: 'année', nameTextStyle: { color: '#6b7280' },
        axisLabel: {
          color: '#6b7280', fontSize: 10, hideOverlap: true,
          // zoom temporel : TOUTES les années -> TOUS les mois -> TOUS les jours (fenêtre relue à chaque formatage)
          formatter: v => {
            try {
              const dzs = chart.getOption().dataZoom || [];
              const dz = dzs.find(d => d.type === 'inside' && d.xAxisIndex !== 'none') || dzs[0];
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
      yAxis: [
        { type: 'value', axisLabel: { color: '#6b7280', fontSize: 10 }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } } },
        // axe caché de l'horloge : secondes avant minuit, INVERSÉ (moins = plus haut = danger)
        { type: 'value', show: false, min: 0, max: 60 * 60 * 24, inverse: true },
      ],
      series: [],
    }, { notMerge: true });

    // clic -> popup détail : picking au pixel près. On ignore le clic si c'était un drag (panoramique).
    const pickNearest = (zx, zy) => {
      let best = null, bd = 24 * 24;
      for (const ev of eventsRef.current) {
        if (hiddenRef.current[ev.group]) continue;
        const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: axisOf(ev) }, [ev.year, yOf(ev)]);
        const d = (px[0] - zx) ** 2 + (px[1] - zy) ** 2;
        if (d < bd) { bd = d; best = ev; }
      }
      return best;
    };
    // V2.9.2 — distinction stricte drag/clic : seuil 4 px entre mousedown et mouseup.
    // Un mouseleave/globalout pendant le drag termine proprement le glissement en CONSERVANT
    // la position courante (aucun reset du viewport).
    chart.getZr().on('mousedown', e => {
      dragRef.current = { downX: e.zrX ?? e.offsetX ?? 0, downY: e.zrY ?? e.offsetY ?? 0, dragging: false, suppressClick: false };
    });
    chart.getZr().on('mousemove', e => {
      const zx0 = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy0 = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
      if (Math.hypot(zx0 - dragRef.current.downX, zy0 - dragRef.current.downY) > 4) {
        dragRef.current.dragging = true; // > 4 px : c'est un pan, pas un clic
      }
      const { downX, downY } = dragRef.current;
      void downX; void downY;
      let raf = 0;
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const hit = pickNearest(zx0, zy0);
        if (hit) {
          const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: axisOf(hit) }, [hit.year, yOf(hit)]);
          setHover({ x: px[0], y: px[1], ev: hit });
        } else setHover(null);
      });
    });
    chart.getZr().on('mouseup', e => {
      const zx = e.zrX ?? e.offsetX ?? 0, zy = e.zrY ?? e.offsetY ?? 0;
      if (Math.hypot(zx - dragRef.current.downX, zy - dragRef.current.downY) > 4) {
        dragRef.current.suppressClick = true; // drag > 4 px : le click suivant est ignoré
      }
    });
    chart.getZr().on('click', e => {
      if (dragRef.current.dragging || dragRef.current.suppressClick) {
        dragRef.current.suppressClick = false;
        return; // c'était un panoramique (drag > 4 px), pas un clic
      }
      if ((e.event?.detail ?? 1) > 1) return; // 2e clic d'un double-clic : réservé au reset de la vue
      const zx = e.zrX ?? e.offsetX ?? (e.event && e.event.offsetX), zy = e.zrY ?? e.offsetY ?? (e.event && e.event.offsetY);
      const hit = pickNearest(zx, zy);
      if (hit) setSelected(hit);
    });
    const endDragClean = () => {
      // mouseleave / globalout pendant un drag : on garde la position courante, on ne reset rien
      dragRef.current.dragging = false;
      setHover(null);
    };
    chart.getZr().on('globalout', endDragClean);
    chart.getDom().addEventListener('mouseleave', endDragClean);

    // fenêtre courante (années)
    const xZoom = () => {
      const dzs = chart.getOption().dataZoom || [];
      return dzs.find(d => d.type === 'inside' && d.xAxisIndex !== 'none') || dzs[0];
    };
    const winRange = () => {
      try {
        const dz = xZoom();
        if (dz && dz.start != null) return (XMAX - XMIN) * (dz.end - dz.start) / 100;
      } catch {}
      return XMAX - XMIN;
    };
    // Y ajusté aux données réelles visibles dans la fenêtre X (comme V1 : le décollage reste visible)
    const fitYToWindow = () => {
      try {
        const dz = xZoom();
        const xa = chart.getOption().xAxis; const x = Array.isArray(xa) ? xa[0] : xa;
        const x0 = x.min + ((dz?.start ?? 0) / 100) * (x.max - x.min);
        const x1 = x.min + ((dz?.end ?? 100) / 100) * (x.max - x.min);
        let hi = 0, lo = Infinity;
        for (const ev of eventsRef.current) {
          if ((ev.year || 0) > nowYear + 0.05) continue;   // prévisions hors Y-fit
          if (/horloge/i.test(ev.group || '')) continue;   // horloge sur son propre axe
          if (hiddenRef.current[ev.group]) continue;
          if ((ev.year || 0) >= x0 && (ev.year || 0) <= x1) { const yy = yOf(ev); hi = Math.max(hi, yy); lo = Math.min(lo, yy); }
        }
        if (hi > 0) chart.setOption({ yAxis: [{ min: Math.max(0, Math.floor(lo * 0.9)), max: Math.round(hi * 1.05) }, {}] });
      } catch {}
    };
    // ticks au fil du zoom : TOUTES les années -> TOUS les mois -> TOUS les jours
    const applyTickInterval = () => {
      const r = winRange();
      let minInterval;
      if (r > 24) minInterval = 1;         // toutes les années
      else if (r > 2) minInterval = 1 / 12; // tous les mois
      else minInterval = 1 / 365;           // tous les jours
      try { chart.setOption({ xAxis: { minInterval } }); } catch {}
    };
    // surcouche HTML "MAINTENANT" : position px du jour courant, recalculée à chaque zoom/resize
    // (une markLine ECharts pouvait sembler "à 0" quand la fenêtre ne la contenait pas)
    const updateNowPx = () => {
      try {
        const dz = xZoom();
        const xa = chart.getOption().xAxis; const x = Array.isArray(xa) ? xa[0] : xa;
        const x0 = x.min + ((dz?.start ?? 0) / 100) * (x.max - x.min);
        const x1 = x.min + ((dz?.end ?? 100) / 100) * (x.max - x.min);
        if (nowYear < x0 || nowYear > x1) { setNowPx(null); return; }
        const px = chart.convertToPixel({ xAxisIndex: 0, yAxisIndex: 0 }, [nowYear, 0])[0];
        setNowPx(px);
      } catch { setNowPx(null); }
    };
    // V2.9.2 — persistance du viewport utilisateur : chaque datazoom met à jour userVpRef
    // (start/end en %) et pose hasUserInteracted. Clamping doux : on borne `start` dans
    // [0, 100 - w] sans jamais toucher à la largeur w (le niveau de zoom).
    const clampStart = (s, w) => Math.max(0, Math.min(100 - w, s));
    const applyUserViewport = () => {
      const vp = userVpRef.current;
      if (!vp.hasUserInteracted) return; // vue par défaut : on ne force rien
      const w = vp.end - vp.start;
      const s = clampStart(vp.start, w);
      const dz = xZoom();
      if (dz && (Math.abs(dz.start - s) > 0.01 || Math.abs(dz.end - (s + w)) > 0.01)) {
        vpGuardRef.current = true;
        chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 0, start: s, end: s + w });
        chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 2, start: s, end: s + w });
        setTimeout(() => { vpGuardRef.current = false; }, 60);
      }
    };
    window.__applyUserVp = applyUserViewport;
    let dzT = 0, lastXKey = null;
    chart.on('datazoom', () => {
      const dz = xZoom();
      if (dz && dz.start != null) {
        const w = dz.end - dz.start;
        const s = clampStart(dz.start, w);
        if (Math.abs(s - dz.start) > 1e-6) {
          // pan au-delà de la butée : on clamp sans toucher au zoom, puis on sort (pas de boucle)
          vpGuardRef.current = true;
          chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 0, start: s, end: s + w });
          chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: 2, start: s, end: s + w });
          setTimeout(() => { vpGuardRef.current = false; }, 60);
        }
        userVpRef.current.start = s;
        userVpRef.current.end = s + w;
        if (!vpGuardRef.current) userVpRef.current.hasUserInteracted = true; // 1er zoom/pan manuel
      }
      clearTimeout(dzT);
      dzT = setTimeout(() => {
        applyTickInterval();
        const d2 = xZoom();
        const key = d2 ? d2.start + '-' + d2.end : '';
        if (key !== lastXKey) { lastXKey = key; fitYToWindow(); } // Y-fit seulement si le zoom X a changé
        updateNowPx();
        // V2.9.3 : la fenêtre visible pilote la densité des étiquettes permanentes
        try {
          const xa = chart.getOption().xAxis; const x = Array.isArray(xa) ? xa[0] : xa;
          const n0 = x.min + ((d2?.start ?? 0) / 100) * (x.max - x.min);
          const n1 = x.min + ((d2?.end ?? 100) / 100) * (x.max - x.min);
          setVpWin(prev => (Math.abs(prev.x0 - n0) < 0.05 && Math.abs(prev.x1 - n1) < 0.05) ? prev : { x0: n0, x1: n1 });
        } catch {}
      }, 120);
    });
    window.__fitY = fitYToWindow;
    window.__updateNow = updateNowPx;
    window.__ticks = applyTickInterval;
    setTimeout(() => { applyTickInterval(); fitYToWindow(); updateNowPx(); }, 250);

    const ro = new ResizeObserver(() => {
      chart.resize();
      applyUserViewport(); // resize : on ré-applique le viewport utilisateur, jamais de reset
      updateNowPx();
      // V2.9.3 : la largeur change -> la densité des étiquettes (budget en px) est recalculée
      const w = boxRef.current ? boxRef.current.clientWidth : 0;
      if (Math.abs(w - lastLabelW.current) > 2) setVpWin(v => ({ x0: v.x0, x1: v.x1 }));
    });
    ro.observe(boxRef.current);

    // navigation clavier (accessibilité) : flèches = panoramique X (Maj = Y), +/- = zoom X
    const dom = chart.getDom();
    dom.tabIndex = 0;
    dom.addEventListener('keydown', ev => {
      const dzs = chart.getOption().dataZoom;
      const ix = dzs.findIndex(d => d.type === 'inside' && d.xAxisIndex !== 'none');
      const iy = dzs.findIndex(d => d.type === 'inside' && d.yAxisIndex !== 'none');
      if (ix < 0) return;
      const step = ev.shiftKey ? 10 : 3;
      const pan = (idx, dir) => {
        const d = dzs[idx]; const w = d.end - d.start;
        const s = Math.max(0, Math.min(100 - w, d.start + dir * step));
        chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: idx, start: s, end: s + w });
      };
      const zoom = (dir) => {
        const d = dzs[ix]; const mid = (d.start + d.end) / 2; const half = Math.max(1, (d.end - d.start) / 2 * (dir > 0 ? 1 / 1.25 : 1.25));
        chart.dispatchAction({ type: 'dataZoom', dataZoomIndex: ix, start: Math.max(0, Math.min(100, mid - half)), end: Math.max(0, Math.min(100, mid + half)) });
      };
      if (ev.key === 'ArrowLeft') { pan(ix, -1); ev.preventDefault(); }
      else if (ev.key === 'ArrowRight') { pan(ix, 1); ev.preventDefault(); }
      else if (ev.key === 'ArrowUp') { if (iy >= 0) { pan(iy, 1); ev.preventDefault(); } }
      else if (ev.key === 'ArrowDown') { if (iy >= 0) { pan(iy, -1); ev.preventDefault(); } }
      else if (ev.key === '+' || ev.key === '=') { zoom(1); ev.preventDefault(); }
      else if (ev.key === '-') { zoom(-1); ev.preventDefault(); }
    });
    dom.addEventListener('dblclick', resetViewport); // V2.9.2 : double-clic dédié = reset de la vue (zoom 1x)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---- MISE À JOUR des séries (préserve le zoom/pan utilisateur) ----
  useEffect(() => {
    eventsRef.current = evts;
    hiddenRef.current = hiddenGroups;
    const chart = chartRef.current;
    if (!chart) return;
    const byGroup = {};
    for (const e of evts) (byGroup[e.group] ||= { color: e.groupColor, data: [] }).data.push(e);

    // V2.7.0 : carte de la synthèse (moyenne par année, hors horloge) -> synRef, utilisée par yOf
    const byYear = {};
    for (const e of allEvts) {
      if (/horloge/i.test(e.group || '')) continue;
      const y = Math.floor(e.year || 0); (byYear[y] ||= []).push(e.value ?? 0);
    }
    const synMap = {}; const synPts = [];
    for (const [y, vals] of Object.entries(byYear)) {
      const v = vals.reduce((a, b) => a + b, 0) / vals.length;
      synMap[y] = v; synPts.push({ y: +y, v });
    }
    synPts.sort((a, b) => a.y - b.y);
    synRef.current = synMap;
    // courbes indexées par catégorie : ratio = (part cumulée cat / total cat) / (part cumulée globale / total global)
    const nonClock = allEvts.filter(e => !/horloge/i.test(e.group || '')).sort((a, b) => (a.year || 0) - (b.year || 0));
    const totalAll = nonClock.length || 1;
    const cumAll = {}; const totG = {}; const cumG = {};
    let acc = 0;
    for (const e of nonClock) {
      acc++;
      const y = Math.floor(e.year || 0);
      cumAll[y] = acc;
      totG[e.group] = (totG[e.group] || 0) + 1;
      (cumG[e.group] ||= {})[y] = (cumG[e.group][y] || 0) + 1;
    }
    // cumuls "jusqu'à l'année y" (reconstruction par balayage des années présentes)
    const rMap = {};
    for (const g of Object.keys(totG)) {
      rMap[g] = {};
      let cg = 0; const keys = Object.keys(byYear).map(Number).sort((a, b) => a - b);
      for (const y of keys) { cg += (cumG[g][y] || 0); const ca = cumAll[y] || 0; const denom = ca / totalAll; rMap[g][y] = denom > 0 ? Math.max(0.55, Math.min(1.8, (cg / totG[g]) / denom)) : 1; }
    }
    rRef.current = rMap;
    // V2.8.0 — horloge : time-bucketing X (1 pt/jour si année >= now-10, 1 pt/mois si >= 1900,
    // 1 pt/an sinon ; moyenne des secondes par bucket ; tri strict croissant) puis EMA
    // ema[i] = alpha*y[i] + (1-alpha)*ema[i-1] — la ligne tracée = EMA, les valeurs brutes
    // restent dans les POI/tooltip. Aucun pixel X ne contient plusieurs Y empilés.
    const clockEv = allEvts.filter(e => /horloge/i.test(e.group || '') && e.doomsday_minutes != null).sort((a, b) => (a.year || 0) - (b.year || 0));
    const buckets = new Map();
    for (const e of clockEv) {
      const y = e.year || 0;
      const key = y >= nowYear - 10 ? 'd' + Math.floor(y * 365.25)
                : y >= 1900 ? 'm' + Math.floor(y * 12)
                : 'y' + Math.floor(y);
      const b = buckets.get(key) || { sx: 0, sy: 0, n: 0 };
      b.sx += y; b.sy += Math.round(e.doomsday_minutes * 60); b.n++;
      buckets.set(key, b);
    }
    const rawPts = [...buckets.values()].map(b => ({ x: b.sx / b.n, y: b.sy / b.n })).sort((a, b) => a.x - b.x);
    const alpha = Math.min(0.95, Math.max(0.05, Number(clockAlpha) || 0.22));
    const emaPts = [];
    for (let i = 0; i < rawPts.length; i++) {
      const y = i === 0 ? rawPts[i].y : alpha * rawPts[i].y + (1 - alpha) * emaPts[i - 1].y;
      emaPts.push({ x: rawPts[i].x, y });
    }
    const emaAt = (x) => {
      const pts = emaPts;
      if (!pts.length) return null;
      if (x <= pts[0].x) return pts[0].y;
      const last = pts[pts.length - 1];
      if (x >= last.x) return last.y;
      for (let i = 1; i < pts.length; i++) {
        if (x <= pts[i].x) {
          const t = (x - pts[i - 1].x) / ((pts[i].x - pts[i - 1].x) || 1);
          return pts[i - 1].y + t * (pts[i].y - pts[i - 1].y);
        }
      }
      return last.y;
    };
    clockEmaRef.current = { pts: emaPts, at: emaAt };
    window.__clockDebug = { raw: rawPts, ema: emaPts, alpha }; // hook de test headless

    // V2.9.3 — étiquettes permanentes des POI principaux, densité intelligente :
    // sélection gloutonne par impact décroissant avec un écart minimal exprimé en PIXELS
    // (donc adapté au zoom courant et à la largeur réelle du canvas), plafond global + par
    // groupe ; labelLayout.hideOverlap reste en garde-fou final. Recalculé à chaque
    // changement de fenêtre visible (zoom/pan via vpWin) ou de largeur (resize).
    const winYears = Math.max(0.01, vpWin.x1 - vpWin.x0);
    const wpx = boxRef.current?.clientWidth || 1200;
    lastLabelW.current = wpx;
    const pxPerYear = wpx / winYears;
    const minGapYears = 70 / Math.max(1e-6, pxPerYear);          // ~70 px entre deux étiquettes
    const totalCap = Math.max(8, Math.min(48, Math.floor(wpx / 70)));
    const gNames = Object.keys(groups).filter(g => !hiddenGroups[g] && !/horloge/i.test(g));
    const perGroupCap = Math.max(2, Math.ceil(totalCap / Math.max(1, gNames.length)));
    const cand = evts
      .filter(e => gNames.includes(e.group) && (e.tipping || (e.impact_score ?? 0) >= 0.85) && (e.year || 0) >= vpWin.x0 && (e.year || 0) <= vpWin.x1)
      .sort((a, b) => ((b.impact_score ?? 0) - (a.impact_score ?? 0)) || ((b.year || 0) - (a.year || 0)));
    const picked = []; const perG = {};
    for (const e of cand) {
      if (picked.length >= totalCap) break;
      if ((perG[e.group] || 0) >= perGroupCap) continue;
      if (picked.every(p => Math.abs((p.year || 0) - (e.year || 0)) >= minGapYears)) { picked.push(e); perG[e.group] = (perG[e.group] || 0) + 1; }
    }
    const labeled = new Set(picked.map(e => e.id));
    window.__labeled = labeled; // hook de test headless

    // V2.6.0 : noms de séries STABLES issus de allEvents (même si le filtre mémétique vide un groupe,
    // la série existe -> le clic sur sa pastille allume/éteint toujours quelque chose)
    const series = [];
    for (const name of Object.keys(groups)) {
      const g = byGroup[name] || { color: groups[name], data: [] };
      const hidden = !!hiddenGroups[name];
      const isClock = /horloge/i.test(name);
      const yIdx = isClock ? 1 : 0;
      if (isClock) {
        // V2.8.0 : la ligne = courbe EMA bucketée avec interpolation monotone (smooth 0.45 +
        // smoothMonotone 'x', aucun dépassement) ; les marqueurs des réglages officiels sont
        // projetés SUR la courbe lissée via emaAt -> alignés, plus de zigzags verticaux.
        series.push({
          name, type: 'line', yAxisIndex: 1, z: 4,
          showSymbol: false,
          smooth: 0.45, smoothMonotone: 'x',
          lineStyle: { color: g.color, width: 2, opacity: hidden ? 0 : 0.9, shadowColor: g.color, shadowBlur: 4 },
          itemStyle: { color: g.color },
          areaStyle: { color: g.color, opacity: 0.06 },
          data: hidden ? [] : emaPts.map(p => [p.x, p.y, `⏰ ${Math.floor(p.x)} (lissé)`, null]),
        });
        series.push({
          name: name + ' · réglages', type: 'scatter', yAxisIndex: 1, z: 5,
          showSymbol: true, symbol: 'circle',
          symbolSize: d => (d[3]?.tipping ? 9 : 5),
          itemStyle: { color: g.color, opacity: hidden ? 0 : 0.95, borderColor: '#050508', borderWidth: 1 },
          emphasis: { scale: 1.7 },
          // V2.9.3 : étiquette à la couleur de la courbe, lisible (bord sombre) — réglages officiels
          label: { show: true, position: 'top', distance: 5, fontSize: 9, fontWeight: 'bold', color: g.color, textBorderColor: 'rgba(9,13,22,0.95)', textBorderWidth: 3, formatter: d => (d[3]?.tipping ? `${String(d[2]).slice(0, 20)}…` : '') },
          labelLayout: { hideOverlap: true },
          data: hidden ? [] : clockEv.map(e => [e.year, emaAt(e.year), e.title, e]),
        });
        continue;
      }
      const pts = hidden ? [] : g.data;
      // courbe reliée : points réels triés par année ; les prévisions restent des points (losanges), futur navigable
      const real = pts.filter(e => (e.year || 0) <= nowYear + 0.05).sort((a, b) => a.year - b.year);
      const future = pts.filter(e => (e.year || 0) > nowYear + 0.05).sort((a, b) => a.year - b.year);
      series.push({
        name, type: 'line', yAxisIndex: yIdx, z: 4,
        showSymbol: true, symbol: 'circle',
        symbolSize: d => { const ev = d[3]; if (!ev) return 4; if (labeled.has(ev.id)) return 9; return ev.tipping ? 7 : 4; },
        smooth: isClock ? 0.35 : 0.12, // horloge lissée (moyenne mobile + smooth) ; sinon segments quasi droits (hockey stick)
        lineStyle: { color: g.color, width: 1.5, opacity: hidden ? 0 : 0.75, shadowColor: g.color, shadowBlur: 3 },
        itemStyle: { color: g.color, opacity: hidden ? 0 : 0.95, borderColor: '#050508', borderWidth: 1 },
        areaStyle: { color: g.color, opacity: 0.05 },
        emphasis: { scale: 1.7 },
        // V2.9.3 : étiquette permanente JOINDTE au POI principal (position top, distance 5),
        // à la couleur de la courbe, lisible grâce au bord sombre ; show au niveau item.
        label: { show: false, position: 'top', distance: 5, fontSize: 9, fontWeight: 'bold', color: g.color,
                 textBorderColor: 'rgba(9,13,22,0.95)', textBorderWidth: 3,
                 formatter: d => { const t = String(d[2] || ''); return t.length > 24 ? t.slice(0, 24) + '…' : t; } },
        labelLayout: { hideOverlap: true },
        data: real.map(e => labeled.has(e.id)
          ? { value: [e.year, yOf(e), e.title, e], label: { show: true } }
          : [e.year, yOf(e), e.title, e]),
      });
      series.push({
        name: name + ' · prédictions', type: 'scatter', yAxisIndex: yIdx, z: 3,
        symbol: 'diamond', symbolSize: 6,
        itemStyle: { color: g.color, opacity: hidden ? 0 : 0.55, borderColor: '#050508', borderWidth: 1 },
        data: future.map(e => [e.year, yOf(e), e.title, e]),
      });
    }
    // courbe de SYNTHÈSE ✦ SINGULARITÉ : moyenne globale par année (synPts calculé ci-dessus),
    // axe partagé, blanche et plus épaisse — les courbes de catégories s'enlacent autour en la croisant
    const synReal = synPts.filter(p => p.y <= nowYear + 0.05);
    const synFut = synPts.filter(p => p.y > nowYear + 0.05);
    if (synReal.length > 1) {
      series.push({
        name: '✦ SINGULARITÉ', type: 'line', z: 6,
        showSymbol: true, symbol: 'circle', symbolSize: 5, smooth: 0.15,
        lineStyle: { color: SYN_COLOR, width: 2.5, opacity: 0.95, shadowColor: SYN_COLOR, shadowBlur: 10 },
        itemStyle: { color: SYN_COLOR, borderColor: '#050508', borderWidth: 1 },
        areaStyle: { color: SYN_COLOR, opacity: 0.08 },
        data: synReal.map(p => [p.y, p.v, `Singularité ${p.y}`, null]),
      });
    }
    if (synFut.length) {
      series.push({
        name: '✦ SINGULARITÉ · prédictions', type: 'scatter', z: 5,
        symbol: 'diamond', symbolSize: 6,
        itemStyle: { color: SYN_COLOR, opacity: 0.6, borderColor: '#050508', borderWidth: 1 },
        data: synFut.map(p => [p.y, p.v, `Singularité ${p.y}`, null]),
      });
    }
    // plage de l'axe caché de l'horloge ajustée aux secondes réelles
    const clockSecs = allEvts.filter(e => /horloge/i.test(e.group || '') && e.doomsday_minutes != null)
      .map(e => Math.round(e.doomsday_minutes * 60));
    const clockMax = clockSecs.length ? Math.max(...clockSecs) : 3600;
    chart.setOption({ series, yAxis: [{}, { min: 0, max: Math.round(clockMax * 1.15) }] }, { lazyUpdate: true, notMerge: false });
    // V2.9.2 : après une màj des séries (SSE/refresh), on ré-applique le viewport utilisateur
    // au lieu de laisser la vue se réinitialiser sur "Aujourd'hui".
    window.__applyUserVp && window.__applyUserVp();
    window.__fitY && window.__fitY();
    window.__updateNow && window.__updateNow();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [evts, hiddenGroups, allEvts, groups, clockAlpha, vpWin]);

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
    const cands = allEvts.filter(e => e.title === label);
    if (!cands.length) return;
    const target = yearHint != null
      ? cands.slice().sort((a, b) => Math.abs((a.year || 0) - yearHint) - Math.abs((b.year || 0) - yearHint))[0]
      : (cands.find(e => e.realYear || e.predictedBy?.length) || cands[0]);
    jumpToEvent(target);
  };

  // ---- flux entrant : NOUVEAUTÉS récentes uniquement, antichronologique, DATES RÉELLES ----
  // le timestamp brut n'est fiable que s'il est cohérent avec l'année de l'événement ;
  // sinon c'est un horodatage d'INGESTION -> on dérive la date de l'année fractionnaire.
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
    const base = allEvts
      .filter(e => !/fiction|horloge/i.test(e.category || '') && e.verified !== false)
      .map(e => ({ e, t: realDate(e) }))
      .filter(x => !isNaN(x.t) && x.t >= from && x.t <= new Date(now.getTime() + 6 * 3600e3)) // pas d'annonces du futur
      .sort((a, b) => b.t - a.t); // antichronologique strict
    return base.slice(0, 60).map(x => x.e)
      .filter(e => (!kineticOnly || e.is_kinetic_signal) && (!search || (e.title || '').toLowerCase().includes(search.toLowerCase())));
  }, [allEvts, search, kineticOnly]);
  // dernière mise à jour = max(horodatage d'ingestion le plus récent parmi TOUS les événements,
  // last_scan de la boucle de veille ~5 min) — le flux avance à chaque cycle même sans nouvel événement
  const lastMaj = useMemo(() => {
    const now = new Date();
    let mx = null;
    for (const e of allEvts) {
      const d = new Date(e.timestamp);
      if (isNaN(d.getTime()) || d > now) continue;
      if (!mx || d > mx) mx = d;
    }
    if (lastScan) {
      const d = new Date(lastScan);
      if (!isNaN(d.getTime()) && d <= new Date(now.getTime() + 6 * 3600e3) && (!mx || d > mx)) mx = d;
    }
    if (!mx) return { txt: '--:--', full: '' };
    const dd = String(mx.getDate()).padStart(2, '0'), mm = String(mx.getMonth() + 1).padStart(2, '0');
    const hh = String(mx.getHours()).padStart(2, '0'), mi = String(mx.getMinutes()).padStart(2, '0');
    return { txt: `${dd}/${mm} ${hh}:${mi}`, full: `${dd}/${mm}/${mx.getFullYear()} ${hh}:${mi}:${String(mx.getSeconds()).padStart(2, '0')}` };
  }, [allEvts, lastScan]);
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

  const allVisible = Object.keys(groups).every(g => !hiddenGroups[g]);

  return (
    <div className="h-full grid grid-cols-[300px_1fr] gap-3 min-h-0">
      {/* panneau gauche : flux */}
      <aside className="panel p-3 overflow-y-auto min-h-0">
        <div className="flex items-center gap-2 text-neon-cyan text-[10px] tracking-widest mb-2"
             title={lastMaj.full ? `Dernière mise à jour : ${lastMaj.full}` : 'Aucune donnée datée'}>
          <Radio size={12} className="animate-pulse" /> FLUX ENTRANT · MAJ {lastMaj.txt}
        </div>
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
              {e.occurrences > 1 && <span className="text-zinc-600"> · {e.occurrences} sources</span>}
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
          <button className="chip flex items-center gap-1 ml-auto" style={{ cursor: 'pointer' }}
                  title="Réinitialiser la vue : plage complète, zoom 1x (double-clic sur le graphique aussi)"
                  onClick={resetViewport}>
            <ArrowLeftRight size={11} /> ⟲ Aujourd'hui
          </button>
        </div>

        {/* légende : pastilles à la couleur des courbes (Singularité = blanche comme sa courbe) — clic = on/off */}
        <div className="panel px-3 py-1.5 flex items-center gap-2 flex-wrap shrink-0">
          <span className="chip flex items-center gap-1.5" title="Tout allumer / tout éteindre (Singularité = toutes les courbes)"
                style={allVisible ? { borderColor: SYN_COLOR, color: SYN_COLOR } : { opacity: 0.4, borderColor: SYN_COLOR, color: SYN_COLOR }}
                onClick={() => {
                  const hideAll = Object.keys(groups).some(g => !hiddenGroups[g]);
                  setHiddenGroups(Object.fromEntries(Object.keys(groups).map(g => [g, hideAll])));
                }}>
            <span className="inline-block w-2.5 h-2.5 rounded-full"
                  style={{ background: SYN_COLOR, boxShadow: `0 0 6px ${SYN_COLOR}` }} />
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

        {/* graphique + ligne "jour courant" + bulle de survol reliée au POI par une courbe organique */}
        <div ref={wrapRef} className="relative flex-1 min-h-0">
          <div ref={boxRef} className="panel absolute inset-0" />
          {nowPx != null && (
            <div className="loom-nowline absolute top-0 bottom-0 pointer-events-none" style={{ left: nowPx, zIndex: 20, borderLeft: '2px dashed #fbbf24', opacity: 0.9 }}>
              <span className="absolute top-1 left-0 -translate-x-1/2 text-[9px] font-bold px-1 rounded whitespace-nowrap"
                    style={{ color: '#fbbf24', background: 'rgba(9,13,22,0.85)' }}>MAINTENANT</span>
            </div>
          )}
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
            {/* Occurrences médias regroupées dans cet événement (V2.8.2) */}
            {Array.isArray(selected.sources) && selected.sources.length > 1 && (
              <div className="mb-3">
                <div className="text-[9px] uppercase text-zinc-500 mb-1">Occurrences médias regroupées ({selected.sources.length})</div>
                <ul className="text-[10px] space-y-0.5 max-h-28 overflow-y-auto">
                  {selected.sources.map((s, i) => (
                    <li key={i} className="truncate">
                      {s.url
                        ? <a href={s.url} target="_blank" rel="noreferrer" className="text-neon-cyan hover:underline">{s.source || s.url}</a>
                        : <span className="text-zinc-400">{s.source || '—'}</span>}
                      {s.title && <span className="text-zinc-600"> — {s.title.slice(0, 90)}</span>}
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
