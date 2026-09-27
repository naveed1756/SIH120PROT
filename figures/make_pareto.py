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
    ax.plot(fr.SOR_q50, fr.J1_q50, color=S.COLORS["ai"], lw=2.6, label="best trade-offs")
    ax.scatter([k["SOR_q50"]], [k["J1_q50"]], marker="*", s=320, color=S.COLORS["ai"], edgecolor="white", zorder=6,
               label="best balance")
    ax.scatter([op["SOR_L0"]], [op["J1_L0"]], marker="D", s=90, color=S.COLORS["thermal"], edgecolor="white", zorder=6,
               label="current practice")
    ax.set_xlabel("Steam-oil ratio (m³ of steam per m³ of oil, lower is better)")
    ax.set_ylabel("Oil per day of the cycle (bbl/day, higher is better)")
    ax.grid(True, color="#E1E6E2", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=9.5, frameon=False)
    cb = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.015)
    cb.set_label("Steam used per cycle (tonnes)")
    dj = 100 * (k["J1_q50"] / op["J1_L0"] - 1)
    ds = 100 * (k["SOR_q50"] / op["SOR_L0"] - 1)
    txt = (f"Best balance\n{k['M_s_t']:,.0f} t of steam at {k['rate_tph']:.1f} t/h,\nsoak {k['soak']:.1f} times the injection time\n\n"
           f"Compared with current practice\n({op['M_s_t']:,.0f} t, soak {op['soak']:.2f}):\n"
           f"{dj:+.1f} % oil per day\n{ds:+.1f} % steam per barrel\n\n"
           "The test well produces more than\nthe field average, so read the\ngains, not the absolute numbers.")
    fig.text(0.735, 0.8, txt, fontsize=10, va="top", color="#2F3532", linespacing=1.5)
    fig.suptitle("Searching for a better steam plan", x=0.08, ha="left", fontsize=15, fontweight="semibold")
    fig.text(0.08, 0.885, "Each grey dot is one possible plan (20,000 tried). The purple line holds the plans "
             "that cannot be beaten on both counts at once. Early estimate from a simplified cycle model.",
             fontsize=10, color="#58625C")
    S.save(fig, "A9_pareto")
    plt.close(fig)


if __name__ == "__main__":
    main()
