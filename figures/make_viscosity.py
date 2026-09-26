"""S1: placeholder rheology prior (T02). Writes assets/S1_viscosity.png/.svg."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from twin import params as P  # noqa: E402
from twin import rheology as R  # noqa: E402
from twin import style as S  # noqa: E402


def main():
    S.apply()
    T = np.linspace(25.0, 300.0, 600)
    mu_cp = R.mu_oil(T) / P.CP_PAS

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.88, bottom=0.16)

    # context bands (neutral, recessive)
    ax.axvspan(25.0, 27.0, color=S.COLORS["warn"], alpha=0.12, lw=0)
    ax.axvspan(57.0, 85.0, color=S.COLORS["ai"], alpha=0.10, lw=0)
    ax.text(25.6, 2.2, "pour point\n21–27 °C", fontsize=8.5, color="#3A423D", va="bottom")
    ax.text(71.0, 2.2e5, "T$_{NN}$ band 57–85 °C\n(literature)", fontsize=8.5,
            color="#3A423D", ha="center", va="top")

    # Herschel-Bulkley apparent viscosity at other shear rates (shows shear thinning)
    for gd, ls in ((5.0, (0, (4, 3))), (500.0, (0, (1, 2)))):
        ax.plot(T, R.mu_app(T, gd) / P.CP_PAS, color=S.COLORS["thermal"], lw=1.0,
                ls=ls, alpha=0.8, label=f"Herschel–Bulkley apparent, {gd:g} s$^{{-1}}$")

    # main Walther curve at the OIL reference shear rate
    ax.plot(T, mu_cp, color=S.COLORS["thermal"], lw=2.2, label="Walther, 50 s$^{-1}$ (reference)")

    # OIL anchor 10,000-13,000 cP at 50 C
    ax.errorbar([50.0], [11_500.0], yerr=[[1_500.0], [1_500.0]], fmt="o", ms=7,
                color=S.COLORS["surface"], mec="white", mew=1.5, capsize=4, lw=1.8, zorder=5)
    ax.annotate("OIL: 10,000–13,000 cP at 50 °C, 50 s$^{-1}$", xy=(50, 11_500), xytext=(92, 22_000),
                fontsize=9.5, color="#18201C",
                arrowprops=dict(arrowstyle="-", color="#6B7570", lw=0.8))
    # assumed slope anchor
    ax.plot([100.0], [R.mu_oil(100.0) / P.CP_PAS], "o", ms=7, mfc="white",
            mec=S.COLORS["thermal"], mew=1.8, zorder=5)
    ax.annotate("assumed anchor: ~300 cP at 100 °C", xy=(100, 302), xytext=(125, 900),
                fontsize=9.5, color="#18201C",
                arrowprops=dict(arrowstyle="-", color="#6B7570", lw=0.8))
    for t in (200.0, 300.0):
        v = R.mu_oil(t) / P.CP_PAS
        ax.plot([t], [v], "o", ms=4, color=S.COLORS["thermal"])
        ax.text(t, v * 1.5, f"{v:.1f} cP", fontsize=8.5, ha="center", color="#3A423D")

    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], loc="upper right", fontsize=9)
    ax.set_yscale("log")
    ax.set_xlim(25, 300)
    ax.set_ylim(1, 3e5)
    ax.set_xlabel("Temperature (°C)")
    ax.set_ylabel("Viscosity (cP, log scale)")
    ax.grid(True, which="major", color="#D3D9D4", lw=0.6)
    ax.set_axisbelow(True)
    fig.suptitle("Placeholder rheology prior (OIL anchor at 50 °C)", x=0.11, ha="left",
                 fontsize=13, fontweight="semibold")
    ax.set_title("Dead oil · Walther (3A B.1) with Herschel–Bulkley shear dependence (B.2–B.4); "
                 "only the 50 °C point is OIL data", fontsize=9, color="#58625C", loc="left")
    path = S.save(fig, "S1_viscosity")
    plt.close(fig)
    print(path)


if __name__ == "__main__":
    main()
