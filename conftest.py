# Makes the repo root importable (twin, ml, optim) when running pytest from the root.
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
