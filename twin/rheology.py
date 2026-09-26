"""T1-B rheology (Layer 3A section 6), PoC subset.

All functions take temperature in deg C and return SI (Pa.s, kg/m3, J/kg/K, W/m/K).
They accept scalars or numpy arrays.

Status: Formulation -> Prototype. Every parameter except the 50 C anchor is a
placeholder prior (Layer 3A 6, "What is known about Baghewala rheology today").
"""
from functools import lru_cache

import numpy as np

from twin import params as P

T_ABS = 273.15


# ------------------------------------------------------------------ B.1 Walther
def nu_cSt(T_C):
    """Kinematic viscosity (cSt) from Walther / ASTM D341:
    log10(log10(nu + 0.7)) = A - B*log10(T_K)."""
    T_K = np.asarray(T_C, dtype=float) + T_ABS
    return 10.0 ** (10.0 ** (P.WALTHER_A - P.WALTHER_B * np.log10(T_K))) - 0.7


# --------------------------------------------------------- density (MPMS 11.1)
def rho(T_C):
    """Oil density (kg/m3), API MPMS 11.1 crude form."""
    dT = np.asarray(T_C, dtype=float) - 15.0
    a15 = 613.97 / P.RHO15 ** 2
    return P.RHO15 * np.exp(-a15 * dT * (1.0 + 0.8 * a15 * dT))


def mu_oil(T_C):
    """Dead-oil dynamic viscosity (Pa.s) at the reference shear rate (50 1/s):
    mu = nu[cSt]*1e-6 * rho[kg/m3]."""
    return nu_cSt(T_C) * 1e-6 * rho(T_C)


# ----------------------------------------------------------- water (IAPWS-97)
@lru_cache(maxsize=None)
def _water_table():
    """Liquid-water viscosity table 1..370 C (step 0.5 C). Pressure is
    P_WATER_VISC_PA, raised to 1.05*Psat where needed so the state stays liquid."""
    from iapws import IAPWS97

    T = np.arange(1.0, 370.0 + 1e-9, 0.5)
    mu = np.empty_like(T)
    for i, t in enumerate(T):
        Tk = t + T_ABS
        psat = IAPWS97(T=Tk, x=0).P  # MPa
        p = max(P.P_WATER_VISC_PA / 1e6, 1.05 * psat)
        mu[i] = IAPWS97(T=Tk, P=p).mu
    return T, mu


def mu_water(T_C):
    """Liquid-water viscosity (Pa.s), IAPWS-97, at 1 MPa (or just above Psat)."""
    T, mu = _water_table()
    return np.interp(np.asarray(T_C, dtype=float), T, mu)


# -------------------------------------------------- B.7-B.8 emulsion mixture
def _pal_rhodes_mu_r(phi_d):
    """Relative viscosity of a dispersion, Pal-Rhodes (3A B.7).
    phi_d/PHI100 is capped at PAL_RHODES_CAP to keep the form finite."""
    x = np.minimum(np.asarray(phi_d, dtype=float) / P.PHI100, P.PAL_RHODES_CAP)
    return (1.0 + x / (1.187 - x)) ** 2.492


def inversion_weight(f_w):
    """Logistic regime weight s(f_w) of 3A B.8: 0 = oil-continuous, 1 = water-continuous."""
    f_w = np.asarray(f_w, dtype=float)
    return 1.0 / (1.0 + np.exp(-(f_w - P.F_INV) / P.F_INV_W))


def mu_mixture(T_C, f_w):
    """Oil-water mixture viscosity in the tubing / rod annulus (Pa.s).

    W/O branch: mu_oil * mu_r(phi = f_w)         (Pal-Rhodes, water dispersed)
    O/W branch: mu_water * mu_r(phi = 1 - f_w)   (Pal-Rhodes, oil dispersed)
    Regime switch: logistic s(f_w) of B.8, applied in LOG space:
        ln mu = (1 - s) ln mu_WO + s ln mu_OW
    Deviation from B.8's linear blend (see PROGRESS.md, Decisions): with the
    linear form the diverging W/O branch dominates past the inversion point and
    the mixture never becomes thin, which contradicts the regime the switch is
    meant to represent. f_w is used as holdup (no-slip default, 3B 4.5)."""
    T_C = np.asarray(T_C, dtype=float)
    f_w = np.clip(np.asarray(f_w, dtype=float), 0.0, 1.0)
    mu_wo = mu_oil(T_C) * _pal_rhodes_mu_r(f_w)
    mu_ow = mu_water(T_C) * _pal_rhodes_mu_r(1.0 - f_w)
    s = inversion_weight(f_w)
    return np.exp((1.0 - s) * np.log(mu_wo) + s * np.log(mu_ow))


# ---------------------------------------------------- thermal properties (B6)
def cp(T_C):
    """Oil heat capacity (J/kg/K), Gambill: (1.685 + 0.00339*T[C])/sqrt(SG) kJ/kg/K."""
    return 1e3 * (1.685 + 0.00339 * np.asarray(T_C, dtype=float)) / np.sqrt(P.SG)


def lam(T_C):
    """Oil thermal conductivity (W/m/K), Cragoe: 0.1172*(1 - 0.00054*T[C])/SG."""
    return 0.1172 * (1.0 - 0.00054 * np.asarray(T_C, dtype=float)) / P.SG


# ------------------------------------------- B.2-B.5 Herschel-Bulkley layer
def _theta(T_C):
    """B.3: 0 at T_NN, 1 at the pour point."""
    th = (P.T_NN_C - np.asarray(T_C, dtype=float)) / (P.T_NN_C - P.T_PP_C)
    return np.clip(th, 0.0, 1.0)


def tau_y(T_C):
    """Yield stress (Pa), B.3: tau0 * theta^a (vanishes above T_NN)."""
    return P.TAU0_PA * _theta(T_C) ** P.A_HB


def n_index(T_C):
    """Flow index, B.3: n = 1 - (1 - n0) * theta^b (1 above T_NN)."""
    return 1.0 - (1.0 - P.N0_HB) * _theta(T_C) ** P.B_HB


def K_consistency(T_C):
    """Consistency (Pa.s^n), B.4 anchor: reproduces Walther exactly at 50 1/s."""
    n = n_index(T_C)
    return (mu_oil(T_C) - tau_y(T_C) / P.GDOT_REF) * P.GDOT_REF ** (1.0 - n)


def mu_app(T_C, gdot, regularised=True):
    """Apparent viscosity (Pa.s) of Herschel-Bulkley oil (B.2), optionally with
    Papanastasiou regularisation (B.5) so it stays finite as gdot -> 0.
    At gdot = GDOT_REF it equals mu_oil(T_C) by construction."""
    gdot = np.asarray(gdot, dtype=float)
    n = n_index(T_C)
    K = K_consistency(T_C)
    ty = tau_y(T_C)
    if regularised:
        yield_term = ty * (1.0 - np.exp(-P.M_PAPANASTASIOU * gdot)) / gdot
    else:
        yield_term = ty / gdot
    return K * gdot ** (n - 1.0) + yield_term


# ----------------------------------------------------------- validity envelope
T_ENV_LO_C = P.T_PP_C + 3.0
T_ENV_HI_C = 320.0


def in_envelope(T_C):
    """True where T is inside the validated rheology envelope (3A 6.4).
    Below it the Walther curve is an extrapolation (gel regime)."""
    T_C = np.asarray(T_C, dtype=float)
    return (T_C >= T_ENV_LO_C) & (T_C <= T_ENV_HI_C)
