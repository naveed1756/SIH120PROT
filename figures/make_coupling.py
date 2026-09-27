"""A1: the CSS -> SRP coupling chart (T09). Five strips on one production-day axis plus
three wave-equation card thumbnails from the cross-check.
Needs out/cycle.parquet + out/thermal.npz (python -m twin.scenario_cycle) and
out/float_glide.parquet + notes + crosscheck_cards.npz (python -m twin.float_glide).
Writes assets/A1_coupling.png/.svg and assets/A1_coupling_notes.md.

Strip 1 deviation (recorded in DEVINSTRUCT.md): the spec's r_h (T - T_R >= 5 K) keeps growing
during production because conduction carries the 5 K front outward, so it cannot show the
halo cooling. The strip plots the hot-zone radius at T >= T_NN_C (70 C, the Newtonian
threshold of the rheology) instead, and the text box states the r_h values."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from twin import params as P  # noqa: E402
from twin import style as S  # noqa: E402
from twin import thermal_rz as TR  # noqa: E402

OUT = ROOT / "out"
LAYER_COLS = ["#A8561A", "#C98A45", "#E0B47C"]
GREY = "#6B7570"


def _radius_where(g, prof, thresh):
    above = np.nonzero(prof >= thresh)[0]
    if above.size == 0:
        return g.r_edges[0]
    i = above[-1]
    if i == len(prof) - 1:
        return g.r_edges[-1]
    x0, x1 = np.log(g.rc[i]), np.log(g.rc[i + 1])
    f = (prof[i] - thresh) / (prof[i] - prof[i + 1])
    return float(np.exp(x0 + f * (x1 - x0)))


def hot_radius(t0_h, thresh=P.T_NN_C):
    """Per-layer outermost radius with T >= thresh, from the 6-hourly snapshots of production."""
    g = TR.build_grid()
    d = np.load(OUT / "thermal.npz")
    m = d["t_snap_h"] >= t0_h - 1e-9
    days = (d["t_snap_h"][m] - t0_h) / 24.0
    r = np.array([[_radius_where(g, Ti[g.layer_of_row == k].max(0), thresh) for k in range(3)]
                  for Ti in d["T_snap"][m]])
    return days, r


def inversion_day(day, f_w):
    i = np.nonzero(np.asarray(f_w) < P.F_INV)[0]
    return float(np.asarray(day)[i[0]]) if i.size else None


def main():
    S.apply()
    cyc = pd.read_parquet(OUT / "cycle.parquet")
    pr = cyc[cyc.phase == "production"]
    t0 = float(pr.t_h.iloc[0])
    s = pd.read_parquet(OUT / "float_glide.parquet")
    notes = json.loads((OUT / "float_glide_notes.json").read_text())
    cc = np.load(OUT / "crosscheck_cards.npz")
    d_hot, r_hot = hot_radius(t0)
    on, now, w_on = notes["onset_day_analytic"], notes["now_day"], notes["onset_day_wave_equation"]
    d_inv = inversion_day(s.day, s.f_w)
    day = s.day.values
    xmax = float(day.max())

    fig = plt.figure(figsize=(16.0, 9.0))
    L, R = 0.075, 0.925
    tops = np.linspace(0.735, 0.085, 6)
    h = (tops[0] - tops[-1]) / 5
    axs = [fig.add_axes([L, tops[i + 1] + 0.012, R - L, h - 0.024]) for i in range(5)]
    for a in axs[1:]:
        a.sharex(axs[0])
    for a in axs:
        a.set_xlim(0, xmax)
        a.grid(True, axis="x", color="#E1E6E2", lw=0.6)
        a.set_axisbelow(True)
        a.tick_params(labelsize=9)
        a.axvline(on, color=S.COLORS["warn"], lw=1.0, ls=(0, (3, 2)), zorder=1)
        a.axvline(now, color=S.COLORS["ai"], lw=1.0, zorder=1)
    for a in axs[:-1]:
        plt.setp(a.get_xticklabels(), visible=False)
    axs[-1].set_xlabel("Days of pumping (after 18 days of steam and 10 days of soak)", fontsize=10)

    def ylab(a, t):
        a.set_ylabel(t, fontsize=9.5, labelpad=6)

    # 1 reservoir hot zone
    a = axs[0]
    for k in range(3):
        a.plot(d_hot, r_hot[:, k], color=LAYER_COLS[k], lw=1.8, label=f"layer {k + 1}")
    ylab(a, "Hot zone\nradius (m)")
    a.legend(loc="upper right", ncol=3, fontsize=8.5, frameon=False)
    rh_end = pr[["r_h_L1", "r_h_L2", "r_h_L3"]].iloc[-1].values
    a.text(0.005, 0.06, f"The zone hotter than {P.T_NN_C:.0f} °C shrinks as the reservoir cools",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 2 temperatures
    a = axs[1]
    a.plot(day, s.T_in_C, color=S.COLORS["thermal"], lw=1.8, label="at the pump")
    a.plot(day, s.T_wh_C, color=S.COLORS["wellbore"], lw=1.8, label="at the surface")
    ylab(a, "Temperature\n(°C)")
    a.legend(loc="upper right", ncol=2, fontsize=8.5, frameon=False)
    a.text(0.005, 0.06, "As the flow slows, the oil loses more heat on its way up",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 3 viscosity + water cut
    a = axs[2]
    a.semilogy(day, s.mu_eff_Pas, color=S.COLORS["wellbore"], lw=1.8, label="tubing viscosity")
    ylab(a, "Viscosity\n(Pa·s)")
    b = a.twinx()
    b.plot(day, 100 * s.f_w, color=GREY, lw=1.2, ls="--", label="water cut")
    b.axhline(100 * P.F_INV, color=GREY, lw=0.6, ls=":")
    b.set_ylim(0, 100)
    b.set_ylabel("Water cut (%)", fontsize=9.5, color=GREY)
    b.tick_params(labelsize=9, colors=GREY)
    b.spines["right"].set_visible(True)
    if d_inv is not None:
        a.axvline(d_inv, color=GREY, lw=0.9, ls=":")
        a.annotate(f"day {d_inv:.0f}: water cut drops below {100 * P.F_INV:.0f} %, the mix turns thick",
                   xy=(d_inv, float(np.interp(d_inv, day, s.mu_eff_Pas))), xytext=(d_inv + 30, 1.6e-4),
                   fontsize=8.5, color="#3E4642", arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
    h1, l1 = a.get_legend_handles_labels()
    h2, l2 = b.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, loc="lower right", ncol=2, fontsize=8.5, frameon=False)
    a.set_ylim(1e-4, 1e2)
    a.text(0.25, 0.86, "Cooler tubing and less water make the fluid thousands of times thicker",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 4 float margin
    a = axs[3]
    lo = min(-0.4, float(s.margin_base.min()) - 0.05)
    a.axhspan(lo, 0, color=S.COLORS["warn"], alpha=0.08, lw=0)
    a.axhline(0, color=S.COLORS["warn"], lw=0.8)
    a.plot(day, s.margin_base, color="#2F3532", lw=1.6, label=f"current practice ({notes['N_base_spm']:.1f} strokes/min)")
    a.plot(day, s.margin_glide, color=S.COLORS["ai"], lw=2.4, label="AI speed plan")
    a.fill_between(day, s.margin_base, 0, where=s.margin_base < 0, color=S.COLORS["warn"], alpha=0.35, lw=0)
    a.set_ylim(lo, 1.05)
    ylab(a, "Rod-float\nmargin")
    a.legend(loc="lower left", ncol=2, fontsize=8.5, frameon=False)
    a.annotate(f"Rod float forecast 14 hours ahead (day {on:.0f})\ndetailed rod model: day {w_on:.0f}",
               xy=(now, 0.0), xytext=(now - 62, -0.30), fontsize=8.8,
               color=S.COLORS["ai"], fontweight="semibold",
               arrowprops=dict(arrowstyle="->", color=S.COLORS["ai"], lw=1.0))
    a.plot([w_on], [0], marker="v", color=S.COLORS["warn"], ms=6, zorder=5)
    a.text(0.005, 0.55, "Below zero, the pump pulls the rods down faster than they can fall",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 5 SPM
    a = axs[4]
    a.plot(day, s.N_base, color="#2F3532", lw=1.4, label="current practice")
    a.plot(day, s.N_inflow, color=S.COLORS["surface"], lw=6.0, alpha=0.35, solid_capstyle="butt",
           label="speed that matches inflow")
    a.plot(day, s.N_float, color=S.COLORS["warn"], lw=1.3, label="float limit")
    a.plot(day, s.N_float_heater, color=S.COLORS["warn"], lw=1.2, ls="--", label="float limit with 6 kW heater")
    a.plot(day, s.N_glide, color=S.COLORS["ai"], lw=2.2, label="AI speed plan")
    a.set_ylim(0, 1.6 * notes["N_base_spm"])
    ylab(a, "Pump speed\n(strokes/min)")
    a.legend(loc="upper center", ncol=5, fontsize=8.5, frameon=False, bbox_to_anchor=(0.55, 1.0))
    a.text(0.12, 0.30, "The plan follows inflow and stays below the float limit",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # thumbnails
    cc_notes = notes["crosscheck"]
    tw, th, ty = 0.10, 0.105, 0.765
    xs = [axs[0].transData.transform((c["day"], 0))[0] for c in cc_notes]
    xs = [fig.transFigure.inverted().transform((x, 0))[0] for x in xs]
    cx = list(xs)
    for i in range(len(cx) - 2, -1, -1):
        cx[i] = min(cx[i], cx[i + 1] - tw - 0.012)
    cx = [min(c, R - tw / 2 - (len(cx) - 1 - i) * (tw + 0.012)) for i, c in enumerate(cx)]
    for i, (c, x0, xc) in enumerate(zip(cc_notes, xs, cx)):
        ta = fig.add_axes([xc - tw / 2, ty, tw, th])
        pos, raw = cc[f"surf_pos_{i}"][0], cc[f"surf_load_raw_{i}"][0] / 1e3
        ta.plot(pos, raw, color="#B9C0BC", lw=0.8)
        ta.plot(pos, np.maximum(raw, 0), color=S.COLORS["wellbore"], lw=1.3)
        ta.axhline(0, color=S.COLORS["warn"] if c["float"] else "#B9C0BC", lw=0.7)
        ta.set_xticks([]); ta.set_yticks([])
        for sp in ta.spines.values():
            sp.set_visible(True); sp.set_color("#C9CFCB"); sp.set_linewidth(0.6)
        state = "rods floating" if c["float"] else "normal"
        ta.set_title(f"Day {c['day']:.0f}: {state}", fontsize=8, pad=2,
                     color=S.COLORS["warn"] if c["float"] else "#3E4642")
        ta.text(0.02, 0.04, f"min {c['min_load_raw_kN']:+.1f} kN", transform=ta.transAxes, fontsize=7, color=GREY)
        fig.add_artist(plt.Line2D([xc, x0], [ty, tops[0] - 0.012], color="#B9C0BC", lw=0.6,
                                  transform=fig.transFigure))
    fig.text(cx[0] - tw / 2 - 0.012, ty + th / 2, "Simulated pump cards at the current speed\n"
             "(grey part = where the load would go below zero)",
             fontsize=8.5, color=GREY, va="center", ha="right")

    fig.suptitle("As the steam heat fades, the oil thickens and the rods start to float",
                 x=L, ha="left", y=0.975, fontsize=16, fontweight="semibold")
    fig.text(L, 0.925, "One steam cycle on the test well. The twin sees the problem coming and slows the pump in time. "
             "A 6 kW heater or a hydraulic unit with a slower downstroke would also avoid it.",
             fontsize=10, color="#58625C")
    S.save(fig, "A1_coupling")
    plt.close(fig)
    write_notes(notes, d_inv, r_hot, d_hot)


def write_notes(n, d_inv, r_hot, d_hot):
    cc = "\n".join(f"| {c['day']:.1f} | {c['mu_eff_Pas']:.2f} | {c['min_load_raw_kN']:+.2f} | "
                   f"{c['load_range_kN']:.1f} | {'yes' if c['float'] else 'no'} |" for c in n["crosscheck"])
    heater = 'no rod float in the cycle' if n['onset_day_heater_6kW'] is None else 'day %.0f' % n['onset_day_heater_6kW']
    hyd = 'no rod float in the cycle' if n['onset_day_hydraulic_S6_df0.6'] is None else 'day %.0f' % n['onset_day_hydraulic_S6_df0.6']
    txt = f"""# Notes on A1 (steam heat to rod float)

{S.CAPTION}

## Settings used
- Pumping period: {n['T_PROD_D']:.0f} days (raised from 120, because rod float only starts around day 125).
- Water share of the produced liquid: starts at {100 * n['FW0']:.0f} %, settles at {100 * n['FW_INF']:.0f} %,
  halfway there in about {n['TAU_W_D'] * 0.69:.0f} days.
- The oil and water mix turns thick when the water share drops below {100 * n['F_INV']:.0f} %
  (day {d_inv:.1f} of pumping). Changing this point between 50 and 80 % did not move the rod float date.
- Reservoir permeability is set to {P.K_MD:,.0f} mD so that the unheated well makes about 18 bbl/day.
  This is a demo setting, not a Baghewala estimate.
- We aimed for rod float to start between day 30 and day 80. With these settings it starts later
  (around day 125), because the well produces enough liquid to keep the tubing warm for most of the cycle.

## Pump
- Plunger {n['plunger_in']}" (the largest standard size), 3 m stroke.
- Current practice: a fixed {n['N_base_spm']:.1f} strokes/min, which matches the inflow at peak production.
  The fastest downstroke speed is then {n['v_down_base_mps']:.2f} m/s.

## When rod float starts (days of pumping)
| Case | Start of rod float |
|---|---|
| Current practice, quick estimate (fall speed of the rods) | day {n['onset_day_analytic']:.1f} |
| Current practice, full rod simulation (surface load drops below zero) | day {n['onset_day_wave_equation']:.1f} |
| With a 6 kW downhole heater | {heater} |
| Hydraulic unit, 6 m stroke, slower downstroke ({n['hydraulic_N_spm']:.1f} strokes/min) | {hyd} |
| AI speed plan | no rod float (lowest margin {n['glide_margin_min']:.2f}) |

The two estimates for current practice differ by about {abs(n['onset_disagreement_days']):.0f} days. We show both.
The quick estimate treats the rods as one rigid piece. The full simulation also includes the rods
stretching and the fluid load at the pump, and the extra bounce on the downstroke makes the rods
float a few days sooner.

The dashboard's "now" is day {n['now_day']:.1f}, 14 hours before the quick estimate says rod float begins.

## Rod simulation check (current practice)
| Day | Tubing viscosity (Pa·s) | Lowest surface load (kN) | Load range (kN) | Rods floating? |
|---|---|---|---|---|
{cc}

## About the top strip
The top strip shows how far out the oil is still above {P.T_NN_C:.0f} °C in each layer (end of pumping:
{', '.join(f'layer {k + 1} {r_hot[-1, k]:.1f} m' for k in range(3))}). The edge of the "warm by 5 °C" zone keeps
creeping outward as heat spreads, so it would not show the hot zone shrinking.
"""
    (ROOT / "assets" / "A1_coupling_notes.md").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
