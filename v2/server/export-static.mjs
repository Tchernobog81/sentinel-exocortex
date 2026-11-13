// Export statique pour GitHub Pages : écrit telemetry.json + rag.json à la racine du repo.
// Appelé par la boucle agent (scripts/run_push_agent.sh) à chaque cycle -> la V2 statique
// sur https://tchernobog81.github.io/sentinel-exocortex/ affiche la télémétrie du nœud local.
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, telemetry, ragStatus } from './lib.mjs';

const tel = await telemetry();
// stamp du dernier cycle de veille : max(export maintenant, heartbeat POSTé par l'agent à chaque cycle)
// -> la MAJ du flux côté front progresse de 5 en 5 minutes même sans nouvel événement.
tel.last_scan = new Date().toISOString();
try {
  const hb = JSON.parse(fs.readFileSync(path.join(ROOT, 'scan_heartbeat.json'), 'utf8'));
  if (hb.last_scan && hb.last_scan > tel.last_scan) tel.last_scan = hb.last_scan;
} catch {}
const rag = ragStatus();
fs.writeFileSync(path.join(ROOT, 'telemetry.json'), JSON.stringify(tel));
fs.writeFileSync(path.join(ROOT, 'rag.json'), JSON.stringify(rag));
console.log(`telemetry.json + rag.json écrits (airgap=${tel.airgap}, mem=${tel.mem.pct}%, ollama=${tel.daemons.ollama.up}, rag docs=${rag.documents})`);
