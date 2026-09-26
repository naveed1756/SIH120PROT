"""T2-B diagnostic mode: surface card -> downhole (pump) card (CLAUDE.md T08).

The same damped wave equation as twin.rodpump,
    a^2 u_xx = u_tt + c(x) u_t - g_b,
is marched in SPACE from the polished rod down to the pump (Everitt-Jennings finite
differences). Known at x = 0 over one stroke: displacement u_0(t) = -y(t) and force
F(t) = EA du/dx + w dx/2 (the same load definition as rodpump.polished_rod_load). The card
is treated as periodic in time, so time derivatives are central differences with wrap-around.

    u_1       = u_0 + (F - w dx/2) dx / EA
    u_{i+1}   = 2 u_i - u_{i-1} + (dx/a)^2 (u_tt + c_i u_t - g_b)_i
    F_pump    = EA (u_{N+1} - u_{N-1}) / (2 dx)          (inverse of the ghost-node BC)
    pump pos  = -u_N  (shifted so its minimum is 0)
"""
import numpy as np

from twin import params as P
from twin.rodpump import A_WAVE, EA, buoyant_weight_per_m, drag_coeff


def downhole_card(surf_pos, surf_load, L, N_spm, mu, rho_f=P.RHO_FLUID_ROD, n_nodes=None):
    """surf_pos, surf_load: one stroke sampled uniformly in time (N), starting anywhere.
    mu: scalar or (n_nodes+1,) viscosity profile (Pa.s). Returns (pump_pos_m, pump_load_N)."""
    y = np.asarray(surf_pos, float)
    F = np.asarray(surf_load, float)
    M = y.size
    dt = 60.0 / N_spm / M
    n = int(np.floor(L / P.DX_ROD_M + 1e-9)) if n_nodes is None else int(n_nodes)
    dx = L / n
    c = drag_coeff(np.broadcast_to(np.asarray(mu, float), (n + 1,)))
    g_b = P.G * (1.0 - rho_f / P.RHO_STEEL)
    w = buoyant_weight_per_m(rho_f)
    k = (dx / A_WAVE) ** 2
    u = np.zeros((n + 2, M))
    u[0] = -y
    u[1] = u[0] + (F - w * dx / 2.0) * dx / EA
    for i in range(1, n + 1):
        ui = u[i]
        up, um = np.roll(ui, -1), np.roll(ui, 1)
        u_t = (up - um) / (2.0 * dt)
        u_tt = (up - 2.0 * ui + um) / dt ** 2
        u[i + 1] = 2.0 * ui - u[i - 1] + k * (u_tt + c[i] * u_t - g_b)
    F_p = EA * (u[n + 1] - u[n - 1]) / (2.0 * dx)
    pos = -u[n]
    return pos - pos.min(), F_p


def rms_error(F_rec, F_imp):
    """RMS difference as a fraction of the imposed load range."""
    F_rec, F_imp = np.asarray(F_rec), np.asarray(F_imp)
    return float(np.sqrt(np.mean((F_rec - F_imp) ** 2)) / max(np.ptp(F_imp), 1e-9))


def downhole_batch(surf_pos, surf_load, L, N_spm, mu, rho_f=P.RHO_FLUID_ROD, n_nodes=None):
    """Returns (pump_pos (n, M) shifted to min 0, pump_load (n, M))."""
    y = np.asarray(surf_pos, float)
    F = np.asarray(surf_load, float)
    nb, M = y.shape
    L = np.broadcast_to(np.asarray(L, float), (nb,))
    N_spm = np.broadcast_to(np.asarray(N_spm, float), (nb,))
    n = int(np.floor(L.min() / P.DX_ROD_M + 1e-9)) if n_nodes is None else int(n_nodes)
    dx = (L / n)[:, None]
    dt = (60.0 / N_spm / M)[:, None]
    c = drag_coeff(np.broadcast_to(np.asarray(mu, float), (nb,)))[:, None]
    g_b = P.G * (1.0 - rho_f / P.RHO_STEEL)
    w = buoyant_weight_per_m(rho_f)
    k = (dx / A_WAVE) ** 2
    hist = [-y, -y + (F - w * dx / 2.0) * dx / EA]          # u_0, u_1
    for _ in range(1, n + 1):
        u, u_prev = hist[-1], hist[-2]
        up, um = np.roll(u, -1, axis=1), np.roll(u, 1, axis=1)
        hist.append(2.0 * u - u_prev + k * ((up - 2.0 * u + um) / dt ** 2 + c * (up - um) / (2.0 * dt) - g_b))
        if len(hist) > 3:
            hist.pop(0)
    u_nm1, u_n, u_np1 = hist
    F_p = EA * (u_np1 - u_nm1) / (2.0 * dx)
    pos = -u_n
    return pos - pos.min(axis=1, keepdims=True), F_p
