"""
test_signals.py - Send fake MarketRaker signals to test momentum_v4
"""

import requests
import json
import time

def create_fake_xrp_buy_signal():
    """Create a fake XRP buy signal like MarketRaker would send"""
    return {
        "type": "indicator",
        "data": {
            "trading_type": "Long",
            "leverage": 1,
            "buy_price": 2.45,  # USD price (current XRP ~$2.45)
            "sell_price": 2.58,  # USD target (+5.3%)
            "buy_date": int(time.time()),
            "sell_prediction_date": int(time.time()) + 3600,  # 1 hour later
            "risk": 4,  # Medium risk (1-10 scale)
            "market_direction": "Bull",
            "percentage_change": 5.3,
            "stoploss": 2.35,  # USD stop loss
            "trading_pair": "XRP/USD"
        }
    }

def send_test_signal():
    """Send a test signal to momentum_v4"""
    
    # Check if server is running
    try:
        health_response = requests.get("http://localhost:8000/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ momentum_v4 server not responding!")
            return
        print("✅ momentum_v4 server is healthy")
    except:
        print("❌ Can't connect to momentum_v4 server!")
        print("   Make sure it's running: python momentum_v4.py")
        return
    
    # Create fake signal
    signal = create_fake_xrp_buy_signal()
    
    print("\n📡 Sending fake XRP buy signal:")
    print(f"   Type: {signal['data']['trading_type']}")
    print(f"   Pair: {signal['data']['trading_pair']}")
    print(f"   Entry: ${signal['data']['buy_price']}")
    print(f"   Target: ${signal['data']['sell_price']}")
    print(f"   Expected: +{signal['data']['percentage_change']}%")
    print(f"   Risk: {signal['data']['risk']}/10")
    
    # Send to test webhook
    try:
        response = requests.post(
            "http://localhost:8000/webhook/test",
            json=signal,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\n✅ Response: {response.status_code}")
        print(f"📄 Body: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 Signal sent successfully!")
            print("   Check momentum_v4 terminal for webhook logs")
        else:
            print(f"\n❌ Signal failed with status {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error sending signal: {e}")

def main():
    print("=" * 60)
    print("🧪 TESTING FAKE MARKETRAKER SIGNALS")
    print("=" * 60)
    
    send_test_signal()
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("   Check momentum_v4 logs to see signal reception")
    print("=" * 60)

if __name__ == "__main__":
    main()