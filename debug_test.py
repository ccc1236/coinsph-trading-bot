import os
import json
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv()

api = CoinsAPI(
    api_key=os.getenv('COINS_API_KEY'),
    secret_key=os.getenv('COINS_SECRET_KEY')
)

print("=== DETAILED DEBUG TEST ===")
print(f"Base URL: {api.base_url}")
print(f"API Key (first 10 chars): {api.api_key[:10]}...")
print()

# Test each endpoint individually
tests = [
    ("Server Time", lambda: api.get_server_time()),
    ("Exchange Info", lambda: api.get_exchange_info('BTCPHP')),
    ("Current Price", lambda: api.get_ticker_price('BTCPHP')),
    ("Account Info", lambda: api.get_account_info()),
    ("Crypto Accounts", lambda: api.get_crypto_accounts()),
    ("Balance", lambda: api.get_balance()),
]

for test_name, test_func in tests:
    try:
        print(f"--- {test_name} ---")
        result = test_func()
        print(f"✅ Success:")
        print(json.dumps(result, indent=2))
        print()
    except Exception as e:
        print(f"❌ Failed: {e}")
        print()