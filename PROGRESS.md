# PROGRESS

Repo root = `D:\naveed\others\SIH2026\PS26120\prototype` (the folder holding CLAUDE.md).
Built and tested in the cloud workspace (Python 3.11.15, venv), committed to git there, and moved to the
folder as a git bundle (`.sync/poc.bundle`, see DEVINSTRUCT.md §3).

## Status
| Task | Status | Key numbers | Notes |
|---|---|---|---|
| T00 | done | pytest: 0 collected, no import errors | layout per CLAUDE.md 3.4; `conftest.py` puts root on sys.path |
| T01 | done | 3 tests pass | IBM Plex Sans bundled in `twin/fonts/` (OFL) so figures look the same on any machine |
| T02 | done | μ_oil 50/100/200 °C = 11.69 / 0.302 / 0.0109 Pa·s; HB = Walther at 50 s⁻¹ to 2e-16; mixture ratio μ(0.50)/μ(0.70) at 50 °C = 3,975 | 18 tests pass. Two deviations from the brief, see Decisions (monotone test, log-space blend). Asset S1 done |
| T03 | done | Marx–Langenheim: grid 275 / 402 m² vs 276 / 403 m² at 14 / 21 d (−1 %); energy closure ≤ 1e-13 every step; 1-D slab vs erf < 3 %; r_h end of injection L1/L2/L3 = 18.6 / 15.5 / 13.5 m (override: top > bottom) | Solver: regime Picard + Jäger–Kačur fallback (18 steps used it, 0 halvings). Latent-heat condensation-front closure (Decisions). Assets A6a, A2 mp4 + 3 stills |
| T04 | done | K_MD = 6,600 mD (DEMO) → cold 18.0 bbl/d; CSS production avg **53.1 bbl/d** (peak 58.0 at day 0, monotone decline to 47.6 at day 120); cycle runtime 26 s | **Average is outside the 20–40 note band; see Checkpoint.** K_MD exceeds the §8 5,000 mD guard: needs human confirmation (Blocked) |
| T05 | done | Wellhead T at T_in 150 °C: 40.7 / 61.7 / 90.4 °C for 5 / 10 / 20 m³/d (3B: 41 / 62 / 91) | Ramey W.13 with L_R = 72 m per m³/d; heater rule of thumb 10 °C/kW at 5 m³/d. S2 figure deferred (Should tier) |
| T06 | done | Static F_pr = 42.43 kN = 28.81 (buoyant rods, 26.19 N/m) + 13.62 (F_fl, 1.75", p_int 20 ksc) kN; normal card N 5, S 3 m, μ 0.5: closure 0.6 %, area > 0, **plunger stroke 2.834 m** | a·Δt/Δx = 0.77; 3 strokes, 3rd kept; ~2.4 s per card single, batched over cards |
| T07 | done | 9 × 1,500 cards in 264 s (2 processes); valid (closed ≤ 5 %, finite): normal 99.1, pound 91.6, gas 98.6, float 100, tv 99.6, sv 99.4, unseated 95.3, parted 97.5, tagging 95.9 %; 13,104 kept after label-consistency drop | `out/cards.parquet` (git-ignored; regenerate `python -m ml.card_library`). Asset A3 |
| T08 | todo | | Should |
| T09 | todo | | |
| T10 | todo | | Should |
| T11 | todo | | Should |
| T12 | todo | | |
| T13 | todo | | |
| T14 | todo | | Could |
| T15 | todo | | Could |
| T16 | todo | | |

## Tuned knobs
- K_MD = 6,600 mD (cold rate 18.0 bbl/d) — T04. Layer-1 value 500 mD kept as `K_MD_LAYER1` (gives 1.4 bbl/d)
- PLUNGER_D_M = … ; float onset day (baseline) = … ; with heater = … ; hydraulic = … — T09

## Decisions
- 2026-09-26 09:50 · The folder holding CLAUDE.md is the repo root (no extra `baghewala-twin-poc/` level) · that is where the user put the brief.
- 2026-09-26 09:50 · Code is built and tested in the cloud workspace and synced to the user's folder · the shell on the user's computer would not start ("workspace unavailable").
- 2026-09-26 09:55 · `docs/` is missing. Not blocking the build: the three architecture HTML files (and plan.md) are in the claude.ai Project "SIH2026" and are read from there for every task. The user is asked to copy them into `docs/` (and plan.md into the root) so the repo is complete · CLAUDE.md 8 says stop; the user said inconsistencies may be resolved at my discretion with Layers 2/3A/3B as the base, and the docs are available unchanged, not reconstructed.
- 2026-09-26 10:05 · **T02 done-when conflict: "mu_mixture is monotone decreasing in f_w".** The brief's own formula (Pal–Rhodes W/O branch, 3A B.7) makes a water-in-oil emulsion thicker than the dead oil as water rises toward inversion (at 50 °C μ rises from 11.7 Pa·s at f_w = 0 to ~44 Pa·s at f_w ≈ 0.42). That is standard emulsion physics and what 3A specifies. Following the user's rule (Layers 2/3A/3B are the base), Pal–Rhodes is kept, and the test asserts monotone decrease from `F_INV − 2·F_INV_W` upward (through and above inversion), plus a separate check that the W/O emulsion is thicker than oil. The ≥ 10× drop threshold is unchanged and passes (3,975×). Consequence for T09: the thickest tubing fluid occurs just after water cut falls through inversion, which strengthens the mid-cycle float trigger described in the brief §4.
- 2026-09-26 10:05 · **Regime blend done in log space:** `ln μ = (1−s)·ln μ_WO + s·ln μ_OW` instead of B.8's linear `(1−s)·μ_WO + s·μ_OW`, same s(f_w). With the linear form the W/O branch (which diverges toward φ/PHI100 → 1.187) dominates far past inversion (μ still ~65 Pa·s at f_w = 0.7–0.8 at 50 °C) and the 10× drop test fails; the log blend keeps s acting as the regime switch B.8 describes. Both formulas give the same end members.
- 2026-09-26 10:05 · `cp()` returns J/kg/K (SI) rather than the kJ/kg/K written in the brief · CLAUDE.md 3.3 "SI inside all code".
- 2026-09-26 10:05 · Water viscosity is tabulated once from IAPWS-97 (1–370 °C, 0.5 °C step, at 1 MPa or 1.05·Psat to stay liquid) and interpolated · iapws is scalar-only and slow; the brief's "1 MPa" would be steam above ~180 °C.
- 2026-09-26 10:05 · Rheology envelope (T_pp+3 … 320 °C) is exposed as `in_envelope()` rather than raising · functions must stay vectorised for the thermal and rod solvers; callers flag out-of-envelope use.

- 2026-09-26 10:30 · `docs/` now provided by the user (plan.md is at `docs/plan.md`, not the root); docs are committed to git.
- 2026-09-26 10:30 · Git: repo initialised in the workspace (branch `main`); commits moved to the user's folder as a git bundle because the local shell does not start. `.gitignore` covers venv/caches, `out/`, node, `.sync/`, OS/editor files; `.gitattributes` normalises line endings.
- 2026-09-26 10:45 · T03 phase lengths rounded to whole hours (soak 0.55 × 18 d = 237.6 h → 238 h) · keeps hourly records and 6-hourly frames on the hour.
- 2026-09-26 10:50 · **T03 latent-heat closure (operator split).** Without the water-mass equation nothing carries the latent part of the injected steam (≈ 36 % of the 1.63 MW) away from the first cell. Each step, the latent power of each z-row is walked outward from the well, filling every cell up to its saturated-liquid enthalpy H_l (the steam zone) and passing the rest on (the condensation front). The implicit solve carries only sensible heat: conduction + upwind liquid advection at h_w(T). Energy-exact. A first attempt (flowing quality x = X_SF·S_s) was abandoned: latent storage per cell (~14 MJ/m³) is tiny against the latent throughput, which made it stiff and produced negative temperatures.
- 2026-09-26 10:55 · **T03 nonlinear solver.** Regime-based Picard first; if a cell sits on the saturation kink and regimes do not settle, Jäger–Kačur relaxation (slope 1/M everywhere, matrix factorised once, monotone and convergent); step-halving as the last fallback. The energy budget uses the linearisation of the final solve, so closure is exact; the linearisation error in T is < 1e-3 K.
- 2026-09-26 11:00 · Grid heated area for the Marx–Langenheim check = per-row interpolated radius where T − T_R = ½ΔT, π(r² − r_w²) averaged over the pay · counting whole cells gave a ±15 % staircase on the log grid; the interpolated radius is the sub-cell equivalent (same interpolation as r_h).
- 2026-09-26 11:00 · T03 pay conductivity = λ_R^(1−φ)·λ_f^φ with λ_f = λ_oil(T_R)^S_oi · λ_w^(1−S_oi) = 1.52 W/mK (brief: "geometric mean of rock and fluid"). KH_CONTRAST read as the kh ratio between layers (total kh = K_MD × 10 m).
- 2026-09-26 11:05 · T04 per-layer ratio: J_k/J_c from each layer's r_h and μ_oil(T_bar_k); total q_o = q_c × kh-weighted mean ratio; layer split ∝ kh_k·J_k (reconciles "kh-weighted mean" and "split by kh_k·J_k" in the brief). Production liquid is advected as water (brief), ρ_w = 988 kg/m³.
- 2026-09-26 11:05 · Checked the brief's step-profile ratio against 3A C.4's cell-by-cell resistance on the same temperature field: both give ≈ 3.3× cold on day 0 and stay flat (step formula 58 → 48 bbl/d; C.4 56 → 55 bbl/d). The high average is therefore not an artefact of the simplification; brief formula kept.

## Checkpoint after T04 (for the human)
- **Tuned K_MD = 6,600 mD** (effective kh 66 D·m over 10 m) gives the 18.0 bbl/d cold rate. This is **above the CLAUDE.md §8 guard of 5,000 mD** and 13× Layer 1's 500 mD. 3A FC-1 predicted exactly this gap (Layer 1 rock + 11,500 cP oil give only ~1.4 bbl/d) and lists the likely reasons: residual heat from earlier cycles, heaters, diluent, shear-thinning near the well, or higher real kh. The value is kept as an explicitly labelled DEMO "effective kh" because it only scales rates (heat transport in T1-A does not depend on it). **Needs your confirmation** (options below).
- Cold rate 18.0 bbl/d · CSS production average **53.1 bbl/d** · peak 58.0 bbl/d at production day 0 · 47.6 bbl/d at day 120 · liquid 382 → 64 bbl/d as water cut falls 0.85 → 0.25.
- r_h (T − T_R ≥ 5 K) at end of injection: L1 18.6 m, L2 15.5 m, L3 13.5 m (β = 2 override). Mobile radius (T ≥ T_NN) is smaller and shrinks through production; r_h itself keeps growing slowly by conduction, so **A1 strip 1 should plot r_m (T ≥ 70 °C) or r_50**, which do shrink (Part 4 decision).
- Average 53 bbl/d is **outside the 20–40 band** (target ~25–26). Cause: after 1,340 t of steam the 10 m pay stays hot (T_in 284 °C → 132 °C over 120 d), so the heated/cold productivity ratio stays near its geometric ceiling ln(r_e/r_w)/ln(r_e/r_h) ≈ 3.3. Not forced, as the brief asks. Levers if you want the field average: fewer days of production in the average, a lower β/thicker pay, or a larger r_e. None is a listed knob, so nothing was changed.

- 2026-09-26 11:30 · K_MD: user briefly chose the Layer-1 500 mD (commit bd2d810, rate 4.2 → 4.6 bbl/d, T04 decline check failed), then reverted to the 6,600 mD DEMO value (this state) and accepted it. The 5,000 mD guard exceedance is accepted by the user; A2 assets were rendered with 6,600 mD and stay.

- 2026-09-26 12:00 · T06/T07 fixed constants added to params: RHO_FLUID_ROD 950 kg/m³ (Assumed; gives the brief's 26.2 N/m), P_THP 5 ksc (Assumed), T06_TEST_PLUNGER 1.75" (until T09 sizes the plunger), HYST_FRAC 0.5 %, MIN_DWELL_FRAC 0.3.
- 2026-09-26 12:05 · Pump state machine: reversal needs 0.5 % S_p of travel AND 30 % of the half-stroke elapsed (without the dwell, stress-wave ringing at low viscosity flipped the state and the tagging impulse re-triggered itself: −146 kN cards). Each half-stroke starts from the load at the reversal (removed a jump on tv_leak). Tagging impulse fires once per stroke at the bottom reversal.
- 2026-09-26 12:05 · Steam/gas interference = polytropic compression (n 1.2) of the gas gap (1−f)·S_p from p_int until p = p_dis, where the travelling valve opens; R = p_dis/p_int per card. tv_leak τ = time since the up-reversal / upstroke duration.
- 2026-09-26 12:10 · Card validity ("closed") = |F_pr(3T) − F_pr(2T)| ≤ 5 % of the load range, on the clean simulated card before noise. The first version compared the first and last recorded samples (one sample apart) on the noisy card, which failed periodic cards with a sharp load change at the stroke boundary and any card with 2–5 % noise. T06's own 1 % test uses the same periodicity metric.
- 2026-09-26 12:10 · Library sampling: non-float classes draw μ ≤ min(3 Pa·s, 0.8 × the float-onset viscosity for that N, S); rod_float draws μ in 5–40 Pa·s and N ≥ 1.15 × the float-onset speed, so the label is physically plausible before simulation; the simulated float flag must still agree or the card is dropped (label_ok). Hydraulic N capped at the feasible maximum for S and down_fraction 0.5–0.65. Noise and ±1 % position jitter applied to the surface card only (the downhole card is computed, not measured). rod_parted cards are batched by length so node spacing stays ~10 m.

## Deferred
- S2 tubing-profile figure (Should tier; after all Musts).
- Live-oil (GOR) correction, Refutas diluent blending (B.9), aquathermolysis multiplier: not needed for the PoC assets.

## Blocked
- ~~K_MD above the 5,000 mD guard~~ **resolved 26 Sep 11:30: user accepted 6,600 mD (DEMO effective kh).** Alternatives: (a) keep 6,600 mD; (b) cap at 5,000 mD → cold rate 13.6 bbl/d (fails the 18 ± 1 test, would be reported); (c) 1,000 mD × 23 m (top of Layer 1) → ~6 bbl/d.

## Assets produced
- `assets/S1_viscosity.png/.svg` — placeholder rheology prior (T02)
- `assets/A6a_marx_langenheim.png/.svg` — grid vs analytical heated area, −1 % at 14 and 21 d (T03)
- `assets/A2_thermal_cycle.mp4` — 592 frames (6-hourly) of the r–z temperature field, 49 s at 12 fps (T03/T04)
- `assets/A2_end_injection|A2_end_soak|A2_day60.png/.svg` — stills (T03/T04)
- `assets/A3_card_library.png/.svg` — medoid card per class from 13,104 kept synthetic cards (T07)
