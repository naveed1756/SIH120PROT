"""T09 done-when checks: float margin, plunger sizing, onset, glide path, wave-equation cross-check."""
import numpy as np
import pytest

from twin import float_glide as FG
from twin import params as P
from twin import rodpump as RP


def test_v_fall_constant_matches_brief():
    # spec: v_fall ~= 5.13 / (K_C_DRAG mu) m/s for these rods
    assert FG.W_FALL * P.K_C_DRAG == pytest.approx(5.13, rel=0.03)


def test_harmonic_mean_equals_mean_viscosity():
    mu = np.array([0.5, 2.0, 8.0, 1.0])
    harm = len(mu) / np.sum(1.0 / FG.v_fall(mu))
    assert harm == pytest.approx(float(FG.v_fall(mu.mean())), rel=1e-12)


@pytest.fixture(scope="module")
def fg(cycle):
    df = cycle[1]
    return df, FG.series(df)


def test_plunger_is_standard_and_closest_to_band(fg):
    df, s = fg
    d_in, N_pk = FG.size_plunger(FG.production_frame(df).q_liq_m3d.values[0])
    assert d_in in P.PLUNGER_SIZES_IN
    assert P.PLUNGER_D_M == pytest.approx(d_in * P.IN_M)
    print(f"plunger {d_in} in, N_inflow at peak {N_pk:.2f} SPM (target 5-6)")


def test_onset_inside_cycle(fg):
    _, s = fg
    on = FG.onset_day(s.day, s.margin_base)
    assert on is not None and 10.0 <= on <= 150.0
    assert (s.margin_base[s.day < on] >= 0).all()


def test_glide_path_never_floats(fg):
    _, s = fg
    assert (s.margin_glide >= 0).all()
    assert (s.N_glide <= s.N_inflow + 1e-12).all()
    assert (s.N_glide <= 0.9 * s.N_float + 1e-12).all()


def test_heater_delays_onset(fg):
    df, s = fg
    on = FG.onset_day(s.day, s.margin_base)
    sh = FG.series(df, FG.HEATER_WHATIF_KW)
    m = 1.0 - (np.pi * P.STROKE_M * s.N_base / 60.0) / sh.v_fall.values
    on_h = FG.onset_day(s.day, m)
    assert on_h is None or on_h > on


def test_wave_equation_crosscheck(fg):
    """Min polished-rod load: > 0 well before onset, ~0 at onset, clipped after."""
    df, s = fg
    on = FG.onset_day(s.day, s.margin_base)
    N = float(s.N_base.iloc[0])
    days = [max(0.0, on - 30.0), on, min(on + 15.0, s.day.max())]
    cc = [FG.rod_card_at(df, d, N) for d in days]
    mins = [float(c["min_load_raw"][0]) for c in cc]
    rngs = [float(np.ptp(c["surf_load_raw"][0])) for c in cc]
    assert mins[0] > 0.0
    assert abs(mins[1]) <= 0.05 * rngs[1], "at the analytic onset the min load should be ~0"
    assert mins[2] < 0.0 and cc[2]["float"][0]
    assert (cc[2]["surf_load"][0] >= 0).all()
    print("cross-check min loads kN:", [round(m / 1e3, 2) for m in mins])
