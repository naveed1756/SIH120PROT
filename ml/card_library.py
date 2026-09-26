"""Synthetic dynamometer-card library, 9 classes (CLAUDE.md T07; innovation I6).

Samples operating conditions per the brief, simulates every card with the T06
rod-string model and the T07 pump boundary condition, adds measurement noise to
the surface card, checks validity and label consistency, and saves
out/cards.parquet. Run: python -m ml.card_library [n_per_class]
"""
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

from twin import kinematics as K
from twin import params as P
from twin import pumpbc as PB
from twin import rodpump as RP

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
SEED = 42
MU_NONFLOAT_CAP = 3.0         # brief: non-float classes capped at ~3 Pa.s
MU_FLOAT = (5.0, 40.0)        # brief: rod_float effective 5-40 Pa.s
CLOSURE_MAX = 0.05            # validity: |F(3T) - F(2T)| <= 5 % of the load range (periodic, closed)


def mu_float_threshold(v_down, rho_f=P.RHO_FLUID_ROD):
    """Viscosity at which the terminal rod-fall speed equals v_down (float onset)."""
    return ((P.RHO_STEEL - rho_f) * P.G * RP.A_ROD * RP.LN_GAP) / (P.K_C_DRAG * 2.0 * np.pi * v_down)


def sample(n_per_class, seed=SEED):
    rng = np.random.default_rng(seed)
    rows = []
    for ci, c in enumerate(PB.CLASSES):
        for _ in range(n_per_class):
            unit = int(rng.random() < 0.2)
            S = rng.uniform(4.0, 7.0) if unit else rng.uniform(2.5, 4.0)
            df = rng.uniform(0.5, 0.65) if unit else 0.5
            n_max = min(8.0, K.max_hydraulic_spm(S, df)) if unit else 8.0
            depth = rng.uniform(900.0, 1150.0)
            L = depth * rng.uniform(0.3, 0.9) if c == "rod_parted" else depth
            p_int = rng.uniform(5.0, 40.0)
            d_in = rng.choice(P.PLUNGER_SIZES_IN)
            if c == "rod_float":
                mu = float(np.exp(rng.uniform(*np.log(MU_FLOAT))))
                # choose N so the carrier bar out-runs the falling rods (float is the label)
                v_fall = (P.RHO_STEEL - P.RHO_FLUID_ROD) * P.G * RP.A_ROD * RP.LN_GAP / (P.K_C_DRAG * 2 * np.pi * mu)
                n_lo = max(2.0, 1.15 * v_fall * 60.0 / (np.pi * S))
                N = rng.uniform(n_lo, n_max) if n_lo < n_max else n_max
            else:
                N = rng.uniform(2.0, n_max)
                v_dn = K.max_down_speed(N, S, unit, df)
                cap = min(MU_NONFLOAT_CAP, 0.8 * mu_float_threshold(v_dn))
                mu = float(np.exp(rng.uniform(np.log(0.05), np.log(max(cap, 0.06)))))
            F_fl, p_dis, p_i = PB.fluid_load(p_int, d_in, depth)
            rows.append(dict(cls=c, cid=ci, unit=unit, N=N, S=S, down_fraction=df, depth=depth, L=L,
                             p_int_ksc=p_int, plunger_in=d_in, mu=mu, F_fl=F_fl, R=p_dis / p_i,
                             fill=rng.uniform(0.4, 0.8), k_leak=rng.uniform(0.2, 0.6),
                             alpha=rng.uniform(0.2, 0.5), noise=rng.uniform(0.02, 0.05),
                             jitter=rng.uniform(-0.01, 0.01), seed=int(rng.integers(1 << 31))))
    return pd.DataFrame(rows)


def _chunks(df, size=400):
    """Group cards so each batch has similar rod length (node spacing ~10 m) and period."""
    df = df.assign(Lb=np.where(df.cls == "rod_parted", (df.L // 100).astype(int), -1), Tp=60.0 / df.N)
    out = []
    for _, g in df.groupby("Lb"):
        g = g.sort_values("Tp")
        out += [g.iloc[i:i + size] for i in range(0, len(g), size)]
    return out


def _run_chunk(g):
    r = RP.simulate(g.L.values, g.N.values, g.S.values, g.mu.values, g.cid.values, g.F_fl.values,
                    unit=g.unit.values, down_fraction=g.down_fraction.values, fill=g.fill.values,
                    k_leak=g.k_leak.values, alpha=g.alpha.values, R=g.R.values)
    return g.index.values, r


def generate(n_per_class=1500, seed=SEED, processes=2, verbose=True):
    df = sample(n_per_class, seed)
    t0 = time.time()
    M = P.CARD_POINTS
    arrays = {k: np.full((len(df), M), np.nan) for k in ("surf_pos", "surf_load", "dh_pos", "dh_load")}
    flt = np.zeros(len(df), bool); minraw = np.zeros(len(df)); Sp = np.zeros(len(df))
    closure = np.full(len(df), np.nan)
    chunks = _chunks(df)
    with Pool(processes) as pool:
        for k, (idx, r) in enumerate(pool.imap_unordered(_run_chunk, chunks)):
            for key in arrays:
                arrays[key][idx] = r[key]
            flt[idx] = r["float"]; minraw[idx] = r["min_load_raw"]; Sp[idx] = r["S_p"]
            closure[idx] = r["closure"]
            if verbose:
                print(f"  chunk {k+1}/{len(chunks)}  ({time.time()-t0:.0f} s)", flush=True)
    # validity on the clean simulated card (before measurement noise)
    finite = np.all(np.isfinite(np.concatenate([arrays[k] for k in arrays], 1)), 1)
    valid = finite & (closure <= CLOSURE_MAX)
    # measurement noise on the SURFACE card only (the downhole card is computed)
    rng = np.random.default_rng(seed + 1)
    rngs = arrays["surf_load"].max(1) - arrays["surf_load"].min(1)
    noisy = arrays["surf_load"] + rng.normal(size=arrays["surf_load"].shape) * (df.noise.values * rngs)[:, None]
    arrays["surf_load"] = np.maximum(noisy, 0.0)
    arrays["surf_pos"] = arrays["surf_pos"] * (1.0 + df.jitter.values)[:, None]
    # label consistency: float flag must agree with the label
    consistent = np.where(df.cls.values == "rod_float", flt, ~flt)
    df = df.assign(float_flag=flt, min_load_raw=minraw, S_p=Sp, closure=closure, valid=valid,
                   label_ok=consistent, keep=valid & consistent)
    for key, a in arrays.items():
        df[key] = list(a.astype(np.float32))
    df.attrs["runtime_s"] = time.time() - t0
    return df


def summary(df):
    g = df.groupby("cls", sort=False)
    return pd.DataFrame({"n": g.size(), "valid_frac": g.valid.mean(), "label_ok_frac": g.label_ok.mean(),
                         "kept": g.keep.sum()}).reindex(PB.CLASSES)


def main(n_per_class=1500):
    OUT.mkdir(exist_ok=True)
    df = generate(n_per_class)
    df.to_parquet(OUT / "cards.parquet", index=False)
    s = summary(df)
    print(s.to_string())
    print(f"runtime {df.attrs['runtime_s']:.0f} s")
    return df, s


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1500)


def load_cards(columns=None):
    """Read the card library: out/cards.parquet, or out/cards_part*.parquet if it was
    delivered in parts (each file < 20 MB for transfer)."""
    single = OUT / "cards.parquet"
    if single.exists():
        return pd.read_parquet(single, columns=columns)
    parts = sorted(OUT.glob("cards_part*.parquet"))
    if not parts:
        raise FileNotFoundError("no card library in out/ (run: python -m ml.card_library)")
    return pd.concat([pd.read_parquet(p, columns=columns) for p in parts], ignore_index=True)


def split_for_transfer(n_parts=2):
    """Write out/cards_part{i}.parquet (zstd) from out/cards.parquet."""
    df = pd.read_parquet(OUT / "cards.parquet")
    for i, idx in enumerate(np.array_split(np.arange(len(df)), n_parts), 1):
        df.iloc[idx].to_parquet(OUT / f"cards_part{i}.parquet", index=False, compression="zstd",
                                compression_level=19)
