#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tamu_fgd.tools.download_pdfs_http import main


if __name__ == "__main__":
    raise SystemExit(main())
