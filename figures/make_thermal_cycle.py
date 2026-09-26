"""A2: reservoir temperature field through one CSS cycle (T03/T04).

Reads out/thermal.npz (runs twin.scenario_cycle if missing) and writes
  out/thermal_frames/f%04d.png          one frame per 6 h (1600 x 900)
  assets/A2_thermal_cycle.mp4           ffmpeg -framerate 12 ... -crf 18
  assets/A2_end_injection.png / A2_end_soak.png / A2_day60.png  (+ .svg)
Run: python figures/make_thermal_cycle.py [--stills-only]
"""
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from twin import params as P  # noqa: E402
from twin import style as S  # noqa: E402

OUT = ROOT / "out"
FRAMES = OUT / "thermal_frames"
T_MIN, T_MAX = 50.0, 310.0
PHASE_COLOR = {"injection": S.COLORS["thermal"], "soak": "#8A938E", "production": S.COLORS["wellbore"]}
PHASE_LABEL = {"injection": "Steam injection", "soak": "Soak (well shut in)", "production": "Pumped production"}

_D = {}


def load():
    f = OUT / "thermal.npz"
    if not f.exists():
        from twin import scenario_cycle
        scenario_cycle.main()
    d = np.load(f)
    t = d["t_snap_h"]
    ph = d["phase_snap"]
    # phase boundaries (hours) from the hourly series
    hp, th = d["phase"], d["t_h"]
    t_inj_end = th[hp == "injection"].max()
    t_soak_end = th[hp == "soak"].max()
    return {"T": d["T_snap"], "t": t, "phase": ph, "r_edges": d["r_edges"], "z_edges": d["z_edges"],
            "t_inj_end": t_inj_end, "t_soak_end": t_soak_end, "t_end": th.max()}


def _init():
    S.apply()
    _D.update(load())


def depth_of(z):
    """Elevation above the base of the pay -> measured depth (m)."""
    return P.TOP_PAY_M + (sum(P.H_LAYERS_M) - z)


def draw(i, fig=None, caption=True):
    D = _D
    T = D["T"][i]
    t_h, phase = float(D["t"][i]), str(D["phase"][i])
    re, ze = D["r_edges"], D["z_edges"]
    rc = np.sqrt(re[:-1] * re[1:])
    zc = 0.5 * (ze[:-1] + ze[1:])
    if fig is None:
        fig = plt.figure(figsize=(16, 9), dpi=100)
    fig.clf()
    ax = fig.add_axes([0.07, 0.19, 0.80, 0.66])
    cax = fig.add_axes([0.895, 0.19, 0.015, 0.66])
    tl = fig.add_axes([0.07, 0.075, 0.80, 0.035])

    # extend the first cell column to the sandface so the plot starts at r_w
    rc = np.concatenate([[re[0]], rc])
    T = np.concatenate([T[:, :1], T], axis=1)
    m = ax.pcolormesh(rc, depth_of(zc), T, cmap="inferno", vmin=T_MIN, vmax=T_MAX, shading="gouraud",
                      rasterized=True)
    cs = ax.contour(rc, depth_of(zc), T, levels=[100.0, 200.0], colors="white", linewidths=0.8, alpha=0.7)
    ax.clabel(cs, fmt="%d °C", fontsize=9, inline=True)
    ax.set_xscale("log")
    ax.set_xlim(0.1, 150.0)
    H = sum(P.H_LAYERS_M)
    ax.set_ylim(depth_of(-15.0), depth_of(H + 15.0))
    # pay and layer boundaries
    tops = H - np.concatenate([[0.0], np.cumsum(P.H_LAYERS_M)])
    for k, z in enumerate(tops):
        ax.axhline(depth_of(z), color="#DDE3DF", lw=1.0 if k in (0, len(tops) - 1) else 0.6,
                   ls="-" if k in (0, len(tops) - 1) else (0, (4, 3)), alpha=0.8)
    for k in range(len(P.H_LAYERS_M)):
        zm = 0.5 * (tops[k] + tops[k + 1])
        ax.text(118, depth_of(zm), f"L{k+1}", color="#DDE3DF", fontsize=11, ha="right", va="center")
    ax.text(118, depth_of(H + 7.5), "cap rock", color="#AEB6B1", fontsize=10, ha="right", va="center")
    ax.text(118, depth_of(-7.5), "base rock", color="#AEB6B1", fontsize=10, ha="right", va="center")
    ax.add_patch(Rectangle((0.1, ax.get_ylim()[1]), P.RW_M - 0.1, ax.get_ylim()[0] - ax.get_ylim()[1],
                           color="#9FB8D6", lw=0, zorder=3))
    ax.text(0.104, depth_of(H + 13.0), "well", rotation=90, fontsize=9, color="#24588A", ha="center",
            va="center", zorder=4)
    ax.set_xlabel("Radius from the well (m, log scale)")
    ax.set_ylabel("Depth (m)")
    ax.set_xticks([0.1, 0.3, 1, 3, 10, 30, 100])
    ax.set_xticklabels(["0.1", "0.3", "1", "3", "10", "30", "100"])
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(m, cax=cax)
    cb.set_label("Temperature (°C)")
    cb.outline.set_visible(False)

    # header
    day = t_h / 24.0
    if phase == "injection":
        pday = day
    elif phase == "soak":
        pday = (t_h - D["t_inj_end"]) / 24.0
    else:
        pday = (t_h - D["t_soak_end"]) / 24.0
    fig.text(0.07, 0.935, PHASE_LABEL[phase], fontsize=24, fontweight="semibold", color=PHASE_COLOR[phase])
    fig.text(0.07, 0.885, f"cycle day {day:5.1f}   ·   {phase} day {pday:5.1f}", fontsize=14, color="#3A423D")
    fig.text(0.87, 0.935, "Reservoir temperature, BGW-SYN-01", fontsize=14, ha="right", color="#18201C",
             fontweight="semibold")
    fig.text(0.87, 0.895, f"r–z grid · {P.STEAM_KGS*3.6:.1f} t/h steam for {P.T_INJ_D:.0f} d · override β = "
             f"{P.BETA_OVERRIDE:g} (assumed closure)", fontsize=11, ha="right", color="#58625C")

    # phase timeline
    t_end = D["t_end"]
    segs = [(0.0, D["t_inj_end"], "injection"), (D["t_inj_end"], D["t_soak_end"], "soak"),
            (D["t_soak_end"], t_end, "production")]
    for a, b, p in segs:
        tl.add_patch(Rectangle((a / t_end, 0.0), (b - a) / t_end, 1.0, color=PHASE_COLOR[p],
                               alpha=0.9 if p == phase else 0.35, lw=0))
        tl.text((a + b) / 2 / t_end, 0.5, p, ha="center", va="center", fontsize=10, color="white")
    tl.axvline(t_h / t_end, color="#18201C", lw=2.2)
    tl.set_xlim(0, 1)
    tl.set_ylim(0, 1)
    tl.axis("off")
    if caption:
        S.add_caption(fig)
    return fig


def render_frame(i):
    fig = draw(i)
    fig.savefig(FRAMES / f"f{i:04d}.png", dpi=100)
    plt.close(fig)
    return i


def stills():
    D = _D
    t, ph = D["t"], D["phase"]
    idx = {
        "A2_end_injection": int(np.nonzero(ph == "injection")[0][-1]),
        "A2_end_soak": int(np.nonzero(ph == "soak")[0][-1]),
        "A2_day60": int(np.argmin(np.abs(t - (D["t_soak_end"] + 60 * 24)))),
    }
    for name, i in idx.items():
        fig = draw(i, fig=plt.figure(figsize=(12.8, 7.2)), caption=False)
        S.save(fig, name)
        plt.close(fig)
    return idx


def main(stills_only=False):
    _init()
    print("stills:", stills())
    if stills_only:
        return
    FRAMES.mkdir(parents=True, exist_ok=True)
    for f in FRAMES.glob("f*.png"):
        f.unlink()
    n = len(_D["t"])
    with Pool(processes=max(1, min(4, (__import__("os").cpu_count() or 1))), initializer=_init) as pool:
        for _ in pool.imap_unordered(render_frame, range(n), chunksize=8):
            pass
    S.ASSETS.mkdir(exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "12", "-i", str(FRAMES / "f%04d.png"),
           "-pix_fmt", "yuv420p", "-crf", "18", str(S.ASSETS / "A2_thermal_cycle.mp4")]
    subprocess.run(cmd, check=True)
    print(f"{n} frames -> assets/A2_thermal_cycle.mp4")


if __name__ == "__main__":
    main(stills_only="--stills-only" in sys.argv)
