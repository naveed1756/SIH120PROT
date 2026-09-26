import math
import numbers

import twin.params as P
import twin.style as S

# Constants that are intentionally unset until a later task fills them in.
PENDING = {"PLUNGER_D_M": "T09"}


def _constants():
    return {k: v for k, v in vars(P).items() if k.isupper()}


def _flatten(v):
    """Numbers inside scalars, lists/tuples and dicts (T14/T15 add dict-valued constants)."""
    if isinstance(v, dict):
        return [x for u in v.values() for x in _flatten(u)]
    if isinstance(v, (list, tuple)):
        return [x for u in v for x in _flatten(u)]
    return [v]


def test_every_constant_is_finite():
    bad = []
    for name, val in _constants().items():
        if val is None and name in PENDING:
            continue
        for v in _flatten(val):
            if not isinstance(v, numbers.Real) or not math.isfinite(v):
                bad.append((name, val))
    assert not bad, f"non-finite constants: {bad}"


def test_layers_consistent():
    assert len(P.H_LAYERS_M) == len(P.KH_CONTRAST) == 3
    assert abs(sum(P.H_LAYERS_M) - 10.0) < 1e-12


def test_style_caption_and_colors():
    assert S.CAPTION == (
        "Synthetic reference well BGW-SYN-01 · OIL published parameters (Jul 2025) "
        "+ literature · not field data · prototype v0"
    )
    assert set(S.COLORS) == {"thermal", "wellbore", "surface", "ai", "warn"}
    assert S.apply() in {"IBM Plex Sans", "Inter", "DejaVu Sans"}
