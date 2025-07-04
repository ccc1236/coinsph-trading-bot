import os
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

def verify_backtest_logic():
    """Simple verification of what happened"""
    print("🔍 BACKTEST VERIFICATION")
    print("=" * 40)
    
    # The key numbers from your backtest
    starting_balance = 2000.00
    final_value = 2066.49
    actual_profit = final_value - starting_balance
    
    print(f"📊 Starting value: ₱{starting_balance}")
    print(f"📊 Final value: ₱{final_value}")
    print(f"📊 ACTUAL PROFIT: ₱{actual_profit:.2f}")
    print()
    
    # Buy & hold comparison
    start_price = 120.43
    end_price = 123.85
    
    if_bought_and_held = starting_balance / start_price
    buy_hold_value = if_bought_and_held * end_price
    buy_hold_profit = buy_hold_value - starting_balance
    
    print(f"💰 If you bought ₱2000 of XRP at ₱{start_price}:")
    print(f"💰 You'd have {if_bought_and_held:.4f} XRP")
    print(f"💰 Worth ₱{buy_hold_value:.2f} at end price ₱{end_price}")
    print(f"💰 Buy & hold profit: ₱{buy_hold_profit:.2f}")
    print()
    
    advantage = actual_profit - buy_hold_profit
    print(f"🎯 Grid advantage: ₱{advantage:.2f}")
    print()
    
    if actual_profit > 0:
        print("✅ Grid strategy was PROFITABLE")
        print(f"✅ Made ₱{actual_profit:.2f} in 30 days")
        print(f"✅ That's {(actual_profit/starting_balance)*100:.2f}% return")
        
        if advantage > 0:
            print(f"🏆 BEAT buy & hold by ₱{advantage:.2f}")
        else:
            print(f"📉 Underperformed buy & hold by ₱{abs(advantage):.2f}")
    else:
        print("❌ Grid strategy lost money")
    
    print()
    print("🔧 CONCLUSION:")
    print("The ₱-751.26 'trading profits' is definitely a BUG")
    print("The REAL profit is ₱66.49 (final value - starting value)")

if __name__ == "__main__":
    verify_backtest_logic()