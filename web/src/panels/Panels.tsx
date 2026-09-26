import type { ReactNode } from "react";
import { clamp, COLORS, inferno, type CardsTimeline, type Scenario, type TubingTimeline } from "../data";

// ---------------------------------------------------------------- tiny SVG plot
interface Scale { (v: number): number }
function lin(d: [number, number], r: [number, number]): Scale {
  return (v) => r[0] + ((v - d[0]) / (d[1] - d[0])) * (r[1] - r[0]);
}
function logS(d: [number, number], r: [number, number]): Scale {
  const a = Math.log10(d[0]), b = Math.log10(d[1]);
  return (v) => r[0] + ((Math.log10(Math.max(v, 1e-12)) - a) / (b - a)) * (r[1] - r[0]);
}
const path = (xs: number[], ys: number[], sx: Scale, sy: Scale) =>
  xs.map((x, i) => `${i ? "L" : "M"}${sx(x).toFixed(1)},${sy(ys[i]).toFixed(1)}`).join("");

function Axes({ w, h, m, xt, yt, sx, sy, xl, yl }: {
  w: number; h: number; m: { l: number; r: number; t: number; b: number };
  xt: number[]; yt: number[]; sx: Scale; sy: Scale; xl: string; yl?: string;
}) {
  const fmt = (v: number) => (Math.abs(v) >= 1000 ? v.toLocaleString("en-US") : Math.abs(v) < 0.1 && v !== 0 ? v.toExponential(0) : `${v}`);
  return (
    <g className="axes">
      <line x1={m.l} x2={w - m.r} y1={h - m.b} y2={h - m.b} />
      <line x1={m.l} x2={m.l} y1={m.t} y2={h - m.b} />
      {xt.map((v) => (
        <g key={`x${v}`}>
          <line className="grid" x1={sx(v)} x2={sx(v)} y1={m.t} y2={h - m.b} />
          <text x={sx(v)} y={h - m.b + 13} textAnchor="middle">{fmt(v)}</text>
        </g>
      ))}
      {yt.map((v) => (
        <g key={`y${v}`}>
          <line className="grid" x1={m.l} x2={w - m.r} y1={sy(v)} y2={sy(v)} />
          <text x={m.l - 5} y={sy(v) + 3.5} textAnchor="end">{fmt(v)}</text>
        </g>
      ))}
      <text className="al" x={(m.l + w - m.r) / 2} y={h - 3} textAnchor="middle">{xl}</text>
      {yl && <text className="al" transform={`translate(11,${(m.t + h - m.b) / 2}) rotate(-90)`} textAnchor="middle">{yl}</text>}
    </g>
  );
}

export function Panel({ title, sub, children, className = "" }: { title: string; sub?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`panel ${className}`}>
      <header>
        <h3>{title}</h3>
        {sub && <span className="sub">{sub}</span>}
      </header>
      {children}
    </section>
  );
}

// ---------------------------------------------------------------- 1. card
export function CardPanel({ cards, scenario, idx, analyticMargin }: { cards: CardsTimeline; scenario: Scenario; idx: number | null; analyticMargin: number }) {
  const w = 360, h = 300, m = { l: 40, r: 10, t: 10, b: 32 };
  const sc = cards[scenario];
  const allMax = Math.max(...cards.baseline.surface.load_kN.flat());
  const sx = lin([0, 3.2], [m.l, w - m.r]);
  const sy = lin([-5, Math.ceil((allMax + 5) / 20) * 20], [h - m.b, m.t]);
  if (idx === null)
    return (
      <Panel title="Dynamometer card" sub="pump off">
        <div className="empty">Well shut in for steam injection / soak: no pumping.</div>
      </Panel>
    );
  const prev = idx > 0 ? idx - 1 : null;
  const clip = sc.float[idx] && sc.settled[idx];
  const fl = clip && analyticMargin < 0; // both models agree: rods float
  const early = clip && analyticMargin >= 0; // wave equation clips first (A1 notes: ~4 d model gap)
  const unsettled = !sc.settled[idx];
  return (
    <Panel
      title="Dynamometer card · live"
      sub={<>day {cards.days[idx].toFixed(0)} · {sc.spm[idx].toFixed(1)} SPM · wave equation</>}
    >
      <svg viewBox={`0 0 ${w} ${h}`} className="plot">
        <Axes w={w} h={h} m={m} sx={sx} sy={sy} xt={[0, 1, 2, 3]} yt={[0, 40, 80]} xl="Position (m)" yl="Load (kN)" />
        <line className="zero" x1={m.l} x2={w - m.r} y1={sy(0)} y2={sy(0)} />
        {prev !== null && (
          <path d={path(sc.surface.pos_m[prev], sc.surface.load_kN[prev], sx, sy) + "Z"} className="ln" stroke={COLORS.wellboreL} strokeOpacity={0.28} strokeWidth={1.2} />
        )}
        <path d={path(sc.downhole.pos_m[idx], sc.downhole.load_kN[idx], sx, sy) + "Z"} className="ln" stroke="#9aa39e" strokeDasharray="4 3" strokeWidth={1.2} />
        <path d={path(sc.surface.pos_m[idx], sc.surface.load_kN[idx], sx, sy) + "Z"} className="ln" stroke={fl ? COLORS.warnL : early ? COLORS.amber : COLORS.wellboreL} strokeWidth={2} />
      </svg>
      <div className="legend">
        <span><i style={{ background: fl ? COLORS.warnL : early ? COLORS.amber : COLORS.wellboreL }} />surface</span>
        <span><i className="dash" />downhole (pump)</span>
        {prev !== null && <span><i style={{ background: COLORS.wellboreL, opacity: 0.3 }} />previous day</span>}
        {fl && <span className="badge warn">rod float · load clipped at 0 · min {sc.min_load_raw_kN[idx].toFixed(1)} kN</span>}
        {early && <span className="badge amber">wave eq.: clipping starts (min {sc.min_load_raw_kN[idx].toFixed(1)} kN) · analytic margin still ≥ 0 · models differ by ~4 d</span>}
        {unsettled && <span className="badge dim">transient not settled (near-water viscosity)</span>}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------- 2. tubing
export function TubingPanel({ tubing, scenario, idx }: { tubing: TubingTimeline; scenario: Scenario; idx: number | null }) {
  const w = 176, h = 340, m = { l: 40, r: 8, t: 8, b: 32 };
  if (idx === null)
    return (
      <Panel title="Tubing profile" sub="pump off">
        <div className="empty">Profiles start with pumped production.</div>
      </Panel>
    );
  const src = scenario === "heater" ? tubing.heater : tubing.baseline;
  const z = tubing.z_m, T = src.T_C[idx], mu = src.mu_Pas[idx];
  const sz = lin([0, 1100], [m.t, h - m.b]);
  const sT = lin([0, 300], [m.l, w - m.r]);
  const sM = logS([1e-4, 1e2], [m.l, w - m.r]);
  const other = scenario === "heater" ? tubing.baseline : null;
  return (
    <Panel title="Tubing T and μ vs depth" sub={<>day {tubing.days[idx].toFixed(0)}{scenario === "heater" ? " · 6 kW heater" : ""}</>}>
      <div className="twin">
        <svg viewBox={`0 0 ${w} ${h}`} className="plot">
          <defs>
            <linearGradient id="tgrad" x1="0" x2="0" y1="0" y2="1">
              {z.map((zz, i) => (i % 10 === 0 ? <stop key={i} offset={zz / 1100} stopColor={inferno((T[i] - 50) / 260)} /> : null))}
            </linearGradient>
          </defs>
          <Axes w={w} h={h} m={m} sx={sT} sy={sz} xt={[0, 100, 200, 300]} yt={[0, 500, 1000]} xl="T (°C)" yl="Depth (m)" />
          {other && <path d={path(other.T_C[idx], z, sT, sz)} className="ln" stroke="#9aa39e" strokeDasharray="3 3" strokeWidth={1.2} />}
          <rect x={w - m.r - 7} y={m.t} width={5} height={h - m.b - m.t} fill="url(#tgrad)" />
          <path d={path(T, z, sT, sz)} className="ln" stroke={COLORS.thermalL} strokeWidth={2} />
          <text className="note" x={sT(T[0]) + 4} y={m.t + 10}>{T[0].toFixed(0)} °C wellhead</text>
        </svg>
        <svg viewBox={`0 0 ${w} ${h}`} className="plot">
          <Axes w={w} h={h} m={m} sx={sM} sy={sz} xt={[1e-3, 1e-1, 10]} yt={[0, 500, 1000]} xl="μ mixture (Pa·s)" />
          {other && <path d={path(other.mu_Pas[idx], z, sM, sz)} className="ln" stroke="#9aa39e" strokeDasharray="3 3" strokeWidth={1.2} />}
          <path d={path(mu, z, sM, sz)} className="ln" stroke={COLORS.wellboreL} strokeWidth={2} />
          <text className="note" x={m.l + 3} y={m.t + 10}>top {mu[0] < 0.1 ? mu[0].toExponential(1) : mu[0].toFixed(2)} Pa·s</text>
        </svg>
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------- 3. gauge
export function Gauge({ value, hours, pumping, vDown }: { value: number; hours: number | null; pumping: boolean; vDown: number }) {
  const w = 230, h = 156, cx = w / 2, cy = 102, R = 78;
  const lo = -0.5, hi = 1.0;
  const ang = (v: number) => Math.PI * (1 - (clamp(v, lo, hi) - lo) / (hi - lo));
  const arc = (a: number, b: number) => {
    const p = (t: number) => `${cx + R * Math.cos(ang(t))},${cy - R * Math.sin(ang(t))}`;
    return `M${p(a)} A${R},${R} 0 0 1 ${p(b)}`;
  };
  const col = value < 0 ? COLORS.warnL : value < 0.3 ? COLORS.amber : COLORS.green;
  const a = ang(value);
  const state = !pumping ? "PUMP OFF" : value < 0 ? "RODS FLOATING" : value < 0.3 ? "FLOAT RISK" : "OK";
  const vFall = value < 1 ? vDown / (1 - value) : Infinity;
  return (
    <Panel title="Float margin" sub="1 − v_down / v_fall">
      <svg viewBox={`0 0 ${w} ${h}`} className="gauge">
        <path d={arc(lo, 0)} stroke={COLORS.warnL} className="arc" />
        <path d={arc(0, 0.3)} stroke={COLORS.amber} className="arc" />
        <path d={arc(0.3, hi)} stroke={COLORS.green} className="arc" />
        {[-0.5, 0, 0.3, 1].map((t) => (
          <text key={t} x={cx + (R + 13) * Math.cos(ang(t))} y={cy - (R + 13) * Math.sin(ang(t)) + 3} textAnchor="middle" className="tick">{t}</text>
        ))}
        <line x1={cx} y1={cy} x2={cx + (R - 14) * Math.cos(a)} y2={cy - (R - 14) * Math.sin(a)} stroke="#e8ece9" strokeWidth={3} strokeLinecap="round" />
        <circle cx={cx} cy={cy} r={5} fill="#e8ece9" />
        <text x={cx} y={cy + 32} textAnchor="middle" className="big" fill={col}>{pumping ? value.toFixed(2) : "—"}</text>
        <text x={cx} y={cy + 49} textAnchor="middle" className="state" fill={col}>{state}</text>
      </svg>
      {pumping && (
        <div className="speeds">
          <div><span>carrier bar, max down</span><b>{vDown.toFixed(2)} m/s</b></div>
          <div><span>rod free-fall in the oil</span><b>{Number.isFinite(vFall) && vFall < 100 ? `${vFall.toFixed(2)} m/s` : "> 100 m/s"}</b></div>
        </div>
      )}
      <div className="forecast">
        {!pumping ? "No pumping in this phase." : hours === null ? "No rod float forecast this cycle." : hours === 0 ? "Rods floating now: the carrier bar outruns the falling rods." : <>Rod float forecast in <b>~{hours.toFixed(0)} h</b> at the current speed.</>}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------- 4. recommendation
export interface RecProps {
  active: boolean;
  approved: boolean;
  scenario: Scenario;
  spmFrom: number;
  spmTo: number;
  fwNow: number;
  fInv: number;
  muNow: number;
  muRise: number;
  twhNow: number;
  twhDrop: number;
  lead: number;
  onApprove: () => void;
  onHeater: () => void;
  onReset: () => void;
  trend: { d: number[]; base: number[]; glide: number[]; now: number };
}

function TrendMini({ t }: { t: RecProps["trend"] }) {
  const w = 440, h = 108, m = { l: 34, r: 8, t: 8, b: 22 };
  const sx = lin([t.d[0], t.d[t.d.length - 1]], [m.l, w - m.r]);
  const sy = lin([-0.3, 1], [h - m.b, m.t]);
  const xt = [t.d[0], t.now - 15, t.now].map((v) => Math.round(v));
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="plot">
      <Axes w={w} h={h} m={m} sx={sx} sy={sy} xt={xt} yt={[0, 0.5, 1]} xl="production day" />
      <rect x={m.l} y={sy(0)} width={w - m.l - m.r} height={sy(-0.3) - sy(0)} fill={COLORS.warn} opacity={0.14} />
      <rect x={sx(t.now)} y={m.t} width={w - m.r - sx(t.now)} height={h - m.b - m.t} fill="#ffffff" opacity={0.035} />
      <path d={path(t.d, t.base, sx, sy)} className="ln" stroke="#c9d0cc" strokeWidth={1.4} />
      <path d={path(t.d, t.glide, sx, sy)} className="ln" stroke={COLORS.aiL} strokeWidth={2.2} />
      <line x1={sx(t.now)} x2={sx(t.now)} y1={m.t} y2={h - m.b} stroke={COLORS.aiL} strokeDasharray="3 2" />
      <text className="note" x={sx(t.now) + 4} y={m.t + 9}>now · forecast →</text>
      <text className="note" x={m.l + 4} y={sy(0) + 11} fill={COLORS.warnL}>float</text>
      <text className="note" x={m.l + 4} y={sy(t.glide[0]) + 13} fill={COLORS.aiL}>AI glide path</text>
      <text className="note" x={sx(t.now) - 6} y={sy(t.base[Math.floor(t.base.length * 0.7)]) - 8} textAnchor="end">current practice</text>
    </svg>
  );
}
export function Recommendation(r: RecProps) {
  if (!r.active)
    return (
      <Panel title="Advisory" sub="H · I13" className="rec">
        <div className="empty">No recommendation pending. The forecaster (F) watches the float margin every hour.</div>
      </Panel>
    );
  return (
    <Panel title="Recommendation" sub={<span className="chip ai">AI · O2 glide path</span>} className="rec">
      <div className="what">
        Step SPM <b>{r.spmFrom.toFixed(1)} → {r.spmTo.toFixed(1)}</b> over 6 h
      </div>
      <ul className="why">
        <li>Water cut {(100 * r.fwNow).toFixed(0)} %, below the {(100 * r.fInv).toFixed(0)} % inversion point: the tubing emulsion is oil-continuous.</li>
        <li>Wellhead temperature down {r.twhDrop.toFixed(0)} °C in 30 days, to {r.twhNow.toFixed(0)} °C; tubing μ_eff {r.muNow.toFixed(1)} Pa·s (+{r.muRise.toFixed(0)} %).</li>
        <li>New speed matches pump displacement to inflow and keeps the float margin ≥ 0.19 (N ≤ 0.9·N_float).</li>
      </ul>
      <TrendMini t={r.trend} />
      <div className="ifun">If unchanged: <b>rod float in ~{r.lead.toFixed(0)} h</b> (carrier-bar separation, impact loads on the next upstroke).</div>
      <div className="conf">Confidence: <span className="chip">synthetic · v0</span> analytic margin + wave-equation cross-check</div>
      <div className="btns">
        {r.approved ? (
          <>
            <span className="ok">✓ Approved · glide path active</span>
            <button onClick={r.onReset}>Undo</button>
          </>
        ) : (
          <>
            <button className="primary" onClick={r.onApprove}>Approve</button>
            <button className={r.scenario === "heater" ? "on" : ""} onClick={r.onHeater}>What-if: 6 kW heater</button>
          </>
        )}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------- 5. status strip
const CHIPS: [string, string, string][] = [
  ["T1", "Reservoir heat · rheology · inflow", "prototype v0"],
  ["T2", "Wellbore (Ramey) · rod & pump wave eq.", "prototype v0"],
  ["T3", "Surface kinematics", "prototype v0 · beam/hydraulic only"],
  ["D", "Card library (9 classes, synthetic)", "prototype v0"],
  ["F", "Rod-float onset forecast", "prototype v0"],
  ["O", "O2 SPM glide path (lite)", "prototype v0"],
];
export function StatusStrip() {
  return (
    <div className="status">
      {CHIPS.map(([k, t, m]) => (
        <div key={k} className="schip" title={t}>
          <b>{k}</b>
          <span>{t}</span>
          <em>{m}</em>
        </div>
      ))}
    </div>
  );
}
