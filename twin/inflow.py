"""T1-C thermal inflow, PoC lite (Layer 3A section 7; CLAUDE.md T04).

Cold IPR (C.2c, no TPG), Boberg-Lantz step-profile productivity ratio per layer
(the 3A 7.6 check form) and the fitted condensate-return water-cut curve (the
3A 7.3 fallback). The full two-node pressure model (C.1-C.2b) is out of scope.
"""
import numpy as np

from twin import params as P
from twin import rheology as R

LN_RE_RW = np.log(P.RE_M / P.RW_M)


def kh_layers():
    """Layer kh (m3). KH_CONTRAST is read as the kh ratio between layers; total
    kh = K_MD * total pay (PROGRESS.md, Decisions)."""
    c = np.asarray(P.KH_CONTRAST, dtype=float)
    return P.K_MD * P.MD_M2 * sum(P.H_LAYERS_M) * c / c.sum()


def drawdown_pa():
    return (P.P_NEARWELL_KSC - P.P_WF_KSC) * P.KSC_PA


def cold_rate_m3s():
    """C.2c without TPG: q_c = 2 pi kh (p_c - p_wf) / (mu_oil(T_R) (ln(re/rw) - 1/2))."""
    mu_c = R.mu_oil(P.T_R_C)
    return 2.0 * np.pi * kh_layers().sum() * drawdown_pa() / (mu_c * (LN_RE_RW - 0.5))


def k_md_for_cold_rate(q_bpd):
    """Invert C.2c for the DEMO tuning knob K_MD (mD)."""
    q = q_bpd * P.BBL_M3 / P.DAY_S
    mu_c = R.mu_oil(P.T_R_C)
    kh = q * mu_c * (LN_RE_RW - 0.5) / (2.0 * np.pi * drawdown_pa())
    return kh / sum(P.H_LAYERS_M) / P.MD_M2


def j_ratio(mu_h, mu_c, r_h):
    """Boberg-Lantz step profile: J_h/J_c = ln(re/rw) / ((mu_h/mu_c) ln(rh/rw) + ln(re/rh))."""
    r_h = np.clip(np.asarray(r_h, dtype=float), P.RW_M, P.RE_M)
    return LN_RE_RW / ((np.asarray(mu_h) / mu_c) * np.log(r_h / P.RW_M) + np.log(P.RE_M / r_h))


def water_cut(t_days):
    """f_w(t) = FW0 exp(-t/tau) + FW_INF (1 - exp(-t/tau)), t = days since production start."""
    e = np.exp(-np.asarray(t_days, dtype=float) / P.TAU_W_D)
    return P.FW0 * e + P.FW_INF * (1.0 - e)


def rates(r_h_k, T_bar_k, t_days):
    """Rates for the current heated state. Per-layer ratio J_k/J_c from that
    layer's r_h and mu_oil(T_bar); total oil = q_c times the kh-weighted mean
    ratio; split to layers by kh_k * J_k. Liquid = oil / (1 - f_w).
    Returns SI (m3/s) plus bbl/d copies."""
    kh = kh_layers()
    mu_c = R.mu_oil(P.T_R_C)
    ratio = j_ratio(R.mu_oil(np.asarray(T_bar_k)), mu_c, r_h_k)
    share = kh * ratio / np.sum(kh * ratio)
    q_o = cold_rate_m3s() * np.sum(kh * ratio) / kh.sum()
    f_w = float(water_cut(t_days))
    q_liq = q_o / (1.0 - f_w)
    to_bpd = P.DAY_S / P.BBL_M3
    return {"q_o": q_o, "q_w": q_liq - q_o, "f_w": f_w, "q_liq": q_liq,
            "q_liq_k": q_liq * share, "ratio_k": ratio,
            "q_o_bpd": q_o * to_bpd, "q_liq_bpd": q_liq * to_bpd}


def rates_from_state(solver, t_days):
    """rate_fn for thermal_rz.run_cycle: reads r_h and T_bar from the solver."""
    rh = solver.r_h()
    return rates(rh, solver.T_bar_heated(rh), t_days)
