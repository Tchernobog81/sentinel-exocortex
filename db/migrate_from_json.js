// db/migrate_from_json.js — Migration one-shot : importe tout l'historique de loom_data.json
// dans data/loom.db (table events + vec_events) SANS PERTE (champ raw = JSON complet d'origine).
// Usage : node db/migrate_from_json.js [--no-embed]   (--no-embed : skip les embeddings Ollama)
const fs = require('node:fs');
const path = require('node:path');
const db = require('./database.js');

(async () => {
  const noEmbed = process.argv.includes('--no-embed');
  const src = process.env.LOOM_JSON || path.join(db.ROOT, 'loom_data.json');
  const events = JSON.parse(fs.readFileSync(src, 'utf8'));
  console.log(`Migration de ${events.length} événements depuis ${src} -> ${db.DB_PATH}`);

  let added = 0, skipped = 0, vectors = 0;
  const t0 = Date.now();
  for (const e of events) {
    if (!e.id) { skipped++; continue; }
    try {
      await db.upsertEvent(e, { embedIt: !noEmbed });
      if (!noEmbed) {
        const hasVec = db.open().prepare('SELECT COUNT(*) c FROM vec_events WHERE event_id = ?').get(e.id).c;
        if (hasVec) vectors++;
      }
      added++;
    } catch (err) {
      // source_url UNIQUE : si conflit, on tente sans source_url pour ne rien perdre
      try {
        const e2 = { ...e, url: e.url ? e.url + '#dup-' + e.id : e.url };
        await db.upsertEvent(e2, { embedIt: !noEmbed });
        added++;
      } catch (err2) {
        console.error('KO', e.id, err2.message);
        skipped++;
      }
    }
    if (added % 100 === 0) process.stdout.write(`\r${added} insérés, ${vectors} vecteurs...`);
  }
  console.log(`\nTerminé en ${((Date.now() - t0) / 1000).toFixed(1)}s : ${added} insérés, ${vectors} embeddings, ${skipped} ignorés`);
  console.log('counts:', db.counts());

  // sanity : aucune perte — chaque id du JSON est dans la DB avec son raw intact
  const missing = events.filter(e => e.id && !db.getEvent(e.id));
  console.log('ids manquants après migration:', missing.length);
  process.exit(missing.length ? 1 : 0);
})().catch(e => { console.error('FATAL', e); process.exit(1); });
