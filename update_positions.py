#!/usr/bin/env python3
import os, json, asyncio, aiohttp, subprocess, requests
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)
POSITIONS = CONFIG.get("positions", [])

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "*/*",
}

async def fetch_price(session, symbol: str) -> float | None:
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{symbol}"
    try:
        async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=8)) as resp:
            text = await resp.text()
            data = json.loads(text)
            return data["result"]["areas"][0]["datas"][0]["nv"]
    except Exception as e:
        print(f"[WARN] price fetch failed {symbol}: {e}")
        return None

def get_usd_krw():
    try:
        res = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5)
        return res.json()['rates']['KRW']
    except Exception as e:
        print(f"[WARN] usd_krw fetch failed: {e}")
        return None

def get_wti():
    # 1차 시도: yfinance (period=5d로 늘려서 당일 데이터 비어도 최근 값 확보)
    try:
        import yfinance as yf
        ticker = yf.Ticker("CL=F")
        hist = ticker.history(period="5d", interval="1m")
        if not hist.empty:
            closes = hist["Close"].dropna()
            if not closes.empty:
                print(f"[INFO] WTI from yfinance: {closes.iloc[-1]}")
                return float(closes.iloc[-1])
    except Exception as e:
        print(f"[WARN] yfinance wti failed: {e}")

    # 2차 시도: Yahoo Finance 직접 API (yfinance 실패 시 fallback)
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F?interval=1m&range=5d"
        res = requests.get(url, headers=HEADERS, timeout=8)
        closes = res.json()["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        if closes:
            print(f"[INFO] WTI from yahoo chart API: {closes[-1]}")
            return float(closes[-1])
    except Exception as e:
        print(f"[WARN] yahoo chart wti failed: {e}")

    print("[ERROR] WTI fetch all sources failed, returning None")
    return None

async def main():
    results = []
    total_exposure = 0.0
    total_pnl = 0.0

    # 환율 & WTI 먼저 가져오기
    usd_krw = get_usd_krw()
    wti = get_wti()
    print(f"USD/KRW: {usd_krw}, WTI: {wti}")

    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        for pos in POSITIONS:
            price = await fetch_price(session, pos["symbol"])
            if price is None:
                price = float(pos.get("avg_price", 0))

            qty  = float(pos["qty"])
            avg  = float(pos["avg_price"])
            side = (pos.get("side") or "LONG").upper()

            exp = avg * qty
            mv = qty * price

            if side.startswith("S"):
                pnl = (avg - price) * qty
            else:
                pnl = (price - avg) * qty

            cost = exp
            pnl_ratio = (pnl / cost) if cost else 0.0

            results.append({
                "symbol": pos["symbol"],
                "name": pos["name"],
                "side": side,
                "qty": qty,
                "avg_price": avg,
                "group": pos.get("group", pos["name"]),
                "last_price": price,
                "exposure": exp,
                "mv": mv,
                "pnl": pnl,
                "pnl_ratio": pnl_ratio,
            })

            total_exposure += exp
            total_pnl += pnl

    snapshot = {
        "as_of": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "currency": CONFIG.get("currency", "KRW"),
        "positions": results,
        "total_exposure": total_exposure,
        "total_pnl": total_pnl,
        "total_pnl_ratio": (total_pnl / total_exposure) if total_exposure else 0.0,
        "usd_krw": usd_krw,
        "wti": wti,
    }

    out_path = "web/live.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    subprocess.run("git add web/live.json", shell=True, check=False)
    subprocess.run(f'git commit -m "chore: update live {snapshot["as_of"]}"', shell=True, check=False)
    subprocess.run("git push", shell=True, check=False)

if __name__ == "__main__":
    asyncio.run(main())