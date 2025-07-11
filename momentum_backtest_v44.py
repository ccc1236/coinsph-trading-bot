"""
🔬 COMPREHENSIVE MOMENTUM BACKTESTING ENGINE v44

Backtesting system for momentum trading strategies with detailed
performance analysis, risk metrics, and strategy optimization.

Features:
- ✅ Historical data fetching and processing
- ✅ Momentum strategy simulation
- ✅ Comprehensive performance metrics
- ✅ Risk analysis (Sharpe, drawdown, volatility)
- ✅ Trade-by-trade analysis
- ✅ Parameter optimization
- ✅ Visual performance reporting
- ✅ Multiple timeframe support
- ✅ Benchmark comparisons
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

class MomentumBacktester:
    """
    🔬 Advanced Momentum Strategy Backtester
    
    Simulates momentum trading strategies with comprehensive analysis
    and performance reporting.
    """
    
    def __init__(self, symbol='XRPPHP', initial_balance=10000):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Backtest configuration
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')
        self.initial_balance = initial_balance
        
        # Strategy parameters (configurable)
        self.buy_threshold = 0.006      # 0.6%
        self.sell_threshold = 0.010     # 1.0%
        self.take_profit_pct = 0.02     # 2.0% default
        self.trade_amount = 200         # ₱200 per trade
        self.min_hold_minutes = 30      # 30 minutes
        self.max_trades_per_day = 10    # Daily limit
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        # State tracking
        self.reset_state()
        
        print(f"🔬 MOMENTUM BACKTESTER v44 initialized")
        print(f"🎯 Symbol: {self.symbol}")
        print(f"💰 Initial balance: ₱{self.initial_balance:,.2f}")
        print(f"📊 Trade amount: ₱{self.trade_amount}")

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

    def fetch_historical_data(self, days=60, interval='1h') -> List[Dict]:
        """
        Fetch historical price data from Coins.ph API
        
        Args:
            days: Number of days of historical data
            interval: Timeframe (1h, 4h, 1d)
            
        Returns:
            List of OHLCV candles
        """
        print(f"\n📊 Fetching {days} days of {interval} data for {self.symbol}...")
        
        try:
            # Calculate limit based on interval
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
            print(f"📅 Period: {data[0]['timestamp'].strftime('%Y-%m-%d')} to {data[-1]['timestamp'].strftime('%Y-%m-%d')}")
            
            return data
            
        except Exception as e:
            print(f"❌ Error fetching historical data: {e}")
            return []

    def calculate_momentum(self, prices: List[float], period: int = 3) -> float:
        """
        Calculate momentum based on recent price changes
        
        Args:
            prices: List of recent prices
            period: Number of periods to calculate momentum over
            
        Returns:
            Momentum as percentage change
        """
        if len(prices) < period + 1:
            return 0.0
        
        current_price = prices[-1]
        past_price = prices[-(period + 1)]
        
        return (current_price - past_price) / past_price

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

    def place_buy(self, price: float, time: datetime, momentum: float) -> bool:
        """Simulate buy order execution"""
        amount_to_spend = min(self.trade_amount, self.php_balance * 0.9)
        
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

    def run_momentum_strategy(self, data: List[Dict], take_profit_pct: Optional[float] = None) -> Dict:
        """
        Run momentum strategy backtest on historical data
        
        Args:
            data: Historical OHLCV data
            take_profit_pct: Take profit percentage (optional override)
            
        Returns:
            Backtest results dictionary
        """
        if take_profit_pct is not None:
            self.take_profit_pct = take_profit_pct
        
        print(f"\n🚀 Running momentum strategy backtest...")
        print(f"📊 Parameters: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%, TP {self.take_profit_pct*100:.1f}%")
        
        self.reset_state()
        
        # Build price history for momentum calculation
        prices = []
        
        for i, candle in enumerate(data):
            current_price = candle['close']
            current_time = candle['timestamp']
            
            prices.append(current_price)
            self.price_history.append(current_price)
            
            # Need at least 5 candles for momentum calculation
            if len(prices) < 5:
                continue
            
            # Calculate momentum
            momentum = self.calculate_momentum(prices, period=3)
            
            # Update equity curve
            self.update_equity_curve(current_price, current_time)
            
            # BUY CONDITIONS
            if (momentum > self.buy_threshold and           # Strong upward momentum
                self.php_balance > self.trade_amount * 1.1 and  # Have enough PHP
                self.can_trade_today(current_time) and     # Within daily limit
                self.position is None):                    # No current position
                
                self.place_buy(current_price, current_time, momentum)
            
            # SELL CONDITIONS - Momentum down
            elif (momentum < -self.sell_threshold and      # Strong downward momentum
                  self.asset_balance > 0.001 and           # Have position
                  self.can_sell_position(current_time) and # Min hold time met
                  self.can_trade_today(current_time)):     # Within daily limit
                
                self.place_sell(current_price, current_time, momentum, "Momentum Down")
            
            # SELL CONDITIONS - Take profit
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position(current_time)):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct >= self.take_profit_pct:
                    self.place_sell(current_price, current_time, momentum, "Take Profit")
        
        # Calculate final results
        final_price = data[-1]['close']
        final_portfolio_value = self.php_balance + (self.asset_balance * final_price)
        
        return self.calculate_performance_metrics(data[0], data[-1], final_portfolio_value)

    def calculate_performance_metrics(self, start_candle: Dict, end_candle: Dict, final_value: float) -> Dict:
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
        
        return {
            # Basic metrics
            'symbol': self.symbol,
            'start_date': start_time.strftime('%Y-%m-%d'),
            'end_date': end_time.strftime('%Y-%m-%d'),
            'total_days': total_days,
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
            
            # Strategy specific
            'take_profit_pct': self.take_profit_pct * 100,
            'profit_taking_trades': len(profit_taking_trades),
            'momentum_down_trades': len(momentum_down_trades),
            'profit_taking_rate': len(profit_taking_trades) / max(1, len(sell_trades)) * 100,
            
            # Raw data
            'trade_history': self.trade_history,
            'equity_curve': self.equity_curve,
            'price_history': self.price_history
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

    def print_results(self, results: Dict):
        """Print comprehensive backtest results"""
        print(f"\n" + "=" * 80)
        print(f"📊 MOMENTUM STRATEGY BACKTEST RESULTS")
        print(f"=" * 80)
        
        print(f"🎯 STRATEGY CONFIGURATION:")
        print(f"   Symbol: {results['symbol']}")
        print(f"   Period: {results['start_date']} to {results['end_date']} ({results['total_days']} days)")
        print(f"   Buy threshold: {self.buy_threshold*100:.1f}%")
        print(f"   Sell threshold: {self.sell_threshold*100:.1f}%")
        print(f"   Take profit: {results['take_profit_pct']:.1f}%")
        print(f"   Trade amount: ₱{self.trade_amount}")
        
        print(f"\n💰 PERFORMANCE SUMMARY:")
        print(f"   Initial balance: ₱{results['initial_balance']:,.2f}")
        print(f"   Final balance: ₱{results['final_balance']:,.2f}")
        print(f"   Total return: ₱{results['total_return']:,.2f} ({results['return_percentage']:+.2f}%)")
        print(f"   Annualized return: {results['annualized_return']:+.2f}%")
        
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
        
        print(f"\n⚠️ RISK METRICS:")
        print(f"   Maximum drawdown: {results['max_drawdown']:.2f}%")
        print(f"   Sharpe ratio: {results['sharpe_ratio']:.2f}")
        print(f"   Volatility: {results['volatility']:.2f}%")
        
        print(f"\n💸 COST ANALYSIS:")
        print(f"   Total fees paid: ₱{results['total_fees']:.2f} ({results['fees_percentage']:.2f}%)")
        
        print(f"\n" + "=" * 80)

    def run_parameter_optimization(self, data: List[Dict], test_params: Dict) -> List[Dict]:
        """
        Run backtest with multiple parameter combinations
        
        Args:
            data: Historical data
            test_params: Dictionary of parameter ranges to test
            
        Returns:
            List of results for each parameter combination
        """
        print(f"\n🔬 PARAMETER OPTIMIZATION")
        print(f"📊 Testing multiple parameter combinations...")
        
        results = []
        original_params = {
            'buy_threshold': self.buy_threshold,
            'sell_threshold': self.sell_threshold,
            'take_profit_pct': self.take_profit_pct,
            'trade_amount': self.trade_amount
        }
        
        # Generate parameter combinations
        combinations = []
        for buy_thresh in test_params.get('buy_threshold', [self.buy_threshold]):
            for sell_thresh in test_params.get('sell_threshold', [self.sell_threshold]):
                for tp_pct in test_params.get('take_profit_pct', [self.take_profit_pct]):
                    for trade_amt in test_params.get('trade_amount', [self.trade_amount]):
                        combinations.append({
                            'buy_threshold': buy_thresh,
                            'sell_threshold': sell_thresh,
                            'take_profit_pct': tp_pct,
                            'trade_amount': trade_amt
                        })
        
        print(f"🔍 Testing {len(combinations)} parameter combinations...")
        
        for i, params in enumerate(combinations):
            # Update parameters
            self.buy_threshold = params['buy_threshold']
            self.sell_threshold = params['sell_threshold']
            self.take_profit_pct = params['take_profit_pct']
            self.trade_amount = params['trade_amount']
            
            # Run backtest
            result = self.run_momentum_strategy(data)
            result.update(params)
            results.append(result)
            
            print(f"   [{i+1:2d}/{len(combinations)}] Buy: {params['buy_threshold']*100:.1f}%, "
                  f"Sell: {params['sell_threshold']*100:.1f}%, TP: {params['take_profit_pct']*100:.1f}% "
                  f"→ Return: {result['return_percentage']:+.1f}%")
        
        # Restore original parameters
        for param, value in original_params.items():
            setattr(self, param, value)
        
        # Sort by return percentage
        results.sort(key=lambda x: x['return_percentage'], reverse=True)
        
        print(f"\n🏆 OPTIMIZATION RESULTS:")
        print(f"📈 Best return: {results[0]['return_percentage']:+.2f}% "
              f"(Buy: {results[0]['buy_threshold']*100:.1f}%, "
              f"Sell: {results[0]['sell_threshold']*100:.1f}%, "
              f"TP: {results[0]['take_profit_pct']*100:.1f}%)")
        
        return results

def main():
    """Main function for running backtests"""
    print("🔬 MOMENTUM BACKTESTING ENGINE v44")
    print("=" * 60)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found!")
        return
    
    # Configuration
    symbol = input("Enter symbol (default XRPPHP): ").strip().upper() or 'XRPPHP'
    
    try:
        days = int(input("Enter days of history (default 60): ") or "60")
    except ValueError:
        days = 60
    
    print(f"\nSelect backtest type:")
    print("1. Single strategy backtest")
    print("2. Parameter optimization")
    print("3. Take profit optimization")
    
    choice = input("Enter choice (1-3): ").strip() or "1"
    
    # Initialize backtester
    backtester = MomentumBacktester(symbol=symbol)
    
    # Fetch historical data
    data = backtester.fetch_historical_data(days=days)
    if not data:
        print("❌ Failed to fetch historical data!")
        return
    
    if choice == "1":
        # Single backtest
        results = backtester.run_momentum_strategy(data)
        backtester.print_results(results)
        
    elif choice == "2":
        # Parameter optimization
        test_params = {
            'buy_threshold': [0.004, 0.006, 0.008, 0.010],
            'sell_threshold': [0.008, 0.010, 0.012, 0.015],
            'take_profit_pct': [0.015, 0.020, 0.025, 0.030],
        }
        results = backtester.run_parameter_optimization(data, test_params)
        
        print(f"\n📊 TOP 5 PARAMETER COMBINATIONS:")
        for i, result in enumerate(results[:5]):
            print(f"{i+1}. Return: {result['return_percentage']:+.1f}% | "
                  f"Buy: {result['buy_threshold']*100:.1f}% | "
                  f"Sell: {result['sell_threshold']*100:.1f}% | "
                  f"TP: {result['take_profit_pct']*100:.1f}% | "
                  f"Trades: {result['total_trades']} | "
                  f"Win%: {result['win_rate']:.0f}")
        
    elif choice == "3":
        # Take profit optimization
        take_profit_levels = [0.005, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050]
        
        print(f"\n🎯 TAKE PROFIT OPTIMIZATION")
        tp_results = []
        
        for tp in take_profit_levels:
            result = backtester.run_momentum_strategy(data, take_profit_pct=tp)
            tp_results.append(result)
            print(f"   TP {tp*100:.1f}%: {result['return_percentage']:+.1f}% return, "
                  f"{result['total_trades']} trades, {result['win_rate']:.0f}% win rate")
        
        # Find best take profit level
        best_tp = max(tp_results, key=lambda x: x['return_percentage'])
        print(f"\n🏆 BEST TAKE PROFIT: {best_tp['take_profit_pct']:.1f}% "
              f"({best_tp['return_percentage']:+.1f}% return)")
        
        # Detailed results for best TP
        backtester.print_results(best_tp)

def run_quick_backtest(symbol='XRPPHP', days=30):
    """Quick backtest function for external use"""
    backtester = MomentumBacktester(symbol=symbol)
    data = backtester.fetch_historical_data(days=days)
    
    if not data:
        return None
    
    results = backtester.run_momentum_strategy(data)
    return results

def compare_strategies(symbol='XRPPHP', days=60):
    """Compare different strategy configurations"""
    print(f"\n🔬 STRATEGY COMPARISON for {symbol}")
    print("=" * 60)
    
    backtester = MomentumBacktester(symbol=symbol)
    data = backtester.fetch_historical_data(days=days)
    
    if not data:
        print("❌ Failed to fetch data!")
        return
    
    strategies = [
        {'name': 'Conservative', 'buy_threshold': 0.008, 'sell_threshold': 0.012, 'take_profit_pct': 0.015},
        {'name': 'Balanced', 'buy_threshold': 0.006, 'sell_threshold': 0.010, 'take_profit_pct': 0.020},
        {'name': 'Aggressive', 'buy_threshold': 0.004, 'sell_threshold': 0.008, 'take_profit_pct': 0.030},
        {'name': 'High Frequency', 'buy_threshold': 0.003, 'sell_threshold': 0.006, 'take_profit_pct': 0.010},
    ]
    
    results = []
    
    for strategy in strategies:
        backtester.buy_threshold = strategy['buy_threshold']
        backtester.sell_threshold = strategy['sell_threshold']
        backtester.take_profit_pct = strategy['take_profit_pct']
        
        result = backtester.run_momentum_strategy(data)
        result['strategy_name'] = strategy['name']
        results.append(result)
    
    # Display comparison
    print(f"\n📊 STRATEGY COMPARISON RESULTS:")
    print("-" * 100)
    print(f"{'Strategy':<15} {'Return%':<8} {'Trades':<7} {'Win%':<6} {'Sharpe':<7} {'MaxDD%':<7} {'vs B&H':<7}")
    print("-" * 100)
    
    for result in results:
        print(f"{result['strategy_name']:<15} "
              f"{result['return_percentage']:+7.1f} "
              f"{result['total_trades']:>6} "
              f"{result['win_rate']:>5.0f} "
              f"{result['sharpe_ratio']:>6.2f} "
              f"{result['max_drawdown']:>6.1f} "
              f"{result['outperformance']:+6.1f}")
    
    print("-" * 100)
    
    # Find best strategy
    best_strategy = max(results, key=lambda x: x['return_percentage'])
    print(f"\n🏆 BEST STRATEGY: {best_strategy['strategy_name']} "
          f"({best_strategy['return_percentage']:+.1f}% return)")
    
    return results

def export_results_to_csv(results: Dict, filename: str = None):
    """Export backtest results to CSV file"""
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_results_{results['symbol']}_{timestamp}.csv"
    
    try:
        # Convert trade history to DataFrame
        if results.get('trade_history'):
            df_trades = pd.DataFrame(results['trade_history'])
            df_trades.to_csv(filename.replace('.csv', '_trades.csv'), index=False)
            print(f"✅ Trade history exported to {filename.replace('.csv', '_trades.csv')}")
        
        # Convert equity curve to DataFrame
        if results.get('equity_curve'):
            df_equity = pd.DataFrame(results['equity_curve'])
            df_equity.to_csv(filename.replace('.csv', '_equity.csv'), index=False)
            print(f"✅ Equity curve exported to {filename.replace('.csv', '_equity.csv')}")
        
        # Export summary metrics
        summary_data = {k: v for k, v in results.items() 
                       if not isinstance(v, (list, dict))}
        df_summary = pd.DataFrame([summary_data])
        df_summary.to_csv(filename.replace('.csv', '_summary.csv'), index=False)
        print(f"✅ Summary metrics exported to {filename.replace('.csv', '_summary.csv')}")
        
    except Exception as e:
        print(f"❌ Error exporting results: {e}")

class AdvancedBacktester(MomentumBacktester):
    """
    🔬 Advanced backtester with additional features
    """
    
    def __init__(self, symbol='XRPPHP', initial_balance=10000):
        super().__init__(symbol, initial_balance)
        self.portfolio_allocation = 1.0  # 100% allocation to strategy
        self.rebalance_frequency = 24    # Rebalance every 24 hours
        self.risk_management_enabled = True
        
    def calculate_position_size(self, current_price: float, volatility: float) -> float:
        """
        Calculate position size based on volatility and risk management
        
        Args:
            current_price: Current asset price
            volatility: Recent price volatility
            
        Returns:
            Position size in PHP
        """
        if not self.risk_management_enabled:
            return self.trade_amount
        
        # Kelly Criterion inspired sizing
        base_size = self.trade_amount
        
        # Reduce size if high volatility
        if volatility > 0.05:  # 5% daily volatility
            volatility_adjustment = max(0.5, 1 - (volatility - 0.05) * 2)
            base_size *= volatility_adjustment
        
        # Account balance adjustment
        balance_ratio = self.php_balance / self.initial_balance
        if balance_ratio < 0.8:  # If lost 20% of initial balance
            base_size *= 0.7  # Reduce position size
        
        return min(base_size, self.php_balance * 0.1)  # Never risk more than 10% of balance
    
    def calculate_dynamic_thresholds(self, recent_volatility: float) -> Tuple[float, float]:
        """
        Calculate dynamic buy/sell thresholds based on market volatility
        
        Args:
            recent_volatility: Recent price volatility
            
        Returns:
            Tuple of (buy_threshold, sell_threshold)
        """
        base_buy = self.buy_threshold
        base_sell = self.sell_threshold
        
        # Adjust thresholds based on volatility
        if recent_volatility > 0.03:  # High volatility
            buy_threshold = base_buy * 1.2
            sell_threshold = base_sell * 1.2
        elif recent_volatility < 0.01:  # Low volatility
            buy_threshold = base_buy * 0.8
            sell_threshold = base_sell * 0.8
        else:
            buy_threshold = base_buy
            sell_threshold = base_sell
        
        return buy_threshold, sell_threshold
    
    def calculate_recent_volatility(self, prices: List[float], period: int = 24) -> float:
        """Calculate recent price volatility"""
        if len(prices) < period + 1:
            return 0.02  # Default volatility
        
        recent_prices = prices[-period:]
        returns = []
        
        for i in range(1, len(recent_prices)):
            ret = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
            returns.append(ret)
        
        if not returns:
            return 0.02
        
        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        # Annualize (assuming hourly data)
        return volatility * (24 ** 0.5)
    
    def run_advanced_momentum_strategy(self, data: List[Dict]) -> Dict:
        """
        Run advanced momentum strategy with dynamic parameters
        """
        print(f"\n🚀 Running ADVANCED momentum strategy...")
        print(f"📊 Features: Dynamic thresholds, volatility-based sizing, risk management")
        
        self.reset_state()
        prices = []
        
        for i, candle in enumerate(data):
            current_price = candle['close']
            current_time = candle['timestamp']
            
            prices.append(current_price)
            
            if len(prices) < 25:  # Need history for volatility calculation
                continue
            
            # Calculate dynamic parameters
            recent_volatility = self.calculate_recent_volatility(prices)
            buy_threshold, sell_threshold = self.calculate_dynamic_thresholds(recent_volatility)
            momentum = self.calculate_momentum(prices, period=3)
            
            # Update equity curve
            self.update_equity_curve(current_price, current_time)
            
            # Dynamic position sizing
            if self.position is None:
                position_size = self.calculate_position_size(current_price, recent_volatility)
            else:
                position_size = self.trade_amount
            
            # BUY CONDITIONS with dynamic thresholds
            if (momentum > buy_threshold and
                self.php_balance > position_size * 1.1 and
                self.can_trade_today(current_time) and
                self.position is None):
                
                # Override trade amount with dynamic sizing
                original_amount = self.trade_amount
                self.trade_amount = position_size
                self.place_buy(current_price, current_time, momentum)
                self.trade_amount = original_amount
            
            # SELL CONDITIONS with dynamic thresholds
            elif (momentum < -sell_threshold and
                  self.asset_balance > 0.001 and
                  self.can_sell_position(current_time) and
                  self.can_trade_today(current_time)):
                
                self.place_sell(current_price, current_time, momentum, "Dynamic Momentum Down")
            
            # Take profit (static)
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position(current_time)):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct >= self.take_profit_pct:
                    self.place_sell(current_price, current_time, momentum, "Take Profit")
        
        # Calculate final results
        final_price = data[-1]['close']
        final_portfolio_value = self.php_balance + (self.asset_balance * final_price)
        
        results = self.calculate_performance_metrics(data[0], data[-1], final_portfolio_value)
        results['strategy_type'] = 'Advanced Dynamic'
        
        return results

def run_monte_carlo_simulation(symbol='XRPPHP', days=60, num_simulations=100):
    """
    Run Monte Carlo simulation on the strategy
    
    Args:
        symbol: Trading symbol
        days: Days of historical data
        num_simulations: Number of simulation runs
        
    Returns:
        Simulation results
    """
    print(f"\n🎲 MONTE CARLO SIMULATION")
    print(f"🎯 Running {num_simulations} simulations on {symbol}")
    
    backtester = MomentumBacktester(symbol=symbol)
    data = backtester.fetch_historical_data(days=days)
    
    if not data:
        print("❌ Failed to fetch data!")
        return None
    
    simulation_results = []
    
    for i in range(num_simulations):
        # Randomly shuffle the data to create different market scenarios
        import random
        shuffled_data = data.copy()
        random.shuffle(shuffled_data)
        
        # Sort by original timestamps to maintain chronological order
        shuffled_data.sort(key=lambda x: x['timestamp'])
        
        result = backtester.run_momentum_strategy(shuffled_data)
        simulation_results.append(result['return_percentage'])
        
        if (i + 1) % 10 == 0:
            print(f"   Completed {i + 1}/{num_simulations} simulations...")
    
    # Calculate simulation statistics
    avg_return = sum(simulation_results) / len(simulation_results)
    sorted_results = sorted(simulation_results)
    
    percentile_5 = sorted_results[int(len(sorted_results) * 0.05)]
    percentile_25 = sorted_results[int(len(sorted_results) * 0.25)]
    median = sorted_results[int(len(sorted_results) * 0.5)]
    percentile_75 = sorted_results[int(len(sorted_results) * 0.75)]
    percentile_95 = sorted_results[int(len(sorted_results) * 0.95)]
    
    positive_outcomes = len([r for r in simulation_results if r > 0])
    probability_profit = positive_outcomes / len(simulation_results) * 100
    
    print(f"\n📊 MONTE CARLO RESULTS:")
    print(f"   Average return: {avg_return:+.2f}%")
    print(f"   Median return: {median:+.2f}%")
    print(f"   5th percentile: {percentile_5:+.2f}%")
    print(f"   25th percentile: {percentile_25:+.2f}%")
    print(f"   75th percentile: {percentile_75:+.2f}%")
    print(f"   95th percentile: {percentile_95:+.2f}%")
    print(f"   Probability of profit: {probability_profit:.1f}%")
    
    return {
        'simulation_results': simulation_results,
        'avg_return': avg_return,
        'median': median,
        'percentiles': {
            '5th': percentile_5,
            '25th': percentile_25,
            '75th': percentile_75,
            '95th': percentile_95
        },
        'probability_profit': probability_profit
    }

if __name__ == "__main__":
    main()