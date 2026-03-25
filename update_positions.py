#!/usr/bin/env python3
"""
update_positions.py — 포지션 스냅샷 생성
환율(USD/KRW)·WTI 는 소스별 fallback 체인으로 안정 취득
"""

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

# ──────────────────────────────────────────────
# USD/KRW  — 3개 소스 fallback 체인
# ──────────────────────────────────────────────

def _fx_open_er_api() -> float | None:
    """open.er-api.com (현재 기본 소스, 무료·제한 있음)"""
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        r.raise_for_status()
        return float(r.json()["rates"]["KRW"])
    except Exception as e:
        print(f"[FX-1] open.er-api 실패: {e}")
        return None


def _fx_frankfurter() -> float | None:
    """frankfurter.app — ECB 기반, 완전 무료·무제한"""
    try:
        r = requests.get(
            "https://api.frankfurter.app/latest?from=USD&to=KRW", timeout=5
        )
        r.raise_for_status()
        return float(r.json()["rates"]["KRW"])
    except Exception as e:
        print(f"[FX-2] frankfurter 실패: {e}")
        return None


def _fx_naver() -> float | None:
    """네이버 금융 환율 API (국내 서버, 장 중 실시간)"""
    try:
        url = (
            "https://finance.naver.com/marketindex/exchangeDailyQuote.naver"
            "?marketindexCd=FX_USDKRW&page=1&count=1"
        )
        r = requests.get(url, headers=HEADERS, timeout=5)
        r.raise_for_status()
        price_str = r.json()["result"]["itemList"][0]["closePrice"]
        return float(price_str.replace(",", ""))
    except Exception as e:
        print(f"[FX-3] 네이버 FX 실패: {e}")
        return None


def get_usd_krw() -> float | None:
    """소스를 순서대로 시도해 처음 성공한 값 반환"""
    for fn in (_fx_open_er_api, _fx_frankfurter, _fx_naver):
        val = fn()
        if val:
            print(f"[FX] USD/KRW = {val}  (소스: {fn.__name__})")
            return val
    print("[FX] 모든 소스 실패 — None 반환")
    return None


# ──────────────────────────────────────────────
# WTI  — 3개 소스 fallback 체인
# ──────────────────────────────────────────────

def _wti_yfinance() -> float | None:
    """yfinance CL=F (기존 방식)"""
    try:
        import yfinance as yf
        ticker = yf.Ticker("CL=F")
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return None
    except Exception as e:
        print(f"[WTI-1] yfinance 실패: {e}")
        return None


def _wti_naver_polling() -> float | None:
    """네이버 실시간 시세 API — WTI 종목코드 @CL#C"""
    try:
        url = "https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:@CL#C"
        r = requests.get(url, headers=HEADERS, timeout=6)
        r.raise_for_status()
        data = r.json()
        price = data["result"]["areas"][0]["datas"][0]["nv"]
        return float(price)
    except Exception as e:
        print(f"[WTI-2] 네이버 polling 실패: {e}")
        return None


def _wti_investing_scrape() -> float | None:
    """
    investing.com 공개 API (비공식, scrape 아님)
    — 실제 운영 전 브라우저 DevTools 에서 실제 엔드포인트 확인 권장
    """
    try:
        url = "https://api.investing.com/api/financialdata/944651/historical/chart/"
        params = {"period": "P1D", "interval": "PT1M", "pointscount": 60}
        hdrs = {**HEADERS, "domain-id": "www"}
        r = requests.get(url, headers=hdrs, params=params, timeout=8)
        r.raise_for_status()
        candles = r.json()["data"]["candles"]
        if candles:
            return float(candles[-1][4])  # close price
        return None
    except Exception as e:
        print(f"[WTI-3] investing 실패: {e}")
        return None


def get_wti() -> float | None:
    """소스를 순서대로 시도해 처음 성공한 값 반환"""
    for fn in (_wti_yfinance, _wti_naver_polling, _wti_investing_scrape):
        val = fn()
        if val:
            print(f"[WTI] WTI = {val}  (소스: {fn.__name__})")
            return val
    print("[WTI] 모든 소스 실패 — None 반환")
    return None


# ──────────────────────────────────────────────
# 주식 현재가 (기존과 동일)
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

async def main():
    results = []
    total_exposure = 0.0
    total_pnl = 0.0

    # 환율 & WTI (fallback 체인 적용)
    usd_krw = get_usd_krw()
    wti = get_wti()
    print(f"[SUMMARY] USD/KRW={usd_krw}, WTI={wti}")

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
            mv  = qty * price

            pnl = (avg - price) * qty if side.startswith("S") else (price - avg) * qty
            pnl_ratio = (pnl / exp) if exp else 0.0

            results.append({
                "symbol":     pos["symbol"],
                "name":       pos["name"],
                "side":       side,
                "qty":        qty,
                "avg_price":  avg,
                "group":      pos.get("group", pos["name"]),
                "last_price": price,
                "exposure":   exp,
                "mv":         mv,
                "pnl":        pnl,
                "pnl_ratio":  pnl_ratio,
            })

            total_exposure += exp
            total_pnl      += pnl

    snapshot = {
        "as_of":           datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "currency":        CONFIG.get("currency", "KRW"),
        "positions":       results,
        "total_exposure":  total_exposure,
        "total_pnl":       total_pnl,
        "total_pnl_ratio": (total_pnl / total_exposure) if total_exposure else 0.0,
        "usd_krw":         usd_krw,
        "wti":             wti,
    }

    out_path = "web/live.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    subprocess.run("git add web/live.json", shell=True, check=False)
    subprocess.run(
        f'git commit -m "chore: update live {snapshot["as_of"]}"',
        shell=True, check=False,
    )
    subprocess.run("git push", shell=True, check=False)


if __name__ == "__main__":
    asyncio.run(main())