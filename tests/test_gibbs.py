"""T08 done-when: surface -> downhole round trip, RMS <= 5 % of the load range at mu <= 1 Pa.s."""
import numpy as np
import pytest

from twin import gibbs as G
from twin import params as P
from twin import pumpbc as PB
from twin import rodpump as RP

L, N, S = P.ROD_LEN_M, 5.0, 3.0


def roundtrip(cls, mu):
    F_fl = PB.fluid_load(20.0, P.T06_TEST_PLUNGER_IN, L)[0]
    n = int(L / P.DX_ROD_M)
    r = RP.simulate(np.array([L]), N, S, np.array([mu]), PB.CID[cls], F_fl, fill=0.6, n_nodes=n)
    pos, Fp = G.downhole_card(r["surf_pos"][0], r["surf_load_raw"][0], L, N, mu, n_nodes=n)
    return G.rms_error(Fp, r["dh_load"][0]), float(np.sqrt(np.mean((pos - r["dh_pos"][0]) ** 2)))


@pytest.mark.parametrize("cls", ["normal", "fluid_pound"])
@pytest.mark.parametrize("mu", [0.5, 1.0])
def test_roundtrip_low_viscosity(cls, mu):
    err, pos_err = roundtrip(cls, mu)
    print(f"[T08] {cls} mu {mu}: RMS {100 * err:.2f} % of range, position RMS {1000 * pos_err:.1f} mm")
    assert err <= 0.05


@pytest.mark.parametrize("cls", ["normal", "fluid_pound"])
def test_roundtrip_10_pas_reported(cls):
    err, _ = roundtrip(cls, 10.0)
    print(f"[T08] {cls} mu 10 (informative): RMS {100 * err:.2f} % of range")
    assert np.isfinite(err)
