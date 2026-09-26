"""T04 done-when checks (CLAUDE.md T04)."""
import numpy as np
import pytest

from twin import inflow
from twin import params as P


def test_cold_rate_18_bpd():
    q = inflow.cold_rate_m3s() * P.DAY_S / P.BBL_M3
    assert q == pytest.approx(18.0, abs=1.0)


def test_cycle_runs_under_5_minutes(cycle):
    assert cycle[2]["wall_s"] < 300.0


def test_peak_in_first_15_days_and_monotone_after_20(cycle):
    _, df, _ = cycle
    pr = df[df.phase == "production"]
    d = (pr.t_h.values - pr.t_h.values[0]) / 24.0
    q = pr.q_o_bpd.values
    assert d[np.argmax(q)] <= 15.0
    assert np.all(np.diff(q[d >= 20.0]) <= 0.0)


def test_production_average_is_reported(cycle, capsys):
    s = cycle[2]
    assert np.isfinite(s["prod_avg_oil_bpd"]) and s["prod_avg_oil_bpd"] > 0
    with capsys.disabled():
        print(f"\n[T04] production-average oil rate = {s['prod_avg_oil_bpd']:.1f} bbl/d "
              f"(brief target ~25-26; note band 20-40)")


def test_j_ratio_limits():
    mu_c = 11.7
    assert inflow.j_ratio(mu_c, mu_c, 10.0) == pytest.approx(1.0)
    lim = np.log(P.RE_M / P.RW_M) / np.log(P.RE_M / 10.0)
    assert inflow.j_ratio(1e-9, mu_c, 10.0) == pytest.approx(lim, rel=1e-6)


def test_water_cut_curve():
    assert inflow.water_cut(0.0) == pytest.approx(P.FW0)
    assert inflow.water_cut(1e4) == pytest.approx(P.FW_INF)
    assert np.all(np.diff(inflow.water_cut(np.linspace(0, 120, 50))) < 0)
