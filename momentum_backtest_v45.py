"""
🔬 ENHANCED MOMENTUM BACKTESTING ENGINE v45

Advanced backtesting system aligned with TITAN v3.3 and Take Profit Optimizer improvements.
Now supports multi-asset testing, TITAN position sizing strategies, and user-friendly interface.

NEW FEATURES v45:
- ✅ Multi-asset support (all 72 PHP pairs)
- ✅ TITAN v3.3 position sizing integration (4 strategies)
- ✅ Asset-specific parameter optimization
- ✅ User-friendly interface like take profit optimizer
- ✅ Volume-based asset suggestions
- ✅ Strategy comparison across assets
- ✅ Bot configuration export (TITAN/ORACLE ready)
- ✅ Volatility-based parameter ranges
- ✅ Comprehensive analysis with integration guidance
"""

import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI
import pandas as pd

load_dotenv(override=True)

class EnhancedMomentumBacktester:
    """
    🔬 Enhanced Momentum Strategy Backtester v45
    
    Comprehensive backtesting system with multi-asset support, TITAN position sizing,
    and user-friendly interface for optimal strategy development.
    """
    
    def __init__(self, symbol='XRPPHP', initial_balance=10000):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Multi-asset configuration
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')
        self.initial_balance = initial_balance
        
        # Strategy parameters (configurable per asset)
        self.buy_threshold = 0.006      # 0.6%
        self.sell_threshold = 0.010     # 1.0%
        self.take_profit_pct = 0.02     # 2.0% default
        self.base_amount = 200          # ₱200 base reference
        self.position_sizing = 'fixed'  # Default to fixed
        self.min_hold_minutes = 30      # 30 minutes
        self.max_trades_per_day = 10    # Daily limit
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        # State tracking
        self.reset_state()
        
        print(f"🔬 ENHANCED MOMENTUM BACKTESTER v45")
        print(f"🎯 Symbol: {self.symbol}")
        print(f"💰 Initial balance: ₱{self.initial_balance:,.2f}")

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
        self.equity_curve = []
        self.price_history = []
        
        # Performance tracking
        self.max_balance = self.initial_balance
        self.max_drawdown = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0

    def validate_symbol(self):
        """Validate that the symbol exists and is tradable"""
        try:
            symbol_info = self.api.get_symbol_info(self.symbol)
            if not symbol_info:
                print(f"❌ Symbol {self.symbol} not found!")
                return False
            
            status = symbol_info.get('status', '').upper()
            if status not in ['TRADING', 'ACTIVE']:
                print(f"❌ Symbol {self.symbol} is not currently tradable (status: {symbol_info.get('status')})")
                return False
            
            print(f"✅ Symbol {self.symbol} validated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error validating symbol {self.symbol}: {e}")
            return False

    def get_symbol_market_data(self):
        """Get market data and volatility analysis for the symbol"""
        try:
            # Get current price and 24hr ticker
            current_price = self.api.get_current_price(self.symbol)
            ticker_24hr = self.api.get_24hr_ticker(self.symbol)
            
            high_24h = float(ticker_24hr.get('highPrice', current_price))
            low_24h = float(ticker_24hr.get('lowPrice', current_price))
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            
            # Calculate volatility
            volatility = abs(price_change_24h)
            
            return {
                'current_price': current_price,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'volume_24h': volume_24h,
                'volatility': volatility,
                'price_change_24h': price_change_24h
            }
            
        except Exception as e:
            print(f"❌ Error getting market data for {self.symbol}: {e}")
            return None

    def get_asset_specific_parameters(self, volatility):
        """Get asset-specific parameter ranges based on volatility (like TITAN)"""
        
        if volatility > 15:  # Very high volatility (e.g., meme coins during pumps)
            return {
                'buy_thresholds': [0.003, 0.004, 0.005, 0.006],
                'sell_thresholds': [0.005, 0.008, 0.010, 0.012],
                'take_profit_range': [0.005, 0.008, 0.010, 0.012, 0.015, 0.020],
                'recommended_position_sizing': ['fixed', 'momentum'],
                'category': 'Very High Volatility'
            }
        elif volatility > 8:  # High volatility (e.g., SOL, small caps)
            return {
                'buy_thresholds': [0.004, 0.006, 0.008, 0.010],
                'sell_thresholds': [0.008, 0.010, 0.012, 0.015],
                'take_profit_range': [0.008, 0.010, 0.015, 0.020, 0.025, 0.030],
                'recommended_position_sizing': ['fixed', 'momentum', 'adaptive'],
                'category': 'High Volatility'
            }
        elif volatility > 3:  # Medium volatility (e.g., XRP, ETH)
            return {
                'buy_thresholds': [0.005, 0.006, 0.008, 0.010],
                'sell_thresholds': [0.008, 0.010, 0.012, 0.015],
                'take_profit_range': [0.015, 0.020, 0.025, 0.030, 0.040, 0.050],
                'recommended_position_sizing': ['percentage', 'adaptive'],
                'category': 'Medium Volatility'
            }
        else:  # Low volatility (e.g., BTC, stablecoins)
            return {
                'buy_thresholds': [0.006, 0.008, 0.010, 0.012],
                'sell_thresholds': [0.010, 0.012, 0.015, 0.020],
                'take_profit_range': [0.020, 0.030, 0.040, 0.050, 0.060, 0.080],
                'recommended_position_sizing': ['percentage', 'adaptive'],
                'category': 'Low Volatility'
            }

    def calculate_position_size_titan(self, current_price, momentum, trend, position_sizing='fixed'):
        """
        Calculate position size using TITAN v3.3 strategies
        
        Args:
            current_price: Current asset price
            momentum: Current momentum score
            trend: Current trend score
            position_sizing: 'fixed', 'percentage', 'momentum', 'adaptive'
            
        Returns:
            Position size in PHP
        """
        
        if position_sizing == 'fixed':
            return self.base_amount
            
        elif position_sizing == 'percentage':
            # 10% of available balance
            available_balance = self.php_balance
            position_pct = 0.10
            calculated_size = available_balance * position_pct
            
            # Ensure within reasonable bounds
            min_size = self.base_amount * 0.5
            max_size = self.base_amount * 2.0
            
            return max(min_size, min(calculated_size, max_size))
            
        elif position_sizing == 'momentum':
            # Adjust size based on momentum strength
            base_size = self.base_amount
            
            # Strong momentum = larger position
            if abs(momentum) > 0.012:  # 1.2% momentum
                multiplier = 1.4
            elif abs(momentum) > 0.008:  # 0.8% momentum  
                multiplier = 1.2
            elif abs(momentum) > 0.006:  # 0.6% momentum (threshold)
                multiplier = 1.0
            else:
                multiplier = 0.8  # Weak momentum
            
            # Apply trend filter
            if trend < -0.03:  # Strong downtrend
                multiplier *= 0.7
            elif trend > 0.02:  # Strong uptrend
                multiplier *= 1.1
                
            calculated_size = base_size * multiplier
            
            # Bounds checking
            min_size = self.base_amount * 0.5
            max_size = self.base_amount * 1.5
            
            return max(min_size, min(calculated_size, max_size))
            
        elif position_sizing == 'adaptive':
            # Advanced: Combine balance, momentum, and recent performance
            available_balance = self.php_balance
            
            # Base sizing on available balance
            balance_multiplier = min(2.0, available_balance / (self.base_amount * 5))
            
            # Momentum adjustment
            momentum_strength = abs(momentum)
            if momentum_strength > 0.015:
                momentum_multiplier = 1.3
            elif momentum_strength > 0.010:
                momentum_multiplier = 1.1
            elif momentum_strength > 0.006:
                momentum_multiplier = 1.0
            else:
                momentum_multiplier = 0.8
            
            # Trend adjustment
            if trend > 0.02:
                trend_multiplier = 1.1
            elif trend < -0.03:
                trend_multiplier = 0.8
            else:
                trend_multiplier = 1.0
            
            # Daily trades adjustment
            today = datetime.now().strftime('%Y-%m-%d')
            trades_today = self.daily_trades.get(today, 0)
            if trades_today >= 7:
                trade_multiplier = 0.7
            elif trades_today >= 5:
                trade_multiplier = 0.9
            else:
                trade_multiplier = 1.0
            
            # Calculate final size
            total_multiplier = balance_multiplier * momentum_multiplier * trend_multiplier * trade_multiplier
            calculated_size = self.base_amount * total_multiplier
            
            # Apply bounds
            min_size = self.base_amount * 0.3
            max_size = self.base_amount * 2.0
            
            return max(min_size, min(calculated_size, max_size))
        
        else:
            return self.base_amount

    def fetch_historical_data(self, days=60, interval='1h') -> List[Dict]:
        """Fetch historical price data from Coins.ph API"""
        cache_key = f'_cached_data_{self.symbol}_{days}_{interval}'
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        print(f"📊 Fetching {days} days of {interval} data for {self.symbol}...")
        
        try:
            intervals_per_day = {'1h': 24, '4h': 6, '1d': 1}
            limit = min(days * intervals_per_day.get(interval, 24), 1000)
            
            klines = self.api._make_request(
                'GET',
                '/openapi/quote/v1/klines',
                {
                    'symbol': self.symbol,
                    'interval': interval,
                    'limit': limit
                }
            )
            
            if not klines:
                print("❌ No historical data received")
                return []
            
            # Convert to standardized format
            data = []
            for kline in klines:
                candle = {
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                }
                data.append(candle)
            
            # Sort by timestamp
            data.sort(key=lambda x: x['timestamp'])
            
            actual_days = (data[-1]['timestamp'] - data[0]['timestamp']).days
            print(f"✅ Fetched {len(data)} candles covering {actual_days} days")
            
            # Cache the data
            setattr(self, cache_key, data)
            return data
            
        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return []

    def calculate_momentum(self, prices: List[float], period: int = 3) -> float:
        """Calculate momentum based on recent price changes"""
        if len(prices) < period + 1:
            return 0.0
        
        current_price = prices[-1]
        past_price = prices[-(period + 1)]
        
        return (current_price - past_price) / past_price

    def calculate_trend(self, prices: List[float], window: int = 12) -> float:
        """Calculate trend direction over the window"""
        if len(prices) < window:
            return 0
        
        recent = prices[-window:]
        mid = len(recent) // 2
        first_half = sum(recent[:mid]) / mid
        second_half = sum(recent[mid:]) / (len(recent) - mid)
        
        return (second_half - first_half) / first_half

    def can_trade_today(self, current_time: datetime) -> bool:
        """Check if we can still trade today (daily limit)"""
        date_key = current_time.strftime('%Y-%m-%d')
        trades_today = self.daily_trades.get(date_key, 0)
        return trades_today < self.max_trades_per_day

    def can_sell_position(self, current_time: datetime) -> bool:
        """Check if minimum hold time has passed"""
        if self.entry_time is None:
            return True
        hold_duration = current_time - self.entry_time
        min_hold_delta = timedelta(minutes=self.min_hold_minutes)
        return hold_duration >= min_hold_delta

    def update_daily_trades(self, current_time: datetime):
        """Update daily trade counter"""
        date_key = current_time.strftime('%Y-%m-%d')
        self.daily_trades[date_key] = self.daily_trades.get(date_key, 0) + 1

    def place_buy(self, price: float, time: datetime, momentum: float, position_size: float) -> bool:
        """Simulate buy order execution with TITAN position sizing"""
        
        amount_to_spend = min(position_size, self.php_balance * 0.9)
        
        if amount_to_spend < 20:  # Minimum order size
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
            
            # Record trade
            trade = {
                'timestamp': time,
                'side': 'BUY',
                'price': price,
                'amount': amount_to_spend,
                'quantity': asset_quantity,
                'fee': fee,
                'momentum': momentum,
                'position_size': position_size,
                'position_sizing': self.position_sizing,
                'balance_after': self.php_balance + (self.asset_balance * price),
                'reason': 'Momentum Signal'
            }
            self.trade_history.append(trade)
            
            return True
        
        return False

    def place_sell(self, price: float, time: datetime, momentum: float, reason: str) -> bool:
        """Simulate sell order execution"""
        if self.asset_balance <= 0:
            return False
        
        asset_to_sell = self.asset_balance * 0.99  # Keep 1% to avoid dust
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
        profit_loss_pct = 0
        if self.entry_price:
            profit_loss = net_amount - (self.entry_price * asset_to_sell)
            profit_loss_pct = (price - self.entry_price) / self.entry_price * 100
            
            if profit_loss > 0:
                self.winning_trades += 1
                self.total_profit += profit_loss
            else:
                self.losing_trades += 1
                self.total_loss += abs(profit_loss)
        
        # Record trade
        trade = {
            'timestamp': time,
            'side': 'SELL',
            'price': price,
            'amount': gross_amount,
            'quantity': asset_to_sell,
            'fee': fee,
            'momentum': momentum,
            'profit_loss': profit_loss,
            'profit_loss_pct': profit_loss_pct,
            'balance_after': self.php_balance + (self.asset_balance * price),
            'reason': reason
        }
        self.trade_history.append(trade)
        
        self.entry_price = None
        self.entry_time = None
        return True

    def update_equity_curve(self, price: float, time: datetime):
        """Update equity curve for drawdown calculation"""
        total_value = self.php_balance + (self.asset_balance * price)
        
        self.equity_curve.append({
            'timestamp': time,
            'total_value': total_value,
            'php_balance': self.php_balance,
            'asset_value': self.asset_balance * price,
            'asset_quantity': self.asset_balance
        })
        
        # Update max balance and drawdown
        if total_value > self.max_balance:
            self.max_balance = total_value
        
        current_drawdown = (self.max_balance - total_value) / self.max_balance * 100
        if current_drawdown > self.max_drawdown:
            self.max_drawdown = current_drawdown

    def run_enhanced_strategy(self, data: List[Dict], 
                            buy_threshold: float = None,
                            sell_threshold: float = None,
                            take_profit_pct: float = None,
                            position_sizing: str = None) -> Dict:
        """
        Run enhanced momentum strategy with TITAN position sizing
        
        Args:
            data: Historical OHLCV data
            buy_threshold: Override buy threshold
            sell_threshold: Override sell threshold
            take_profit_pct: Override take profit percentage
            position_sizing: Override position sizing strategy
            
        Returns:
            Comprehensive backtest results
        """
        # Use provided parameters or defaults
        self.buy_threshold = buy_threshold or self.buy_threshold
        self.sell_threshold = sell_threshold or self.sell_threshold
        self.take_profit_pct = take_profit_pct or self.take_profit_pct
        self.position_sizing = position_sizing or self.position_sizing
        
        print(f"🚀 Running enhanced momentum strategy...")
        print(f"📊 Parameters: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%, TP {self.take_profit_pct*100:.1f}%")
        print(f"💰 Position sizing: {self.position_sizing}")
        
        self.reset_state()
        
        # Build price history for momentum calculation
        prices = []
        
        for i, candle in enumerate(data):
            current_price = candle['close']
            current_time = candle['timestamp']
            
            prices.append(current_price)
            
            # Need at least 15 candles for proper momentum and trend calculation
            if len(prices) < 15:
                continue
            
            # Calculate momentum and trend
            momentum = self.calculate_momentum(prices, period=3)
            trend = self.calculate_trend(prices, window=12)
            
            # Update equity curve
            self.update_equity_curve(current_price, current_time)
            
            # Calculate dynamic position size using TITAN strategies
            position_size = self.calculate_position_size_titan(current_price, momentum, trend, self.position_sizing)
            
            # BUY CONDITIONS
            if (momentum > self.buy_threshold and              # Strong upward momentum
                trend > -0.02 and                              # Not in strong downtrend
                self.php_balance > position_size * 0.6 and     # Have enough PHP
                self.can_trade_today(current_time) and         # Within daily limit
                self.position is None):                        # No current position
                
                self.place_buy(current_price, current_time, momentum, position_size)
            
            # SELL CONDITIONS - Momentum down
            elif (momentum < -self.sell_threshold and          # Strong downward momentum
                  self.asset_balance > 0.001 and               # Have position
                  self.can_sell_position(current_time) and     # Min hold time met
                  self.can_trade_today(current_time)):         # Within daily limit
                
                self.place_sell(current_price, current_time, momentum, "Momentum Down")
            
            # SELL CONDITIONS - Take profit
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position(current_time)):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct >= self.take_profit_pct:
                    self.place_sell(current_price, current_time, momentum, "Take Profit")
            
            # EMERGENCY EXIT - Strong downtrend
            elif (trend < -0.05 and                            # Very strong downtrend
                  self.asset_balance > 0.001 and               # Have position
                  self.can_sell_position(current_time)):       # Min hold time met
                
                self.place_sell(current_price, current_time, momentum, "Emergency Exit")
        
        # Calculate final results
        final_price = data[-1]['close']
        final_portfolio_value = self.php_balance + (self.asset_balance * final_price)
        
        return self.calculate_comprehensive_metrics(data[0], data[-1], final_portfolio_value)

    def calculate_comprehensive_metrics(self, start_candle: Dict, end_candle: Dict, final_value: float) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        start_price = start_candle['close']
        end_price = end_candle['close']
        start_time = start_candle['timestamp']
        end_time = end_candle['timestamp']
        
        # Basic returns
        total_return = final_value - self.initial_balance
        return_percentage = (total_return / self.initial_balance) * 100
        
        # Time metrics
        total_days = (end_time - start_time).days
        if total_days > 0:
            daily_return = (final_value / self.initial_balance) ** (1/total_days) - 1
            annualized_return = ((1 + daily_return) ** 365 - 1) * 100
        else:
            annualized_return = 0
        
        # Buy and hold comparison
        initial_asset_if_bought = (self.initial_balance - (self.initial_balance * self.maker_fee)) / start_price
        buy_hold_value = initial_asset_if_bought * end_price
        buy_hold_return = (buy_hold_value - self.initial_balance) / self.initial_balance * 100
        outperformance = return_percentage - buy_hold_return
        
        # Trade analysis
        total_trades = len(self.trade_history)
        if total_trades > 0:
            win_rate = (self.winning_trades / (self.winning_trades + self.losing_trades)) * 100 if (self.winning_trades + self.losing_trades) > 0 else 0
            avg_win = self.total_profit / max(1, self.winning_trades)
            avg_loss = self.total_loss / max(1, self.losing_trades)
            profit_factor = self.total_profit / max(1, self.total_loss)
            trades_per_day = total_trades / max(1, total_days)
        else:
            win_rate = avg_win = avg_loss = profit_factor = trades_per_day = 0
        
        # Risk metrics
        sharpe_ratio = self.calculate_sharpe_ratio()
        volatility = self.calculate_volatility()
        
        # Trade type analysis
        buy_trades = [t for t in self.trade_history if t['side'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['side'] == 'SELL']
        profit_taking_trades = [t for t in sell_trades if t.get('reason') == 'Take Profit']
        momentum_down_trades = [t for t in sell_trades if t.get('reason') == 'Momentum Down']
        emergency_trades = [t for t in sell_trades if t.get('reason') == 'Emergency Exit']
        
        # Position sizing analysis
        if buy_trades:
            avg_position_size = sum(t.get('position_size', 0) for t in buy_trades) / len(buy_trades)
            max_position_size = max(t.get('position_size', 0) for t in buy_trades)
            min_position_size = min(t.get('position_size', 0) for t in buy_trades)
        else:
            avg_position_size = max_position_size = min_position_size = 0
        
        return {
            # Strategy configuration
            'symbol': self.symbol,
            'base_asset': self.base_asset,
            'position_sizing': self.position_sizing,
            'buy_threshold': self.buy_threshold * 100,
            'sell_threshold': self.sell_threshold * 100,
            'take_profit_pct': self.take_profit_pct * 100,
            'base_amount': self.base_amount,
            
            # Time and market data
            'start_date': start_time.strftime('%Y-%m-%d'),
            'end_date': end_time.strftime('%Y-%m-%d'),
            'total_days': total_days,
            'start_price': start_price,
            'end_price': end_price,
            'market_return': ((end_price - start_price) / start_price) * 100,
            
            # Performance metrics
            'initial_balance': self.initial_balance,
            'final_balance': final_value,
            'total_return': total_return,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            
            # Benchmark comparison
            'buy_hold_return': buy_hold_return,
            'outperformance': outperformance,
            'beat_buy_hold': return_percentage > buy_hold_return,
            
            # Trade metrics
            'total_trades': total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades_per_day': trades_per_day,
            
            # Cost analysis
            'total_fees': self.total_fees_paid,
            'fees_percentage': (self.total_fees_paid / self.initial_balance) * 100,
            
            # Risk metrics
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            
            # Exit analysis
            'profit_taking_trades': len(profit_taking_trades),
            'momentum_down_trades': len(momentum_down_trades),
            'emergency_trades': len(emergency_trades),
            'profit_taking_rate': len(profit_taking_trades) / max(1, len(sell_trades)) * 100,
            
            # Position sizing analysis
            'avg_position_size': avg_position_size,
            'max_position_size': max_position_size,
            'min_position_size': min_position_size,
            'position_size_range': max_position_size - min_position_size,
            
            # Raw data
            'trade_history': self.trade_history,
            'equity_curve': self.equity_curve,
            'daily_trades': self.daily_trades
        }

    def calculate_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio from equity curve"""
        if len(self.equity_curve) < 2:
            return 0
        
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_value = self.equity_curve[i-1]['total_value']
            curr_value = self.equity_curve[i]['total_value']
            returns.append((curr_value - prev_value) / prev_value)
        
        if not returns:
            return 0
        
        avg_return = sum(returns) / len(returns)
        
        if len(returns) < 2:
            return 0
        
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance ** 0.5
        
        if std_dev == 0:
            return 0
        
        # Annualize (assuming hourly data)
        risk_free_rate = 0.02 / (365 * 24)  # 2% annual risk-free rate
        return (avg_return - risk_free_rate) / std_dev * (24 * 365) ** 0.5

    def calculate_volatility(self) -> float:
        """Calculate portfolio volatility"""
        if len(self.equity_curve) < 2:
            return 0
        
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_value = self.equity_curve[i-1]['total_value']
            curr_value = self.equity_curve[i]['total_value']
            returns.append((curr_value - prev_value) / prev_value)
        
        if len(returns) < 2:
            return 0
        
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        
        # Annualize (assuming hourly data)
        return (variance ** 0.5) * (24 * 365) ** 0.5 * 100

    def print_comprehensive_results(self, results: Dict):
        """Print comprehensive backtest results with TITAN integration"""
        print(f"\n" + "=" * 90)
        print(f"📊 ENHANCED MOMENTUM BACKTEST RESULTS v45")
        print(f"=" * 90)
        
        print(f"🎯 STRATEGY CONFIGURATION:")
        print(f"   Symbol: {results['symbol']} ({results['base_asset']}/PHP)")
        print(f"   Period: {results['start_date']} to {results['end_date']} ({results['total_days']} days)")
        print(f"   Position sizing: {results['position_sizing'].title()}")
        print(f"   Buy threshold: {results['buy_threshold']:.1f}%")
        print(f"   Sell threshold: {results['sell_threshold']:.1f}%")
        print(f"   Take profit: {results['take_profit_pct']:.1f}%")
        print(f"   Base amount: ₱{results['base_amount']}")
        
        print(f"\n💰 PERFORMANCE SUMMARY:")
        print(f"   Initial balance: ₱{results['initial_balance']:,.2f}")
        print(f"   Final balance: ₱{results['final_balance']:,.2f}")
        print(f"   Total return: ₱{results['total_return']:,.2f} ({results['return_percentage']:+.2f}%)")
        print(f"   Annualized return: {results['annualized_return']:+.2f}%")
        print(f"   Market return: {results['market_return']:+.2f}%")
        
        print(f"\n📈 BENCHMARK COMPARISON:")
        print(f"   Buy & Hold return: {results['buy_hold_return']:+.2f}%")
        print(f"   Strategy outperformance: {results['outperformance']:+.2f}%")
        print(f"   Beat buy & hold: {'✅ YES' if results['beat_buy_hold'] else '❌ NO'}")
        
        print(f"\n📊 TRADE ANALYSIS:")
        print(f"   Total trades: {results['total_trades']}")
        print(f"   Winning trades: {results['winning_trades']} ({results['win_rate']:.1f}%)")
        print(f"   Losing trades: {results['losing_trades']}")
        print(f"   Average win: ₱{results['avg_win']:.2f}")
        print(f"   Average loss: ₱{results['avg_loss']:.2f}")
        print(f"   Profit factor: {results['profit_factor']:.2f}")
        print(f"   Trades per day: {results['trades_per_day']:.1f}")
        
        print(f"\n🎯 EXIT ANALYSIS:")
        print(f"   Take profit exits: {results['profit_taking_trades']} ({results['profit_taking_rate']:.1f}%)")
        print(f"   Momentum down exits: {results['momentum_down_trades']}")
        print(f"   Emergency exits: {results['emergency_trades']}")
        
        print(f"\n💰 POSITION SIZING ANALYSIS ({results['position_sizing'].title()}):")
        print(f"   Average position size: ₱{results['avg_position_size']:.0f}")
        print(f"   Position size range: ₱{results['min_position_size']:.0f} - ₱{results['max_position_size']:.0f}")
        print(f"   Dynamic range: ₱{results['position_size_range']:.0f}")
        
        print(f"\n⚠️ RISK METRICS:")
        print(f"   Maximum drawdown: {results['max_drawdown']:.2f}%")
        print(f"   Sharpe ratio: {results['sharpe_ratio']:.2f}")
        print(f"   Volatility: {results['volatility']:.2f}%")
        
        print(f"\n💸 COST ANALYSIS:")
        print(f"   Total fees paid: ₱{results['total_fees']:.2f} ({results['fees_percentage']:.2f}%)")
        
        print(f"\n" + "=" * 90)

    def test_all_position_sizing_strategies(self, data: List[Dict]) -> Dict:
        """Test all 4 TITAN position sizing strategies and compare results"""
        
        print(f"\n🔬 TESTING ALL TITAN POSITION SIZING STRATEGIES")
        print(f"🎯 Symbol: {self.symbol}")
        print("=" * 80)
        
        strategies = ['fixed', 'percentage', 'momentum', 'adaptive']
        results = {}
        
        for strategy in strategies:
            print(f"\n📊 Testing {strategy.title()} Position Sizing...")
            
            # Run backtest with this position sizing strategy
            result = self.run_enhanced_strategy(data, position_sizing=strategy)
            results[strategy] = result
            
            print(f"   Return: {result['return_percentage']:+.1f}% | "
                  f"Trades: {result['total_trades']} | "
                  f"Win Rate: {result['win_rate']:.0f}% | "
                  f"Avg Size: ₱{result['avg_position_size']:.0f}")
        
        # Display comparison
        print(f"\n📊 POSITION SIZING STRATEGY COMPARISON:")
        print("-" * 90)
        print(f"{'Strategy':<12} {'Return%':<8} {'Trades':<7} {'Win%':<6} {'Avg Size':<9} {'Range':<10} {'Sharpe':<7}")
        print("-" * 90)
        
        best_return = None
        best_sharpe = None
        
        for strategy, result in results.items():
            return_pct = result['return_percentage']
            total_trades = result['total_trades']
            win_rate = result['win_rate']
            avg_size = result['avg_position_size']
            size_range = result['position_size_range']
            sharpe = result['sharpe_ratio']
            
            # Track best performers
            if best_return is None or return_pct > best_return['return']:
                best_return = {'strategy': strategy, 'return': return_pct}
            if best_sharpe is None or sharpe > best_sharpe['sharpe']:
                best_sharpe = {'strategy': strategy, 'sharpe': sharpe}
            
            print(f"{strategy.title():<12} "
                  f"{return_pct:+7.1f} "
                  f"{total_trades:>6} "
                  f"{win_rate:>5.0f} "
                  f"₱{avg_size:>7.0f} "
                  f"₱{size_range:>8.0f} "
                  f"{sharpe:>6.2f}")
        
        print("-" * 90)
        
        # Recommendations
        print(f"\n🏆 POSITION SIZING RECOMMENDATIONS:")
        print(f"   📈 Best Return: {best_return['strategy'].title()} ({best_return['return']:+.1f}%)")
        print(f"   ⚖️ Best Sharpe: {best_sharpe['strategy'].title()} ({best_sharpe['sharpe']:.2f})")
        
        # Strategy explanations
        print(f"\n💡 STRATEGY CHARACTERISTICS:")
        print(f"   🔒 Fixed: Consistent ₱{self.base_amount} trades (predictable)")
        print(f"   📊 Percentage: 10% of balance (grows with account)")
        print(f"   ⚡ Momentum: Size varies with signal strength")
        print(f"   🧠 Adaptive: Multi-factor intelligent sizing (recommended)")
        
        return results

    def optimize_asset_parameters(self, data: List[Dict], market_data: Dict) -> Dict:
        """Optimize parameters specifically for this asset based on volatility"""
        
        volatility = market_data['volatility']
        asset_params = self.get_asset_specific_parameters(volatility)
        
        print(f"\n🔬 ASSET-SPECIFIC PARAMETER OPTIMIZATION")
        print(f"🎯 Symbol: {self.symbol} ({asset_params['category']})")
        print(f"📊 24h Volatility: {volatility:.1f}%")
        print("=" * 80)
        
        # Test different parameter combinations
        best_results = []
        test_count = 0
        total_tests = len(asset_params['buy_thresholds']) * len(asset_params['take_profit_range'])
        
        for buy_thresh in asset_params['buy_thresholds']:
            for tp_pct in asset_params['take_profit_range']:
                test_count += 1
                print(f"📊 [{test_count:2d}/{total_tests}] Testing Buy: {buy_thresh*100:.1f}%, TP: {tp_pct*100:.1f}%...", end=" ")
                
                # Use appropriate sell threshold (typically 1.5-2x buy threshold)
                sell_thresh = buy_thresh * 1.67
                
                result = self.run_enhanced_strategy(
                    data,
                    buy_threshold=buy_thresh,
                    sell_threshold=sell_thresh,
                    take_profit_pct=tp_pct,
                    position_sizing='adaptive'  # Use adaptive for optimization
                )
                
                result['test_buy_threshold'] = buy_thresh * 100
                result['test_sell_threshold'] = sell_thresh * 100
                result['test_take_profit'] = tp_pct * 100
                
                best_results.append(result)
                
                print(f"Return: {result['return_percentage']:+.1f}%")
        
        # Sort by return percentage
        best_results.sort(key=lambda x: x['return_percentage'], reverse=True)
        
        # Display top results
        print(f"\n🏆 TOP 5 PARAMETER COMBINATIONS for {self.symbol}:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Buy%':<6} {'TP%':<6} {'Return%':<8} {'Win%':<6} {'Trades':<7} {'Sharpe':<7}")
        print("-" * 80)
        
        for i, result in enumerate(best_results[:5]):
            rank = i + 1
            buy_pct = result['test_buy_threshold']
            tp_pct = result['test_take_profit']
            return_pct = result['return_percentage']
            win_rate = result['win_rate']
            trades = result['total_trades']
            sharpe = result['sharpe_ratio']
            
            print(f"{rank:<4} {buy_pct:<6.1f} {tp_pct:<6.1f} "
                  f"{return_pct:+7.1f} {win_rate:>5.0f} "
                  f"{trades:>6} {sharpe:>6.2f}")
        
        print("-" * 80)
        
        # Best configuration
        best_config = best_results[0]
        
        print(f"\n🎯 OPTIMAL CONFIGURATION for {self.symbol}:")
        print(f"   Buy threshold: {best_config['test_buy_threshold']:.1f}%")
        print(f"   Take profit: {best_config['test_take_profit']:.1f}%")
        print(f"   Expected return: {best_config['return_percentage']:+.1f}%")
        print(f"   Win rate: {best_config['win_rate']:.0f}%")
        print(f"   Recommended position sizing: {', '.join(asset_params['recommended_position_sizing'])}")
        
        return {
            'best_config': best_config,
            'all_results': best_results,
            'asset_category': asset_params['category'],
            'volatility': volatility
        }

    def generate_bot_config(self, optimization_results: Dict) -> Dict:
        """Generate ready-to-use configuration for TITAN and ORACLE bots"""
        
        best_config = optimization_results['best_config']
        
        # TITAN configuration
        titan_config = {
            'symbol': self.symbol,
            'take_profit_pct': best_config['test_take_profit'],
            'base_amount': self.base_amount,
            'position_sizing': 'adaptive',  # Recommended
            'buy_threshold': best_config['test_buy_threshold'],
            'sell_threshold': best_config['test_sell_threshold'],
            'min_hold_hours': 0.5,
            'max_trades_per_day': 10,
            'expected_performance': {
                'return_pct': best_config['return_percentage'],
                'win_rate': best_config['win_rate'],
                'trades_per_day': best_config['trades_per_day'],
                'sharpe_ratio': best_config['sharpe_ratio']
            }
        }
        
        # ORACLE configuration
        oracle_config = {
            'symbol': self.symbol.replace('PHP', '/USD'),  # Convert to AI format
            'fallback_take_profit': best_config['test_take_profit'],
            'base_amount': self.base_amount,
            'momentum_confirmation': {
                'buy_threshold': best_config['test_buy_threshold'],
                'sell_threshold': best_config['test_sell_threshold']
            }
        }
        
        return {
            'titan': titan_config,
            'oracle': oracle_config,
            'optimization_summary': {
                'tested_configurations': len(optimization_results['all_results']),
                'asset_category': optimization_results['asset_category'],
                'volatility': optimization_results['volatility'],
                'optimization_date': datetime.now().strftime('%Y-%m-%d')
            }
        }

# ========== USER INTERFACE FUNCTIONS ==========

def get_symbol_suggestions():
    """Get trading pair suggestions with volume data"""
    try:
        api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Get all tickers
        tickers = api.get_24hr_ticker()
        if not isinstance(tickers, list):
            tickers = [tickers]
        
        # Filter and sort PHP pairs by volume
        php_pairs = []
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if symbol.endswith('PHP'):
                volume = float(ticker.get('quoteVolume', 0))
                price_change = float(ticker.get('priceChangePercent', 0))
                
                if volume > 10000:  # Only show pairs with decent volume
                    php_pairs.append({
                        'symbol': symbol,
                        'volume': volume,
                        'price_change': price_change
                    })
        
        # Sort by volume (highest first)
        php_pairs.sort(key=lambda x: x['volume'], reverse=True)
        
        return php_pairs[:15]  # Return top 15
        
    except Exception as e:
        print(f"❌ Error getting symbol suggestions: {e}")
        return []

def get_available_php_pairs():
    """Get all available PHP trading pairs from the exchange"""
    try:
        api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        exchange_info = api.get_exchange_info()
        symbols = exchange_info.get('symbols', [])
        
        # Filter for PHP pairs that are trading
        php_pairs = []
        for symbol in symbols:
            if (symbol.get('quoteAsset') == 'PHP' and 
                symbol.get('status', '').upper() in ['TRADING', 'ACTIVE']):
                php_pairs.append(symbol['symbol'])
        
        php_pairs.sort()
        return php_pairs
        
    except Exception as e:
        print(f"❌ Error fetching available pairs: {e}")
        return []

def main():
    """Main function with enhanced user interface"""
    print("🔬 ENHANCED MOMENTUM BACKTESTING ENGINE v45")
    print("🎯 Multi-asset testing with TITAN position sizing integration")
    print("=" * 85)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found!")
        return
    
    # Get symbol suggestions
    print("🔍 Getting available trading pairs...")
    suggestions = get_symbol_suggestions()
    
    if suggestions:
        print(f"\n📊 TOP VOLUME PHP PAIRS (Recommended):")
        for i, pair in enumerate(suggestions[:8], 1):
            volume_str = f"₱{pair['volume']/1000000:.1f}M" if pair['volume'] >= 1000000 else f"₱{pair['volume']/1000:.0f}K"
            change_emoji = "📈" if pair['price_change'] > 0 else "📉"
            print(f"  {i}. {pair['symbol']:<8} - {volume_str:<8} {change_emoji} {pair['price_change']:+.1f}%")
    
    # Asset selection
    print(f"\n🎯 Select trading asset for backtesting:")
    print("1. XRPPHP - Recommended (Medium volatility, proven momentum performance)")
    print("2. SOLPHP - High volatility (Good for testing adaptive strategies)")
    print("3. BTCPHP - Lower volatility (Conservative, stable testing)")
    print("4. Custom symbol - Enter any PHP trading pair")
    print("5. Browse all available pairs")
    
    while True:
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == '1':
            symbol = 'XRPPHP'
            break
        elif choice == '2':
            symbol = 'SOLPHP'
            break
        elif choice == '3':
            symbol = 'BTCPHP'
            break
        elif choice == '4':
            while True:
                custom_symbol = input("Enter symbol (e.g., ETHPHP, ADAPHP): ").strip().upper()
                if custom_symbol.endswith('PHP') and len(custom_symbol) >= 6:
                    symbol = custom_symbol
                    break
                else:
                    print("Please enter a valid PHP trading pair (e.g., ETHPHP)")
            break
        elif choice == '5':
            available_pairs = get_available_php_pairs()
            if available_pairs:
                print(f"\n📋 All available PHP pairs ({len(available_pairs)} total):")
                for i, pair in enumerate(available_pairs):
                    print(f"  {pair}", end="  ")
                    if (i + 1) % 6 == 0:
                        print()
                print()
                
                while True:
                    browse_symbol = input("Enter symbol from list above: ").strip().upper()
                    if browse_symbol in available_pairs:
                        symbol = browse_symbol
                        break
                    else:
                        print(f"Please enter a valid symbol from the list above")
                break
            else:
                print("❌ Could not fetch available pairs")
                continue
        else:
            print("Please enter 1-5")
    
    # Backtest type selection
    print(f"\n🔬 Select backtest type:")
    print("1. Quick Strategy Test - Test single configuration (Fast)")
    print("2. Position Sizing Comparison - Test all 4 TITAN strategies")
    print("3. Asset-Specific Optimization - Find optimal parameters")
    print("4. Complete Analysis - Full optimization + strategy comparison")
    
    while True:
        test_choice = input("Enter choice (1-4): ").strip()
        if test_choice in ['1', '2', '3', '4']:
            break
        else:
            print("Please enter 1-4")
    
    # Time period selection
    print(f"\n⚙️ Select testing period:")
    print("1. Quick test (30 days) - Fast results")
    print("2. Standard test (60 days) - Balanced analysis")
    print("3. Custom period")
    
    while True:
        days_choice = input("Enter choice (1-3): ").strip()
        if days_choice == '1':
            days = 30
            break
        elif days_choice == '2':
            days = 60
            break
        elif days_choice == '3':
            while True:
                try:
                    days = int(input("Enter number of days (7-365): "))
                    if 7 <= days <= 365:
                        break
                    else:
                        print("Please enter a value between 7 and 365")
                except ValueError:
                    print("Please enter a valid number")
            break
        else:
            print("Please enter 1-3")
    
    print(f"\n🚀 Starting enhanced backtesting...")
    print(f"🎯 Symbol: {symbol}")
    print(f"📅 Period: {days} days")
    
    # Initialize backtester
    backtester = EnhancedMomentumBacktester(symbol=symbol)
    
    # Validate symbol
    if not backtester.validate_symbol():
        print("❌ Symbol validation failed!")
        return
    
    # Get market data
    market_data = backtester.get_symbol_market_data()
    if not market_data:
        print("❌ Could not fetch market data!")
        return
    
    # Fetch historical data
    data = backtester.fetch_historical_data(days=days)
    if not data:
        print("❌ Failed to fetch historical data!")
        return
    
    # Display market context
    print(f"\n📊 {symbol} Market Analysis:")
    print(f"   Current Price: ₱{market_data['current_price']:,.4f}")
    print(f"   24h Volume: ₱{market_data['volume_24h']:,.0f}")
    print(f"   24h Volatility: {market_data['volatility']:.1f}%")
    
    # Execute selected backtest type
    if test_choice == '1':
        # Quick Strategy Test
        results = backtester.run_enhanced_strategy(data)
        backtester.print_comprehensive_results(results)
        
    elif test_choice == '2':
        # Position Sizing Comparison
        results = backtester.test_all_position_sizing_strategies(data)
        
    elif test_choice == '3':
        # Asset-Specific Optimization
        optimization_results = backtester.optimize_asset_parameters(data, market_data)
        
        # Generate bot configuration
        bot_config = backtester.generate_bot_config(optimization_results)
        
        print(f"\n🤖 BOT CONFIGURATION READY:")
        print(f"📊 TITAN Configuration:")
        titan_config = bot_config['titan']
        print(f"   Symbol: {titan_config['symbol']}")
        print(f"   Take Profit: {titan_config['take_profit_pct']:.1f}%")
        print(f"   Position Sizing: {titan_config['position_sizing']}")
        print(f"   Expected Return: {titan_config['expected_performance']['return_pct']:+.1f}%")
        
        print(f"\n🔮 ORACLE Configuration:")
        oracle_config = bot_config['oracle']
        print(f"   Symbol: {oracle_config['symbol']}")
        print(f"   Fallback TP: {oracle_config['fallback_take_profit']:.1f}%")
        
    elif test_choice == '4':
        # Complete Analysis
        print(f"\n🔬 RUNNING COMPLETE ANALYSIS...")
        
        # 1. Position sizing comparison
        print(f"\n1️⃣ POSITION SIZING COMPARISON:")
        sizing_results = backtester.test_all_position_sizing_strategies(data)
        
        # 2. Asset-specific optimization
        print(f"\n2️⃣ ASSET-SPECIFIC OPTIMIZATION:")
        optimization_results = backtester.optimize_asset_parameters(data, market_data)
        
        # 3. Generate configurations
        bot_config = backtester.generate_bot_config(optimization_results)
        
        # 4. Final recommendations
        print(f"\n🎯 FINAL RECOMMENDATIONS for {symbol}:")
        print(f"   📈 Best Position Sizing: Check comparison table above")
        print(f"   🎯 Optimal Parameters: {optimization_results['best_config']['test_buy_threshold']:.1f}% buy, "
              f"{optimization_results['best_config']['test_take_profit']:.1f}% TP")
        print(f"   🤖 Ready for TITAN: Use configuration above")
        print(f"   🔮 Ready for ORACLE: Fallback TP configured")
    
    # Export option
    export_choice = input(f"\n💾 Export results to JSON? (y/n): ").strip().lower()
    if export_choice.startswith('y'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"enhanced_backtest_{symbol}_{timestamp}.json"
        try:
            if 'bot_config' in locals():
                with open(filename, 'w') as f:
                    json.dump(bot_config, f, indent=2, default=str)
                print(f"✅ Configuration exported to {filename}")
            else:
                print("⚠️ No configuration data to export")
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    print(f"\n✅ Enhanced backtesting complete for {symbol}!")
    print(f"🎯 Use the optimized settings in your TITAN and ORACLE bots")

if __name__ == "__main__":
    main()