"""T05 done-when checks (3B 4.5 table)."""
import pytest

from twin import wellbore as W


@pytest.mark.parametrize("q, target, tol", [(5.0, 41.0, 2.0), (10.0, 62.0, 4.0), (20.0, 91.0, 5.0)])
def test_wellhead_temperature_matches_3B_table(q, target, tol):
    assert W.ramey_T(0.0, 150.0, q) == pytest.approx(target, abs=tol)


def test_profile_bounds_and_heater():
    p = W.profile(150.0, 5.0, 0.3)
    assert p["T_C"][-1] == pytest.approx(150.0, abs=1e-9)          # at the pump
    assert all(p["T_C"][:-1] <= 150.0)
    hot = W.profile(150.0, 5.0, 0.3, heater_kW=6.0)
    assert hot["T_C"][-1] == pytest.approx(210.0, abs=1e-9)         # +10 C/kW at 5 m3/d
    assert (hot["mu_Pas"] <= p["mu_Pas"]).all()
