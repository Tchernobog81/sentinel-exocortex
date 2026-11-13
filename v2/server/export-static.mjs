// Export statique pour GitHub Pages : écrit telemetry.json + rag.json à la racine du repo.
// Appelé par la boucle agent (scripts/run_push_agent.sh) à chaque cycle -> la V2 statique
// sur https://tchernobog81.github.io/sentinel-exocortex/ affiche la télémétrie du nœud local.
import fs from 'node:fs';
import path from 'node:path';
import { ROOT, telemetry, ragStatus } from './lib.mjs';

const tel = await telemetry();
// stamp du dernier cycle de veille : la MAJ du flux côté front = max(dernier événement, last_scan)
tel.last_scan = new Date().toISOString();
const rag = ragStatus();
fs.writeFileSync(path.join(ROOT, 'telemetry.json'), JSON.stringify(tel));
fs.writeFileSync(path.join(ROOT, 'rag.json'), JSON.stringify(rag));
console.log(`telemetry.json + rag.json écrits (airgap=${tel.airgap}, mem=${tel.mem.pct}%, ollama=${tel.daemons.ollama.up}, rag docs=${rag.documents})`);
