#!/usr/bin/env python3
"""
coinsph_trade_fee_checker.py

Fetches current trade fees for a given symbol from the Coins.ph REST API using HMAC authentication.
Usage: python coinsph_trade_fee_checker.py SOLPHP
"""
import os
import sys
import hmac
import hashlib
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY    = os.getenv("COINS_API_KEY")
API_SECRET = os.getenv("COINS_SECRET_KEY")

if not API_KEY or not API_SECRET:
    print("🔴 Error: COINS_API_KEY and COINS_SECRET_KEY must be set in .env.")
    sys.exit(1)

# Based on documentation, the correct host is api.pro.coins.ph and endpoint is /openapi/v1/asset/tradeFee
BASE_URL = "https://api.pro.coins.ph"
ENDPOINT = "/openapi/v1/asset/tradeFee"

# Helper to create HMAC SHA256 signature
def create_signature(ts: str, method: str, path: str, secret: str) -> str:
    payload = ts + method + path
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

# Main function to fetch fees
def fetch_trade_fee(symbol: str):
    ts = str(int(time.time() * 1000))  # timestamp in milliseconds
    method = "GET"
    # include query in path for REST signature
    signed_path = f"{ENDPOINT}?symbol={symbol}"
    url = BASE_URL + signed_path

    # Create signature
    signature = create_signature(ts, method, signed_path, API_SECRET)

    headers = {
        "X-COINS-APIKEY":    API_KEY,
        "X-COINS-TIMESTAMP": ts,
        "X-COINS-SIGN":      signature,
        "Content-Type":      "application/json",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.HTTPError as e:
        print(f"🔴 HTTP error: {e} - {resp.text}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"🔴 Connection error: {e}")
        sys.exit(1)

    data = resp.json()
    # Expecting a JSON object with fields 'symbol', 'makerRate', 'takerRate'
    sym   = data.get("symbol")
    maker = data.get("makerRate")
    taker = data.get("takerRate")

    if sym is None or maker is None or taker is None:
        print(f"🔴 Unexpected response format: {data}")
        sys.exit(1)

    print(f"🟢 Trade fees for {sym}:")
    print(f"  • Maker rate: {maker * 100:.2f}%")
    print(f"  • Taker rate: {taker * 100:.2f}%")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("🔴 Usage: python coinsph_trade_fee_checker.py <SYMBOL>")
        sys.exit(1)
    symbol = sys.argv[1]
    fetch_trade_fee(symbol)
