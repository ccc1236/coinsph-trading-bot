import os
import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

def test_signature_methods():
    """Test different signature generation methods"""
    
    api_key = os.getenv('COINS_API_KEY')
    secret_key = os.getenv('COINS_SECRET_KEY')
    
    print("=== SIGNATURE TESTING ===")
    print(f"API Key (first 10): {api_key[:10]}...")
    print(f"Secret Key (first 10): {secret_key[:10]}...")
    print()
    
    # Test with Coins.ph documentation example
    print("--- Testing with Documentation Example ---")
    doc_params = {
        'symbol': 'BTCPHP',
        'side': 'BUY', 
        'type': 'LIMIT',
        'timeInForce': 'GTC',
        'quantity': '1',
        'price': '0.1',
        'recvWindow': '5000',
        'timestamp': '1538323200000'
    }
    
    doc_query = urlencode(sorted(doc_params.items()))
    doc_signature = hmac.new(
        secret_key.encode('utf-8'),
        doc_query.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"Doc Query: {doc_query}")
    print(f"Doc Signature: {doc_signature}")
    print()
    
    # Test account endpoint with current time
    print("--- Testing Account Endpoint ---")
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
    
    print(f"Account Query: {account_query}")
    print(f"Account Signature: {account_signature}")
    print()
    
    # Test actual API call
    print("--- Testing Actual API Call ---")
    url = "https://api.pro.coins.ph/openapi/v1/account"
    headers = {'X-COINS-APIKEY': api_key}
    
    final_params = {
        'recvWindow': '5000',
        'timestamp': str(current_timestamp),
        'signature': account_signature
    }
    
    try:
        response = requests.get(url, params=final_params, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Signature worked!")
        else:
            print("❌ Signature still failed")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print()
    
    # Test with server time sync
    print("--- Testing with Server Time ---")
    try:
        server_time_response = requests.get("https://api.pro.coins.ph/openapi/v1/time")
        server_time = server_time_response.json()['serverTime']
        
        synced_params = {
            'recvWindow': '5000',
            'timestamp': str(server_time)
        }
        
        synced_query = urlencode(sorted(synced_params.items()))
        synced_signature = hmac.new(
            secret_key.encode('utf-8'),
            synced_query.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        print(f"Server Time: {server_time}")
        print(f"Synced Query: {synced_query}")
        print(f"Synced Signature: {synced_signature}")
        
        synced_final_params = {
            'recvWindow': '5000',
            'timestamp': str(server_time),
            'signature': synced_signature
        }
        
        synced_response = requests.get(url, params=synced_final_params, headers=headers, timeout=30)
        print(f"Synced Status: {synced_response.status_code}")
        print(f"Synced Response: {synced_response.text}")
        
        if synced_response.status_code == 200:
            print("✅ Server time sync worked!")
        else:
            print("❌ Server time sync still failed")
            
    except Exception as e:
        print(f"❌ Server time test failed: {e}")

if __name__ == "__main__":
    test_signature_methods()