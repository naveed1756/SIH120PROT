# PROGRESS

Repo root = `D:\naveed\others\SIH2026\PS26120\prototype` (the folder holding CLAUDE.md).
Built and tested in the cloud workspace (Python 3.11.15, venv), then synced to the folder.

## Status
| Task | Status | Key numbers | Notes |
|---|---|---|---|
| T00 | done | pytest: 0 collected, no import errors | layout per CLAUDE.md 3.4; `conftest.py` puts root on sys.path |
| T01 | done | 3 tests pass | IBM Plex Sans bundled in `twin/fonts/` (OFL) so figures look the same on any machine |
| T02 | done | μ_oil 50/100/200 °C = 11.69 / 0.302 / 0.0109 Pa·s; HB = Walther at 50 s⁻¹ to 2e-16; mixture ratio μ(0.50)/μ(0.70) at 50 °C = 3,975 | 18 tests pass. Two deviations from the brief, see Decisions (monotone test, log-space blend). Asset S1 done |
| T03 | todo | | |
| T04 | todo | | |
| T05 | todo | | |
| T06 | todo | | |
| T07 | todo | | |
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
- K_MD = … mD (cold rate … bbl/d) — T04
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

## Deferred
- Live-oil (GOR) correction, Refutas diluent blending (B.9), aquathermolysis multiplier: not needed for the PoC assets.

## Blocked
- (none) — see Decisions for `docs/`.

## Assets produced
- `assets/S1_viscosity.png/.svg` — placeholder rheology prior (T02)
