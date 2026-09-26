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
    axs[-1].set_xlabel("Pumped-production day (after injection 18 d + soak 9.9 d; flowback phase not modelled in the PoC, pumping starts after soak)", fontsize=10)

    def ylab(a, t):
        a.set_ylabel(t, fontsize=9.5, labelpad=6)

    # 1 reservoir hot zone
    a = axs[0]
    for k in range(3):
        a.plot(d_hot, r_hot[:, k], color=LAYER_COLS[k], lw=1.8, label=f"L{k + 1} ({P.H_LAYERS_M[k]:.0f} m)")
    ylab(a, "Hot-zone\nradius (m)")
    a.legend(loc="upper right", ncol=3, fontsize=8.5, frameon=False)
    rh_end = pr[["r_h_L1", "r_h_L2", "r_h_L3"]].iloc[-1].values
    a.text(0.005, 0.06, f"1 · Reservoir: radius where T ≥ {P.T_NN_C:.0f} °C shrinks as the halo cools "
           f"(the 5 K conduction front r_h still creeps out: {rh_end.min():.0f}–{rh_end.max():.0f} m at the end)",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 2 temperatures
    a = axs[1]
    a.plot(day, s.T_in_C, color=S.COLORS["thermal"], lw=1.8, label="pump intake T_in")
    a.plot(day, s.T_wh_C, color=S.COLORS["wellbore"], lw=1.8, label="wellhead (Ramey, VIT)")
    ylab(a, "Temperature\n(°C)")
    a.legend(loc="upper right", ncol=2, fontsize=8.5, frameon=False)
    a.text(0.005, 0.06, "2 · Wellbore: falling rate → the tubing loses more heat before the fluid reaches surface",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 3 viscosity + water cut
    a = axs[2]
    a.semilogy(day, s.mu_eff_Pas, color=S.COLORS["wellbore"], lw=1.8, label="tubing μ_eff (mean over string)")
    ylab(a, "μ_eff\n(Pa·s)")
    b = a.twinx()
    b.plot(day, 100 * s.f_w, color=GREY, lw=1.2, ls="--", label="water cut")
    b.axhline(100 * P.F_INV, color=GREY, lw=0.6, ls=":")
    b.set_ylim(0, 100)
    b.set_ylabel("Water cut (%)", fontsize=9.5, color=GREY)
    b.tick_params(labelsize=9, colors=GREY)
    b.spines["right"].set_visible(True)
    if d_inv is not None:
        a.axvline(d_inv, color=GREY, lw=0.9, ls=":")
        a.annotate(f"day {d_inv:.0f}: water cut < {100 * P.F_INV:.0f} % → emulsion inverts to oil-continuous (thick)",
                   xy=(d_inv, float(np.interp(d_inv, day, s.mu_eff_Pas))), xytext=(d_inv + 30, 1.6e-4),
                   fontsize=8.5, color="#3E4642", arrowprops=dict(arrowstyle="-", color=GREY, lw=0.7))
    h1, l1 = a.get_legend_handles_labels()
    h2, l2 = b.get_legend_handles_labels()
    a.legend(h1 + h2, l1 + l2, loc="lower right", ncol=2, fontsize=8.5, frameon=False)
    a.set_ylim(1e-4, 1e2)
    a.text(0.25, 0.86, "3 · Fluid: cooler tubing + inverted emulsion → tubing viscosity rises by four orders of magnitude",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 4 float margin
    a = axs[3]
    lo = min(-0.4, float(s.margin_base.min()) - 0.05)
    a.axhspan(lo, 0, color=S.COLORS["warn"], alpha=0.08, lw=0)
    a.axhline(0, color=S.COLORS["warn"], lw=0.8)
    a.plot(day, s.margin_base, color="#2F3532", lw=1.6, label=f"current practice: N = {notes['N_base_spm']:.1f} SPM fixed")
    a.plot(day, s.margin_glide, color=S.COLORS["ai"], lw=2.4, label="AI glide path")
    a.fill_between(day, s.margin_base, 0, where=s.margin_base < 0, color=S.COLORS["warn"], alpha=0.35, lw=0)
    a.set_ylim(lo, 1.05)
    ylab(a, "Float\nmargin")
    a.legend(loc="lower left", ncol=2, fontsize=8.5, frameon=False)
    a.annotate(f"now (day {now:.1f}): rod float forecast 14 h ahead\nonset day {on:.1f} (analytic) · "
               f"wave equation: day {w_on:.1f}", xy=(now, 0.0), xytext=(now - 62, -0.30), fontsize=8.8,
               color=S.COLORS["ai"], fontweight="semibold",
               arrowprops=dict(arrowstyle="->", color=S.COLORS["ai"], lw=1.0))
    a.plot([w_on], [0], marker="v", color=S.COLORS["warn"], ms=6, zorder=5)
    a.text(0.005, 0.55, "4 · Rods: margin = 1 − v_down / v_fall   (< 0: the carrier bar outruns the falling rods)",
           transform=a.transAxes, fontsize=8.5, color="#3E4642")

    # 5 SPM
    a = axs[4]
    a.plot(day, s.N_base, color="#2F3532", lw=1.4, label="current practice")
    a.plot(day, s.N_inflow, color=S.COLORS["surface"], lw=6.0, alpha=0.35, solid_capstyle="butt",
           label="N_inflow (pump = inflow)")
    a.plot(day, s.N_float, color=S.COLORS["warn"], lw=1.3, label="N_float (rod-fall limit)")
    a.plot(day, s.N_float_heater, color=S.COLORS["warn"], lw=1.2, ls="--", label="N_float with 6 kW heater")
    a.plot(day, s.N_glide, color=S.COLORS["ai"], lw=2.2, label="AI glide path N_glide (= N_inflow here)")
    a.set_ylim(0, 1.6 * notes["N_base_spm"])
    ylab(a, "Pump speed\n(SPM)")
    a.legend(loc="upper center", ncol=5, fontsize=8.5, frameon=False, bbox_to_anchor=(0.55, 1.0))
    a.text(0.12, 0.30, "5 · AI: N_glide = min(N_inflow, 0.9·N_float), advised before the forecast onset",
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
        state = "rods float: load clipped" if c["float"] else "normal card"
        ta.set_title(f"day {c['day']:.0f} · {state}", fontsize=8, pad=2,
                     color=S.COLORS["warn"] if c["float"] else "#3E4642")
        ta.text(0.02, 0.04, f"min {c['min_load_raw_kN']:+.1f} kN", transform=ta.transAxes, fontsize=7, color=GREY)
        fig.add_artist(plt.Line2D([xc, x0], [ty, tops[0] - 0.012], color="#B9C0BC", lw=0.6,
                                  transform=fig.transFigure))
    fig.text(cx[0] - tw / 2 - 0.012, ty + th / 2, "Wave-equation cross-check at baseline SPM\n"
             "surface cards (blue = measured, clipped at 0;\ngrey = rod tension below zero → carrier-bar separation)",
             fontsize=8.5, color=GREY, va="center", ha="right")

    fig.suptitle("Steam heat decays → oil thickens in the tubing → rods float: forecast and prevented",
                 x=L, ha="left", y=0.975, fontsize=16, fontweight="semibold")
    fig.text(L, 0.925, f"BGW-SYN-01, one CSS cycle · plunger {notes['plunger_in']}\" · stroke {P.STROKE_M:.0f} m · "
             f"heater what-if (6 kW): {'no float in the cycle' if notes['onset_day_heater_6kW'] is None else 'onset day %.0f' % notes['onset_day_heater_6kW']}"
             f" · hydraulic what-if (S 6 m, slow downstroke): "
             f"{'no float in the cycle' if notes['onset_day_hydraulic_S6_df0.6'] is None else 'onset day %.0f' % notes['onset_day_hydraulic_S6_df0.6']}",
             fontsize=10, color="#58625C")
    S.save(fig, "A1_coupling")
    plt.close(fig)
    write_notes(notes, d_inv, r_hot, d_hot)


def write_notes(n, d_inv, r_hot, d_hot):
    cc = "\n".join(f"| {c['day']:.1f} | {c['mu_eff_Pas']:.2f} | {c['min_load_raw_kN']:+.2f} | "
                   f"{c['load_range_kN']:.1f} | {'yes' if c['float'] else 'no'} |" for c in n["crosscheck"])
    txt = f"""# A1_coupling · notes

Synthetic reference well BGW-SYN-01 · OIL published parameters (Jul 2025) + literature · not field data · prototype v0

## Knob values (T09 order: T_PROD_D / water cut → F_INV → heater)
- T_PROD_D = {n['T_PROD_D']:.0f} d (was 120; onset at ~day 125 fell outside a 120-day cycle)
- Water cut: FW0 = {n['FW0']}, FW_INF = {n['FW_INF']}, TAU_W_D = {n['TAU_W_D']} d (scanned, unchanged)
- F_INV = {n['F_INV']} (scanned 0.5–0.8: no effect on onset, unchanged)
- Heater baseline: 0 kW (a heater only delays onset)
- K_MD = {P.K_MD:.0f} mD (DEMO, see DEVINSTRUCT.md)
- **The 30–80 day onset target is not reached with the listed knobs.** Onset stays inside days
  10–150, so this is recorded, not blocked. Reason: the DEMO K_MD gives high liquid rates that
  keep the tubing warm for most of the cycle.

## Pump and speed
- Plunger {n['plunger_in']}" (largest standard size); N_inflow at the production peak = {n['N_inflow_peak_spm']:.2f} SPM
  (5–6 SPM band not reachable with standard sizes; closest chosen)
- Current practice: N = {n['N_base_spm']:.2f} SPM fixed, v_down,max = {n['v_down_base_mps']:.3f} m/s

## Onset days (production days)
| Case | Onset |
|---|---|
| Baseline, analytic float margin | {n['onset_day_analytic']:.2f} |
| Baseline, wave equation (min polished-rod load < 0) | {n['onset_day_wave_equation']:.2f} |
| Disagreement | {n['onset_disagreement_days']:+.1f} d (**> 3 d, reported per spec**) |
| 6 kW heater | {'none in cycle' if n['onset_day_heater_6kW'] is None else '%.2f' % n['onset_day_heater_6kW']} |
| Hydraulic S = 6 m, down_fraction 0.6, N = {n['hydraulic_N_spm']:.2f} SPM (v_down {n['hydraulic_v_down_mps']:.3f} m/s) | {'none in cycle' if n['onset_day_hydraulic_S6_df0.6'] is None else '%.2f' % n['onset_day_hydraulic_S6_df0.6']} |
| AI glide path | none (minimum margin {n['glide_margin_min']:.2f}) |

Demo "now" = day {n['now_day']:.3f} (14 h before the analytic onset).
Emulsion inversion crossing (water cut < {P.F_INV:.0%}): day {d_inv:.1f}.

Why the two onsets differ: the analytic margin uses the terminal fall speed of a rigid string
against the peak carrier-bar speed; the wave equation also carries the elastic stress wave and
the pump's fluid load, whose downstroke overshoot unloads the polished rod a few days earlier.

## Wave-equation cross-check (baseline N, T05 viscosity profile)
| Day | μ_eff (Pa·s) | min polished-rod load (kN) | load range (kN) | float |
|---|---|---|---|---|
{cc}

## Strip 1 deviation
The spec asks for r_h (T − T_R ≥ 5 K). That front keeps moving outward during production by
conduction, so it cannot show the halo cooling. Strip 1 shows the hot-zone radius at
T ≥ T_NN = {P.T_NN_C:.0f} °C per layer (end of production: {', '.join(f'L{k + 1} {r_hot[-1, k]:.1f} m' for k in range(3))});
the r_h values are stated in the strip text.
"""
    (ROOT / "assets" / "A1_coupling_notes.md").write_text(txt, encoding="utf-8")


if __name__ == "__main__":
    main()
