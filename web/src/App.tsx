import { useEffect, useMemo, useRef, useState } from "react";
import {
  CAPTION, cardIdx, hourIdx, hoursToFloat, loadAll, margin, muEff, prodDay, spm, Twh, type Data, type Scenario,
} from "./data";
import { CardPanel, Gauge, Recommendation, StatusStrip, TubingPanel } from "./panels/Panels";
import Timeline from "./panels/Timeline";
import Scene from "./scene/Scene";
import { tourState, TOUR_S } from "./tour";
import { STRESS_RANGE } from "./scene/Well";

const q = new URLSearchParams(window.location.search);
const PRESENT = q.get("present") === "1";
const SHOT = q.get("shot") === "1";
const F_INV = 0.6; // params.F_INV (emulsion inversion water fraction)

declare global {
  interface Window { __READY?: boolean }
}

export default function App() {
  const [data, setData] = useState<Data | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    loadAll().then(setData).catch((e) => setErr(String(e)));
  }, []);
  if (err) return <div className="loading">Could not load /data: {err}. Run python tools/export_web.py.</div>;
  if (!data) return <div className="loading">Loading twin data…</div>;
  return <Dashboard d={data} />;
}

function Dashboard({ d }: { d: Data }) {
  const c = d.cycle;
  const ev = c.events[0];
  const qt = q.get("t");
  const [tH, setTH] = useState<number>(qt && qt !== "now" ? +qt : ev.t_h);
  const [scenario, setScenario] = useState<Scenario>((q.get("scenario") as Scenario) || "baseline");
  const [unit, setUnit] = useState<"beam" | "hydraulic">((q.get("unit") as "beam") || "beam");
  const [playing, setPlaying] = useState(false);
  const [tourSec, setTourSec] = useState<number | null>(
    q.get("tourAt") !== null ? +(q.get("tourAt") as string) : q.get("tour") === "1" ? 0 : null,
  );
  const tourFrozen = q.get("tourAt") !== null;
  const [speed, setSpeed] = useState(2);
  const end = c.t_h[c.t_h.length - 1];

  // play loop: speed in days per second
  const last = useRef<number | null>(null);
  useEffect(() => {
    if (!playing) return;
    let raf = 0;
    const step = (now: number) => {
      const dt = last.current === null ? 0 : (now - last.current) / 1000;
      last.current = now;
      setTH((t) => {
        const n = t + dt * speed * 24;
        if (n >= end) {
          setPlaying(false);
          return end;
        }
        return n;
      });
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => {
      cancelAnimationFrame(raf);
      last.current = null;
    };
  }, [playing, speed, end]);

  // demo tour (storyboard, CLAUDE.md section 7)
  const touring = tourSec !== null;
  useEffect(() => {
    if (!touring || tourFrozen) return;
    let raf = 0;
    let t0: number | null = null;
    const step = (now: number) => {
      if (t0 === null) t0 = now;
      const s = (now - t0) / 1000;
      if (s >= TOUR_S) {
        setTourSec(null);
        return;
      }
      setTourSec(s);
      raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [touring, tourFrozen]);
  const ts = touring ? tourState(tourSec as number, c) : null;
  useEffect(() => {
    if (ts) {
      setTH(ts.tH);
      setScenario(ts.scenario);
    }
  }, [ts?.tH, ts?.scenario]); // eslint-disable-line react-hooks/exhaustive-deps

  const i = hourIdx(c, tH);
  const ph = c.phase[i];
  const pumping = ph === "production";
  const day = prodDay(c, tH);
  const ci = pumping ? cardIdx(d.cards, day) : null;
  const N = spm(c, i, scenario);
  const m = pumping ? margin(c, i, scenario) : 1;
  const hrs = pumping ? hoursToFloat(c, i, scenario) : null;
  const frameIdx = Math.min(d.thermal.frames.length - 1, Math.max(0, Math.round(tH / 24)));

  // fluid temperature along the tubing for the 3D column
  const fluid = useMemo(() => {
    const z = d.tubing.z_m;
    if (ci !== null) return { z, T: (scenario === "heater" ? d.tubing.heater : d.tubing.baseline).T_C[ci] };
    if (ph === "injection") return { z, T: z.map(() => c.T_in_C[i]) };
    return { z, T: z.map((zz) => 30 + (20 * zz) / 1150) }; // soak: shut in, geotherm (params T_SURF_GEO_C..T_R_C)
  }, [ci, ph, scenario, d.tubing, c.T_in_C, i]);

  // recommendation facts, all taken at the forecast event
  const ie = hourIdx(c, ev.t_h);
  const i30 = hourIdx(c, ev.t_h - 30 * 24);
  const rec = {
    fwNow: c.water_cut[ie] ?? 0,
    muNow: c.mu_tubing_eff_Pas[ie] ?? 0,
    muRise: 100 * ((c.mu_tubing_eff_Pas[ie] ?? 0) / (c.mu_tubing_eff_Pas[i30] ?? 1) - 1),
    twhNow: c.T_wh_C[ie] ?? 0,
    twhDrop: (c.T_wh_C[i30] ?? 0) - (c.T_wh_C[ie] ?? 0),
  };
  const recActive = pumping && tH >= ev.t_h - 0.5;

  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (ready) window.__READY = true;
  }, [ready]);

  const kpi = (l: string, v: string) => (
    <div className="kpi">
      <span>{l}</span>
      <b>{v}</b>
    </div>
  );
  const muNow = muEff(c, i, scenario);
  const twh = Twh(c, i, scenario);

  return (
    <div className={`app ${PRESENT ? "present" : ""}`}>
      <header className="top">
        <div className="title">
          <h1>Baghewala Well-to-Surface Twin</h1>
          <span className="chip">Synthetic well BGW-SYN-01 · prototype v0</span>
          <span className={`chip scen ${scenario}`}>
            {scenario === "baseline" ? "Current practice" : scenario === "glide" ? "AI speed plan approved" : "What if: 6 kW downhole heater"}
          </span>
        </div>
        <div className="kpis">
          {kpi("Oil rate", pumping ? `${c.q_oil_bpd[i].toFixed(0)} bbl/day` : "—")}
          {kpi("Water cut", c.water_cut[i] !== null ? `${(100 * (c.water_cut[i] as number)).toFixed(0)} %` : "—")}
          {kpi("Temp. at pump", `${c.T_in_C[i].toFixed(0)} °C`)}
          {kpi("Temp. at surface", twh !== null ? `${twh.toFixed(0)} °C` : "—")}
          {kpi("Tubing viscosity", muNow !== null ? `${muNow.toFixed(muNow < 0.1 ? 3 : 1)} Pa·s` : "—")}
          {kpi("Pump speed", pumping ? `${N.toFixed(1)} strokes/min` : "off")}
          <div className="unit">
            <button className={unit === "beam" ? "on" : ""} onClick={() => setUnit("beam")}>Beam</button>
            <button className={unit === "hydraulic" ? "on" : ""} onClick={() => setUnit("hydraulic")}>Hydraulic</button>
          </div>
        </div>
      </header>

      <main>
        <div className="scene">
          <Scene
            thermal={d.thermal}
            frameIdx={frameIdx}
            phase={ph}
            spm={N}
            unit={unit}
            rod={d.rod}
            floatStroke={pumping && m < 0}
            fluidZ={fluid.z}
            fluidT={fluid.T}
            TinC={c.T_in_C[i]}
            present={PRESENT}
            frozenPhase={SHOT ? 0.62 : null}
            cam={ts ? ts.cam : null}
            onReady={() => setReady(true)}
          />
          <div className="scene-over">
            <div className="legend3d">
              <div>
                <span>Temperature</span>
                <i className="inferno" />
                <em>{50} °C</em>
                <em>310 °C</em>
              </div>
              <div>
                <span>Rod stress</span>
                <i className="stress" />
                <em>{STRESS_RANGE[0]} MPa</em>
                <em>{STRESS_RANGE[1]} MPa</em>
              </div>
            </div>
            {!PRESENT && !ts && <div className="hint">Drag to rotate · scroll to zoom · depth compressed, widths exaggerated</div>}
            {ts?.caption && <div className="tour-cap">{ts.caption}</div>}
          </div>
        </div>
        <aside className="side">
          <div className="row2">
            <CardPanel cards={d.cards} scenario={scenario} idx={ci} analyticMargin={m} />
            <TubingPanel tubing={d.tubing} scenario={scenario} idx={ci} />
          </div>
          <div className="row2 b">
            <Gauge value={m} hours={hrs} pumping={pumping} vDown={(Math.PI * 3.0 * N) / 60} />
            <Recommendation
              active={recActive}
              approved={scenario === "glide"}
              scenario={scenario}
              spmFrom={ev.spm_from}
              spmTo={ev.spm_to}
              fInv={F_INV}
              lead={ev.onset_t_h - ev.t_h}
              {...rec}
              onApprove={() => setScenario("glide")}
              onHeater={() => setScenario(scenario === "heater" ? "baseline" : "heater")}
              onReset={() => setScenario("baseline")}
            />
          </div>
          <StatusStrip />
        </aside>
      </main>

      <Timeline
        cycle={c}
        tH={tH}
        scenario={scenario}
        playing={playing}
        speed={speed}
        present={PRESENT}
        onScrub={(t) => setTH(t)}
        onPlay={() => setPlaying((v) => !v)}
        onSpeed={setSpeed}
        touring={touring}
        onTour={() => {
          setPlaying(false);
          setTourSec(touring ? null : 0);
        }}
        onNow={() => {
          setPlaying(false);
          setTH(ev.t_h);
        }}
      />
      <footer className="caption">{CAPTION}</footer>
      {ts?.overlay && <TourOverlay kind={ts.overlay} />}
    </div>
  );
}

function TourOverlay({ kind }: { kind: "title" | "A3" | "A5" | "end" }) {
  const base = import.meta.env.BASE_URL + "tour/";
  if (kind === "title")
    return (
      <div className="overlay title">
        <h1>Baghewala Well-to-Surface Twin</h1>
        <p>Cyclic steam stimulation and sucker-rod pumping, simulated as one system</p>
        <span className="chip">synthetic well BGW-SYN-01 · OIL published parameters · prototype v0</span>
      </div>
    );
  if (kind === "end")
    return (
      <div className="overlay end">
        <div className="chain">
          {["Steam heat in the reservoir", "Oil thickness vs temperature", "Heat loss up the well", "Rods & pump", "AI failure-card library", "Rod-float forecast", "Pump-speed plan", "Advice to the operator"].map((x, k) => (
            <span key={x} className={k >= 4 ? "ai" : ""}>{x}</span>
          ))}
        </div>
        <p>synthetic well · OIL parameters · prototype v0</p>
      </div>
    );
  const src = kind === "A3" ? "A3_card_library.png" : "A5_confusion.png";
  const cap = kind === "A3" ? "No failure data? The twin generates it: 9 pump conditions" : "The classifier, tested on an operating range it never saw";
  return (
    <div className="overlay img">
      <img src={base + src} alt={cap} />
      <p>{cap}</p>
    </div>
  );
}
