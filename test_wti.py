#!/usr/bin/env python3
"""WTI 데이터 소스 테스트 스크립트"""
import yfinance as yf

print("=" * 40)

# 1차: fast_info
print("[TEST 1] fast_info")
try:
    ticker = yf.Ticker("CL=F")
    price = ticker.fast_info["last_price"]
    print(f"  ✅ 성공: {price}")
except Exception as e:
    print(f"  ❌ 실패: {e}")

print()

# 2차: history (period=5d)
print("[TEST 2] history(period=5d)")
try:
    ticker = yf.Ticker("CL=F")
    hist = ticker.history(period="5d", interval="1m")
    if not hist.empty:
        closes = hist["Close"].dropna()
        print(f"  ✅ 성공: {closes.iloc[-1]}")
    else:
        print("  ❌ 실패: 빈 데이터")
except Exception as e:
    print(f"  ❌ 실패: {e}")

print()

# 3차: history (period=1d) — 기존 방식
print("[TEST 3] history(period=1d) — 기존 방식")
try:
    ticker = yf.Ticker("CL=F")
    hist = ticker.history(period="1d", interval="1m")
    if not hist.empty:
        print(f"  ✅ 성공: {hist['Close'].iloc[-1]}")
    else:
        print("  ❌ 실패: 빈 데이터")
except Exception as e:
    print(f"  ❌ 실패: {e}")

print("=" * 40)