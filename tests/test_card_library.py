"""T07 done-when: every class >= 90 % valid (closed, finite). Reads out/cards.parquet
(generate with `python -m ml.card_library`)."""
from pathlib import Path

import pandas as pd
import pytest

from twin import pumpbc as PB

CARDS = Path(__file__).resolve().parents[1] / "out" / "cards.parquet"


@pytest.fixture(scope="module")
def cards():
    if not CARDS.exists():
        pytest.skip("out/cards.parquet not generated yet (python -m ml.card_library)")
    return pd.read_parquet(CARDS, columns=["cls", "valid", "label_ok", "keep"])


def test_all_classes_present(cards):
    assert set(cards.cls) == set(PB.CLASSES)


@pytest.mark.parametrize("c", PB.CLASSES)
def test_class_at_least_90pct_valid(cards, c):
    assert cards[cards.cls == c].valid.mean() >= 0.90
