"""T15 (Could): the L0 cycle model behaves physically and the Pareto run reports (no score threshold)."""
import json
from pathlib import Path

import numpy as np
import pytest

from optim import l0_cycle as L0

OUT = Path(__file__).resolve().parents[1] / "out"


def test_l0_monotone_in_steam():
    r = L0.evaluate(np.array([800.0, 1340.0, 2200.0]), 3.1, 0.65, 0.55)
    assert np.all(np.diff(r["r_h_m"]) > 0) and np.all(np.diff(r["Np_bbl"]) > 0)
    assert np.all(np.isfinite(r["J1_bbl_per_day"])) and np.all(r["SOR_m3_per_m3"] > 0)


@pytest.mark.skipif(not (OUT / "pareto.json").exists(), reason="run python -m optim.pareto")
def test_front_is_non_dominated_and_reported():
    r = json.loads((OUT / "pareto.json").read_text())
    F = np.array([[-f["J1_q50"], f["SOR_q50"]] for f in r["front"]])
    dominated = [(np.all(F <= F[i], 1) & np.any(F < F[i], 1)).any() for i in range(len(F))]
    assert not any(dominated)
    print(f"[T15] front {len(F)} designs; knee M_s {r['knee']['M_s_t']:.0f} t, J1 {r['knee']['J1_q50']:.1f}, "
          f"SOR {r['knee']['SOR_q50']:.3f}; proxy R2 {r['proxy_J1']['r2_holdout']:.3f}/{r['proxy_SOR']['r2_holdout']:.3f}")
