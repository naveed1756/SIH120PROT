# Baghewala Well-to-Surface Twin · PoC

Proof-of-concept for SIH 2026 PS 26120 (Oil India Limited): a thin physics + ML slice
on the synthetic reference well **BGW-SYN-01**, built only to produce visual assets for
the idea PPT. All data is synthetic, generated from OIL's published field-level figures
and literature priors. Not field data.

- Build brief: `CLAUDE.md` (wins over `plan.md`)
- Progress, decisions, tuned knobs: `PROGRESS.md`
- Architecture: `docs/` (Layer 2, Layer 3A, Layer 3B HTML)

## Setup (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
python figures\make_viscosity.py
```

macOS/Linux: `python3 -m venv .venv && . .venv/bin/activate`, then the same commands.

Every figure is produced by `figures/make_<asset>.py` and written to `assets/` as PNG + SVG.
