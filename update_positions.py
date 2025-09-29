#!/usr/bin/env python3
import os, json, asyncio, aiohttp, subprocess
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
POSITIONS = CONFIG.get("positions", [])

HEADERS = {
    # 일부 프록시/방화벽이 UA 없으면 차단하거나 text/plain으로 내려줌
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "*/*",
}

async def fetch_price(session, symbol: str) -> float | None:
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{symbol}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            # ➜ 여기! resp.json() 대신 문자열로 받고 json.loads()
            text = await resp.text()  # euc-kr도 알아서 str로 디코드됨
            data = json.loads(text)
            return data["result"]["areas"][0]["datas"][0]["nv"]
    except Exception as e:
        print(f"[WARN] price fetch failed {symbol}: {e}")
        return None

async def main():
    results = []
    total_exposure = 0.0
    total_pnl = 0.0

    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        for pos in POSITIONS:
            price = await fetch_price(session, pos["symbol"])
            if price is None:
                # 가격 못 받으면 스킵(원하면 마지막가 그대로 두도록 바꿀 수 있음)
                continue

            qty = float(pos["qty"])
            avg = float(pos["avg_price"])
            side = (pos.get("side") or "LONG").upper()

            mv = qty * price
            if side.startswith("S"):  # SHORT
                pnl = (avg - price) * qty
            else:                     # LONG
                pnl = (price - avg) * qty

            cost = avg * qty
            pnl_ratio = (pnl / cost) if cost else 0.0

            results.append({
                "symbol": pos["symbol"],
                "name": pos["name"],
                "side": side,
                "qty": qty,
                "avg_price": avg,
                "group": pos.get("group", pos["name"]),
                "last_price": price,
                "mv": mv,
                "pnl": pnl,
                "pnl_ratio": pnl_ratio,
            })

            total_exposure += mv
            total_pnl += pnl

    snapshot = {
        "as_of": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "currency": CONFIG.get("currency", "KRW"),
        "positions": results,
        "total_exposure": total_exposure,
        "total_pnl": total_pnl,
        "total_pnl_ratio": (total_pnl / total_exposure) if total_exposure else 0.0,
    }

    out_path = "web/live.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    # git add/commit/push
    subprocess.run("git add web/live.json", shell=True, check=False)
    subprocess.run(f'git commit -m "chore: update live {snapshot["as_of"]}"', shell=True, check=False)
    subprocess.run("git push", shell=True, check=False)

if __name__ == "__main__":
    asyncio.run(main())
