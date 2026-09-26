"""T2-A injection mode, simplified (task T14; 3B 4.2-4.4).

Wet steam marched down the tubing in 10 m segments (z downward):
    dx/dz = -q' / (w L_v(p)),   q' = (T_sat(p) - T_ei(z)) / R_w
    dp/dz = rho_m g,            1/rho_m = x/rho_v + (1 - x)/rho_l   (homogeneous, no friction)
Series resistances per metre (3B W.1, steel walls and the steam-side film neglected):
    R_w = R_VIT + R_ann + R_cem + R_form
    R_VIT  = ln(r_ins,o / r_ins,i) / (2 pi k_VIT C_CPL)          (spec T14; 0 for bare tubing)
    R_ann  = 1 / (2 pi r_to (h_r + h_c))                          N2 annulus, h_r from W.2 radiation,
             h_c = k_N2 / (r_to ln(r_ci/r_to)) (conduction only, no convective enhancement)
    R_cem  = ln(r_wb / r_co) / (2 pi k_cem)
    R_form = T_D / (2 pi k_e), Hasan-Kabir W.5 at t = 1 day
The annulus surface temperatures are iterated (4 passes). The spec's two-term q' (R_VIT + R_form
only) was tried first and under-predicts grades C and B (DEVINSTRUCT.md, design decisions).
Once x reaches 0 the column is hot water; the march stops (condensation depth).
"""
import numpy as np

from twin import params as P
from twin import steam
from twin import wellbore as W

SIGMA = 5.670374e-8
R_CEM = np.log(P.RW_M / P.CASING_RO_M) / (2.0 * np.pi * P.K_CEM)


def r_form(t_days=P.T_FORM_DAYS, k_e=P.K_E_FORM, rc_e=P.M_OB, r_wb=P.RW_M):
    t_D = (k_e / rc_e) * t_days * P.DAY_S / r_wb ** 2
    T_D = np.log(np.exp(-0.2 * t_D) + (1.5 - 0.3719 * np.exp(-t_D)) * np.sqrt(t_D))
    return T_D / (2.0 * np.pi * k_e)


def r_vit(k_vit, c_cpl=P.C_CPL):
    return np.log(P.VIT_R_INS_O_M / P.VIT_R_INS_I_M) / (2.0 * np.pi * k_vit * c_cpl)


def r_annulus(T_to, T_ci, r_to, r_ci=P.CASING_RI_M, eps=P.EPS_STEEL):
    T1, T2 = T_to + 273.15, T_ci + 273.15
    h_r = SIGMA * (T1 ** 2 + T2 ** 2) * (T1 + T2) / (1.0 / eps + (r_to / r_ci) * (1.0 / eps - 1.0))
    h_c = P.K_N2 / (r_to * np.log(r_ci / r_to))
    return 1.0 / (2.0 * np.pi * r_to * (h_r + h_c))


def heat_loss_per_m(T_f, T_ei, k_vit, passes=4):
    """q' (W/m) and the resistances, iterating the annulus surface temperatures."""
    Rv = 0.0 if k_vit is None else r_vit(k_vit)
    r_to = P.VIT_R_INS_I_M if k_vit is None else P.VIT_R_TO_M
    Rf = r_form()
    q = (T_f - T_ei) / (Rv + Rf + R_CEM + 0.05)
    for _ in range(passes):
        T_to = T_f - q * Rv
        T_ci = T_ei + q * (R_CEM + Rf)
        Ra = r_annulus(T_to, T_ci, r_to)
        q = (T_f - T_ei) / (Rv + Ra + R_CEM + Rf)
    return q


def march(k_vit=None, w=P.STEAM_KGS, x0=P.X_SURF, p0_ksc=P.P_SURF_KSC, depth=P.TOP_PAY_M, dz=P.DZ_INJ_M):
    """k_vit None = bare tubing + N2 annulus. Returns dict of arrays along depth."""
    z = np.arange(0.0, depth + 1e-9, dz)
    x = np.full(z.size, np.nan); T = np.full(z.size, np.nan); p = np.full(z.size, np.nan); q = np.zeros(z.size)
    x[0], p[0] = x0, steam.p_abs_ksc_g(p0_ksc)
    for k in range(z.size):
        s = steam.sat(float(p[k]))
        T[k] = s["T_C"]
        q[k] = heat_loss_per_m(T[k], float(W.T_ei(z[k])), k_vit)
        if k + 1 == z.size:
            break
        rho_m = 1.0 / (x[k] / s["rho_v"] + (1.0 - x[k]) / s["rho_l"])
        p[k + 1] = p[k] + rho_m * P.G * dz
        dx = q[k] * dz / (w * s["L_v"])
        if x[k] - dx <= 0.0:
            x[k + 1] = 0.0
            z_c = z[k] + dz * x[k] / dx
            sl = slice(0, k + 2)
            return {"z": z[sl], "x": x[sl], "T_C": T[sl], "p_pa": p[sl], "q_Wpm": q[sl], "z_condensed": float(z_c),
                    "x_bh": 0.0, "heat_loss_W": float(np.sum(q[: k + 1]) * dz)}
        x[k + 1] = x[k] - dx
    return {"z": z, "x": x, "T_C": T, "p_pa": p, "q_Wpm": q, "z_condensed": None, "x_bh": float(x[-1]),
            "heat_loss_W": float(np.sum(q[:-1]) * dz)}


def grades():
    out = {g: march(k) for g, k in P.K_VIT_GRADES.items()}
    out["bare"] = march(None)
    return out
