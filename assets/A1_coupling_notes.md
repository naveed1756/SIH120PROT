# A1_coupling · notes

Synthetic reference well BGW-SYN-01 · OIL published parameters (Jul 2025) + literature · not field data · prototype v0

## Knob values (T09 order: T_PROD_D / water cut → F_INV → heater)
- T_PROD_D = 150 d (was 120; onset at ~day 125 fell outside a 120-day cycle)
- Water cut: FW0 = 0.85, FW_INF = 0.25, TAU_W_D = 20.0 d (scanned, unchanged)
- F_INV = 0.6 (scanned 0.5–0.8: no effect on onset, unchanged)
- Heater baseline: 0 kW (a heater only delays onset)
- K_MD = 6600 mD (DEMO, see DEVINSTRUCT.md)
- **The 30–80 day onset target is not reached with the listed knobs.** Onset stays inside days
  10–150, so this is recorded, not blocked. Reason: the DEMO K_MD gives high liquid rates that
  keep the tubing warm for most of the cycle.

## Pump and speed
- Plunger 2.25" (largest standard size); N_inflow at the production peak = 6.88 SPM
  (5–6 SPM band not reachable with standard sizes; closest chosen)
- Current practice: N = 6.88 SPM fixed, v_down,max = 1.081 m/s

## Onset days (production days)
| Case | Onset |
|---|---|
| Baseline, analytic float margin | 125.21 |
| Baseline, wave equation (min polished-rod load < 0) | 121.21 |
| Disagreement | -4.0 d (**> 3 d, reported per spec**) |
| 6 kW heater | none in cycle |
| Hydraulic S = 6 m, down_fraction 0.6, N = 3.44 SPM (v_down 0.655 m/s) | none in cycle |
| AI glide path | none (minimum margin 0.76) |

Demo "now" = day 124.625 (14 h before the analytic onset).
Emulsion inversion crossing (water cut < 60%): day 10.8.

Why the two onsets differ: the analytic margin uses the terminal fall speed of a rigid string
against the peak carrier-bar speed; the wave equation also carries the elastic stress wave and
the pump's fluid load, whose downstroke overshoot unloads the polished rod a few days earlier.

## Wave-equation cross-check (baseline N, T05 viscosity profile)
| Day | μ_eff (Pa·s) | min polished-rod load (kN) | load range (kN) | float |
|---|---|---|---|---|
| 95.2 | 1.69 | +7.74 | 67.1 | no |
| 125.2 | 3.17 | -1.75 | 86.2 | yes |
| 140.2 | 4.12 | -8.72 | 100.1 | yes |

## Strip 1 deviation
The spec asks for r_h (T − T_R ≥ 5 K). That front keeps moving outward during production by
conduction, so it cannot show the halo cooling. Strip 1 shows the hot-zone radius at
T ≥ T_NN = 70 °C per layer (end of production: L1 13.6 m, L2 13.0 m, L3 10.7 m);
the r_h values are stated in the strip text.
