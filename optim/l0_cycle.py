"""O3 stage-v0 L0 cycle model (CLAUDE.md T15), vectorised over designs.

Design d = (M_s [t], rate [t/h], x_surf, soak ratio):
  1. injection: t_inj = M_s / rate; sandface quality x_sf = x_surf - Q_loss / (w L_v), with Q_loss
     the VIT grade D tubing heat loss from twin.injection (1 day, 3B Fig. 3 completion);
     sandface heat rate Q_h = w (h_w(T_s) - h_w(T_R) + x_sf L_v) at the bottomhole injection pressure.
  2. heated area at the end of injection: Marx-Langenheim (A.7-A.8), 10 m pay; r_h = sqrt(A/pi + r_w^2).
  3. soak and production: Boberg-Lantz average temperature (A.9-A.12)
       T(t) = T_R + (T_s - T_R) [f_HD f_VD (1 - f_PD) - f_PD]
       f_VD exact slab (A.10) with alpha_ob, f_HD = 1/(1 + 5 alpha_R t / r_h^2) (A.11),
       f_PD = 1/2 int delta dt, delta = H_f / (pi r_h^2 h M_R (T_s - T_R)),
       H_f = (q_o M_o + q_w M_w)(T - T_R)  (A.12; the 1/2 as in the doc, flagged there as to-check)
  4. rate: q_o = q_c J_h/J_c (T04 step-profile ratio, mu_h = mu_oil(T)), water cut as T04.
  5. cycle length L: production days until the CSS uplift q_o - q_c falls below Q_CUT_BPD
     (the DEMO cold rate, 18 bbl/d, is already above 8 bbl/d, so a cut-off on total rate is never
     reached), capped at L_MAX_D.
  Outputs: N_p (total oil over L, bbl), SOR = M_s / N_p (t steam per m3... reported per bbl and per m3),
  J1 = N_p / (t_inj + t_soak + L + T_MOB_D) [bbl per cycle-day].
Stage v0: analytical proxy only, not the grid.
"""
import numpy as np
from scipy.special import erf

from twin import inflow as INF
from twin import injection as INJ
from twin import params as P
from twin import rheology as R
from twin import steam
from twin.thermal_rz import ml_area, pay_conductivity

H_PAY = float(sum(P.H_LAYERS_M))
_S_BH = steam.sat(steam.p_abs_ksc_g(P.P_BH_INJ_KSC))
T_S = _S_BH["T_C"]
L_V = _S_BH["L_v"]
DH_SENS = float(steam.h_w(T_S) - steam.h_w(P.T_R_C))
Q_LOSS_D = INJ.march(P.K_VIT_GRADES["D"])["heat_loss_W"]      # W, ~1 day, VIT grade D
ALPHA_OB = P.LAM_OB / P.M_OB
ALPHA_R = pay_conductivity() / P.M_R
Q_C = INF.cold_rate_m3s()
MU_C = R.mu_oil(P.T_R_C)


def f_vd(t):
    tv = 4.0 * ALPHA_OB * np.maximum(t, 1e-9) / H_PAY ** 2
    return erf(1.0 / np.sqrt(tv)) - np.sqrt(tv / np.pi) * (1.0 - np.exp(-1.0 / tv))


def evaluate(M_s_t, rate_tph, x_surf, soak, dt_d=1.0, return_series=False):
    M_s_t, rate_tph, x_surf, soak = np.broadcast_arrays(*(np.atleast_1d(np.asarray(a, float)) for a in
                                                         (M_s_t, rate_tph, x_surf, soak)))
    w = rate_tph / 3.6                                      # kg/s
    t_inj = M_s_t / rate_tph * P.HOUR_S                     # s
    x_sf = np.clip(x_surf - Q_LOSS_D / (w * L_V), 0.0, 1.0)
    Q_h = w * (DH_SENS + x_sf * L_V)
    A = ml_area(t_inj, Q_h, H_PAY, T_S - P.T_R_C)
    r_h = np.sqrt(A / np.pi + P.RW_M ** 2)
    t_soak = soak * t_inj
    dT_s = T_S - P.T_R_C
    dt = dt_d * P.DAY_S
    n = M_s_t.size
    f_pd = np.zeros(n)
    Np = np.zeros(n)
    L = np.full(n, P.L_MAX_D)
    alive = np.ones(n, bool)
    series = [] if return_series else None
    for k in range(int(P.L_MAX_D / dt_d)):
        tp = (k + 0.5) * dt                                 # production time (mid-step)
        t = t_soak + tp                                     # time since end of injection
        f_hd = 1.0 / (1.0 + 5.0 * ALPHA_R * t / r_h ** 2)
        Tb = P.T_R_C + dT_s * np.maximum(f_hd * f_vd(t) * (1.0 - f_pd) - f_pd, 0.0)
        q_o = Q_C * INF.j_ratio(R.mu_oil(Tb), MU_C, r_h)    # m3/s
        f_w = INF.water_cut(tp / P.DAY_S)
        q_w = q_o * f_w / (1.0 - f_w)
        H_f = (q_o * P.M_OIL_VOL + q_w * P.M_WATER_VOL) * (Tb - P.T_R_C)
        f_pd = f_pd + 0.5 * H_f / (np.pi * r_h ** 2 * H_PAY * P.M_R * dT_s) * dt
        uplift_bpd = (q_o - Q_C) * P.DAY_S / P.BBL_M3
        stop = alive & (uplift_bpd < P.Q_CUT_BPD)
        L[stop] = k * dt_d
        alive &= ~stop
        Np += np.where(alive, q_o * dt / P.BBL_M3, 0.0)
        if return_series:
            series.append((tp / P.DAY_S, Tb.copy(), q_o * P.DAY_S / P.BBL_M3))
        if not alive.any():
            break
    t_cycle_d = (t_inj + t_soak) / P.DAY_S + L + P.T_MOB_D
    Np_safe = np.maximum(Np, 1e-9)
    out = {"t_inj_d": t_inj / P.DAY_S, "x_sf": x_sf, "Q_h_W": Q_h, "r_h_m": r_h, "L_d": L, "Np_bbl": Np,
           "SOR_t_per_bbl": M_s_t / Np_safe, "SOR_m3_per_m3": (M_s_t / 1.0) / (Np_safe * P.BBL_M3),
           "J1_bbl_per_day": Np / t_cycle_d, "t_cycle_d": t_cycle_d}
    if return_series:
        out["series"] = series
    return out
