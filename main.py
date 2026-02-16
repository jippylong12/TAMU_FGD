#!/usr/bin/env python3
from pathlib import Path
import sys


def _bootstrap_import_path() -> None:
    root = Path(__file__).resolve().parent
    src_dir = root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


def main() -> None:
    _bootstrap_import_path()
    from tamu_fgd.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
