#!/usr/bin/env python3
import os
import json
import subprocess
from datetime import datetime, timezone, timedelta

import aiohttp
import asyncio

# 한국 시간
KST = timezone(timedelta(hours=9))

# config.json 읽기
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

POSITIONS = CONFIG["positions"]

# 네이버 API 호출
async def fetch_price(session, symbol):
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{symbol}"
    async with session.get(url) as resp:
        data = await resp.json()
        try:
            return data["result"]["areas"][0]["datas"][0]["nv"]
        except Exception:
            return None

async def main():
    results = []
    total_exposure = 0
    total_pnl = 0

    async with aiohttp.ClientSession() as session:
        for pos in POSITIONS:
            price = await fetch_price(session, pos["symbol"])
            if price is None:
                continue

            mv = pos["qty"] * price
            pnl = (price - pos["avg_price"]) * pos["qty"] if pos["side"] == "LONG" else (pos["avg_price"] - price) * pos["qty"]
            pnl_ratio = pnl / (pos["avg_price"] * pos["qty"])

            results.append({
                "symbol": pos["symbol"],
                "name": pos["name"],
                "side": pos["side"],
                "qty": pos["qty"],
                "avg_price": pos["avg_price"],
                "group": pos["group"],
                "last_price": price,
                "mv": mv,
                "pnl": pnl,
                "pnl_ratio": pnl_ratio
            })

            total_exposure += mv
            total_pnl += pnl

    snapshot = {
        "as_of": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "currency": CONFIG.get("currency", "KRW"),
        "positions": results,
        "total_exposure": total_exposure,
        "total_pnl": total_pnl,
        "total_pnl_ratio": total_pnl / total_exposure if total_exposure else 0
    }

    # 저장
    out_path = "web/live.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    # GitHub 커밋 & 푸시
    subprocess.run("git add web/live.json", shell=True)
    subprocess.run(f'git commit -m "chore: update live {snapshot["as_of"]}"', shell=True)
    subprocess.run("git push", shell=True)

if __name__ == "__main__":
    asyncio.run(main())
