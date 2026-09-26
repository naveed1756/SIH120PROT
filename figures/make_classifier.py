"""A5: card classifier results (T11). Reads out/classifier_report.json
(python -m ml.train_classifier). Writes assets/A5_confusion.png and assets/A5_f1_bars.png."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from twin import style as S  # noqa: E402

NAMES = {"normal": "Normal", "fluid_pound": "Fluid pound", "steam_gas_interference": "Steam / gas interf.",
         "rod_float": "Rod float", "tv_leak": "TV leak", "sv_leak": "SV leak", "unseated": "Pump unseated",
         "rod_parted": "Rod parted", "tagging": "Tagging"}


def main():
    S.apply()
    r = json.loads((ROOT / "out" / "classifier_report.json").read_text())
    cls = r["classes"]
    names = [NAMES[c] for c in cls]
    cm = np.array(r["confusion_test"], float)
    cmn = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    cmap = LinearSegmentedColormap.from_list("ai", ["#FFFFFF", "#D9D3EC", S.COLORS["ai"]])
    split = (f"Split by operating range, not random: trained on μ ≤ 10 Pa·s and pump depth ≤ 1,050 m "
             f"({r['n_train']:,} cards); tested on all other cards ({r['n_test']:,}, extrapolation)")

    fig, ax = plt.subplots(figsize=(11.5, 9.6))
    fig.subplots_adjust(left=0.19, right=0.97, top=0.86, bottom=0.2)
    ax.imshow(cmn, cmap=cmap, vmin=0, vmax=1)
    for i in range(len(cls)):
        for j in range(len(cls)):
            v = cmn[i, j]
            if v >= 0.005:
                ax.text(j, i, f"{100 * v:.0f}", ha="center", va="center", fontsize=10,
                        color="white" if v > 0.55 else "#2A2F2C")
    ax.set_xticks(range(len(cls)), names, rotation=35, ha="right")
    ax.set_yticks(range(len(cls)), names)
    ax.set_xlabel("Predicted class")
    ax.set_ylabel("True class")
    for sp in ax.spines.values():
        sp.set_visible(False)
    fig.suptitle(f"Card classifier on held-out operating range: macro-F1 {r['macro_f1_test']:.2f}",
                 x=0.03, ha="left", fontsize=15, fontweight="semibold")
    fig.text(0.03, 0.905, split + f"\nRow-normalised (% of true class). 5-fold CV inside the training range: "
             f"macro-F1 {r['cv5_macro_f1_train_range']['mean']:.2f} ± {r['cv5_macro_f1_train_range']['std']:.2f}. "
             "Features: Fourier descriptors, shape stats, Gibbs downhole fillage. XGBoost.",
             fontsize=9.5, color="#58625C", va="center")
    S.save(fig, "A5_confusion")
    plt.close(fig)

    f1 = np.array([r["f1_test_per_class"][c] for c in cls])
    o = np.argsort(f1)
    fig, ax = plt.subplots(figsize=(11.0, 6.2))
    fig.subplots_adjust(left=0.2, right=0.96, top=0.8, bottom=0.14)
    ax.barh(np.arange(len(cls)), f1[o], color=[S.COLORS["ai"] if v >= 0.8 else "#9A8FC4" for v in f1[o]], height=0.62)
    for k, v in enumerate(f1[o]):
        ax.text(v + 0.01, k, f"{v:.2f}  (n = {r['n_test_per_class'][cls[o[k]]]})", va="center", fontsize=9.5)
    ax.set_yticks(np.arange(len(cls)), [names[i] for i in o])
    ax.axvline(r["macro_f1_test"], color="#2F3532", lw=1, ls="--")
    ax.text(r["macro_f1_test"], len(cls) - 0.4, f" macro-F1 {r['macro_f1_test']:.2f}", fontsize=9.5)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("F1 on the held-out operating range")
    fig.suptitle("Per-class F1: where the card shapes overlap", x=0.03, ha="left", fontsize=15, fontweight="semibold")
    fig.text(0.03, 0.87, split, fontsize=9.5, color="#58625C")
    S.save(fig, "A5_f1_bars")
    plt.close(fig)


if __name__ == "__main__":
    main()
