"""House figure style for every PoC asset (task T01)."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
FONT_DIR = Path(__file__).resolve().parent / "fonts"

CAPTION = (
    "Synthetic test well (BGW-SYN-01) based on OIL's published parameters (July 2025) "
    "and literature. Not field data. Prototype."
)

# Domain colours from the architecture documents
COLORS = {
    "thermal": "#A8561A",
    "wellbore": "#24588A",
    "surface": "#546B1C",
    "ai": "#5A4A8C",
    "warn": "#A3321F",
}
GREY = "#6B7570"

_PREFERRED = ["IBM Plex Sans", "Inter", "DejaVu Sans"]


def _register_bundled_fonts():
    if FONT_DIR.is_dir():
        for f in FONT_DIR.glob("*.ttf"):
            try:
                font_manager.fontManager.addfont(str(f))
            except Exception:  # pragma: no cover - font problems must not break figures
                pass


def _pick_font():
    names = {f.name for f in font_manager.fontManager.ttflist}
    for n in _PREFERRED:
        if n in names:
            return n
    return "DejaVu Sans"


def apply():
    """Set matplotlib rcParams for the house style and return the font used."""
    _register_bundled_fonts()
    font = _pick_font()
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [font, "DejaVu Sans"],
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#3A423D",
        "axes.labelcolor": "#18201C",
        "xtick.color": "#3A423D",
        "ytick.color": "#3A423D",
        "legend.frameon": False,
        "figure.dpi": 100,
        "savefig.dpi": 300,
        "svg.fonttype": "none",
    })
    return font


def add_caption(fig, text=CAPTION):
    """Bottom-left, 8 pt, grey synthetic-data caption ."""
    fig.text(0.006, 0.006, text, fontsize=8, color=GREY, ha="left", va="bottom")


def save(fig, name, caption=True):
    """Write assets/<name>.png and assets/<name>.svg. Returns the PNG path."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    if caption:
        add_caption(fig)
    png = ASSETS / f"{name}.png"
    fig.savefig(png, dpi=300)
    fig.savefig(ASSETS / f"{name}.svg")
    return png
