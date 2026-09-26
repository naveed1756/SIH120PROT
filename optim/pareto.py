"""O3 stage v0: Pareto front of CSS designs on a quantile-XGBoost proxy of the L0 model (T15).

20k scrambled Sobol designs -> L0 (optim.l0_cycle) -> XGBoost reg:quantileerror (alpha 0.1/0.5/0.9)
for J1 (oil per cycle-day) and SOR -> NSGA-II (pop 200, 150 generations) on the median proxy:
maximise J1, minimise SOR. The front is re-checked on the L0 model itself.
Run: python -m optim.pareto  -> out/pareto.json, out/pareto_samples.parquet
"""
import json
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from scipy.stats import qmc
from xgboost import XGBRegressor

from optim import l0_cycle as L0
from twin import params as P

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SEED = 42
N_SOBOL = 20_000
ALPHAS = np.array([0.1, 0.5, 0.9])
KEYS = list(P.DESIGN_BOUNDS)
LO = np.array([P.DESIGN_BOUNDS[k][0] for k in KEYS])
HI = np.array([P.DESIGN_BOUNDS[k][1] for k in KEYS])


def to_design(u):
    return LO + np.asarray(u) * (HI - LO)


def l0(X):
    r = L0.evaluate(X[:, 0], X[:, 1], X[:, 2], X[:, 3])
    return r["J1_bbl_per_day"], r["SOR_m3_per_m3"], r


def quantile_model():
    return XGBRegressor(objective="reg:quantileerror", quantile_alpha=ALPHAS, n_estimators=600, max_depth=6,
                        learning_rate=0.05, subsample=0.8, colsample_bytree=1.0, random_state=SEED, n_jobs=2,
                        tree_method="hist")


def fit_proxy(U, y):
    idx = np.random.default_rng(SEED).permutation(len(U))
    n_tr = int(0.8 * len(U))
    tr, te = idx[:n_tr], idx[n_tr:]
    m = quantile_model().fit(U[tr], y[tr])
    q = m.predict(U[te])
    med = q[:, 1]
    r2 = 1.0 - np.sum((y[te] - med) ** 2) / np.sum((y[te] - y[te].mean()) ** 2)
    cover = float(np.mean((y[te] >= q[:, 0]) & (y[te] <= q[:, 2])))
    m = quantile_model().fit(U, y)                       # final model on all samples
    return m, {"r2_holdout": float(r2), "p10_p90_coverage_holdout": cover, "n_train": n_tr, "n_holdout": len(te)}


class ProxyProblem(Problem):
    def __init__(self, mJ, mS):
        super().__init__(n_var=4, n_obj=2, xl=np.zeros(4), xu=np.ones(4))
        self.mJ, self.mS = mJ, mS

    def _evaluate(self, U, out, *args, **kwargs):
        out["F"] = np.column_stack([-self.mJ.predict(U)[:, 1], self.mS.predict(U)[:, 1]])


def knee(F):
    """Point of the (min, min) front farthest from the line through its normalised extremes."""
    f = (F - F.min(0)) / np.maximum(np.ptp(F, 0), 1e-12)
    a, b = f[np.argmin(f[:, 0])], f[np.argmin(f[:, 1])]
    v = b - a
    d = np.abs(v[0] * (f[:, 1] - a[1]) - v[1] * (f[:, 0] - a[0])) / max(np.linalg.norm(v), 1e-12)
    return int(np.argmax(d))


def main():
    t0 = time.time()
    with warnings.catch_warnings():               # 20k is not a power of 2 (spec's count kept)
        warnings.simplefilter("ignore", UserWarning)
        U = qmc.Sobol(4, scramble=True, seed=SEED).random(N_SOBOL)
    X = to_design(U)
    J1, SOR, raw = l0(X)
    t_l0 = time.time() - t0
    mJ, sJ = fit_proxy(U, J1)
    mS, sS = fit_proxy(U, SOR)
    res = minimize(ProxyProblem(mJ, mS), NSGA2(pop_size=200), ("n_gen", 150), seed=SEED, verbose=False)
    Uf = res.X
    Xf = to_design(Uf)
    qJ, qS = mJ.predict(Uf), mS.predict(Uf)
    J1v, SORv, rv = l0(Xf)                                # verification on L0 itself
    order = np.argsort(qS[:, 1])
    k = knee(np.column_stack([-qJ[:, 1], qS[:, 1]]))
    op = P.OIL_PRACTICE
    Xo = np.array([[op["M_s_t"], op["rate_tph"], op["x"], op["soak"]]])
    J1o, SORo, ro = l0(Xo)
    Uo = (Xo - LO) / (HI - LO)
    front = [{**dict(zip(KEYS, map(float, Xf[i]))), "J1_q10": float(qJ[i, 0]), "J1_q50": float(qJ[i, 1]),
              "J1_q90": float(qJ[i, 2]), "SOR_q10": float(qS[i, 0]), "SOR_q50": float(qS[i, 1]), "SOR_q90": float(qS[i, 2]),
              "J1_L0": float(J1v[i]), "SOR_L0": float(SORv[i]), "L_d": float(rv["L_d"][i]), "Np_bbl": float(rv["Np_bbl"][i])}
             for i in order]
    rep = {
        "n_sobol": N_SOBOL, "l0_runtime_s": t_l0, "proxy_J1": sJ, "proxy_SOR": sS,
        "front": front, "knee": front[int(np.nonzero(order == k)[0][0])],
        "oil_practice": {**op, "J1_L0": float(J1o[0]), "SOR_L0": float(SORo[0]), "L_d": float(ro["L_d"][0]),
                         "Np_bbl": float(ro["Np_bbl"][0]), "J1_proxy_q50": float(mJ.predict(Uo)[0, 1]),
                         "SOR_proxy_q50": float(mS.predict(Uo)[0, 1])},
        "front_verification": {"J1_mean_abs_rel_err": float(np.mean(np.abs(qJ[:, 1] - J1v) / J1v)),
                               "SOR_mean_abs_rel_err": float(np.mean(np.abs(qS[:, 1] - SORv) / SORv))},
        "share_L_capped": float(np.mean(raw["L_d"] >= P.L_MAX_D)),
        "runtime_s": time.time() - t0,
    }
    (OUT / "pareto.json").write_text(json.dumps(rep, indent=2))
    pd.DataFrame({**{k: X[:, i] for i, k in enumerate(KEYS)}, "J1": J1, "SOR": SOR, "L_d": raw["L_d"]}).to_parquet(
        OUT / "pareto_samples.parquet", index=False)
    return rep


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("proxy_J1", "proxy_SOR", "knee", "oil_practice", "front_verification",
                                        "share_L_capped", "runtime_s")}, indent=1))
