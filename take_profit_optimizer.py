import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI
import pandas as pd

load_dotenv(override=True)

class TakeProfitOptimizer:
    def __init__(self, symbol='XRPPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')  # Extract base asset (XRP, SOL, etc.)
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
            print(f"   Base Asset: {symbol_info.get('baseAsset')}")
            print(f"   Quote Asset: {symbol_info.get('quoteAsset')}")
            print(f"   Status: {symbol_info.get('status')}")
            
            # Check minimum order requirements
            filters = symbol_info.get('filters', [])
            for f in filters:
                if f.get('filterType') == 'MIN_NOTIONAL':
                    min_notional = float(f.get('minNotional', 0))
                    if min_notional > 0:
                        print(f"   Min order size: ₱{min_notional}")
                        if self.trade_amount < min_notional:
                            print(f"⚠️ Trade amount (₱{self.trade_amount}) below minimum (₱{min_notional})")
                            print(f"   Consider increasing trade amount to at least ₱{min_notional + 1}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating symbol {self.symbol}: {e}")
            return False

    def get_symbol_price_range(self):
        """Get recent price range for the symbol to validate our test parameters"""
        try:
            # Get current price
            current_price = self.api.get_current_price(self.symbol)
            
            # Get 24hr ticker
            ticker_24hr = self.api.get_24hr_ticker(self.symbol)
            
            high_24h = float(ticker_24hr.get('highPrice', current_price))
            low_24h = float(ticker_24hr.get('lowPrice', current_price))
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            
            print(f"📊 {self.symbol} Market Data:")
            print(f"   Current Price: ₱{current_price:.4f}")
            print(f"   24h High: ₱{high_24h:.4f}")
            print(f"   24h Low: ₱{low_24h:.4f}")
            print(f"   24h Volume: ₱{volume_24h:,.0f}")
            print(f"   24h Change: {price_change_24h:+.2f}%")
            
            # Calculate volatility
            volatility = abs(price_change_24h)
            if volatility > 10:
                print(f"⚠️ High volatility asset ({volatility:.1f}%) - Consider shorter take profit levels")
            elif volatility > 5:
                print(f"📊 Moderate volatility asset ({volatility:.1f}%)")
            else:
                print(f"📈 Low volatility asset ({volatility:.1f}%) - Consider longer take profit levels")
            
            return {
                'current_price': current_price,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'volume_24h': volume_24h,
                'volatility': volatility
            }
            
        except Exception as e:
            print(f"❌ Error getting market data for {self.symbol}: {e}")
            return None

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
        cache_key = f'_cached_data_{self.symbol}_{days}'
        if hasattr(self, cache_key):
            return getattr(self, cache_key)
        
        print(f"\n📊 Fetching {days} days of historical data for {self.symbol}...")
        
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
            
            if not klines:
                print(f"❌ No historical data received for {self.symbol}")
                return None, 0
            
            data = []
            for kline in klines:
                data.append({
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'close': float(kline[4])
                })
            
            if data:
                actual_days = (data[-1]['timestamp'] - data[0]['timestamp']).days
                print(f"✅ Got {len(data)} hourly candles covering {actual_days} days")
                cached_data = (data, actual_days)
                setattr(self, cache_key, cached_data)
                return cached_data
            else:
                return None, 0
            
        except Exception as e:
            print(f"❌ Error fetching data for {self.symbol}: {e}")
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

    def get_asset_specific_tp_levels(self, volatility):
        """Get asset-specific take profit levels based on volatility"""
        if volatility > 15:  # Very high volatility (e.g., SOL during bull runs)
            return [0.5, 0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0, 4.0]
        elif volatility > 8:  # High volatility 
            return [0.8, 1.0, 1.2, 1.5, 1.8, 2.0, 2.2, 2.5, 3.0, 3.5, 4.0, 5.0]
        elif volatility > 3:  # Medium volatility (e.g., XRP)
            return [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 6.0, 8.0, 10.0]
        else:  # Low volatility (e.g., stable coins, BTC sometimes)
            return [1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0, 12.0, 15.0]

    def run_comprehensive_optimization(self, days=60):
        """Run comprehensive take profit optimization"""
        print(f"\n🚀 COMPREHENSIVE TAKE PROFIT OPTIMIZATION")
        print(f"🎯 Symbol: {self.symbol}")
        print(f"📅 Testing period: {days} days")
        print("=" * 80)
        
        # Validate symbol first
        if not self.validate_symbol():
            return None
        
        # Get market data
        market_data = self.get_symbol_price_range()
        if not market_data:
            return None
        
        volatility = market_data['volatility']
        
        # Get asset-specific take profit levels based on volatility
        take_profit_levels = self.get_asset_specific_tp_levels(volatility)
        
        print(f"\n🔬 Testing {len(take_profit_levels)} take profit levels optimized for {self.base_asset}:")
        print(f"   Volatility: {volatility:.1f}% (24h)")
        print(f"   TP Levels: {', '.join([f'{tp:.1f}%' for tp in take_profit_levels])}")
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
        self.display_optimization_results(df, best_return, best_sharpe, best_win_rate, most_profit_taking, market_data)
        
        return df

    def display_optimization_results(self, df, best_return, best_sharpe, best_win_rate, most_profit_taking, market_data):
        """Display comprehensive optimization results"""
        
        print(f"\n🏆 OPTIMIZATION RESULTS SUMMARY for {self.symbol}")
        print("=" * 80)
        
        # Market context
        print(f"📊 MARKET CONTEXT:")
        print(f"   Current Price: ₱{market_data['current_price']:.4f}")
        print(f"   24h Volume: ₱{market_data['volume_24h']:,.0f}")
        print(f"   24h Volatility: {market_data['volatility']:.1f}%")
        print()
        
        # Overall statistics
        print(f"📈 PERFORMANCE LEADERS:")
        print(f"   🏆 Best return: {best_return['return_percentage']:+.2f}% (@ {best_return['take_profit_pct']:.1f}% TP)")
        print(f"   ⚖️ Best Sharpe: {best_sharpe['sharpe_ratio']:.2f} (@ {best_sharpe['take_profit_pct']:.1f}% TP)")
        print(f"   🎯 Best win rate: {best_win_rate['win_rate']:.1f}% (@ {best_win_rate['take_profit_pct']:.1f}% TP)")
        print(f"   💰 Most profit taking: {most_profit_taking['profit_taking_pct']:.1f}% (@ {most_profit_taking['take_profit_pct']:.1f}% TP)")
        print()
        
        # Detailed table
        print(f"📋 DETAILED RESULTS TABLE for {self.symbol}:")
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
        
        # Asset-specific analysis
        print(f"📈 {self.base_asset} TAKE PROFIT ANALYSIS:")
        
        # Find optimal range
        profitable_strategies = df[df['return_percentage'] > 0]
        if len(profitable_strategies) > 0:
            min_profitable_tp = profitable_strategies['take_profit_pct'].min()
            max_profitable_tp = profitable_strategies['take_profit_pct'].max()
            avg_profitable_return = profitable_strategies['return_percentage'].mean()
            
            print(f"   ✅ Profitable range: {min_profitable_tp:.1f}% - {max_profitable_tp:.1f}% TP")
            print(f"   📊 Average profitable return: {avg_profitable_return:+.1f}%")
        else:
            print(f"   ❌ No profitable take profit levels found for {self.base_asset}!")
        
        # Volatility-based recommendations
        volatility = market_data['volatility']
        if volatility > 10:
            print(f"   ⚡ High volatility asset: Consider lower TP levels (0.5%-2.0%)")
        elif volatility > 5:
            print(f"   📊 Medium volatility asset: Balanced TP levels (1.0%-4.0%)")
        else:
            print(f"   📈 Low volatility asset: Higher TP levels may work (2.0%-8.0%)")
        
        print()
        
        # Final recommendation with asset context
        print(f"🎯 FINAL RECOMMENDATION for {self.symbol}:")
        
        # Simple scoring system
        df['score'] = (
            df['return_percentage'] * 0.4 +  # 40% weight on returns
            df['win_rate'] * 0.3 +           # 30% weight on win rate
            df['sharpe_ratio'] * 10 * 0.2 +  # 20% weight on Sharpe
            df['profit_taking_pct'] * 0.1    # 10% weight on profit taking frequency
        )
        
        best_overall = df.loc[df['score'].idxmax()]
        print(f"   🏆 OPTIMAL: {best_overall['take_profit_pct']:.1f}% take profit")
        print(f"   📊 Expected performance for {self.base_asset}:")
        print(f"      Return: {best_overall['return_percentage']:+.1f}%")
        print(f"      Win rate: {best_overall['win_rate']:.0f}%")
        print(f"      Trades per day: {best_overall['trades_per_day']:.1f}")
        print(f"      Profit taking exits: {best_overall['profit_taking_pct']:.0f}%")
        print(f"      vs Buy & Hold: {best_overall['outperformance']:+.1f}%")
        print()
        
        print(f"💡 INTEGRATION TIPS:")
        print(f"   🤖 For TITAN bot: Use {best_overall['take_profit_pct']:.1f}% in interactive setup")
        print(f"   🔮 For ORACLE bot: Set as fallback TP if AI doesn't provide target")
        print(f"   📊 For live trading: Start conservative with {best_overall['take_profit_pct']:.1f}% then adjust")

def get_available_php_pairs():
    """Get all available PHP trading pairs from the exchange"""
    try:
        # Initialize API
        api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Get exchange info
        exchange_info = api.get_exchange_info()
        symbols = exchange_info.get('symbols', [])
        
        # Filter for PHP pairs that are trading
        php_pairs = []
        for symbol in symbols:
            if (symbol.get('quoteAsset') == 'PHP' and 
                symbol.get('status', '').upper() in ['TRADING', 'ACTIVE']):
                php_pairs.append(symbol['symbol'])
        
        # Sort alphabetically
        php_pairs.sort()
        
        return php_pairs
        
    except Exception as e:
        print(f"❌ Error fetching available pairs: {e}")
        return []

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

def main():
    print("🔬 ENHANCED TAKE PROFIT OPTIMIZER")
    print("🎯 Now supports ALL PHP trading pairs with custom optimization")
    print("=" * 75)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
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
    
    print(f"\n🎯 Select trading pair to optimize:")
    print("1. XRPPHP - Recommended (Medium volatility, good volume)")
    print("2. SOLPHP - High volatility (Good for aggressive strategies)")
    print("3. BTCPHP - Lower volatility (Stable, good for conservative)")
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
            # Show all available pairs
            available_pairs = get_available_php_pairs()
            if available_pairs:
                print(f"\n📋 All available PHP pairs ({len(available_pairs)} total):")
                for i, pair in enumerate(available_pairs):
                    print(f"  {pair}", end="  ")
                    if (i + 1) % 6 == 0:  # 6 per line
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
    
    # Get optimization depth
    print(f"\n⚙️ Select optimization depth:")
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
    
    print(f"\n🚀 Starting comprehensive optimization...")
    print(f"🎯 Symbol: {symbol}")
    print(f"📅 Period: {days} days")
    print(f"🔬 Testing asset-specific take profit levels")
    
    # Run optimization
    optimizer = TakeProfitOptimizer(symbol)
    results = optimizer.run_comprehensive_optimization(days)
    
    if results is not None:
        print(f"\n✅ OPTIMIZATION COMPLETE for {symbol}!")
        print(f"🎯 Use the recommended take profit level in your trading bots")
        print(f"📊 Results are optimized specifically for {symbol} characteristics")
        
        # Export results option
        export_choice = input(f"\n💾 Export results to CSV? (y/n): ").strip().lower()
        if export_choice.startswith('y'):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"take_profit_optimization_{symbol}_{timestamp}.csv"
            try:
                results.to_csv(filename, index=False)
                print(f"✅ Results exported to {filename}")
            except Exception as e:
                print(f"❌ Export failed: {e}")
    else:
        print(f"\n❌ Optimization failed for {symbol}!")

def quick_optimize(symbol, days=60):
    """Quick optimization function for external use"""
    print(f"🔬 Quick optimization for {symbol}")
    optimizer = TakeProfitOptimizer(symbol)
    
    if not optimizer.validate_symbol():
        return None
    
    results = optimizer.run_comprehensive_optimization(days)
    
    if results is not None:
        best_result = results.loc[results['return_percentage'].idxmax()]
        return {
            'symbol': symbol,
            'optimal_tp': best_result['take_profit_pct'],
            'expected_return': best_result['return_percentage'],
            'win_rate': best_result['win_rate'],
            'total_trades': best_result['total_trades']
        }
    
    return None

def optimize_multiple_pairs(symbols_list, days=60):
    """Optimize multiple trading pairs and compare results"""
    print(f"🔬 MULTI-PAIR OPTIMIZATION")
    print(f"🎯 Symbols: {', '.join(symbols_list)}")
    print(f"📅 Period: {days} days")
    print("=" * 60)
    
    results_summary = []
    
    for symbol in symbols_list:
        print(f"\n📊 Optimizing {symbol}...")
        optimizer = TakeProfitOptimizer(symbol)
        
        if not optimizer.validate_symbol():
            print(f"❌ Skipping {symbol} - validation failed")
            continue
        
        results = optimizer.run_comprehensive_optimization(days)
        
        if results is not None:
            best_result = results.loc[results['return_percentage'].idxmax()]
            results_summary.append({
                'symbol': symbol,
                'optimal_tp': best_result['take_profit_pct'],
                'expected_return': best_result['return_percentage'],
                'win_rate': best_result['win_rate'],
                'total_trades': best_result['total_trades'],
                'sharpe_ratio': best_result['sharpe_ratio']
            })
            print(f"✅ {symbol}: {best_result['take_profit_pct']:.1f}% TP, {best_result['return_percentage']:+.1f}% return")
        else:
            print(f"❌ {symbol}: Optimization failed")
    
    if results_summary:
        print(f"\n📊 MULTI-PAIR COMPARISON:")
        print("-" * 70)
        print(f"{'Symbol':<8} {'Opt TP%':<8} {'Return%':<9} {'Win%':<6} {'Trades':<7} {'Sharpe':<7}")
        print("-" * 70)
        
        for result in results_summary:
            print(f"{result['symbol']:<8} "
                  f"{result['optimal_tp']:<8.1f} "
                  f"{result['expected_return']:<+9.1f} "
                  f"{result['win_rate']:<6.0f} "
                  f"{result['total_trades']:<7.0f} "
                  f"{result['sharpe_ratio']:<7.2f}")
        
        print("-" * 70)
        
        # Find best performing pairs
        best_return = max(results_summary, key=lambda x: x['expected_return'])
        best_sharpe = max(results_summary, key=lambda x: x['sharpe_ratio'])
        
        print(f"\n🏆 BEST PERFORMERS:")
        print(f"   📈 Best Return: {best_return['symbol']} ({best_return['expected_return']:+.1f}%)")
        print(f"   ⚖️ Best Sharpe: {best_sharpe['symbol']} ({best_sharpe['sharpe_ratio']:.2f})")
        
        return results_summary
    
    return None

if __name__ == "__main__":
    main()