"""Polished-rod kinematics (task T06). y = position, positive up, 0 at the bottom.

Beam unit: sinusoid y = S/2 (1 - cos(2 pi N t / 60)).
Hydraulic long-stroke unit: trapezoidal velocity, acceleration HYD_ACCEL, separate
plateau speeds up and down; down_fraction = share of the period spent on the
downstroke (> 0.5 means a slower downstroke).
All functions are vectorised over cards (arrays broadcast together).
"""
import numpy as np

from twin import params as P


def period_s(N_spm):
    return 60.0 / np.asarray(N_spm, dtype=float)


def plateau_speed(S, tau, a=P.HYD_ACCEL):
    """Plateau speed covering distance S in time tau with accel/decel a:
    S = v tau - v^2 / a  ->  v = (a tau - sqrt(a^2 tau^2 - 4 a S)) / 2."""
    S = np.asarray(S, float); tau = np.asarray(tau, float)
    disc = a * a * tau * tau - 4.0 * a * S
    if np.any(disc < 0):
        raise ValueError("hydraulic stroke infeasible: half-stroke time < 2*sqrt(S/a)")
    return 0.5 * (a * tau - np.sqrt(disc))


def hydraulic_speeds(N_spm, S, down_fraction, a=P.HYD_ACCEL):
    T = period_s(N_spm)
    Td = np.asarray(down_fraction, float) * T
    Tu = T - Td
    return plateau_speed(S, Tu, a), plateau_speed(S, Td, a), Tu, Td


def max_hydraulic_spm(S, down_fraction, a=P.HYD_ACCEL):
    """Largest N for which both half-strokes are feasible."""
    f = min(float(down_fraction), 1.0 - float(down_fraction))
    return 60.0 * f / (2.0 * np.sqrt(S / a))


def _trap_pos(t, tau, v, a, S):
    """Distance covered at time t in a trapezoidal move of length S over tau."""
    ta = v / a
    return np.where(t < ta, 0.5 * a * t * t,
                    np.where(t <= tau - ta, 0.5 * a * ta * ta + v * (t - ta),
                             S - 0.5 * a * np.maximum(tau - t, 0.0) ** 2))


def _trap_vel(t, tau, v, a):
    ta = v / a
    return np.where(t < ta, a * t, np.where(t <= tau - ta, v, a * np.maximum(tau - t, 0.0)))


def position(t, N_spm, S, unit=0, down_fraction=0.5, a=P.HYD_ACCEL):
    """y(t); unit 0 = beam, 1 = hydraulic. Arrays broadcast."""
    t = np.asarray(t, float); N = np.asarray(N_spm, float); S = np.asarray(S, float)
    unit = np.asarray(unit); df = np.asarray(down_fraction, float)
    T = 60.0 / N
    y_beam = 0.5 * S * (1.0 - np.cos(2.0 * np.pi * t / T))
    if not np.any(unit == 1):
        return y_beam
    Td = df * T
    Tu = T - Td
    dfh = np.where(unit == 1, df, 0.5)
    vu, vd, Tu, Td = hydraulic_speeds(np.where(unit == 1, N, 1e-3), S, dfh, a)
    tau = np.mod(t, T)
    up = tau < Tu
    y_h = np.where(up, _trap_pos(tau, Tu, vu, a, S), S - _trap_pos(tau - Tu, Td, vd, a, S))
    return np.where(unit == 1, y_h, y_beam)


def velocity(t, N_spm, S, unit=0, down_fraction=0.5, a=P.HYD_ACCEL):
    t = np.asarray(t, float); N = np.asarray(N_spm, float); S = np.asarray(S, float)
    unit = np.asarray(unit); df = np.asarray(down_fraction, float)
    T = 60.0 / N
    v_beam = 0.5 * S * (2.0 * np.pi / T) * np.sin(2.0 * np.pi * t / T)
    if not np.any(unit == 1):
        return v_beam
    dfh = np.where(unit == 1, df, 0.5)
    vu, vd, Tu, Td = hydraulic_speeds(np.where(unit == 1, N, 1e-3), S, dfh, a)
    tau = np.mod(t, T)
    v_h = np.where(tau < Tu, _trap_vel(tau, Tu, vu, a), -_trap_vel(tau - Tu, Td, vd, a))
    return np.where(unit == 1, v_h, v_beam)


def max_down_speed(N_spm, S, unit=0, down_fraction=0.5):
    """v_down_max: pi S N / 60 (beam) or the hydraulic downstroke plateau."""
    if unit == 1:
        return float(hydraulic_speeds(N_spm, S, down_fraction)[1])
    return float(np.pi * S * N_spm / 60.0)


class Kin:
    """Precomputed per-card kinematics for fast stepping (same results as position())."""

    def __init__(self, N_spm, S, unit, down_fraction, a=P.HYD_ACCEL):
        self.N = np.asarray(N_spm, float); self.S = np.asarray(S, float)
        self.unit = np.asarray(unit).astype(int); self.a = a
        self.T = 60.0 / self.N
        self.w = 2.0 * np.pi / self.T
        self.hyd = self.unit == 1
        df = np.where(self.hyd, np.asarray(down_fraction, float), 0.5)
        if self.hyd.any():
            vu, vd, Tu, Td = hydraulic_speeds(np.where(self.hyd, self.N, 1.0),
                                              np.where(self.hyd, self.S, 1e-3), df, a)
        else:
            vu = vd = Tu = Td = np.zeros_like(self.N)
        self.vu, self.vd, self.Tu, self.Td = vu, vd, Tu, Td

    def pos(self, t):
        y = 0.5 * self.S * (1.0 - np.cos(self.w * t))
        if self.hyd.any():
            tau = np.mod(t, self.T)
            up = tau < self.Tu
            yh = np.where(up, _trap_pos(tau, self.Tu, self.vu, self.a, self.S),
                          self.S - _trap_pos(tau - self.Tu, self.Td, self.vd, self.a, self.S))
            y = np.where(self.hyd, yh, y)
        return y
