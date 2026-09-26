"""T2-B rod string and pump, predictive mode (CLAUDE.md T06; Layer 2 section 4).

Damped wave equation for the rod string, x downward from the polished rod,
u = downward displacement:
    u_tt = a^2 u_xx - c(x) u_t + g_b,   a = sqrt(E/rho_s),  g_b = g (1 - rho_f/rho_s)
    c(x) = K_C_DRAG 2 pi mu_mix(x) / (rho_s A_r ln(r_ti/r_r))       (annular Couette drag)
Explicit central differences (Everitt-Jennings form); top BC u_0 = -y(t); bottom BC
by a ghost node carrying the pump tension F_p from twin.pumpbc.

simulate() is vectorised over a batch of cards: every card has its own rod length,
node spacing (same node count), kinematics, viscosity profile and pump state; all
share dt. The 3rd stroke of each card is resampled to CARD_POINTS points on the fly.
"""
import numpy as np

from twin import kinematics as K
from twin import params as P
from twin.pumpbc import PumpBC

A_ROD = np.pi * P.ROD_R_M ** 2
EA = P.E_STEEL * A_ROD
A_WAVE = np.sqrt(P.E_STEEL / P.RHO_STEEL)
LN_GAP = np.log(P.TUB_RI_M / P.ROD_R_M)


def drag_coeff(mu):
    """c = K_C 2 pi mu / (rho_s A_r ln(r_ti/r_r)), 1/s."""
    return P.K_C_DRAG * 2.0 * np.pi * np.asarray(mu, float) / (P.RHO_STEEL * A_ROD * LN_GAP)


def buoyant_weight_per_m(rho_f=P.RHO_FLUID_ROD):
    return P.RHO_STEEL * A_ROD * P.G * (1.0 - rho_f / P.RHO_STEEL)


def static_profile(L, F_p, n_nodes, rho_f=P.RHO_FLUID_ROD, u0=0.0):
    """Static displacement under buoyant weight and pump tension F_p:
    T(x) = F_p + w (L - x);  u(x) = u0 + [F_p x + w (L x - x^2/2)] / EA."""
    L = np.atleast_1d(np.asarray(L, float))[:, None]
    x = np.linspace(0.0, 1.0, n_nodes + 1)[None, :] * L
    w = buoyant_weight_per_m(rho_f)
    return u0 + (np.atleast_1d(F_p)[:, None] * x + w * (L * x - 0.5 * x * x)) / EA


def polished_rod_load(u, dx, rho_f=P.RHO_FLUID_ROD):
    """F_pr = EA (u_1 - u_0)/dx + w dx/2 (the one-sided difference sits at dx/2,
    so half a segment of buoyant rod weight is added back)."""
    return EA * (u[:, 1] - u[:, 0]) / dx + buoyant_weight_per_m(rho_f) * dx / 2.0


def simulate(L, N_spm, S, mu, cls, F_fl, unit=None, down_fraction=None, rho_f=None,
             fill=None, k_leak=None, alpha=None, R=None, n_strokes=P.N_STROKES_SIM,
             dt=P.DT_ROD_S, n_nodes=None, record_rod=False, n_rec_depths=20):
    """Simulate a batch of cards. Arrays of length n (scalars broadcast).
    mu: (n,) uniform viscosity or (n, n_nodes+1) profile (Pa.s) along the rod.
    Returns dict of resampled 3rd-stroke cards (n, CARD_POINTS) and flags."""
    L = np.atleast_1d(np.asarray(L, float))
    n = L.size
    bc = lambda v, d: np.broadcast_to(np.asarray(d if v is None else v, float), (n,)).copy()  # noqa: E731
    N_spm = bc(N_spm, 5.0); S = bc(S, P.STROKE_M); cls = np.broadcast_to(np.asarray(cls), (n,)).copy()
    F_fl = bc(F_fl, 0.0); unit = bc(unit, 0).astype(int); df = bc(down_fraction, 0.5)
    rho_f = bc(rho_f, P.RHO_FLUID_ROD)
    if n_nodes is None:
        n_nodes = max(4, int(np.floor(L.min() / P.DX_ROD_M + 1e-9)))
    dx = L / n_nodes
    r2 = (A_WAVE * dt / dx) ** 2
    assert np.all(A_WAVE * dt / dx <= 1.0 + 1e-12), "CFL: a*dt/dx must be <= 1"
    mu = np.asarray(mu, float)
    mu_nodes = np.broadcast_to(mu[:, None] if mu.ndim == 1 else mu, (n, n_nodes + 1))
    c = drag_coeff(mu_nodes)
    cp = 1.0 + 0.5 * c * dt
    cm = 1.0 - 0.5 * c * dt
    g_b = (P.G * (1.0 - rho_f / P.RHO_STEEL))[:, None]
    T = 60.0 / N_spm
    Tu = np.where(unit == 1, (1.0 - df) * T, 0.5 * T)

    # initial condition: static, pump unloaded at the start of the upstroke
    u = static_profile(L, np.zeros(n), n_nodes, rho_f[0])
    if np.any(rho_f != rho_f[0]):
        u = np.vstack([static_profile(L[i], 0.0, n_nodes, rho_f[i]) for i in range(n)])
    u_prev = u.copy()
    pump = PumpBC(cls, F_fl, S, -u[:, -1], fill=fill, k_leak=k_leak, alpha=alpha, R=R, Tu=Tu, T=T)

    # recording targets: 3rd stroke, CARD_POINTS samples uniform in time
    M = P.CARD_POINTS
    # M samples of the last stroke plus one more at the end of the stroke (same phase as the
    # first) so closure compares F(n T) with F((n-1) T)
    t_rec = (n_strokes - 1) * T[:, None] + T[:, None] * np.arange(M + 1)[None, :] / M
    rec = {k: np.full((n, M + 1), np.nan) for k in ("y", "F_pr", "y_p", "F_p")}
    nxt = np.zeros(n, int)
    rod = None
    if record_rod:
        idx_d = np.linspace(0, n_nodes, n_rec_depths).round().astype(int)
        rod = {"u": np.full((n, M + 1, n_rec_depths), np.nan), "strain": np.full((n, M + 1, n_rec_depths), np.nan),
               "idx": idx_d}
    n_steps = int(np.ceil(n_strokes * T.max() / dt)) + 2
    float_any = np.zeros(n, bool)
    min_raw = np.full(n, np.inf)
    rows = np.arange(n)
    Fp = np.zeros(n)
    kin = K.Kin(N_spm, S, unit, df)
    for step in range(n_steps):
        t = step * dt
        # record (before advancing) where the target time has been reached
        due = (nxt <= M) & (t >= t_rec[rows, np.minimum(nxt, M)])
        if due.any():
            ii = rows[due]; kk = nxt[due]
            Fpr = polished_rod_load(u[due], dx[due], rho_f[due])
            rec["y"][ii, kk] = -u[due, 0]
            rec["F_pr"][ii, kk] = Fpr
            rec["y_p"][ii, kk] = -u[due, -1]
            rec["F_p"][ii, kk] = Fp[due]
            float_any[due] |= Fpr < 0.0
            min_raw[due] = np.minimum(min_raw[due], Fpr)
            if record_rod:
                rod["u"][ii, kk] = u[due][:, rod["idx"]]
                grad = np.gradient(u[due], axis=1) / dx[due][:, None]
                rod["strain"][ii, kk] = grad[:, rod["idx"]]
            nxt[due] += 1
        if (nxt > M).all():
            break
        Fp = pump.update(-u[:, -1], t)
        u_new = np.empty_like(u)
        u_new[:, 1:-1] = (r2[:, None] * (u[:, 2:] - 2.0 * u[:, 1:-1] + u[:, :-2]) + 2.0 * u[:, 1:-1]
                          - cm[:, 1:-1] * u_prev[:, 1:-1] + dt * dt * g_b) / cp[:, 1:-1]
        ghost = u[:, -2] + 2.0 * dx * Fp / EA
        u_new[:, -1] = (r2 * (ghost - 2.0 * u[:, -1] + u[:, -2]) + 2.0 * u[:, -1]
                        - cm[:, -1] * u_prev[:, -1] + dt * dt * g_b[:, 0]) / cp[:, -1]
        u_new[:, 0] = -kin.pos(t + dt)
        u_prev, u = u, u_new

    rng = np.nanmax(rec["F_pr"], 1) - np.nanmin(rec["F_pr"], 1)
    closure = np.abs(rec["F_pr"][:, M] - rec["F_pr"][:, 0]) / np.maximum(rng, 1e-9)
    rec = {k: v[:, :M] for k, v in rec.items()}
    if record_rod:
        rod["u"] = rod["u"][:, :M]; rod["strain"] = rod["strain"][:, :M]
    load = np.maximum(rec["F_pr"], 0.0)
    out = {"closure": closure,
        "surf_pos": rec["y"], "surf_load": load, "surf_load_raw": rec["F_pr"],
        "dh_pos": rec["y_p"] - np.nanmin(rec["y_p"], axis=1, keepdims=True), "dh_load": rec["F_p"],
        "float": float_any, "min_load_raw": min_raw, "S_p": np.nanmax(rec["y_p"], 1) - np.nanmin(rec["y_p"], 1),
        "dx": dx, "n_nodes": n_nodes, "T": T,
    }
    if record_rod:
        out["rod_u"] = rod["u"]; out["rod_stress"] = rod["strain"] * P.E_STEEL
        out["rod_depth"] = rod["idx"][None, :] * dx[:, None]
    return out


def card_closure(load):
    """|last - first sample| / load range. Note: simulate() returns the proper
    periodicity closure |F(nT) - F((n-1)T)| / range as out["closure"]."""
    rng = np.nanmax(load, 1) - np.nanmin(load, 1)
    return np.abs(load[:, -1] - load[:, 0]) / np.maximum(rng, 1e-9)


def card_area(pos, load):
    """Enclosed area, positive when traversed clockwise (up-stroke on top)."""
    x = np.concatenate([pos, pos[:, :1]], 1)
    y = np.concatenate([load, load[:, :1]], 1)
    return -0.5 * np.sum(x[:, :-1] * y[:, 1:] - x[:, 1:] * y[:, :-1], axis=1)
