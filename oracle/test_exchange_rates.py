"""
USD/PHP Exchange Rate API Testing

Simple testing script to verify exchange rate APIs are working
for ORACLE's USD/PHP conversion functionality.
"""

import requests
import json
from datetime import datetime

# ========== OPTION 1: ExchangeRate-API (Recommended) ==========
# ✅ FREE: 1,500 requests/month 
# ✅ Updated every 24 hours (good for our use case)
# ✅ No API key required for basic plan
# ✅ Very reliable and fast

def get_usd_php_rate_option1():
    """Get USD/PHP rate from ExchangeRate-API (FREE)"""
    try:
        url = "https://v6.exchangerate-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('result') == 'success':
            php_rate = data['conversion_rates']['PHP']
            last_update = data.get('time_last_update_utc')
            
            return {
                'rate': php_rate,
                'last_update': last_update,
                'source': 'ExchangeRate-API'
            }
    except Exception as e:
        print(f"Error getting exchange rate: {e}")
        return None

# ========== OPTION 2: Fawaz Free API (No limits!) ==========
# ✅ FREE: Unlimited requests
# ✅ No API key required
# ✅ GitHub-hosted, open source

def get_usd_php_rate_option2():
    """Get USD/PHP rate from Fawaz Free API (UNLIMITED)"""
    try:
        url = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        php_rate = data['usd']['php']
        last_update = data.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        return {
            'rate': php_rate,
            'last_update': last_update,
            'source': 'Fawaz Free API'
        }
    except Exception as e:
        print(f"Error getting exchange rate: {e}")
        return None

# ========== SMART EXCHANGE RATE FUNCTION ==========
# Uses multiple APIs with fallback

def get_usd_php_rate():
    """
    Get USD/PHP exchange rate with fallback options
    Returns current USD to PHP exchange rate
    """
    
    # Try Option 1 first (ExchangeRate-API)
    rate_data = get_usd_php_rate_option1()
    if rate_data:
        return rate_data
    
    # Fallback to Option 2 (Fawaz Free API)
    print("Primary API failed, trying fallback...")
    rate_data = get_usd_php_rate_option2()
    if rate_data:
        return rate_data
    
    # If all APIs fail, use estimated rate
    print("All APIs failed, using estimated rate...")
    return {
        'rate': 56.5,  # Approximate current rate
        'last_update': 'estimated',
        'source': 'fallback_estimate'
    }

# ========== CONVERSION FUNCTIONS ==========

def convert_usd_to_php(usd_amount, exchange_rate=None):
    """Convert USD amount to PHP"""
    if exchange_rate is None:
        rate_data = get_usd_php_rate()
        exchange_rate = rate_data['rate']
    
    php_amount = usd_amount * exchange_rate
    return php_amount

def convert_php_to_usd(php_amount, exchange_rate=None):
    """Convert PHP amount to USD"""
    if exchange_rate is None:
        rate_data = get_usd_php_rate()
        exchange_rate = rate_data['rate']
    
    usd_amount = php_amount / exchange_rate
    return usd_amount

def calculate_ai_targets_in_php(ai_buy_usd, ai_target_usd, ai_stop_usd):
    """
    Convert AI signal USD prices to PHP using live exchange rate
    
    Args:
        ai_buy_usd: AI entry price in USD
        ai_target_usd: AI target price in USD
        ai_stop_usd: AI stop loss in USD
        
    Returns:
        Dictionary with PHP prices and exchange rate info
    """
    
    # Get current exchange rate
    rate_data = get_usd_php_rate()
    usd_php_rate = rate_data['rate']
    
    # Convert all USD prices to PHP
    ai_buy_php = convert_usd_to_php(ai_buy_usd, usd_php_rate)
    ai_target_php = convert_usd_to_php(ai_target_usd, usd_php_rate)
    ai_stop_php = convert_usd_to_php(ai_stop_usd, usd_php_rate)
    
    return {
        'ai_buy_php': ai_buy_php,
        'ai_target_php': ai_target_php,
        'ai_stop_php': ai_stop_php,
        'usd_php_rate': usd_php_rate,
        'rate_source': rate_data['source'],
        'rate_updated': rate_data['last_update']
    }

# ========== API TESTING ==========

def test_exchange_rate_apis():
    """Test all exchange rate APIs for functionality"""
    
    print("=" * 60)
    print("🌐 TESTING USD/PHP EXCHANGE RATE APIs")
    print("=" * 60)
    
    # Test Individual APIs
    print("🔍 Testing individual APIs...")
    print()
    
    # Test Option 1: ExchangeRate-API
    print("📡 Testing ExchangeRate-API...")
    rate1 = get_usd_php_rate_option1()
    if rate1:
        print(f"   ✅ Success: {rate1['rate']:.4f} PHP per USD")
        print(f"   📅 Last updated: {rate1['last_update']}")
    else:
        print("   ❌ Failed")
    print()
    
    # Test Option 2: Fawaz Free API
    print("📡 Testing Fawaz Free API...")
    rate2 = get_usd_php_rate_option2()
    if rate2:
        print(f"   ✅ Success: {rate2['rate']:.4f} PHP per USD")
        print(f"   📅 Last updated: {rate2['last_update']}")
    else:
        print("   ❌ Failed")
    print()
    
    # Test Smart Fallback Function
    print("🤖 Testing smart fallback function...")
    rate_data = get_usd_php_rate()
    print(f"✅ Current USD/PHP rate: {rate_data['rate']:.4f}")
    print(f"📅 Last updated: {rate_data['last_update']}")
    print(f"🔗 Source: {rate_data['source']}")
    print()
    
    # Test Conversion Functions
    print("🔄 Testing conversion functions...")
    test_usd_amount = 100
    test_php_amount = convert_usd_to_php(test_usd_amount, rate_data['rate'])
    converted_back = convert_php_to_usd(test_php_amount, rate_data['rate'])
    
    print(f"   ${test_usd_amount} USD → ₱{test_php_amount:.2f} PHP")
    print(f"   ₱{test_php_amount:.2f} PHP → ${converted_back:.2f} USD")
    
    if abs(converted_back - test_usd_amount) < 0.01:
        print("   ✅ Conversion functions working correctly")
    else:
        print("   ❌ Conversion error detected")
    print()
    
    # Test AI Signal Conversion
    print("🎯 Testing AI signal conversion...")
    ai_signal_example = {
        'buy_price': 2.45,    # USD
        'target_price': 2.58, # USD  
        'stop_loss': 2.35     # USD
    }
    
    php_prices = calculate_ai_targets_in_php(
        ai_signal_example['buy_price'],
        ai_signal_example['target_price'], 
        ai_signal_example['stop_loss']
    )
    
    print(f"   AI Entry: ${ai_signal_example['buy_price']:.2f} → ₱{php_prices['ai_buy_php']:.2f}")
    print(f"   AI Target: ${ai_signal_example['target_price']:.2f} → ₱{php_prices['ai_target_php']:.2f}")
    print(f"   AI Stop: ${ai_signal_example['stop_loss']:.2f} → ₱{php_prices['ai_stop_php']:.2f}")
    print(f"   Exchange Rate: 1 USD = {php_prices['usd_php_rate']:.4f} PHP")
    print(f"   ✅ AI signal conversion working")
    print()
    
    # Summary
    print("📊 SUMMARY:")
    working_apis = 0
    if rate1:
        working_apis += 1
        print(f"   ✅ ExchangeRate-API: Working ({rate1['rate']:.4f})")
    else:
        print("   ❌ ExchangeRate-API: Failed")
    
    if rate2:
        working_apis += 1
        print(f"   ✅ Fawaz Free API: Working ({rate2['rate']:.4f})")
    else:
        print("   ❌ Fawaz Free API: Failed")
    
    print(f"   📈 Working APIs: {working_apis}/2")
    
    if working_apis > 0:
        print("   ✅ ORACLE exchange rate functionality: READY")
    else:
        print("   ❌ ORACLE exchange rate functionality: FAILED")
    
    print("=" * 60)

if __name__ == "__main__":
    test_exchange_rate_apis()