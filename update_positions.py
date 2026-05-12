#!/usr/bin/env python3
import os, json, asyncio, aiohttp, subprocess, requests, time
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "*/*",
}


async def get_kis_token():
    token_path = '/home/ubuntu/shmon/.kis_token.json'
    with open('/home/ubuntu/shmon/.env') as f:
        env = dict(line.strip().split('=', 1) for line in f if '=' in line and not line.startswith('#'))
    try:
        with open(token_path) as f:
            d = json.load(f)
        if time.time() - d['issued_at'] < 86100:
            return d['token'], env
    except:
        pass
    async with aiohttp.ClientSession() as session:
        resp = await session.post(
            'https://openapi.koreainvestment.com:9443/oauth2/tokenP',
            json={
                'grant_type': 'client_credentials',
                'appkey':     env['KIS_APP_KEY'],
                'appsecret':  env['KIS_APP_SECRET'],
            }
        )
        data = await resp.json()
    token = data['access_token']
    with open(token_path, 'w') as f:
        json.dump({'token': token, 'issued_at': time.time()}, f)
    return token, env


async def fetch_price(session, symbol: str, token: str, env: dict) -> float | None:
    try:
        url = 'https://openapi.koreainvestment.com:9443/uapi/domestic-stock/v1/quotations/inquire-price'
        async with session.get(
            url,
            headers={
                'authorization': f'Bearer {token}',
                'appkey':        env['KIS_APP_KEY'],
                'appsecret':     env['KIS_APP_SECRET'],
                'tr_id':         'FHKST01010100',
            },
            params={
                'fid_cond_mrkt_div_code': 'J',
                'fid_input_iscd':         symbol,
            },
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            data  = await resp.json(content_type=None)
            price = data.get('output', {}).get('stck_prpr')
            if not price:
                msg = data.get('msg1', '')
                print(f'[WARN] {symbol}: {msg}')
            return float(price) if price else None
    except Exception as e:
        print(f'[WARN] price fetch failed {symbol}: {e}')
        return None


def get_usd_krw():
    try:
        res = requests.get('https://open.er-api.com/v6/latest/USD', timeout=5)
        return res.json()['rates']['KRW']
    except Exception as e:
        print(f"[WARN] usd_krw fetch failed: {e}")
        return None


def get_wti():
    try:
        import yfinance as yf
        ticker = yf.Ticker("CL=F")
        price  = ticker.fast_info["last_price"]
        if price:
            print(f"[INFO] WTI from fast_info: {price}")
            return float(price)
    except Exception as e:
        print(f"[WARN] yfinance fast_info failed: {e}")

    try:
        import yfinance as yf
        ticker = yf.Ticker("CL=F")
        hist   = ticker.history(period="5d", interval="1m")
        if not hist.empty:
            closes = hist["Close"].dropna()
            if not closes.empty:
                print(f"[INFO] WTI from history fallback: {closes.iloc[-1]}")
                return float(closes.iloc[-1])
    except Exception as e:
        print(f"[WARN] yfinance history fallback failed: {e}")

    print("[ERROR] WTI fetch all sources failed, returning None")
    return None


async def main():
    # config.json 매번 재로드 (웹 UI 수정 반영)
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    positions = [p for p in config.get("positions", []) if not p.get("deleted", False)]

    results        = []
    total_exposure = 0.0
    total_pnl      = 0.0

    usd_krw = get_usd_krw()
    wti     = get_wti()
    print(f"USD/KRW: {usd_krw}, WTI: {wti}")

    # 토큰 한 번만 발급
    token, env = await get_kis_token()

    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        for pos in positions:
            price = await fetch_price(session, pos["symbol"], token, env)
            await asyncio.sleep(1.0)
            if price is None:
                price = float(pos.get("avg_price", 0))

            qty  = float(pos["qty"])
            avg  = float(pos["avg_price"])
            side = (pos.get("side") or "LONG").upper()

            exp = avg * qty
            mv  = qty * price

            if side.startswith("S"):
                pnl = (avg - price) * qty
            else:
                pnl = (price - avg) * qty

            cost      = exp
            pnl_ratio = (pnl / cost) if cost else 0.0

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
        "currency":        config.get("currency", "KRW"),
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


if __name__ == "__main__":
    asyncio.run(main())