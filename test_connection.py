import os
import logging
from dotenv import load_dotenv
from coinsph_api import CoinsAPI

# Load environment variables
load_dotenv(override=True)

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_api_connection():
    """Test API connection and functionality"""
    
    # Get API credentials from environment
    api_key = os.getenv('COINS_API_KEY')
    secret_key = os.getenv('COINS_SECRET_KEY')
    trading_symbol = os.getenv('TRADING_SYMBOL', 'BTCPHP')  # Use from .env file
    
    if not api_key or not secret_key:
        logging.error("API keys not found! Please check your .env file")
        return False
    
    logging.info("🔑 API keys loaded successfully")
    
    # Initialize API client
    api = CoinsAPI(api_key, secret_key)
    
    print("=" * 50)
    print("🚀 COINS.PH API CONNECTION TEST")
    print("=" * 50)
    print(f"📊 Testing with symbol: {trading_symbol}")
    print()
    
    # Test 1: Basic connectivity
    try:
        logging.info("📡 Testing basic connectivity...")
        ping_result = api.ping()
        print("✅ Ping successful:", ping_result)
    except Exception as e:
        print("❌ Ping failed:", e)
        return False
    
    # Test 2: Server time
    try:
        logging.info("⏰ Getting server time...")
        time_result = api.get_server_time()
        print("✅ Server time:", time_result)
    except Exception as e:
        print("❌ Server time failed:", e)
        return False
    
    # Test 3: Exchange info (using your symbol)
    try:
        logging.info(f"📊 Getting exchange information for {trading_symbol}...")
        exchange_info = api.get_exchange_info(trading_symbol)
        if exchange_info.get('symbols'):
            symbol_info = exchange_info['symbols'][0]
            print(f"✅ Exchange info for {trading_symbol}:")
            print(f"   Status: {symbol_info.get('status')}")
            print(f"   Base Asset: {symbol_info.get('baseAsset')}")
            print(f"   Quote Asset: {symbol_info.get('quoteAsset')}")
        else:
            print(f"⚠️  {trading_symbol} symbol not found")
    except Exception as e:
        print("❌ Exchange info failed:", e)
        return False
    
    # Test 4: Market data (using your symbol)
    try:
        logging.info(f"💰 Getting market data for {trading_symbol}...")
        price_data = api.get_ticker_price(trading_symbol)
        print(f"✅ Current {trading_symbol} price:", price_data.get('price'))
        
        ticker_24hr = api.get_24hr_ticker(trading_symbol)
        print("✅ 24hr change:", ticker_24hr.get('priceChangePercent', 'N/A') + "%")
    except Exception as e:
        print("❌ Market data failed:", e)
        return False
    
    # Test 5: Account information (requires authentication)
    try:
        logging.info("👤 Testing account access...")
        account_info = api.get_account_info()
        
        # Check if we got an error response
        if account_info.get('code') and account_info.get('msg'):
            print("❌ Account access failed:", account_info.get('msg'))
            return False
        
        print("✅ Account access successful!")
        print(f"   Account type: {account_info.get('accountType', 'N/A')}")
        print(f"   Can trade: {account_info.get('canTrade', 'N/A')}")
        print(f"   Can deposit: {account_info.get('canDeposit', 'N/A')}")
        print(f"   Can withdraw: {account_info.get('canWithdraw', 'N/A')}")
        
    except Exception as e:
        print("❌ Account access failed:", e)
        print("   Check your API key permissions and IP whitelist")
        return False
    
    # Test 6: Account balances
    try:
        logging.info("💼 Getting account balances...")
        account_info = api.get_account_info()
        
        if account_info.get('balances'):
            balances = account_info['balances']
            print("✅ Account balances:")
            
            # Show non-zero balances
            non_zero_balances = []
            for balance in balances:
                total = float(balance['free']) + float(balance['locked'])
                if total > 0:
                    non_zero_balances.append({
                        'asset': balance['asset'],
                        'total': total,
                        'free': float(balance['free']),
                        'locked': float(balance['locked'])
                    })
            
            if non_zero_balances:
                for balance in non_zero_balances[:10]:  # Show first 10
                    if balance['total'] >= 0.000001:  # Skip tiny amounts
                        print(f"   {balance['asset']}: {balance['total']:.6f} (Free: {balance['free']:.6f})")
                if len(non_zero_balances) > 10:
                    print(f"   ... and {len(non_zero_balances) - 10} more assets")
            else:
                print("   No significant balances found")
        else:
            print("❌ No balance data in response")
            
    except Exception as e:
        print("❌ Balance check failed:", e)
        return False
    
    # Test 7: Open orders (using your symbol)
    try:
        logging.info(f"📋 Checking open orders for {trading_symbol}...")
        open_orders = api.get_open_orders(trading_symbol)
        
        # Check if we got an error response
        if isinstance(open_orders, dict) and open_orders.get('code'):
            print(f"⚠️  Open orders check had issues: {open_orders.get('msg', 'Unknown error')}")
        elif isinstance(open_orders, list):
            print(f"✅ Open orders for {trading_symbol}: {len(open_orders)} orders")
            
            if open_orders:
                for order in open_orders[:3]:  # Show first 3
                    print(f"   Order {order.get('orderId')}: {order.get('side')} {order.get('origQty')} at {order.get('price')}")
        else:
            print("⚠️  Unexpected open orders response format")
            
    except Exception as e:
        print(f"⚠️  Open orders check failed: {e}")
        # Don't return False here as this isn't critical
    
    print("=" * 50)
    print("🎉 CORE TESTS PASSED! Your API setup is working correctly.")
    print("=" * 50)
    
    return True

def test_trading_permissions():
    """Test if trading is enabled and check order placement capabilities"""
    
    api_key = os.getenv('COINS_API_KEY')
    secret_key = os.getenv('COINS_SECRET_KEY')
    trading_symbol = os.getenv('TRADING_SYMBOL', 'BTCPHP')
    base_amount = float(os.getenv('BASE_AMOUNT', 1000))
    
    api = CoinsAPI(api_key, secret_key)
    
    print(f"\n🔧 TESTING TRADING READINESS FOR {trading_symbol}...")
    print("-" * 50)
    
    try:
        account = api.get_account_info()
        
        if account.get('canTrade'):
            print("✅ Trading permissions: ENABLED")
            
            # Check if we have enough balance for minimum trade
            balances = account.get('balances', [])
            php_balance = 0
            
            for balance in balances:
                if balance['asset'] == 'PHP':
                    php_balance = float(balance['free'])
                    break
            
            print(f"✅ PHP Balance: ₱{php_balance:,.2f}")
            print(f"✅ Configured trade amount: ₱{base_amount:,.2f}")
            
            # Check minimum order size for your symbol
            symbol_info = api.get_symbol_info(trading_symbol)
            if symbol_info:
                filters = symbol_info.get('filters', [])
                min_notional = 0
                
                for f in filters:
                    if f.get('filterType') == 'MIN_NOTIONAL':
                        min_notional = float(f.get('minNotional', 0))
                        break
                
                print(f"✅ Minimum order size for {trading_symbol}: ₱{min_notional}")
                
                if php_balance >= base_amount >= min_notional:
                    print("✅ You have sufficient balance to trade!")
                    
                    # Get current price
                    current_price = api.get_current_price(trading_symbol)
                    quantity_you_can_buy = base_amount / current_price
                    print(f"✅ Current {trading_symbol} price: ₱{current_price:.2f}")
                    print(f"✅ With ₱{base_amount}, you can buy ~{quantity_you_can_buy:.6f} {symbol_info.get('baseAsset')}")
                    
                elif base_amount < min_notional:
                    print(f"⚠️  Your BASE_AMOUNT (₱{base_amount}) is below minimum (₱{min_notional})")
                    print(f"   Update your .env file: BASE_AMOUNT={int(min_notional) + 1}")
                else:
                    print(f"⚠️  You need at least ₱{base_amount} to place your configured trade size")
            
        else:
            print("❌ Trading permissions: DISABLED")
            print("   Contact Coins.ph support to enable trading")
            
    except Exception as e:
        print(f"❌ Trading test failed: {e}")

if __name__ == "__main__":
    success = test_api_connection()
    if success:
        test_trading_permissions()
        print(f"\n🚀 YOUR BOT IS READY TO TRADE {os.getenv('TRADING_SYMBOL', 'BTCPHP')}!")
        print("Run: py simple_bot.py")
    else:
        print("\n❌ Please fix the API connection issues before proceeding.")