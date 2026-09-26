# Asset manifest · BGW-SYN-01 prototype v0 (T16)

Every figure carries the caption below (bottom-left, 8 pt, grey). All numbers come from our own
models on a **synthetic** reference well driven by OIL's published field-level parameters and
literature priors; nothing here is field data. Regenerate any asset with the script named in
DEVINSTRUCT.md §2.

> Caption on every asset: `Synthetic reference well BGW-SYN-01 · OIL published parameters (Jul 2025) + literature · not field data · prototype v0`

| File | One-sentence message | Modules · innovations | Key numbers | Suggested slide |
|---|---|---|---|---|
| `A4_dashboard.png` (3840 × 2160) | One screen shows the whole well, from reservoir heat to the pumping unit, and an AI recommendation that prevents rod float before it happens. | H (advisory), T1, T2-A, T2-B, F, O2 lite · I2, I13 | At the "now" event (production day 124.6): float margin 0.01, rod float forecast in ~14 h at 6.9 SPM; recommendation 6.9 → 1.1 SPM over 6 h; tubing μ_eff 3.1 Pa·s, wellhead 58 °C, water cut 25 % | **Idea / proposed solution** (hero, full bleed) |
| `A1_coupling.png` + `A1_coupling_notes.md` | As the steam heat decays the oil in the tubing thickens and the rods start to float; the twin forecasts it 14 h ahead and the SPM glide path prevents it. | T1 → T1-B → T2-A → T2-B → F → O2 lite · I2, I13 | Onset production day 125.2 (analytic) vs 121.2 (wave equation), both reported; glide path minimum margin 0.76; 6 kW heater and hydraulic (S 6 m, slow downstroke) what-ifs: no float in the 150-day cycle; plunger 2.25", T_PROD_D 150 d | **Impact & benefits** (centrepiece) |
| `A2_thermal_cycle.mp4` | The reservoir temperature field through one CSS cycle: steam injection builds a halo that is wider at the top (override), soak spreads it, production cools it. | T1-A thermal grid | 592 frames (6-hourly, 120-day production run), 49 s at 12 fps; r_h end of injection L1/L2/L3 = 18.6 / 15.5 / 13.5 m; heat-budget closure ≤ 1e-13 | Technical approach (thumbnail) / video |
| `A2_end_injection.png`, `A2_end_soak.png`, `A2_day60.png` | Stills of the same field at three moments of the cycle. | T1-A | Steam injection 3.1 t/h for 18 d at 99 ksc(g) bottomhole, 1.63 MW to the sandface | Technical approach |
| `A3_card_library.png` | No failure data? The twin generates it: nine pump conditions from the rod-string wave equation. | T2-B, D1 · I6 | 13,104 labelled synthetic cards (9 classes × 1,500, 91.6–100 % valid per class), 2–5 % noise on surface cards | Technical approach |
| `A6a_marx_langenheim.png` | The thermal grid reproduces the Marx–Langenheim analytical heated area. | T1-A verification | Grid 275 / 402 m² vs analytical 276 / 403 m² at 14 / 21 days (−1 %) | Feasibility & viability |
| `A5_confusion.png`, `A5_f1_bars.png` | The AI learns failure modes from simulated cards and is tested on an operating range it never saw. | D1 · I6 | Macro-F1 0.80 on 5,917 held-out cards (μ > 10 Pa·s or depth > 1,050 m); 5-fold CV in range 0.80; weakest: tagging vs normal | Feasibility & viability |
| `A6b_gibbs_roundtrip.png` | The diagnostic direction works: the pump card is recovered from the surface card. | T2-B diagnostic (Gibbs) | RMS 0.6 % (normal) and 3.7 % (fluid pound) of the load range at 0.5 Pa·s; 1.9 % at 10 Pa·s | Feasibility & viability |
| `A7_sectional_speed.png` | Same pump speed, no rod float: slowing only the downstroke of a hydraulic unit clears the float. | O1 · T2-B | Day 135, N 4.5 SPM, S 4 m: downstroke 50 → 56 % of the cycle, max down speed 0.78 → 0.65 m/s, min load -0.8 → +4.5 kN | Impact & benefits |
| `S2_tubing_profiles.png` | The tubing, not the reservoir, sets the viscosity the rods see. | T2-A (Ramey W.13) · T1-B | Wellhead 189 → 64 °C from day 5 to day 100; μ at the top 0.0007 → 8 Pa·s | Technical approach / backup |
| `A8_vit_quality.png` | Tubing insulation decides how much steam reaches the pay; the wellbore model reproduces Layer 3B's grade study. | T2-A injection mode | Sandface quality E/D/C/B 0.59 / 0.51 / 0.34 / 0.23 (3B 0.61 / 0.54 / 0.37 / 0.25); bare tubing condenses at 779 m | Technical approach / backup |
| `A9_pareto.png` | The twin can design the steam cycle: a Pareto front of oil per cycle-day vs SOR, with a knee design and OIL's current practice for reference. | O3 (stage v0) · T1-D-like proxy | Knee 1,710 t at 3.3 t/h, soak 0.74: J1 41.0 bbl/d vs OIL practice 39.5; SOR levels unrealistically low (DEMO permeability), shape only | Impact & benefits (optional) |
| `S1_viscosity.png` | Placeholder rheology prior anchored on OIL's 11,500 cP at 50 °C. | T1-B | μ 11.7 / 0.30 / 0.011 Pa·s at 50 / 100 / 200 °C | Feasibility (small) or backup |

## Also available

The dashboard also has a 75 s **demo tour** (`Demo tour` button, or `?tour=1`) following the CLAUDE.md §7 storyboard; no MP4 of it is recorded yet (screen-record `npm run preview` with `?tour=1&present=1`).

## How A4 was made

`web/`: `npm run build`, `npm run preview`, then `node scripts/screenshot.mjs`, which opens
`http://localhost:4173/?present=1&shot=1` in headless Chromium at 1920 × 1080 with device
scale 2 and waits for the 3D scene to render. `present=1` hides the cursor and renders at
pixel ratio 2; `shot=1` freezes the pump stroke at 62 % of the cycle (downstroke) so the
image is reproducible. The only console message is a THREE.Clock deprecation warning
raised inside @react-three/fiber (no errors).

## Notes an Oil India reviewer may ask about
- No **flowback** (natural-flow) phase: Layer 2 has one between soak and pumped, plan.md makes it
  optional and the PoC goes straight to pumping after soak (marked on the dashboard timeline and the A1 axis).
- K_MD = 6,600 mD is a DEMO effective kh tuned to the 18 bbl/d cold rate (above the Layer 1
  500 mD); production averages 52 bbl/d, above the field's ~26 bbl/d (see PROGRESS.md).
- Rod-float onset lands at production day ~121–125, not mid-cycle (days 30–80): with these
  rates the tubing stays warm for most of the cycle. The listed tuning knobs could not move it.
- The "current practice" baseline runs at the peak-inflow speed all cycle and assumes a full
  pump (no fluid pound), per the brief.
