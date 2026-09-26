"""T03 done-when checks (CLAUDE.md T03)."""
import numpy as np
import pytest
from scipy.special import erfc

from twin import params as P
from twin import thermal_rz as TR


def test_energy_closure_every_step(cycle):
    res, _, _ = cycle
    assert np.max(np.abs(res["eps_steps"])) < 0.01


def test_temperatures_physical(cycle):
    res, _, _ = cycle
    T = res["T_snap"]
    assert T.min() >= P.T_R_C - 0.01
    assert T.max() <= res["T_sat_inj"] + 0.01


@pytest.fixture(scope="module")
def ml():
    return TR.marx_langenheim_check(t_end_d=21.0)


@pytest.mark.parametrize("day, target_m2", [(14, 276.0), (21, 403.0)])
def test_marx_langenheim_within_20pct(ml, day, target_m2):
    i = int(np.argmin(np.abs(ml["t_s"] - day * P.DAY_S)))
    assert abs(ml["A_grid"][i] / target_m2 - 1.0) < 0.20
    # our analytical G(t_D) reproduces the 3A worked example within 1.5 %
    assert abs(ml["A_ml"][i] / target_m2 - 1.0) < 0.015
    assert ml["eps_max"] < 0.01


def test_override_top_layer_wider_at_end_of_injection(cycle):
    _, df, _ = cycle
    end = df[df.phase == "injection"].iloc[-1]
    assert end.r_h_L1 > end.r_h_L3


def test_conduction_slab_matches_erf():
    """1-D slab (one radial column, insulated sides) with an initial step of dT
    against theta = dT/2 * erfc(z / (2 sqrt(alpha t)))."""
    nz, dz, lam, M, dT = 200, 0.1, 2.0, 2.4e6, 100.0
    z_edges = np.linspace(-nz * dz / 2, nz * dz / 2, nz + 1)
    g = TR.Grid(np.array([P.RW_M, 1.0]), z_edges, np.full(nz, -1), np.array([]),
                np.full((nz, 1), M), np.full((nz, 1), lam), outer_fixed=False, vert_fixed=False)
    sol = TR.ThermalRZ(g)
    zc = g.zc
    sol.H = np.where(zc < 0, M * dT, 0.0)
    t_end = 10 * P.DAY_S
    for dt in TR.time_steps(t_end):
        sol.step_adaptive(dt, sol.p_abs)
    alpha = lam / M
    exact = 0.5 * dT * erfc(zc / (2.0 * np.sqrt(alpha * t_end)))
    assert np.max(np.abs(sol.theta() - exact)) / dT < 0.03


def test_injection_heat_rate_about_1p6_MW(cycle):
    res, _, _ = cycle
    assert 1.4e6 < res["q_heat_W"] < 1.8e6
