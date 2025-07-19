import os
import sys
import time
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

class ProphetSimplified:
    def __init__(self, symbol='SOLPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.initial_balance = 2000
        
        # Fixed parameters
        self.trade_amount = 200
        self.sell_percentage = 1.00  # 100% clean exits
        self.min_hold_minutes = 30
        self.max_trades_per_day = 10
        
        # Fees
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        
        # Test ranges for parameters
        self.buy_thresholds = [0.004, 0.006, 0.008, 0.010, 0.012, 0.015, 0.020]  # 0.4% to 2.0%
        self.sell_thresholds = [0.005, 0.008, 0.010, 0.012, 0.015, 0.020, 0.025]  # 0.5% to 2.5%
        
        # Test ranges for take profit
        self.take_profit_levels = [0.015, 0.020, 0.025, 0.030, 0.035, 0.040, 0.050, 0.060, 0.080, 0.100]  # 1.5% to 10%
        
        print(f"🔮 PROPHET - Optimizing for TITAN Bot")
        print(f"🎯 Asset: {symbol}")
        print(f"📊 Finding optimal parameters for TITAN configuration")
        print("=" * 60)

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
        """Get historical data"""
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
                return data, actual_days
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
                'reason': 'Momentum Buy'
            })
            
            return True
        
        return False

    def place_sell(self, price, time, change, reason):
        """Place sell order"""
        asset_to_sell = self.asset_balance * self.sell_percentage
        
        if asset_to_sell < 0.000001:
            return False
        
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
        
        # Calculate results
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
        """Find optimal parameters across multiple periods"""
        print(f"🔮 PROPHET is analyzing {self.symbol}...")
        print(f"📊 Testing {len(self.take_profit_levels)} TP × {len(self.buy_thresholds)} buy × {len(self.sell_thresholds)} sell")
        print(f"⏰ Across {days_list} day periods")
        print("-" * 60)
        
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
                        
                        if current_test % 50 == 0:
                            print(f"   Progress: {current_test}/{total_tests}")
                        
                        result = self.test_strategy(buy, sell, tp, data)
                        if result:
                            result['period'] = f"{days}_days"
                            result['actual_days'] = actual_days
                            period_results.append(result)
            
            all_results.extend(period_results)
            print(f"✅ Completed {days}-day analysis ({len(period_results)} combinations)")
        
        return all_results

    def show_titan_configuration(self, results):
        """Show optimal configuration for TITAN bot"""
        if not results:
            print("❌ No results to analyze")
            return
        
        # Find best overall strategy
        df = pd.DataFrame(results)
        best_overall = df.loc[df['return_pct'].idxmax()]
        
        # Find best per period
        period_results = {}
        for period in df['period'].unique():
            period_df = df[df['period'] == period]
            best_period = period_df.loc[period_df['return_pct'].idxmax()]
            period_results[period] = best_period
        
        print(f"\n🎯 PROPHET'S TITAN BOT CONFIGURATION")
        print("=" * 60)
        
        # Show best per period
        print(f"📊 Performance by Period:")
        for period, result in period_results.items():
            print(f"   {period:10s}: {result['return_pct']:+6.1f}% | "
                  f"Buy {result['buy_threshold']:4.1f}% | Sell {result['sell_threshold']:4.1f}% | "
                  f"TP {result['take_profit']:4.1f}%")
        
        print(f"\n🏆 OPTIMAL TITAN CONFIGURATION:")
        print("=" * 40)
        print(f"🎯 Asset to trade: {self.symbol}")
        print(f"📈 Buy threshold: {best_overall['buy_threshold']:.1f}%")
        print(f"📉 Sell threshold: {best_overall['sell_threshold']:.1f}%")
        print(f"🎯 Take profit level: {best_overall['take_profit']:.1f}%")
        print("💰 Position sizing: [Configure in TITAN as needed]")
        
        print(f"\n📈 Expected Performance:")
        print(f"   💰 Return: {best_overall['return_pct']:+.1f}%")
        print(f"   🎯 Win rate: {best_overall['win_rate']:.1f}%")
        print(f"   📊 TP hit rate: {best_overall['tp_rate']:.1f}%")
        print(f"   🔄 Trades: {best_overall['total_trades']}")
        print(f"   💸 Fees: {best_overall['fee_pct']:.1f}% of capital")
        
        print(f"\n🤖 COPY THESE VALUES TO TITAN:")
        print("=" * 40)
        print(f"Asset: {self.symbol}")
        print(f"Buy: {best_overall['buy_threshold']:.1f}")
        print(f"Sell: {best_overall['sell_threshold']:.1f}")
        print(f"Take Profit: {best_overall['take_profit']:.1f}")
        
        return best_overall, period_results

    def export_results(self, results, best_config):
        """Optional export of results"""
        export = input(f"\n💾 Export detailed results to CSV? (y/n): ").lower().startswith('y')
        
        if export:
            # Create logs directory if it doesn't exist
            logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
            os.makedirs(logs_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Export combined results
            df = pd.DataFrame(results)
            df_sorted = df.sort_values('return_pct', ascending=False)
            
            filename = os.path.join(logs_dir, f"prophet_titan_config_{self.symbol}_{timestamp}.csv")
            df_sorted.to_csv(filename, index=False)
            
            # Export summary
            summary_data = {
                'symbol': [self.symbol],
                'optimal_buy': [best_config['buy_threshold']],
                'optimal_sell': [best_config['sell_threshold']],
                'optimal_tp': [best_config['take_profit']],
                'expected_return': [best_config['return_pct']],
                'win_rate': [best_config['win_rate']],
                'tp_rate': [best_config['tp_rate']],
                'total_trades': [best_config['total_trades']],
                'analysis_date': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_filename = os.path.join(logs_dir, f"titan_config_summary_{self.symbol}_{timestamp}.csv")
            summary_df.to_csv(summary_filename, index=False)
            
            print(f"✅ Detailed results: logs/{os.path.basename(filename)}")
            print(f"✅ TITAN summary: logs/{os.path.basename(summary_filename)}")
        else:
            print("📊 Results not exported")

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

def main():
    try:
        print("🔮 PROPHET - TITAN Bot Configuration Generator")
        print("🎯 Finds optimal parameters for your TITAN bot")
        print("⚡ Simplified output with direct TITAN settings")
        print("=" * 55)
        
        if not os.getenv('COINS_API_KEY'):
            print("❌ API keys not found in environment")
            return
        
        print("🔮 Select asset for TITAN optimization:")
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
            
            if not pairs:  # This was the bug - empty pairs list
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
                    print("\n🔮 PROPHET session ended gracefully")
                    return
                    
        elif choice == '6':
            try:
                symbol = input("Enter trading pair (e.g., DOGEPHP): ").strip().upper()
                if not symbol.endswith('PHP'):
                    symbol += 'PHP'
            except KeyboardInterrupt:
                print("\n🔮 PROPHET session ended gracefully")
                return
            
        else:
            symbol_map = {
                '1': 'XRPPHP',
                '2': 'SOLPHP', 
                '3': 'BTCPHP',
                '4': 'ETHPHP'
            }
            symbol = symbol_map.get(choice, 'XRPPHP')
        
        print(f"\n🎯 Optimizing {symbol} for TITAN bot...")
        
        try:
            confirm = input(f"🔮 Start optimization? (y/n): ").lower()
            if not confirm.startswith('y'):
                print("🔮 PROPHET awaits your return.")
                return
        except KeyboardInterrupt:
            print("\n🔮 PROPHET session ended gracefully")
            return
        
        # Run optimization
        prophet = ProphetSimplified(symbol)
        results = prophet.find_optimal_parameters([30, 60])
        
        if results:
            best_config, period_results = prophet.show_titan_configuration(results)
            prophet.export_results(results, best_config)
            
            print(f"\n🔮 PROPHET's task is complete!")
            print(f"🤖 Use the configuration above in your TITAN bot")
            print(f"🚀 May profitable trades be with you!")
        else:
            print("❌ No results generated. Check your data connection.")
            
    except KeyboardInterrupt:
        print("\n🔮 PROPHET session ended gracefully")
        print("✨ Thank you for consulting PROPHET")
    except Exception as e:
        print(f"\n❌ PROPHET encountered an error: {e}")
        print("🔮 Please try again or check your configuration")

if __name__ == "__main__":
    main()