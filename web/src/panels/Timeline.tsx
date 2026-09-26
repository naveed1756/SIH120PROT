import { useMemo } from "react";
import { Area, ComposedChart, Line, ReferenceLine, ResponsiveContainer, XAxis, YAxis } from "recharts";
import { COLORS, margin, phaseBounds, type Cycle, type Scenario } from "../data";

interface Props {
  cycle: Cycle;
  tH: number;
  scenario: Scenario;
  playing: boolean;
  speed: number;
  present: boolean;
  onScrub: (t: number) => void;
  onPlay: () => void;
  onSpeed: (s: number) => void;
  onNow: () => void;
  touring: boolean;
  onTour: () => void;
}

export default function Timeline(p: Props) {
  const c = p.cycle;
  const b = phaseBounds(c);
  const data = useMemo(() => {
    const out = [];
    for (let i = 0; i < c.t_h.length; i += 6) {
      const prod = c.phase[i] === "production";
      out.push({
        t: c.t_h[i],
        q: prod ? c.q_oil_bpd[i] : null,
        m: prod ? margin(c, i, p.scenario) : null,
        mb: prod && p.scenario !== "baseline" ? c.float_margin[i] : null,
      });
    }
    return out;
  }, [c, p.scenario]);
  const ev = c.events[0];
  const seg = (a: number, z: number, name: string, cls: string) => (
    <div className={`seg ${cls}`} style={{ left: `${(100 * a) / b.end}%`, width: `${(100 * (z - a)) / b.end}%` }}>
      {name}
    </div>
  );
  const day = p.tH / 24;
  const ph = c.phase[Math.min(c.phase.length - 1, Math.round(p.tH))];
  const phDay = ph === "injection" ? day : ph === "soak" ? (p.tH - b.injEnd) / 24 : (p.tH - c.prod_start_h) / 24;
  return (
    <div className="timeline">
      <div className="tl-left">
        <div className="clock">
          <div className="d">Cycle day {day.toFixed(1)}</div>
          <div className="p">{ph === "production" ? "Pumping" : ph === "injection" ? "Steam injection" : "Soak (well shut in)"} · day {phDay.toFixed(1)}</div>
        </div>
        {!p.present && (
          <div className="ctl">
            <button onClick={p.onPlay}>{p.playing ? "Pause" : "Play"}</button>
            <select value={p.speed} onChange={(e) => p.onSpeed(+e.target.value)}>
              {[0.5, 2, 8].map((s) => (
                <option key={s} value={s}>{s} days/s</option>
              ))}
            </select>
            <button onClick={p.onNow}>Jump to “now”</button>
            <button className={p.touring ? "on" : ""} onClick={p.onTour}>{p.touring ? "■ Stop tour" : "Demo tour"}</button>
          </div>
        )}
      </div>
      <div className="tl-main">
        <div className="chart">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data} margin={{ top: 4, right: 36, bottom: 0, left: 36 }}>
              <XAxis dataKey="t" type="number" domain={[0, b.end]} hide />
              <YAxis yAxisId="q" hide domain={[0, 70]} />
              <YAxis yAxisId="m" hide domain={[-0.6, 1.1]} />
              <Area yAxisId="q" dataKey="q" stroke={COLORS.surface} fill={COLORS.surface} fillOpacity={0.12} strokeWidth={1.2} isAnimationActive={false} connectNulls={false} />
              {p.scenario !== "baseline" && (
                <Line yAxisId="m" dataKey="mb" stroke="#9AA39E" strokeDasharray="3 3" dot={false} strokeWidth={1} isAnimationActive={false} />
              )}
              <Line yAxisId="m" dataKey="m" stroke={p.scenario === "baseline" ? "#27302B" : COLORS.ai} dot={false} strokeWidth={p.scenario === "baseline" ? 1.4 : 2.2} isAnimationActive={false} />
              <ReferenceLine yAxisId="m" y={0} stroke={COLORS.warn} strokeOpacity={0.6} strokeDasharray="4 3" />
              <ReferenceLine yAxisId="m" x={ev.t_h} stroke={COLORS.ai} strokeDasharray="2 2" />
              <ReferenceLine yAxisId="m" x={p.tH} stroke="#1E2622" strokeWidth={1.5} />
            </ComposedChart>
          </ResponsiveContainer>
          <div className="chart-lg">
            <span><i style={{ background: COLORS.surface }} />Oil rate</span>
            <span><i style={{ background: p.scenario === "baseline" ? "#27302B" : COLORS.ai }} />Rod-float margin</span>
            <span><i style={{ background: COLORS.warn }} />Float line (margin 0)</span>
            <span><i style={{ background: COLORS.ai }} className="dash" />Forecast raised</span>
          </div>
        </div>
        <div className="bar">
          {seg(0, b.injEnd, "Injection", "inj")}
          {seg(b.injEnd, b.soakEnd, "Soak", "soak")}
          {seg(b.soakEnd, b.end, "Pumping", "prod")}
          <div className="fb" style={{ left: `${(100 * b.soakEnd) / b.end}%` }}>no natural-flow phase in this prototype</div>
          <div className="evt" style={{ left: `${(100 * ev.t_h) / b.end}%` }} title="float forecast" />
          <input
            type="range"
            min={0}
            max={b.end}
            step={1}
            value={Math.round(p.tH)}
            onChange={(e) => p.onScrub(+e.target.value)}
            aria-label="cycle time"
          />
        </div>
      </div>
    </div>
  );
}
