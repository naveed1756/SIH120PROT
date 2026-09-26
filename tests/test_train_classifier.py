"""T11: runs and reports (no minimum score). Checks the split is by operating range."""
import json
from pathlib import Path

import pytest

OUT = Path(__file__).resolve().parents[1] / "out"
pytestmark = pytest.mark.skipif(not (OUT / "classifier_report.json").exists(), reason="run python -m ml.train_classifier")


def test_report_complete_and_split_by_range():
    import pandas as pd
    from ml.train_classifier import DEPTH_MAX, MU_MAX
    r = json.loads((OUT / "classifier_report.json").read_text())
    assert 0.0 <= r["macro_f1_test"] <= 1.0 and len(r["f1_test_per_class"]) == 9
    d = pd.read_parquet(OUT / "features.parquet", columns=["mu", "depth"])
    train = (d.mu <= MU_MAX) & (d.depth <= DEPTH_MAX)
    assert int(train.sum()) == r["n_train"] and int((~train).sum()) == r["n_test"]
    print(f"[T11] macro-F1 test {r['macro_f1_test']:.3f}, CV {r['cv5_macro_f1_train_range']['mean']:.3f}")


def test_features_finite():
    import numpy as np
    import pandas as pd
    from ml.features import FEATURES
    d = pd.read_parquet(OUT / "features.parquet", columns=FEATURES)
    assert np.isfinite(d.values).all()
