// Demo tour: the CLAUDE.md section 7 storyboard (75 s) as keyframes over tour seconds.
import { phaseBounds, type Cycle, type Scenario } from "./data";

export type Cam = "surface" | "reservoir" | "overview";
export type Overlay = null | "title" | "A3" | "A5" | "end";
export const TOUR_S = 75;

export const CAMS: Record<Cam, { pos: [number, number, number]; target: [number, number, number] }> = {
  surface: { pos: [15, 7, 19], target: [-2, 2.5, 0] },
  reservoir: { pos: [20, -15, 26], target: [2, -23.5, 0] },
  overview: { pos: [46, 5, 58], target: [0, -10.5, 0] },
};

const lerpKeys = (keys: [number, number][], s: number) => {
  if (s <= keys[0][0]) return keys[0][1];
  for (let k = 1; k < keys.length; k++) {
    const [s0, v0] = keys[k - 1], [s1, v1] = keys[k];
    if (s <= s1) return v0 + ((v1 - v0) * (s - s0)) / Math.max(s1 - s0, 1e-9);
  }
  return keys[keys.length - 1][1];
};

export function tourState(sec: number, c: Cycle) {
  const b = phaseBounds(c);
  const now = c.events[0].t_h;
  const p0 = c.prod_start_h;
  const tH = lerpKeys(
    [
      [0, 0], [6, 0], [22, b.injEnd], [35, p0 + 3 * 24], [37, p0 + 95 * 24], [48, now], [TOUR_S, now],
    ],
    sec,
  );
  const cam: Cam = sec < 6 ? "surface" : sec < 22 ? "reservoir" : "overview";
  const scenario: Scenario = sec >= 51 ? "glide" : "baseline";
  const overlay: Overlay = sec < 6 ? "title" : sec >= 68 ? "end" : sec >= 61 ? "A5" : sec >= 55 ? "A3" : null;
  const caption =
    sec < 6 ? "" :
    sec < 22 ? "Steam injection: 3.1 t/h wet steam for 18 days; the hot halo grows wider at the top (steam override)" :
    sec < 35 ? "Soak, then pumped production: the rod string's stress wave and the live dynamometer card" :
    sec < 48 ? "Cooling: tubing viscosity rises as the halo shrinks and the emulsion inverts" :
    sec < 51 ? "Forecast: rod float in ~14 h at the current speed" :
    sec < 55 ? "Approved: the AI glide path steps the pump speed down; the card returns to normal" : "";
  return { tH, cam, scenario, overlay, caption };
}
