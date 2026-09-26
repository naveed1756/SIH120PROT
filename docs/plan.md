# Baghewala Well-to-Surface Twin: PoC build plan for the idea PPT

SIH 2026 · PS 26120 · Oil India Limited · Smart Automation
Baseline: Layer 2 v3, Layer 3A rev 2, Layer 3B rev 2 (25 Sep 2026)
Written: Fri 25 Sep 2026

---

## 0. The situation and the one decision that follows from it

- **Deadline.** Third-party SIH guides give **30 Sep 2026** as the national portal deadline for nominations and idea submission. Confirm the exact date with your SPOC tonight. This plan assumes **4 build days (Sat 26 to Tue 29)** and submission on Wed 30 morning.
- **People.** 3 on this PS.
- **Data.** None. There is no public Baghewala dataset. What is public (OIL's Jul 2025 field deck, the Apr 2026 PTI report) is already in the Layer 2/3 docs as parameter anchors.
- **Goal.** Not a working system. It is a small set of **physics-true, visually striking assets** (stills and one short video) that prove three things to a judge in 10 seconds each:
  1. *This team can actually simulate the well*: reservoir heat, wellbore, rods and pump.
  2. *They understood the real problem*: CSS heat decay → viscosity → rod float, the coupling that the PS title ("well-to-surface") is about.
  3. *There is AI on top that solves a real data gap*: synthetic failure cards → classifier; float forecast → SPM advice.

**Decision:** build a *thin vertical slice* of the architecture on the synthetic reference well **BGW-SYN-01** (Layer 3A §9), tuned to OIL's field-level figures, and nothing else. Skip P1 (MQTT, TimescaleDB), SE/ensembles, O5, CSP4 benchmarking, and the full enthalpy two-phase T1-A. Those go to the finale plan (section 9).

---

## 1. What goes in the PPT, ranked by attention per hour of work

Most teams on this PS will show a generic dashboard with an LSTM. The assets below are hard to fake, and an OIL engineer will recognise each one on sight.

| # | Asset | Why it catches attention | Architecture it proves | Effort | Tier |
|---|---|---|---|---|---|
| **A1** | **Coupling story chart**: one stacked timeline over a CSS cycle: heated radius shrinking → wellhead T falling → tubing viscosity rising → rod-float margin → *SPM glide path* with a "float predicted 14 h ahead" marker and card thumbnails morphing along the top | This *is* the PS. It shows CSS and SRP as one system. Nobody else will have it. | T1-A → T1-B → T2-A → T2-B → F → O2 (I2 predictive float prevention) | 1 day (after A2 and A3 exist) | **Must** |
| **A2** | **Reservoir thermal field animation**: r–z temperature heatmap through injection → soak → flowback → pumped, steam override visible (hot wedge wider at top), halo collapsing | Looks like "real simulation". Heat maps sell. | T1-A, T1-B | 1–1.5 days | **Must** |
| **A3** | **Dynamometer card failure library**: 3×3 grid of surface + downhole cards: normal, fluid pound, steam/gas interference, rod float, TV leak, SV leak, unseated, rod parted, plunger tagging | OIL production engineers read cards daily. Instant credibility. Also *is* innovation I6 ("no failure data? the twin generates it"). | T2-B (Gibbs wave equation, predictive mode), D1 | 1.5 days | **Must** |
| **A4** | **3D twin hero + advisory dashboard**: cutaway well (pump jack → VIT tubing → rods → glowing reservoir halo), live card, float gauge, recommendation card with reason and counterfactual | First-impression slide. Screenshot for slide 2, 60–90 s screen recording if the template allows a link. | H layer, I13 | 2–3 days (parallel from day 1 on mock data) | **Must** (static screenshot); video **Should** |
| **A5** | **Classifier confusion matrix + per-class F1**, trained on A3's synthetic cards, tested on a *held-out viscosity range* | Proves the ML is real and honestly validated | D1, I6 | 0.5 day | **Should** |
| **A6** | **Validation plot**: T1-A heated radius vs Marx–Langenheim (and a Gibbs round-trip: surface card → recovered downhole card vs imposed) | Feasibility slide: "our physics is checked against closed-form solutions" | T1-A guard-rails, E2 | 0.25 day each (falls out of A2 and A3) | **Should** |
| **A7** | **O1 sectional speed control before/after**: same SPM, slowed downstroke → float disappears from the card | Cheap, visual, shows *control*, not just monitoring | O1, T3 kinematics | 0.25 day | **Should** |
| **A8** | Steam quality at sandface by VIT grade (bar chart) + wellhead T vs rate | Nice T2-A evidence; numbers already in Layer 3B §2 and §4.4 | T2-A | 0.5 day | Could |
| **A9** | O3 Pareto front (oil per cycle-day vs SOR) with "OIL practice" point and knee design, on an L0 analytical proxy | Optimiser visual | T1-D, O3 (stage v0) | 0.75 day | Could |
| A10 | Architecture diagram restyled (from Layer 2 Figure 1) | Required context | all | 1 h | Must (cheap) |

**Cut line if time runs out (Monday night check):** A1, A2, A3, A4-static, A10 must exist. A5–A7 next. A8–A9 only if someone is idle.

---

## 2. Data strategy: what is real, what is synthetic, and how to label it

### 2.1 What exists publicly (searched 25 Sep 2026)

| Need | Found | Use this week? |
|---|---|---|
| Baghewala parameters | OIL Jul 2025 field deck; PTI/Business Standard Apr 2026 (already in Layer 2 §2, 3A §2) | **Yes**: every anchor value in BGW-SYN-01 |
| Labelled dynamometer cards | Only in papers (e.g. SPE-194949: 35,292 cards in 12 classes; Sensors 2020 AlexNet-SVM study). No downloadable labelled set found. | **No**: generate our own (this is I6) |
| Measured downhole cards | Sandia **Downhole Dynamometer Database (DDDB)**, 1997, distributed on request (CD-ROM) | No (too slow). **Email Sandia now** for the finale. |
| CSS benchmark | SPE CSP4 Problem 1 (Aziz, Ramesh & Woo, JPT 1987): full data in the paper, OnePetro paywall | No. Get via college library for the finale. |
| Oil-well anomaly time series | Petrobras 3W | No: offshore naturally flowing wells, not SRP |

### 2.2 Labelling rule for every asset

Every figure and video frame carries one caption line, bottom-left, small:

> *Synthetic reference well BGW-SYN-01 · parameters from OIL's published field data (Jul 2025) and literature · not field data · prototype stage v0*

This is consistent with the architecture docs' evidence labels. Judges from OIL will respect it, and it protects you from a "where did you get this data?" question. **Do not put OIL's logo on the dashboard UI** (the SIH template's title slide can name the organisation; the product mock should not look like an official OIL tool).

### 2.3 BGW-SYN-01 "demo variant"

Layer 3A §9 flags that the reference well's cold rate (~1.4 bbl/d) is far below field evidence (FC-1). For the PoC, tune one knob so the demo is consistent with OIL's published numbers:

| Quantity | Target | Source | Knob |
|---|---|---|---|
| Cold (pre-CSS) oil rate | ~18 bbl/d (≈ 70% of 26 bbl/d) | OIL: +39.5% CSS uplift; ~26 bbl/d per listed well (Layer 3B §2) | Raise effective kh (k·h) until cold IPR (3A eq. C.2c, no TPG) gives 18 bbl/d |
| Cycle-average oil rate after CSS | ~25–26 bbl/d | same | Emerges from T1-A + two-zone ratio; do not force |
| Everything else | Layer 3A §9 and 3B §6 values | registry P-01…P-41 | unchanged |

Write the chosen kh into `params.py` with a comment `# DEMO: tuned to OIL field-level figures (FC-1), not a Baghewala prediction`.

---

## 3. Team split and interfaces

| Person | Owns | Assets |
|---|---|---|
| **P-A: Reservoir & wellbore** | `twin/params.py`, `rheology.py`, `thermal_rz.py`, `inflow.py`, `wellbore.py`, `scenario_cycle.py` | A2, A6 (thermal), A8, feeds A1 |
| **P-B: Rods, pump & ML** | `rodpump.py`, `kinematics.py`, `ml/*`, float and glide-path logic | A3, A5, A6 (Gibbs), A7, feeds A1 |
| **P-C: Visual & integration** (the teammate who does immersive web; the 3D scene and dashboard are exactly that skill set) | `web/`, figure style, PPT assembly, video | A4, A10, final A1 layout |

**P-C starts on day 1 with mock data** that follows the contracts in section 7, so nobody waits on anyone. P-A and P-B hand over real exports by Sunday night.

---

## 4. Day-by-day

| Day | P-A | P-B | P-C |
|---|---|---|---|
| **Sat 26** | `params.py` + `rheology.py` (tests pass); `thermal_rz.py` conduction + injection heat source running; first injection frame | `rodpump.py` FD wave equation with normal pump BC; first surface + downhole card that closes; static-load check passes | Repo + Vite/React/R3F scaffold; pump-jack geometry + animated linkage; dashboard layout with mock JSON; lock figure style (section 8) |
| **Sun 27** | Full cycle (inject 18 d → soak 10 d → produce 120 d); Marx–Langenheim check (A6); export frames + `cycle_timeseries.json` | All 9 pump BCs; card library generator (≥ 8 × 1,500 cards); Gibbs diagnostic round-trip (A6); render A3 grid | Well cutaway + rods + reservoir disc textured from P-A frames; card panel wired to P-B JSON |
| **Mon 28** | `wellbore.py` Ramey profile + mixture viscosity along tubing; hand T(z,t), μ(z,t) to P-B; A8 if time | Rod-fall float margin over the cycle; SPM glide path; A1 data; XGBoost classifier + confusion matrix (A5); O1 before/after (A7) | Phase timeline scrubber; recommendation card; render A1 final; **cut-line check at 21:00** |
| **Tue 29** | A9 Pareto (optional); proofread every caption and number | Polish; any failed class fixed | Record 75 s video; 4K stills; assemble PPT; everyone reviews |
| **Wed 30** | — | — | Submit before noon. Do not wait for evening portal load. |

---

## 5. Physics and ML specs: what to build and how simple it may be

Each module lists the **equation from the docs**, the **allowed PoC simplification**, and a **done-when** test. Units SI internally.

### 5.1 `params.py`: BGW-SYN-01 subset (registry IDs from Layer 3A §14)

```python
# Reservoir (P-01..P-18)            # Fluid (P-19..P-25)
TOP_PAY_M     = 1150                API, SG, RHO15 = 16, 0.959, 959.0
H_LAYERS_M    = [4, 3, 3]           WALTHER_A, WALTHER_B = 9.049, 3.362
KH_CONTRAST   = [1.0, 0.6, 1.4]     T_PP_C, T_NN_C = 24, 70
PHI, K_MD     = 0.19, 500           TAU0_PA, N0, A_HB, B_HB = 0.1, 0.7, 1.5, 1.0
T_R_C         = 50                  # Steam (P-34..P-37)
P_NEARWELL_KSC= 75                  STEAM_TPH, P_SURF_KSC, X_SURF = 3.1, 91, 0.65
RW_M, RE_M    = 0.108, 150          T_INJ_D, SOAK_RATIO = 18, 0.55
M_R, LAM_R    = 2.4e6, 2.5          # J/m3K, W/mK
M_OB, LAM_OB  = 2.3e6, 1.7          # cap/base
BETA_OVERRIDE = 2.0                 # ASSUMED closure (P-13), shows override
# Wellbore (P-26..P-31)             # Rods & pump (3B §6, assumed)
VIT_GRADE, K_VIT = "D", 0.01        ROD_R_M, TUB_RI_M = 0.0111, 0.038
T_SURF_GEO_C  = 30                  ROD_LEN_M = 1100; E_STEEL = 2.07e11; RHO_STEEL = 7850
```

### 5.2 `rheology.py` (T1-B, Layer 3A §6)

- **Walther (B.1):** `log10(log10(nu+0.7)) = A - B*log10(T_K)`, `mu = nu*rho` (cSt × g/cm³ → cP).
- **Density (MPMS 11.1):** `rho = rho15*exp(-a15*dT*(1+0.8*a15*dT))`, `a15 = 613.97/rho15**2`, dT from 15 °C.
- **Mixture mode for the tubing (B.7–B.8):** Pal–Rhodes below inversion, logistic switch at `f_inv = 0.60`, width `w = 0.05` (assumed). *This matters for A1*: early in the cycle, high condensate water cut makes the tubing fluid water-continuous and thin; float risk appears as water cut drops through inversion **and** the tubing cools.
- Herschel–Bulkley (B.2–B.5): implement, but the PoC only calls it at 50 s⁻¹, where it reduces to Walther by construction (B.4 anchor).

**Done when:** μ(50 °C) = 11,500 ± 500 cP; μ(100 °C) ≈ 300 cP; μ(200 °C) ≈ 11 cP. This reproduces Layer 3A Figure 4; re-plot it in house style as a bonus asset.

### 5.3 `thermal_rz.py` (T1-A, Layer 3A §5): simplified

**Keep:** 2-D axisymmetric r–z grid, implicit finite volume, cap and base conduction blocks, override allocation, residual heat carried across phases.
**Simplify for PoC:** single pressure per phase (so `T_sat` constant per phase); energy equation only (no water-mass equation A.3; water cut comes from the simple model in 5.4); latent heat through an enthalpy-to-temperature map with constant `p`.

- **Grid:** `Nr = 40` geometric from `r_w = 0.108 m` to `r_e = 150 m` (ratio ≈ 1.20); pay 10 cells (1 m); cap and base 12 cells each, geometric 0.25 m → 60 m.
- **Equation (A.1):** `dH/dt + (1/r) d/dr (r * rho_w * h_w * u) = div(lam grad T)`; backward Euler, upwind advection, `scipy.sparse.linalg.splu`. Δt = 1 h (5 min for 6 h after each phase change).
- **Injection (A.4–A.5):** `q_heat = mdot*(h_w(Tsat) + x_sf*L_v - h_w(T_R))`, `x_sf = 0.5` (from 3B Figure 3, VIT D ≈ 0.54) → ≈ 1.6 MW. Split by `w_k ∝ (kh)_k * exp(BETA*zeta_k)`; radial velocity `u_k(r) = mdot_k/(2*pi*r*h_k*rho_w)`. Use `iapws.IAPWS97` for `Tsat`, `h_l`, `h_v`.
- **Soak:** `u = 0`, conduction only.
- **Production:** reverse `u` with layer rates from 5.4 (`q_k` split by kh × mobility).
- **Outputs per hour:** `T[r,z]`, heated radius `r_h,k` (T − T_R ≥ 5 K), `T_in` (flow-weighted inner-cell T), `E_res`, heat budget.

**Done when:**
1. Energy closure `|eps|/E_sf < 1%` every step (the doc target is 0.5%; 1% is fine for the PoC).
2. **A6 check:** with `BETA = 0` and one 10 m layer, heated radius at 14 d / 21 d within 20% of **9.4 m / 11.3 m** (Marx–Langenheim, Layer 3A §5.6, eq. A.7–A.8). Plot grid vs analytical over time. That plot *is* asset A6.
3. Override visible: with `BETA = 2`, top-layer heated radius clearly larger than bottom.

**Export for A2:** matplotlib `pcolormesh` on a log-r axis, `inferno` colormap fixed at 50–310 °C, one frame every 6 h, phase label and day counter burned in → `ffmpeg -framerate 12 -i f%04d.png -pix_fmt yuv420p a2_thermal.mp4`. Also export raw frames as PNG for P-C's reservoir texture.

### 5.4 `inflow.py`: two-zone rate model (T1-C lite)

The full two-node pressure model (3A §7.1) waits for the finale. For the PoC:

- **Cold rate (C.2c, no TPG):** `q_c = 2*pi*kh*(p_c - p_wf)/(mu_c*(ln(re/rw) - 0.5))`. Tune kh to 18 bbl/d (section 2.3).
- **Heated rate:** Boberg–Lantz step-profile ratio (3A §7.6 check):
  `J_h/J_c = ln(re/rw) / ((mu_h/mu_c)*ln(rh/rw) + ln(re/rh))`, with `mu_h = mu(T̄_heated)` and `rh` from T1-A.
- **Water cut:** condensate return `f_w(t) = f_w0*exp(-t/tau_w) + f_w_inf`, `f_w0 = 0.85`, `tau_w = 20 d`, `f_w_inf = 0.25` (assumed; the fallback curve Layer 3A §7.3 keeps). Total liquid = oil / (1 − f_w).
- **Flowback:** optional. For the PoC, go straight to pumped after soak and note it on the timeline.

**Done when:** cycle-average oil ≈ 25–26 bbl/d with the base design; the rate curve peaks early and declines as `rh` and T̄ fall.

### 5.5 `wellbore.py` (T2-A, Layer 3B §4.5): production temperature and viscosity profile

- **Ramey upward (W.13):** `T(l) = T_ei(l) + (T_in - T_bh)*exp(-l/L_R) + g_G*L_R*(1 - exp(-l/L_R))`, `l` measured up from the pump, `g_G = (50-30)/1150 K/m`.
- **Relaxation length:** `L_R = w*c_p*R_total`. Calibrate it to Layer 3B's table: **VIT D ≈ 72 m per m³/d of liquid** (5 → 360 m, 10 → 720 m, 20 → 1,440 m); bare tubing ≈ 27 m per m³/d.
- **Viscosity profile:** `mu_mix(z,t) = rheology.mu_mixture(T(z,t), f_w(t))`.
- **Heater what-if (I9, for A1):** add `+ΔT ≈ 10 °C per kW at 5 m³/d` over the heater interval (3B §4.5 rule of thumb) or put `q'_heat` into the march.

**Done when:** 5 m³/d, `T_in = 150 °C`, VIT D gives wellhead ≈ 41–42 °C (3B table: 42 °C).

**A8 (Could):** injection steam-quality march in 10 m segments, `dx/dz = -q'/(w*L_v)`, `q' = (Tsat - T_ei)/(R_VIT + R_form)`, `R_form` from Hasan–Kabir (W.5). Reproduce the 3B Figure 3 bars (E 0.61, D 0.54, C 0.37, B 0.25, bare 0) within ±0.05.

### 5.6 `rodpump.py` + `kinematics.py` (T2-B / T3, Layer 2 §4; Gibbs predictive mode)

**Damped wave equation** (x downward from the polished rod, `u` downward displacement):

```
u_tt = a^2 u_xx - c(x) u_t + g (1 - rho_f/rho_s)          a = sqrt(E/rho_s) ≈ 5,135 m/s
c(x) = k_c * 2*pi*mu_mix(x) / (rho_s * A_r * ln(r_ti/r_r))  # annular Couette drag, per unit mass
```

- `k_c = 1.5` coupling/guide drag multiplier (assumed; label it).
- Explicit central difference (Everitt–Jennings form), Δx = 10 m, Δt ≤ Δx/a (use 1.5 ms):
  `u_i^{n+1} = [r²(u_{i+1}-2u_i+u_{i-1}) + 2u_i - (1 - cΔt/2)u_i^{n-1} + Δt² g_b] / (1 + cΔt/2)`, `r = aΔt/Δx`.
- **Top BC:** `u(0,t) = -y(t)`, where `y` is polished-rod position (up positive).
  - Beam unit: `y = S/2*(1 - cos(2*pi*N*t/60))` (sinusoid is fine for the PoC; API four-bar is a finale item).
  - Hydraulic long-stroke: trapezoidal velocity, accel 0.5 m/s², separate up/down speeds (this also gives O1 sectional control for A7).
- **Bottom BC (pump):** ghost node `u_{N+1} = u_{N-1} + 2Δx*F_p/(E*A_r)`, with `F_p` from the pump state machine below.
- **Polished-rod load:** `F_pr = E*A_r*(u_1 - u_0)/Δx`. **Carrier-bar separation (rod float):** if `F_pr < 0`, clip to 0 and flag the stroke.
- Run 3 strokes and keep the 3rd (periodic steady state).

**Pump load `F_p` by class** (fluid load `F_fl = (p_dis - p_int)*A_p`; `S_p` = plunger stroke from the previous cycle):

| Class | Rule |
|---|---|
| Normal | Upstroke `F_fl`; downstroke `0`; linear ramps over 3% of `S_p` (fluid compressibility) |
| Fluid pound | Downstroke holds `F_fl` for `(1-f)S_p`, `f ∈ [0.4, 0.8]`, then drops over 1% of `S_p` |
| Steam/gas interference | Same travel, but gradual polytropic drop over `(1-f)S_p` |
| Rod float / viscous overload | Normal pump; `mu_mix` 5–40 Pa·s so the top clips at 0 |
| Travelling-valve leak | Upstroke load decays `F_fl*(1 - k*τ)`, `k ∈ [0.2, 0.6]` |
| Standing-valve leak | Downstroke load stays at `α*F_fl`, `α ∈ [0.2, 0.5]`, decaying |
| Pump unseated | `F_p ≈ 0.05*F_fl` throughout |
| Rod parted | Rod length cut to break depth `∈ [0.3, 0.9]·L`; `F_p = 0` |
| Plunger tagging | Normal + negative impulse (`-0.3*F_fl`, 30 ms) at the bottom of the downstroke |

**Diagnostic mode (for A6):** implement the Gibbs surface-to-downhole transform (Fourier series or FD in space, Layer 2 E2). **Round-trip test:** simulate surface card from a known pump BC → invert → recovered downhole card within 5% RMS of the imposed one. Plot all three: this is A6's second panel.

**Done when:**
1. Static check: rods hanging still with the travelling valve closed → `F_pr = buoyant rod weight + F_fl` within 1% (buoyant weight ≈ 26 N/m × 1,100 m ≈ 29 kN).
2. Cards close; the normal card has the textbook parallelogram-with-wave shape.
3. Round-trip passes.

### 5.7 Rod-fall float margin and SPM glide path (F / O2 lite → A1)

Terminal fall speed of the rod string in the local fluid (Couette drag equals buoyant weight per metre):

```
v_fall(z) = (rho_s - rho_f)*g*A_r*ln(r_ti/r_r) / (k_c*2*pi*mu_mix(z))
          ≈ 5.13 / (k_c * mu_mix[Pa·s])   m/s   for 7/8" rods in 3½" tubing
v_down_max = pi*S*N/60  (beam, sinusoidal);  = 2*S*N/60 (hydraulic, constant speed)
float_margin(t) = 1 - v_down_max / v_fall_eff(t),  v_fall_eff = length-weighted harmonic mean over the string
```

- **Float onset forecast:** first `t` where `float_margin < 0` at the current SPM. Report the lead time from "now" (the demo "now" is where the recommendation fires).
- **SPM glide path (O2):** `N(t) = min(N_inflow(t), 0.9 * N_float(t))`, where
  `N_inflow = q_liq(t)/(A_p*S*eta_v*1440)` (pump-to-inflow matching, C17) and `N_float = 0.9*60*v_fall_eff/(pi*S)`.
  Choose plunger and stroke so `N_inflow` ≈ 5–6 SPM at peak and ≈ 2 at cut-off.
- **Cross-check against 5.6:** run the wave equation at 3 points on the cycle. The card must start clipping (min load 0) where `float_margin` crosses 0. Show those three cards as the A1 thumbnails.
- **What-ifs for A1 (two dashed lines):** (a) 6 kW heater → onset pushed out by X days (I9); (b) hydraulic long-stroke at the same rate → higher float tolerance (why OIL uses hydraulic units, Layer 2 §2).

**Tuning knob:** if float never or always happens, adjust (in this order) the declining liquid rate profile, the inversion point `f_inv`, and heater power, until onset lands around day 40–70 of production. Document the final knob values in the figure notes.

### 5.8 `ml/`: card library and classifier (D1 / I6 → A3, A5)

- **Generation:** 9 classes × ~1,500 cards, sampling SPM 2–8, S 2.5–4 m (beam) and hydraulic profiles, `mu_mix` 0.05–40 Pa·s, pump depth 900–1,150 m, `F_fl` from `p_int` 5–40 ksc, class-specific severities (table above), plus 2–5% load noise and ±1% position jitter.
- **Features:** resample the closed card to 128 points; complex contour `z = x + i*y` normalised to [0,1]²; first 12 Fourier-descriptor magnitudes; plus min/max/mean normalised load, area ratio vs ideal, downhole fillage estimate, upstroke/downstroke load slopes.
- **Model:** `xgboost.XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05)` with class weights.
- **Honest split:** train on `mu_mix ≤ 10 Pa·s` and depth ≤ 1,050 m; test on `mu_mix > 10` or depth > 1,050 m (extrapolation). Report macro-F1 and a per-class confusion matrix (row-normalised).
- **Caption:** "sim-to-sim; field validation requires OIL cards (DDDB / OIL surveys)".
- **Optional:** a small CNN on 64×64 card images for a second bar in the F1 chart.

**Done when:** macro-F1 on the held-out range is reported, whatever it is. A lower honest number with the right split beats 99.9% on a random split: OIL judges know card data.

### 5.9 `optim/`: O3 Pareto on an L0 proxy (A9, Could)

- **L0 generator per design** `(M_s ∈ 600–2,500 t, rate 2.5–3.3 t/h, x 0.60–0.70, soak ratio 0.3–0.8)`: Marx–Langenheim (heated radius and efficiency) → Boberg–Lantz average T (A.9–A.12) → J ratio → rate to `q_cut` → `N_p`, `L`, `SOR = M_s/N_p`.
- **Proxy:** 20k Sobol samples (`scipy.stats.qmc`) → XGBoost quantile (`reg:quantileerror`, α = 0.1/0.5/0.9).
- **Search:** `pymoo` NSGA-II, population 200, 150 generations; J1 = oil per cycle-day (O.0a), J2 = SOR.
- **Plot:** verified front, knee point (farthest from the line joining the extremes), and "OIL practice" (1,340 t, soak 0.55) as a marked point.
- **Label:** "stage v0 · L0 analytical proxy · synthetic well".

---

## 6. Front end: 3D twin and advisory dashboard (A4)

**Stack:** Vite + React + `@react-three/fiber` + `@react-three/drei` + `@react-three/postprocessing` (bloom on the hot reservoir) + Recharts or `visx` for cards and strips. Static JSON and PNG from `web/public/data`.

**Scene (left 60%):**
- Surface: procedural pump jack (walking beam, horsehead, crank, counterweight); rotation driven by the same `y(t)` P-B uses. Toggle: hydraulic long-stroke unit.
- Wellbore cutaway: casing → N₂ annulus → VIT tubing → rod string. **Compress depth visually** (broken axis or log-depth) and label "1,150 m".
- Rods: vertex colour by local stress from `u(x,t)` (P-B exports 20 depths × 200 samples per stroke) → a visible stress wave running down the string.
- Reservoir: disc or half-cylinder at the bottom, textured with P-A's `T(r,z)` frame revolved around the axis → glowing heated halo that grows during injection and fades in production. Steam particles down the tubing during injection.
- Timeline scrubber: Injection · Soak · (Flowback) · Pumped, with day counter.

**Panels (right 40%):**
1. Live surface + downhole card (current stroke, with faint previous-day overlay).
2. Tubing temperature and viscosity vs depth (from 5.5).
3. **Float margin gauge** (green → amber → red) + forecast "float in ~14 h at 4.2 SPM".
4. **Recommendation card (I13):** "Step SPM 4.2 → 3.4 over 6 h" · *why:* tubing μ up 38% in 24 h as water cut crossed inversion · *if unchanged:* rod float in ~14 h · confidence band · twin trust score · [Approve] [Simulate what-if].
5. Twin status strip: T1 · T2 · T3 · SE · D · O chips with maturity labels.

**Look:** dark UI, the doc palette (section 8). No OIL logo.

**Capture:**
- Stills at 3840×2160: `gl.setPixelRatio(2)` plus a "presentation mode" that hides the cursor and debug UI.
- Video: OBS at 1080p60, then `ffmpeg -crf 18`. Storyboard in section 8.

---

## 7. Data contracts (freeze Saturday noon)

```jsonc
// web/public/data/cycle_timeseries.json   (P-A + P-B → P-C, hourly)
{ "well":"BGW-SYN-01", "label":"synthetic · stage v0",
  "t_h":[...], "phase":[...], "q_oil_bpd":[...], "water_cut":[...],
  "r_h_m":{"L1":[...],"L2":[...],"L3":[...]}, "T_in_C":[...], "T_wh_C":[...],
  "mu_tubing_eff_Pas":[...], "float_margin":[...], "spm_current":[...], "spm_glide":[...],
  "events":[{"t_h":..., "type":"FLOAT_FORECAST","lead_h":14,"msg":"..."}] }

// web/public/data/thermal/f0000.png ... + thermal_meta.json
{ "r_edges_m":[...], "z_edges_m":[...], "cmap":"inferno", "T_min_C":50, "T_max_C":310,
  "frames":[{"file":"f0000.png","t_h":0,"phase":"injection"}, ...] }

// web/public/data/cards/{class}_{id}.json
{ "class":"rod_float", "spm":5.0, "mu_Pas":18.0, "unit":"beam",
  "surface":{"pos_m":[...200],"load_kN":[...200]}, "downhole":{"pos_m":[...],"load_kN":[...]},
  "flags":["carrier_bar_separation"] }

// web/public/data/rod_motion.json   (one stroke, for the stress wave)
{ "depth_m":[...20], "t_s":[...200], "u_m":[[...]], "stress_MPa":[[...]] }
```

P-C builds against hand-written mocks of exactly these shapes on day 1.

---

## 8. Assembly: figure style, slide mapping, video

**Figure style (every chart, all three people):**
- matplotlib `rcParams`: IBM Plex Sans (or Inter), 11 pt, no top/right spines, 300 dpi PNG plus SVG.
- Domain colours from the architecture docs: thermal `#A8561A`, wellbore/rods `#24588A`, surface/electrical `#546B1C`, AI/optimiser `#5A4A8C`, warning `#A3321F`.
- One caption line (section 2.2) on every figure.

**Slide mapping.** Check the 2026 SIH idea template; recent years used roughly Title · Idea · Technical approach · Feasibility · Impact · References.

| Slide | Put here |
|---|---|
| Idea / proposed solution | **A4 hero screenshot** (full bleed) + the causal chain strip (CSS heat → temperature field → rheology → inflow + rod drag → rod and pump → surface → control) |
| Technical approach | A10 architecture (compact) + 3 thumbnails: A2 frame, A3 grid, A1 chart; method names in small text (Gibbs wave eq., finite-volume r–z enthalpy, Walther/HB rheology, Ramey, XGBoost, NSGA-II) |
| Feasibility & viability | A6 validation (grid vs Marx–Langenheim; Gibbs round-trip) + A5 confusion matrix + "built on OIL's published parameters" mini-table + risks (no field data → synthetic-to-field swap by design, Layer 2 §11) |
| Impact & benefits | **A1 coupling chart** as the centrepiece ("predicts rod float ~14 h ahead and plans SPM before it happens") + A7 before/after + A9 Pareto if built. Every number labelled synthetic. |
| References | OIL Jul 2025 deck, PTI Apr 2026, Gibbs, Marx–Langenheim, Boberg–Lantz, Ramey, Hasan–Kabir, SPE CSP4, Sandia DDDB |

**Video storyboard (75 s)**, only if the template accepts a link:

| Time | Shot |
|---|---|
| 0–6 s | Title: "Baghewala Well-to-Surface Twin" |
| 6–22 s | Camera from pump jack down the cutaway to the reservoir; injection; halo grows with override (A2 texture) |
| 22–35 s | Soak → pumped; card panel appears; stress wave on rods |
| 35–55 s | Cooling; viscosity strip rises; gauge turns amber; "float in ~14 h" → Approve → glide path; card returns to normal |
| 55–68 s | Failure library grid → classifier matrix |
| 68–75 s | Architecture + "synthetic well · OIL parameters · stage v0" |

---

## 9. After submission: path to the finale (Dec 2026)

In order of what unblocks the most (Layer 2 §12, 3A §10, 3B §7):

1. **Data requests this week:** email Sandia for the DDDB; get SPE CSP4 through the library.
2. Upgrade T1-A to the full enthalpy + water-mass formulation (A.1–A.3); run SPE CSP4 Problem 1 as code verification.
3. T1-C two-node pressure model with FC-1; T2-A full injection mode + integrity outputs.
4. T2-B deviated-well friction; separate drag and friction (C2); I1 viscometer inversion.
5. P1 docker stack (Mosquitto + TimescaleDB + FastAPI) with the synthetic well publishing on real Sparkplug topics, so the live demo runs on the true data path.
6. SE: 64-member ensemble, ES-MDA; trust gate.
7. O3 at stage v0 on the real proxy (T1-D), then v1 once T2-B and T3 are coupled.

---

## 10. Risk list for the next 4 days

| Risk | Mitigation |
|---|---|
| T1-A implicit solver unstable or slow | Fall back to explicit with a CFL-limited step inside each hour, or temperature form without latent heat plus Marx–Langenheim heat placement. The animation still works. |
| Wave-equation card looks wrong | Run the static check first; check sign conventions (x down, u down, `F_pr = EA ∂u/∂x`); halve Δt. |
| Float never or always happens | Tuning order in 5.7; the goal is a *clear* crossing mid-cycle with documented knobs. |
| 3D scene eats all of P-C's time | Monday 21:00 cut-line: freeze 3D, finish the dashboard as a 2D layout with the A2 animation embedded. |
| Numbers inconsistent between slides | One `params.py`; every figure script reads it; P-A proofreads all captions on Tuesday. |
| Deadline earlier than 30 Sep | Confirm tonight. If earlier, ship A2 + A3 + A4-static + A10 only. |
