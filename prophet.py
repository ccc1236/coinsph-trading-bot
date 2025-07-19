import os
import sys
import time
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
import itertools

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from coinsph_api_v2 import CoinsAPI
except ImportError:
    print("❌ Could not import coinsph_api_v2 module")
    print("   Make sure coinsph_api_v2.py is in the same directory")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("❌ pandas not installed. Installing...")
    os.system("pip install pandas")
    import pandas as pd

load_dotenv(override=True)

class ProphetEnhanced:
    """
    🔮 PROPHET v3.0 - Enhanced Comprehensive Parameter Optimizer
    
    NEW in v3.0:
    - ✅ Asset-specific parameter ranges based on volatility analysis
    - ✅ Real-time market data validation and symbol verification
    - ✅ Professional results presentation with detailed analysis
    - ✅ Interactive parameter override capability
    - ✅ Enhanced symbol support with market data integration
    - ✅ Maintains TITAN integration (prophet_reco.json output)
    - ✅ Proven 30 & 60-day test periods (API-friendly)
    """
    
    def __init__(self, symbol='SOLPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')
        self.initial_balance = 2000
        
        # Fixed parameters (core strategy)
        self.trade_amount = 200
        self.sell_percentage = 1.00  # 100% clean exits
        self.min_hold_minutes = 30
        self.max_trades_per_day = 10
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        # Will be set after market analysis
        self.buy_thresholds = []
        self.sell_thresholds = []
        self.take_profit_levels = []
        self.market_data = None
        
        print(f"🔮 PROPHET v3.0 - Enhanced Parameter Optimizer")
        print(f"🎯 Asset: {self.symbol}")
        print(f"📊 Comprehensive optimization with market-based parameter ranges")
        print("=" * 70)

    def validate_symbol(self):
        """Validate that the symbol exists and is tradable (from TPO)"""
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

    def get_market_data_analysis(self):
        """Get comprehensive market data analysis (from TPO)"""
        try:
            # Get current price and 24hr ticker
            current_price = self.api.get_current_price(self.symbol)
            ticker_24hr = self.api.get_24hr_ticker(self.symbol)
            
            high_24h = float(ticker_24hr.get('highPrice', current_price))
            low_24h = float(ticker_24hr.get('lowPrice', current_price))
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            
            print(f"📊 {self.symbol} Market Analysis:")
            print(f"   Current Price: ₱{current_price:.4f}")
            print(f"   24h High: ₱{high_24h:.4f}")
            print(f"   24h Low: ₱{low_24h:.4f}")
            print(f"   24h Volume: ₱{volume_24h:,.0f}")
            print(f"   24h Change: {price_change_24h:+.2f}%")
            
            # Calculate volatility
            volatility = abs(price_change_24h)
            if volatility > 10:
                print(f"📈 High volatility asset ({volatility:.1f}%) - Using aggressive parameter ranges")
            elif volatility > 5:
                print(f"📊 Moderate volatility asset ({volatility:.1f}%) - Using balanced parameter ranges")
            else:
                print(f"📉 Low volatility asset ({volatility:.1f}%) - Using conservative parameter ranges")
            
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

    def get_asset_specific_parameters(self, volatility, allow_override=True):
        """Get asset-specific parameter ranges based on volatility (enhanced from TPO)"""
        
        if volatility > 15:  # Very high volatility
            default_buy = [0.003, 0.004, 0.005, 0.006, 0.008]
            default_sell = [0.005, 0.008, 0.010, 0.012, 0.015]
            default_tp = [0.005, 0.008, 0.010, 0.012, 0.015, 0.020]
            category = 'Very High Volatility'
        elif volatility > 8:  # High volatility
            default_buy = [0.004, 0.006, 0.008, 0.010, 0.012]
            default_sell = [0.008, 0.010, 0.012, 0.015, 0.020]
            default_tp = [0.008, 0.010, 0.015, 0.020, 0.025, 0.030]
            category = 'High Volatility'
        elif volatility > 3:  # Medium volatility
            default_buy = [0.005, 0.006, 0.008, 0.010, 0.012]
            default_sell = [0.008, 0.010, 0.012, 0.015, 0.020]
            default_tp = [0.015, 0.020, 0.025, 0.030, 0.040, 0.050]
            category = 'Medium Volatility'
        else:  # Low volatility
            default_buy = [0.006, 0.008, 0.010, 0.012, 0.015]
            default_sell = [0.010, 0.012, 0.015, 0.020, 0.025]
            default_tp = [0.020, 0.030, 0.040, 0.050, 0.060, 0.080]
            category = 'Low Volatility'

        print(f"\n🎯 {category} Parameter Ranges for {self.base_asset}:")
        print(f"   Buy Thresholds: {[f'{x*100:.1f}%' for x in default_buy]}")
        print(f"   Take Profit: {[f'{x*100:.1f}%' for x in default_tp]}")
        
        if not allow_override:
            return {
                'buy_thresholds': default_buy,
                'sell_thresholds': default_sell,
                'take_profit_range': default_tp,
                'category': category
            }
        
        # Interactive parameter override capability
        print(f"\n🔧 Parameter Configuration:")
        print(f"1. Use optimized defaults for {category}")
        print(f"2. Customize parameter ranges")
        
        try:
            choice = input("Enter choice (1-2, default: 1): ").strip()
            
            if choice == '2':
                print(f"\n📈 Customize Buy Thresholds:")
                print(f"   Current: {[f'{x*100:.1f}%' for x in default_buy]}")
                custom_buy_input = input("Enter buy thresholds % (comma-separated, or press Enter for default): ").strip()
                
                if custom_buy_input:
                    try:
                        custom_buy = [float(x.strip())/100 for x in custom_buy_input.split(',')]
                        if all(0.001 <= x <= 0.05 for x in custom_buy):
                            default_buy = sorted(custom_buy)
                            print(f"✅ Using custom buy thresholds: {[f'{x*100:.1f}%' for x in default_buy]}")
                        else:
                            print("⚠️ Invalid ranges, using defaults")
                    except:
                        print("⚠️ Invalid format, using defaults")
                
                print(f"\n🎯 Customize Take Profit Levels:")
                print(f"   Current: {[f'{x*100:.1f}%' for x in default_tp]}")
                custom_tp_input = input("Enter take profit levels % (comma-separated, or press Enter for default): ").strip()
                
                if custom_tp_input:
                    try:
                        custom_tp = [float(x.strip())/100 for x in custom_tp_input.split(',')]
                        if all(0.005 <= x <= 0.15 for x in custom_tp):
                            default_tp = sorted(custom_tp)
                            print(f"✅ Using custom take profit levels: {[f'{x*100:.1f}%' for x in default_tp]}")
                        else:
                            print("⚠️ Invalid ranges, using defaults")
                    except:
                        print("⚠️ Invalid format, using defaults")
                        
                print(f"✅ Configuration complete!")
            
        except KeyboardInterrupt:
            print(f"\n⚠️ Using default parameters for {category}")
        
        # Auto-calculate sell thresholds based on buy thresholds
        default_sell = [x * 1.67 for x in default_buy]  # 1.67x buy threshold
        
        return {
            'buy_thresholds': default_buy,
            'sell_thresholds': default_sell,
            'take_profit_range': default_tp,
            'category': category
        }

    def reset_state(self):
        """Reset trading state for each test"""
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
                cached_data = (data, actual_days)
                setattr(self, cache_key, cached_data)
                return cached_data
            else:
                return None, 0
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
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

    def test_strategy(self, buy_threshold, sell_threshold, take_profit, data):
        """Test strategy with given parameters"""
        self.reset_state()
        
        if not data or len(data) < 2:
            return None
        
        last_price = data[0]['close']
        
        # Process each hour
        for candle in data[1:]:
            current_price = candle['close']
            current_time = candle['timestamp']
            
            # Calculate price change
            price_change = (current_price - last_price) / last_price
            
            # BUY CONDITIONS
            if (price_change > buy_threshold and
                self.php_balance > self.trade_amount * 1.1 and
                self.can_trade_today(current_time) and
                self.position is None):
                
                self.place_buy(current_price, current_time, price_change)
            
            # SELL CONDITIONS - Momentum Down
            elif (price_change < -sell_threshold and
                  self.asset_balance > 0.001 and
                  self.can_sell_position(current_time) and
                  self.can_trade_today(current_time)):
                
                self.place_sell(current_price, current_time, price_change, "Momentum Down")
            
            # SELL CONDITIONS - Take Profit
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position(current_time)):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct >= take_profit:
                    self.place_sell(current_price, current_time, price_change, "Take Profit")
            
            last_price = current_price
        
        # Calculate comprehensive results
        final_price = data[-1]['close']
        final_portfolio_value = self.calculate_portfolio_value(final_price)
        total_return = final_portfolio_value - self.initial_balance
        return_percentage = (total_return / self.initial_balance) * 100
        
        # Calculate metrics
        buy_trades = [t for t in self.trade_history if t['side'] == 'BUY']
        sell_trades = [t for t in self.trade_history if t['side'] == 'SELL']
        profitable_sells = [t for t in sell_trades if t.get('profit_loss', 0) > 0]
        take_profit_sells = [t for t in sell_trades if t.get('reason') == 'Take Profit']
        
        win_rate = (len(profitable_sells) / max(1, len(sell_trades))) * 100
        tp_rate = (len(take_profit_sells) / max(1, len(sell_trades))) * 100
        
        return {
            'buy_threshold': buy_threshold * 100,
            'sell_threshold': sell_threshold * 100,
            'take_profit': take_profit * 100,
            'return_pct': return_percentage,
            'win_rate': win_rate,
            'tp_rate': tp_rate,
            'total_trades': self.total_trades,
            'fee_pct': (self.total_fees_paid / self.initial_balance) * 100
        }

    def find_optimal_parameters(self, days_list=[30, 60]):
        """Find optimal parameters with enhanced analysis"""
        print(f"\n🔮 PROPHET v3.0 Enhanced Analysis for {self.symbol}")
        print(f"📊 Market-Based Optimization with {len(self.take_profit_levels)} TP × {len(self.buy_thresholds)} buy × {len(self.sell_thresholds)} sell")
        print(f"⏰ Testing across {days_list} day periods")
        print("-" * 70)
        
        all_results = []
        
        for days in days_list:
            print(f"📈 Testing {days}-day period...")
            data, actual_days = self.get_historical_data(days)
            
            if not data:
                print(f"❌ Failed to get data for {days} days")
                continue
            
            period_results = []
            
            # Test all combinations
            total_tests = len(self.take_profit_levels) * len(self.buy_thresholds) * len(self.sell_thresholds)
            current_test = 0
            
            for tp in self.take_profit_levels:
                for buy in self.buy_thresholds:
                    for sell in self.sell_thresholds:
                        current_test += 1
                        
                        if current_test % 20 == 0:
                            print(f"   Progress: {current_test}/{total_tests}")
                        
                        result = self.test_strategy(buy, sell, tp, data)
                        if result:
                            result['period'] = f"{days}_days"
                            result['actual_days'] = actual_days
                            period_results.append(result)
            
            all_results.extend(period_results)
            print(f"✅ Completed {days}-day analysis ({len(period_results)} combinations)")
        
        return all_results

    def display_enhanced_results(self, results):
        """Enhanced results presentation (from TPO)"""
        if not results:
            print("❌ No results to analyze")
            return None, None
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(results)
        
        # Find optimal strategies
        best_overall = df.loc[df['return_pct'].idxmax()]
        best_win_rate = df.loc[df['win_rate'].idxmax()]
        most_profit_taking = df.loc[df['tp_rate'].idxmax()]
        
        # Find best per period
        period_results = {}
        for period in df['period'].unique():
            period_df = df[df['period'] == period]
            best_period = period_df.loc[period_df['return_pct'].idxmax()]
            period_results[period] = best_period
        
        print(f"\n🏆 PROPHET v3.0 ENHANCED OPTIMIZATION RESULTS")
        print("=" * 80)
        
        # Market context (enhanced from TPO)
        if self.market_data:
            print(f"📊 MARKET CONTEXT for {self.symbol}:")
            print(f"   Current Price: ₱{self.market_data['current_price']:.4f}")
            print(f"   24h Volume: ₱{self.market_data['volume_24h']:,.0f}")
            print(f"   24h Volatility: {self.market_data['volatility']:.1f}%")
            print()
        
        # Performance leaders
        print(f"📈 PERFORMANCE LEADERS:")
        print(f"   🏆 Best return: {best_overall['return_pct']:+.2f}% (Buy: {best_overall['buy_threshold']:.1f}%, TP: {best_overall['take_profit']:.1f}%)")
        print(f"   🎯 Best win rate: {best_win_rate['win_rate']:.1f}% (Buy: {best_win_rate['buy_threshold']:.1f}%, TP: {best_win_rate['take_profit']:.1f}%)")
        print(f"   💰 Most profit taking: {most_profit_taking['tp_rate']:.1f}% (Buy: {most_profit_taking['buy_threshold']:.1f}%, TP: {most_profit_taking['take_profit']:.1f}%)")
        print()
        
        # Show best per period
        print(f"📊 Performance by Period:")
        for period, result in period_results.items():
            print(f"   {period:10s}: {result['return_pct']:+6.1f}% | "
                  f"Buy {result['buy_threshold']:4.1f}% | TP {result['take_profit']:4.1f}%")
        print()
        
        # Detailed results table (enhanced presentation)
        print(f"📋 DETAILED RESULTS TABLE for {self.symbol}:")
        print("-" * 80)
        print(f"{'Buy%':<5} {'TP%':<5} {'Return%':<8} {'Win%':<6} {'Trades':<7} {'PT%':<6} {'Fees%':<6}")
        print("-" * 80)
        
        # Show top 10 results
        top_results = df.nlargest(10, 'return_pct')
        for _, row in top_results.iterrows():
            buy = f"{row['buy_threshold']:.1f}"
            tp = f"{row['take_profit']:.1f}"
            ret = f"{row['return_pct']:+.1f}"
            win = f"{row['win_rate']:.0f}"
            trades = f"{row['total_trades']:.0f}"
            pt = f"{row['tp_rate']:.0f}"
            fees = f"{row['fee_pct']:.1f}"
            
            # Highlight the best overall
            highlight = " 🏆" if row['return_pct'] == best_overall['return_pct'] else ""
            
            print(f"{buy:<5} {tp:<5} {ret:<8} {win:<6} {trades:<7} {pt:<6} {fees:<6}{highlight}")
        
        print("-" * 80)
        print("🏆 = Best Overall Performance")
        print()
        
        return best_overall, period_results

    def show_titan_configuration(self, results):
        """Show optimal configuration for TITAN bot with enhanced presentation"""
        best_overall, period_results = self.display_enhanced_results(results)
        
        if best_overall is None:
            return None, None
        
        print(f"🎯 OPTIMAL TITAN CONFIGURATION for {self.symbol}:")
        print("=" * 50)
        print(f"🎯 Asset to trade: {self.symbol}")
        print(f"📈 Buy threshold: {best_overall['buy_threshold']:.1f}%")
        print(f"📉 Sell threshold: {best_overall['sell_threshold']:.1f}%")
        print(f"🎯 Take profit level: {best_overall['take_profit']:.1f}%")
        print(f"💰 Position sizing: adaptive (recommended)")
        
        print(f"📈 Expected Performance:")
        print(f"   💰 Return: {best_overall['return_pct']:+.1f}%")
        print(f"   🎯 Win rate: {best_overall['win_rate']:.1f}%")
        print(f"   📊 TP hit rate: {best_overall['tp_rate']:.1f}%")
        print(f"   🔄 Trades: {best_overall['total_trades']}")
        print(f"   💸 Fees: {best_overall['fee_pct']:.1f}% of capital")
        
        # Asset-specific insights (enhanced from TPO)
        if self.market_data:
            volatility = self.market_data['volatility']
            print(f"\n💡 {self.base_asset} OPTIMIZATION INSIGHTS:")
            if volatility > 10:
                print(f"   ⚡ High volatility asset: Lower thresholds capture more opportunities")
            elif volatility > 5:
                print(f"   📊 Medium volatility asset: Balanced approach with moderate thresholds")
            else:
                print(f"   📈 Low volatility asset: Higher thresholds reduce noise trading")
        
        return best_overall, period_results

    def save_recommendations_for_titan(self, best_config, symbol):
        """Save Prophet's recommendations for TITAN to load"""
        try:
            # Prepare recommendation data
            recommendation = {
                'buy_threshold': best_config['buy_threshold'],
                'sell_threshold': best_config['sell_threshold'], 
                'take_profit': best_config['take_profit'],
                'position_sizing': 'adaptive',  # Prophet's recommended default
                'rationale': f"Prophet v3.0 optimized on {datetime.now().strftime('%Y-%m-%d')}: {best_config['return_pct']:+.1f}% return, {best_config['win_rate']:.1f}% win rate",
                'expected_performance': f"{best_config['return_pct']:+.1f}% return, {best_config['win_rate']:.1f}% win rate, {best_config['total_trades']} trades",
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prophet_version': '3.0',
                'test_periods': '30-60 days',
                'optimization_score': best_config['return_pct'],
                'market_data': {
                    'volatility': self.market_data['volatility'] if self.market_data else 0,
                    'volume_24h': self.market_data['volume_24h'] if self.market_data else 0,
                    'analysis_type': 'market_based_ranges'
                }
            }
            
            # Load existing recommendations file or create new
            reco_file = 'prophet_reco.json'
            try:
                with open(reco_file, 'r') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {
                    'timestamp': datetime.now().isoformat(),
                    'prophet_version': '3.0',
                    'recommendations': {}
                }
            
            # Update with new recommendation
            existing_data['recommendations'][symbol] = recommendation
            existing_data['last_updated'] = datetime.now().isoformat()
            existing_data['timestamp'] = datetime.now().isoformat()
            existing_data['prophet_version'] = '3.0'
            
            # Save to file
            with open(reco_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
            
            print(f"\n💾 PROPHET v3.0 RECOMMENDATIONS SAVED!")
            print(f"📁 File: {reco_file}")
            print(f"🎯 {symbol}: Buy {best_config['buy_threshold']:.1f}%, Sell {best_config['sell_threshold']:.1f}%, TP {best_config['take_profit']:.1f}%")
            print(f"🤖 TITAN ready to load these optimized settings")
            print(f"⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error saving recommendations: {e}")
            return False

def get_available_pairs():
    """Get available trading pairs from the exchange"""
    # First, always return the fallback list to ensure we have something
    fallback_pairs = get_fallback_pairs()
    
    try:
        api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        print("   Connecting to exchange...")
        exchange_info = api.get_exchange_info()
        
        if 'symbols' in exchange_info:
            live_pairs = []
            for symbol_info in exchange_info['symbols']:
                symbol = symbol_info.get('symbol', '')
                if symbol.endswith('PHP') and symbol_info.get('status') == 'TRADING':
                    live_pairs.append(symbol)
            
            if live_pairs:
                print(f"   ✅ Found {len(live_pairs)} live trading pairs")
                return sorted(live_pairs)
        
        print("   ⚠️  No PHP pairs found in live data, using known pairs")
        return fallback_pairs
            
    except Exception as e:
        print(f"   ⚠️  Exchange connection failed, using known pairs")
        return fallback_pairs

def get_fallback_pairs():
    """Fallback list of known PHP pairs"""
    return [
        'BTCPHP', 'ETHPHP', 'XRPPHP', 'SOLPHP', 'ADAPHP', 'DOTPHP',
        'LINKPHP', 'LTCPHP', 'BCHPHP', 'EOSPHA', 'TRXPHP', 'XLMPHP',
        'DOGEPHP', 'MATICPHP', 'USDTPHP', 'USDCPHP', 'BUSDPHP',
        'BNBPHP', 'AVAXPHP', 'ATOMPHP', 'ALGOPHP', 'VETPHP',
        'ICPPHP', 'FTMPHP', 'SANDPHP', 'MANAPHP', 'AXSPHP',
        'SHIBPHP', 'APTPHP', 'NEARPHP', 'FLOWPHP', 'EGLDPHP',
        'CHZPHP', 'ENJPHP', 'BATPHP', 'ZECPHP', 'DASHPHP',
        'COMPPHP', 'MKRPHP', 'SNXPHP', 'CRVPHP', 'UMAPHP',
        'YFIPHA', 'SUSHIPHP', 'BADGERPHP', 'RENFPH', 'OGNPHA',
        'STORJPHP', 'CTXCPHP', 'CELOPHP', 'SKIPHP', 'REQPHP',
        'LOOMPHP', 'MITHPHP', 'DNTPHA', 'FUNPHA', 'ELFPHA',
        'AMBPHP', 'BCDPHA', 'CHATPHP', 'CMTPHP', 'CVCPHA',
        'DATXPHP', 'DENTPHP', 'DLTPHA', 'DOCKPHP', 'FTPHA',
        'GOPHA', 'HOTPHA', 'IOSTPHP', 'KEYPHA', 'LENDPHP',
        'LSKPHA', 'LTOPHP', 'LUNAPHP', 'MFTPHA', 'MTLPHA',
        'NULSPHP', 'ONGPHA', 'ONTPHA', 'PHBPHA', 'PIVXPHP',
        'POEPHA', 'POWRPHP', 'RLCPHA', 'RPXPHA', 'RVNPHP',
        'SCPHA', 'SKYPHA', 'STORMPHP', 'STRATPHP', 'SUBPHA',
        'TFUELPHP', 'THETAPHP', 'TNBPHA', 'TOMOPHA', 'TRBPHA',
        'TRUPHA', 'TUSDPHP', 'TVKPHA', 'VENPHA', 'VIAPHA',
        'VITEPHA', 'WANPHA', 'WAVESPHP', 'WINPHA', 'WTCPHA',
        'XEMPHA', 'XTZPHP', 'XVGPHA', 'XVSPHA', 'ZILPHA',
        'PEPEPHP', 'FLOKIPHP', 'BONKPHP', 'WIFPHP', 'DOGSPHP'
    ]

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
        print(f"❌ Error getting symbol suggestions: {e}")
        return []

def main():
    try:
        print("🔮 PROPHET v3.0 - Enhanced Comprehensive Parameter Optimizer")
        print("🎯 NEW: Market-based parameter ranges + Interactive configuration")
        print("💾 Optimized recommendations saved for TITAN integration")
        print("=" * 75)
        
        if not os.getenv('COINS_API_KEY'):
            print("❌ API keys not found in environment")
            return
        
        print("🔮 Select asset for enhanced TITAN optimization:")
        print("1. XRPPHP - Stable performer")
        print("2. SOLPHP - Higher volatility")
        print("3. BTCPHP - Conservative choice")
        print("4. ETHPHP - Popular altcoin")
        print("5. Browse all PHP pairs")
        print("6. Custom pair")
        
        choice = input("🔮 Choose your asset (1-6): ").strip()
        
        if choice == '5':
            print("\n🔍 Getting available pairs...")
            pairs = get_available_pairs()
            
            if not pairs:
                print("❌ Could not retrieve trading pairs")
                print("🔮 PROPHET suggests trying option 6 (Custom pair) or options 1-4")
                return
            
            print(f"\n📊 Available PHP pairs ({len(pairs)} total):")
            for i, pair in enumerate(pairs, 1):
                print(f"{i:2d}. {pair}")
            
            while True:
                try:
                    pair_choice = int(input(f"\nSelect pair (1-{len(pairs)}): "))
                    if 1 <= pair_choice <= len(pairs):
                        symbol = pairs[pair_choice - 1]
                        break
                    else:
                        print(f"⚠️  Please enter 1-{len(pairs)}")
                except ValueError:
                    print("⚠️  Please enter a valid number")
                except KeyboardInterrupt:
                    print("\n🔮 PROPHET v3.0 session ended gracefully")
                    return
                    
        elif choice == '6':
            try:
                symbol = input("Enter trading pair (e.g., DOGEPHP): ").strip().upper()
                if not symbol.endswith('PHP'):
                    symbol += 'PHP'
            except KeyboardInterrupt:
                print("\n🔮 PROPHET v3.0 session ended gracefully")
                return
            
        else:
            symbol_map = {
                '1': 'XRPPHP',
                '2': 'SOLPHP', 
                '3': 'BTCPHP',
                '4': 'ETHPHP'
            }
            symbol = symbol_map.get(choice, 'XRPPHP')
        
        print(f"\n🎯 Starting enhanced optimization for {symbol}...")
        
        # Initialize Prophet with enhanced capabilities
        prophet = ProphetEnhanced(symbol)
        
        # Validate symbol with market analysis
        if not prophet.validate_symbol():
            print("❌ Symbol validation failed!")
            return
        
        # Get market data for asset-specific parameter ranges
        prophet.market_data = prophet.get_market_data_analysis()
        if not prophet.market_data:
            print("❌ Market data analysis failed!")
            return
        
        # Get asset-specific parameter ranges with override capability
        volatility = prophet.market_data['volatility']
        param_config = prophet.get_asset_specific_parameters(volatility, allow_override=True)
        
        # Set the parameters for optimization
        prophet.buy_thresholds = param_config['buy_thresholds']
        prophet.sell_thresholds = param_config['sell_thresholds']
        prophet.take_profit_levels = param_config['take_profit_range']
        
        print(f"\n✅ Configuration complete!")
        print(f"🎯 Asset Category: {param_config['category']}")
        print(f"📊 Testing {len(prophet.take_profit_levels)} TP × {len(prophet.buy_thresholds)} buy combinations")
        
        try:
            confirm = input(f"🔮 Start enhanced optimization? (y/n): ").lower()
            if not confirm.startswith('y'):
                print("🔮 PROPHET v3.0 awaits your return.")
                return
        except KeyboardInterrupt:
            print("\n🔮 PROPHET v3.0 session ended gracefully")
            return
        
        # Run enhanced optimization
        results = prophet.find_optimal_parameters([30, 60])
        
        if results:
            best_config, period_results = prophet.show_titan_configuration(results)
            
            if best_config is not None:
                # Save enhanced recommendations for TITAN
                save_success = prophet.save_recommendations_for_titan(best_config, symbol)
                
                if save_success:
                    print(f"\n🎉 PROPHET v3.0 ENHANCED OPTIMIZATION COMPLETE!")
                    print(f"💾 Enhanced recommendations saved to prophet_reco.json")
                    print(f"🤖 TITAN will now load these market-optimized settings for {symbol}")
                    
                    print(f"\n📋 NEXT STEPS:")
                    print("=" * 60)
                    print("🔮 python prophet.py → ✅ DONE (generated enhanced recommendations)")
                    print("🤖 python titan.py   → Load Prophet's market-optimized findings")
                    print("=" * 60)
                    print(f"✨ When you run TITAN, it will automatically suggest:")
                    print(f"   📈 Buy: {best_config['buy_threshold']:.1f}% (market-optimized)")
                    print(f"   📉 Sell: {best_config['sell_threshold']:.1f}% (calculated)")
                    print(f"   🎯 TP: {best_config['take_profit']:.1f}% (volatility-based)")
                    print(f"   (You can still customize any values in TITAN)")
                else:
                    print("❌ Failed to save enhanced recommendations")
            else:
                print("❌ No optimal configuration found")
        else:
            print("❌ No results generated. Check your data connection.")
            
    except KeyboardInterrupt:
        print("\n🔮 PROPHET v3.0 session ended gracefully")
        print("✨ Thank you for consulting enhanced PROPHET")
    except Exception as e:
        print(f"\n❌ PROPHET v3.0 encountered an error: {e}")
        print("🔮 Please try again or check your configuration")

if __name__ == "__main__":
    main()