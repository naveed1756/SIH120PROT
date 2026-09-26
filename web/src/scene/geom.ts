// Scene layout: y up, ground at y = 0, well axis at x = z = 0. Surface equipment is at
// true scale (m). Underground depth is compressed in three sections (brief T13):
//   0 .. 30 m        to scale x SCALE_A
//   30 .. 1,090 m    compressed into GAP units (break symbols at both ends)
//   1,090 .. 1,175 m to scale x SCALE_A (pump at 1,100 m, pay 1,150-1,160 m, window pay +/- 15 m)
// Radii of casing / tubing / rods are exaggerated (schematic) and labelled as such.
export const SCALE_A = 0.2;
export const TOP_M = 30;
export const MID_END_M = 1090;
export const GAP = 5;

export function depthToY(d: number): number {
  if (d <= TOP_M) return -d * SCALE_A;
  if (d <= MID_END_M) return -TOP_M * SCALE_A - ((d - TOP_M) / (MID_END_M - TOP_M)) * GAP;
  return -TOP_M * SCALE_A - GAP - (d - MID_END_M) * SCALE_A;
}
/** Local vertical scale (units per m) at depth d. */
export function scaleAt(d: number): number {
  return d > TOP_M && d <= MID_END_M ? GAP / (MID_END_M - TOP_M) : SCALE_A;
}

export const PUMP_DEPTH_M = 1100;
export const PAY_TOP_M = 1150;
export const PAY_H = [4, 3, 3];
export const WIN_TOP_M = PAY_TOP_M - 15; // texture top  (1,135 m)
export const WIN_BOT_M = PAY_TOP_M + 10 + 15; // texture bottom (1,175 m)

export const R_RES = 10; // reservoir cutaway radius (units) <-> log r 0.1 .. 150 m
export const R_CASING = 0.42;
export const R_TUB_O = 0.24;
export const R_TUB_I = 0.17;
export const R_ROD = 0.075;

export const STROKE = 3.0; // m, beam unit (params.STROKE_M)

/** Radius on the reservoir faces (units) for a true radius (m), log mapping of the texture. */
export const rToX = (r: number, rMin = 0.1, rMax = 150) => (R_RES * Math.log(r / rMin)) / Math.log(rMax / rMin);

/** Beam-unit polished-rod position (m, 0 at bottom) for stroke phase 0..1 (twin/kinematics.py). */
export const beamY = (ph: number) => (STROKE / 2) * (1 - Math.cos(2 * Math.PI * ph));

/** Hydraulic unit: trapezoidal speed, equal up/down time (visual; the what-if uses df 0.6). */
export function hydY(ph: number) {
  const ramp = 0.12;
  const ease = (u: number) => {
    // position along a trapezoidal-velocity stroke, u in 0..1
    const v = 1 / (1 - ramp);
    if (u < ramp) return (0.5 * v * u * u) / ramp;
    if (u > 1 - ramp) return 1 - (0.5 * v * (1 - u) * (1 - u)) / ramp;
    return 0.5 * v * ramp + v * (u - ramp);
  };
  return ph < 0.5 ? STROKE * ease(ph / 0.5) : STROKE * (1 - ease((ph - 0.5) / 0.5));
}
