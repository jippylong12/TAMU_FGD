"""Legacy parser modules retained for backward-compatible behavior."""

from pathlib import Path
import sys


_legacy_dir = Path(__file__).resolve().parent
if str(_legacy_dir) not in sys.path:
    sys.path.insert(0, str(_legacy_dir))
