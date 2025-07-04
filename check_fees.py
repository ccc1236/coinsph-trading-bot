import os
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

def check_trading_fees():
    """Check actual trading fees for your symbol"""
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )
    
    symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')
    
    try:
        # Get trading fees
        fees = api._make_request('GET', '/openapi/v1/asset/tradeFee', {'symbol': symbol}, signed=True)
        
        print("💰 TRADING FEES FOR", symbol)
        print("=" * 40)
        
        if isinstance(fees, list) and fees:
            fee_info = fees[0]
            maker_fee = float(fee_info.get('makerCommission', 0))
            taker_fee = float(fee_info.get('takerCommission', 0))
            
            print(f"📊 Maker fee: {maker_fee*100:.3f}%")
            print(f"📊 Taker fee: {taker_fee*100:.3f}%")
            
            # Calculate impact on 90-day backtest
            total_trades = 259
            avg_trade_size = 100
            
            # Assuming all trades are taker orders (market orders)
            total_fees = total_trades * avg_trade_size * taker_fee
            
            print(f"\n💸 IMPACT ON 90-DAY BACKTEST:")
            print(f"   Total trades: {total_trades}")
            print(f"   Average trade size: ₱{avg_trade_size}")
            print(f"   Total fees: ₱{total_fees:.2f}")
            
            # Adjusted results
            original_profit = 28.18
            adjusted_profit = original_profit - total_fees
            
            print(f"\n📊 ADJUSTED RESULTS:")
            print(f"   Original profit: ₱{original_profit}")
            print(f"   After fees: ₱{adjusted_profit:.2f}")
            
            if adjusted_profit < 0:
                print("❌ Grid strategy would be UNPROFITABLE after fees!")
            else:
                print("✅ Still profitable after fees")
                
        else:
            print("❌ Could not get fee information")
            print("Assuming typical 0.25% taker fee...")
            
            total_trades = 259
            avg_trade_size = 100
            assumed_fee = 0.0025  # 0.25%
            
            total_fees = total_trades * avg_trade_size * assumed_fee
            original_profit = 28.18
            adjusted_profit = original_profit - total_fees
            
            print(f"💸 With 0.25% fees:")
            print(f"   Total fees: ₱{total_fees:.2f}")
            print(f"   Adjusted profit: ₱{adjusted_profit:.2f}")
            
    except Exception as e:
        print(f"❌ Error checking fees: {e}")

if __name__ == "__main__":
    check_trading_fees()