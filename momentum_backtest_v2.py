import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class EnhancedMomentumBacktester:
    def __init__(self, symbol='XRPPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.initial_balance = 2000
        
        # ENHANCED PARAMETERS - Asset-Specific Optimization
        self.asset_configs = {
            'XRPPHP': {
                'buy_threshold': 0.012,    # 1.2% (slightly higher than 1%)
                'sell_threshold': 0.015,   # 1.5% (wider sell for fewer whipsaws)
                'base_amount': 120,        # Slightly larger trades
                'min_hold_hours': 2,       # Hold positions for min 2 hours
                'trend_window': 24,        # 24-hour trend filter
                'max_trades_per_day': 3    # Max 3 trades per day
            },
            'SOLPHP': {
                'buy_threshold': 0.018,    # 1.8% (much higher for SOL)
                'sell_threshold': 0.022,   # 2.2% (wider spread)
                'base_amount': 150,        # Larger trades to offset fees
                'min_hold_hours': 4,       # Hold longer (SOL is more volatile)
                'trend_window': 12,        # Shorter trend window for faster moves
                'max_trades_per_day': 2    # Fewer trades to reduce churn
            },
            'BTCPHP': {
                'buy_threshold': 0.015,    # 1.5% (moderate)
                'sell_threshold': 0.018,   # 1.8%
                'base_amount': 100,        # Standard amount
                'min_hold_hours': 3,       # Medium hold time
                'trend_window': 48,        # Longer trend for BTC
                'max_trades_per_day': 2    # Conservative frequency
            }
        }
        
        # Get config for current asset
        if symbol in self.asset_configs:
            config = self.asset_configs[symbol]
            self.buy_threshold = config['buy_threshold']
            self.sell_threshold = config['sell_threshold']
            self.base_amount = config['base_amount']
            self.min_hold_hours = config['min_hold_hours']
            self.trend_window = config['trend_window']
            self.max_trades_per_day = config['max_trades_per_day']
        else:
            # Default config for unknown assets
            self.buy_threshold = 0.015
            self.sell_threshold = 0.018
            self.base_amount = 100
            self.min_hold_hours = 3
            self.trend_window = 24
            self.max_trades_per_day = 2
        
        # Trading fees and settings
        self.taker_fee = 0.0030
        self.balance_usage = 0.9
        self.check_interval_minutes = 15
        
        # Enhanced state tracking
        self.php_balance = self.initial_balance
        self.asset_balance = 0
        self.last_price = None
        self.position = None
        self.entry_price = None
        self.entry_time = None
        self.trade_history = []
        self.portfolio_history = []
        self.total_trades = 0
        self.total_fees_paid = 0
        self.daily_trades = {}  # Track trades per day
        self.price_history = []  # For trend calculation
        
        asset_name = symbol.replace('PHP', '')
        print(f"🚀 Enhanced Momentum Bot for {symbol}")
        print(f"📊 Optimized parameters for {asset_name}:")
        print(f"   📈 Buy threshold: {self.buy_threshold*100:.1f}%")
        print(f"   📉 Sell threshold: {self.sell_threshold*100:.1f}%")
        print(f"   💰 Trade size: ₱{self.base_amount}")
        print(f"   ⏰ Min hold time: {self.min_hold_hours} hours")
        print(f"   📊 Trend window: {self.trend_window} hours")
        print(f"   🔄 Max trades/day: {self.max_trades_per_day}")

    def get_historical_data(self, days=30):
        """Get historical data for enhanced backtesting"""
        print(f"\n📊 Fetching {days} days of hourly data for {self.symbol}...")
        
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
            
            processed_data = []
            for kline in klines:
                processed_data.append({
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            if processed_data:
                actual_days = (processed_data[-1]['timestamp'] - processed_data[0]['timestamp']).days
                print(f"✅ Got {len(processed_data)} hourly data points covering {actual_days} days")
                return processed_data, actual_days
            else:
                return None, 0
            
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
            return None, 0

    def calculate_trend(self, prices, window=None):
        """Calculate trend direction using moving average slope"""
        if window is None:
            window = self.trend_window
            
        if len(prices) < window:
            return 0  # Neutral if not enough data
        
        recent_prices = prices[-window:]
        
        # Simple trend: compare first half vs second half of window
        first_half = sum(recent_prices[:window//2]) / (window//2)
        second_half = sum(recent_prices[window//2:]) / (window - window//2)
        
        trend_strength = (second_half - first_half) / first_half
        return trend_strength  # Positive = uptrend, Negative = downtrend

    def can_trade_today(self, current_time):
        """Check if we can still trade today (daily limit)"""
        date_key = current_time.strftime('%Y-%m-%d')
        trades_today = self.daily_trades.get(date_key, 0)
        return trades_today < self.max_trades_per_day

    def can_sell_position(self, current_time):
        """Check if we can sell (minimum hold time)"""
        if self.entry_time is None:
            return True
        
        hold_duration = current_time - self.entry_time
        min_hold_delta = timedelta(hours=self.min_hold_hours)
        return hold_duration >= min_hold_delta

    def update_daily_trades(self, current_time):
        """Update daily trade counter"""
        date_key = current_time.strftime('%Y-%m-%d')
        self.daily_trades[date_key] = self.daily_trades.get(date_key, 0) + 1

    def create_15min_checks_from_hourly(self, hourly_data):
        """Create 15-minute check points from hourly data"""
        check_points = []
        
        for candle in hourly_data:
            # Store price in history for trend calculation
            self.price_history.append(candle['close'])
            
            # Create 4 check points per hour (every 15 minutes)
            for i in range(4):
                minutes_offset = i * 15
                check_time = candle['timestamp'] + timedelta(minutes=minutes_offset)
                
                # Simple interpolation within the hour
                progress = i / 4
                interpolated_price = (
                    candle['open'] * (1 - progress) + 
                    candle['close'] * progress
                )
                
                # Add realistic variation using high/low
                price_range = candle['high'] - candle['low']
                if price_range > 0:
                    import random
                    variation_factor = (random.random() - 0.5) * 0.3
                    variation = variation_factor * price_range
                    interpolated_price += variation
                    interpolated_price = max(candle['low'], 
                                           min(candle['high'], interpolated_price))
                
                check_points.append({
                    'timestamp': check_time,
                    'price': interpolated_price
                })
        
        return check_points

    def enhanced_momentum_strategy(self, current_price, check_time):
        """Enhanced momentum strategy with fine-tuning"""
        if self.last_price is None:
            self.last_price = current_price
            return
        
        # Calculate price change
        price_change = (current_price - self.last_price) / self.last_price
        
        # Calculate trend
        trend = self.calculate_trend(self.price_history)
        
        # Enhanced buy logic
        if (price_change > self.buy_threshold and 
            trend > -0.02 and  # Don't buy in strong downtrend
            self.php_balance > self.base_amount * 1.2 and
            self.can_trade_today(check_time) and
            self.position is None):
            
            self.place_enhanced_buy_order(current_price, check_time, trend)
            
        # Enhanced sell logic  
        elif (price_change < -self.sell_threshold and
              self.asset_balance > 0.001 and
              self.can_sell_position(check_time) and
              self.can_trade_today(check_time)):
            
            self.place_enhanced_sell_order(current_price, check_time, trend)
        
        # Trend-based emergency exit (strong downtrend)
        elif (trend < -0.05 and  # Very strong downtrend
              self.asset_balance > 0.001 and
              self.can_sell_position(check_time)):
            
            print(f"🚨 TREND EXIT: Strong downtrend detected ({trend*100:.1f}%)")
            self.place_enhanced_sell_order(current_price, check_time, trend, reason="Trend Exit")
        
        self.last_price = current_price

    def place_enhanced_buy_order(self, price, check_time, trend):
        """Place enhanced buy order with dynamic sizing"""
        # Dynamic position sizing based on trend strength
        if trend > 0.02:  # Strong uptrend
            amount_to_spend = self.base_amount * 1.2  # 20% larger
        elif trend > 0:  # Mild uptrend
            amount_to_spend = self.base_amount
        else:  # Neutral/weak downtrend
            amount_to_spend = self.base_amount * 0.8  # 20% smaller
        
        # Ensure we don't exceed available balance
        available_php = self.php_balance * self.balance_usage
        amount_to_spend = min(amount_to_spend, available_php)
        
        if amount_to_spend < 25:
            return False
        
        # Calculate fees and execute
        fee = amount_to_spend * self.taker_fee
        total_cost = amount_to_spend + fee
        
        if self.php_balance >= total_cost:
            asset_quantity = amount_to_spend / price
            self.php_balance -= total_cost
            self.asset_balance += asset_quantity
            self.total_fees_paid += fee
            self.total_trades += 1
            self.position = 'long'
            self.entry_price = price
            self.entry_time = check_time
            self.update_daily_trades(check_time)
            
            asset_name = self.symbol.replace('PHP', '')
            print(f"💰 ENHANCED BUY: ₱{amount_to_spend:.2f} {asset_name} at ₱{price:.2f} (Trend: {trend*100:+.1f}%, Fee: ₱{fee:.2f})")
            
            self.trade_history.append({
                'timestamp': check_time,
                'side': 'BUY',
                'price': price,
                'amount': amount_to_spend,
                'quantity': asset_quantity,
                'fee': fee,
                'trend': trend,
                'reason': 'Enhanced Momentum'
            })
            
            return True
        
        return False

    def place_enhanced_sell_order(self, price, check_time, trend, reason="Enhanced Momentum"):
        """Place enhanced sell order"""
        # Sell 90% of position (keep some for potential recovery)
        asset_to_sell = self.asset_balance * 0.9
        gross_amount = asset_to_sell * price
        fee = gross_amount * self.taker_fee
        net_amount = gross_amount - fee
        
        # Execute sell
        self.php_balance += net_amount
        self.asset_balance -= asset_to_sell
        self.total_fees_paid += fee
        self.total_trades += 1
        self.position = None
        self.update_daily_trades(check_time)
        
        # Calculate P/L
        profit_loss = 0
        if self.entry_price:
            profit_loss = (price - self.entry_price) / self.entry_price * 100
        
        asset_name = self.symbol.replace('PHP', '')
        print(f"💵 ENHANCED SELL: {asset_to_sell:.6f} {asset_name} at ₱{price:.2f} = ₱{net_amount:.2f} (P/L: {profit_loss:+.1f}%, Fee: ₱{fee:.2f})")
        
        self.trade_history.append({
            'timestamp': check_time,
            'side': 'SELL',
            'price': price,
            'amount': gross_amount,
            'quantity': asset_to_sell,
            'fee': fee,
            'profit_loss': profit_loss,
            'trend': trend,
            'reason': reason
        })
        
        self.entry_price = None
        self.entry_time = None
        return True

    def calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.php_balance + (self.asset_balance * current_price)

    def run_enhanced_backtest(self, days=30):
        """Run enhanced momentum backtest"""
        print(f"\n🚀 Starting Enhanced Momentum Backtest")
        print("=" * 60)
        
        data, actual_days = self.get_historical_data(days)
        if not data:
            return None
        
        # Create 15-minute check points
        check_points = self.create_15min_checks_from_hourly(data)
        
        print(f"\n📊 Enhanced backtest parameters:")
        asset_name = self.symbol.replace('PHP', '')
        print(f"🎯 Asset: {asset_name}")
        print(f"📈 Buy threshold: {self.buy_threshold*100:.1f}%")
        print(f"📉 Sell threshold: {self.sell_threshold*100:.1f}%")
        print(f"⏰ Min hold: {self.min_hold_hours}h")
        print(f"📊 Trend filter: {self.trend_window}h window")
        print()
        
        start_price = check_points[0]['price']
        trades_shown = 0
        
        # Process each 15-minute check
        for check_point in check_points:
            current_price = check_point['price']
            check_time = check_point['timestamp']
            
            # Execute enhanced strategy
            trades_before = len(self.trade_history)
            self.enhanced_momentum_strategy(current_price, check_time)
            
            # Show first few trades
            if len(self.trade_history) > trades_before and trades_shown < 8:
                trades_shown += 1
            elif trades_shown == 8:
                print("... (showing first 8 trades only)")
                trades_shown += 1
            
            # Track portfolio
            portfolio_value = self.calculate_portfolio_value(current_price)
            self.portfolio_history.append({
                'timestamp': check_time,
                'price': current_price,
                'portfolio_value': portfolio_value
            })
        
        # Calculate results
        final_price = check_points[-1]['price']
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
        initial_asset_if_bought = (self.initial_balance - (self.initial_balance * self.taker_fee)) / start_price
        buy_hold_value = initial_asset_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Win rate calculation
        profitable_sells = [t for t in self.trade_history if t['side'] == 'SELL' and t.get('profit_loss', 0) > 0]
        total_sells = [t for t in self.trade_history if t['side'] == 'SELL']
        win_rate = (len(profitable_sells) / max(1, len(total_sells))) * 100
        
        # Display results
        print(f"\n🎯 ENHANCED MOMENTUM BACKTEST RESULTS")
        print("=" * 60)
        print(f"📅 Period: {check_points[0]['timestamp'].strftime('%Y-%m-%d')} to {check_points[-1]['timestamp'].strftime('%Y-%m-%d')}")
        print(f"📊 Actual days tested: {actual_days}")
        print(f"💹 Start price: ₱{start_price:.2f}")
        print(f"💹 End price: ₱{final_price:.2f}")
        print(f"📈 {asset_name} price change: {((final_price - start_price) / start_price) * 100:+.2f}%")
        print()
        print("🚀 ENHANCED STRATEGY PERFORMANCE:")
        print(f"💰 Starting value: ₱{self.initial_balance:.2f}")
        print(f"💰 Final value: ₱{final_portfolio_value:.2f}")
        print(f"📈 Total return: ₱{total_return:.2f} ({return_percentage:+.2f}%)")
        print(f"📊 Annualized return: {annualized_return:+.1f}%")
        print(f"💸 Total fees paid: ₱{self.total_fees_paid:.2f}")
        print(f"🔄 Total trades: {self.total_trades}")
        print(f"📈 Trades per day: {self.total_trades / max(actual_days, 1):.1f}")
        print(f"🎯 Win rate: {win_rate:.1f}%")
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
            print(f"🏆 Enhanced strategy OUTPERFORMED buy & hold by {outperformance:+.2f}%!")
        else:
            underperformance = buy_hold_percentage - return_percentage
            print(f"📉 Enhanced strategy underperformed buy & hold by {underperformance:.2f}%")
        
        # Enhanced analysis
        print(f"\n📊 ENHANCEMENT ANALYSIS:")
        fee_percentage = (self.total_fees_paid / self.initial_balance) * 100
        print(f"   💸 Fees as % of capital: {fee_percentage:.2f}%")
        print(f"   🎯 Optimized thresholds: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%")
        print(f"   ⏰ Min hold time: {self.min_hold_hours} hours")
        print(f"   📊 Trend filter: {self.trend_window} hour window")
        print(f"   🔄 Daily trade limit: {self.max_trades_per_day}")
        
        if self.total_trades > 0:
            avg_return_per_trade = total_return / self.total_trades
            print(f"   💰 Average return per trade: ₱{avg_return_per_trade:.2f}")
        
        print("=" * 60)
        
        return {
            'total_return': total_return,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            'total_trades': self.total_trades,
            'total_fees': self.total_fees_paid,
            'win_rate': win_rate,
            'actual_days': actual_days,
            'outperformed_buy_hold': return_percentage > buy_hold_percentage
        }

def main():
    print("🚀 Enhanced Momentum Trading Bot Backtester")
    print("⚡ Fine-tuned parameters for each asset")
    print("=" * 50)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    print("Select asset to test:")
    print("1. XRPPHP (Conservative: 1.2%/1.5% thresholds)")
    print("2. SOLPHP (Aggressive: 1.8%/2.2% thresholds)")
    print("3. BTCPHP (Moderate: 1.5%/1.8% thresholds)")
    
    choice = input("Enter choice (1-3): ").strip()
    symbol_map = {'1': 'XRPPHP', '2': 'SOLPHP', '3': 'BTCPHP'}
    symbol = symbol_map.get(choice, 'XRPPHP')
    
    try:
        days_input = input("How many days to test? (7-90): ").strip()
        days = int(days_input) if days_input else 30
        days = max(7, min(days, 90))
    except ValueError:
        days = 30
    
    print(f"\nTesting enhanced {symbol} momentum for {days} days...")
    
    backtester = EnhancedMomentumBacktester(symbol)
    results = backtester.run_enhanced_backtest(days)
    
    if results:
        print(f"\n💡 ENHANCED STRATEGY CONCLUSION:")
        
        if results['return_percentage'] > 5:
            print("🚀 Excellent performance with enhanced parameters!")
        elif results['return_percentage'] > 2:
            print("✅ Good performance improvement!")
        elif results['return_percentage'] > 0:
            print("🟡 Modest positive returns with enhancements")
        else:
            print("⚠️ Still negative - may need further tuning")
        
        if results['win_rate'] > 50:
            print(f"🎯 Excellent win rate: {results['win_rate']:.1f}%!")
        elif results['win_rate'] > 30:
            print(f"✅ Improved win rate: {results['win_rate']:.1f}%")
        
        print(f"\n📊 Enhanced features working:")
        print(f"   • Asset-specific thresholds")
        print(f"   • Trend filtering")
        print(f"   • Minimum hold times")
        print(f"   • Daily trade limits")
        print(f"   • Dynamic position sizing")

if __name__ == "__main__":
    main()