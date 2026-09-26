# DEVINSTRUCT · developer guide and tracker

Read this first if you are joining the project. It says what every file and folder is
for, how the pieces connect, how to run and extend things, and where the build stands.
It is updated at the end of every build part.

| File | Role |
|---|---|
| `CLAUDE.md` | The build brief. Task list T00–T16, done-when tests, rules. **Wins over everything else.** |
| `PROGRESS.md` | Machine-resumable log: task status, tuned knobs, decisions, deferred items, blockers. |
| `DEVINSTRUCT.md` | This file: human guide + repo map + tracker. |
| `README.md` | One-screen summary and setup. |

---

## 1. What we are building (30-second version)

A thin physics + ML slice of the Baghewala Well-to-Surface Twin, run on one synthetic
well (BGW-SYN-01), whose only job is to produce **assets for the SIH idea PPT**: stills,
two MP4s and a web dashboard with a 3D well. It is not the full architecture in `docs/`.

The story every asset serves (the "causal chain" of Layer 2):

```
CSS steam heat ─► reservoir temperature field ─► oil viscosity (rheology)
   ─► inflow rate + tubing cooling ─► viscous drag on rods ─► rod float
   ─► AI: forecast float, recommend SPM glide path
```

All numbers are **synthetic**: our models, driven by OIL's published field-level figures
and literature priors. Every figure carries the caption in `twin/style.py::CAPTION`.

---

## 2. Setup and everyday commands

Windows PowerShell, from the repo root (`prototype\`):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest                                  # all done-when tests
python figures\make_viscosity.py        # any figures\make_*.py writes to assets\
python -m twin.scenario_cycle           # full CSS cycle -> out\ (needed by make_thermal_cycle.py)
python figures\make_thermal_cycle.py    # A2 frames + mp4 (needs ffmpeg on PATH)
```

macOS / Linux: `python3 -m venv .venv && . .venv/bin/activate`, then the same.
Web (from Part 5 on): `cd web; npm install; npm run dev`.

---

## 3. How code gets into this folder (sync)

The build runs in a cloud workspace (the shell on this Windows machine does not start),
so commits are moved here as a **git bundle**, one file per build part:

```powershell
# first time only (the folder already has Part 1 files; this adopts the history)
git init -b main
git fetch .sync\poc.bundle main
git reset --hard FETCH_HEAD

# every later part (or simply: powershell -ExecutionPolicy Bypass -File tools\sync.ps1)
git pull --ff-only .sync\poc.bundle main
```

`reset --hard` only touches tracked files; your own untracked files are left alone.
If you edit files locally, commit them before pulling. `.sync/` is git-ignored.
Planned upgrade: a GitHub repo (push from the workspace, `git pull` here). See PROGRESS.md.

Commit style: `T0x: short summary`, one commit per task or per part.

---

## 4. Repository map

Status: ✅ done · 🟡 in progress · ⬜ not started. Tier from CLAUDE.md §6.

### Root
| Path | What it is |
|---|---|
| `requirements.txt` | Python deps (numpy, scipy, iapws, matplotlib, pandas, pyarrow, xgboost, scikit-learn, pytest; pymoo only for T15) |
| `pytest.ini`, `conftest.py` | Test config; `conftest.py` puts the root on `sys.path` so `import twin` works |
| `tools/sync.ps1` | Windows helper: adopts/pulls the `.sync\poc.bundle` commits (first run inits git) |
| `.gitignore`, `.gitattributes` | Ignores venv, caches, `out/`, node, sync bundles, OS/editor files; line-ending and binary rules |

### `docs/` (provided, read-only)
| Path | What it is |
|---|---|
| `solution-architecture-layer2.html` | Whole architecture: modules, phases, innovations I1–I16 |
| `solution-architecture-layer3a.html` | T1-A thermal (A.x), T1-B rheology (B.x), T1-C inflow (C.x, FC-1), BGW-SYN-01 card §9, registry §14 |
| `solution-architecture-layer3b.html` | T2-A wellbore (W.x), O3 designer, reference-well additions §6 |
| `plan.md` | Human plan for the 4-day PoC (CLAUDE.md wins where they differ) |

### `twin/` (physics)
| Path | Task | Status | What it does |
|---|---|---|---|
| `params.py` | T01 | ✅ | **Single source of every number.** Each constant tagged with registry ID (P-xx) and evidence label |
| `style.py` | T01 | ✅ | Figure style, domain colours, `CAPTION`, `save()` → `assets/*.png/.svg` |
| `fonts/` | T01 | ✅ | IBM Plex Sans TTFs (OFL) so figures render identically everywhere |
| `rheology.py` | T02 | ✅ | Walther viscosity, density, water viscosity (IAPWS), Pal–Rhodes mixture, Herschel–Bulkley, cp, λ |
| `steam.py` | T03 | ✅ | IAPWS-97 saturation properties and liquid enthalpy, tabulated for vectorised use (pressures in Pa **absolute**) |
| `thermal_rz.py` | T03 | ✅ | 2-D r–z enthalpy grid (39 × 34 cells): implicit conduction + liquid advection, latent-heat condensation front, Jäger–Kačur fallback solver, heat budget, r_h / T_bar / T_in, Marx–Langenheim check (`marx_langenheim_check`) |
| `inflow.py` | T04 | ✅ | Cold IPR, Boberg–Lantz step ratio per layer, water-cut curve, `k_md_for_cold_rate()` for the DEMO knob |
| `scenario_cycle.py` | T04 | ✅ | `python -m twin.scenario_cycle`: one full cycle (~30 s) → `out/thermal.npz` + `out/cycle.parquet`; prints the checkpoint summary |
| `wellbore.py` | T05 | ⬜ | Ramey tubing temperature + mixture viscosity profile |
| `kinematics.py` | T06 | ⬜ | Polished-rod motion: beam (sinusoid) and hydraulic (trapezoid) |
| `rodpump.py` | T06 | ⬜ | Damped wave equation for the rod string → surface/downhole cards |
| `pumpbc.py` | T07 | ⬜ | Pump boundary condition per failure class (9 classes) |
| `gibbs.py` | T08 | ⬜ | Surface → downhole card inversion (Should) |
| `float_glide.py` | T09 | ⬜ | Rod-fall float margin, float-onset forecast, SPM glide path |

### `ml/`, `optim/`
| Path | Task | Status | What it does |
|---|---|---|---|
| `ml/card_library.py` | T07 | ⬜ | Generates 9 × 1,500 synthetic dynamometer cards |
| `ml/features.py` | T11 | ⬜ | Fourier descriptors + geometric card features |
| `ml/train_classifier.py` | T11 | ⬜ | XGBoost card classifier, split by operating range |
| `optim/l0_cycle.py`, `optim/pareto.py` | T15 | ⬜ | Analytical cycle model + NSGA-II Pareto (Could) |

### `figures/`, `tests/`, outputs
| Path | What it is |
|---|---|
| `figures/make_*.py` | One script per asset; deterministic; reads `params.py` and module outputs. `make_thermal_cycle.py` renders 592 frames in parallel + ffmpeg (~75 s); `--stills-only` for the 3 stills |
| `tests/test_*.py` | Done-when checks from CLAUDE.md §5, one file per module. `tests/conftest.py` runs the full cycle once per session (shared fixture `cycle`) |
| `out/` | Intermediate data (npz, parquet, raw frames). **Git-ignored**, regenerate with scripts |
| `assets/` | Final PPT assets (PNG + SVG, MP4) + `assets/README.md` manifest (T16) |
| `web/` | Vite + React + three.js dashboard (T13); `web/public/data/` holds T12 exports |

---

## 5. Conventions (short form of CLAUDE.md §3)

- SI units inside code; convert only when plotting/exporting (°C, cP, bbl/d, ksc, kN).
- No magic numbers in modules: add a constant to `params.py` with registry ID + evidence label.
- Every figure: `style.apply()` at the start, `style.save(fig, name)` at the end (adds the caption).
- Never loosen a done-when threshold. Two honest failed attempts → stop, log in PROGRESS.md "Blocked".
- Tuning knobs only where CLAUDE.md names them; record final values in PROGRESS.md and figure notes.
- Classifier split by operating range, never random.

---

## 6. Build tracker

| Part | Tasks | Status | Outputs |
|---|---|---|---|
| 1 | T00 setup · T01 params/style · T02 rheology | ✅ | `S1_viscosity` |
| 2 | T03 thermal grid · T04 inflow + cycle | ✅ (K_MD awaits confirmation) | `A6a_marx_langenheim`, `A2_thermal_cycle.mp4`, A2 stills |
| 3 | T05 wellbore · T06 rod string · T07 pump BCs + card library | ⬜ | `S2_tubing_profiles`, `A3_card_library` |
| 4 | T09 float + glide path · T12 web exports | ⬜ | `A1_coupling` (+ notes) |
| 5 | T13 dashboard · T16 manifest | ⬜ | `A4_dashboard` |
| 6 | T08 · T10 · T11 · T14 · T15 (Should/Could) | ⬜ | `A6b`, `A7`, `A5`, `A8`, `A9` |

## 7. Changelog
- **Part 1 (26 Sep):** repo skeleton, params, style, rheology + tests (21 pass), S1 figure.
- **Git (26 Sep):** repo initialised; `.gitignore`/`.gitattributes`; this file; docs committed.
- **Part 2 (26 Sep):** `steam.py`, `thermal_rz.py`, `inflow.py`, `scenario_cycle.py`; 34 tests pass (~35 s); assets A6a, A2 (mp4 + 3 stills). K_MD = 6,600 mD DEMO (above the 5,000 mD guard; see PROGRESS.md Blocked). CSS average 53 bbl/d (outside 20–40 note band).
