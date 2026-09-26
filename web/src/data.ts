// Loaders and types for the T12 exports in public/data (see tools/export_web.py).
export type Phase = "injection" | "soak" | "production";
export type Scenario = "baseline" | "glide" | "heater";

export interface Cycle {
  well: string;
  label: string;
  t_h: number[];
  day: number[];
  prod_start_h: number;
  phase: Phase[];
  q_oil_bpd: number[];
  water_cut: (number | null)[];
  r_h_m: { L1: number[]; L2: number[]; L3: number[] };
  T_in_C: number[];
  T_wh_C: (number | null)[];
  mu_tubing_eff_Pas: (number | null)[];
  float_margin: number[];
  float_margin_glide: number[];
  float_margin_heater: number[];
  spm_current: number[];
  spm_glide: number[];
  spm_inflow: number[];
  spm_float: number[];
  spm_float_heater: number[];
  T_wh_heater_C: (number | null)[];
  mu_tubing_eff_heater_Pas: (number | null)[];
  events: { t_h: number; type: string; lead_h: number; msg: string; spm_from: number; spm_to: number; onset_t_h: number }[];
}

export interface ThermalMeta {
  T_min_C: number;
  T_max_C: number;
  tex_r_range_m: [number, number];
  tex_z_range_m: [number, number];
  frames: { file: string; tex: string; t_h: number; phase: Phase }[];
}

export interface CardXY { pos_m: number[]; load_kN: number[] }
export interface ScenarioCards {
  spm: number[];
  float: boolean[];
  settled: boolean[];
  min_load_raw_kN: number[];
  surface: { pos_m: number[][]; load_kN: number[][] };
  downhole: { pos_m: number[][]; load_kN: number[][] };
}
export interface CardsTimeline { days: number[]; t_h: number[]; baseline: ScenarioCards; glide: ScenarioCards; heater: ScenarioCards }

export interface TubingTimeline {
  days: number[];
  z_m: number[];
  baseline: { T_C: number[][]; mu_Pas: number[][] };
  heater: { T_C: number[][]; mu_Pas: number[][] };
}

export interface RodStroke { t_s: number[]; u_m: number[][]; stress_MPa: number[][] }
export interface RodMotion extends RodStroke { depth_m: number[]; float: RodStroke }

export interface Data {
  cycle: Cycle;
  thermal: ThermalMeta;
  cards: CardsTimeline;
  tubing: TubingTimeline;
  rod: RodMotion;
}

const base = import.meta.env.BASE_URL + "data/";
const get = async <T,>(f: string): Promise<T> => {
  const r = await fetch(base + f);
  if (!r.ok) throw new Error(`${f}: ${r.status}`);
  return (await r.json()) as T;
};

export async function loadAll(): Promise<Data> {
  const [cycle, thermal, cards, tubing, rod] = await Promise.all([
    get<Cycle>("cycle_timeseries.json"),
    get<ThermalMeta>("thermal_meta.json"),
    get<CardsTimeline>("cards_timeline.json"),
    get<TubingTimeline>("tubing_timeline.json"),
    get<RodMotion>("rod_motion.json"),
  ]);
  return { cycle, thermal, cards, tubing, rod };
}

export const texUrl = (f: string) => base + "thermal/" + f;

// ---------------------------------------------------------------- helpers
export const clamp = (x: number, a: number, b: number) => Math.min(b, Math.max(a, x));

/** Hourly index for a cycle time (t_h is 0,1,2,... h). */
export const hourIdx = (c: Cycle, tH: number) => clamp(Math.round(tH), 0, c.t_h.length - 1);

export const prodDay = (c: Cycle, tH: number) => (tH - c.prod_start_h) / 24;

export function margin(c: Cycle, i: number, s: Scenario) {
  return s === "glide" ? c.float_margin_glide[i] : s === "heater" ? c.float_margin_heater[i] : c.float_margin[i];
}
export function spm(c: Cycle, i: number, s: Scenario) {
  if (c.phase[i] !== "production") return 0;
  return s === "glide" ? c.spm_glide[i] : c.spm_current[i];
}
export function muEff(c: Cycle, i: number, s: Scenario) {
  return s === "heater" ? c.mu_tubing_eff_heater_Pas[i] : c.mu_tubing_eff_Pas[i];
}
export function Twh(c: Cycle, i: number, s: Scenario) {
  return s === "heater" ? c.T_wh_heater_C[i] : c.T_wh_C[i];
}

/** Hours from index i until the scenario's float margin first goes below zero (null: not this cycle). */
export function hoursToFloat(c: Cycle, i: number, s: Scenario): number | null {
  for (let j = i; j < c.t_h.length; j++) if (c.phase[j] === "production" && margin(c, j, s) < 0) return c.t_h[j] - c.t_h[i];
  return null;
}

/** Nearest timeline-card index for a production day (null before production). */
export function cardIdx(cards: CardsTimeline, day: number): number | null {
  if (day < 0) return null;
  let best = 0;
  for (let k = 0; k < cards.days.length; k++) if (Math.abs(cards.days[k] - day) < Math.abs(cards.days[best] - day)) best = k;
  return best;
}

export function phaseBounds(c: Cycle) {
  const last = (p: Phase) => {
    let t = 0;
    c.phase.forEach((q, k) => { if (q === p) t = c.t_h[k]; });
    return t;
  };
  return { injEnd: last("injection") + 1, soakEnd: last("soak") + 1, end: c.t_h[c.t_h.length - 1] };
}

// inferno (matplotlib) sampled at 9 stops, for fluid-temperature colouring
const INFERNO = ["#000004", "#1b0c41", "#4a0c6b", "#781c6d", "#a52c60", "#cf4446", "#ed6925", "#fb9b06", "#f7d13d", "#fcffa4"];
export function inferno(x: number): string {
  const t = clamp(x, 0, 1) * (INFERNO.length - 1);
  const k = Math.min(Math.floor(t), INFERNO.length - 2);
  const f = t - k;
  const a = hex(INFERNO[k]), b = hex(INFERNO[k + 1]);
  return `rgb(${a.map((v, n) => Math.round(v + f * (b[n] - v))).join(",")})`;
}
export function hex(h: string): [number, number, number] {
  const n = parseInt(h.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export const COLORS = {
  thermal: "#A8561A",
  wellbore: "#24588A",
  surface: "#546B1C",
  ai: "#5A4A8C",
  warn: "#A3321F",
  // lighter tints of the same hues for lines and text on the dark background
  thermalL: "#E08A45",
  wellboreL: "#6FA3D6",
  surfaceL: "#9DBA55",
  aiL: "#A796E6",
  warnL: "#E0654F",
  amber: "#D9A23A",
  green: "#6FB36A",
};

export const CAPTION =
  "Synthetic reference well BGW-SYN-01 · OIL published parameters (Jul 2025) + literature · not field data · prototype v0";
