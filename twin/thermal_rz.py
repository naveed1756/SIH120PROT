"""T1-A thermal field, simplified for the PoC (Layer 3A section 5; CLAUDE.md T03).

2-D axisymmetric r-z finite-volume energy balance in volumetric-enthalpy form,
fully implicit (backward Euler) with upwind radial advection in the pay and
Picard iteration on the piecewise-linear H -> T map.

Simplifications (deliberate, from the brief):
  * one pressure per phase, so T_sat is constant within a phase;
  * energy equation only (no water-mass equation A.3);
  * vertical transport by conduction only; override enters only through the
    injection allocation (A.4) with the closure parameter beta.
Closure added here (PROGRESS.md, Decisions): with the water-mass equation
removed, nothing moves the LATENT heat of the injected steam away from the well.
Each step it is distributed by an explicit, energy-exact condensation-front
march per z-row (operator split): starting at the well, each cell is filled up
to its saturated-liquid enthalpy H_l (the steam zone), and whatever latent power
is left passes to the next cell. The implicit solve then carries only sensible
heat: conduction plus upwind advection of liquid water at h_w(T).

State H is J/m3 above the reservoir temperature T_R. Temperatures are handled as
theta = T - T_R. Elevation z is measured upward from the base of the pay.
"""
from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp
from scipy.optimize import brentq
from scipy.sparse.linalg import splu, spsolve

from twin import params as P
from twin import rheology as R
from twin import steam

T_R = P.T_R_C


# ======================================================================== grid
def _geometric_sizes(dz0, n, total):
    """n sizes growing geometrically from dz0 that sum to total."""
    f = lambda q: dz0 * (q ** n - 1.0) / (q - 1.0) - total  # noqa: E731
    q = brentq(f, 1.0 + 1e-9, 3.0)
    return dz0 * q ** np.arange(n)


def pay_conductivity():
    """3A 5.2: lambda = lambda_r^(1-phi) * lambda_f^phi, pore fluid mixed
    geometrically by the initial saturations (oil from Cragoe at T_R)."""
    lam_f = R.lam(T_R) ** P.S_OI * P.LAM_W ** (1.0 - P.S_OI)
    return P.LAM_R ** (1.0 - P.PHI) * lam_f ** P.PHI


@dataclass
class Grid:
    r_edges: np.ndarray
    z_edges: np.ndarray            # elevation, 0 = base of pay, upward
    layer_of_row: np.ndarray       # layer index per z-row (0 = top layer), -1 = rock
    layer_h: np.ndarray            # thickness per layer (top -> bottom)
    M: np.ndarray                  # (nz, nr) volumetric heat capacity
    lam: np.ndarray                # (nz, nr) conductivity
    outer_fixed: bool = True       # T = T_R at r_e
    vert_fixed: bool = True        # T = T_R at top and bottom
    nr: int = field(init=False)
    nz: int = field(init=False)

    def __post_init__(self):
        self.nr = len(self.r_edges) - 1
        self.nz = len(self.z_edges) - 1
        self.rc = np.sqrt(self.r_edges[:-1] * self.r_edges[1:])   # log-centre
        self.dz = np.diff(self.z_edges)
        self.zc = 0.5 * (self.z_edges[:-1] + self.z_edges[1:])
        self.area_z = np.pi * (self.r_edges[1:] ** 2 - self.r_edges[:-1] ** 2)  # (nr,)
        self.V = self.dz[:, None] * self.area_z[None, :]                     # (nz, nr)
        self.is_pay_row = self.layer_of_row >= 0
        self._build_conductances()

    @property
    def N(self):
        return self.nr * self.nz

    def idx(self, j, i):
        return j * self.nr + i

    def _build_conductances(self):
        nr, nz, re, rc, lam = self.nr, self.nz, self.r_edges, self.rc, self.lam
        # radial internal faces (cylindrical, log form)
        J, I = np.meshgrid(np.arange(nz), np.arange(nr - 1), indexing="ij")
        rf = re[1:-1][None, :]
        Rres = (np.log(rf / rc[None, :-1]) / lam[:, :-1] + np.log(rc[None, 1:] / rf) / lam[:, 1:])
        Gr = 2.0 * np.pi * self.dz[:, None] / Rres
        self.rad_p = (J * nr + I).ravel()
        self.rad_q = (J * nr + I + 1).ravel()
        self.rad_G = Gr.ravel()
        # vertical internal faces (harmonic)
        J2, I2 = np.meshgrid(np.arange(nz - 1), np.arange(nr), indexing="ij")
        Rv = (0.5 * self.dz[:-1, None] / lam[:-1, :] + 0.5 * self.dz[1:, None] / lam[1:, :])
        Gv = self.area_z[None, :] / Rv
        self.ver_p = (J2 * nr + I2).ravel()
        self.ver_q = ((J2 + 1) * nr + I2).ravel()
        self.ver_G = Gv.ravel()
        # boundary conductances to T_R
        Gb = np.zeros((nz, nr))
        if self.outer_fixed:
            Gb[:, -1] += 2.0 * np.pi * self.dz * lam[:, -1] / np.log(re[-1] / rc[-1])
        if self.vert_fixed:
            Gb[0, :] += self.area_z * lam[0, :] / (0.5 * self.dz[0])
            Gb[-1, :] += self.area_z * lam[-1, :] / (0.5 * self.dz[-1])
        self.G_bnd = Gb.ravel()


def build_grid(layers_h=None, outer_fixed=True, vert_fixed=True):
    """Default BGW-SYN-01 grid: 39 log-spaced radial cells, pay 10 x 1 m,
    12 geometric cells each in cap and base (0.25 m -> 60 m total)."""
    layers_h = np.asarray(P.H_LAYERS_M if layers_h is None else layers_h, dtype=float)
    r_edges = np.geomspace(P.RW_M, P.RE_M, P.NR_EDGES)
    cap = _geometric_sizes(P.CAP_DZ0_M, P.N_CAP, P.CAP_EXTENT_M)
    h_pay = layers_h.sum()
    n_pay = int(round(h_pay / P.PAY_DZ_M))
    pay = np.full(n_pay, h_pay / n_pay)
    sizes = np.concatenate([cap[::-1], pay, cap])                  # bottom -> top
    z_edges = np.concatenate([[0.0], np.cumsum(sizes)]) - P.CAP_EXTENT_M
    zc = 0.5 * (z_edges[:-1] + z_edges[1:])
    # layer index by elevation: layer 0 is the top layer
    tops = h_pay - np.concatenate([[0.0], np.cumsum(layers_h)])    # top elevation of each layer
    layer_of_row = np.full(len(zc), -1)
    for k in range(len(layers_h)):
        m = (zc < tops[k]) & (zc > tops[k + 1])
        layer_of_row[m] = k
    nz, nr = len(zc), len(r_edges) - 1
    pay_row = layer_of_row >= 0
    M = np.where(pay_row[:, None], P.M_R, P.M_OB) * np.ones((nz, nr))
    lam = np.where(pay_row[:, None], pay_conductivity(), P.LAM_OB) * np.ones((nz, nr))
    return Grid(r_edges, z_edges, layer_of_row, layers_h, M, lam, outer_fixed, vert_fixed)


# ================================================================= allocation
def injection_weights(layers_h, kh_contrast, beta):
    """A.4 with uniform layer injectivity: w_k ∝ kh_k * exp(beta * zeta_k),
    zeta_k = layer mid-height / pay height (0 = base, 1 = top)."""
    h = np.asarray(layers_h, dtype=float)
    H = h.sum()
    mid_from_top = np.cumsum(h) - 0.5 * h
    zeta = (H - mid_from_top) / H
    w = np.asarray(kh_contrast, dtype=float) * np.exp(beta * zeta)
    return w / w.sum()


# ===================================================================== solver
class ThermalRZ:
    """Implicit enthalpy solver. Call step() with the phase pressure and the
    per-row mass rates and heat sources; read summaries with the helpers."""

    def __init__(self, grid: Grid):
        self.g = grid
        self.H = np.zeros(grid.N)
        self.t = 0.0
        self.E_sf = 0.0
        self.E_prod = 0.0
        self.E_out = 0.0
        self.eps_max = 0.0
        self.jk_steps = 0
        self.halvings = 0
        self.M_flat = grid.M.ravel()
        self.V_flat = grid.V.ravel()
        row = np.repeat(np.arange(grid.nz), grid.nr)
        self.pay_cell = grid.is_pay_row[row]
        self.row_of = row
        self.last_rows_m = np.zeros(grid.nz)
        self._set_pressure(steam.p_abs_ksc_g(P.P_NEARWELL_KSC))

    # ----------------------------------------------------------- properties
    def _set_pressure(self, p_abs):
        s = steam.sat(float(p_abs))
        self.p_abs = float(p_abs)
        self.T_sat = s["T_C"]
        self.dTs = s["T_C"] - T_R
        self.h_sat_rel = steam.h_w(s["T_C"]) - steam.h_w(T_R)
        self.cap_latent = P.PHI * s["rho_v"] * s["L_v"]     # J/m3 of pore steam at S_s = 1
        self.rho_v = s["rho_v"]
        self.L_v = s["L_v"]
        self.H_l = np.where(self.pay_cell, self.M_flat * self.dTs, np.inf)

    def theta(self, H=None):
        """T - T_R (K) from H with the true piecewise map."""
        H = self.H if H is None else H
        return np.where(H > self.H_l, self.dTs, H / self.M_flat)

    def T(self):
        return T_R + self.theta()

    def steam_sat(self):
        S = np.where(self.H > self.H_l, (self.H - self.H_l) / self.cap_latent, 0.0)
        return np.clip(S, 0.0, 1.0)

    def _linearise(self, H):
        """theta = a*H + b ; flowing specific enthalpy (liquid water, J/kg above
        T_R) e = alpha*H + beta. Two-phase cells sit at T_sat."""
        g = self
        two = (H > g.H_l)
        a = np.where(two, 0.0, 1.0 / g.M_flat)
        b = np.where(two, g.dTs, 0.0)
        th = np.where(two, g.dTs, np.maximum(H, 0.0) / g.M_flat)
        thc = np.maximum(th, 0.5)
        cbar = (steam.h_w(T_R + thc) - steam.h_w(T_R)) / thc      # secant cp of water
        alpha = np.where(two, 0.0, cbar / g.M_flat)
        beta = np.where(two, g.h_sat_rel, 0.0)
        alpha = np.where(g.pay_cell, alpha, 0.0)
        beta = np.where(g.pay_cell, beta, 0.0)
        return a, b, alpha, beta, two

    def latent_march(self, rows_lat, dt):
        """Distribute per-row latent power (W) outward from the well: each cell
        takes what it needs to reach H_l over this step; the rest moves on.
        Anything left past r_e leaves the domain (E_out). Returns the source
        array (W per cell) and the power lost at r_e."""
        g = self.g
        src = np.zeros(g.N)
        lost = 0.0
        for j in np.nonzero(rows_lat)[0]:
            L = rows_lat[j]
            for i in range(g.nr):
                c = j * g.nr + i
                need = max(0.0, (self.H_l[c] - self.H[c]) * self.V_flat[c] / dt)
                take = min(L, need)
                src[c] += take
                L -= take
                if L <= 0.0:
                    break
            lost += max(L, 0.0)
        return src, lost

    # ----------------------------------------------------------------- step
    def _theta_e(self, H):
        """True (piecewise) theta(H) and flowing enthalpy e(H), plus the secant cp."""
        two = H > self.H_l
        th = np.where(two, self.dTs, H / self.M_flat)
        thc = np.maximum(th, 0.5)
        cbar = (steam.h_w(T_R + thc) - steam.h_w(T_R)) / thc
        e = np.where(self.pay_cell, np.where(two, self.h_sat_rel, cbar * np.maximum(th, 0.0)), 0.0)
        return th, e, cbar, two

    def step(self, dt, p_abs, rows_m=None, rows_q=None, rows_lat=None, max_regime=6, max_jk=400,
             tol_theta=1e-3):
        """Advance by dt (backward Euler).
        rows_m:   mass rate per z-row (kg/s); > 0 outward (injection), < 0 inward.
        rows_q:   sensible heat entering the innermost cell of each z-row (W).
        rows_lat: latent heat per z-row (W), placed by latent_march().
        Nonlinear solve: regime-based Picard first (fast when no cell sits on the
        saturation kink); if that does not settle, Jager-Kacur relaxation with the
        maximum slope 1/M (monotone, always converges; matrix factorised once).
        The energy budget uses the linearisation of the final solve, so it is exact;
        the linearisation error in theta is below tol_theta (K)."""
        g = self.g
        if p_abs != self.p_abs:
            self._set_pressure(p_abs)
        nz, nr, N = g.nz, g.nr, g.N
        rows_m = np.zeros(nz) if rows_m is None else np.asarray(rows_m, float)
        rows_q = np.zeros(nz) if rows_q is None else np.asarray(rows_q, float)
        rows_lat = np.zeros(nz) if rows_lat is None else np.asarray(rows_lat, float)
        self.last_rows_m = rows_m
        Hn = self.H.copy()
        Vdt = self.V_flat / dt

        # advection edges (fixed for the step): upwind u -> downwind d, |m|
        eu, ed, em = [], [], []
        bu, bm, bkind = [], [], []           # boundary outflow cells: 0 = r_e, 1 = r_w
        for j in np.nonzero(rows_m)[0]:
            m = rows_m[j]
            base = j * nr
            if m > 0:
                eu.append(base + np.arange(nr - 1)); ed.append(base + np.arange(1, nr))
                em.append(np.full(nr - 1, m)); bu.append(base + nr - 1); bm.append(m); bkind.append(0)
            else:
                eu.append(base + np.arange(1, nr)); ed.append(base + np.arange(nr - 1))
                em.append(np.full(nr - 1, -m)); bu.append(base); bm.append(-m); bkind.append(1)
        if eu:
            eu = np.concatenate(eu); ed = np.concatenate(ed); em = np.concatenate(em)
        else:
            eu = ed = np.zeros(0, int); em = np.zeros(0)
        bu = np.asarray(bu, int); bm = np.asarray(bm, float); bkind = np.asarray(bkind, int)
        src, lat_lost = self.latent_march(rows_lat, dt)
        src[np.arange(nz) * nr] += rows_q

        def assemble(a, b, al, be):
            diag = Vdt.copy()
            rhs = Vdt * Hn + src
            rows_i, cols_i, vals = [], [], []
            for p_, q_, G in ((g.rad_p, g.rad_q, g.rad_G), (g.ver_p, g.ver_q, g.ver_G)):
                np.add.at(diag, p_, G * a[p_]); np.add.at(diag, q_, G * a[q_])
                rows_i += [p_, q_]; cols_i += [q_, p_]; vals += [-G * a[q_], -G * a[p_]]
                np.add.at(rhs, p_, -G * (b[p_] - b[q_])); np.add.at(rhs, q_, -G * (b[q_] - b[p_]))
            diag += g.G_bnd * a
            rhs -= g.G_bnd * b
            if em.size:
                np.add.at(diag, eu, em * al[eu]); np.add.at(rhs, eu, -em * be[eu])
                rows_i.append(ed); cols_i.append(eu); vals.append(-em * al[eu])
                np.add.at(rhs, ed, em * be[eu])
            if bu.size:
                np.add.at(diag, bu, bm * al[bu]); np.add.at(rhs, bu, -bm * be[bu])
            rows_i.append(np.arange(N)); cols_i.append(np.arange(N)); vals.append(diag)
            A = sp.csc_matrix((np.concatenate(vals), (np.concatenate(rows_i), np.concatenate(cols_i))),
                              shape=(N, N))
            return A, rhs

        def lin_error(H, a, b, al, be):
            th, e, _, _ = self._theta_e(H)
            return (np.max(np.abs(a * H + b - th)),
                    np.max(np.abs(al * H + be - e)) / max(self.h_sat_rel, 1.0))

        H = Hn.copy()
        converged = False
        self.picard_iters = 0
        # --- 1) regime-based Picard (Newton-like on the piecewise map)
        for _ in range(max_regime):
            self.picard_iters += 1
            a, b, al, be, _ = self._linearise(H)
            A, rhs = assemble(a, b, al, be)
            H = spsolve(A, rhs)
            eth, ee = lin_error(H, a, b, al, be)
            if eth < tol_theta and ee < 1e-6:
                converged = True
                break
        # --- 2) Jager-Kacur relaxation: slope 1/M everywhere (monotone fixed point)
        if not converged:
            self.jk_steps += 1
            a = 1.0 / self.M_flat
            th0, e0, cbar, _ = self._theta_e(H)
            al = np.where(self.pay_cell, cbar / self.M_flat, 0.0)
            A, _ = assemble(a, np.zeros(N), al, np.zeros(N))
            lu = splu(A)
            for _ in range(max_jk):
                self.picard_iters += 1
                th0, e0, _, _ = self._theta_e(H)
                b = th0 - a * H
                be = e0 - al * H
                _, rhs = assemble(a, b, al, be)
                H_new = lu.solve(rhs)
                eth, ee = lin_error(H_new, a, b, al, be)
                H = H_new
                if eth < tol_theta and ee < 1e-5:
                    converged = True
                    break
        if not converged:
            return None
        # budget with the SAME linearisation used in the final solve (exact)
        th = a * H + b
        e_b = al[bu] * H[bu] + be[bu] if bu.size else np.zeros(0)
        cond_out = np.sum(g.G_bnd * th) * dt
        adv_out = np.sum(bm[bkind == 0] * e_b[bkind == 0]) * dt if bu.size else 0.0
        adv_prod = np.sum(bm[bkind == 1] * e_b[bkind == 1]) * dt if bu.size else 0.0
        self.E_sf += (np.sum(rows_q) + np.sum(rows_lat)) * dt
        self.E_out += cond_out + adv_out + lat_lost * dt
        self.E_prod += adv_prod
        self.H = H
        self.t += dt
        eps = self.eps_rel()
        self.eps_max = max(self.eps_max, abs(eps))
        return eps

    def step_adaptive(self, dt, p_abs, rows_m=None, rows_q=None, rows_lat=None, min_dt=1.0):
        """step(); if the nonlinear solve fails, take two half-steps (recursively)."""
        eps = self.step(dt, p_abs, rows_m, rows_q, rows_lat)
        if eps is not None:
            return eps
        if dt / 2 < min_dt:
            raise RuntimeError(f"thermal step did not converge down to dt = {dt:.3g} s")
        self.halvings += 1
        self.step_adaptive(dt / 2, p_abs, rows_m, rows_q, rows_lat, min_dt)
        return self.step_adaptive(dt / 2, p_abs, rows_m, rows_q, rows_lat, min_dt)

    # -------------------------------------------------------------- outputs
    def energy(self, mask=None):
        e = self.H * self.V_flat
        return float(e.sum() if mask is None else e[mask].sum())

    def zone_masks(self):
        g = self.g
        zc = g.zc[self.row_of]
        return {"pay": self.pay_cell, "cap": (~self.pay_cell) & (zc > 0), "base": (~self.pay_cell) & (zc < 0)}

    def eps_rel(self):
        if self.E_sf <= 0:
            return 0.0
        return (self.E_sf - self.energy() - self.E_prod - self.E_out) / self.E_sf

    def layer_theta_max(self):
        """(n_layers, nr) max theta over the rows of each layer."""
        g = self.g
        th = self.theta().reshape(g.nz, g.nr)
        out = np.zeros((len(g.layer_h), g.nr))
        for k in range(len(g.layer_h)):
            out[k] = th[g.layer_of_row == k].max(axis=0)
        return out

    def radius_where(self, prof, thresh):
        """Outermost radius where prof >= thresh, interpolated in log r between
        cell centres. Returns r_w if no cell reaches thresh."""
        g = self.g
        above = np.nonzero(prof >= thresh)[0]
        if above.size == 0:
            return g.r_edges[0]
        i = above[-1]
        if i == g.nr - 1:
            return g.r_edges[-1]
        x0, x1 = np.log(g.rc[i]), np.log(g.rc[i + 1])
        y0, y1 = prof[i], prof[i + 1]
        f = (y0 - thresh) / (y0 - y1) if y0 != y1 else 0.0
        return float(np.exp(x0 + f * (x1 - x0)))

    def r_h(self, dT=P.R_H_DT_K):
        return np.array([self.radius_where(p, dT) for p in self.layer_theta_max()])

    def T_bar_heated(self, r_h=None):
        """Pore-volume-weighted T inside r_h, per layer (C)."""
        g = self.g
        r_h = self.r_h() if r_h is None else r_h
        th = self.theta().reshape(g.nz, g.nr)
        out = np.full(len(g.layer_h), T_R)
        for k in range(len(g.layer_h)):
            rows = g.layer_of_row == k
            cols = g.rc < r_h[k]
            if cols.any():
                V = g.V[np.ix_(rows, cols)]
                out[k] = T_R + float((th[np.ix_(rows, cols)] * V).sum() / V.sum())
        return out

    def heated_area(self, half_dT):
        """Grid equivalent of the Marx-Langenheim heated area (m2): in every pay
        row, the radius where T - T_R = half_dT (interpolated in log r between
        cell centres), then pi*(r^2 - r_w^2) averaged over the pay thickness."""
        g = self.g
        th = self.theta().reshape(g.nz, g.nr)
        rows = np.nonzero(g.is_pay_row)[0]
        r = np.array([self.radius_where(th[j], half_dT) for j in rows])
        A = np.pi * (r ** 2 - g.r_edges[0] ** 2)
        return float((A * g.dz[rows]).sum() / g.dz[rows].sum())

    def T_in(self, phase):
        """Temperature of fluid at the sandface (C). Injection: T_sat.
        Production: flow-weighted T of the innermost pay cells. Otherwise
        thickness-weighted mean of the innermost pay cells."""
        g = self.g
        th0 = self.theta().reshape(g.nz, g.nr)[:, 0]
        rows = g.is_pay_row
        if phase == "injection":
            return self.T_sat
        w = np.abs(self.last_rows_m) if phase == "production" and np.any(self.last_rows_m) else g.dz * rows
        w = w * rows
        return float(T_R + (th0 * w).sum() / w.sum())


# ================================================================ phase runner
def rows_from_layers(grid: Grid, layer_values):
    """Spread a per-layer quantity over that layer's z-rows in proportion to dz."""
    out = np.zeros(grid.nz)
    for k, v in enumerate(layer_values):
        rows = grid.layer_of_row == k
        out[rows] = v * grid.dz[rows] / grid.dz[rows].sum()
    return out


def injection_rows(grid, weights, mdot, p_abs, x_sf=P.X_SF):
    """Per-row mass rate, sensible and latent sandface heat for injection.
    A.5: q = mdot * (h_w(T_sat) + x_sf * L_v - h_w(T_R)) = sensible + latent."""
    s = steam.sat(float(p_abs))
    q_sens = mdot * (steam.h_w(s["T_C"]) - steam.h_w(T_R))
    q_lat = mdot * x_sf * s["L_v"]
    return (rows_from_layers(grid, weights * mdot), rows_from_layers(grid, weights * q_sens),
            rows_from_layers(grid, weights * q_lat), q_sens + q_lat)


def time_steps(duration_s):
    """300 s steps for the first 6 h of a phase, then 3600 s."""
    steps, t = [], 0.0
    while t < duration_s - 1e-6:
        dt = P.DT_FINE_S if t < P.FINE_WINDOW_S - 1e-6 else P.DT_S
        dt = min(dt, duration_s - t)
        steps.append(dt)
        t += dt
    return steps


def run_cycle(rate_fn=None, beta=P.BETA_OVERRIDE, t_inj_d=P.T_INJ_D, soak_ratio=P.SOAK_RATIO,
              t_prod_d=P.T_PROD_D, save_path=None, verbose=False):
    """Injection -> soak -> production on the BGW-SYN-01 grid.

    rate_fn(solver, t_prod_days) -> dict with 'q_liq_k' (per layer, m3/s, > 0 = produced)
    and any extra scalars to log. Rates are evaluated from the state at the start of
    each step (one-step lag). Default: twin.inflow.rates_from_state.
    Returns a dict of hourly series, 6-hourly T snapshots and the budget."""
    if rate_fn is None:
        from twin import inflow
        rate_fn = inflow.rates_from_state
    g = build_grid()
    sol = ThermalRZ(g)
    w = injection_weights(g.layer_h, P.KH_CONTRAST, beta)
    p_inj = steam.p_abs_ksc_g(P.P_BH_INJ_KSC)
    p_near = steam.p_abs_ksc_g(P.P_NEARWELL_KSC)
    rows_m_inj, rows_q_inj, rows_l_inj, q_tot = injection_rows(g, w, P.STEAM_KGS, p_inj)
    # phase lengths rounded to whole hours so hourly records stay on the hour
    # (soak = 0.55 x 18 d = 237.6 h -> 238 h)
    hr = lambda d: round(d * 24.0) * 3600.0  # noqa: E731
    phases = [("injection", hr(t_inj_d), p_inj),
              ("soak", hr(soak_ratio * t_inj_d), p_near),
              ("production", hr(t_prod_d), p_near)]
    hourly = {k: [] for k in ("t_h", "phase", "q_o", "q_w", "f_w", "q_liq", "T_in", "E_res",
                              "E_sf", "dE_pay", "dE_cap", "dE_base", "E_prod", "E_out", "eps_rel")}
    hourly["r_h"], hourly["T_bar"] = [], []
    snaps_T, snaps_t, snaps_phase = [], [], []
    masks = sol.zone_masks()
    t_glob = 0.0
    last = {"q_o": 0.0, "q_w": 0.0, "f_w": np.nan, "q_liq": 0.0}

    def record(phase):
        rh = sol.r_h()
        hourly["t_h"].append(t_glob / 3600.0); hourly["phase"].append(phase)
        for k in ("q_o", "q_w", "f_w", "q_liq"):
            hourly[k].append(last[k])
        hourly["r_h"].append(rh); hourly["T_bar"].append(sol.T_bar_heated(rh))
        hourly["T_in"].append(sol.T_in(phase)); hourly["E_res"].append(sol.energy())
        hourly["E_sf"].append(sol.E_sf)
        hourly["dE_pay"].append(sol.energy(masks["pay"])); hourly["dE_cap"].append(sol.energy(masks["cap"]))
        hourly["dE_base"].append(sol.energy(masks["base"]))
        hourly["E_prod"].append(sol.E_prod); hourly["E_out"].append(sol.E_out)
        hourly["eps_rel"].append(sol.eps_rel())

    def snap(phase):
        snaps_T.append(sol.T().reshape(g.nz, g.nr).astype(np.float32))
        snaps_t.append(t_glob / 3600.0); snaps_phase.append(phase)

    record("injection"); snap("injection")
    eps_steps = []
    for phase, dur, p_abs in phases:
        t_ph = 0.0
        for dt in time_steps(dur):
            rl = None
            if phase == "injection":
                rm, rq, rl = rows_m_inj, rows_q_inj, rows_l_inj
                last.update(q_o=0.0, q_w=0.0, f_w=np.nan, q_liq=0.0)
            elif phase == "soak":
                rm, rq = None, None
                last.update(q_o=0.0, q_w=0.0, f_w=np.nan, q_liq=0.0)
            else:
                r = rate_fn(sol, t_ph / P.DAY_S)
                last.update({k: r[k] for k in ("q_o", "q_w", "f_w", "q_liq")})
                rm = -rows_from_layers(g, np.asarray(r["q_liq_k"]) * P.RHO_W)
                rq = None
            eps_steps.append(sol.step_adaptive(dt, p_abs, rm, rq, rl))
            t_ph += dt
            t_glob += dt
            if abs(t_glob / 3600.0 - round(t_glob / 3600.0)) < 1e-9:
                record(phase)
            if abs(t_glob / P.SNAP_EVERY_S - round(t_glob / P.SNAP_EVERY_S)) < 1e-9:
                snap(phase)
        if verbose:
            print(f"{phase:>10s} done: t = {t_glob/86400:.1f} d, r_h = {np.round(sol.r_h(), 2)}, "
                  f"eps = {sol.eps_rel():.2e}")
    out = {k: np.asarray(v) for k, v in hourly.items() if k != "phase"}
    out["phase"] = np.asarray(hourly["phase"])
    out["T_snap"] = np.asarray(snaps_T)
    out["t_snap_h"] = np.asarray(snaps_t)
    out["phase_snap"] = np.asarray(snaps_phase)
    out["eps_steps"] = np.asarray(eps_steps)
    out["jk_steps"] = sol.jk_steps
    out["halvings"] = sol.halvings
    out["r_edges"] = g.r_edges
    out["z_edges"] = g.z_edges
    out["q_heat_W"] = q_tot
    out["weights"] = w
    out["T_sat_inj"] = steam.sat(float(p_inj))["T_C"]
    if save_path is not None:
        np.savez_compressed(save_path, **out)
    return out


# ======================================================= Marx-Langenheim check
def ml_area(t_s, q_heat, h, dT, M_R=P.M_R, K_ob=P.LAM_OB, M_ob=P.M_OB):
    """Marx-Langenheim heated area (3A A.7-A.8):
    A = Q M_R h / (4 K_ob M_ob dT) * G(t_D),  G = e^tD erfc(sqrt tD) + 2 sqrt(tD/pi) - 1,
    t_D = 4 K_ob M_ob t / (M_R^2 h^2). Uses scaled erfc for large t_D."""
    from scipy.special import erfcx
    t_s = np.asarray(t_s, dtype=float)
    tD = 4.0 * K_ob * M_ob * t_s / (M_R ** 2 * h ** 2)
    G = erfcx(np.sqrt(tD)) + 2.0 * np.sqrt(tD / np.pi) - 1.0
    return q_heat * M_R * h / (4.0 * K_ob * M_ob * dT) * G


def marx_langenheim_check(t_end_d=21.0, h=10.0, T_s_C=P.ML_T_S_C, record_every_s=6 * 3600.0):
    """Grid vs analytical heated area: beta = 0, one uniform layer of thickness h,
    steam at T_s (dT = T_s - T_R), OIL steam rate, X_SF. Heated area = pay volume
    with T - T_R >= dT/2, divided by h. Returns dict of time series."""
    g = build_grid(layers_h=[h])
    sol = ThermalRZ(g)
    p = steam.psat_pa(T_s_C)
    rm, rq, rl, q = injection_rows(g, np.array([1.0]), P.STEAM_KGS, p)
    dT = T_s_C - T_R
    t, ts, A, rh = 0.0, [], [], []
    for dt in time_steps(t_end_d * P.DAY_S):
        sol.step_adaptive(dt, p, rm, rq, rl)
        t += dt
        if abs(t / record_every_s - round(t / record_every_s)) < 1e-9:
            ts.append(t); A.append(sol.heated_area(0.5 * dT)); rh.append(sol.radius_where(sol.layer_theta_max()[0], 0.5 * dT))
    ts = np.asarray(ts)
    return {"t_s": ts, "A_grid": np.asarray(A), "A_ml": ml_area(ts, q, h, dT), "r_half": np.asarray(rh),
            "q_heat_W": q, "dT": dT, "eps_max": sol.eps_max}
