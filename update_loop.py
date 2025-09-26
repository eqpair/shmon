#!/usr/bin/env python3
import subprocess, time, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
PY   = ROOT / ".venv" / "bin" / "python"
UPD  = ROOT / "update_positions.py"

INTERVAL = 60  # 초 (원하면 30으로)

while True:
    try:
        subprocess.run([str(PY), str(UPD)], check=False)
    except Exception as e:
        print("Error:", e, flush=True)
    time.sleep(INTERVAL)
