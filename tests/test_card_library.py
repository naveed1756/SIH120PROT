"""T07 done-when: every class >= 90 % valid (closed, finite). Reads out/cards.parquet
(generate with `python -m ml.card_library`)."""
import pytest

from twin import pumpbc as PB

from ml.card_library import load_cards


@pytest.fixture(scope="module")
def cards():
    try:
        return load_cards(columns=["cls", "valid", "label_ok", "keep"])
    except FileNotFoundError:
        pytest.skip("card library not generated yet (python -m ml.card_library)")


def test_all_classes_present(cards):
    assert set(cards.cls) == set(PB.CLASSES)


@pytest.mark.parametrize("c", PB.CLASSES)
def test_class_at_least_90pct_valid(cards, c):
    assert cards[cards.cls == c].valid.mean() >= 0.90
