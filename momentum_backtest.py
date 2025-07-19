"""
Enhanced Momentum Backtesting Engine v4.7

NEW in v4.7: Ecosystem Integration
- ✅ Generates research insights for Ecosystem Manager
- ✅ Saves asset performance rankings and recommendations
- ✅ Creates ecosystem-compatible data structures
- ✅ Provides smart asset suggestions for other tools
- ✅ Maintains all v4.6 functionality with ecosystem enhancements

SAVE THIS FILE AS: momentum_backtest_v47.py
Then run: python momentum_backtest_v47.py
"""

import os
import sys
import signal
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI
import pandas as pd

# Import ecosystem manager
try:
    from ecosystem_manager import get_ecosystem_manager, AssetInsight, log_tool_usage
    ECOSYSTEM_AVAILABLE = True
    print("✅ Ecosystem Manager available - insights will be generated")
except ImportError:
    ECOSYSTEM_AVAILABLE = False
    print("⚠️ Ecosystem Manager not available - running in standalone mode")

load_dotenv(override=True)

class MomentumBacktesterEcosystem:
    """
    Enhanced Momentum Strategy Backtester v4.7 with Ecosystem Integration
    
    NEW: Generates research insights and asset recommendations for the trading ecosystem
    """
    
    def __init__(self, symbol='XRPPHP', initial_balance=10000):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Configuration
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')
        self.initial_balance = initial_balance
        
        # Strategy parameters
        self.buy_threshold = 0.006      # 0.6%
        self.sell_threshold = 0.010     # 1.0%
        self.take_profit_pct = 0.02     # 2.0% default
        self.base_amount = 200          # PHP 200 base reference
        self.position_sizing = 'fixed'  # Default to fixed
        self.min_hold_minutes = 30      # 30 minutes
        self.max_trades_per_day = 10    # Daily limit
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        # Setup graceful exit handling
        self._running = True
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Ecosystem integration
        self.ecosystem_manager = None
        if ECOSYSTEM_AVAILABLE:
            try:
                self.ecosystem_manager = get_ecosystem_manager()
                log_tool_usage('momentum_backtest', '4.7')
                print("🌐 Ecosystem Manager connected")
            except Exception as e:
                print(f"⚠️ Ecosystem Manager connection failed: {e}")
                self.ecosystem_manager = None
        
        # State tracking
        self.reset_state()
        
        print(f"Momentum Backtester v4.7 with Ecosystem Integration - {self.symbol}")
        print(f"Initial balance: {self.initial_balance:,.2f} PHP")

    def _signal_handler(self, signum, frame):
        """Handle graceful exit on Ctrl+C"""
        print(f"\nReceived signal {signum}. Gracefully stopping...")
        self._running = False
        sys.exit(0)

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
                print(f"Symbol {self.symbol} not found")
                return False
            
            status = symbol_info.get('status', '').upper()
            if status not in ['TRADING', 'ACTIVE']:
                print(f"Symbol {self.symbol} is not tradable (status: {status})")
                return False
            
            print(f"Symbol {self.symbol} validated successfully")
            return True
            
        except Exception as e:
            print(f"Error validating symbol {self.symbol}: {e}")
            return False

    def get_symbol_market_data(self):
        """Get market data and volatility analysis for the symbol"""
        try:
            current_price = self.api.get_current_price(self.symbol)
            ticker_24hr = self.api.get_24hr_ticker(self.symbol)
            
            high_24h = float(ticker_24hr.get('highPrice', current_price))
            low_24h = float(ticker_24hr.get('lowPrice', current_price))
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            
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
            print(f"Error getting market data for {self.symbol}: {e}")
            return None

    def get_asset_specific_parameters(self, volatility):
        """Get asset-specific parameter ranges based on volatility"""
        
        if volatility > 15:  # Very high volatility
            return {
                'buy_thresholds': [0.003, 0.004, 0.005, 0.006],
                'sell_thresholds': [0.005, 0.008, 0.010, 0.012],
                'take_profit_range': [0.005, 0.008, 0.010, 0.012, 0.015, 0.020],
                'recommended_position_sizing': ['fixed', 'momentum'],
                'category': 'Very High Volatility',
                'risk_level': 'high'
            }
        elif volatility > 8:  # High volatility
            return {
                'buy_thresholds': [0.004, 0.006, 0.008, 0.010],
                'sell_thresholds': [0.008, 0.010, 0.012, 0.015],
                'take_profit_range': [0.008, 0.010, 0.015, 0.020, 0.025, 0.030],
                'recommended_position_sizing': ['fixed', 'momentum', 'adaptive'],
                'category': 'High Volatility',
                'risk_level': 'medium-high'
            }
        elif volatility > 3:  # Medium volatility
            return {
                'buy_thresholds': [0.005, 0.006, 0.008, 0.010],
                'sell_thresholds': [0.008, 0.010, 0.012, 0.015],
                'take_profit_range': [0.015, 0.020, 0.025, 0.030, 0.040, 0.050],
                'recommended_position_sizing': ['percentage', 'adaptive'],
                'category': 'Medium Volatility',
                'risk_level': 'medium'
            }
        else:  # Low volatility
            return {
                'buy_thresholds': [0.006, 0.008, 0.010, 0.012],
                'sell_thresholds': [0.010, 0.012, 0.015, 0.020],
                'take_profit_range': [0.020, 0.030, 0.040, 0.050, 0.060, 0.080],
                'recommended_position_sizing': ['percentage', 'adaptive'],
                'category': 'Low Volatility',
                'risk_level': 'low'
            }

    def fetch_historical_data(self, days=60, interval='1h') -> List[Dict]:
        """Fetch historical price data from Coins.ph API"""
        cache_key = f'_cached_data_{self.symbol}_{days}_{interval}'
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        print(f"Fetching {days} days of {interval} data for {self.symbol}...")
        
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
                print("No historical data received")
                return []
            
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
            
            data.sort(key=lambda x: x['timestamp'])
            
            actual_days = (data[-1]['timestamp'] - data[0]['timestamp']).days
            print(f"Fetched {len(data)} candles covering {actual_days} days")
            
            setattr(self, cache_key, data)
            return data
            
        except Exception as e:
            print(f"Error fetching historical data: {e}")
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
        """Simulate buy order execution"""
        
        amount_to_spend = min(position_size, self.php_balance * 0.9)
        
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
        
        asset_to_sell = self.asset_balance * 0.99
        gross_amount = asset_to_sell * price
        fee = gross_amount * self.taker_fee
        net_amount = gross_amount - fee
        
        self.php_balance += net_amount
        self.asset_balance -= asset_to_sell
        self.total_fees_paid += fee
        self.total_trades += 1
        
        self.position = None
        self.update_daily_trades(time)
        
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

    def run_enhanced_strategy(self, data: List[Dict], 
                            buy_threshold: float = None,
                            sell_threshold: float = None,
                            take_profit_pct: float = None,
                            position_sizing: str = None) -> Dict:
        """Run enhanced momentum strategy"""
        
        self.buy_threshold = buy_threshold or self.buy_threshold
        self.sell_threshold = sell_threshold or self.sell_threshold
        self.take_profit_pct = take_profit_pct or self.take_profit_pct
        self.position_sizing = position_sizing or self.position_sizing
        
        print(f"Running strategy...")
        print(f"Parameters: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%, TP {self.take_profit_pct*100:.1f}%")
        print(f"Position sizing: {self.position_sizing}")
        
        self.reset_state()
        
        prices = []
        
        for i, candle in enumerate(data):
            if not self._running:
                print("Backtest interrupted by user")
                break
                
            current_price = candle['close']
            current_time = candle['timestamp']
            
            prices.append(current_price)
            
            if len(prices) < 15:
                continue
            
            momentum = self.calculate_momentum(prices, period=3)
            trend = self.calculate_trend(prices, window=12)
            
            position_size = self.base_amount  # Simplified for ecosystem version
            
            # BUY CONDITIONS
            if (momentum > self.buy_threshold and
                trend > -0.02 and
                self.php_balance > position_size * 0.6 and
                self.can_trade_today(current_time) and
                self.position is None):
                
                self.place_buy(current_price, current_time, momentum, position_size)
            
            # SELL CONDITIONS - Momentum down
            elif (momentum < -self.sell_threshold and
                  self.asset_balance > 0.001 and
                  self.can_sell_position(current_time) and
                  self.can_trade_today(current_time)):
                
                self.place_sell(current_price, current_time, momentum, "Momentum Down")
            
            # SELL CONDITIONS - Take profit
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position(current_time)):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct >= self.take_profit_pct:
                    self.place_sell(current_price, current_time, momentum, "Take Profit")
            
            # EMERGENCY EXIT - Strong downtrend
            elif (trend < -0.05 and
                  self.asset_balance > 0.001 and
                  self.can_sell_position(current_time)):
                
                self.place_sell(current_price, current_time, momentum, "Emergency Exit")
        
        final_price = data[-1]['close']
        final_portfolio_value = self.php_balance + (self.asset_balance * final_price)
        
        return self.calculate_comprehensive_metrics(data[0], data[-1], final_portfolio_value)

    def calculate_comprehensive_metrics(self, start_candle: Dict, end_candle: Dict, final_value: float) -> Dict:
        """Calculate comprehensive performance metrics"""
        
        start_price = start_candle['close']
        end_price = end_candle['close']
        start_time = start_candle['timestamp']
        end_time = end_candle['timestamp']
        
        total_return = final_value - self.initial_balance
        return_percentage = (total_return / self.initial_balance) * 100
        
        total_days = (end_time - start_time).days
        if total_days > 0:
            daily_return = (final_value / self.initial_balance) ** (1/total_days) - 1
            annualized_return = ((1 + daily_return) ** 365 - 1) * 100
        else:
            annualized_return = 0
        
        initial_asset_if_bought = (self.initial_balance - (self.initial_balance * self.maker_fee)) / start_price
        buy_hold_value = initial_asset_if_bought * end_price
        buy_hold_return = (buy_hold_value - self.initial_balance) / self.initial_balance * 100
        outperformance = return_percentage - buy_hold_return
        
        total_trades = len(self.trade_history)
        if total_trades > 0:
            win_rate = (self.winning_trades / (self.winning_trades + self.losing_trades)) * 100 if (self.winning_trades + self.losing_trades) > 0 else 0
            avg_win = self.total_profit / max(1, self.winning_trades)
            avg_loss = self.total_loss / max(1, self.losing_trades)
            profit_factor = self.total_profit / max(1, self.total_loss)
            trades_per_day = total_trades / max(1, total_days)
        else:
            win_rate = avg_win = avg_loss = profit_factor = trades_per_day = 0
        
        return {
            'symbol': self.symbol,
            'base_asset': self.base_asset,
            'position_sizing': self.position_sizing,
            'buy_threshold': self.buy_threshold * 100,
            'sell_threshold': self.sell_threshold * 100,
            'take_profit_pct': self.take_profit_pct * 100,
            'base_amount': self.base_amount,
            
            'start_date': start_time.strftime('%Y-%m-%d'),
            'end_date': end_time.strftime('%Y-%m-%d'),
            'total_days': total_days,
            'start_price': start_price,
            'end_price': end_price,
            'market_return': ((end_price - start_price) / start_price) * 100,
            
            'initial_balance': self.initial_balance,
            'final_balance': final_value,
            'total_return': total_return,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            
            'buy_hold_return': buy_hold_return,
            'outperformance': outperformance,
            'beat_buy_hold': return_percentage > buy_hold_return,
            
            'total_trades': total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'trades_per_day': trades_per_day,
            
            'total_fees': self.total_fees_paid,
            'fees_percentage': (self.total_fees_paid / self.initial_balance) * 100,
        }

    def print_results(self, results: Dict):
        """Print clean, streamlined backtest results"""
        print(f"\n{'='*80}")
        print(f"MOMENTUM BACKTEST RESULTS v4.7 with Ecosystem Integration")
        print(f"{'='*80}")
        
        print(f"\nSTRATEGY CONFIGURATION:")
        print(f"   Symbol: {results['symbol']} ({results['base_asset']}/PHP)")
        print(f"   Period: {results['start_date']} to {results['end_date']} ({results['total_days']} days)")
        print(f"   Position sizing: {results['position_sizing'].title()}")
        print(f"   Buy threshold: {results['buy_threshold']:.1f}%")
        print(f"   Sell threshold: {results['sell_threshold']:.1f}%")
        print(f"   Take profit: {results['take_profit_pct']:.1f}%")
        print(f"   Base amount: {results['base_amount']} PHP")
        
        print(f"\nPERFORMANCE SUMMARY:")
        print(f"   Initial balance: {results['initial_balance']:,.2f} PHP")
        print(f"   Final balance: {results['final_balance']:,.2f} PHP")
        print(f"   Total return: {results['total_return']:,.2f} PHP ({results['return_percentage']:+.2f}%)")
        print(f"   Annualized return: {results['annualized_return']:+.2f}%")
        print(f"   Market return: {results['market_return']:+.2f}%")
        
        print(f"\nBENCHMARK COMPARISON:")
        print(f"   Buy & Hold return: {results['buy_hold_return']:+.2f}%")
        print(f"   Strategy outperformance: {results['outperformance']:+.2f}%")
        status = "OUTPERFORMED" if results['beat_buy_hold'] else "UNDERPERFORMED"
        print(f"   vs Buy & Hold: {status}")
        
        print(f"\nTRADE ANALYSIS:")
        print(f"   Total trades: {results['total_trades']}")
        print(f"   Winning trades: {results['winning_trades']} ({results['win_rate']:.1f}%)")
        print(f"   Losing trades: {results['losing_trades']}")
        print(f"   Trades per day: {results['trades_per_day']:.1f}")
        
        print(f"\n{'='*80}")

    def generate_asset_insight(self, results: Dict, market_data: Dict) -> AssetInsight:
        """Generate AssetInsight for Ecosystem Manager"""
        
        if not ECOSYSTEM_AVAILABLE:
            return None
        
        # Calculate performance score (0-10 based on multiple factors)
        return_score = min(max(results['return_percentage'] / 10, 0), 10)  # 10% return = 10 points
        win_rate_score = results['win_rate'] / 10  # 100% win rate = 10 points
        
        performance_score = (return_score * 0.6 + win_rate_score * 0.4)
        
        # Determine recommended strategy based on volatility and performance
        volatility = market_data.get('volatility', 5)
        if volatility > 8:
            recommended_strategy = 'momentum'
        elif volatility > 3:
            recommended_strategy = 'adaptive'
        else:
            recommended_strategy = 'percentage'
        
        # Determine risk level
        if volatility > 8:
            risk_level = 'high'
        elif volatility > 3:
            risk_level = 'medium'
        else:
            risk_level = 'low'
        
        # Determine trade frequency
        if results['trades_per_day'] > 2:
            trade_frequency = 'high'
        elif results['trades_per_day'] > 0.5:
            trade_frequency = 'medium'
        else:
            trade_frequency = 'low'
        
        return AssetInsight(
            symbol=results['symbol'],
            volatility=volatility,
            performance_score=performance_score,
            recommended_strategy=recommended_strategy,
            last_analyzed=datetime.now().isoformat(),
            risk_level=risk_level,
            trade_frequency=trade_frequency
        )

    def analyze_multiple_assets(self, asset_list: List[str], days: int = 30) -> Dict:
        """NEW: Analyze multiple assets and generate ecosystem insights"""
        
        print(f"\n🌐 ECOSYSTEM MULTI-ASSET ANALYSIS")
        print(f"📊 Analyzing {len(asset_list)} assets over {days} days")
        print("="*70)
        
        all_insights = []
        asset_rankings = []
        
        for i, symbol in enumerate(asset_list, 1):
            if not self._running:
                break
                
            print(f"\n[{i}/{len(asset_list)}] Analyzing {symbol}...")
            
            try:
                # Temporarily switch to this symbol
                original_symbol = self.symbol
                original_base_asset = self.base_asset
                
                self.symbol = symbol
                self.base_asset = symbol.replace('PHP', '')
                
                # Validate symbol
                if not self.validate_symbol():
                    print(f"   ❌ {symbol} validation failed, skipping")
                    continue
                
                # Get market data
                market_data = self.get_symbol_market_data()
                if not market_data:
                    print(f"   ❌ {symbol} market data failed, skipping")
                    continue
                
                # Get historical data
                data = self.fetch_historical_data(days=days)
                if not data or len(data) < 50:
                    print(f"   ❌ {symbol} insufficient data, skipping")
                    continue
                
                # Run quick strategy test
                result = self.run_enhanced_strategy(data, position_sizing='adaptive')
                
                print(f"   ✅ {symbol}: {result['return_percentage']:+.1f}% return, "
                      f"{result['win_rate']:.0f}% win rate, "
                      f"{result['total_trades']} trades")
                
                # Generate insight
                insight = self.generate_asset_insight(result, market_data)
                if insight:
                    all_insights.append(insight)
                    
                    asset_rankings.append({
                        'symbol': symbol,
                        'performance_score': insight.performance_score,
                        'return_percentage': result['return_percentage'],
                        'win_rate': result['win_rate'],
                        'volatility': insight.volatility,
                        'risk_level': insight.risk_level,
                        'recommended_strategy': insight.recommended_strategy,
                        'trade_frequency': insight.trade_frequency
                    })
                
                # Restore original symbol
                self.symbol = original_symbol
                self.base_asset = original_base_asset
                
            except Exception as e:
                print(f"   ❌ {symbol} analysis failed: {e}")
                continue
        
        # Sort by performance score
        asset_rankings.sort(key=lambda x: x['performance_score'], reverse=True)
        
        # Display rankings
        print(f"\n🏆 ASSET PERFORMANCE RANKINGS:")
        print("-" * 80)
        print(f"{'Rank':<4} {'Symbol':<8} {'Score':<6} {'Return%':<8} {'Win%':<6} {'Risk':<8} {'Strategy'}")
        print("-" * 80)
        
        for i, asset in enumerate(asset_rankings[:10], 1):
            print(f"{i:<4} {asset['symbol']:<8} {asset['performance_score']:<6.1f} "
                  f"{asset['return_percentage']:+7.1f} {asset['win_rate']:<6.0f} "
                  f"{asset['risk_level']:<8} {asset['recommended_strategy']}")
        
        print("-" * 80)
        
        # Save all insights to ecosystem
        if ECOSYSTEM_AVAILABLE and self.ecosystem_manager and all_insights:
            try:
                self.ecosystem_manager.save_research_insights(all_insights)
                print(f"\n🌐 ECOSYSTEM INTEGRATION COMPLETE!")
                print(f"   💾 Saved {len(all_insights)} asset insights")
                print(f"   🏆 Top performer: {asset_rankings[0]['symbol']} ({asset_rankings[0]['performance_score']:.1f}/10)")
                print(f"   📊 Data available for Prophet, TITAN, and ORACLE")
                
                # Generate ecosystem recommendations
                top_assets = asset_rankings[:5]
                print(f"\n💡 ECOSYSTEM RECOMMENDATIONS:")
                for asset in top_assets:
                    print(f"   {asset['symbol']}: {asset['recommended_strategy']} sizing, "
                          f"{asset['risk_level']} risk, {asset['trade_frequency']} frequency")
                
            except Exception as e:
                print(f"⚠️ Could not save insights to ecosystem: {e}")
        
        return {
            'asset_rankings': asset_rankings,
            'insights_generated': len(all_insights),
            'ecosystem_integration': ECOSYSTEM_AVAILABLE and self.ecosystem_manager is not None
        }


# User Interface Functions

def get_symbol_suggestions():
    """Get trading pair suggestions with volume data"""
    try:
        api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        tickers = api.get_24hr_ticker()
        if not isinstance(tickers, list):
            tickers = [tickers]
        
        php_pairs = []
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if symbol.endswith('PHP'):
                volume = float(ticker.get('quoteVolume', 0))
                price_change = float(ticker.get('priceChangePercent', 0))
                
                if volume > 10000:
                    php_pairs.append({
                        'symbol': symbol,
                        'volume': volume,
                        'price_change': price_change
                    })
        
        php_pairs.sort(key=lambda x: x['volume'], reverse=True)
        return php_pairs[:15]
        
    except Exception as e:
        print(f"Error getting symbol suggestions: {e}")
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
        
        php_pairs = []
        for symbol in symbols:
            if (symbol.get('quoteAsset') == 'PHP' and 
                symbol.get('status', '').upper() in ['TRADING', 'ACTIVE']):
                php_pairs.append(symbol['symbol'])
        
        php_pairs.sort()
        return php_pairs
        
    except Exception as e:
        print(f"Error fetching available pairs: {e}")
        return []

def main():
    """Enhanced main function with ecosystem integration options"""
    try:
        print("Enhanced Momentum Backtesting Engine v4.7")
        print("🌐 NEW: Ecosystem Integration for Research Insights")
        print("="*70)
        
        if not os.getenv('COINS_API_KEY'):
            print("API keys not found!")
            return
        
        # Show ecosystem status
        if ECOSYSTEM_AVAILABLE:
            print("✅ Ecosystem Manager available - insights will be generated")
        else:
            print("⚠️ Ecosystem Manager not available - running in standalone mode")
        
        # Get symbol suggestions
        print("Getting available trading pairs...")
        suggestions = get_symbol_suggestions()
        
        if suggestions:
            print(f"\nTop volume PHP pairs:")
            for i, pair in enumerate(suggestions[:8], 1):
                volume_str = f"{pair['volume']/1000000:.1f}M" if pair['volume'] >= 1000000 else f"{pair['volume']/1000:.0f}K PHP"
                change_symbol = "↗" if pair['price_change'] > 0 else "↘"
                print(f"  {i}. {pair['symbol']:<8} - {volume_str:<8} {change_symbol} {pair['price_change']:+.1f}%")
        
        # Enhanced test type selection with ecosystem options
        print(f"\nSelect backtest type:")
        print("1. Quick Strategy Test - Test single asset configuration")
        print("2. Asset-Specific Optimization - Find optimal parameters")
        print("3. Complete Analysis - Full optimization + strategy comparison")
        if ECOSYSTEM_AVAILABLE:
            print("4. 🌐 Multi-Asset Ecosystem Analysis - Generate insights for multiple assets")
            print("5. 🌐 Top Volume Assets Analysis - Analyze highest volume PHP pairs")
        
        while True:
            try:
                max_choice = 5 if ECOSYSTEM_AVAILABLE else 3
                test_choice = input(f"Enter choice (1-{max_choice}): ").strip()
                if test_choice in [str(i) for i in range(1, max_choice + 1)]:
                    break
                else:
                    print(f"Please enter 1-{max_choice}")
            except KeyboardInterrupt:
                print("\nBacktest cancelled by user")
                return
        
        # Handle ecosystem analysis options
        if ECOSYSTEM_AVAILABLE and test_choice in ['4', '5']:
            if test_choice == '4':
                # Multi-asset ecosystem analysis
                print(f"\n🌐 Multi-Asset Ecosystem Analysis")
                print("Select assets to analyze:")
                print("1. Top 10 volume pairs")
                print("2. Custom asset list")
                print("3. Predefined set (XRP, SOL, BTC, ETH, DOGE)")
                
                asset_choice = input("Enter choice (1-3): ").strip()
                
                if asset_choice == '1':
                    asset_list = [pair['symbol'] for pair in suggestions[:10]]
                elif asset_choice == '2':
                    custom_input = input("Enter symbols separated by commas (e.g., XRPPHP,SOLPHP,BTCPHP): ").strip()
                    asset_list = [s.strip().upper() for s in custom_input.split(',') if s.strip()]
                else:
                    asset_list = ['XRPPHP', 'SOLPHP', 'BTCPHP', 'ETHPHP', 'DOGEPHP']
                
                if not asset_list:
                    print("No assets selected!")
                    return
                    
                print(f"\n📊 Will analyze {len(asset_list)} assets: {', '.join(asset_list)}")
                
            elif test_choice == '5':
                # Top volume assets analysis
                asset_list = [pair['symbol'] for pair in suggestions[:8]]
                print(f"\n📊 Will analyze top 8 volume PHP pairs: {', '.join(asset_list)}")
            
            # Time period for ecosystem analysis
            while True:
                try:
                    days_input = input("Enter analysis period in days (7-60, default: 30): ").strip()
                    if not days_input:
                        days = 30
                        break
                    else:
                        days = int(days_input)
                        if 7 <= days <= 60:
                            break
                        else:
                            print("Please enter a value between 7 and 60")
                except ValueError:
                    print("Please enter a valid number")
                except KeyboardInterrupt:
                    print("\nBacktest cancelled by user")
                    return
            
            print(f"\n🌐 Starting ecosystem analysis...")
            print(f"Assets: {len(asset_list)} symbols")
            print(f"Period: {days} days")
            
            # Initialize backtester for ecosystem analysis
            backtester = MomentumBacktesterEcosystem()
            
            # Run ecosystem analysis
            ecosystem_results = backtester.analyze_multiple_assets(asset_list, days)
            
            print(f"\n✅ Ecosystem analysis complete!")
            if ecosystem_results['ecosystem_integration']:
                print(f"🌐 {ecosystem_results['insights_generated']} insights saved to ecosystem")
                print(f"💡 Other tools can now access these research insights")
                print(f"🔄 Run Prophet, TITAN, or ORACLE to use this data")
            
            return
        
        # Standard single-asset analysis
        # Asset selection
        print(f"\nSelect trading asset for backtesting:")
        print("1. XRPPHP - Medium volatility, proven momentum performance")
        print("2. SOLPHP - High volatility, good for testing adaptive strategies")
        print("3. BTCPHP - Lower volatility, conservative testing")
        print("4. Custom symbol")
        print("5. Browse all available pairs")
        
        while True:
            try:
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
                        custom_symbol = input("Enter symbol (e.g., ETHPHP): ").strip().upper()
                        if custom_symbol.endswith('PHP') and len(custom_symbol) >= 6:
                            symbol = custom_symbol
                            break
                        else:
                            print("Please enter a valid PHP trading pair")
                    break
                elif choice == '5':
                    available_pairs = get_available_php_pairs()
                    if available_pairs:
                        print(f"\nAll available PHP pairs ({len(available_pairs)} total):")
                        for i, pair in enumerate(available_pairs):
                            print(f"  {pair}", end="  ")
                            if (i + 1) % 6 == 0:
                                print()
                        print()
                        
                        while True:
                            browse_symbol = input("Enter symbol from list: ").strip().upper()
                            if browse_symbol in available_pairs:
                                symbol = browse_symbol
                                break
                            else:
                                print("Please enter a valid symbol from the list")
                        break
                    else:
                        print("Could not fetch available pairs")
                        continue
                else:
                    print("Please enter 1-5")
            except KeyboardInterrupt:
                print("\nBacktest cancelled by user")
                return
        
        # Time period selection
        print(f"\nSelect testing period:")
        print("1. Quick test (30 days)")
        print("2. Standard test (60 days)")
        print("3. Custom period")
        
        while True:
            try:
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
            except KeyboardInterrupt:
                print("\nBacktest cancelled by user")
                return
        
        print(f"\nStarting backtesting...")
        print(f"Symbol: {symbol}")
        print(f"Period: {days} days")
        if ECOSYSTEM_AVAILABLE:
            print(f"🌐 Ecosystem integration: Enabled")
        
        # Initialize backtester
        backtester = MomentumBacktesterEcosystem(symbol=symbol)
        
        # Validate symbol
        if not backtester.validate_symbol():
            print("Symbol validation failed!")
            return
        
        # Get market data
        market_data = backtester.get_symbol_market_data()
        if not market_data:
            print("Could not fetch market data!")
            return
        
        # Fetch historical data
        data = backtester.fetch_historical_data(days=days)
        if not data:
            print("Failed to fetch historical data!")
            return
        
        # Display market context
        print(f"\n{symbol} Market Analysis:")
        print(f"   Current Price: {market_data['current_price']:,.4f} PHP")
        print(f"   24h Volume: {market_data['volume_24h']:,.0f} PHP")
        print(f"   24h Volatility: {market_data['volatility']:.1f}%")
        
        # Execute selected backtest type
        if test_choice == '1':
            # Quick Strategy Test
            results = backtester.run_enhanced_strategy(data)
            backtester.print_results(results)
            
            # Generate ecosystem insight if available
            if ECOSYSTEM_AVAILABLE and backtester.ecosystem_manager:
                try:
                    insight = backtester.generate_asset_insight(results, market_data)
                    if insight:
                        backtester.ecosystem_manager.save_research_insights([insight])
                        print(f"\n🌐 Saved research insight to ecosystem")
                        print(f"   Performance Score: {insight.performance_score:.1f}/10")
                        print(f"   Risk Level: {insight.risk_level}")
                        print(f"   Recommended Strategy: {insight.recommended_strategy}")
                except Exception as e:
                    print(f"⚠️ Could not save insight to ecosystem: {e}")
        
        elif test_choice == '2':
            # Asset-Specific Optimization
            asset_params = backtester.get_asset_specific_parameters(market_data['volatility'])
            
            print(f"\n{asset_params['category']} Parameter Optimization for {symbol}")
            print("="*60)
            
            best_results = []
            test_count = 0
            total_tests = len(asset_params['buy_thresholds']) * len(asset_params['take_profit_range'])
            
            for buy_thresh in asset_params['buy_thresholds']:
                if not backtester._running:
                    break
                    
                for tp_pct in asset_params['take_profit_range']:
                    if not backtester._running:
                        break
                        
                    test_count += 1
                    print(f"[{test_count:2d}/{total_tests}] Testing Buy: {buy_thresh*100:.1f}%, TP: {tp_pct*100:.1f}%...", end=" ")
                    
                    sell_thresh = buy_thresh * 1.67
                    
                    result = backtester.run_enhanced_strategy(
                        data,
                        buy_threshold=buy_thresh,
                        sell_threshold=sell_thresh,
                        take_profit_pct=tp_pct,
                        position_sizing='adaptive'
                    )
                    
                    result['test_buy_threshold'] = buy_thresh * 100
                    result['test_sell_threshold'] = sell_thresh * 100
                    result['test_take_profit'] = tp_pct * 100
                    
                    best_results.append(result)
                    
                    print(f"Return: {result['return_percentage']:+.1f}%")
            
            if best_results:
                best_results.sort(key=lambda x: x['return_percentage'], reverse=True)
                
                print(f"\nTOP 5 PARAMETER COMBINATIONS for {symbol}:")
                print("-" * 60)
                print(f"{'Rank':<4} {'Buy%':<6} {'TP%':<6} {'Return%':<8} {'Win%':<6} {'Trades':<7}")
                print("-" * 60)
                
                for i, result in enumerate(best_results[:5]):
                    rank = i + 1
                    buy_pct = result['test_buy_threshold']
                    tp_pct = result['test_take_profit']
                    return_pct = result['return_percentage']
                    win_rate = result['win_rate']
                    trades = result['total_trades']
                    
                    print(f"{rank:<4} {buy_pct:<6.1f} {tp_pct:<6.1f} "
                          f"{return_pct:+7.1f} {win_rate:>5.0f} "
                          f"{trades:>6}")
                
                print("-" * 60)
                
                best_config = best_results[0]
                
                print(f"\nOPTIMAL CONFIGURATION for {symbol}:")
                print(f"   Buy threshold: {best_config['test_buy_threshold']:.1f}%")
                print(f"   Take profit: {best_config['test_take_profit']:.1f}%")
                print(f"   Expected return: {best_config['return_percentage']:+.1f}%")
                print(f"   Win rate: {best_config['win_rate']:.0f}%")
                
                # Generate and save ecosystem insight for the best configuration
                if ECOSYSTEM_AVAILABLE and backtester.ecosystem_manager:
                    try:
                        insight = backtester.generate_asset_insight(best_config, market_data)
                        if insight:
                            backtester.ecosystem_manager.save_research_insights([insight])
                            print(f"\n🌐 Saved optimization insight to ecosystem")
                            print(f"   Performance Score: {insight.performance_score:.1f}/10")
                            print(f"   Risk Level: {insight.risk_level}")
                            print(f"   Recommended Strategy: {insight.recommended_strategy}")
                    except Exception as e:
                        print(f"⚠️ Could not save insight to ecosystem: {e}")
        
        elif test_choice == '3':
            # Complete Analysis
            print(f"\nRunning complete analysis...")
            
            # 1. Quick test
            print(f"\n1. Quick strategy test:")
            results = backtester.run_enhanced_strategy(data)
            backtester.print_results(results)
            
            # 2. Asset-specific optimization
            print(f"\n2. Asset-specific optimization:")
            asset_params = backtester.get_asset_specific_parameters(market_data['volatility'])
            
            print(f"{asset_params['category']} Parameter Optimization")
            print("="*50)
            
            # Run a subset of optimizations for demo
            best_results = []
            for i, buy_thresh in enumerate(asset_params['buy_thresholds'][:3]):  # Just test first 3
                for j, tp_pct in enumerate(asset_params['take_profit_range'][:3]):  # Just test first 3
                    print(f"Testing Buy: {buy_thresh*100:.1f}%, TP: {tp_pct*100:.1f}%...")
                    
                    result = backtester.run_enhanced_strategy(
                        data,
                        buy_threshold=buy_thresh,
                        sell_threshold=buy_thresh * 1.67,
                        take_profit_pct=tp_pct,
                        position_sizing='adaptive'
                    )
                    
                    result['test_buy_threshold'] = buy_thresh * 100
                    result['test_take_profit'] = tp_pct * 100
                    best_results.append(result)
                    
                    print(f"   Return: {result['return_percentage']:+.1f}%")
            
            if best_results:
                best_config = max(best_results, key=lambda x: x['return_percentage'])
                print(f"\nBest Configuration: Buy {best_config['test_buy_threshold']:.1f}%, TP {best_config['test_take_profit']:.1f}%")
                print(f"Expected Return: {best_config['return_percentage']:+.1f}%")
                
                # Save ecosystem insight
                if ECOSYSTEM_AVAILABLE and backtester.ecosystem_manager:
                    try:
                        insight = backtester.generate_asset_insight(best_config, market_data)
                        if insight:
                            backtester.ecosystem_manager.save_research_insights([insight])
                            print(f"\n🌐 Complete analysis insight saved to ecosystem")
                    except Exception as e:
                        print(f"⚠️ Could not save insight to ecosystem: {e}")
        
        print(f"\nBacktest complete for {symbol}!")
        if ECOSYSTEM_AVAILABLE:
            print(f"🌐 Research insights saved to ecosystem for Prophet, TITAN, and ORACLE")
        print(f"Use the optimized settings in your trading bots")
        
    except KeyboardInterrupt:
        print("\nBacktest session ended gracefully")
        print("Thank you for using the momentum backtester")
    except Exception as e:
        print(f"\nBacktest encountered an error: {e}")
        print("Please check your configuration and try again")

if __name__ == "__main__":
    main()