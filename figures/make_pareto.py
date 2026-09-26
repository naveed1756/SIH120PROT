"""A9: CSS design Pareto front, stage v0 L0 analytical proxy (T15). Needs out/pareto.json and
out/pareto_samples.parquet (python -m optim.pareto). Writes assets/A9_pareto.png/.svg."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from twin import style as S  # noqa: E402


def main():
    S.apply()
    r = json.loads((ROOT / "out" / "pareto.json").read_text())
    smp = pd.read_parquet(ROOT / "out" / "pareto_samples.parquet").sample(4000, random_state=0)
    fr = pd.DataFrame(r["front"])
    k, op = r["knee"], r["oil_practice"]
    fig, ax = plt.subplots(figsize=(12.5, 7.4))
    fig.subplots_adjust(left=0.08, right=0.64, top=0.83, bottom=0.11)
    sc = ax.scatter(smp.SOR, smp.J1, c=smp.M_s_t, cmap="Greys", s=5, alpha=0.5, vmin=300, vmax=2600, lw=0)
    sub = fr.iloc[:: max(1, len(fr) // 25)]
    ax.errorbar(sub.SOR_q50, sub.J1_q50, xerr=np.clip([sub.SOR_q50 - sub.SOR_q10, sub.SOR_q90 - sub.SOR_q50], 0, None),
                yerr=np.clip([sub.J1_q50 - sub.J1_q10, sub.J1_q90 - sub.J1_q50], 0, None), fmt="none", ecolor=S.COLORS["ai"],
                alpha=0.45, lw=0.8, label="proxy P10–P90")
    ax.plot(fr.SOR_q50, fr.J1_q50, color=S.COLORS["ai"], lw=2.4, label="Pareto front (NSGA-II on the proxy median)")
    ax.scatter(fr.SOR_L0, fr.J1_L0, s=9, color="#2F3532", zorder=4, label="front designs re-checked on the L0 model")
    ax.scatter([k["SOR_q50"]], [k["J1_q50"]], marker="*", s=320, color=S.COLORS["ai"], edgecolor="white", zorder=6,
               label="knee point")
    ax.scatter([op["SOR_L0"]], [op["J1_L0"]], marker="D", s=90, color=S.COLORS["thermal"], edgecolor="white", zorder=6,
               label="OIL practice (1,340 t, soak 0.55)")
    ax.set_xlabel("SOR (m³ cold-water-equivalent steam per m³ oil) · lower is better")
    ax.set_ylabel("Oil per cycle-day (bbl/d, incl. soak + 5 d downtime) · higher is better")
    ax.grid(True, color="#E1E6E2", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9, frameon=False)
    cb = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.015)
    cb.set_label("steam mass M_s (t), Sobol samples")
    txt = (f"Knee design\n  M_s {k['M_s_t']:,.0f} t · {k['rate_tph']:.2f} t/h\n  x {k['x']:.2f} · soak ratio {k['soak']:.2f}\n"
           f"  J1 {k['J1_q50']:.1f} bbl/d · SOR {k['SOR_q50']:.2f}\n  cycle: {k['L_d']:.0f} d of production\n\n"
           f"OIL practice (L0)\n  J1 {op['J1_L0']:.1f} bbl/d · SOR {op['SOR_L0']:.2f}\n  cycle: {op['L_d']:.0f} d of production\n\n"
           f"Proxy (XGBoost quantile, 20k Sobol)\n  hold-out R²: J1 {r['proxy_J1']['r2_holdout']:.3f}, SOR {r['proxy_SOR']['r2_holdout']:.3f}\n"
           f"  P10–P90 coverage: {100 * r['proxy_J1']['p10_p90_coverage_holdout']:.0f} % / "
           f"{100 * r['proxy_SOR']['p10_p90_coverage_holdout']:.0f} % (target 80 %)\n\n"
           "Why SOR looks low: the DEMO effective\npermeability (6,600 mD) makes this well\n3–5× more productive than the field average;\n"
           "read the shape and the ranking, not the\nlevels. Cut-off on the CSS uplift < 8 bbl/d.")
    fig.text(0.735, 0.8, txt, fontsize=9.2, va="top", color="#2F3532", family="IBM Plex Sans")
    fig.suptitle("Steam design trade-off: oil per cycle-day vs steam-oil ratio", x=0.08, ha="left", fontsize=15,
                 fontweight="semibold")
    fig.text(0.08, 0.885, "stage v0 · L0 analytical proxy (Marx–Langenheim → Boberg–Lantz → T04 inflow ratio) · "
             "design space M_s 600–2,500 t, 2.5–3.3 t/h, x 0.60–0.70, soak 0.3–0.8", fontsize=10, color="#58625C")
    S.save(fig, "A9_pareto")
    plt.close(fig)


if __name__ == "__main__":
    main()
