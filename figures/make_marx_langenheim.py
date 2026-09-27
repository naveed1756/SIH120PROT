"""A6a: T1-A grid heated area vs Marx-Langenheim over 21 days of injection (T03).
Writes assets/A6a_marx_langenheim.png/.svg."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from twin import params as P  # noqa: E402
from twin import style as S  # noqa: E402
from twin import thermal_rz as TR  # noqa: E402


def main():
    S.apply()
    r = TR.marx_langenheim_check(t_end_d=21.0)
    d = r["t_s"] / P.DAY_S
    err = 100.0 * (r["A_grid"] / r["A_ml"] - 1.0)

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.86, bottom=0.16)
    ax.plot(d, r["A_ml"], color="#3A423D", lw=1.6, ls=(0, (5, 3)), label="textbook formula (Marx–Langenheim)")
    ax.plot(d, r["A_grid"], color=S.COLORS["thermal"], lw=2.2, label="our reservoir simulator")
    for day, tgt in ((14, 276.0), (21, 403.0)):
        i = int(np.argmin(np.abs(d - day)))
        ax.plot([day], [r["A_grid"][i]], "o", ms=6, color=S.COLORS["thermal"], mec="white", mew=1.2, zorder=5)
        ax.annotate(f"day {day}: {r['A_grid'][i]:.0f} m² vs {tgt:.0f} m² ({err[i]:+.0f} %)",
                    xy=(day, r["A_grid"][i]), xytext=((10.6, 452) if day == 21 else (3.0, 330)),
                    fontsize=9.5, color="#18201C", arrowprops=dict(arrowstyle="-", color="#6B7570", lw=0.8))
    ax.set_xlim(0, 21.5)
    ax.set_ylim(0, 480)
    ax.set_xlabel("Days of steam injection")
    ax.set_ylabel("Heated area (m²)")
    ax.grid(True, color="#D3D9D4", lw=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9.5)

    ins = fig.add_axes([0.66, 0.24, 0.28, 0.24])
    ins.axhspan(-20, 20, color=S.COLORS["surface"], alpha=0.10, lw=0)
    ins.plot(d[d >= 1], err[d >= 1], color=S.COLORS["thermal"], lw=1.4)
    ins.axhline(0, color="#6B7570", lw=0.8)
    ins.set_ylim(-25, 25)
    ins.set_xlim(0, 21.5)
    ins.set_title("difference (%), shaded band = ±20 %", fontsize=8.5, color="#3A423D", loc="left")
    ins.tick_params(labelsize=8)

    fig.suptitle("Our reservoir simulator matches the textbook heated area", x=0.11, ha="left",
                 fontsize=13, fontweight="semibold")
    ax.set_title(f"Test case: one 10 m layer, steam at {P.ML_T_S_C:.0f} °C, {r['q_heat_W']/1e6:.1f} MW of heat for 21 days",
                 fontsize=9, color="#58625C", loc="left")
    path = S.save(fig, "A6a_marx_langenheim")
    plt.close(fig)
    print(path, "errors at 14/21 d:", err[np.argmin(np.abs(d - 14))], err[np.argmin(np.abs(d - 21))])


if __name__ == "__main__":
    main()
