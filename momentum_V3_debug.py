#!/usr/bin/env python3

print("🔍 Starting momentum_v3 debug...")

try:
    print("📦 Testing imports...")
    
    import sys
    print("✅ sys imported")
    
    import os
    print("✅ os imported")
    
    import time
    print("✅ time imported")
    
    import logging
    print("✅ logging imported")
    
    from datetime import datetime, timedelta
    print("✅ datetime imported")
    
    from dotenv import load_dotenv
    print("✅ dotenv imported")
    
    from coinsph_api import CoinsAPI
    print("✅ coinsph_api imported")
    
    print("\n🔍 Testing environment...")
    load_dotenv(override=True)
    
    api_key = os.getenv('COINS_API_KEY')
    secret_key = os.getenv('COINS_SECRET_KEY')
    
    if api_key and secret_key:
        print("✅ API credentials found")
        print(f"   API Key: {api_key[:10]}...")
        print(f"   Secret Key: {secret_key[:10]}...")
    else:
        print("❌ API credentials missing!")
        print("   Please check your .env file")
        exit(1)
    
    print("\n🔍 Testing API connection...")
    api = CoinsAPI(api_key, secret_key)
    
    try:
        ping_result = api.ping()
        print("✅ API ping successful")
    except Exception as e:
        print(f"❌ API ping failed: {e}")
        exit(1)
    
    print("\n🚀 All tests passed! Starting main script...")
    
    # Now run the actual main function
    def get_user_inputs():
        """Get trading parameters from user"""
        print("🚀 MOMENTUM TRADING BOT v3.0")
        print("💡 Choose your trading asset and take profit level")
        print("=" * 60)
        
        # Asset selection
        print("🎯 Select trading asset:")
        print("1. XRPPHP - Recommended (Backtested +1.5% with 5.0% TP)")
        print("2. SOLPHP - High volatility (Backtested -1.3% with 1.8% TP)")
        print("3. Custom symbol")
        
        while True:
            choice = input("Enter choice (1-3): ").strip()
            if choice == '1':
                symbol = 'XRPPHP'
                suggested_tp = 5.0
                break
            elif choice == '2':
                symbol = 'SOLPHP'
                suggested_tp = 1.8
                break
            elif choice == '3':
                symbol = input("Enter symbol (e.g., BTCPHP): ").strip().upper()
                suggested_tp = 2.0
                break
            else:
                print("Please enter 1, 2, or 3")
        
        # Take profit selection
        print(f"\n🎯 Configure take profit for {symbol}:")
        print(f"💡 Suggested: {suggested_tp:.1f}% (based on backtesting)")
        print("📊 Other options:")
        print("   1.0% - Conservative (quick profits)")
        print("   2.0% - Balanced")
        print("   3.0% - Moderate")
        print("   5.0% - Aggressive")
        
        while True:
            try:
                take_profit = input(f"Enter take profit % (suggested: {suggested_tp:.1f}): ").strip()
                if not take_profit:  # Use suggested if empty
                    take_profit = suggested_tp
                    break
                else:
                    take_profit = float(take_profit)
                    if 0.1 <= take_profit <= 10.0:
                        break
                    else:
                        print("Please enter a value between 0.1% and 10.0%")
            except ValueError:
                print("Please enter a valid number")
        
        # Confirmation
        print(f"\n✅ CONFIGURATION CONFIRMED:")
        print(f"🎯 Asset: {symbol}")
        print(f"📈 Take Profit: {take_profit:.1f}%")
        print(f"💰 Trade Size: ₱200")
        print(f"⏰ Check Interval: 15 minutes")
        
        return symbol, take_profit

    # Get user inputs
    symbol, take_profit = get_user_inputs()
    
    print(f"\n🎯 You selected: {symbol} with {take_profit:.1f}% take profit")
    print("✅ Debug completed successfully!")
    print("\nIf this works, the full momentum_v3.py should work too.")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("💡 Try: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    import traceback
    traceback.print_exc()