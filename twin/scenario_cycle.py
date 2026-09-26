"""One full CSS cycle on BGW-SYN-01: injection -> soak -> production (task T04).

Couples T1-A (thermal_rz) with T1-C lite (inflow) at a one-step lag and writes
  out/thermal.npz     all series + 6-hourly T[t, z, r] snapshots
  out/cycle.parquet   hourly table: t_h, phase, q_o, q_w, f_w, q_liq, r_h per layer,
                      T_in, T_bar per layer, E_res (+ bbl/d copies and budget)
Run:  python -m twin.scenario_cycle
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd

from twin import inflow
from twin import params as P
from twin import thermal_rz as TR

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"


def to_frame(res):
    to_bpd = P.DAY_S / P.BBL_M3
    df = pd.DataFrame({
        "t_h": res["t_h"], "phase": res["phase"],
        "q_o": res["q_o"], "q_w": res["q_w"], "f_w": res["f_w"], "q_liq": res["q_liq"],
        "q_o_bpd": res["q_o"] * to_bpd, "q_liq_bpd": res["q_liq"] * to_bpd,
        "T_in": res["T_in"], "E_res": res["E_res"],
        "E_sf": res["E_sf"], "E_pay": res["dE_pay"], "E_cap": res["dE_cap"], "E_base": res["dE_base"],
        "E_prod": res["E_prod"], "E_out": res["E_out"], "eps_rel": res["eps_rel"],
    })
    for k in range(res["r_h"].shape[1]):
        df[f"r_h_L{k+1}"] = res["r_h"][:, k]
        df[f"T_bar_L{k+1}"] = res["T_bar"][:, k]
    return df


def summary(df):
    prod = df[df.phase == "production"].copy()
    prod["t_d"] = (prod.t_h - prod.t_h.iloc[0]) / 24.0
    inj_end = df[df.phase == "injection"].iloc[-1]
    return {
        "cold_rate_bpd": inflow.cold_rate_m3s() * P.DAY_S / P.BBL_M3,
        "K_MD": P.K_MD,
        "prod_avg_oil_bpd": float(prod.q_o_bpd.mean()),
        "prod_peak_oil_bpd": float(prod.q_o_bpd.max()),
        "prod_peak_day": float(prod.t_d.iloc[int(prod.q_o_bpd.values.argmax())]),
        "r_h_end_inj_m": [float(inj_end[f"r_h_L{k}"]) for k in (1, 2, 3)],
        "eps_max": float(np.abs(df.eps_rel).max()),
    }


def main(save=True):
    OUT.mkdir(exist_ok=True)
    t0 = time.time()
    res = TR.run_cycle(save_path=OUT / "thermal.npz" if save else None, verbose=True)
    df = to_frame(res)
    if save:
        df.to_parquet(OUT / "cycle.parquet", index=False)
    s = summary(df)
    s["runtime_s"] = time.time() - t0
    return res, df, s


if __name__ == "__main__":
    _, _, s = main()
    for k, v in s.items():
        print(f"{k:>20s}: {v}")
