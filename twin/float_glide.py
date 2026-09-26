"""F / O2 lite: rod-float margin, float-onset forecast and SPM glide path (CLAUDE.md T09).

Float margin (analytic): terminal rod-fall speed through the tubing fluid,
    v_fall(z) = (rho_s - rho_f) g A_r ln(r_ti/r_r) / (K_C 2 pi mu_mix(z)),
its length-weighted harmonic mean over the string (= v_fall at the arithmetic-mean
viscosity), against the carrier-bar's fastest downstroke speed:
    float_margin = 1 - v_down_max / v_fall_eff.
Glide path (O2 lite): N_glide = min(N_inflow, 0.9 N_float), with
N_inflow = q_liq / (A_p S 0.8 1440) (pump-to-inflow matching, C17) and
N_float = 0.9 * 60 v_fall_eff / (pi S).
Cross-check: the T06 wave equation is run on the same tubing viscosity profile;
its onset is where the minimum polished-rod load first goes below zero.
Run: python -m twin.float_glide   (needs out/cycle.parquet)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from twin import kinematics as K
from twin import params as P
from twin import pumpbc as PB
from twin import rodpump as RP
from twin import wellbore as W

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
W_FALL = (P.RHO_STEEL - P.RHO_FLUID_ROD) * P.G * RP.A_ROD * RP.LN_GAP / (P.K_C_DRAG * 2.0 * np.pi)
VOL_EFF = 0.8
LEAD_H = 14.0                         # demo "now" = onset - 14 h (brief)
HEATER_WHATIF_KW = 6.0
HYD_WHATIF = dict(S=6.0, down_fraction=0.6)


def v_fall(mu):
    return W_FALL / np.asarray(mu, float)


def plunger_area():
    return np.pi * P.PLUNGER_D_M ** 2 / 4.0


def n_inflow(q_liq_m3d, S=P.STROKE_M, d_m=None):
    A = plunger_area() if d_m is None else np.pi * d_m ** 2 / 4.0
    return np.asarray(q_liq_m3d, float) / (A * S * VOL_EFF * 1440.0)


def size_plunger(q_peak_m3d, S=P.STROKE_M, target=(5.0, 6.0)):
    """Standard plunger whose N_inflow at the production peak is closest to the 5-6 SPM band."""
    mid = 0.5 * sum(target)
    best = min(P.PLUNGER_SIZES_IN, key=lambda d: abs(n_inflow(q_peak_m3d, S, d * P.IN_M) - mid))
    return best, float(n_inflow(q_peak_m3d, S, best * P.IN_M))


def production_frame(cycle_df):
    pr = cycle_df[cycle_df.phase == "production"].copy()
    pr["day"] = (pr.t_h.values - pr.t_h.values[0]) / 24.0
    pr["q_liq_m3d"] = pr.q_liq * P.DAY_S
    return pr.reset_index(drop=True)


def series(cycle_df, heater_kW=0.0):
    """Hourly tubing state and float quantities over the production phase (beam unit, S = STROKE_M)."""
    pr = production_frame(cycle_df)
    T_wh, mu_eff = np.empty(len(pr)), np.empty(len(pr))
    for i, r in enumerate(pr.itertuples()):
        prof = W.profile(r.T_in, r.q_liq_m3d, r.f_w, heater_kW)
        T_wh[i] = prof["T_C"][0]
        mu_eff[i] = prof["mu_Pas"].mean()          # harmonic mean of v_fall <=> arithmetic mean of mu
    S = P.STROKE_M
    vf = v_fall(mu_eff)
    N_base = float(n_inflow(pr.q_liq_m3d.values[0]))
    N_in = n_inflow(pr.q_liq_m3d.values)
    N_fl = 0.9 * 60.0 * vf / (np.pi * S)
    N_gl = np.minimum(N_in, 0.9 * N_fl)
    v_base = np.pi * S * N_base / 60.0
    return pd.DataFrame({
        "day": pr.day, "t_h": pr.t_h, "T_in_C": pr.T_in, "T_wh_C": T_wh, "q_liq_m3d": pr.q_liq_m3d,
        "f_w": pr.f_w, "mu_eff_Pas": mu_eff, "v_fall": vf,
        "N_base": N_base, "N_inflow": N_in, "N_float": N_fl, "N_glide": N_gl,
        "margin_base": 1.0 - v_base / vf,
        "margin_glide": 1.0 - (np.pi * S * N_gl / 60.0) / vf,
    })


def onset_day(day, margin):
    neg = np.nonzero(np.asarray(margin) < 0.0)[0]
    return float(np.asarray(day)[neg[0]]) if neg.size else None


def hydraulic_whatif(s):
    """Same stroke volume per minute as the beam baseline, S = 6 m, down_fraction 0.6."""
    N_h = float(s.N_base.iloc[0]) * P.STROKE_M / HYD_WHATIF["S"]
    v_d = K.max_down_speed(N_h, HYD_WHATIF["S"], 1, HYD_WHATIF["down_fraction"])
    margin = 1.0 - v_d / s.v_fall.values
    return N_h, v_d, margin


def rod_card_at(cycle_df, day, N, unit=0, S=P.STROKE_M, down_fraction=0.5, heater_kW=0.0):
    """Wave-equation card at a production day with the tubing viscosity profile (normal pump)."""
    pr = production_frame(cycle_df)
    r = pr.iloc[int(np.argmin(np.abs(pr.day.values - day)))]
    prof = W.profile(r.T_in, r.q_liq_m3d, r.f_w, heater_kW)
    n_nodes = len(prof["z_m"]) - 1
    F_fl = PB.fluid_load(P.P_WF_KSC, P.PLUNGER_D_M / P.IN_M, P.ROD_LEN_M)[0]
    res = RP.simulate(np.array([P.ROD_LEN_M]), N, S, prof["mu_Pas"][None, :], PB.CID["normal"], F_fl,
                      unit=unit, down_fraction=down_fraction, n_nodes=n_nodes, record_rod=True)
    res["day"] = float(r.day); res["mu_eff"] = float(prof["mu_Pas"].mean()); res["F_fl"] = F_fl
    return res


def wave_onset(cycle_df, N, day_lo, day_hi, step=1.0):
    """First day at which the wave-equation minimum polished-rod load goes negative
    (scan in one batched simulation, then report the bracketing days)."""
    pr = production_frame(cycle_df)
    days = np.arange(day_lo, min(day_hi, pr.day.max()) + 1e-9, step)
    mus, F_fl = [], PB.fluid_load(P.P_WF_KSC, P.PLUNGER_D_M / P.IN_M, P.ROD_LEN_M)[0]
    for d in days:
        r = pr.iloc[int(np.argmin(np.abs(pr.day.values - d)))]
        mus.append(W.profile(r.T_in, r.q_liq_m3d, r.f_w)["mu_Pas"])
    mus = np.array(mus)
    res = RP.simulate(np.full(len(days), P.ROD_LEN_M), N, P.STROKE_M, mus, PB.CID["normal"], F_fl,
                      n_nodes=mus.shape[1] - 1)
    neg = np.nonzero(res["min_load_raw"] < 0)[0]
    return (float(days[neg[0]]) if neg.size else None), days, res["min_load_raw"]


def main():
    cyc = pd.read_parquet(OUT / "cycle.parquet")
    pr = production_frame(cyc)
    d_in, N_pk = size_plunger(pr.q_liq_m3d.values[0])
    assert abs(P.PLUNGER_D_M - d_in * P.IN_M) < 1e-9, f"params.PLUNGER_D_M should be {d_in} in"
    s = series(cyc)
    s_heat = series(cyc, HEATER_WHATIF_KW)
    N_h, v_dh, m_hyd = hydraulic_whatif(s)
    s["margin_heater"] = 1.0 - (np.pi * P.STROKE_M * s.N_base / 60.0) / s_heat.v_fall.values
    s["N_float_heater"] = s_heat.N_float.values
    s["T_wh_heater_C"] = s_heat.T_wh_C.values
    s["mu_eff_heater_Pas"] = s_heat.mu_eff_Pas.values
    s["margin_hydraulic"] = m_hyd
    on = onset_day(s.day, s.margin_base)
    notes = {
        "plunger_in": d_in, "N_inflow_peak_spm": N_pk, "N_base_spm": float(s.N_base.iloc[0]),
        "v_down_base_mps": float(np.pi * P.STROKE_M * s.N_base.iloc[0] / 60.0),
        "onset_day_analytic": on,
        "onset_day_heater_6kW": onset_day(s.day, s.margin_heater),
        "onset_day_hydraulic_S6_df0.6": onset_day(s.day, s.margin_hydraulic),
        "hydraulic_N_spm": N_h, "hydraulic_v_down_mps": v_dh,
        "glide_margin_min": float(s.margin_glide.min()),
        "T_PROD_D": P.T_PROD_D, "F_INV": P.F_INV, "FW0": P.FW0, "FW_INF": P.FW_INF, "TAU_W_D": P.TAU_W_D,
    }
    if on is not None:
        now = on - LEAD_H / 24.0
        notes["now_day"] = now
        w_on, days, mins = wave_onset(cyc, s.N_base.iloc[0], max(0.0, on - 30.0), on + 15.0)
        notes["onset_day_wave_equation"] = w_on
        notes["onset_disagreement_days"] = None if w_on is None else w_on - on
        cc_days = [max(0.0, on - 30.0), on, min(on + 15.0, s.day.max())]
        cc = [rod_card_at(cyc, d, s.N_base.iloc[0]) for d in cc_days]
        notes["crosscheck"] = [{"day": c["day"], "mu_eff_Pas": c["mu_eff"], "min_load_raw_kN": float(c["min_load_raw"][0]) / 1e3,
                                "load_range_kN": float(np.ptp(c["surf_load_raw"][0])) / 1e3, "float": bool(c["float"][0])}
                               for c in cc]
        pd.DataFrame({"day": days, "min_load_raw": mins}).to_parquet(OUT / "wave_onset_scan.parquet", index=False)
        np.savez_compressed(OUT / "crosscheck_cards.npz", **{f"{k}_{i}": v for i, c in enumerate(cc)
                                                             for k, v in c.items() if isinstance(v, np.ndarray)})
    s.to_parquet(OUT / "float_glide.parquet", index=False)
    (OUT / "float_glide_notes.json").write_text(json.dumps(notes, indent=2))
    return s, notes


if __name__ == "__main__":
    _, n = main()
    print(json.dumps(n, indent=2))
