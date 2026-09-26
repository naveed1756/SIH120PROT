"""Water / steam properties from IAPWS-IF97, tabulated once for fast vectorised use.

Pressures in this module are ABSOLUTE Pa. Use p_abs_ksc_g() to convert OIL's ksc(g).
"""
from functools import lru_cache

import numpy as np
from iapws import IAPWS97

from twin import params as P

T_ABS = 273.15


def p_abs_ksc_g(ksc_g):
    """ksc gauge -> Pa absolute."""
    return ksc_g * P.KSC_PA + P.ATM_PA


@lru_cache(maxsize=None)
def sat(p_abs_pa):
    """Saturation state at an absolute pressure (Pa). Returns SI values:
    T_C, h_l, h_v, L_v (J/kg), rho_l, rho_v (kg/m3)."""
    p = float(p_abs_pa) / 1e6
    w = IAPWS97(P=p, x=0.0)
    v = IAPWS97(P=p, x=1.0)
    return {
        "T_C": w.T - T_ABS,
        "h_l": w.h * 1e3,
        "h_v": v.h * 1e3,
        "L_v": (v.h - w.h) * 1e3,
        "rho_l": w.rho,
        "rho_v": v.rho,
    }


@lru_cache(maxsize=None)
def psat_pa(T_C):
    """Saturation pressure (Pa abs) at T (C)."""
    return IAPWS97(T=float(T_C) + T_ABS, x=0.0).P * 1e6


@lru_cache(maxsize=None)
def _hl_table():
    T = np.arange(1.0, 370.0 + 1e-9, 0.5)
    h = np.array([IAPWS97(T=t + T_ABS, x=0.0).h * 1e3 for t in T])
    return T, h


def h_w(T_C):
    """Saturated-liquid water enthalpy (J/kg) at T (C); pressure effect ignored."""
    T, h = _hl_table()
    return np.interp(np.asarray(T_C, dtype=float), T, h)
