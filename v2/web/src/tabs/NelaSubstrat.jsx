import { useEffect, useRef } from 'react';
import * as echarts from 'echarts';
import { Cpu, MemoryStick, Thermometer, Gauge, Wifi, WifiOff, Server } from 'lucide-react';

// Onglet 2 — NELA SUBSTRAT : santé du nœud local (jauges RAM/VRAM/temp, joules/action, air-gap, démons)
export default function NelaSubstrat({ tel }) {
  const ramRef = useRef(null), vramRef = useRef(null), tempRef = useRef(null);
  const refs = { ram: ramRef, vram: vramRef, temp: tempRef };
  const charts = useRef({});

  useEffect(() => {
    for (const [k, ref] of Object.entries(refs)) {
      if (ref.current && !charts.current[k]) {
        charts.current[k] = echarts.init(ref.current, null, { renderer: 'canvas' });
        charts.current[k].setOption(gaugeOption(k === 'temp' ? 'TEMP CPU' : k === 'vram' ? 'VRAM GPU' : 'RAM', 0, k === 'temp' ? 100 : 100, '%'));
      }
    }
    return () => {};
  }, []);

  useEffect(() => {
    if (!tel) return;
    const set = (k, val, max, unit) => {
      const c = charts.current[k]; if (!c) return;
      c.setOption(gaugeOption(k === 'temp' ? 'TEMP CPU °C' : k === 'vram' ? 'VRAM GPU' : 'RAM', val, max, unit));
    };
    set('ram', tel.mem?.pct ?? 0, 100, '%');
    set('vram', tel.gpu?.vram ? Math.round(((tel.gpu.vramUsed || 0) / tel.gpu.vram) * 100) : 0, 100, '%');
    set('temp', tel.cpu?.temp ?? 0, 100, '°C');
  }, [tel]);

  const d = tel?.daemons || {};
  return (
    <div className="h-full grid grid-cols-3 grid-rows-2 gap-3 min-h-0 overflow-y-auto">
      {/* jauges */}
      {['ram', 'vram', 'temp'].map(k => (
        <div key={k} className="panel p-3 flex flex-col">
          <div ref={refs[k]} className="flex-1 min-h-[120px]" />
        </div>
      ))}

      {/* joules par action */}
      <div className="panel p-3">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-2"><Gauge size={12} /> JOULES / ACTION (est.)</div>
        <div className={`text-3xl font-black ${tel?.joules_per_action_score === 'Critique' ? 'red-text' : tel?.joules_per_action_score === 'Élevé' ? 'amber-text' : 'text-neon-green'}`}>
          {tel?.joules_per_action ?? '—'} <span className="text-xs">J/action</span>
        </div>
        <div className="text-[10px] text-zinc-500 mt-1">score: {tel?.joules_per_action_score ?? '—'} · moteur: <b>{tel?.active_engine ?? '—'}</b></div>
        <div className="text-[10px] text-zinc-600 mt-1">heuristique: charge CPU × taille modèles chargés</div>
      </div>

      {/* air-gap & ports */}
      <div className="panel p-3 overflow-y-auto">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-2">
          {tel?.airgap ? <WifiOff size={12} className="text-neon-green" /> : <Wifi size={12} className="red-text" />}
          AIR-GAP & AUDIT SOCKETS
        </div>
        <div className={`text-sm font-bold mb-1 ${tel?.airgap ? 'text-neon-green' : 'red-text'}`}>{tel?.airgap ? 'AIR-GAP ACTIF (loopback only)' : 'FUITE : écoute externe détectée'}</div>
        <ul className="text-[10px] text-zinc-400 space-y-0.5">
          {(tel?.open_ports || []).slice(0, 12).map((p, i) => <li key={i}><span className="text-neon-cyan">{p.addr}</span>:{p.port} <span className="text-zinc-600">{p.proto}{p.pid ? ` pid ${p.pid}` : ''}</span></li>)}
        </ul>
        {(tel?.external_listeners || []).length > 0 && (
          <div className="red-text text-[10px] mt-1">EXTERNES: {tel.external_listeners.join(', ')}</div>
        )}
      </div>

      {/* démons d'inférence */}
      <div className="panel p-3">
        <div className="flex items-center gap-2 text-[10px] tracking-widest text-neon-cyan mb-2"><Server size={12} /> DÉMONS D'INFÉRENCE</div>
        <div className="text-xs space-y-1">
          <div>Ollama <b className={d.ollama?.up ? 'text-neon-green' : 'red-text'}>{d.ollama?.up ? 'UP' : 'DOWN'}</b> <span className="text-zinc-600">{d.ollama?.url}</span></div>
          {(d.ollama?.models || []).map(m => <div key={m.name} className="text-[10px] text-zinc-400 pl-3">▸ {m.name} <span className="text-zinc-600">{(m.size / 1e9).toFixed(1)} Go</span></div>)}
          <div>Exo cluster <b className={d.exo?.up ? 'text-neon-green' : 'text-zinc-500'}>{d.exo?.up ? 'UP' : 'DOWN'}</b> <span className="text-zinc-600">{d.exo?.url}</span></div>
        </div>
        <div className="text-[10px] text-zinc-600 mt-2 flex items-center gap-1"><Cpu size={10} /> CPU {tel?.cpu?.load ?? '—'}% · {tel?.cpu?.cores ?? '—'} cœurs · <MemoryStick size={10} inline /> RAM {tel?.mem?.pct ?? '—'}% · <Thermometer size={10} inline /> {tel?.cpu?.temp ?? '—'}°C</div>
      </div>
    </div>
  );
}

function gaugeOption(title, value, max, unit) {
  return {
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge', startAngle: 210, endAngle: -30, min: 0, max,
      splitNumber: 5,
      axisLine: { lineStyle: { width: 10, color: [[0.3, '#22c55e'], [0.7, '#fbbf24'], [1, '#ff3860']] } },
      pointer: { length: '60%', width: 3, itemStyle: { color: '#00f0ff' } },
      axisTick: { distance: -10, length: 4, lineStyle: { color: '#555', width: 1 } },
      splitLine: { distance: -10, length: 10, lineStyle: { color: '#666', width: 2 } },
      axisLabel: { color: '#6b7280', fontSize: 9, distance: -22 },
      title: { offsetCenter: [0, '65%'], fontSize: 10, color: '#9ca3af' },
      detail: { valueAnimation: true, offsetCenter: [0, '38%'], fontSize: 18, color: '#fff', formatter: `{value}${unit}` },
      data: [{ value, name: title }],
    }],
  };
}
