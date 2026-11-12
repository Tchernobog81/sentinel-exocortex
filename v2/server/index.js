// THE LOOM V2 — serveur Fastify (air-gap : bind 127.0.0.1 uniquement)
import fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { ROOT, DATA_FILE, buildEnvelope, readEvents, telemetry, ragStatus, purgeVram } from './lib.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const WEB_DIST = path.resolve(__dirname, '..', 'web', 'dist');
const HOST = process.env.LOOM_HOST || '127.0.0.1';
const PORT = Number(process.env.LOOM_PORT || 8787);

const app = fastify({ logger: true });
// CORS : autorise la page Pages à appeler le serveur local (purge VRAM) en air-gap
app.addHook('onRequest', (req, reply, done) => {
  reply.header('Access-Control-Allow-Origin', '*');
  reply.header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  if (req.method === 'OPTIONS') { reply.code(204).send(); return; }
  done();
});

app.get('/api/data', async () => buildEnvelope());
app.get('/api/events', async () => readEvents());
app.get('/api/telemetry', async () => telemetry());
app.get('/api/rag', async () => ragStatus());
app.post('/api/purge', async () => { const r = await purgeVram(); app.log.info({ actions: r.actions }, 'PURGE VRAM'); return r; });

// Prompt de veille éditable depuis le dashboard (onglet FILTRE MÉMÉTIQUE) : le sentinel relit ce fichier à chaque cycle
const PROMPT_FILE = path.join(ROOT, 'agent_prompt.txt');
const DEFAULT_PROMPT = [
  '[PROMPT DE VEILLE — Sentinel Exocortex / The Loom]',
  'FOCUS STRICT : faits avérés sourcés liés à la singularité / course à l\'AGI (étude AI2027 en priorité),',
  'compute, autonomie des agents, modèles frontier (ARC-AGI), risques existentiels, cyber, espace, régulation.',
  'Corroborer 2+ sources. Un événement = une année RÉELLE. Ignorer les faits divers sans lien.',
  '',
  '[MOTS-CLÉS À EXCLURE]',
].join('\n');
app.get('/api/prompt', async () => {
  try { return { prompt: fs.readFileSync(PROMPT_FILE, 'utf8'), custom: true, path: 'agent_prompt.txt' }; }
  catch { return { prompt: DEFAULT_PROMPT, custom: false, path: 'agent_prompt.txt' }; }
});
app.post('/api/prompt', async (req) => {
  const p = (req.body && typeof req.body.prompt === 'string') ? req.body.prompt : '';
  try { fs.writeFileSync(PROMPT_FILE, p, 'utf8'); return { ok: true, path: 'agent_prompt.txt', chars: p.length }; }
  catch (e) { return { ok: false, error: String(e) }; }
});

// SSE — données (push à chaque changement du fichier)
app.get('/api/stream', async (req, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
  const send = () => reply.raw.write(`data: ${JSON.stringify(buildEnvelope())}\n\n`);
  send();
  const iv = setInterval(send, 15000);
  let timer = null;
  try {
    const watcher = fs.watch(DATA_FILE, () => { clearTimeout(timer); timer = setTimeout(send, 300); });
    req.raw.on('close', () => { clearInterval(iv); clearTimeout(timer); watcher.close(); });
  } catch { req.raw.on('close', () => clearInterval(iv)); }
});

// SSE — télémétrie toutes les 2 s
app.get('/api/telemetry/stream', async (req, reply) => {
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
  const send = async () => { try { reply.raw.write(`data: ${JSON.stringify(await telemetry())}\n\n`); } catch {} };
  await send();
  const iv = setInterval(send, 2000);
  req.raw.on('close', () => clearInterval(iv));
});

if (fs.existsSync(WEB_DIST)) {
  await app.register(fastifyStatic, { root: WEB_DIST, prefix: '/' });
  app.get('/', async (req, reply) => reply.sendFile('index.html'));
} else {
  app.get('/', async () => ({ ok: true, note: 'frontend non buildé — cd v2/web && npm install && npm run build' }));
}

app.listen({ host: HOST, port: PORT }).then(() => {
  app.log.info(`THE LOOM V2 — http://${HOST}:${PORT}  (air-gap, données: ${DATA_FILE})`);
});
