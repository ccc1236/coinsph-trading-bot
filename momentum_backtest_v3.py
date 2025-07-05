import os
import time
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class ProfitableEnhancedBacktester:
    def __init__(self, symbol='SOLPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.initial_balance = 2000
        
        # PROFITABLE ENHANCEMENT PARAMETERS
        self.asset_configs = {
            'XRPPHP': {
                'base_buy_threshold': 0.008,    # Reduced from 1.2% to 0.8%
                'base_sell_threshold': 0.012,   # Reduced from 1.5% to 1.2%
                'base_amount': 120,
                'min_hold_hours': 1.5,          # Reduced hold time
                'short_trend_window': 6,        # 6-hour short trend
                'medium_trend_window': 24,      # 24-hour medium trend
                'long_trend_window': 72,        # 72-hour long trend
                'max_trades_per_day': 4,        # Increased frequency
                'volume_threshold': 1.2         # 20% above average volume
            },
            'SOLPHP': {
                'base_buy_threshold': 0.012,    # Reduced from 1.8% to 1.2%
                'base_sell_threshold': 0.016,   # Reduced from 2.2% to 1.6%
                'base_amount': 150,
                'min_hold_hours': 2,            # Reduced from 4 to 2 hours
                'short_trend_window': 4,        # 4-hour short trend
                'medium_trend_window': 12,      # 12-hour medium trend
                'long_trend_window': 48,        # 48-hour long trend
                'max_trades_per_day': 3,        # Increased frequency
                'volume_threshold': 1.3         # 30% above average volume
            },
            'BTCPHP': {
                'base_buy_threshold': 0.010,    # Reduced from 1.5% to 1.0%
                'base_sell_threshold': 0.014,   # Reduced from 1.8% to 1.4%
                'base_amount': 100,
                'min_hold_hours': 2,            # Reduced hold time
                'short_trend_window': 8,        # 8-hour short trend
                'medium_trend_window': 48,      # 48-hour medium trend
                'long_trend_window': 96,        # 96-hour long trend
                'max_trades_per_day': 3,        # Increased frequency
                'volume_threshold': 1.15        # 15% above average volume
            }
        }
        
        # Load configuration
        if symbol in self.asset_configs:
            config = self.asset_configs[symbol]
            self.base_buy_threshold = config['base_buy_threshold']
            self.base_sell_threshold = config['base_sell_threshold']
            self.base_amount = config['base_amount']
            self.min_hold_hours = config['min_hold_hours']
            self.short_trend_window = config['short_trend_window']
            self.medium_trend_window = config['medium_trend_window']
            self.long_trend_window = config['long_trend_window']
            self.max_trades_per_day = config['max_trades_per_day']
            self.volume_threshold = config['volume_threshold']
        else:
            # Default enhanced config
            self.base_buy_threshold = 0.010
            self.base_sell_threshold = 0.014
            self.base_amount = 100
            self.min_hold_hours = 2
            self.short_trend_window = 6
            self.medium_trend_window = 24
            self.long_trend_window = 72
            self.max_trades_per_day = 3
            self.volume_threshold = 1.2
        
        # Enhanced fee structure (VIP 0 level)
        self.maker_fee = 0.0025  # 0.25% maker fee
        self.taker_fee = 0.0030  # 0.30% taker fee
        self.balance_usage = 0.95  # Use 95% of balance (more aggressive)
        
        # State tracking
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
        self.daily_trades = {}
        
        # Multi-timeframe data
        self.price_history = []
        self.volume_history = []
        self.volatility_window = 24  # 24-hour volatility window
        
        asset_name = symbol.replace('PHP', '')
        print(f"🚀 PROFITABLE Enhanced Momentum Bot v3 for {symbol}")
        print(f"💡 Multi-timeframe + Volume + Dynamic Thresholds")
        print(f"📊 Optimized parameters for {asset_name}:")
        print(f"   📈 Base buy threshold: {self.base_buy_threshold*100:.1f}% (dynamic)")
        print(f"   📉 Base sell threshold: {self.base_sell_threshold*100:.1f}% (dynamic)")
        print(f"   💰 Trade size: ₱{self.base_amount}")
        print(f"   ⏰ Min hold time: {self.min_hold_hours} hours")
        print(f"   📊 Multi-timeframe: {self.short_trend_window}h/{self.medium_trend_window}h/{self.long_trend_window}h")
        print(f"   🔄 Max trades/day: {self.max_trades_per_day}")
        print(f"   📈 Volume filter: {(self.volume_threshold-1)*100:.0f}% above average")
        print(f"   💸 Fees: {self.maker_fee*100:.2f}% maker / {self.taker_fee*100:.2f}% taker")

    def get_historical_data(self, days=30):
        """Get historical data with volume"""
        print(f"\n📊 Fetching {days} days of enhanced data for {self.symbol}...")
        
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
                total_volume = sum(candle['volume'] for candle in processed_data)
                print(f"✅ Got {len(processed_data)} hourly candles covering {actual_days} days")
                print(f"📊 Total volume: {total_volume:,.0f} {self.symbol.replace('PHP', '')}")
                return processed_data, actual_days
            else:
                return None, 0
            
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
            return None, 0

    def calculate_volatility(self, prices, window=24):
        """Calculate price volatility (standard deviation)"""
        if len(prices) < window:
            return 0
        
        recent_prices = prices[-window:]
        if len(recent_prices) < 2:
            return 0
        
        # Calculate returns
        returns = []
        for i in range(1, len(recent_prices)):
            returns.append((recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1])
        
        if not returns:
            return 0
        
        # Standard deviation of returns
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance)

    def calculate_multi_timeframe_trend(self, prices):
        """Calculate trend across multiple timeframes"""
        trends = {}
        
        # Short-term trend (momentum)
        if len(prices) >= self.short_trend_window:
            recent = prices[-self.short_trend_window:]
            mid = len(recent) // 2
            first_half = sum(recent[:mid]) / mid
            second_half = sum(recent[mid:]) / (len(recent) - mid)
            trends['short'] = (second_half - first_half) / first_half
        else:
            trends['short'] = 0
        
        # Medium-term trend (primary)
        if len(prices) >= self.medium_trend_window:
            recent = prices[-self.medium_trend_window:]
            mid = len(recent) // 2
            first_half = sum(recent[:mid]) / mid
            second_half = sum(recent[mid:]) / (len(recent) - mid)
            trends['medium'] = (second_half - first_half) / first_half
        else:
            trends['medium'] = 0
        
        # Long-term trend (filter)
        if len(prices) >= self.long_trend_window:
            recent = prices[-self.long_trend_window:]
            mid = len(recent) // 2
            first_half = sum(recent[:mid]) / mid
            second_half = sum(recent[mid:]) / (len(recent) - mid)
            trends['long'] = (second_half - first_half) / first_half
        else:
            trends['long'] = 0
        
        return trends

    def calculate_volume_signal(self, volumes):
        """Calculate volume-based signal strength"""
        if len(volumes) < 20:
            return 1.0  # Neutral if not enough data
        
        recent_volume = volumes[-1]
        avg_volume = sum(volumes[-20:]) / 20  # 20-hour average
        
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        return volume_ratio

    def get_dynamic_thresholds(self, volatility, trends, volume_ratio):
        """Calculate dynamic buy/sell thresholds based on market conditions"""
        
        # Base thresholds
        buy_threshold = self.base_buy_threshold
        sell_threshold = self.base_sell_threshold
        
        # Volatility adjustment (higher volatility = higher thresholds)
        volatility_multiplier = 1 + (volatility * 10)  # Scale volatility impact
        volatility_multiplier = min(volatility_multiplier, 2.0)  # Cap at 2x
        
        # Trend adjustment
        medium_trend = trends.get('medium', 0)
        long_trend = trends.get('long', 0)
        
        # In strong uptrends, lower buy threshold (easier to buy)
        # In strong downtrends, raise sell threshold (quicker to sell)
        if medium_trend > 0.02:  # Strong uptrend
            buy_threshold *= 0.8  # 20% easier to buy
        elif medium_trend < -0.02:  # Strong downtrend
            sell_threshold *= 0.8  # 20% easier to sell
        
        # Long-term filter
        if long_trend < -0.05:  # Very strong long-term downtrend
            buy_threshold *= 1.5  # Much harder to buy
            sell_threshold *= 0.7  # Much easier to sell
        
        # Volume adjustment (high volume = more confident signals)
        if volume_ratio > self.volume_threshold:
            buy_threshold *= 0.9   # 10% easier with high volume
            sell_threshold *= 0.9  # 10% easier with high volume
        
        # Apply volatility
        buy_threshold *= volatility_multiplier
        sell_threshold *= volatility_multiplier
        
        return buy_threshold, sell_threshold

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
        min_hold_delta = timedelta(hours=self.min_hold_hours)
        return hold_duration >= min_hold_delta

    def update_daily_trades(self, current_time):
        """Update daily trade counter"""
        date_key = current_time.strftime('%Y-%m-%d')
        self.daily_trades[date_key] = self.daily_trades.get(date_key, 0) + 1

    def create_enhanced_checks_from_hourly(self, hourly_data):
        """Create 15-minute check points with enhanced data"""
        check_points = []
        
        for candle in hourly_data:
            # Store data for calculations
            self.price_history.append(candle['close'])
            self.volume_history.append(candle['volume'])
            
            # Create 4 check points per hour (every 15 minutes)
            for i in range(4):
                minutes_offset = i * 15
                check_time = candle['timestamp'] + timedelta(minutes=minutes_offset)
                
                # Price interpolation
                progress = i / 4
                interpolated_price = (
                    candle['open'] * (1 - progress) + 
                    candle['close'] * progress
                )
                
                # Add realistic variation
                price_range = candle['high'] - candle['low']
                if price_range > 0:
                    import random
                    variation_factor = (random.random() - 0.5) * 0.3
                    variation = variation_factor * price_range
                    interpolated_price += variation
                    interpolated_price = max(candle['low'], 
                                           min(candle['high'], interpolated_price))
                
                # Volume stays constant for the hour
                interpolated_volume = candle['volume']
                
                check_points.append({
                    'timestamp': check_time,
                    'price': interpolated_price,
                    'volume': interpolated_volume
                })
        
        return check_points

    def enhanced_profitable_strategy(self, current_price, current_volume, check_time):
        """Enhanced profitable momentum strategy"""
        if self.last_price is None:
            self.last_price = current_price
            return
        
        # Calculate price change
        price_change = (current_price - self.last_price) / self.last_price
        
        # Calculate multi-timeframe trends
        trends = self.calculate_multi_timeframe_trend(self.price_history)
        
        # Calculate volatility
        volatility = self.calculate_volatility(self.price_history, self.volatility_window)
        
        # Calculate volume signal
        volume_ratio = self.calculate_volume_signal(self.volume_history)
        
        # Get dynamic thresholds
        buy_threshold, sell_threshold = self.get_dynamic_thresholds(volatility, trends, volume_ratio)
        
        # Enhanced buy logic
        buy_conditions = [
            price_change > buy_threshold,                           # Price momentum
            trends['medium'] > -0.03,                              # Not in strong downtrend
            trends['long'] > -0.08,                                # Long-term not too bearish
            volume_ratio >= self.volume_threshold * 0.8,           # Decent volume (80% of threshold)
            self.php_balance > self.base_amount * 1.1,             # Sufficient balance
            self.can_trade_today(check_time),                      # Daily limit check
            self.position is None                                   # No existing position
        ]
        
        if all(buy_conditions):
            self.place_enhanced_buy_order(current_price, check_time, trends, volatility, volume_ratio, buy_threshold)
        
        # Enhanced sell logic
        sell_conditions_momentum = [
            price_change < -sell_threshold,                         # Negative momentum
            self.asset_balance > 0.001,                            # Have position
            self.can_sell_position(check_time),                    # Hold time met
            self.can_trade_today(check_time)                       # Daily limit check
        ]
        
        # Emergency sell conditions (ignore hold time)
        emergency_sell_conditions = [
            trends['short'] < -0.05,                               # Strong short-term reversal
            trends['medium'] < -0.08,                              # Strong medium-term downtrend
            self.asset_balance > 0.001                             # Have position
        ]
        
        # Profit-taking conditions (partial sells)
        if self.entry_price and current_price > self.entry_price:
            profit_pct = (current_price - self.entry_price) / self.entry_price
            profit_take_conditions = [
                profit_pct > 0.04,                                 # 4% profit
                trends['short'] < 0.01,                            # Momentum weakening
                self.can_sell_position(check_time)                 # Hold time met
            ]
            
            if all(profit_take_conditions):
                self.place_enhanced_sell_order(current_price, check_time, trends, "Profit Taking", partial=True)
                
        elif all(sell_conditions_momentum):
            self.place_enhanced_sell_order(current_price, check_time, trends, "Momentum Reversal")
            
        elif all(emergency_sell_conditions):
            print(f"🚨 EMERGENCY SELL: Strong reversal detected")
            self.place_enhanced_sell_order(current_price, check_time, trends, "Emergency Exit")
        
        self.last_price = current_price

    def place_enhanced_buy_order(self, price, check_time, trends, volatility, volume_ratio, threshold_used):
        """Place enhanced buy order with intelligent sizing"""
        
        # Dynamic position sizing based on signal strength
        signal_strength = 1.0
        
        # Increase size for strong signals
        if trends['short'] > 0.02 and trends['medium'] > 0.01:
            signal_strength *= 1.3  # Strong multi-timeframe alignment
        
        if volume_ratio > self.volume_threshold * 1.5:
            signal_strength *= 1.2  # Very high volume
        
        # Decrease size for weak signals
        if volatility > 0.05:  # High volatility
            signal_strength *= 0.8
        
        # Calculate amount to spend
        base_amount = self.base_amount * signal_strength
        available_php = self.php_balance * self.balance_usage
        amount_to_spend = min(base_amount, available_php)
        
        if amount_to_spend < 25:
            return False
        
        # Use maker fee (assume limit order)
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
            self.entry_time = check_time
            self.update_daily_trades(check_time)
            
            asset_name = self.symbol.replace('PHP', '')
            print(f"💰 ENHANCED BUY: ₱{amount_to_spend:.2f} {asset_name} at ₱{price:.2f}")
            print(f"   📊 Signals: ST:{trends['short']*100:+.1f}% MT:{trends['medium']*100:+.1f}% LT:{trends['long']*100:+.1f}%")
            print(f"   📈 Vol:{volume_ratio:.1f}x Volatility:{volatility*100:.1f}% Threshold:{threshold_used*100:.1f}% Fee:₱{fee:.2f}")
            
            self.trade_history.append({
                'timestamp': check_time,
                'side': 'BUY',
                'price': price,
                'amount': amount_to_spend,
                'quantity': asset_quantity,
                'fee': fee,
                'trends': trends.copy(),
                'volume_ratio': volume_ratio,
                'volatility': volatility,
                'signal_strength': signal_strength,
                'threshold_used': threshold_used,
                'reason': 'Enhanced Multi-timeframe'
            })
            
            return True
        
        return False

    def place_enhanced_sell_order(self, price, check_time, trends, reason="Enhanced Momentum", partial=False):
        """Place enhanced sell order"""
        
        # Determine sell percentage
        if partial and reason == "Profit Taking":
            sell_percentage = 0.5  # Sell 50% on profit taking
        else:
            sell_percentage = 0.95  # Sell 95% on normal/emergency sells
        
        asset_to_sell = self.asset_balance * sell_percentage
        gross_amount = asset_to_sell * price
        
        # Use taker fee for market sells (faster execution)
        fee = gross_amount * self.taker_fee
        net_amount = gross_amount - fee
        
        # Execute sell
        self.php_balance += net_amount
        self.asset_balance -= asset_to_sell
        self.total_fees_paid += fee
        self.total_trades += 1
        
        if not partial:
            self.position = None
        
        self.update_daily_trades(check_time)
        
        # Calculate P/L
        profit_loss = 0
        if self.entry_price:
            profit_loss = (price - self.entry_price) / self.entry_price * 100
        
        asset_name = self.symbol.replace('PHP', '')
        sell_type = "PARTIAL" if partial else "FULL"
        print(f"💵 {sell_type} SELL: {asset_to_sell:.6f} {asset_name} at ₱{price:.2f} = ₱{net_amount:.2f}")
        print(f"   📊 P/L: {profit_loss:+.1f}% | {reason} | Fee: ₱{fee:.2f}")
        
        self.trade_history.append({
            'timestamp': check_time,
            'side': 'SELL',
            'price': price,
            'amount': gross_amount,
            'quantity': asset_to_sell,
            'fee': fee,
            'profit_loss': profit_loss,
            'trends': trends.copy(),
            'reason': reason,
            'partial': partial
        })
        
        if not partial:
            self.entry_price = None
            self.entry_time = None
        
        return True

    def calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.php_balance + (self.asset_balance * current_price)

    def run_profitable_backtest(self, days=30):
        """Run enhanced profitable backtest"""
        print(f"\n🚀 Starting PROFITABLE Enhanced Backtest v3")
        print("=" * 65)
        
        data, actual_days = self.get_historical_data(days)
        if not data:
            return None
        
        # Create enhanced check points
        check_points = self.create_enhanced_checks_from_hourly(data)
        
        print(f"\n📊 PROFITABLE enhancement features:")
        asset_name = self.symbol.replace('PHP', '')
        print(f"🎯 Asset: {asset_name}")
        print(f"📈 Dynamic thresholds: {self.base_buy_threshold*100:.1f}%/{self.base_sell_threshold*100:.1f}% base")
        print(f"⏰ Reduced hold time: {self.min_hold_hours} hours")
        print(f"📊 Multi-timeframe: {self.short_trend_window}h/{self.medium_trend_window}h/{self.long_trend_window}h")
        print(f"📈 Volume filtering: {(self.volume_threshold-1)*100:.0f}% above average")
        print(f"💸 Optimized fees: {self.maker_fee*100:.2f}% maker")
        print()
        
        start_price = check_points[0]['price']
        trades_shown = 0
        
        # Process each enhanced check
        for check_point in check_points:
            current_price = check_point['price']
            current_volume = check_point['volume']
            check_time = check_point['timestamp']
            
            # Execute enhanced profitable strategy
            trades_before = len(self.trade_history)
            self.enhanced_profitable_strategy(current_price, current_volume, check_time)
            
            # Show first several trades
            if len(self.trade_history) > trades_before and trades_shown < 12:
                trades_shown += 1
            elif trades_shown == 12:
                print("... (showing first 12 trades only)")
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
        initial_asset_if_bought = (self.initial_balance - (self.initial_balance * self.maker_fee)) / start_price
        buy_hold_value = initial_asset_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Enhanced metrics
        buy_trades = [t for t in self.trade_history if t['side'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['side'] == 'SELL']
        profitable_sells = [t for t in sell_trades if t.get('profit_loss', 0) > 0]
        
        win_rate = (len(profitable_sells) / max(1, len(sell_trades))) * 100
        
        # Calculate average profit per winning/losing trade
        if profitable_sells:
            avg_win = sum(t.get('profit_loss', 0) for t in profitable_sells) / len(profitable_sells)
        else:
            avg_win = 0
        
        losing_sells = [t for t in sell_trades if t.get('profit_loss', 0) <= 0]
        if losing_sells:
            avg_loss = sum(t.get('profit_loss', 0) for t in losing_sells) / len(losing_sells)
        else:
            avg_loss = 0
        
        # Display enhanced results
        print(f"\n🎯 PROFITABLE ENHANCED BACKTEST RESULTS v3")
        print("=" * 65)
        print(f"📅 Period: {check_points[0]['timestamp'].strftime('%Y-%m-%d')} to {check_points[-1]['timestamp'].strftime('%Y-%m-%d')}")
        print(f"📊 Actual days tested: {actual_days}")
        print(f"💹 Start price: ₱{start_price:.2f}")
        print(f"💹 End price: ₱{final_price:.2f}")
        print(f"📈 {asset_name} price change: {((final_price - start_price) / start_price) * 100:+.2f}%")
        print()
        print("🚀 ENHANCED PROFITABLE STRATEGY PERFORMANCE:")
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
            print(f"🏆 PROFITABLE strategy OUTPERFORMED buy & hold by {outperformance:+.2f}%!")
        else:
            underperformance = buy_hold_percentage - return_percentage
            print(f"📉 Strategy underperformed buy & hold by {underperformance:.2f}%")
        
        # Enhanced analysis
        print(f"\n📊 PROFITABILITY ENHANCEMENT ANALYSIS:")
        fee_percentage = (self.total_fees_paid / self.initial_balance) * 100
        print(f"   💸 Fees as % of capital: {fee_percentage:.2f}%")
        print(f"   🎯 Dynamic thresholds: Base {self.base_buy_threshold*100:.1f}%/{self.base_sell_threshold*100:.1f}%")
        print(f"   ⏰ Reduced hold time: {self.min_hold_hours} hours")
        print(f"   📊 Multi-timeframe analysis: {self.short_trend_window}h/{self.medium_trend_window}h/{self.long_trend_window}h")
        print(f"   📈 Volume filtering: {(self.volume_threshold-1)*100:.0f}% threshold")
        print(f"   💰 Optimized fees: {self.maker_fee*100:.2f}% maker used")
        
        if self.total_trades > 0:
            avg_return_per_trade = total_return / self.total_trades
            print(f"   💰 Average return per trade: ₱{avg_return_per_trade:.2f}")
        
        # Risk metrics
        if len(self.portfolio_history) > 1:
            portfolio_values = [p['portfolio_value'] for p in self.portfolio_history]
            max_portfolio = max(portfolio_values)
            min_portfolio = min(portfolio_values)
            max_drawdown = (max_portfolio - min_portfolio) / max_portfolio * 100
            print(f"   📉 Maximum drawdown: {max_drawdown:.1f}%")
        
        print("=" * 65)
        
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
    print("🚀 PROFITABLE Enhanced Momentum Trading Bot v3")
    print("💡 Multi-timeframe + Volume + Dynamic Thresholds + Fee Optimization")
    print("=" * 70)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    print("Select asset to test:")
    print("1. XRPPHP (Enhanced: 0.8%/1.2% dynamic thresholds)")
    print("2. SOLPHP (Enhanced: 1.2%/1.6% dynamic thresholds)")
    print("3. BTCPHP (Enhanced: 1.0%/1.4% dynamic thresholds)")
    
    choice = input("Enter choice (1-3): ").strip()
    symbol_map = {'1': 'XRPPHP', '2': 'SOLPHP', '3': 'BTCPHP'}
    symbol = symbol_map.get(choice, 'XRPPHP')
    
    try:
        days_input = input("How many days to test? (7-90): ").strip()
        days = int(days_input) if days_input else 30
        days = max(7, min(days, 90))
    except ValueError:
        days = 30
    
    print(f"\nTesting PROFITABLE enhanced {symbol} for {days} days...")
    
    backtester = ProfitableEnhancedBacktester(symbol)
    results = backtester.run_profitable_backtest(days)
    
    if results:
        print(f"\n💡 PROFITABLE ENHANCEMENT CONCLUSION:")
        
        improvement_vs_v2 = "Comparing to v2 baseline:"
        print(f"\n{improvement_vs_v2}")
        
        if results['return_percentage'] > 10:
            print("🚀 EXCELLENT: Major profitability improvement!")
        elif results['return_percentage'] > 5:
            print("🎯 GREAT: Significant profitability boost!")
        elif results['return_percentage'] > 2:
            print("✅ GOOD: Solid improvement in returns!")
        elif results['return_percentage'] > 0:
            print("🟡 POSITIVE: Modest gains, room for more optimization")
        else:
            print("⚠️ NEGATIVE: Need further refinement")
        
        if results['trades_per_day'] > 1:
            print(f"📈 ACTIVE: {results['trades_per_day']:.1f} trades/day (much more active!)")
        elif results['trades_per_day'] > 0.5:
            print(f"📊 MODERATE: {results['trades_per_day']:.1f} trades/day (good activity)")
        
        if results['win_rate'] > 60:
            print(f"🎯 EXCELLENT win rate: {results['win_rate']:.1f}%!")
        elif results['win_rate'] > 45:
            print(f"✅ GOOD win rate: {results['win_rate']:.1f}%")
        
        print(f"\n📊 Key improvements implemented:")
        print(f"   ✅ Multi-timeframe trend analysis")
        print(f"   ✅ Dynamic threshold adjustment")
        print(f"   ✅ Volume confirmation filters")
        print(f"   ✅ Reduced minimum hold times")
        print(f"   ✅ Optimized maker/taker fees")
        print(f"   ✅ Intelligent position sizing")
        print(f"   ✅ Emergency exit mechanisms")
        print(f"   ✅ Partial profit-taking")
        
        if results['outperformed_buy_hold']:
            print(f"\n🏆 Strategy beats buy & hold by {results['outperformance']:+.2f}%")
        
        print(f"\nNext steps for further optimization:")
        print(f"   🔧 Fine-tune parameters based on these results")
        print(f"   📊 Test on different time periods")
        print(f"   🎯 Consider additional technical indicators")
        print(f"   💰 Implement on live paper trading")

if __name__ == "__main__":
    main()