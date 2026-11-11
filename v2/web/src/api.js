// Hooks SSE — 100 % local (même origine), fallback polling si SSE indispo
import { useEffect, useRef, useState } from 'react';

export function useSSE(url, onMessage, pollMs = 5000) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;
  useEffect(() => {
    let es;
    try {
      es = new EventSource(url);
      es.onopen = () => setConnected(true);
      es.onmessage = (ev) => { try { const j = JSON.parse(ev.data); setData(j); onMessageRef.current?.(j); } catch {} };
      es.onerror = () => setConnected(false);
    } catch { setConnected(false); }
    const iv = setInterval(async () => {
      try { const r = await fetch(url.replace('/stream', '')); if (r.ok) { const j = await r.json(); setData(j); onMessageRef.current?.(j); setConnected(true); } } catch {}
    }, pollMs);
    return () => { es?.close(); clearInterval(iv); };
  }, [url]);
  return { data, connected };
}
