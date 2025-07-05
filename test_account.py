import os
import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

# Use exact working method from test_signature.py
api_key = os.getenv('COINS_API_KEY')
secret_key = os.getenv('COINS_SECRET_KEY')

print("=== SIMPLE ACCOUNT TEST ===")

# Method that worked perfectly in test_signature.py
current_timestamp = int(time.time() * 1000)

account_params = {
    'recvWindow': '5000',
    'timestamp': str(current_timestamp)
}

account_query = urlencode(sorted(account_params.items()))
account_signature = hmac.new(
    secret_key.encode('utf-8'),
    account_query.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"Query: {account_query}")
print(f"Signature: {account_signature}")

# Make the request
url = "https://api.pro.coins.ph/openapi/v1/account"
headers = {'X-COINS-APIKEY': api_key}

final_params = {
    'recvWindow': '5000',
    'timestamp': str(current_timestamp),
    'signature': account_signature
}

try:
    response = requests.get(url, params=final_params, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(f"Account Type: {data.get('accountType')}")
        print(f"Can Trade: {data.get('canTrade')}")
        
        # Show balances
        balances = data.get('balances', [])
        print("Balances:")
        for balance in balances:
            total = float(balance['free']) + float(balance['locked'])
            if total > 0:
                print(f"  {balance['asset']}: {total}")
    else:
        print(f"❌ Failed: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")