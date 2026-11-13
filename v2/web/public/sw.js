// THE LOOM V2 — Service Worker (offline-first : CACHE FIRST + network fallback, mise à jour en fond)
const CACHE = 'loom-v2-8-1';
const PRECACHE = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './loom_data.json', './telemetry.json', './rag.json'];

self.addEventListener('install', (e) => {
  e.waitUntil((async () => {
    const c = await caches.open(CACHE);
    await Promise.all(PRECACHE.map(u => c.add(new Request(u, { cache: 'reload' })).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

const cleanUrl = (req) => {
  const u = new URL(req.url);
  u.search = '';
  return u.toString();
};

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || !req.url.startsWith(self.location.origin)) return;
  e.respondWith((async () => {
    const cached = await caches.match(req, { ignoreSearch: true });
    // fallback réseau mise à jour en FOND (l'app resteimmédiatement servie depuis le cache)
    const bg = fetch(req).then(async (res) => {
      if (res && res.ok) {
        const c = await caches.open(CACHE);
        const clone = res.clone();
        c.put(cleanUrl(req), clone).catch(() => {});
      }
      return res;
    }).catch(() => null);
    if (cached) { bg.catch(() => {}); return cached; }
    const fresh = await bg;
    if (fresh && fresh.ok) return fresh;
    // dernier recours : page racine pour les navigations
    if (req.mode === 'navigate') {
      const root = await caches.match('./index.html', { ignoreSearch: true });
      if (root) return root;
    }
    return fresh || Response.error();
  })());
});
