import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI
import pandas as pd

load_dotenv(override=True)

class TakeProfitOptimizer:
    def __init__(self, symbol='SOLPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.initial_balance = 2000
        
        # Fixed parameters for consistency
        self.buy_threshold = 0.006     # 0.6%
        self.sell_threshold = 0.010    # 1.0%
        self.trade_amount = 200        # ₱200 trades
        self.sell_percentage = 1.00    # 100% exits
        self.min_hold_minutes = 30     # 30 minutes
        self.max_trades_per_day = 10   # High frequency
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        print(f"🔬 TAKE PROFIT OPTIMIZER for {symbol}")
        print(f"📊 Testing multiple take profit levels systematically")
        print(f"🎯 Fixed parameters: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%, Trade ₱{self.trade_amount}")

    def reset_state(self):
        """Reset backtester state for new run"""
        self.php_balance = self.initial_balance
        self.asset_balance = 0
        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.trade_history = []
        self.daily_trades = {}
        self.total_trades = 0
        self.total_fees_paid = 0

    def get_historical_data(self, days=60):
        """Get historical data - cached for efficiency"""
        if hasattr(self, '_cached_data'):
            return self._cached_data
        
        print(f"\n📊 Fetching {days} days of historical data...")
        
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
                self._cached_data = (data, actual_days)
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

    def strategy_with_take_profit(self, current_price, current_time, last_price, take_profit_pct):
        """Run strategy with specific take profit level"""
        
        # Calculate price change
        price_change = (current_price - last_price) / last_price
        
        # BUY CONDITIONS
        if (price_change > self.buy_threshold and           
            self.php_balance > self.trade_amount * 1.1 and  
            self.can_trade_today(current_time) and          
            self.position is None):                          
            
            self.place_buy(current_price, current_time, price_change)
        
        # SELL CONDITIONS - Momentum down
        elif (price_change < -self.sell_threshold and       
              self.asset_balance > 0.001 and                
              self.can_sell_position(current_time) and      
              self.can_trade_today(current_time)):           
            
            self.place_sell(current_price, current_time, price_change, "Momentum Down")
        
        # SELL CONDITIONS - Take profit
        elif (self.entry_price and 
              current_price > self.entry_price and
              self.can_sell_position(current_time)):
            
            profit_pct = (current_price - self.entry_price) / self.entry_price
            if profit_pct > take_profit_pct:
                self.place_sell(current_price, current_time, price_change, "Profit Taking")

    def place_buy(self, price, time, change):
        """Place buy order"""
        amount_to_spend = min(self.trade_amount, self.php_balance * 0.9)
        
        if amount_to_spend < 20:
            return False
        
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

    def place_sell(self, price, time, change, reason):
        """Place sell order"""
        asset_to_sell = self.asset_balance * self.sell_percentage
        gross_amount = asset_to_sell * price
        fee = gross_amount * self.taker_fee
        net_amount = gross_amount - fee
        
        self.php_balance += net_amount
        self.asset_balance -= asset_to_sell
        self.total_fees_paid += fee
        self.total_trades += 1
        
        self.position = None
        self.update_daily_trades(time)
        
        # Calculate P/L
        profit_loss = 0
        if self.entry_price:
            profit_loss = (price - self.entry_price) / self.entry_price * 100
        
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
        
        self.entry_price = None
        self.entry_time = None
        return True

    def calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.php_balance + (self.asset_balance * current_price)

    def run_single_backtest(self, take_profit_pct, days=60, verbose=False):
        """Run backtest with specific take profit level"""
        self.reset_state()
        
        data, actual_days = self.get_historical_data(days)
        if not data:
            return None
        
        if verbose:
            print(f"\n🔬 Testing take profit: {take_profit_pct*100:.1f}%")
        
        start_price = data[0]['close']
        last_price = start_price
        
        # Process each hour
        for candle in data[1:]:
            current_price = candle['close']
            current_time = candle['timestamp']
            
            self.strategy_with_take_profit(current_price, current_time, last_price, take_profit_pct)
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
        
        # Buy and hold comparison
        initial_asset_if_bought = (self.initial_balance - (self.initial_balance * self.maker_fee)) / start_price
        buy_hold_value = initial_asset_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Trade analysis
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
        
        # Exit reason analysis
        profit_taking_trades = [t for t in sell_trades if t.get('reason') == 'Profit Taking']
        momentum_down_trades = [t for t in sell_trades if t.get('reason') == 'Momentum Down']
        
        return {
            'take_profit_pct': take_profit_pct * 100,
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
            'outperformance': return_percentage - buy_hold_percentage,
            'profit_taking_trades': len(profit_taking_trades),
            'momentum_down_trades': len(momentum_down_trades),
            'profit_taking_pct': len(profit_taking_trades)/max(len(sell_trades),1)*100,
            'sharpe_ratio': self.calculate_sharpe_ratio(return_percentage, actual_days),
            'max_drawdown': self.calculate_max_drawdown(),
            'fee_percentage': (self.total_fees_paid / self.initial_balance) * 100
        }

    def calculate_sharpe_ratio(self, annual_return, days):
        """Calculate approximate Sharpe ratio"""
        if days < 30:
            return 0
        # Simplified Sharpe using 2% risk-free rate
        risk_free_rate = 2.0
        return (annual_return - risk_free_rate) / max(10, abs(annual_return))  # Simplified volatility

    def calculate_max_drawdown(self):
        """Calculate maximum drawdown during the period"""
        if not self.trade_history:
            return 0
        
        peak_value = self.initial_balance
        max_drawdown = 0
        current_value = self.initial_balance
        
        for trade in self.trade_history:
            if trade['side'] == 'SELL':
                current_value = self.php_balance + (self.asset_balance * trade['price'])
                peak_value = max(peak_value, current_value)
                drawdown = (peak_value - current_value) / peak_value * 100
                max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown

    def run_comprehensive_optimization(self, days=60):
        """Run comprehensive take profit optimization"""
        print(f"\n🚀 COMPREHENSIVE TAKE PROFIT OPTIMIZATION")
        print(f"🎯 Symbol: {self.symbol}")
        print(f"📅 Testing period: {days} days")
        print("=" * 80)
        
        # Define take profit levels to test
        take_profit_levels = [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.5, 4.0, 5.0]
        
        print(f"🔬 Testing {len(take_profit_levels)} take profit levels:")
        print(f"   {', '.join([f'{tp:.1f}%' for tp in take_profit_levels])}")
        print()
        
        results = []
        
        for i, tp_pct in enumerate(take_profit_levels):
            tp_decimal = tp_pct / 100
            print(f"📊 [{i+1:2d}/{len(take_profit_levels)}] Testing {tp_pct:.1f}% take profit...", end=" ")
            
            result = self.run_single_backtest(tp_decimal, days, verbose=False)
            if result:
                results.append(result)
                print(f"Return: {result['return_percentage']:+.1f}%, Trades: {result['total_trades']}, Win: {result['win_rate']:.0f}%")
            else:
                print("❌ Failed")
        
        if not results:
            print("❌ No successful backtests!")
            return None
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)
        
        # Find optimal strategies
        best_return = df.loc[df['return_percentage'].idxmax()]
        best_sharpe = df.loc[df['sharpe_ratio'].idxmax()]
        best_win_rate = df.loc[df['win_rate'].idxmax()]
        most_profit_taking = df.loc[df['profit_taking_pct'].idxmax()]
        
        # Display comprehensive results
        self.display_optimization_results(df, best_return, best_sharpe, best_win_rate, most_profit_taking)
        
        return df

    def display_optimization_results(self, df, best_return, best_sharpe, best_win_rate, most_profit_taking):
        """Display comprehensive optimization results"""
        
        print(f"\n🏆 OPTIMIZATION RESULTS SUMMARY")
        print("=" * 80)
        
        # Overall statistics
        print(f"📊 OVERALL STATISTICS:")
        print(f"   📈 Best return: {best_return['return_percentage']:+.2f}% (@ {best_return['take_profit_pct']:.1f}% TP)")
        print(f"   🎯 Best Sharpe: {best_sharpe['sharpe_ratio']:.2f} (@ {best_sharpe['take_profit_pct']:.1f}% TP)")
        print(f"   🏆 Best win rate: {best_win_rate['win_rate']:.1f}% (@ {best_win_rate['take_profit_pct']:.1f}% TP)")
        print(f"   💰 Most profit taking: {most_profit_taking['profit_taking_pct']:.1f}% (@ {most_profit_taking['take_profit_pct']:.1f}% TP)")
        print()
        
        # Detailed table
        print(f"📋 DETAILED RESULTS TABLE:")
        print("-" * 80)
        print(f"{'TP%':<4} {'Return%':<8} {'Win%':<6} {'Trades':<7} {'PT%':<6} {'Fees%':<6} {'Sharpe':<7} {'vs B&H':<7}")
        print("-" * 80)
        
        for _, row in df.iterrows():
            tp = f"{row['take_profit_pct']:.1f}"
            ret = f"{row['return_percentage']:+.1f}"
            win = f"{row['win_rate']:.0f}"
            trades = f"{row['total_trades']:.0f}"
            pt = f"{row['profit_taking_pct']:.0f}"
            fees = f"{row['fee_percentage']:.1f}"
            sharpe = f"{row['sharpe_ratio']:.2f}"
            vs_bh = f"{row['outperformance']:+.1f}"
            
            # Highlight best performers
            highlight = ""
            if row['take_profit_pct'] == best_return['take_profit_pct']:
                highlight = " 🏆"
            elif row['take_profit_pct'] == best_sharpe['take_profit_pct']:
                highlight = " ⭐"
            elif row['take_profit_pct'] == best_win_rate['take_profit_pct']:
                highlight = " 🎯"
            
            print(f"{tp:<4} {ret:<8} {win:<6} {trades:<7} {pt:<6} {fees:<6} {sharpe:<7} {vs_bh:<7}{highlight}")
        
        print("-" * 80)
        print("🏆 = Best Return | ⭐ = Best Sharpe | 🎯 = Best Win Rate")
        print()
        
        # Analysis and recommendations
        print(f"📈 TAKE PROFIT ANALYSIS:")
        
        # Find optimal range
        profitable_strategies = df[df['return_percentage'] > 0]
        if len(profitable_strategies) > 0:
            min_profitable_tp = profitable_strategies['take_profit_pct'].min()
            max_profitable_tp = profitable_strategies['take_profit_pct'].max()
            avg_profitable_return = profitable_strategies['return_percentage'].mean()
            
            print(f"   ✅ Profitable range: {min_profitable_tp:.1f}% - {max_profitable_tp:.1f}% TP")
            print(f"   📊 Average profitable return: {avg_profitable_return:+.1f}%")
        else:
            print(f"   ❌ No profitable take profit levels found!")
        
        # Trend analysis
        low_tp = df[df['take_profit_pct'] <= 1.5]['return_percentage'].mean()
        mid_tp = df[(df['take_profit_pct'] > 1.5) & (df['take_profit_pct'] <= 2.5)]['return_percentage'].mean()
        high_tp = df[df['take_profit_pct'] > 2.5]['return_percentage'].mean()
        
        print(f"   📊 Low TP (≤1.5%): {low_tp:+.1f}% avg return")
        print(f"   📊 Mid TP (1.5-2.5%): {mid_tp:+.1f}% avg return")
        print(f"   📊 High TP (>2.5%): {high_tp:+.1f}% avg return")
        print()
        
        # Recommendations
        print(f"💡 OPTIMIZATION RECOMMENDATIONS:")
        
        if best_return['return_percentage'] > 0:
            print(f"   🎯 For maximum returns: Use {best_return['take_profit_pct']:.1f}% take profit")
            print(f"      Expected: {best_return['return_percentage']:+.1f}% return, {best_return['win_rate']:.0f}% win rate")
        
        if best_sharpe['sharpe_ratio'] > 0:
            print(f"   ⚖️ For best risk-adjusted returns: Use {best_sharpe['take_profit_pct']:.1f}% take profit")
            print(f"      Expected: {best_sharpe['return_percentage']:+.1f}% return, Sharpe {best_sharpe['sharpe_ratio']:.2f}")
        
        conservative_options = df[(df['win_rate'] >= 40) & (df['return_percentage'] > -2)]
        if len(conservative_options) > 0:
            best_conservative = conservative_options.loc[conservative_options['return_percentage'].idxmax()]
            print(f"   🛡️ For conservative approach: Use {best_conservative['take_profit_pct']:.1f}% take profit")
            print(f"      Expected: {best_conservative['return_percentage']:+.1f}% return, {best_conservative['win_rate']:.0f}% win rate")
        
        print()
        print(f"🎯 FINAL RECOMMENDATION:")
        
        # Simple scoring system
        df['score'] = (
            df['return_percentage'] * 0.4 +  # 40% weight on returns
            df['win_rate'] * 0.3 +           # 30% weight on win rate
            df['sharpe_ratio'] * 10 * 0.2 +  # 20% weight on Sharpe
            df['profit_taking_pct'] * 0.1    # 10% weight on profit taking frequency
        )
        
        best_overall = df.loc[df['score'].idxmax()]
        print(f"   🏆 OPTIMAL: {best_overall['take_profit_pct']:.1f}% take profit")
        print(f"   📊 Expected performance:")
        print(f"      Return: {best_overall['return_percentage']:+.1f}%")
        print(f"      Win rate: {best_overall['win_rate']:.0f}%")
        print(f"      Trades per day: {best_overall['trades_per_day']:.1f}")
        print(f"      Profit taking exits: {best_overall['profit_taking_pct']:.0f}%")
        print(f"      vs Buy & Hold: {best_overall['outperformance']:+.1f}%")

def main():
    print("🔬 TAKE PROFIT COMPREHENSIVE OPTIMIZER")
    print("🎯 Testing multiple take profit levels systematically")
    print("=" * 65)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    print("Select asset to optimize:")
    print("1. SOLPHP (High volatility)")
    print("2. XRPPHP (Medium volatility)")
    
    choice = input("Enter choice (1-2): ").strip()
    symbol_map = {'1': 'SOLPHP', '2': 'XRPPHP'}
    symbol = symbol_map.get(choice, 'SOLPHP')
    
    print("Select optimization depth:")
    print("1. Quick test (30 days)")
    print("2. Standard test (60 days)")
    print("3. Deep test (90 days)")
    
    days_choice = input("Enter choice (1-3): ").strip()
    days_map = {'1': 30, '2': 60, '3': 90}
    days = days_map.get(days_choice, 60)
    
    print(f"\n🚀 Starting comprehensive optimization...")
    print(f"🎯 Symbol: {symbol}")
    print(f"📅 Period: {days} days")
    print(f"🔬 Testing 14 different take profit levels")
    
    optimizer = TakeProfitOptimizer(symbol)
    results = optimizer.run_comprehensive_optimization(days)
    
    if results is not None:
        print(f"\n✅ OPTIMIZATION COMPLETE!")
        print(f"🎯 Use the recommended take profit level in your live trading")
        print(f"📊 Save these results for strategy validation")
    else:
        print(f"\n❌ Optimization failed!")

if __name__ == "__main__":
    main()