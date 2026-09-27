"""A8: injection steam quality down the well by VIT grade (T14). Writes assets/A8_vit_quality.png/.svg."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from twin import injection as I  # noqa: E402
from twin import params as P  # noqa: E402
from twin import style as S  # noqa: E402

REF_3B = {"E": 0.61, "D": 0.54, "C": 0.37, "B": 0.25, "bare": 0.0}
COLS = {"E": "#24588A", "D": "#4F7FB0", "C": "#C98A45", "B": "#A8561A", "bare": "#A3321F"}


def main():
    S.apply()
    res = I.grades()
    fig, (a, b) = plt.subplots(1, 2, figsize=(14.0, 7.0), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(left=0.07, right=0.98, top=0.8, bottom=0.11, wspace=0.22)
    for g, r in res.items():
        lab = ({"E": "insulated tubing, grade E (best)", "D": "insulated tubing, grade D", "C": "insulated tubing, grade C", "B": "insulated tubing, grade B"}.get(g, "plain tubing"))
        a.plot(r["x"], r["z"], color=COLS[g], lw=2.2, label=lab)
        if r["z_condensed"] is not None:
            a.plot([0], [r["z_condensed"]], "o", color=COLS[g])
            a.annotate(f"all steam turned to water by {r['z_condensed']:.0f} m", (0, r["z_condensed"]), xytext=(0.05, r["z_condensed"] + 60),
                       fontsize=9, color=COLS[g])
    a.axhline(P.TOP_PAY_M, color="#8A938E", lw=0.8, ls="--")
    a.text(0.66, P.TOP_PAY_M - 12, "top of the oil sand, 1,150 m", fontsize=9, color="#58625C", ha="right")
    a.invert_yaxis()
    a.set_xlim(0, 0.7)
    a.set_xlabel("Steam quality (share still in vapour form)")
    a.set_ylabel("Depth (m)")
    a.legend(loc="lower left", fontsize=9, frameon=False)
    a.grid(True, color="#E1E6E2", lw=0.6)
    gs = ["E", "D", "C", "B", "bare"]
    y = np.arange(len(gs))
    ours = [res[g]["x_bh"] for g in gs]
    b.barh(y + 0.18, ours, height=0.34, color=[COLS[g] for g in gs], label="our model")
    b.barh(y - 0.18, [REF_3B[g] for g in gs], height=0.34, color="#C9CFCB", label="earlier design study")
    for k, g in enumerate(gs):
        loss = res[g]["heat_loss_W"] / 1e3
        b.text(ours[k] + 0.01, y[k] + 0.18, f"{ours[k]:.2f} ({loss:.0f} kW lost)", va="center", fontsize=9)
        b.text(REF_3B[g] + 0.01, y[k] - 0.18, f"{REF_3B[g]:.2f}", va="center", fontsize=9, color="#58625C")
    b.set_yticks(y, ["Grade E", "Grade D", "Grade C", "Grade B", "Plain"])
    b.invert_yaxis()
    b.set_xlim(0, 0.85)
    b.set_xlabel("Steam quality reaching the oil sand")
    b.legend(loc="lower right", fontsize=9, frameon=False)
    b.grid(True, axis="x", color="#E1E6E2", lw=0.6)
    fig.suptitle("Better tubing insulation gets more steam down to the oil", x=0.07, ha="left", fontsize=15, fontweight="semibold")
    fig.text(0.07, 0.885, f"{P.STEAM_KGS * 3.6:.1f} t/h of steam at {P.P_SURF_KSC:.0f} ksc, {100 * P.X_SURF:.0f} % quality at the wellhead, "
             "one day into injection. Well completion is assumed.", fontsize=10, color="#58625C")
    S.save(fig, "A8_vit_quality")
    plt.close(fig)


if __name__ == "__main__":
    main()
