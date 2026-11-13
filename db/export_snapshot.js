// db/export_snapshot.js — Export lissé de la DB vers loom_data.json (PWA hors-ligne + GitHub Pages).
// Règles anti-zigzag sur la série Horloge de l'Apocalypse :
//   1) Time-bucketing : 1 point max par jour (GROUP BY date, valeur de clôture du jour),
//   2) Lissage EMA (alpha = 0.22) sur les valeurs récentes -> champ ema_clock_minutes,
//   3) Valeur brute exacte conservée dans raw_clock_seconds (pour le tooltip).
// Le frontend applique en plus smooth: 0.45 + smoothMonotone: 'x' (interpolation monotone ECharts).
// Écrit : <repo>/loom_data.json (Pages) et v2/web/public/loom_data.json (build PWA).
const fs = require('node:fs');
const path = require('node:path');
const db = require('./database.js');

const EMA_ALPHA = 0.22;

// Pour l'horloge, la date d'un réglage officiel se dérive de son ANNÉE (réglage annuel de janvier),
// pas du timestamp d'ingestion.
function clockDate(year) {
  const y = year ?? 2026;
  const yi = Math.floor(y);
  const frac = y - yi;
  const m = Math.min(11, Math.floor(frac * 12));
  const day = 1 + Math.floor(((frac * 12) % 1) * 28);
  return `${yi}-${String(m + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

function exportFromDb() {
  let events = db.allEvents();
  // --- Horloge : bucketing 1 point/jour (clôture) + EMA + raw conservé ---
  const clockEv = events.filter(e => /horloge/i.test(e.category || '') || e.doomsday_minutes != null)
    .sort((a, b) => (a.timestamp || '').localeCompare(b.timestamp || ''));
  if (clockEv.length) {
    const byDay = new Map(); // date -> { date, secs(close), raw[], e }
    for (const e of clockEv) {
      const d = clockDate(e.year);
      const secs = e.doomsday_minutes != null ? Math.round(e.doomsday_minutes * 60) : (e.apocalypse_clock_seconds ?? null);
      const prev = byDay.get(d);
      if (!prev) {
        byDay.set(d, { date: d, secs, raw: secs != null ? [secs] : [], e, timestamp: e.timestamp || `${d}T00:00:00` });
      } else {
        if (secs != null) prev.raw.push(secs);
        // clôture du jour = valeur du relevé le plus récent (par timestamp d'origine)
        if ((e.timestamp || '') >= (prev.timestamp || '')) { prev.secs = secs ?? prev.secs; prev.e = e; prev.timestamp = e.timestamp; }
      }
    }
    const days = [...byDay.values()].filter(x => x.secs != null).sort((a, b) => a.date < b.date ? -1 : 1);
    // EMA alpha=0.22 sur les clôtures journalières (chronologique)
    let ema = null;
    const clockOut = days.map(d => {
      ema = ema == null ? d.secs : EMA_ALPHA * d.secs + (1 - EMA_ALPHA) * ema;
      const y = parseInt(d.date.slice(0, 4), 10);
      return {
        ...d.e,
        id: d.e.id || `clock-${d.date}`,
        year: y + (new Date(d.date + 'T00:00:00Z').getUTCMonth() / 12),
        timestamp: d.timestamp || `${d.date}T00:00:00`,
        date: d.date,
        doomsday_minutes: Math.round((d.secs / 60) * 1000) / 1000, // clôture du jour
        apocalypse_clock_seconds: d.secs,
        ema_clock_minutes: Math.round((ema / 60) * 1000) / 1000,   // lissé EMA (alpha=0.22)
        raw_clock_seconds: d.raw.length ? d.raw : [d.secs],        // brut exact pour tooltip
      };
    });
    const originals = new Set(clockEv.map(e => e.id));
    events = events.filter(e => !originals.has(e.id)).concat(clockOut);
    events.sort((a, b) => (a.year || 0) - (b.year || 0));
  }
  return events;
}

function exportFromJsonFallback() {
  const p = path.join(db.ROOT, 'loom_data.json');
  if (!fs.existsSync(p)) return [];
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

(async () => {
  let events;
  try {
    const c = db.counts();
    events = c.events > 0 ? exportFromDb() : exportFromJsonFallback();
    console.log(`export depuis ${c.events > 0 ? 'loom.db' : 'loom_data.json (fallback)'} : ${events.length} événements`);
  } catch (e) {
    console.warn('DB indisponible, fallback JSON:', e.message);
    events = exportFromJsonFallback();
  }
  const json = JSON.stringify(events, null, 2);
  const targets = [
    path.join(db.ROOT, 'loom_data.json'),
    path.join(db.ROOT, 'v2', 'web', 'public', 'loom_data.json'),
  ];
  for (const t of targets) {
    fs.mkdirSync(path.dirname(t), { recursive: true });
    fs.writeFileSync(t, json);
    console.log('écrit:', path.relative(db.ROOT, t));
  }
  const clock = events.filter(e => e.doomsday_minutes != null);
  console.log(`horloge exportée: ${clock.length} points (bucket 1/jour, EMA alpha=${EMA_ALPHA}, raw_clock_seconds conservé)`);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
