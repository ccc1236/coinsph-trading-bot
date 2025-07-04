import os
from dotenv import load_dotenv
from fixed_coins_api import CoinsAPI

load_dotenv()

api = CoinsAPI(
    api_key=os.getenv('COINS_API_KEY'),
    secret_key=os.getenv('COINS_SECRET_KEY')
)

print("=== TESTING FIXED API ===")
print()

# Test 1: Public endpoint (should work)
print("--- Public Test ---")
try:
    price = api.get_current_price('BTCPHP')
    print(f"✅ Current BTC price: ₱{price:,.2f}")
except Exception as e:
    print(f"❌ Public test failed: {e}")

print()

# Test 2: Account info (this was failing before)
print("--- Account Info Test ---")
try:
    account = api.get_account_info()
    print(f"✅ Account info successful!")
    print(f"Account type: {account.get('accountType', 'N/A')}")
    print(f"Can trade: {account.get('canTrade', 'N/A')}")
    print(f"Can deposit: {account.get('canDeposit', 'N/A')}")
    print(f"Can withdraw: {account.get('canWithdraw', 'N/A')}")
except Exception as e:
    print(f"❌ Account test failed: {e}")

print()

# Test 3: Balance (this was returning empty)
print("--- Balance Test ---")
try:
    balances = api.get_balance()
    print(f"✅ Balance successful!")
    if balances:
        for balance in balances:
            print(f"  {balance['asset']}: {balance['total']:.6f}")
    else:
        print("  No balances found")
except Exception as e:
    print(f"❌ Balance test failed: {e}")

print()
print("=== TEST COMPLETE ===")