"""Console-free Windows entry point with persistent startup diagnostics."""

import ctypes
import os
from pathlib import Path
import sys
import traceback

root = Path(__file__).resolve().parent.parent
logs = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "eChemTips" / "logs"
logs.mkdir(parents=True, exist_ok=True)
analysis = "--analysis" in sys.argv
log_path = logs / ("analysis.log" if analysis else "control.log")
with log_path.open("a", encoding="utf-8", buffering=1) as stream:
    sys.stdout = sys.stderr = stream
    try:
        # A checkout uses local source; an offline kit uses the installed wheel.
        if (root / "echemtips").is_dir():
            sys.path.insert(0, str(root))
        sys.argv = [sys.argv[0]]
        if analysis:
            from echemtips.analysis import main
        else:
            from echemtips.app import main
        main()
    except SystemExit as exc:
        if exc.code not in (None, 0):
            traceback.print_exc()
            ctypes.windll.user32.MessageBoxW(None, f"eChemTips exited with an error.\nSee {log_path}", "eChemTips", 16)
    except Exception:
        traceback.print_exc()
        ctypes.windll.user32.MessageBoxW(None, f"eChemTips could not start.\nSee {log_path}", "eChemTips", 16)
