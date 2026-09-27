"""A3: synthetic dynamometer-card library, one representative card per class (T07, I6).
Representative = medoid of the class's kept beam-unit cards in normalised shape space.
Writes assets/A3_card_library.png/.svg. Needs out/cards.parquet."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from twin import pumpbc as PB  # noqa: E402
from twin import style as S  # noqa: E402

TITLES = {
    "normal": "Normal", "fluid_pound": "Fluid pound", "steam_gas_interference": "Steam or gas in the pump",
    "rod_float": "Rod float", "tv_leak": "Travelling-valve leak", "sv_leak": "Standing-valve leak",
    "unseated": "Pump unseated", "rod_parted": "Rod parted", "tagging": "Plunger tagging",
}


def _norm(pos, load):
    p = (pos - pos.min()) / max(np.ptp(pos), 1e-9)
    ld = (load - load.min()) / max(np.ptp(load), 1e-9)
    return np.concatenate([p, ld])


def medoid(g, max_n=300, seed=0):
    g = g.sample(min(len(g), max_n), random_state=seed)
    X = np.stack([_norm(np.asarray(a), np.asarray(b)) for a, b in zip(g.surf_pos, g.surf_load)])
    D = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    return g.iloc[int(D.sum(1).argmin())]


def main():
    S.apply()
    from ml.card_library import load_cards
    df = load_cards()
    df = df[df.keep]
    fig, axs = plt.subplots(3, 3, figsize=(14.0, 10.5))
    fig.subplots_adjust(left=0.06, right=0.985, top=0.885, bottom=0.075, hspace=0.62, wspace=0.22)
    reps = {}
    for ax, c in zip(axs.flat, PB.CLASSES):
        g = df[(df.cls == c) & (df.unit == 0)]
        r = medoid(g if len(g) else df[df.cls == c])
        reps[c] = r
        ax.plot(np.asarray(r.dh_pos), np.asarray(r.dh_load) / 1e3, color="#8A938E", lw=1.3, ls=(0, (4, 2.5)),
                label="at the pump")
        ax.plot(np.asarray(r.surf_pos), np.asarray(r.surf_load) / 1e3, color=S.COLORS["wellbore"], lw=1.6,
                label="at the surface")
        ax.set_title(TITLES[c], loc="left", fontsize=12, fontweight="semibold", pad=18)
        ax.text(0.0, 1.03, PB.CAUSES[c], transform=ax.transAxes, fontsize=9, color="#58625C", va="bottom")
        ax.text(1.0, 1.17, f"{r.N:.1f} strokes/min, pump at {r.depth:.0f} m", transform=ax.transAxes,
                fontsize=8.5, color="#6B7570", ha="right", va="bottom")
        ax.set_ylim(bottom=min(-2.0, float(np.min(r.dh_load)) / 1e3 - 2.0))
        ax.grid(True, color="#E1E6E2", lw=0.6)
        ax.set_axisbelow(True)
        ax.tick_params(labelsize=9)
    for ax in axs[-1]:
        ax.set_xlabel("Rod position (m)")
    for ax in axs[:, 0]:
        ax.set_ylabel("Load (kN)")
    h, lab = axs[0, 0].get_legend_handles_labels()
    fig.legend(h[::-1], lab[::-1], loc="upper right", bbox_to_anchor=(0.985, 0.985), ncol=2, fontsize=10)
    n_kept = len(df)
    fig.suptitle("Nine pump problems, simulated so the AI can learn them",
                 x=0.06, ha="left", fontsize=15, fontweight="semibold")
    fig.text(0.06, 0.935, f"One typical card per problem, out of {n_kept:,} simulated cards. Surface cards include 2–5 % sensor noise.",
             fontsize=10, color="#58625C")
    S.save(fig, "A3_card_library")
    plt.close(fig)
    print({c: (round(r.N, 2), round(r.mu, 3)) for c, r in reps.items()})


if __name__ == "__main__":
    main()
