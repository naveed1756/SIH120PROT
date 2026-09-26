"""T12: export the data contracts for the web dashboard to web/public/data/.

Run after python -m twin.scenario_cycle, python -m twin.float_glide and the card library:
    python tools/export_web.py [--no-frames]

Contracts are those of CLAUDE.md T12. Additive extras (documented in DEVINSTRUCT.md):
- cycle_timeseries.json: T_wh_C, mu_tubing_eff_Pas and water_cut are null outside production (pump off);
  spm_* = 0 and float_margin* = 1 outside production. Extra keys: "day", "prod_start_h", and the
  6 kW heater what-if traces float_margin_heater, spm_float_heater, T_wh_heater_C, mu_tubing_eff_heater_Pas.
  events carry extra "spm_from", "spm_to", "onset_t_h" fields.
- thermal frames: one per 24 h (every 4th 6-h snapshot) to keep the web bundle small;
  f%04d.png are labelled 640 x 360 frames, tex_%04d.png are 256 x 128 textures. Each meta
  frame has an extra "tex" key; meta has "tex_r_range_m" / "tex_z_range_m" (elevation above
  the base of the pay, top row of the image = top of the range).
- rod_motion.json: contract keys hold the normal stroke; the float stroke is under "float".
- New files (not in the contract): cards_timeline.json and tubing_timeline.json feed the live
  card and tubing panels (every production day; baseline / glide / heater scenarios).
  "settled" = closure <= CLOSURE_MAX (5 %, the card-library validity rule). At near-water tubing
  viscosity (~0.002 Pa.s, days 8-10 on the glide path) the rod string is almost undamped, the
  3-stroke run has not settled and the ringing can dip below zero load: the UI must label such
  cards "transient, not settled" and must not report them as rod float.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "figures"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from twin import params as P  # noqa: E402
from twin import wellbore as W  # noqa: E402

OUT = ROOT / "out"
DATA = ROOT / "web" / "public" / "data"
FRAME_EVERY = 4                      # 6-h snapshots -> one frame per day
TEX_W, TEX_H = 256, 128
TEX_R = (0.1, 150.0)
T_MIN, T_MAX = 50.0, 310.0
PROFILE_DAYS = [5, 30, 60, 100]
TIMELINE_STEP_D = 1.0


def _r(a, nd=4):
    """Round to nd significant digits; NaN -> None."""
    a = np.asarray(a, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        mag = np.where(np.isfinite(a) & (a != 0), np.floor(np.log10(np.abs(a))), 0)
    out = np.round(a / 10 ** mag, nd - 1) * 10 ** mag
    return [None if not np.isfinite(v) else float(f"{v:.{nd}g}") for v in out]


def _dump(name, obj):
    p = DATA / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, separators=(",", ":"), allow_nan=False))
    return p


def cycle_timeseries(cyc, fg, notes):
    t0 = float(cyc.t_h[cyc.phase == "production"].iloc[0])
    n = len(cyc)
    idx = np.searchsorted(cyc.t_h.values, fg.t_h.values)
    prod = np.zeros(n, bool); prod[idx] = True

    def spread(col, fill):
        a = np.full(n, fill, float)
        a[idx] = fg[col].values
        return a
    now_h = t0 + notes["now_day"] * 24.0
    on_h = t0 + notes["onset_day_analytic"] * 24.0
    i_now = int(np.argmin(np.abs(fg.t_h.values - now_h)))
    a, b = float(fg.N_base.iloc[0]), float(fg.N_glide.iloc[i_now])
    mu_now, mu_60 = float(fg.mu_eff_Pas.iloc[i_now]), float(np.interp(notes["now_day"] - 30, fg.day, fg.mu_eff_Pas))
    msg = (f"Rod float forecast in ~14 h at {a:.1f} SPM: tubing mu_eff {mu_now:.1f} Pa.s "
           f"(+{100 * (mu_now / mu_60 - 1):.0f} % in 30 d, water cut {100 * fg.f_w.iloc[i_now]:.0f} % < inversion "
           f"{100 * P.F_INV:.0f} %). Step SPM {a:.1f} -> {b:.1f} over 6 h.")
    return {
        "well": "BGW-SYN-01", "label": "synthetic · stage v0",
        "t_h": _r(cyc.t_h, 7), "day": _r(cyc.t_h / 24.0, 6), "prod_start_h": t0,
        "phase": cyc.phase.astype(str).tolist(),
        "q_oil_bpd": _r(cyc.q_o_bpd), "water_cut": _r(cyc.f_w),
        "r_h_m": {f"L{k}": _r(cyc[f"r_h_L{k}"]) for k in (1, 2, 3)},
        "T_in_C": _r(cyc.T_in),
        "T_wh_C": _r(spread("T_wh_C", np.nan)),
        "mu_tubing_eff_Pas": _r(spread("mu_eff_Pas", np.nan)),
        "float_margin": _r(spread("margin_base", 1.0)),
        "float_margin_glide": _r(spread("margin_glide", 1.0)),
        "spm_current": _r(spread("N_base", 0.0)),
        "spm_glide": _r(spread("N_glide", 0.0)),
        "spm_inflow": _r(spread("N_inflow", 0.0)),
        "spm_float": _r(np.minimum(spread("N_float", 0.0), 99.0)),
        "float_margin_heater": _r(spread("margin_heater", 1.0)),
        "spm_float_heater": _r(np.minimum(spread("N_float_heater", 0.0), 99.0)),
        "T_wh_heater_C": _r(spread("T_wh_heater_C", np.nan)),
        "mu_tubing_eff_heater_Pas": _r(spread("mu_eff_heater_Pas", np.nan)),
        "events": [{"t_h": round(now_h, 2), "type": "FLOAT_FORECAST", "lead_h": 14, "msg": msg,
                    "spm_from": round(a, 2), "spm_to": round(b, 2), "onset_t_h": round(on_h, 2)}],
    }


def thermal(frames=True):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    d = np.load(OUT / "thermal.npz")
    re, ze = d["r_edges"], d["z_edges"]
    sel = np.arange(0, len(d["t_snap_h"]), FRAME_EVERY)
    H = sum(P.H_LAYERS_M)
    z_rng = (H + 15.0, -15.0)                         # top of image first
    rs = np.geomspace(*TEX_R, TEX_W)
    zs = np.linspace(z_rng[0], z_rng[1], TEX_H)
    ir = np.clip(np.searchsorted(re, rs) - 1, 0, len(re) - 2)
    iz = np.clip(np.searchsorted(ze, zs) - 1, 0, len(ze) - 2)
    cmap = plt.get_cmap("inferno")
    tdir = DATA / "thermal"
    tdir.mkdir(parents=True, exist_ok=True)
    meta = {"r_edges_m": _r(re, 6), "z_edges_m": _r(ze, 6), "cmap": "inferno", "T_min_C": T_MIN, "T_max_C": T_MAX,
            "tex_r_range_m": list(TEX_R), "tex_r_scale": "log", "tex_z_range_m": list(z_rng),
            "z_ref": "elevation above the base of the pay (m); pay 0..%g" % H, "frames": []}
    if frames:
        import make_thermal_cycle as MT
        MT._init()
    for j, i in enumerate(sel):
        T = d["T_snap"][i][iz][:, ir]
        rgba = cmap(np.clip((T - T_MIN) / (T_MAX - T_MIN), 0, 1))
        plt.imsave(tdir / f"tex_{j:04d}.png", rgba[..., :3])
        if frames:
            fig = MT.draw(int(i), fig=plt.figure(figsize=(16, 9), dpi=40))
            fig.savefig(tdir / f"f{j:04d}.png", dpi=40)
            plt.close(fig)
        meta["frames"].append({"file": f"f{j:04d}.png", "tex": f"tex_{j:04d}.png",
                               "t_h": float(d["t_snap_h"][i]), "phase": str(d["phase_snap"][i])})
    _dump("thermal_meta.json", meta)
    return meta


def _card_json(cls, spm, mu, unit, sp, sl, dp, dl, flags, **extra):
    return {"class": cls, "spm": round(float(spm), 3), "mu_Pas": round(float(mu), 4),
            "unit": "hydraulic" if int(unit) == 1 else "beam",
            "surface": {"pos_m": _r(sp), "load_kN": _r(np.asarray(sl) / 1e3)},
            "downhole": {"pos_m": _r(dp), "load_kN": _r(np.asarray(dl) / 1e3)}, "flags": flags, **extra}


def cards(notes):
    from ml.card_library import load_cards
    df = load_cards()
    df = df[df.keep]
    index = []
    for cls, g in df.groupby("cls", sort=False):
        gb = g[g.unit == 0] if (g.unit == 0).sum() >= 3 else g
        for i, (_, r) in enumerate(gb.sample(3, random_state=42).iterrows()):
            flags = (["float"] if r.float_flag else []) + (["clipped"] if r.min_load_raw < 0 else []) + ["noise"]
            name = f"cards/{cls}_{i}.json"
            _dump(name, _card_json(cls, r.N, r.mu, r.unit, r.surf_pos, r.surf_load, r.dh_pos, r.dh_load, flags,
                                   depth_m=round(float(r.depth), 1)))
            index.append({"file": name.split("/")[1], "class": cls, "source": "library"})
    cc = np.load(OUT / "crosscheck_cards.npz")
    for i, c in enumerate(notes["crosscheck"]):
        fl = bool(cc[f"float_{i}"][0])
        cls = "rod_float" if fl else "normal"
        name = f"cards/crosscheck_{i}.json"
        _dump(name, _card_json(cls, notes["N_base_spm"], c["mu_eff_Pas"], 0, cc[f"surf_pos_{i}"][0],
                               cc[f"surf_load_{i}"][0], cc[f"dh_pos_{i}"][0], cc[f"dh_load_{i}"][0],
                               (["float", "clipped"] if fl else []), prod_day=round(c["day"], 3),
                               min_load_raw_kN=round(c["min_load_raw_kN"], 3)))
        index.append({"file": name.split("/")[1], "class": cls, "source": "A1_crosscheck",
                      "prod_day": round(c["day"], 3)})
    _dump("cards/index.json", {"cards": index})
    return index


def rod_motion():
    cc = np.load(OUT / "crosscheck_cards.npz")

    def one(i):
        T = float(cc[f"T_{i}"][0])
        return {"t_s": _r(np.arange(P.CARD_POINTS) * T / P.CARD_POINTS),
                "u_m": [_r(row) for row in cc[f"rod_u_{i}"][0]],
                "stress_MPa": [_r(row / 1e6) for row in cc[f"rod_stress_{i}"][0]]}
    out = {"depth_m": _r(cc["rod_depth_0"][0]), **one(0), "float": one(2)}
    _dump("rod_motion.json", out)
    return out


def tubing_profiles(cyc):
    prof = [W.profile_at_day(cyc, d) for d in PROFILE_DAYS]
    out = {"z_m": _r(prof[0]["z_m"]), "days": PROFILE_DAYS,
           "T_C": [_r(p["T_C"]) for p in prof], "mu_Pas": [_r(p["mu_Pas"]) for p in prof]}
    _dump("tubing_profiles.json", out)
    return out


def timelines(cyc, fg, step_d=TIMELINE_STEP_D):
    """Extra files for the live dashboard panels (additive, not in the T12 contract):
    cards_timeline.json: wave-equation surface/downhole cards every step_d production days for
      the three dashboard scenarios (baseline N, AI glide N, baseline N + 6 kW heater);
    tubing_timeline.json: T(z), mu(z) on the same days, without and with the heater."""
    from twin import float_glide as FG
    from twin import pumpbc as PB
    from twin import rodpump as RP
    pr = FG.production_frame(cyc)
    days = np.arange(0.0, float(pr.day.max()) + 1e-9, step_d)
    rows = [pr.iloc[int(np.argmin(np.abs(pr.day.values - d)))] for d in days]
    F_fl = PB.fluid_load(P.P_WF_KSC, P.PLUNGER_D_M / P.IN_M, P.ROD_LEN_M)[0]
    N_base = float(fg.N_base.iloc[0])
    N_glide = np.interp(days, fg.day, fg.N_glide)
    from ml.card_library import CLOSURE_MAX
    tub, cards_out = {"days": _r(days)}, {"days": _r(days), "t_h": _r([r.t_h for r in rows], 7)}
    for key, heater, N in (("baseline", 0.0, np.full(len(days), N_base)), ("glide", 0.0, N_glide),
                           ("heater", FG.HEATER_WHATIF_KW, np.full(len(days), N_base))):
        prof = [W.profile(r.T_in, r.q_liq_m3d, r.f_w, heater) for r in rows]
        mu = np.array([p["mu_Pas"] for p in prof])
        res = RP.simulate(np.full(len(days), P.ROD_LEN_M), N, P.STROKE_M, mu, PB.CID["normal"], F_fl,
                          n_nodes=mu.shape[1] - 1)
        settled = res["closure"] <= CLOSURE_MAX
        cards_out[key] = {"spm": _r(N), "float": [bool(f) for f in res["float"]],
                          "settled": [bool(x) for x in settled], "closure": _r(res["closure"], 3),
                          "min_load_raw_kN": _r(res["min_load_raw"] / 1e3),
                          "surface": {"pos_m": [_r(a) for a in res["surf_pos"]],
                                      "load_kN": [_r(a / 1e3) for a in res["surf_load"]]},
                          "downhole": {"pos_m": [_r(a) for a in res["dh_pos"]],
                                       "load_kN": [_r(a / 1e3) for a in res["dh_load"]]}}
        if key != "glide":
            tub["z_m"] = _r(prof[0]["z_m"])
            tub[key] = {"T_C": [_r(p["T_C"]) for p in prof], "mu_Pas": [_r(p["mu_Pas"]) for p in prof]}
    _dump("cards_timeline.json", cards_out)
    _dump("tubing_timeline.json", tub)


def main(frames=True):
    cyc = pd.read_parquet(OUT / "cycle.parquet")
    fg = pd.read_parquet(OUT / "float_glide.parquet")
    notes = json.loads((OUT / "float_glide_notes.json").read_text())
    _dump("cycle_timeseries.json", cycle_timeseries(cyc, fg, notes))
    tubing_profiles(cyc)
    rod_motion()
    cards(notes)
    timelines(cyc, fg)
    m = thermal(frames)
    print(f"exported to {DATA} ({len(m['frames'])} thermal frames)")


if __name__ == "__main__":
    main(frames="--no-frames" not in sys.argv)
