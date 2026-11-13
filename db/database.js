// db/database.js — Base hybride locale THE LOOM : SQLite (better-sqlite3) + vecteurs (sqlite-vec).
// - Table `events` : schéma relationnel demandé (champs normalisés) + colonnes métier Loom + `raw` (JSON complet, zéro perte).
// - Table virtuelle `vec_events` : embeddings 768 dims (Ollama local nomic-embed-text / embeddinggemma),
//   métrique cosinus, fallback gracieux (vecteur NULL) si Ollama est coupé.
// Source de vérité historique ; `loom_data.json` n'est plus qu'un EXPORT lissé (db/export_snapshot.js).
const path = require('node:path');
const fs = require('node:fs');
const Database = require('better-sqlite3');
const sqliteVec = require('sqlite-vec');

const ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(ROOT, 'data');
const DB_PATH = process.env.LOOM_DB || path.join(DATA_DIR, 'loom.db');
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://127.0.0.1:11434';
const EMBED_MODELS = (process.env.EMBED_MODEL || 'nomic-embed-text,embeddinggemma').split(',').map(s => s.trim()).filter(Boolean);
const EMBED_DIM = 768;

let _db = null;

function open() {
  if (_db) return _db;
  fs.mkdirSync(DATA_DIR, { recursive: true });
  const db = new Database(DB_PATH);
  db.pragma('journal_mode = WAL');
  db.pragma('foreign_keys = ON');
  sqliteVec.load(db);
  db.exec(`
    CREATE TABLE IF NOT EXISTS events (
      id TEXT PRIMARY KEY,
      date TEXT,
      year REAL,
      timestamp TEXT,
      category TEXT,
      title TEXT,
      source TEXT,
      source_url TEXT UNIQUE,
      is_kinetic_signal INTEGER DEFAULT 0,
      impact_score REAL DEFAULT 0,
      summary TEXT,
      pharmakon_remedy_percent INTEGER,
      pharmakon_poison_percent INTEGER,
      remedy_text TEXT,
      poison_text TEXT,
      s_curve_phase INTEGER,
      s_curve_label TEXT,
      convergences TEXT,
      grand_filter_analysis TEXT,
      final_note TEXT,
      apocalypse_clock_seconds INTEGER,
      singularity_index REAL,
      -- champs métier Loom conservés tels quels (zéro perte) :
      value INTEGER,
      tipping INTEGER DEFAULT 0,
      verified INTEGER,
      doomsday_minutes REAL,
      realYear REAL,
      realLabel TEXT,
      predictedBy TEXT,
      sources TEXT,
      occurrences INTEGER,
      merged_into TEXT,
      raw_clock_seconds TEXT,
      ema_clock_minutes REAL,
      related_ids TEXT,
      raw TEXT NOT NULL DEFAULT '{}',
      created_at TEXT DEFAULT (datetime('now')),
      updated_at TEXT DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_events_year ON events(year);
    CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);
    CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
    CREATE VIRTUAL TABLE IF NOT EXISTS vec_events USING vec0(
      embedding float[768] distance_metric=cosine,
      +event_id TEXT
    );
  `);
  _db = db;
  return db;
}

// ---- Embeddings locaux via Ollama (fallback gracieux : null si Ollama coupé / modèle absent) ----
async function embed(text) {
  const input = String(text || '').slice(0, 4000);
  if (!input.trim()) return null;
  for (const model of EMBED_MODELS) {
    for (const endpoint of ['/api/embed', '/api/embeddings']) {
      try {
        const ctl = new AbortController();
        const t = setTimeout(() => ctl.abort(), 15000);
        const body = endpoint === '/api/embed'
          ? { model, input }
          : { model, prompt: input };
        const r = await fetch(`${OLLAMA_URL}${endpoint}`, {
          method: 'POST', headers: { 'content-type': 'application/json' },
          body: JSON.stringify(body), signal: ctl.signal,
        });
        clearTimeout(t);
        if (!r.ok) continue;
        const j = await r.json();
        const vec = endpoint === '/api/embed' ? (j.embeddings || [])[0] : j.embedding;
        if (Array.isArray(vec) && vec.length === EMBED_DIM) return vec;
        if (Array.isArray(vec) && vec.length > EMBED_DIM) return vec.slice(0, EMBED_DIM);
      } catch { /* modèle/endpoint indisponible -> suivant */ }
    }
  }
  return null; // fallback gracieux : pas de vecteur, l'événement est quand même stocké
}

function vecToJson(vec) { return JSON.stringify(vec); }

// ---- Lecture / écriture ----
function rowToEvent(row) {
  let raw = {};
  try { raw = JSON.parse(row.raw || '{}'); } catch {}
  const e = {
    ...raw,
    id: row.id,
    date: row.date,
    year: row.year,
    timestamp: row.timestamp,
    category: row.category,
    label: raw.label ?? row.title,
    title: row.title,
    whoWhat: raw.whoWhat ?? row.source,
    source: row.source,
    url: raw.url ?? row.source_url,
    source_url: row.source_url,
    description: raw.description ?? row.summary,
    summary: row.summary,
    is_kinetic_signal: !!row.is_kinetic_signal,
    impact_score: row.impact_score,
    value: row.value,
    tipping: !!row.tipping,
    verified: row.verified == null ? undefined : !!row.verified,
    doomsday_minutes: row.doomsday_minutes,
    apocalypse_clock_seconds: row.apocalypse_clock_seconds,
    singularity_index: row.singularity_index,
    pharmakon_remedy_percent: row.pharmakon_remedy_percent,
    pharmakon_poison_percent: row.pharmakon_poison_percent,
    remedy_text: row.remedy_text,
    poison_text: row.poison_text,
    s_curve_phase: row.s_curve_phase,
    s_curve_label: row.s_curve_label,
    convergences: row.convergences,
    grand_filter_analysis: row.grand_filter_analysis,
    final_note: row.final_note,
    realYear: row.realYear,
    realLabel: row.realLabel,
    sources: row.sources ? JSON.parse(row.sources) : raw.sources,
    occurrences: row.occurrences ?? raw.occurrences,
    merged_into: row.merged_into ?? raw.merged_into,
    raw_clock_seconds: row.raw_clock_seconds ? JSON.parse(row.raw_clock_seconds) : raw.raw_clock_seconds,
    ema_clock_minutes: row.ema_clock_minutes,
    related_ids: row.related_ids ? JSON.parse(row.related_ids) : raw.related_ids,
  };
  return e;
}

function eventToRow(e) {
  const raw = { ...e };
  delete raw.title; delete raw.source; delete raw.source_url; delete raw.summary;
  return {
    id: e.id,
    date: e.date || (e.timestamp ? String(e.timestamp).slice(0, 10) : null),
    year: e.year ?? null,
    timestamp: e.timestamp || null,
    category: e.category || null,
    title: e.title || e.label || '',
    source: e.source || e.whoWhat || '',
    source_url: e.source_url || e.url || null,
    is_kinetic_signal: e.is_kinetic_signal ? 1 : 0,
    impact_score: e.impact_score ?? null,
    summary: e.summary || e.description || '',
    pharmakon_remedy_percent: e.pharmakon_remedy_percent ?? e.remedy_percent ?? null,
    pharmakon_poison_percent: e.pharmakon_poison_percent ?? e.poison_percent ?? null,
    remedy_text: e.remedy_text || null,
    poison_text: e.poison_text || null,
    s_curve_phase: e.s_curve_phase ?? null,
    s_curve_label: e.s_curve_label || null,
    convergences: e.convergences || null,
    grand_filter_analysis: e.grand_filter_analysis || null,
    final_note: e.final_note || null,
    apocalypse_clock_seconds: e.apocalypse_clock_seconds ?? null,
    singularity_index: e.singularity_index ?? null,
    value: e.value ?? null,
    tipping: e.tipping ? 1 : 0,
    verified: e.verified == null ? null : (e.verified ? 1 : 0),
    doomsday_minutes: e.doomsday_minutes ?? null,
    realYear: e.realYear ?? null,
    realLabel: e.realLabel ?? null,
    predictedBy: Array.isArray(e.predictedBy) ? JSON.stringify(e.predictedBy) : null,
    sources: Array.isArray(e.sources) ? JSON.stringify(e.sources) : null,
    occurrences: e.occurrences ?? null,
    merged_into: e.merged_into ?? null,
    raw_clock_seconds: e.raw_clock_seconds ? JSON.stringify(e.raw_clock_seconds) : null,
    ema_clock_minutes: e.ema_clock_minutes ?? null,
    related_ids: Array.isArray(e.related_ids) ? JSON.stringify(e.related_ids) : null,
    raw: JSON.stringify(raw),
  };
}

// ON CONFLICT(id) uniquement : un conflit source_url ne doit JAMAIS supprimer une autre ligne
// (INSERT OR REPLACE le faisait). La source_url en conflit est nullifiée, l'originale reste dans raw.
const insertStmt = () => open().prepare(`
  INSERT INTO events (
    id, date, year, timestamp, category, title, source, source_url, is_kinetic_signal, impact_score,
    summary, pharmakon_remedy_percent, pharmakon_poison_percent, remedy_text, poison_text,
    s_curve_phase, s_curve_label, convergences, grand_filter_analysis, final_note,
    apocalypse_clock_seconds, singularity_index, value, tipping, verified, doomsday_minutes,
    realYear, realLabel, predictedBy, sources, occurrences, merged_into, raw_clock_seconds,
    ema_clock_minutes, related_ids, raw, updated_at
  ) VALUES (
    @id, @date, @year, @timestamp, @category, @title, @source, @source_url, @is_kinetic_signal, @impact_score,
    @summary, @pharmakon_remedy_percent, @pharmakon_poison_percent, @remedy_text, @poison_text,
    @s_curve_phase, @s_curve_label, @convergences, @grand_filter_analysis, @final_note,
    @apocalypse_clock_seconds, @singularity_index, @value, @tipping, @verified, @doomsday_minutes,
    @realYear, @realLabel, @predictedBy, @sources, @occurrences, @merged_into, @raw_clock_seconds,
    @ema_clock_minutes, @related_ids, @raw, datetime('now')
  )
  ON CONFLICT(id) DO UPDATE SET
    date=excluded.date, year=excluded.year, timestamp=excluded.timestamp, category=excluded.category,
    title=excluded.title, source=excluded.source, source_url=excluded.source_url,
    is_kinetic_signal=excluded.is_kinetic_signal, impact_score=excluded.impact_score, summary=excluded.summary,
    pharmakon_remedy_percent=excluded.pharmakon_remedy_percent, pharmakon_poison_percent=excluded.pharmakon_poison_percent,
    remedy_text=excluded.remedy_text, poison_text=excluded.poison_text, s_curve_phase=excluded.s_curve_phase,
    s_curve_label=excluded.s_curve_label, convergences=excluded.convergences,
    grand_filter_analysis=excluded.grand_filter_analysis, final_note=excluded.final_note,
    apocalypse_clock_seconds=excluded.apocalypse_clock_seconds, singularity_index=excluded.singularity_index,
    value=excluded.value, tipping=excluded.tipping, verified=excluded.verified, doomsday_minutes=excluded.doomsday_minutes,
    realYear=excluded.realYear, realLabel=excluded.realLabel, predictedBy=excluded.predictedBy,
    sources=excluded.sources, occurrences=excluded.occurrences, merged_into=excluded.merged_into,
    raw_clock_seconds=excluded.raw_clock_seconds, ema_clock_minutes=excluded.ema_clock_minutes,
    related_ids=excluded.related_ids, raw=excluded.raw, updated_at=datetime('now')`);

async function upsertEvent(e, { embedIt = true } = {}) {
  const db = open();
  const row = eventToRow(e);
  const existing = row.source_url
    ? db.prepare('SELECT id FROM events WHERE source_url = ? AND id != ?').get(row.source_url, row.id)
    : db.prepare('SELECT id FROM events WHERE id = ?').get(row.id);
  const strictDup = existing ? existing.id : null;
  if (strictDup && row.source_url) row.source_url = null; // garde l'unicité par id ; l'URL d'origine reste dans raw
  db.prepare('BEGIN').run();
  try {
    insertStmt().run(row);
    if (embedIt) {
      const vec = await embed(`${row.title}\n${row.summary || ''}`);
      db.prepare('DELETE FROM vec_events WHERE event_id = ?').run(row.id);
      if (vec) db.prepare('INSERT INTO vec_events(event_id, embedding) VALUES (?, ?)').run(row.id, vecToJson(vec));
    }
    db.prepare('COMMIT').run();
  } catch (err) {
    db.prepare('ROLLBACK').run();
    throw err;
  }
  return { id: row.id, strictDup };
}

// Recherche sémantique KNN (cosine). Retourne [{event_id, similarity}] triés par similarité desc.
function semanticSearch(vec, { limit = 10, sinceDays = null, excludeId = null } = {}) {
  if (!vec) return [];
  const db = open();
  let sql = 'SELECT event_id, distance FROM vec_events WHERE embedding MATCH ? ORDER BY distance LIMIT ?';
  const rows = db.prepare(sql).all(vecToJson(vec), limit + 5);
  const out = [];
  for (const r of rows) {
    if (excludeId && r.event_id === excludeId) continue;
    const similarity = 1 - r.distance; // distance cosinus
    if (sinceDays != null) {
      const ev = db.prepare('SELECT timestamp FROM events WHERE id = ?').get(r.event_id);
      if (!ev || !ev.timestamp) continue;
      const age = (Date.now() - new Date(ev.timestamp).getTime()) / 86400000;
      if (age > sinceDays) continue;
    }
    out.push({ event_id: r.event_id, similarity });
    if (out.length >= limit) break;
  }
  return out;
}

function getEvent(id) {
  const row = open().prepare('SELECT * FROM events WHERE id = ?').get(id);
  return row ? rowToEvent(row) : null;
}

function findBySourceUrl(url) {
  if (!url) return null;
  const row = open().prepare('SELECT * FROM events WHERE source_url = ?').get(url);
  return row ? rowToEvent(row) : null;
}

function allEvents() {
  return open().prepare('SELECT * FROM events ORDER BY year').all().map(rowToEvent);
}

function counts() {
  const db = open();
  const events = db.prepare('SELECT COUNT(*) c FROM events').get().c;
  const vecs = db.prepare('SELECT COUNT(*) c FROM vec_events').get().c;
  return { events, vectors: vecs, dbPath: DB_PATH };
}

// Ajoute une source à un événement existant (occurrence multi-source) sans créer de doublon.
function addSource(eventId, sourceEntry) {
  const db = open();
  const ev = getEvent(eventId);
  if (!ev) return null;
  const sources = Array.isArray(ev.sources) ? ev.sources : [];
  if (ev.whoWhat && !sources.some(s => s.source === ev.whoWhat)) {
    sources.unshift({ source: ev.whoWhat, url: ev.url || '', title: ev.label || '' });
  }
  if (sourceEntry && (sourceEntry.source || sourceEntry.url) &&
      !sources.some(s => (s.url && s.url === sourceEntry.url) || (!sourceEntry.url && s.title === sourceEntry.title))) {
    sources.push(sourceEntry);
  }
  ev.sources = sources;
  ev.occurrences = sources.length;
  if (sourceEntry.verified) ev.verified = true;
  upsertEventSync(ev);
  return ev;
}

function upsertEventSync(e) {
  insertStmt().run(eventToRow(e));
}

module.exports = {
  ROOT, DB_PATH, EMBED_DIM, OLLAMA_URL,
  open, embed, upsertEvent, upsertEventSync, semanticSearch,
  getEvent, findBySourceUrl, allEvents, counts, addSource, rowToEvent, eventToRow,
};
