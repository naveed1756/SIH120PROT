import numpy as np
import pytest

from twin import params as P
from twin import rheology as R


# ---- T02 done-when --------------------------------------------------------
def test_mu_oil_anchor_points():
    assert R.mu_oil(50.0) == pytest.approx(11.5, abs=0.5)     # Pa.s (OIL anchor)
    assert R.mu_oil(100.0) == pytest.approx(0.30, abs=0.05)
    assert R.mu_oil(200.0) == pytest.approx(0.011, abs=0.003)


@pytest.mark.parametrize("T", [25.0, 30.0, 40.0, 50.0, 60.0, 70.0, 100.0, 200.0, 300.0])
def test_herschel_bulkley_equals_walther_at_reference_shear(T):
    for reg in (True, False):
        rel = abs(R.mu_app(T, P.GDOT_REF, regularised=reg) / R.mu_oil(T) - 1.0)
        assert rel < 1e-9


def test_mixture_drops_10x_across_inversion_at_50C():
    lo = R.mu_mixture(50.0, P.F_INV - 2 * P.F_INV_W)
    hi = R.mu_mixture(50.0, P.F_INV + 2 * P.F_INV_W)
    assert lo / hi >= 10.0


def test_mixture_monotone_decreasing_through_and_above_inversion():
    # Spec T02 asks for monotone decreasing over all f_w. Pal-Rhodes (3A B.7),
    # which the spec itself specifies, makes a water-in-oil emulsion thicker
    # than the oil as water rises toward inversion, so the literal test
    # contradicts the doc model. Monotonicity is asserted from the inversion
    # band upward (see DEVINSTRUCT.md, design decisions).
    fw = np.linspace(P.F_INV - 2 * P.F_INV_W, 1.0, 400)
    for T in (40.0, 50.0, 80.0, 150.0):
        mu = R.mu_mixture(T, fw)
        assert np.all(np.diff(mu) <= 0.0)


def test_mixture_end_members_and_wo_emulsion_effect():
    for T in (40.0, 50.0, 100.0):
        assert R.mu_mixture(T, 0.0) == pytest.approx(R.mu_oil(T), rel=1e-3)
        # logistic weight is 0.9997 (not 1) at f_w = 1, so allow 1 %
        assert R.mu_mixture(T, 1.0) == pytest.approx(R.mu_water(T), rel=1e-2)
        # W/O emulsion below inversion is thicker than the dead oil (Pal-Rhodes)
        assert R.mu_mixture(T, 0.3) > R.mu_oil(T)


# ---- supporting checks -------------------------------------------------------
def test_density_and_thermal_properties_match_3A_table():
    assert R.rho(15.0) == pytest.approx(959.0, rel=1e-9)
    assert R.rho(50.0) == pytest.approx(937.0, abs=2.0)      # 3A 6.3: 937 kg/m3
    assert R.rho(200.0) == pytest.approx(838.0, abs=2.0)     # 3A 6.3: 838 kg/m3
    assert R.cp(50.0) == pytest.approx(1890.0, rel=0.01)     # 3A 6.3: 1.89 kJ/kgK
    assert R.cp(300.0) == pytest.approx(2760.0, rel=0.01)    # 3A 6.3: 2.76
    assert R.lam(50.0) == pytest.approx(0.119, abs=0.002)    # 3A 6.3: 0.119


def test_water_viscosity_iapws():
    assert R.mu_water(20.0) == pytest.approx(1.0e-3, rel=0.02)
    assert R.mu_water(100.0) == pytest.approx(2.82e-4, rel=0.02)


def test_viscosity_decreases_with_temperature():
    T = np.linspace(25, 300, 200)
    assert np.all(np.diff(R.mu_oil(T)) < 0)


def test_yield_stress_and_flow_index():
    assert R.tau_y(P.T_NN_C + 1) == 0.0
    assert R.n_index(P.T_NN_C + 1) == 1.0
    assert R.tau_y(P.T_PP_C) == pytest.approx(P.TAU0_PA)
    assert R.n_index(P.T_PP_C) == pytest.approx(P.N0_HB)
    # shear-thinning below T_NN: apparent viscosity higher at low shear
    assert R.mu_app(50.0, 1.0) > R.mu_app(50.0, 50.0) > R.mu_app(50.0, 500.0)
    # FC-1 cap: C_G * tau_y(T_R) <~ 0.03 Pa with C_G = 1 (3A 7.1)
    assert R.tau_y(P.T_R_C) <= 0.03


def test_envelope():
    assert not R.in_envelope(P.T_PP_C)
    assert R.in_envelope(50.0)
    assert not R.in_envelope(330.0)
