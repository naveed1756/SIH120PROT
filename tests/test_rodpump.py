"""T06 done-when checks (task T06) plus kinematics sanity."""
import numpy as np
import pytest

from twin import kinematics as K
from twin import params as P
from twin import pumpbc as PB
from twin import rodpump as RP


def test_cfl_and_wave_speed():
    assert RP.A_WAVE == pytest.approx(5135.0, rel=0.01)
    assert RP.A_WAVE * P.DT_ROD_S / P.DX_ROD_M <= 1.0


def test_static_load_equals_buoyant_weight_plus_fluid_load():
    F_fl = PB.fluid_load(20.0, P.T06_TEST_PLUNGER_IN, P.ROD_LEN_M)[0]
    u = RP.static_profile(P.ROD_LEN_M, F_fl, int(P.ROD_LEN_M / P.DX_ROD_M))
    Fpr = RP.polished_rod_load(u, np.array([P.DX_ROD_M]))[0]
    w = RP.buoyant_weight_per_m()
    assert w == pytest.approx(26.2, abs=0.05)
    assert Fpr == pytest.approx(w * P.ROD_LEN_M + F_fl, rel=0.01)


@pytest.fixture(scope="module")
def normal_card():
    F_fl = PB.fluid_load(20.0, P.T06_TEST_PLUNGER_IN, P.ROD_LEN_M)[0]
    return RP.simulate(P.ROD_LEN_M, 5.0, 3.0, 0.5, PB.CID["normal"], F_fl)


def test_normal_card_closes_and_has_positive_area(normal_card):
    r = normal_card
    assert r["closure"][0] <= 0.01
    assert RP.card_area(r["surf_pos"], r["surf_load"])[0] > 0
    assert not r["float"][0]


def test_plunger_stroke_shorter_than_surface_stroke(normal_card, capsys):
    Sp = normal_card["S_p"][0]
    assert 0.0 < Sp < 3.0
    with capsys.disabled():
        print(f"\n[T06] plunger stroke on the normal card = {Sp:.3f} m (surface 3.0 m)")


def test_hydraulic_kinematics():
    N, S, df = 2.0, 6.0, 0.6
    t = np.linspace(0, 60 / N, 20001)
    y = K.position(t, N, S, 1, df)
    assert y.min() == pytest.approx(0.0, abs=1e-6) and y.max() == pytest.approx(S, abs=1e-6)
    vu, vd, Tu, Td = K.hydraulic_speeds(N, S, df)
    assert vd < vu                        # slower downstroke when down_fraction > 0.5
    kin = K.Kin(np.array([N]), np.array([S]), np.array([1]), np.array([df]))
    assert np.allclose(kin.pos(t[::997]), y[::997])
