"""Downhole pump boundary condition by failure class (CLAUDE.md T07).

A vectorised state machine over cards. Each step it reads the plunger position
(up positive), tracks the half-stroke (up / down) with a small hysteresis so
stress-wave ripples do not flip it, measures plunger travel since the last
reversal, and returns the rod tension at the pump F_p (N, tension positive).
F_fl = (p_dis - p_int) * A_p is the fluid load carried on the upstroke.
"""
import numpy as np

from twin import params as P

CLASSES = ["normal", "fluid_pound", "steam_gas_interference", "rod_float", "tv_leak",
           "sv_leak", "unseated", "rod_parted", "tagging"]
CID = {c: i for i, c in enumerate(CLASSES)}
CAUSES = {
    "normal": "full pump, valves working",
    "fluid_pound": "incomplete pump fillage; plunger hits the fluid",
    "steam_gas_interference": "steam or gas in the barrel compresses slowly",
    "rod_float": "rods cannot fall through viscous oil",
    "tv_leak": "travelling valve leaks; load bleeds off on the upstroke",
    "sv_leak": "standing valve leaks; load bleeds on the downstroke",
    "unseated": "pump pulled off its hold-down; no fluid load",
    "rod_parted": "rod string broken; only rod weight above the break",
    "tagging": "plunger strikes the bottom of the pump",
}


def area_plunger(d_in):
    return np.pi * (np.asarray(d_in, float) * P.IN_M) ** 2 / 4.0


def fluid_load(p_int_ksc, d_in, depth_m, rho_f=P.RHO_FLUID_ROD, p_thp_ksc=P.P_THP_KSC):
    """F_fl = (p_dis - p_int) A_p with p_dis = THP + rho_f g depth (N). Also returns p_dis, p_int (Pa)."""
    p_dis = p_thp_ksc * P.KSC_PA + rho_f * P.G * np.asarray(depth_m, float)
    p_int = np.asarray(p_int_ksc, float) * P.KSC_PA
    return (p_dis - p_int) * area_plunger(d_in), p_dis, p_int


class PumpBC:
    """Per-card pump state. Arrays of length n (one entry per card).
    cls: class index; F_fl: fluid load; S0: initial plunger-stroke estimate (m);
    fill: fillage f (pound / gas); k_leak (tv_leak); alpha (sv_leak);
    R: p_dis/p_int (gas); Tu: upstroke duration (s) for tv_leak's normalised time."""

    def __init__(self, cls, F_fl, S0, y0, fill=None, k_leak=None, alpha=None, R=None, Tu=None, T=None):
        n = len(cls)
        z = np.zeros(n)
        self.cls = np.asarray(cls)
        self.F_fl = np.asarray(F_fl, float)
        self.S_p = np.asarray(S0, float).copy()
        self.fill = z + 1.0 if fill is None else np.asarray(fill, float)
        self.k = z if k_leak is None else np.asarray(k_leak, float)
        self.alpha = z if alpha is None else np.asarray(alpha, float)
        self.R = z + 10.0 if R is None else np.asarray(R, float)
        self.Tu = z + 1.0 if Tu is None else np.asarray(Tu, float)
        self.Td = (z + 1.0 if T is None else np.asarray(T, float)) - self.Tu
        self.t_tag = z - 1e9                    # last tagging impulse
        self.down = np.zeros(n, bool)           # start of upstroke
        self.bottom = np.asarray(y0, float).copy()
        self.top = self.bottom.copy()
        self.ext = self.bottom.copy()           # running extreme in the current half
        self.t_sw = z.copy()                    # time of the last reversal
        self.s_sw = z.copy()                    # travel at which the reversal was detected
        self.F = z.copy()
        self.F_sw = z.copy()                    # load at the last reversal

    def update(self, y_p, t):
        """Advance the state machine with plunger position y_p (up +) at time t; return F_p."""
        h = P.HYST_FRAC * self.S_p
        # --- reversal detection with hysteresis
        up = ~self.down
        self.ext = np.where(up, np.maximum(self.ext, y_p), np.minimum(self.ext, y_p))
        dwell = t - self.t_sw
        to_down = up & (y_p < self.ext - h) & (dwell > P.MIN_DWELL_FRAC * self.Tu)
        to_up = self.down & (y_p > self.ext + h) & (dwell > P.MIN_DWELL_FRAC * self.Td)
        if to_down.any():
            self.top = np.where(to_down, self.ext, self.top)
            self.S_p = np.where(to_down, np.maximum(self.top - self.bottom, 1e-3), self.S_p)
            self.t_sw = np.where(to_down, t, self.t_sw)
            self.s_sw = np.where(to_down, self.top - y_p, self.s_sw)
            self.F_sw = np.where(to_down, self.F, self.F_sw)
            self.ext = np.where(to_down, y_p, self.ext)
        if to_up.any():
            self.bottom = np.where(to_up, self.ext, self.bottom)
            self.t_sw = np.where(to_up, t, self.t_sw)
            self.s_sw = np.where(to_up, y_p - self.bottom, self.s_sw)
            self.F_sw = np.where(to_up, self.F, self.F_sw)
            self.t_tag = np.where(to_up & (self.cls == CID["tagging"]), t, self.t_tag)
            self.ext = np.where(to_up, y_p, self.ext)
        self.down = (self.down | to_down) & ~to_up

        c, Ff, Sp = self.cls, self.F_fl, self.S_p
        s_up = np.clip(y_p - self.bottom, 0.0, None)
        s_dn = np.clip(self.top - y_p, 0.0, None)
        ramp_up = np.clip((s_up - self.s_sw) / (P.RAMP_FRAC * Sp), 0.0, 1.0)
        ramp_dn = np.clip(1.0 - (s_dn - self.s_sw) / (P.RAMP_FRAC * Sp), 0.0, 1.0)
        dt_sw = t - self.t_sw

        # --- upstroke
        tau = np.clip(dt_sw / self.Tu, 0.0, 1.0)
        F_up = Ff * ramp_up
        F_up = np.where(c == CID["tv_leak"], Ff * (1.0 - self.k * tau) * ramp_up, F_up)
        F_up = np.where((c == CID["tagging"]) & (t - self.t_tag < P.TAG_S) & ~self.down, P.TAG_FRAC * Ff, F_up)
        # --- downstroke
        Fs = self.F_sw                                  # downstroke starts from the load at reversal
        F_dn = Fs * ramp_dn
        s_gap = (1.0 - self.fill) * Sp
        pound = np.where(s_dn < s_gap, Fs,
                         Fs * np.clip(1.0 - (s_dn - s_gap) / (P.POUND_DROP_FRAC * Sp), 0.0, 1.0))
        F_dn = np.where(c == CID["fluid_pound"], pound, F_dn)
        V0 = np.maximum(s_gap, 1e-6)
        comp = (V0 / np.maximum(V0 - s_dn, 1e-9)) ** P.GAS_N          # p / p_int
        gas = Fs * np.clip(1.0 - (comp - 1.0) / np.maximum(self.R - 1.0, 1e-9), 0.0, 1.0)
        gas = np.where(s_dn >= V0, 0.0, gas)
        F_dn = np.where(c == CID["steam_gas_interference"], gas, F_dn)
        sv = np.maximum(self.alpha * Ff * np.clip(1.0 - s_dn / Sp, 0.0, 1.0), Fs * ramp_dn)
        F_dn = np.where(c == CID["sv_leak"], sv, F_dn)

        F = np.where(self.down, F_dn, F_up)
        F = np.where(c == CID["unseated"], 0.05 * Ff, F)
        F = np.where(c == CID["rod_parted"], 0.0, F)
        self.F = F
        return F
