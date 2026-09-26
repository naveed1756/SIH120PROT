"""D1 card features (task T11).

Per surface card (as measured: noisy, clipped at zero):
  - position and load normalised to [0, 1];
  - closed contour z = x + i y resampled to 128 points by arc length; |FFT coefficients 1..12|
    normalised by |c1| (so f_fd01 = 1 by construction; kept for the spec's feature list);
  - min, max, mean load normalised by the card's peak load (load / max load; on the [0, 1]
    normalised card min and max would be 0 and 1 by construction);
  - enclosed area / bounding-box area (on the normalised card);
  - upstroke and downstroke mean slopes (least-squares d load / d position, normalised units);
  - downhole fillage: the downhole card is computed from the surface card with the Gibbs method
    (twin.gibbs, same as in the field; the library's simulated pump card is NOT used), then the
    position where the downstroke load falls below 50 % of the fluid load estimate, / S_p.
Inputs the field also has: pump setting depth, SPM, and a viscosity estimate (here the card's mu).
"""
import numpy as np
import pandas as pd

from twin import gibbs as G

N_ARC = 128
N_FD = 12
GIBBS_NODES = 90          # same node count for every card (spacing 10-12.8 m for 900-1,150 m)


def _norm(a):
    a = np.asarray(a, float)
    lo, hi = a.min(1, keepdims=True), a.max(1, keepdims=True)
    return (a - lo) / np.maximum(hi - lo, 1e-12)


def fourier_descriptors(x, y, n_arc=N_ARC, n_fd=N_FD):
    """x, y: (n, M) normalised closed contours. Returns (n, n_fd) |c_k|/|c_1|, k = 1..n_fd."""
    out = np.empty((x.shape[0], n_fd))
    for i in range(x.shape[0]):
        xs, ys = np.append(x[i], x[i, 0]), np.append(y[i], y[i, 0])
        s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))])
        t = np.linspace(0.0, s[-1], n_arc, endpoint=False)
        z = np.interp(t, s, xs) + 1j * np.interp(t, s, ys)
        c = np.fft.fft(z) / n_arc
        out[i] = np.abs(c[1:n_fd + 1]) / max(abs(c[1]), 1e-12)
    return out


def area_ratio(x, y):
    xs, ys = np.concatenate([x, x[:, :1]], 1), np.concatenate([y, y[:, :1]], 1)
    a = 0.5 * np.abs(np.sum(xs[:, :-1] * ys[:, 1:] - xs[:, 1:] * ys[:, :-1], 1))
    return a / np.maximum(np.ptp(x, 1) * np.ptp(y, 1), 1e-12)


def stroke_halves(pos):
    """Boolean masks (n, M) for upstroke / downstroke samples, split at the top reversal."""
    n, M = pos.shape
    top = np.argmax(pos, 1)
    bot = np.argmin(pos, 1)
    idx = np.arange(M)[None, :]
    # samples from the bottom reversal to the top reversal (cyclically) are the upstroke
    up = ((idx - bot[:, None]) % M) <= ((top - bot) % M)[:, None]
    return up, ~up


def mean_slope(x, y, mask):
    out = np.empty(x.shape[0])
    for i in range(x.shape[0]):
        xi, yi = x[i, mask[i]], y[i, mask[i]]
        out[i] = np.polyfit(xi, yi, 1)[0] if xi.size > 2 and np.ptp(xi) > 1e-6 else 0.0
    return out


def fillage(dh_pos, dh_load):
    """Downstroke position where the pump load falls below 50 % of the fluid-load estimate,
    measured from the bottom, divided by the plunger stroke (1 = full pump, ~0 = empty)."""
    n, M = dh_pos.shape
    out = np.empty(n)
    Sp = np.maximum(np.ptp(dh_pos, 1), 1e-9)
    F_fl = np.percentile(dh_load, 90, axis=1)
    for i in range(n):
        top = int(np.argmax(dh_pos[i]))
        seq = np.roll(np.arange(M), -top)                       # downstroke starts at the top
        bot_rel = int(np.argmin(dh_pos[i, seq]))
        down = seq[: bot_rel + 1]
        below = np.nonzero(dh_load[i, down] < 0.5 * F_fl[i])[0]
        out[i] = (dh_pos[i, down[below[0]]] - dh_pos[i].min()) / Sp[i] if below.size else 0.0
    return np.clip(out, 0.0, 1.0)


def features(df, batch=1000):
    """Feature table (one row per card) from a card-library frame."""
    pos = np.stack(df.surf_pos.values).astype(float)
    load = np.stack(df.surf_load.values).astype(float)
    x, y = _norm(pos), _norm(load)
    fd = fourier_descriptors(x, y)
    rel = load / np.maximum(load.max(1, keepdims=True), 1e-9)
    up, down = stroke_halves(pos)
    dh_pos = np.empty_like(pos); dh_load = np.empty_like(load)
    for a in range(0, len(df), batch):
        s = slice(a, a + batch)
        dh_pos[s], dh_load[s] = G.downhole_batch(pos[s], load[s], df.depth.values[s], df.N.values[s],
                                                 df.mu.values[s], n_nodes=GIBBS_NODES)
    feats = {f"fd{k:02d}": fd[:, k - 1] for k in range(1, N_FD + 1)}
    feats.update({
        "load_min": rel.min(1), "load_max": rel.max(1), "load_mean": rel.mean(1),
        "area_ratio": area_ratio(x, y),
        "slope_up": mean_slope(x, y, up), "slope_down": mean_slope(x, y, down),
        "fillage": fillage(dh_pos, dh_load),
    })
    return pd.DataFrame(feats, index=df.index)


FEATURES = [f"fd{k:02d}" for k in range(1, N_FD + 1)] + ["load_min", "load_max", "load_mean", "area_ratio",
                                                          "slope_up", "slope_down", "fillage"]
