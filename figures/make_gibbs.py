"""A6b: Gibbs round trip (T08). A surface card is simulated from a known pump boundary
condition, inverted back to the pump with twin.gibbs, and compared with the imposed card.
Writes assets/A6b_gibbs_roundtrip.png/.svg."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from twin import gibbs as G  # noqa: E402
from twin import params as P  # noqa: E402
from twin import pumpbc as PB  # noqa: E402
from twin import rodpump as RP  # noqa: E402
from twin import style as S  # noqa: E402

CASES = [("normal", 0.5, "Normal pump"), ("fluid_pound", 0.5, "Fluid pound (fill 0.6)"),
         ("fluid_pound", 10.0, "Fluid pound, thick oil (informative)")]
L, N, STROKE = P.ROD_LEN_M, 5.0, 3.0


def main():
    S.apply()
    F_fl = PB.fluid_load(20.0, P.T06_TEST_PLUNGER_IN, L)[0]
    n = int(L / P.DX_ROD_M)
    fig, axs = plt.subplots(1, 3, figsize=(15.0, 5.6))
    fig.subplots_adjust(left=0.055, right=0.985, top=0.76, bottom=0.14, wspace=0.18)
    errs = []
    for ax, (cls, mu, title) in zip(axs, CASES):
        r = RP.simulate(np.array([L]), N, STROKE, np.array([mu]), PB.CID[cls], F_fl, fill=0.6, n_nodes=n)
        pos, Fp = G.downhole_card(r["surf_pos"][0], r["surf_load_raw"][0], L, N, mu, n_nodes=n)
        e = G.rms_error(Fp, r["dh_load"][0])
        errs.append(e)
        close = lambda a: np.append(a, a[0])  # noqa: E731
        ax.plot(close(r["surf_pos"][0]), close(r["surf_load_raw"][0]) / 1e3, color=S.COLORS["wellbore"], lw=1.6,
                label="surface card (simulated input)")
        ax.plot(close(r["dh_pos"][0]), close(r["dh_load"][0]) / 1e3, color="#8A938E", lw=3.2, alpha=0.55,
                label="pump card imposed")
        ax.plot(close(pos), close(Fp) / 1e3, color=S.COLORS["ai"], lw=1.3, ls=(0, (4, 2)),
                label=f"pump card recovered · RMS {100 * e:.1f} % of range")
        ax.set_title(f"{title}\nμ = {mu:g} Pa·s, N = {N:g} SPM, S = {STROKE:g} m, rods {L:.0f} m", loc="left", fontsize=11)
        if r["float"][0]:
            ax.text(0.02, 0.03, "surface load below 0 = rods float (unclipped model load shown)", transform=ax.transAxes,
                    fontsize=8.5, color=S.COLORS["warn"])
        ax.set_xlabel("Position (m)")
        ax.grid(True, color="#E1E6E2", lw=0.6)
        ax.set_axisbelow(True)
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), fontsize=8.5, frameon=False, ncol=1)
    axs[0].set_ylabel("Load (kN)")
    fig.subplots_adjust(bottom=0.27)
    fig.suptitle("Diagnostic mode: the pump card recovered from the surface card (Gibbs wave equation)",
                 x=0.055, ha="left", fontsize=15, fontweight="semibold")
    fig.text(0.055, 0.895, "Surface card simulated from a known pump condition, then inverted by marching the same damped "
             "wave equation down the rods (Everitt–Jennings finite differences). Done-when: RMS ≤ 5 % at μ ≤ 1 Pa·s.",
             fontsize=10, color="#58625C")
    S.save(fig, "A6b_gibbs_roundtrip")
    plt.close(fig)
    print({c[0] + "_" + str(c[1]): round(100 * e, 2) for c, e in zip(CASES, errs)})


if __name__ == "__main__":
    main()
