import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class MomentumBacktester:
    def __init__(self, symbol='XRPPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        
        # Momentum bot parameters (optimized for XRP volatility)
        self.base_amount = 100  # ₱100 per trade (conservative sizing)
        self.price_threshold = 0.01  # 1% price change threshold (reduced from 2%)
        self.check_interval_minutes = 15  # Check every 15 minutes (increased from 5)
        self.balance_usage = 0.9  # Use 90% of available balance
        
        # Trading fees (market orders = taker fees)
        self.taker_fee = 0.0030  # 0.30% taker fee for market orders
        
        # Starting capital
        self.initial_balance = 2000  # ₱2000 starting balance
        
        # Backtest state
        self.php_balance = self.initial_balance
        self.asset_balance = 0  # Holds the crypto asset (XRP, SOL, BTC, etc.)
        self.last_price = None
        self.position = None  # 'long' or None
        self.entry_price = None
        self.trade_history = []
        self.portfolio_history = []
        self.total_trades = 0
        self.total_fees_paid = 0
        
        print(f"🚀 Momentum Bot Backtest initialized for {self.symbol}")
        print(f"💰 Starting balance: ₱{self.initial_balance}")
        print(f"💰 Base trading amount: ₱{self.base_amount} (conservative sizing)")
        asset_name = self.symbol.replace('PHP', '')
        print(f"📊 Price threshold: {self.price_threshold*100}% (optimized for {asset_name})")
        print(f"⏱️  Check interval: {self.check_interval_minutes} minutes (optimized)")
        print(f"💸 Taker fee: {self.taker_fee*100}%")

    def get_historical_data(self, days=30):
        """Get hourly historical data for realistic momentum testing"""
        print(f"\n📊 Fetching {days} days of HOURLY data for {self.symbol}...")
        
        # Use hourly data directly for more realistic momentum testing
        if days <= 30:
            interval = '1h'
            limit = days * 24  # 24 hours per day
        else:
            interval = '1h'
            limit = min(days * 24, 1000)  # Cap at API limit
        
        try:
            klines = self.api._make_request(
                'GET', 
                '/openapi/quote/v1/klines',
                {
                    'symbol': self.symbol,
                    'interval': interval,
                    'limit': limit
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
                print(f"From: {processed_data[0]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                print(f"To: {processed_data[-1]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                return processed_data, interval, actual_days
            else:
                print("❌ No data received")
                return None, None, 0
            
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
            return None, None, 0

    def create_15min_checks_from_hourly(self, hourly_data):
        """Create 15-minute check points from hourly data"""
        check_points = []
        
        for candle in hourly_data:
            # For each hour, create 4 check points (every 15 minutes)
            for i in range(4):
                minutes_offset = i * 15
                check_time = candle['timestamp'] + timedelta(minutes=minutes_offset)
                
                # Simple interpolation within the hour
                progress = i / 4
                interpolated_price = (
                    candle['open'] * (1 - progress) + 
                    candle['close'] * progress
                )
                
                # Add some realistic variation within the hour using high/low
                price_range = candle['high'] - candle['low']
                if price_range > 0:
                    import random
                    # Add variation but keep within high/low bounds
                    variation_factor = (random.random() - 0.5) * 0.3  # 30% of range
                    variation = variation_factor * price_range
                    interpolated_price += variation
                    
                    # Clamp to high/low bounds
                    interpolated_price = max(candle['low'], 
                                           min(candle['high'], interpolated_price))
                
                check_points.append({
                    'timestamp': check_time,
                    'price': interpolated_price
                })
        
        return check_points

    def calculate_fees(self, amount_php):
        """Calculate taker fees for market orders"""
        return amount_php * self.taker_fee

    def place_buy_order(self, price, check_time):
        """Simulate buy order (momentum up)"""
        # Use min of available PHP and base_amount
        available_php = self.php_balance * self.balance_usage
        amount_to_spend = min(available_php, self.base_amount)
        
        if amount_to_spend < 25:  # Minimum trade size for ₱100 base amount
            return False
        
        # Calculate fees
        fee = self.calculate_fees(amount_to_spend)
        total_cost = amount_to_spend + fee
        
        if self.php_balance >= total_cost:
            # Execute buy
            asset_quantity = amount_to_spend / price
            self.php_balance -= total_cost
            self.asset_balance += asset_quantity
            self.total_fees_paid += fee
            self.total_trades += 1
            self.position = 'long'
            self.entry_price = price
            
            trade = {
                'timestamp': check_time,
                'side': 'BUY',
                'price': price,
                'amount_php': amount_to_spend,
                'asset_quantity': asset_quantity,
                'fee': fee,
                'reason': 'Momentum UP'
            }
            
            # Get asset name from symbol (e.g., SOLPHP -> SOL, XRPPHP -> XRP)
            asset_name = self.symbol.replace('PHP', '')
            
            self.trade_history.append(trade)
            print(f"💰 BUY: ₱{amount_to_spend:.2f} worth of {asset_name} at ₱{price:.2f} (Fee: ₱{fee:.2f})")
            return True
        
        return False

    def place_sell_order(self, price, check_time):
        """Simulate sell order (momentum down)"""
        if self.asset_balance <= 0.00001:  # No crypto to sell
            return False
        
        # Sell 90% of available crypto
        asset_to_sell = self.asset_balance * self.balance_usage
        gross_php = asset_to_sell * price
        fee = self.calculate_fees(gross_php)
        net_php = gross_php - fee
        
        # Execute sell
        self.php_balance += net_php
        self.asset_balance -= asset_to_sell
        self.total_fees_paid += fee
        self.total_trades += 1
        self.position = None
        
        # Calculate profit/loss
        profit_loss = 0
        if self.entry_price:
            profit_loss = (price - self.entry_price) / self.entry_price * 100
        
        # Get asset name from symbol
        asset_name = self.symbol.replace('PHP', '')
        
        trade = {
            'timestamp': check_time,
            'side': 'SELL',
            'price': price,
            'amount_php': gross_php,
            'asset_quantity': asset_to_sell,
            'net_php': net_php,
            'fee': fee,
            'profit_loss_pct': profit_loss,
            'reason': 'Momentum DOWN'
        }
        
        self.trade_history.append(trade)
        print(f"💵 SELL: {asset_to_sell:.6f} {asset_name} at ₱{price:.2f} = ₱{net_php:.2f} (Fee: ₱{fee:.2f}, P/L: {profit_loss:+.1f}%)")
        return True

    def momentum_strategy_check(self, current_price, check_time):
        """Execute momentum strategy logic (matching simple_bot.py)"""
        if self.last_price is None:
            self.last_price = current_price
            return
        
        # Calculate price change percentage
        price_change = (current_price - self.last_price) / self.last_price
        
        # Trading logic (with ₱100 per trade and 1% threshold)
        if price_change > self.price_threshold and self.php_balance > 120:  # Need at least ₱120 for fees
            # Price went up significantly, buy crypto (momentum strategy)
            self.place_buy_order(current_price, check_time)
            
        elif price_change < -self.price_threshold and self.asset_balance > 0.001:
            # Price went down significantly, sell crypto (momentum strategy) 
            self.place_sell_order(current_price, check_time)
        
        self.last_price = current_price

    def calculate_portfolio_value(self, asset_price):
        """Calculate total portfolio value"""
        return self.php_balance + (self.asset_balance * asset_price)

    def run_backtest(self, days=30):
        """Run momentum trading backtest"""
        print("\n🚀 Starting Momentum Trading Bot Backtest")
        print("=" * 60)
        
        # Get historical data
        data, interval, actual_days = self.get_historical_data(days)
        if not data:
            return None
        
        # Create 15-minute check points from hourly data
        print(f"📊 Creating 15-minute check points from hourly data...")
        check_points = self.create_15min_checks_from_hourly(data)
        print(f"✅ Generated {len(check_points)} check points (every 15 minutes)")
        
        print(f"\n📊 Testing OPTIMIZED momentum strategy:")
        print(f"💰 Starting balance: ₱{self.initial_balance}")
        print(f"📈 Buy trigger: Price up >{self.price_threshold*100}% (reduced from 2%)")
        print(f"📉 Sell trigger: Price down >{self.price_threshold*100}% (reduced from 2%)")
        print(f"⏰ Check interval: Every {self.check_interval_minutes} minutes (increased from 5)")
        print(f"💰 Trade size: ₱{self.base_amount} (reduced from ₱250)")
        print()
        
        start_price = check_points[0]['price']
        trades_shown = 0
        max_trades_to_show = 10
        
        # Process each 15-minute check
        for i, check_point in enumerate(check_points):
            current_price = check_point['price']
            check_time = check_point['timestamp']
            
            # Execute momentum strategy
            trades_before = len(self.trade_history)
            self.momentum_strategy_check(current_price, check_time)
            
            # Show progress for first few trades
            if len(self.trade_history) > trades_before and trades_shown < max_trades_to_show:
                trades_shown += 1
            elif trades_shown == max_trades_to_show:
                print("... (showing first 10 trades only)")
                trades_shown += 1
            
            # Track portfolio value
            portfolio_value = self.calculate_portfolio_value(current_price)
            self.portfolio_history.append({
                'timestamp': check_time,
                'price': current_price,
                'portfolio_value': portfolio_value,
                'php_balance': self.php_balance,
                'asset_balance': self.asset_balance
            })
        
        # Calculate final results
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
        initial_asset_if_bought = (self.initial_balance - self.calculate_fees(self.initial_balance)) / start_price
        buy_hold_value = initial_asset_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Calculate winning trades
        profitable_trades = [t for t in self.trade_history if t['side'] == 'SELL' and t.get('profit_loss_pct', 0) > 0]
        win_rate = (len(profitable_trades) / max(1, len([t for t in self.trade_history if t['side'] == 'SELL']))) * 100
        
        # Display results
        print(f"\n🎯 MOMENTUM TRADING BACKTEST RESULTS")
        print("=" * 60)
        print(f"📅 Period: {check_points[0]['timestamp'].strftime('%Y-%m-%d')} to {check_points[-1]['timestamp'].strftime('%Y-%m-%d')}")
        print(f"📊 Actual days tested: {actual_days}")
        print(f"📊 Check points processed: {len(check_points)} (every 15 minutes)")
        print(f"💹 Start price: ₱{start_price:.2f}")
        print(f"💹 End price: ₱{final_price:.2f}")
        asset_name = self.symbol.replace('PHP', '')
        print(f"📈 {asset_name} price change: {((final_price - start_price) / start_price) * 100:+.2f}%")
        print()
        print("🚀 OPTIMIZED MOMENTUM STRATEGY PERFORMANCE:")
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
            print(f"🏆 OPTIMIZED Momentum strategy OUTPERFORMED buy & hold by {outperformance:+.2f}%!")
        else:
            underperformance = buy_hold_percentage - return_percentage
            print(f"📉 Momentum strategy underperformed buy & hold by {underperformance:.2f}%")
        
        # Performance analysis
        print(f"\n📊 OPTIMIZED MOMENTUM STRATEGY ANALYSIS:")
        fee_percentage = (self.total_fees_paid / self.initial_balance) * 100
        print(f"   💸 Fees as % of capital: {fee_percentage:.2f}%")
        
        if self.total_trades > 0:
            avg_return_per_trade = total_return / self.total_trades
            print(f"   💰 Average return per trade: ₱{avg_return_per_trade:.2f}")
            
        print(f"   📊 Price threshold used: {self.price_threshold*100}% (reduced from 2%)")
        print(f"   ⏱️  Check frequency: Every {self.check_interval_minutes} minutes (increased from 5)")
        print(f"   💰 Trade size: ₱{self.base_amount} (conservative sizing)")
        
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
    """Main function"""
    print("🚀 Momentum Trading Bot Backtester v1.0")
    print("⚡ OPTIMIZED: 1% threshold, 15-min intervals, ₱100 trades")
    print("=" * 60)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ COINS_API_KEY not found in .env file")
        return
    
    symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')  # Default to XRP like your other bots
    print(f"Testing symbol: {symbol}")
    
    try:
        days_input = input("How many days of history to test? (7-90): ").strip()
        days = int(days_input) if days_input else 30
        days = max(7, min(days, 90))  # Limit to 7-90 days for momentum testing
    except ValueError:
        days = 30
    
    print(f"Testing {days} days of momentum trading...")
    print()
    
    # Run momentum backtest
    backtester = MomentumBacktester(symbol)
    results = backtester.run_backtest(days)
    
    if results:
        print(f"\n💡 OPTIMIZED MOMENTUM STRATEGY CONCLUSION:")
        
        if results['return_percentage'] > 5:
            print("🚀 Excellent momentum trading results with optimizations!")
        elif results['return_percentage'] > 2:
            print("✅ Good momentum trading performance after optimization!")
        elif results['return_percentage'] > 0:
            print("🟡 Modest positive returns from optimized momentum strategy")
        else:
            asset_name = symbol.replace('PHP', '')
            print(f"⚠️  Still negative returns - momentum may not suit {asset_name}")
        
        if results['total_trades'] > 0:
            print(f"🎯 Optimizations worked: {results['total_trades']} trades generated!")
            if results['win_rate'] > 60:
                print(f"🎯 Great win rate: {results['win_rate']:.1f}%")
            elif results['win_rate'] > 50:
                print(f"✅ Decent win rate: {results['win_rate']:.1f}%")
        else:
            print("❌ Still no trades - try even lower threshold (0.5%)?")
        
        if results['outperformed_buy_hold']:
            print("💪 Optimized momentum trading beat buy-and-hold!")
        else:
            print("📈 Buy-and-hold was still better - consider grid trading instead")
        
        asset_name = symbol.replace('PHP', '')
        print(f"\n📊 Optimized for {asset_name}: 1% threshold, 15-min checks, ₱100 trades")

if __name__ == "__main__":
    main()