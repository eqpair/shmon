#!/usr/bin/env python3
import asyncio, aiohttp, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "config.json"
LIVE = ROOT / "web" / "live.json"

POLL_URL = "https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"

async def fetch_quote(session, code: str):
    url = POLL_URL.format(code=code)
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as r:
            # 일부 케이스에서 content-type이 text/html로 오므로 강제 파싱
            data = await r.json(content_type=None)
            areas = data.get("result", {}).get("areas", [])
            if not areas or not areas[0].get("datas"):
                return None
            item = areas[0]["datas"][0]
            price = item.get("nv") or item.get("now")
            return float(price)
    except Exception:
        return None

async def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    currency = cfg.get("currency", "KRW")
    positions = cfg["positions"]

    async with aiohttp.ClientSession(headers={
        "User-Agent": "Mozilla/5.0 (RaspberryPi) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
    }) as session:
        tasks = [fetch_quote(session, p["symbol"]) for p in positions]
        results = await asyncio.gather(*tasks)

    total_exp = 0.0
    total_pnl = 0.0
    enriched = []

    for p, price in zip(positions, results):
        last = float(price or 0.0)
        qty = float(p["qty"])
        avg = float(p["avg_price"])
        side = p["side"].upper()

        mv = qty * last
        pnl = (avg - last) * qty if side == "SHORT" else (last - avg) * qty
        ratio = pnl / abs(mv) if mv != 0 else 0.0

        enriched.append({
            **p,
            "last_price": last,
            "mv": mv,
            "pnl": pnl,
            "pnl_ratio": ratio
        })
        total_exp += abs(mv)
        total_pnl += pnl

    payload = {
        "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "currency": currency,
        "positions": enriched,
        "total_exposure": total_exp,
        "total_pnl": total_pnl,
        "total_pnl_ratio": (total_pnl / total_exp) if total_exp else 0.0
    }

    LIVE.parent.mkdir(parents=True, exist_ok=True)
    LIVE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 무인 커밋/푸시 (PAT 또는 SSH 설정 가정)
    try:
        subprocess.run(["git", "add", str(LIVE)], check=True, cwd=str(ROOT))
        subprocess.run(["git", "commit", "-m", f"chore: update live {payload['as_of']}"], check=False, cwd=str(ROOT))
        subprocess.run(["git", "push"], check=True, cwd=str(ROOT))
    except Exception as e:
        print("git push skipped:", e)

if __name__ == "__main__":
    asyncio.run(main())
