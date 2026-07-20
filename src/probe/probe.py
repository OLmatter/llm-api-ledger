"""
Thin entry-point script so PyInstaller can bundle a single file.

Usage:
    python probe.py            # run the probe
    pyinstaller probe.spec     # build single-file binary

This file lives at src/probe/probe.py so `probe.app` imports resolve
correctly both in source-tree runs and inside the PyInstaller bundle.
"""

import os
import sys
from pathlib import Path

# Ensure src/ is on sys.path when run as a plain script
HERE = Path(__file__).resolve().parent
SRC = HERE.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# When frozen by PyInstaller, force the data dir to be alongside the exe
if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    data_dir = exe_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("LEDGER_DATA_DIR", str(data_dir))

from probe.app import main  # noqa: E402

if __name__ == "__main__":
    main()
