#!/usr/bin/env python3
import subprocess, time, pathlib
from datetime import datetime, timezone, timedelta

ROOT = pathlib.Path(__file__).resolve().parent
PY   = ROOT / ".venv" / "bin" / "python"
UPD  = ROOT / "update_positions.py"

INTERVAL = 60  # 초
KST = timezone(timedelta(hours=9))

def is_trading_session_kst(now: datetime) -> bool:
    # 월=0 … 일=6
    if now.weekday() >= 5:  # 토,일 제외
        return False
    start = now.replace(hour=8, minute=30, second=0, microsecond=0)
    end   = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    return start <= now <= end

while True:
    try:
        now = datetime.now(KST)
        if is_trading_session_kst(now):
            subprocess.run([str(PY), str(UPD)], check=False)
        # 장외 시간에는 조용히 대기
    except Exception as e:
        print("Error:", e, flush=True)
    time.sleep(INTERVAL)
