"""T12 done-when: JSON-schema-lite check of web/public/data (keys present, equal lengths, no NaN).
Regenerate with: python tools/export_web.py"""
import json
import math
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "web" / "public" / "data"
pytestmark = pytest.mark.skipif(not (DATA / "cycle_timeseries.json").exists(), reason="run tools/export_web.py")


def load(name):
    # json.loads accepts NaN/Infinity tokens; reject them explicitly
    def bad(tok):
        raise ValueError(f"non-finite token {tok} in {name}")
    return json.loads((DATA / name).read_text(), parse_constant=bad)


def finite(v, allow_null=False):
    if v is None:
        return allow_null
    if isinstance(v, (int, float)):
        return math.isfinite(v)
    if isinstance(v, list):
        return all(finite(x, allow_null) for x in v)
    if isinstance(v, dict):
        return all(finite(x, allow_null) for x in v.values())
    return True


def test_cycle_timeseries():
    d = load("cycle_timeseries.json")
    keys = ["well", "label", "t_h", "phase", "q_oil_bpd", "water_cut", "r_h_m", "T_in_C", "T_wh_C",
            "mu_tubing_eff_Pas", "float_margin", "float_margin_glide", "spm_current", "spm_glide",
            "spm_inflow", "spm_float", "events"]
    assert all(k in d for k in keys)
    n = len(d["t_h"])
    series = [k for k in keys if isinstance(d[k], list) and k != "events"]
    assert all(len(d[k]) == n for k in series)
    assert set(d["r_h_m"]) == {"L1", "L2", "L3"} and all(len(v) == n for v in d["r_h_m"].values())
    prod = [p == "production" for p in d["phase"]]
    for k in series:
        if k == "phase":
            continue
        for v, pr in zip(d[k], prod):
            assert finite(v, allow_null=(k in ("T_wh_C", "mu_tubing_eff_Pas", "water_cut", "T_wh_heater_C", "mu_tubing_eff_heater_Pas") and not pr)), k
    assert finite(d["r_h_m"])
    ev = d["events"]
    assert ev and all({"t_h", "type", "lead_h", "msg"} <= set(e) for e in ev)
    assert any(e["type"] == "FLOAT_FORECAST" and e["lead_h"] == 14 for e in ev)


def test_thermal_meta_and_frames():
    m = load("thermal_meta.json")
    assert {"r_edges_m", "z_edges_m", "cmap", "T_min_C", "T_max_C", "frames"} <= set(m)
    assert finite(m["r_edges_m"]) and finite(m["z_edges_m"])
    assert m["frames"] and all({"file", "t_h", "phase"} <= set(f) for f in m["frames"])
    for f in m["frames"]:
        assert (DATA / "thermal" / f["file"]).exists()
        assert (DATA / "thermal" / f["tex"]).exists()


def test_tex_size():
    from PIL import Image
    m = load("thermal_meta.json")
    assert Image.open(DATA / "thermal" / m["frames"][0]["tex"]).size == (256, 128)


def test_cards():
    idx = load("cards/index.json")["cards"]
    classes = {c["class"] for c in idx if c["source"] == "library"}
    assert len(classes) == 9
    assert sum(c["source"] == "A1_crosscheck" for c in idx) == 3
    for c in idx:
        d = load(f"cards/{c['file']}")
        assert {"class", "spm", "mu_Pas", "unit", "surface", "downhole", "flags"} <= set(d)
        for side in ("surface", "downhole"):
            assert len(d[side]["pos_m"]) == len(d[side]["load_kN"]) > 0
        assert finite({k: d[k] for k in ("spm", "mu_Pas", "surface", "downhole")})


def test_rod_motion():
    d = load("rod_motion.json")
    assert len(d["depth_m"]) == 20 and len(d["t_s"]) == 200
    for case in (d, d["float"]):
        assert len(case["u_m"]) == len(case["stress_MPa"]) == len(case["t_s"])
        assert all(len(r) == 20 for r in case["u_m"] + case["stress_MPa"])
        assert finite(case["u_m"]) and finite(case["stress_MPa"])


def test_tubing_profiles():
    d = load("tubing_profiles.json")
    assert d["days"] == [5, 30, 60, 100]
    n = len(d["z_m"])
    for k in ("T_C", "mu_Pas"):
        assert len(d[k]) == 4 and all(len(r) == n for r in d[k]) and finite(d[k])
