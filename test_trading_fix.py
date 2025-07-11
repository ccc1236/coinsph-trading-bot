import os
import logging
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

load_dotenv()

def test_trading_endpoints():
    """Test trading-specific endpoints that were failing"""
    
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )
    
    print("🔧 TESTING TRADING ENDPOINT SIGNATURES")
    print("=" * 50)
    
    # Test 1: Open Orders (was failing before)
    print("\n📋 Testing open orders for XRPPHP...")
    try:
        open_orders = api.get_open_orders('XRPPHP')
        print(f"✅ Open orders success: {len(open_orders)} orders")
    except Exception as e:
        print(f"❌ Open orders failed: {e}")
    
    # Test 2: Order History
    print("\n📜 Testing order history for XRPPHP...")
    try:
        order_history = api.get_order_history('XRPPHP', limit=5)
        print(f"✅ Order history success: {len(order_history)} orders")
    except Exception as e:
        print(f"❌ Order history failed: {e}")
    
    # Test 3: Current Price (should work)
    print("\n💰 Testing current price...")
    try:
        price = api.get_current_price('XRPPHP')
        print(f"✅ Current XRPPHP price: ₱{price:.4f}")
    except Exception as e:
        print(f"❌ Price check failed: {e}")
    
    # Test 4: Account Info (should work)
    print("\n👤 Testing account info...")
    try:
        account = api.get_account_info()
        print(f"✅ Account info: Can trade = {account.get('canTrade')}")
    except Exception as e:
        print(f"❌ Account info failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 If open orders and order history work, the signature fix is successful!")
    print("🚀 Your bot should now be able to place orders!")

if __name__ == "__main__":
    test_trading_endpoints()