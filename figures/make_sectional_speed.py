"""A7: O1 sectional speed, before / after (T10).

Hydraulic unit (S = HYD_S_M, N = HYD_N_SPM), T05 tubing viscosity profile. First the day on
which this unit's card starts to clip at down_fraction 0.5 is found (1-day scan); the demo day
is DAYS_AFTER later (persistent onset: every later card clips). At that day, down_fraction is raised in 0.01 steps, same N, until the
minimum polished-rod load exceeds 5 % of the peak load, subject to the unit's acceleration
limit (kinematics.max_hydraulic_spm). Writes assets/A7_sectional_speed.png/.svg + notes json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from twin import float_glide as FG  # noqa: E402
from twin import kinematics as K  # noqa: E402
from twin import params as P  # noqa: E402
from twin import pumpbc as PB  # noqa: E402
from twin import rodpump as RP  # noqa: E402
from twin import style as S  # noqa: E402
from twin import wellbore as W  # noqa: E402

HYD_S_M = 4.0          # lower end of the library's hydraulic stroke range (T07: 4-7 m)
HYD_N_SPM = 4.5        # same stroke volume per minute as 6 SPM on the 3 m beam unit
DAYS_AFTER = 2.0
MIN_FRAC = 0.05        # brief: min load > 5 % of peak
OUT = ROOT / "out"


def _mu(pr, d):
    r = pr.iloc[int(np.argmin(np.abs(pr.day.values - d)))]
    return float(r.day), W.profile(r.T_in, r.q_liq_m3d, r.f_w)["mu_Pas"]


def run(cyc):
    pr = FG.production_frame(cyc)
    F_fl = PB.fluid_load(P.P_WF_KSC, P.PLUNGER_D_M / P.IN_M, P.ROD_LEN_M)[0]
    days = np.arange(0.0, pr.day.max() + 1e-9, 1.0)
    mus = np.array([_mu(pr, d)[1] for d in days])
    n = mus.shape[1] - 1
    scan = RP.simulate(np.full(len(days), P.ROD_LEN_M), HYD_N_SPM, HYD_S_M, mus, PB.CID["normal"], F_fl,
                       unit=1, down_fraction=0.5, n_nodes=n)
    # persistent float onset: first day from which every later card clips (early-production
    # cards at near-water viscosity ring without settling and can dip below zero; excluded)
    neg = scan["min_load_raw"] < 0
    tail = np.nonzero([neg[i:].all() for i in range(len(neg))])[0]
    if not neg[-1] or not tail.size:
        raise RuntimeError("hydraulic configuration never floats persistently in this cycle")
    onset = float(days[tail[0]])
    day, mu = _mu(pr, min(onset + DAYS_AFTER, pr.day.max()))
    dfs = np.round(np.arange(0.5, 0.80001, 0.01), 2)
    feas = dfs[[HYD_N_SPM <= K.max_hydraulic_spm(HYD_S_M, df) for df in dfs]]
    res = RP.simulate(np.full(len(feas), P.ROD_LEN_M), HYD_N_SPM, HYD_S_M, np.tile(mu, (len(feas), 1)),
                      PB.CID["normal"], F_fl, unit=1, down_fraction=feas, n_nodes=n, record_rod=False)
    frac = res["min_load_raw"] / np.nanmax(res["surf_load_raw"], 1)
    ok = np.nonzero(frac > MIN_FRAC)[0]
    k = int(ok[0]) if ok.size else int(np.argmax(frac))
    pick = lambda j: {key: (v[j] if isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == len(feas) else v)  # noqa: E731
                      for key, v in res.items()}
    notes = {"S_m": HYD_S_M, "N_spm": HYD_N_SPM, "hydraulic_onset_day_df0.5": onset, "day": day,
             "mu_eff_Pas": float(mu.mean()), "df_before": float(feas[0]), "df_after": float(feas[k]),
             "reached_5pct": bool(ok.size), "df_limit_accel": float(feas[-1]),
             "v_down_before_mps": K.max_down_speed(HYD_N_SPM, HYD_S_M, 1, float(feas[0])),
             "v_down_after_mps": K.max_down_speed(HYD_N_SPM, HYD_S_M, 1, float(feas[k])),
             "v_up_after_mps": float(K.hydraulic_speeds(HYD_N_SPM, HYD_S_M, float(feas[k]))[0]),
             "min_load_before_kN": float(res["min_load_raw"][0]) / 1e3, "min_load_after_kN": float(res["min_load_raw"][k]) / 1e3,
             "min_frac_after": float(frac[k])}
    return pick(0), pick(k), notes


def main():
    S.apply()
    cyc = pd.read_parquet(OUT / "cycle.parquet")
    before, after, n = run(cyc)
    (OUT / "sectional_speed_notes.json").write_text(json.dumps(n, indent=2))
    fig, axs = plt.subplots(1, 2, figsize=(14.0, 6.2), sharey=True)
    fig.subplots_adjust(left=0.065, right=0.985, top=0.74, bottom=0.12, wspace=0.08)
    cases = [(before, n["df_before"], n["v_down_before_mps"], "Before: symmetric stroke", S.COLORS["warn"]),
             (after, n["df_after"], n["v_down_after_mps"], "After: slower downstroke (O1 sectional speed)", S.COLORS["ai"])]
    for ax, (r, df, vd, title, col) in zip(axs, cases):
        close = lambda a: np.append(a, a[0])  # noqa: E731
        raw = close(r["surf_load_raw"]) / 1e3
        ax.plot(close(r["surf_pos"]), raw, color="#B9C0BC", lw=1.0, label="rod load (model, unclipped)")
        ax.plot(close(r["surf_pos"]), np.maximum(raw, 0), color=col, lw=2.0, label="surface card (measured, clipped at 0)")
        ax.plot(close(r["dh_pos"]), close(r["dh_load"]) / 1e3, color="#8A938E", lw=1.2, ls=(0, (4, 2.5)), label="downhole (pump)")
        ax.axhline(0, color=S.COLORS["warn"], lw=0.8)
        mn = float(r["min_load_raw"]) / 1e3
        state = "rods float: load clipped" if mn < 0 else f"min load {mn:.1f} kN ({100 * mn / np.nanmax(r['surf_load_raw']) * 1e3:.0f} % of peak)"
        ax.set_title(title, loc="left", fontsize=12.5, fontweight="semibold", color=col, pad=38)
        ax.text(0.0, 1.015, f"N {n['N_spm']:.1f} SPM · S {n['S_m']:.0f} m · downstroke {100 * df:.0f} % of the cycle · "
                f"max down speed {vd:.2f} m/s\n{state}", transform=ax.transAxes, fontsize=9.5, color="#3E4642")
        j = int(np.nanargmin(r["surf_load_raw"]))
        if mn < 0:
            ax.annotate(f"carrier bar outruns the rods:\nload clipped ({mn:.1f} kN)", xy=(r["surf_pos"][j], 0),
                        xytext=(r["surf_pos"][j] - 1.6, 16), fontsize=9, color=S.COLORS["warn"],
                        arrowprops=dict(arrowstyle="->", color=S.COLORS["warn"], lw=1.0))
        ax.set_xlabel("Position (m)")
        ax.grid(True, color="#E1E6E2", lw=0.6)
        ax.set_axisbelow(True)
        ax.legend(loc="upper right", fontsize=8.5, frameon=False)
    axs[0].set_ylabel("Load (kN)")
    fig.suptitle("Same pump speed, no rod float: slow only the downstroke", x=0.065, ha="left", fontsize=15, fontweight="semibold")
    extra = "" if n["reached_5pct"] else f" (5 % target not reached within the unit's acceleration limit, df ≤ {n['df_limit_accel']:.2f})"
    fig.text(0.065, 0.875, f"Hydraulic unit, production day {n['day']:.0f} ({DAYS_AFTER:.0f} d after this unit's own float onset, "
             f"day {n['hydraulic_onset_day_df0.5']:.0f}); tubing μ_eff {n['mu_eff_Pas']:.1f} Pa·s. Wave equation, normal pump. "
             f"Upstroke speeds up to {n['v_up_after_mps']:.2f} m/s to keep N{extra}.", fontsize=10, color="#58625C")
    S.save(fig, "A7_sectional_speed")
    plt.close(fig)
    print(json.dumps(n, indent=1))


if __name__ == "__main__":
    main()
