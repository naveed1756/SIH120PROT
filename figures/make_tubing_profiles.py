"""S2: tubing temperature and mixture viscosity against depth at production days 5, 30, 60, 100
(T05, Ramey W.13 through VIT). Needs out/cycle.parquet. Writes assets/S2_tubing_profiles.png/.svg."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from twin import params as P  # noqa: E402
from twin import style as S  # noqa: E402
from twin import wellbore as W  # noqa: E402

DAYS = [5, 30, 60, 100]
SHADES = ["#E0B47C", "#C98A45", "#A8561A", "#6B3510"]


def main():
    S.apply()
    cyc = pd.read_parquet(ROOT / "out" / "cycle.parquet")
    pr = cyc[cyc.phase == "production"]
    d = (pr.t_h.values - pr.t_h.values[0]) / 24.0
    fig, (a, b) = plt.subplots(1, 2, figsize=(13.0, 7.2), sharey=True)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.82, bottom=0.2, wspace=0.08)
    z = W.depth_grid()
    a.plot(W.T_ei(z), z, color="#8A938E", lw=1.2, ls=":", label="natural rock temperature")
    for day, col in zip(DAYS, SHADES):
        r = pr.iloc[int(np.argmin(np.abs(d - day)))]
        p = W.profile(r.T_in, r.q_liq * P.DAY_S, r.f_w)
        lab = f"day {day}: {r.q_liq * P.DAY_S:.0f} m³/day, {100 * r.f_w:.0f} % water"
        a.plot(p["T_C"], p["z_m"], color=col, lw=2, label=lab)
        b.semilogx(p["mu_Pas"], p["z_m"], color=col, lw=2, label=f"day {day}")
    a.invert_yaxis()
    a.set_xlabel("Tubing temperature (°C)")
    a.set_ylabel("Depth (m)")
    b.set_xlabel("Viscosity of the oil and water mix (Pa·s, log scale)")
    b.set_xlim(1e-4, 30)
    b.axvspan(1.0, 30, color=S.COLORS["warn"], alpha=0.06, lw=0)
    b.text(1.2, 1060, "thick enough\nto slow the rods", fontsize=9, color=S.COLORS["warn"])
    for ax in (a, b):
        ax.grid(True, color="#E1E6E2", lw=0.6)
        ax.set_axisbelow(True)
    a.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, fontsize=8.5, frameon=False)
    b.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, fontsize=8.5, frameon=False)
    fig.suptitle("The oil cools on its way up the tubing", x=0.07, ha="left",
                 fontsize=15, fontweight="semibold")
    fig.text(0.07, 0.885, "As the flow slows and the water share drops, the fluid around the rods gets much thicker",
             fontsize=10, color="#58625C")
    S.save(fig, "S2_tubing_profiles")
    plt.close(fig)


if __name__ == "__main__":
    main()
