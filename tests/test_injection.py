"""T14 done-when: sandface steam quality by VIT grade (3B Fig. 3) and bare tubing condensing."""
import pytest

from twin import injection as I
from twin import params as P

TARGET = {"E": 0.61, "D": 0.54, "C": 0.37, "B": 0.25}


@pytest.fixture(scope="module")
def res():
    return I.grades()


@pytest.mark.parametrize("g", list(TARGET))
def test_grade_quality(res, g):
    print(f"[T14] grade {g}: x_bh = {res[g]['x_bh']:.3f} (3B {TARGET[g]}), loss {res[g]['heat_loss_W'] / 1e3:.0f} kW")
    assert abs(res[g]["x_bh"] - TARGET[g]) <= 0.06


def test_bare_tubing_condenses_before_pay(res):
    zc = res["bare"]["z_condensed"]
    print(f"[T14] bare tubing: all condensed at {zc:.0f} m (3B: ~635 m after 1 day)")
    assert zc is not None and zc < P.TOP_PAY_M
