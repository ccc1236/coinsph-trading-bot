import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class CleanExitBacktester:
    def __init__(self, symbol='SOLPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.initial_balance = 2000
        
        # CLEAN EXIT v4.3 PARAMETERS
        self.buy_threshold = 0.006     # 0.6%
        self.sell_threshold = 0.010    # 1.0%
        self.trade_amount = 200        # ₱200 trades
        self.sell_percentage = 1.00    # 🎯 100% CLEAN EXITS (vs 95%)
        self.min_hold_minutes = 30     # 30 minutes
        self.max_trades_per_day = 10   # High frequency
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        # State
        self.php_balance = self.initial_balance
        self.asset_balance = 0
        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.trade_history = []
        self.daily_trades = {}
        self.total_trades = 0
        self.total_fees_paid = 0
        
        asset_name = symbol.replace('PHP', '')
        print(f"🚀 CLEAN EXIT Trading Bot v4.3 for {symbol}")
        print(f"✨ Ultimate optimization: 100% clean exits!")
        print(f"📊 CLEAN EXIT parameters:")
        print(f"   📈 Buy threshold: {self.buy_threshold*100:.1f}%")
        print(f"   📉 Sell threshold: {self.sell_threshold*100:.1f}%")
        print(f"   💰 Trade amount: ₱{self.trade_amount}")
        print(f"   📉 Sell percentage: {self.sell_percentage*100:.0f}% (🎯 CLEAN EXITS!)")
        print(f"   ⏰ Min hold: {self.min_hold_minutes} minutes")
        print(f"   🔄 Max trades/day: {self.max_trades_per_day}")
        print(f"   🎯 Assets: SOL & XRP only")
        print(f"   ✨ No more tiny remainder trades!")

    def get_historical_data(self, days=60):
        """Get historical data"""
        print(f"\n📊 Fetching data for CLEAN EXIT testing...")
        
        try:
            klines = self.api._make_request(
                'GET', 
                '/openapi/quote/v1/klines',
                {
                    'symbol': self.symbol,
                    'interval': '1h',
                    'limit': min(days * 24, 1000)
                }
            )
            
            data = []
            for kline in klines:
                data.append({
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'close': float(kline[4])
                })
            
            if data:
                actual_days = (data[-1]['timestamp'] - data[0]['timestamp']).days
                print(f"✅ Got {len(data)} hourly candles covering {actual_days} days")
                return data, actual_days
            else:
                return None, 0
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None, 0

    def can_trade_today(self, current_time):
        """Check daily trade limit"""
        date_key = current_time.strftime('%Y-%m-%d')
        trades_today = self.daily_trades.get(date_key, 0)
        return trades_today < self.max_trades_per_day

    def can_sell_position(self, current_time):
        """Check minimum hold time"""
        if self.entry_time is None:
            return True
        hold_duration = current_time - self.entry_time
        min_hold_delta = timedelta(minutes=self.min_hold_minutes)
        return hold_duration >= min_hold_delta

    def update_daily_trades(self, current_time):
        """Update daily trade counter"""
        date_key = current_time.strftime('%Y-%m-%d')
        self.daily_trades[date_key] = self.daily_trades.get(date_key, 0) + 1

    def clean_exit_strategy(self, current_price, current_time, last_price):
        """CLEAN EXIT strategy: 100% exits, no remainders"""
        
        # Calculate price change
        price_change = (current_price - last_price) / last_price
        
        # CLEAN EXIT BUY CONDITIONS
        if (price_change > self.buy_threshold and           # 0.6% momentum
            self.php_balance > self.trade_amount * 1.1 and  # Have money
            self.can_trade_today(current_time) and          # Daily limit
            self.position is None):                          # No position
            
            self.place_clean_buy(current_price, current_time, price_change)
        
        # CLEAN EXIT SELL CONDITIONS
        elif (price_change < -self.sell_threshold and       # 1.0% decline
              self.asset_balance > 0.001 and                # Have position
              self.can_sell_position(current_time) and      # Hold time met
              self.can_trade_today(current_time)):           # Daily limit
            
            self.place_clean_sell(current_price, current_time, price_change, "Momentum Down")
        
        # Clean exit profit taking (2% profit)
        elif (self.entry_price and 
              current_price > self.entry_price and
              self.can_sell_position(current_time)):
            
            profit_pct = (current_price - self.entry_price) / self.entry_price
            if profit_pct > 0.02:  # 2% profit
                self.place_clean_sell(current_price, current_time, price_change, "Profit Taking")

    def place_clean_buy(self, price, time, change):
        """Clean buy: ₱200 trades"""
        
        # Use ₱200 amount
        amount_to_spend = min(self.trade_amount, self.php_balance * 0.9)
        
        if amount_to_spend < 20:
            return False
        
        # Calculate with maker fee
        fee = amount_to_spend * self.maker_fee
        total_cost = amount_to_spend + fee
        
        if self.php_balance >= total_cost:
            asset_quantity = amount_to_spend / price
            self.php_balance -= total_cost
            self.asset_balance += asset_quantity
            self.total_fees_paid += fee
            self.total_trades += 1
            self.position = 'long'
            self.entry_price = price
            self.entry_time = time
            self.update_daily_trades(time)
            
            asset_name = self.symbol.replace('PHP', '')
            print(f"💰 CLEAN BUY: ₱{amount_to_spend:.2f} {asset_name} at ₱{price:.2f}")
            print(f"   📊 Change: {change*100:+.2f}% | Fee: ₱{fee:.2f}")
            
            self.trade_history.append({
                'timestamp': time,
                'side': 'BUY',
                'price': price,
                'amount': amount_to_spend,
                'quantity': asset_quantity,
                'fee': fee,
                'price_change': change,
                'reason': 'Clean Entry'
            })
            
            return True
        
        return False

    def place_clean_sell(self, price, time, change, reason):
        """Clean sell: 100% complete exits"""
        
        # Sell 100% - COMPLETE EXIT (vs 95% in v4.2)
        asset_to_sell = self.asset_balance * self.sell_percentage
        gross_amount = asset_to_sell * price
        fee = gross_amount * self.taker_fee
        net_amount = gross_amount - fee
        
        self.php_balance += net_amount
        self.asset_balance -= asset_to_sell  # Will be 0 after this
        self.total_fees_paid += fee
        self.total_trades += 1
        
        # ALWAYS clear position completely with 100% sell
        self.position = None
        self.update_daily_trades(time)
        
        # Calculate P/L
        profit_loss = 0
        if self.entry_price:
            profit_loss = (price - self.entry_price) / self.entry_price * 100
        
        asset_name = self.symbol.replace('PHP', '')
        print(f"💵 CLEAN SELL: {asset_to_sell:.6f} {asset_name} at ₱{price:.2f} = ₱{net_amount:.2f}")
        print(f"   📊 P/L: {profit_loss:+.1f}% | {reason} | COMPLETE EXIT | Fee: ₱{fee:.2f}")
        
        self.trade_history.append({
            'timestamp': time,
            'side': 'SELL',
            'price': price,
            'amount': gross_amount,
            'quantity': asset_to_sell,
            'fee': fee,
            'profit_loss': profit_loss,
            'price_change': change,
            'reason': reason
        })
        
        # ALWAYS clear entry data with clean exits
        self.entry_price = None
        self.entry_time = None
        return True

    def calculate_portfolio_value(self, current_price):
        """Calculate total value"""
        return self.php_balance + (self.asset_balance * current_price)

    def run_clean_exit_backtest(self, days=60):
        """Run clean exit backtest"""
        print(f"\n🚀 Starting CLEAN EXIT Backtest v4.3")
        print("✨ 100% clean exits - no tiny remainder trades!")
        print("=" * 70)
        
        data, actual_days = self.get_historical_data(days)
        if not data:
            return None
        
        print(f"\n📊 CLEAN EXIT v4.3 approach:")
        asset_name = self.symbol.replace('PHP', '')
        print(f"🎯 Asset: {asset_name}")
        print(f"📈 Buy: {self.buy_threshold*100:.1f}% momentum with ₱{self.trade_amount} trades")
        print(f"📉 Sell: {self.sell_threshold*100:.1f}% decline OR 2% profit ({self.sell_percentage*100:.0f}% COMPLETE EXIT)")
        print(f"⏰ Hold: {self.min_hold_minutes} minutes minimum")
        print(f"🔄 Frequency: {self.max_trades_per_day} trades/day max")
        print(f"✨ Clean: No position fragmentation!")
        print()
        
        start_price = data[0]['close']
        last_price = start_price
        trades_shown = 0
        
        # Process each hour
        for candle in data[1:]:
            current_price = candle['close']
            current_time = candle['timestamp']
            
            # Run clean exit strategy
            trades_before = len(self.trade_history)
            self.clean_exit_strategy(current_price, current_time, last_price)
            
            # Show trades
            if len(self.trade_history) > trades_before and trades_shown < 25:
                trades_shown += 1
            elif trades_shown == 25:
                print("... (showing first 25 trades)")
                trades_shown += 1
            
            last_price = current_price
        
        # Calculate results
        final_price = data[-1]['close']
        final_portfolio_value = self.calculate_portfolio_value(final_price)
        total_return = final_portfolio_value - self.initial_balance
        return_percentage = (total_return / self.initial_balance) * 100
        
        # Annualized return
        if actual_days > 0:
            daily_return = (final_portfolio_value / self.initial_balance) ** (1/actual_days) - 1
            annualized_return = ((1 + daily_return) ** 365 - 1) * 100
        else:
            annualized_return = 0
        
        # Buy and hold
        initial_asset_if_bought = (self.initial_balance - (self.initial_balance * self.maker_fee)) / start_price
        buy_hold_value = initial_asset_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Metrics
        buy_trades = [t for t in self.trade_history if t['side'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['side'] == 'SELL']
        profitable_sells = [t for t in sell_trades if t.get('profit_loss', 0) > 0]
        
        win_rate = (len(profitable_sells) / max(1, len(sell_trades))) * 100
        
        if profitable_sells:
            avg_win = sum(t.get('profit_loss', 0) for t in profitable_sells) / len(profitable_sells)
        else:
            avg_win = 0
        
        losing_sells = [t for t in sell_trades if t.get('profit_loss', 0) <= 0]
        if losing_sells:
            avg_loss = sum(t.get('profit_loss', 0) for t in losing_sells) / len(losing_sells)
        else:
            avg_loss = 0
        
        # Display results
        print(f"\n🎯 CLEAN EXIT v4.3 BACKTEST RESULTS")
        print("=" * 70)
        print(f"📅 Period: {data[0]['timestamp'].strftime('%Y-%m-%d')} to {data[-1]['timestamp'].strftime('%Y-%m-%d')}")
        print(f"📊 Actual days tested: {actual_days}")
        print(f"💹 Start price: ₱{start_price:.2f}")
        print(f"💹 End price: ₱{final_price:.2f}")
        print(f"📈 {asset_name} price change: {((final_price - start_price) / start_price) * 100:+.2f}%")
        print()
        print("🚀 CLEAN EXIT STRATEGY PERFORMANCE:")
        print(f"💰 Starting value: ₱{self.initial_balance:.2f}")
        print(f"💰 Final value: ₱{final_portfolio_value:.2f}")
        print(f"📈 Total return: ₱{total_return:.2f} ({return_percentage:+.2f}%)")
        print(f"📊 Annualized return: {annualized_return:+.1f}%")
        print(f"💸 Total fees paid: ₱{self.total_fees_paid:.2f}")
        print(f"🔄 Total trades: {self.total_trades} ({len(buy_trades)} buys, {len(sell_trades)} sells)")
        print(f"📈 Trades per day: {self.total_trades / max(actual_days, 1):.1f}")
        print(f"🎯 Win rate: {win_rate:.1f}% ({len(profitable_sells)}/{len(sell_trades)})")
        print(f"📊 Avg win: {avg_win:+.1f}% | Avg loss: {avg_loss:+.1f}%")
        print()
        print(f"💰 Final balances:")
        print(f"   PHP: ₱{self.php_balance:.2f}")
        print(f"   {asset_name}: {self.asset_balance:.6f} (worth ₱{self.asset_balance * final_price:.2f})")
        print()
        print("📊 BUY & HOLD COMPARISON:")
        print(f"💰 Buy & hold value: ₱{buy_hold_value:.2f}")
        print(f"📈 Buy & hold return: ₱{buy_hold_return:.2f} ({buy_hold_percentage:+.2f}%)")
        print()
        
        if return_percentage > buy_hold_percentage:
            outperformance = return_percentage - buy_hold_percentage
            print(f"🏆 CLEAN EXIT strategy OUTPERFORMED buy & hold by {outperformance:+.2f}%!")
        else:
            underperformance = buy_hold_percentage - return_percentage
            print(f"📉 Strategy underperformed buy & hold by {underperformance:.2f}%")
        
        print(f"\n📊 CLEAN EXIT v4.3 ADVANTAGES:")
        fee_percentage = (self.total_fees_paid / self.initial_balance) * 100
        print(f"   ✨ COMPLETE exits: {self.sell_percentage*100:.0f}% (no remainders)")
        print(f"   💰 Optimal trade size: ₱{self.trade_amount}")
        print(f"   💸 Cleaner fees: {fee_percentage:.2f}% of capital")
        print(f"   🎯 No tiny remainder trades")
        print(f"   ⚡ Pure buy/sell pairs")
        
        if self.total_trades > 0:
            avg_return_per_trade = total_return / self.total_trades
            print(f"   💰 Average return per trade: ₱{avg_return_per_trade:.2f}")
        
        # Trade efficiency analysis
        if len(buy_trades) > 0 and len(sell_trades) > 0:
            trade_efficiency = len(sell_trades) / len(buy_trades)
            print(f"   📊 Trade efficiency: {trade_efficiency:.2f} (sells per buy)")
        
        print(f"\n🎯 v4.3 vs v4.2 COMPARISON:")
        print(f"   v4.2: ₱200 trades + 95% sells = messy remainders")
        print(f"   v4.3: ₱200 trades + 100% sells = CLEAN PERFECTION!")
        
        print("=" * 70)
        
        return {
            'total_return': total_return,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            'total_trades': self.total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_fees': self.total_fees_paid,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'actual_days': actual_days,
            'trades_per_day': self.total_trades / max(actual_days, 1),
            'outperformed_buy_hold': return_percentage > buy_hold_percentage,
            'outperformance': return_percentage - buy_hold_percentage
        }

def main():
    print("🚀 CLEAN EXIT Trading Bot v4.3")
    print("✨ Ultimate optimization: 100% clean exits!")
    print("=" * 65)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    print("Select asset to test:")
    print("1. SOLPHP (High volatility - clean exit test)")
    print("2. XRPPHP (Medium volatility - efficiency test)")
    print("   (100% exits - no more tiny remainder trades!)")
    
    choice = input("Enter choice (1-2): ").strip()
    symbol_map = {'1': 'SOLPHP', '2': 'XRPPHP'}
    symbol = symbol_map.get(choice, 'SOLPHP')
    
    print(f"\nTesting CLEAN EXIT v4.3 {symbol}...")
    print("✨ Expected improvements:")
    print("   🎯 Fewer total trades (no remainders)")
    print("   💸 Lower fee burden")
    print("   📊 Cleaner win/loss tracking")
    print("   ⚡ Perfect trade pairs (1 buy = 1 sell)")
    
    backtester = CleanExitBacktester(symbol)
    results = backtester.run_clean_exit_backtest(60)
    
    if results:
        print(f"\n💡 CLEAN EXIT v4.3 CONCLUSION:")
        
        print(f"\n📊 EVOLUTION RESULTS:")
        asset_short = symbol.replace('PHP', '')
        if symbol == 'SOLPHP':
            print(f"   v4.2 SOL: 143 trades, -1.76%, 3.27% fees")
        else:  # XRP
            print(f"   v4.2 XRP: TBD")
        print(f"   v4.3 {asset_short}: {results['total_trades']} trades, {results['return_percentage']:+.2f}%, {(results['total_fees']/2000)*100:.2f}% fees")
        
        # Check if cleaner
        trade_efficiency = results['sell_trades'] / max(results['buy_trades'], 1)
        if abs(trade_efficiency - 1.0) < 0.1:
            print("✨ PERFECT: Clean 1:1 buy/sell ratio achieved!")
        elif trade_efficiency < 1.2:
            print("✅ EXCELLENT: Very clean trade ratios!")
        
        # Check fee improvement
        fee_pct = (results['total_fees'] / 2000) * 100
        if fee_pct < 3.0:
            print(f"💸 EXCELLENT: Fees reduced to {fee_pct:.2f}%!")
        elif fee_pct < 3.5:
            print(f"✅ GOOD: Fees at {fee_pct:.2f}%")
        
        if results['return_percentage'] > -1.5:
            print("🎯 EXCELLENT: Best returns yet!")
        elif results['return_percentage'] > -2.0:
            print("✅ GOOD: Solid improvement!")
        
        if results['win_rate'] > 40:
            print(f"🏆 EXCELLENT win rate: {results['win_rate']:.1f}%!")
        elif results['win_rate'] > 35:
            print(f"✅ GOOD win rate: {results['win_rate']:.1f}%")
        
        print(f"\n🎯 v4.3 CLEAN EXIT ACHIEVEMENTS:")
        print(f"   ✨ Perfect exits: {backtester.sell_percentage*100:.0f}% (no fragmentation)")
        print(f"   💰 Optimal sizing: ₱200 trades")
        print(f"   🎯 Clean strategy: No remainder noise")
        print(f"   ⚡ Pure efficiency: 1 buy = 1 sell")
        
        if results['outperformed_buy_hold']:
            print(f"\n🏆 Strategy beats buy & hold by {results['outperformance']:+.2f}%")
        
        if results['total_trades'] >= 60 and fee_pct < 3.0:
            print(f"\n🎉 v4.3 CLEAN EXIT SUCCESS!")
            print(f"   📊 Optimal activity: {results['trades_per_day']:.1f} trades/day")
            print(f"   💰 Perfect sizing: ₱200 trades")
            print(f"   ✨ Ultimate cleanliness: 100% exits")
            print(f"   🎯 Fee efficiency: {fee_pct:.2f}% of capital")
            
            print(f"\n🚀 READY FOR FINAL VALIDATION:")
            print(f"   ✅ Test v4.3 on both SOL and XRP")
            print(f"   ✅ Compare all version results")
            print(f"   ✅ Begin live paper trading")
            print(f"   ✅ Deploy optimal strategy")
        else:
            print(f"\n📊 Great progress with v4.3 clean approach!")

if __name__ == "__main__":
    main()