"""T2-A production profile, PoC subset (Layer 3B 4.5 W.13; task T05).

Ramey closed form for upward flow in the VIT tubing, with the relaxation length
L_R scaled per m3/d from the 3B 4.5 table (72 m per m3/d for VIT grade D), and the
tubing mixture viscosity from T1-B (mixture mode, f_w as holdup, no slip).
Depth z is measured downward from the wellhead.
"""
import numpy as np

from twin import params as P
from twin import rheology as R

G_GEO = (P.T_R_C - P.T_SURF_GEO_C) / P.TOP_PAY_M      # geothermal gradient, K/m


def T_ei(depth_m):
    """Undisturbed formation temperature (C) at a depth (m)."""
    return P.T_SURF_GEO_C + G_GEO * np.asarray(depth_m, dtype=float)


def relaxation_length(q_liq_m3d, lr_per_m3d=P.LR_PER_M3D_VIT_D):
    return lr_per_m3d * np.asarray(q_liq_m3d, dtype=float)


def heater_dT(heater_kW, q_liq_m3d):
    """3B 4.5 rule of thumb: ~10 C per kW at 5 m3/d, scaling inversely with rate."""
    if heater_kW <= 0:
        return 0.0
    return P.HEATER_DT_PER_KW_AT_5M3D * heater_kW * (5.0 / max(q_liq_m3d, 1e-6))


def ramey_T(depth_m, T_in_C, q_liq_m3d, heater_kW=0.0, pump_depth_m=P.ROD_LEN_M,
            lr_per_m3d=P.LR_PER_M3D_VIT_D):
    """W.13: T(l) = T_ei(l) + (T_in - T_bh) e^(-l/L_R) + g_G L_R (1 - e^(-l/L_R)),
    l = distance up from the pump. Above the pump only (depth <= pump depth)."""
    depth = np.asarray(depth_m, dtype=float)
    l = np.clip(pump_depth_m - depth, 0.0, None)
    L_R = max(float(relaxation_length(q_liq_m3d, lr_per_m3d)), 1e-9)
    T_bh = T_ei(pump_depth_m)
    Tin = T_in_C + heater_dT(heater_kW, q_liq_m3d)
    e = np.exp(-l / L_R)
    return T_ei(depth) + (Tin - T_bh) * e + G_GEO * L_R * (1.0 - e)


def depth_grid(pump_depth_m=P.ROD_LEN_M, dz=10.0):
    return np.arange(0.0, pump_depth_m + 1e-9, dz)


def profile(T_in_C, q_liq_m3d, f_w, heater_kW=0.0, pump_depth_m=P.ROD_LEN_M):
    """Tubing profile: depth z (0 .. pump, 10 m), T(z) and mixture viscosity mu_mix(z)."""
    z = depth_grid(pump_depth_m)
    T = ramey_T(z, T_in_C, q_liq_m3d, heater_kW, pump_depth_m)
    return {"z_m": z, "T_C": T, "mu_Pas": R.mu_mixture(T, f_w)}


def profile_at_day(cycle_df, prod_day, heater_kW=0.0):
    """Tubing profile at a production day, using T_in, q_liq and f_w from out/cycle.parquet."""
    pr = cycle_df[cycle_df.phase == "production"]
    d = (pr.t_h.values - pr.t_h.values[0]) / 24.0
    i = int(np.argmin(np.abs(d - prod_day)))
    row = pr.iloc[i]
    q_m3d = row.q_liq * P.DAY_S
    out = profile(row.T_in, q_m3d, row.f_w, heater_kW)
    out.update(day=float(d[i]), T_in_C=float(row.T_in), q_liq_m3d=float(q_m3d), f_w=float(row.f_w))
    return out
