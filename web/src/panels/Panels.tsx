import type { ReactNode } from "react";
import { clamp, COLORS, type CardsTimeline, type Scenario, type TubingTimeline } from "../data";

// ---------------------------------------------------------------- tiny SVG plot helpers
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
const fmtTick = (v: number) =>
  v >= 1000 ? v.toLocaleString("en-US") : v < 0.01 && v > 0 ? `0.${"0".repeat(-Math.floor(Math.log10(v)) - 1)}1` : `${v}`;

type Margin = { l: number; r: number; t: number; b: number };
function Axes({ w, h, m, xt, yt, sx, sy, xl, yl }: {
  w: number; h: number; m: Margin; xt: number[]; yt: number[]; sx: Scale; sy: Scale; xl: string; yl?: string;
}) {
  return (
    <g className="axes">
      {xt.map((v) => (
        <g key={`x${v}`}>
          <line className="grid" x1={sx(v)} x2={sx(v)} y1={m.t} y2={h - m.b} />
          <text x={sx(v)} y={h - m.b + 14} textAnchor="middle">{fmtTick(v)}</text>
        </g>
      ))}
      {yt.map((v) => (
        <g key={`y${v}`}>
          <line className="grid" x1={m.l} x2={w - m.r} y1={sy(v)} y2={sy(v)} />
          <text x={m.l - 6} y={sy(v) + 3.5} textAnchor="end">{fmtTick(v)}</text>
        </g>
      ))}
      <line className="base" x1={m.l} x2={w - m.r} y1={h - m.b} y2={h - m.b} />
      <line className="base" x1={m.l} x2={m.l} y1={m.t} y2={h - m.b} />
      <text className="al" x={(m.l + w - m.r) / 2} y={h - 4} textAnchor="middle">{xl}</text>
      {yl && <text className="al" transform={`translate(12,${(m.t + h - m.b) / 2}) rotate(-90)`} textAnchor="middle">{yl}</text>}
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

// ---------------------------------------------------------------- 1. dynamometer card
export function CardPanel({ cards, scenario, idx, analyticMargin }: { cards: CardsTimeline; scenario: Scenario; idx: number | null; analyticMargin: number }) {
  const w = 380, h = 250, m = { l: 44, r: 10, t: 8, b: 34 };
  const sc = cards[scenario];
  const allMax = Math.max(...cards.baseline.surface.load_kN.flat());
  const sx = lin([0, 3.2], [m.l, w - m.r]);
  const sy = lin([-5, Math.ceil((allMax + 5) / 20) * 20], [h - m.b, m.t]);
  if (idx === null)
    return (
      <Panel title="Pump load card" sub="pump off">
        <div className="empty">The well is shut in for steam injection or soak, so the pump is not running.</div>
      </Panel>
    );
  const prev = idx > 0 ? idx - 1 : null;
  const clip = sc.float[idx] && sc.settled[idx];
  const fl = clip && analyticMargin < 0;
  const early = clip && analyticMargin >= 0;
  const unsettled = !sc.settled[idx];
  const col = fl ? COLORS.warn : early ? COLORS.amber : COLORS.wellbore;
  return (
    <Panel title="Pump load card" sub={<>day {cards.days[idx].toFixed(0)} · {sc.spm[idx].toFixed(1)} strokes/min · simulated</>}>
      <div className="plotbox">
        <svg viewBox={`0 0 ${w} ${h}`} className="plot" preserveAspectRatio="xMidYMid meet">
          <Axes w={w} h={h} m={m} sx={sx} sy={sy} xt={[0, 1, 2, 3]} yt={[0, 40, 80]} xl="Rod position in the stroke (m)" yl="Load on the rods (kN)" />
          <line className="zero" x1={m.l} x2={w - m.r} y1={sy(0)} y2={sy(0)} />
          {prev !== null && (
            <path d={path(sc.surface.pos_m[prev], sc.surface.load_kN[prev], sx, sy) + "Z"} className="ln" stroke={COLORS.wellbore} strokeOpacity={0.22} strokeWidth={1.2} />
          )}
          <path d={path(sc.downhole.pos_m[idx], sc.downhole.load_kN[idx], sx, sy) + "Z"} className="ln" stroke="#8F9892" strokeDasharray="4 3" strokeWidth={1.2} />
          <path d={path(sc.surface.pos_m[idx], sc.surface.load_kN[idx], sx, sy) + "Z"} className="ln" stroke={col} strokeWidth={2} />
        </svg>
      </div>
      <div className="legend">
        <span><i style={{ background: col }} />at the surface</span>
        <span><i className="dash" />at the pump</span>
        {prev !== null && <span><i style={{ background: COLORS.wellbore, opacity: 0.25 }} />previous day</span>}
      </div>
      {fl && <div className="note warn">Rods are floating: the load drops to zero on the downstroke.</div>}
      {early && <div className="note amber">Detailed rod model: load is starting to touch zero. The quick check is still just above it (the two differ by about 4 days).</div>}
      {unsettled && <div className="note">Fluid is almost water here, so the rods ring for a few strokes; not rod float.</div>}
    </Panel>
  );
}

// ---------------------------------------------------------------- 2. tubing profiles
export function TubingPanel({ tubing, scenario, idx }: { tubing: TubingTimeline; scenario: Scenario; idx: number | null }) {
  const w = 190, h = 250, m = { l: 42, r: 8, t: 8, b: 34 };
  if (idx === null)
    return (
      <Panel title="Up the tubing" sub="pump off">
        <div className="empty">Profiles start once the pump runs.</div>
      </Panel>
    );
  const src = scenario === "heater" ? tubing.heater : tubing.baseline;
  const z = tubing.z_m, T = src.T_C[idx], mu = src.mu_Pas[idx];
  const sz = lin([0, 1100], [m.t, h - m.b]);
  const sT = lin([0, 300], [m.l, w - m.r]);
  const sM = logS([1e-4, 1e2], [m.l, w - m.r]);
  const other = scenario === "heater" ? tubing.baseline : null;
  return (
    <Panel title="Up the tubing" sub={<>day {tubing.days[idx].toFixed(0)}{scenario === "heater" ? " · with 6 kW heater" : ""}</>}>
      <div className="plotbox twin">
        <svg viewBox={`0 0 ${w} ${h}`} className="plot" preserveAspectRatio="xMidYMid meet">
          <Axes w={w} h={h} m={m} sx={sT} sy={sz} xt={[0, 100, 200, 300]} yt={[0, 500, 1000]} xl="Temperature (°C)" yl="Depth (m)" />
          {other && <path d={path(other.T_C[idx], z, sT, sz)} className="ln" stroke="#A7AFAA" strokeDasharray="3 3" strokeWidth={1.2} />}
          <path d={path(T, z, sT, sz)} className="ln" stroke={COLORS.thermal} strokeWidth={2} />
          <text className="note" x={sT(T[0]) + 5} y={m.t + 11}>{T[0].toFixed(0)} °C at surface</text>
        </svg>
        <svg viewBox={`0 0 ${w} ${h}`} className="plot" preserveAspectRatio="xMidYMid meet">
          <Axes w={w} h={h} m={m} sx={sM} sy={sz} xt={[0.001, 0.1, 10]} yt={[0, 500, 1000]} xl="Viscosity (Pa·s, log)" />
          {other && <path d={path(other.mu_Pas[idx], z, sM, sz)} className="ln" stroke="#A7AFAA" strokeDasharray="3 3" strokeWidth={1.2} />}
          <path d={path(mu, z, sM, sz)} className="ln" stroke={COLORS.wellbore} strokeWidth={2} />
          <text className="note" x={m.l + 4} y={m.t + 11}>{mu[0] < 0.1 ? mu[0].toFixed(4) : mu[0].toFixed(1)} Pa·s at surface</text>
        </svg>
      </div>
      <div className="legend">
        <span>Viscosity = how thick the oil–water mix is (water ≈ 0.001 Pa·s)</span>
        {other && <span><i className="dash" />without heater</span>}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------- 3. float margin gauge
export function Gauge({ value, hours, pumping, vDown }: { value: number; hours: number | null; pumping: boolean; vDown: number }) {
  const w = 240, h = 150, cx = w / 2, cy = 104, R = 82;
  const lo = -0.5, hi = 1.0;
  const ang = (v: number) => Math.PI * (1 - (clamp(v, lo, hi) - lo) / (hi - lo));
  const arc = (a: number, b: number) => {
    const p = (t: number) => `${cx + R * Math.cos(ang(t))},${cy - R * Math.sin(ang(t))}`;
    return `M${p(a)} A${R},${R} 0 0 1 ${p(b)}`;
  };
  const col = value < 0 ? COLORS.warn : value < 0.3 ? COLORS.amber : COLORS.green;
  const a = ang(value);
  const state = !pumping ? "Pump off" : value < 0 ? "Rods floating" : value < 0.3 ? "Float risk" : "Safe";
  const vFall = value < 1 ? vDown / (1 - value) : Infinity;
  return (
    <Panel title="Rod-float margin" sub="0 = rods start to float" className="gauge-panel">
      <div className="plotbox">
        <svg viewBox={`0 0 ${w} ${h}`} className="gauge" preserveAspectRatio="xMidYMid meet">
          <path d={arc(lo, 0)} stroke={COLORS.warn} className="arc" />
          <path d={arc(0, 0.3)} stroke={COLORS.amber} className="arc" />
          <path d={arc(0.3, hi)} stroke={COLORS.green} className="arc" />
          <line x1={cx} y1={cy} x2={cx + (R - 16) * Math.cos(a)} y2={cy - (R - 16) * Math.sin(a)} stroke="#1E2622" strokeWidth={3} strokeLinecap="round" />
          <circle cx={cx} cy={cy} r={5} fill="#1E2622" />
          <text x={cx - R} y={cy + 16} textAnchor="middle" className="tick">float</text>
          <text x={cx + R} y={cy + 16} textAnchor="middle" className="tick">safe</text>
          <text x={cx} y={cy + 34} textAnchor="middle" className="big" fill={col}>{pumping ? value.toFixed(2) : "—"}</text>
        </svg>
      </div>
      <div className="state" style={{ color: col }}>{state}</div>
      {pumping && (
        <div className="speeds">
          <div><span>Pump pulls the rods down at</span><b>{vDown.toFixed(2)} m/s</b></div>
          <div><span>Rods can fall through the oil at</span><b>{Number.isFinite(vFall) && vFall < 100 ? `${vFall.toFixed(2)} m/s` : "> 100 m/s"}</b></div>
        </div>
      )}
      <div className="forecast">
        {!pumping ? "No pumping in this phase." : hours === null ? "No rod float expected this cycle." : hours === 0 ? "The pump is outrunning the falling rods now." : <>Rod float expected in <b>about {hours.toFixed(0)} hours</b> at this speed.</>}
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
}
export function Recommendation(r: RecProps) {
  if (!r.active)
    return (
      <Panel title="Recommendation" sub="none pending" className="rec">
        <div className="empty">The forecaster checks the rod-float margin every hour and raises a recommendation before trouble starts.</div>
      </Panel>
    );
  return (
    <Panel title="Recommendation" sub={<span className="chip ai">AI speed plan</span>} className="rec">
      <div className="what">
        Slow the pump from <b>{r.spmFrom.toFixed(1)}</b> to <b>{r.spmTo.toFixed(1)}</b> strokes/min over 6 hours
      </div>
      <ul className="why">
        <li>Water cut is {(100 * r.fwNow).toFixed(0)} %, below the {(100 * r.fInv).toFixed(0)} % point where the oil–water mix turns thick.</li>
        <li>The wellhead cooled {r.twhDrop.toFixed(0)} °C in 30 days (now {r.twhNow.toFixed(0)} °C); the tubing fluid is {r.muRise.toFixed(0)} % more viscous.</li>
        <li>The new speed matches what the reservoir delivers and keeps a safety margin.</li>
      </ul>
      <div className="ifun">If nothing changes: <b>rods float in about {r.lead.toFixed(0)} hours</b>, with impact loads on every upstroke.</div>
      <div className="btns">
        {r.approved ? (
          <>
            <span className="ok">✓ Approved · new speed plan running</span>
            <button onClick={r.onReset}>Undo</button>
          </>
        ) : (
          <>
            <button className="primary" onClick={r.onApprove}>Approve</button>
            <button className={r.scenario === "heater" ? "on" : ""} onClick={r.onHeater}>What if: 6 kW downhole heater</button>
          </>
        )}
        <span className="conf">synthetic data · prototype v0</span>
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------- 5. status strip
const CHIPS: [string, string][] = [
  ["T1", "Reservoir"],
  ["T2", "Well & pump"],
  ["T3", "Surface unit"],
  ["D", "Failure cards"],
  ["F", "Float forecast"],
  ["O", "Speed plan"],
];
export function StatusStrip() {
  return (
    <div className="status">
      {CHIPS.map(([k, t]) => (
        <div key={k} className="schip">
          <b>{k}</b>
          <span>{t}</span>
          <em>v0</em>
        </div>
      ))}
    </div>
  );
}
