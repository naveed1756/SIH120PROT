"""D1 card classifier (CLAUDE.md T11). XGBoost on ml.features, split by OPERATING RANGE:
train = mu <= 10 Pa.s and pump depth <= 1,050 m; test = every other card (extrapolation in
viscosity or depth). 5-fold stratified CV inside the training range is a secondary number.
Run: python -m ml.train_classifier   -> out/features.parquet, out/classifier_report.json
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from ml.card_library import load_cards
from ml.features import FEATURES, features
from twin import pumpbc as PB

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SEED = 42
MU_MAX, DEPTH_MAX = 10.0, 1050.0


def model():
    return XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                         random_state=SEED, n_jobs=2, tree_method="hist", eval_metric="mlogloss")


def build_features(force=False):
    f = OUT / "features.parquet"
    if f.exists() and not force:
        return pd.read_parquet(f)
    df = load_cards()
    df = df[df.keep].reset_index(drop=True)
    t0 = time.time()
    X = features(df)
    meta = df[["cls", "unit", "N", "S", "depth", "mu"]]
    out = pd.concat([meta, X], axis=1)
    out.to_parquet(f, index=False)
    print(f"features for {len(out)} cards in {time.time() - t0:.0f} s")
    return out


def main(force=False):
    d = build_features(force)
    y = d.cls.map({c: i for i, c in enumerate(PB.CLASSES)}).values
    X = d[FEATURES].values
    train = ((d.mu <= MU_MAX) & (d.depth <= DEPTH_MAX)).values
    test = ~train
    # secondary: 5-fold CV inside the training range
    cv = []
    for tr, va in StratifiedKFold(5, shuffle=True, random_state=SEED).split(X[train], y[train]):
        m = model()
        m.fit(X[train][tr], y[train][tr], sample_weight=compute_sample_weight("balanced", y[train][tr]))
        cv.append(f1_score(y[train][va], m.predict(X[train][va]), average="macro"))
    m = model()
    m.fit(X[train], y[train], sample_weight=compute_sample_weight("balanced", y[train]))
    pred = m.predict(X[test])
    labels = list(range(len(PB.CLASSES)))
    cm = confusion_matrix(y[test], pred, labels=labels)
    f1 = f1_score(y[test], pred, labels=labels, average=None, zero_division=0)
    rep = {
        "split": f"train: mu <= {MU_MAX:g} Pa.s and depth <= {DEPTH_MAX:g} m; test: all other cards",
        "n_train": int(train.sum()), "n_test": int(test.sum()),
        "n_test_per_class": {c: int((y[test] == i).sum()) for i, c in enumerate(PB.CLASSES)},
        "n_train_per_class": {c: int((y[train] == i).sum()) for i, c in enumerate(PB.CLASSES)},
        "macro_f1_test": float(f1_score(y[test], pred, average="macro")),
        "accuracy_test": float((pred == y[test]).mean()),
        "f1_test_per_class": {c: float(v) for c, v in zip(PB.CLASSES, f1)},
        "cv5_macro_f1_train_range": {"mean": float(np.mean(cv)), "std": float(np.std(cv)), "folds": [float(v) for v in cv]},
        "confusion_test": cm.tolist(), "classes": PB.CLASSES, "features": FEATURES,
        "feature_importance_gain": {k: float(v) for k, v in zip(FEATURES, m.feature_importances_)},
    }
    (OUT / "classifier_report.json").write_text(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("n_train", "n_test", "macro_f1_test", "accuracy_test",
                                        "cv5_macro_f1_train_range", "f1_test_per_class", "n_test_per_class")}, indent=1))
