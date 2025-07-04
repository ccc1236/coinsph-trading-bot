import os
from datetime import datetime
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class MicroGridBacktester:
    def __init__(self, symbol='USDTPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.initial_balance = 2000  # ₱2000 starting balance
        
        # MICRO-GRID parameters (much smaller than regular grid)
        self.base_grid_amount = 100      # ₱100 per grid level
        self.micro_grid_spacing = 0.003  # 0.3% spacing (vs 1.5% for XRP)
        self.num_grids = 4               # More levels for micro movements
        self.max_total_investment = 800  # Max ₱800 invested (40% of capital)
        
        # Enhanced settings for stablecoins
        self.rebalance_threshold = 0.0015  # 0.15% to rebalance (very tight)
        self.min_trade_size = 50           # ₱50 minimum
        
        # Trading fees
        self.maker_fee = 0.0025  # 0.25% maker fee
        
        # Backtest state
        self.php_balance = self.initial_balance
        self.asset_balance = 0  # USDT or USDC balance
        self.active_orders = []
        self.trade_history = []
        self.total_trades = 0
        self.total_fees_paid = 0
        self.last_center_price = None
        self.portfolio_history = []
        self.grid_rebalances = 0
        
        asset_name = symbol.replace('PHP', '')
        print(f"🔬 Micro-Grid Backtester for {symbol}")
        print(f"💰 Starting balance: ₱{self.initial_balance}")
        print(f"📏 Micro-grid spacing: {self.micro_grid_spacing*100:.1f}% (ultra-tight)")
        print(f"🔢 Grid levels: {self.num_grids} each side")
        print(f"💰 Grid amount: ₱{self.base_grid_amount} per level")
        print(f"⚖️ Max investment: ₱{self.max_total_investment}")
    
    def get_historical_data(self, days=30):
        """Get historical data for micro-grid backtesting"""
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
                print(f"From: {processed_data[0]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                print(f"To: {processed_data[-1]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                return processed_data, actual_days
            else:
                print("❌ No data received")
                return None, 0
            
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
            return None, 0
    
    def calculate_fees(self, amount):
        """Calculate trading fees"""
        return amount * self.maker_fee
    
    def place_micro_grid_orders(self, center_price):
        """Place micro-grid orders around center price"""
        self.active_orders = []
        self.last_center_price = center_price
        orders_placed = 0
        
        available_php = max(0, self.php_balance - 200)  # Keep ₱200 buffer
        
        # BUY orders below current price (micro spacing)
        for i in range(1, self.num_grids + 1):
            buy_price = center_price * (1 - self.micro_grid_spacing * i)
            total_cost = self.base_grid_amount + self.calculate_fees(self.base_grid_amount)
            
            if available_php >= total_cost and len([o for o in self.active_orders if o['side'] == 'BUY']) * self.base_grid_amount < self.max_total_investment:
                quantity = self.base_grid_amount / buy_price
                
                self.active_orders.append({
                    'side': 'BUY',
                    'price': buy_price,
                    'quantity': quantity,
                    'amount': self.base_grid_amount,
                    'level': i
                })
                orders_placed += 1
                available_php -= total_cost
        
        # SELL orders above current price
        if self.asset_balance > 0.001:
            available_asset = self.asset_balance
            for i in range(1, self.num_grids + 1):
                sell_price = center_price * (1 + self.micro_grid_spacing * i)
                max_quantity = min(available_asset / self.num_grids, self.base_grid_amount / sell_price)
                
                if max_quantity > 0.001:
                    amount = max_quantity * sell_price
                    
                    self.active_orders.append({
                        'side': 'SELL',
                        'price': sell_price,
                        'quantity': max_quantity,
                        'amount': amount,
                        'level': i
                    })
                    orders_placed += 1
                    available_asset -= max_quantity
        
        return orders_placed
    
    def check_micro_fills(self, candle):
        """Check for micro-grid order fills"""
        high_price = candle['high']
        low_price = candle['low']
        timestamp = candle['timestamp']
        filled_orders = []
        
        for order in self.active_orders[:]:
            order_filled = False
            
            if order['side'] == 'BUY' and low_price <= order['price']:
                # Execute micro buy
                fee = self.calculate_fees(order['amount'])
                total_cost = order['amount'] + fee
                
                if self.php_balance >= total_cost:
                    self.php_balance -= total_cost
                    self.asset_balance += order['quantity']
                    self.total_fees_paid += fee
                    
                    filled_orders.append({
                        'timestamp': timestamp,
                        'side': 'BUY',
                        'price': order['price'],
                        'quantity': order['quantity'],
                        'amount': order['amount'],
                        'fee': fee,
                        'level': order['level']
                    })
                    
                    order_filled = True
                    
            elif order['side'] == 'SELL' and high_price >= order['price']:
                # Execute micro sell
                if self.asset_balance >= order['quantity']:
                    gross_amount = order['amount']
                    fee = self.calculate_fees(gross_amount)
                    net_amount = gross_amount - fee
                    
                    self.php_balance += net_amount
                    self.asset_balance -= order['quantity']
                    self.total_fees_paid += fee
                    
                    filled_orders.append({
                        'timestamp': timestamp,
                        'side': 'SELL',
                        'price': order['price'],
                        'quantity': order['quantity'],
                        'amount': gross_amount,
                        'net_amount': net_amount,
                        'fee': fee,
                        'level': order['level']
                    })
                    
                    order_filled = True
            
            if order_filled:
                self.trade_history.append(filled_orders[-1])
                self.total_trades += 1
                self.active_orders.remove(order)
        
        return filled_orders
    
    def should_rebalance_micro_grid(self, current_price):
        """Check if micro-grid should be rebalanced"""
        if self.last_center_price is None:
            return True
        
        price_change = abs(current_price - self.last_center_price) / self.last_center_price
        return price_change > self.rebalance_threshold
    
    def calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.php_balance + (self.asset_balance * current_price)
    
    def run_micro_grid_backtest(self, days=30):
        """Run micro-grid backtesting"""
        print("\n🔬 Starting Micro-Grid Backtesting")
        print("=" * 60)
        
        data, actual_days = self.get_historical_data(days)
        if not data:
            return None
        
        print(f"\n📊 Testing micro-grid strategy:")
        print(f"💰 Starting balance: ₱{self.initial_balance}")
        print(f"📏 Micro-grid spacing: {self.micro_grid_spacing*100:.1f}%")
        print(f"🔢 Grid levels: {self.num_grids} each side")
        print(f"💰 Trade size: ₱{self.base_grid_amount}")
        print(f"🔄 Rebalance threshold: {self.rebalance_threshold*100:.2f}%")
        print()
        
        # Initialize
        start_price = data[0]['close']
        self.place_micro_grid_orders(start_price)
        
        min_price = float('inf')
        max_price = 0
        trades_shown = 0
        
        # Process each hour
        for i, candle in enumerate(data):
            current_price = candle['close']
            min_price = min(min_price, candle['low'])
            max_price = max(max_price, candle['high'])
            
            # Check for fills
            filled_orders = self.check_micro_fills(candle)
            
            # Show first few trades
            for trade in filled_orders:
                if trades_shown < 10:
                    print(f"🔬 {trade['side']}: ₱{trade['amount']:.2f} at ₱{trade['price']:.3f} (Level {trade['level']})")
                    trades_shown += 1
                elif trades_shown == 10:
                    print("... (showing first 10 trades only)")
                    trades_shown += 1
            
            # Rebalance if needed
            if filled_orders and self.should_rebalance_micro_grid(current_price):
                self.place_micro_grid_orders(current_price)
                self.grid_rebalances += 1
            
            # Track portfolio
            portfolio_value = self.calculate_portfolio_value(current_price)
            self.portfolio_history.append({
                'timestamp': candle['timestamp'],
                'price': current_price,
                'portfolio_value': portfolio_value
            })
        
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
        
        # Price statistics
        price_range = max_price - min_price
        price_range_pct = (price_range / start_price) * 100
        
        # Display results
        print(f"\n🎯 MICRO-GRID BACKTEST RESULTS")
        print("=" * 60)
        print(f"📅 Period: {data[0]['timestamp'].strftime('%Y-%m-%d')} to {data[-1]['timestamp'].strftime('%Y-%m-%d')}")
        print(f"📊 Actual days tested: {actual_days}")
        print(f"📊 Price range: ₱{min_price:.3f} - ₱{max_price:.3f}")
        print(f"📊 Total price range: ₱{price_range:.3f} ({price_range_pct:.2f}%)")
        print(f"💹 Start price: ₱{start_price:.3f}")
        print(f"💹 End price: ₱{final_price:.3f}")
        print(f"📈 Price change: {((final_price - start_price) / start_price) * 100:+.2f}%")
        print()
        print("🔬 MICRO-GRID STRATEGY PERFORMANCE:")
        print(f"💰 Starting value: ₱{self.initial_balance:.2f}")
        print(f"💰 Final value: ₱{final_portfolio_value:.2f}")
        print(f"📈 Total return: ₱{total_return:.2f} ({return_percentage:+.2f}%)")
        print(f"📊 Annualized return: {annualized_return:+.1f}%")
        print(f"💸 Total fees paid: ₱{self.total_fees_paid:.2f}")
        print(f"🔄 Total trades: {self.total_trades}")
        print(f"⚖️ Grid rebalances: {self.grid_rebalances}")
        print(f"📈 Trades per day: {self.total_trades / max(actual_days, 1):.1f}")
        
        asset_name = self.symbol.replace('PHP', '')
        print(f"\n💰 Final balances:")
        print(f"   PHP: ₱{self.php_balance:.2f}")
        print(f"   {asset_name}: {self.asset_balance:.6f} (worth ₱{self.asset_balance * final_price:.2f})")
        
        # Analysis
        print(f"\n📊 MICRO-GRID ANALYSIS:")
        fee_percentage = (self.total_fees_paid / self.initial_balance) * 100
        print(f"   💸 Fees as % of capital: {fee_percentage:.2f}%")
        
        if self.total_trades > 0:
            avg_return_per_trade = total_return / self.total_trades
            print(f"   💰 Average return per trade: ₱{avg_return_per_trade:.2f}")
        
        print(f"   📏 Grid spacing used: {self.micro_grid_spacing*100:.1f}%")
        print(f"   🎯 Price range needed for profit: >{(self.maker_fee * 4)*100:.1f}%")
        print(f"   📊 Actual price range captured: {price_range_pct:.2f}%")
        
        # Verdict
        if return_percentage > 1:
            print(f"\n✅ MICRO-GRID VIABLE: {return_percentage:+.2f}% return in {actual_days} days!")
        elif return_percentage > 0:
            print(f"\n🟡 MICRO-GRID MARGINAL: {return_percentage:+.2f}% return, small but positive")
        else:
            print(f"\n❌ MICRO-GRID NOT VIABLE: {return_percentage:+.2f}% return, losses exceed gains")
        
        print("=" * 60)
        
        return {
            'total_return': total_return,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            'total_trades': self.total_trades,
            'total_fees': self.total_fees_paid,
            'price_range_pct': price_range_pct,
            'viable': return_percentage > 0.5
        }

def main():
    print("🔬 Micro-Grid Strategy Backtester")
    print("=" * 40)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    print("Select stablecoin to test:")
    print("1. USDTPHP (highest volume)")
    print("2. USDCPHP (second highest)")
    
    choice = input("Enter choice (1-2): ").strip()
    symbol = 'USDTPHP' if choice == '1' else 'USDCPHP'
    
    try:
        days_input = input("How many days to test? (7-30): ").strip()
        days = int(days_input) if days_input else 14
        days = max(7, min(days, 30))
    except ValueError:
        days = 14
    
    print(f"\nTesting {symbol} micro-grid for {days} days...")
    
    backtester = MicroGridBacktester(symbol)
    results = backtester.run_micro_grid_backtest(days)
    
    if results:
        print(f"\n💡 MICRO-GRID CONCLUSION:")
        
        if results['viable']:
            print(f"🚀 Micro-grid strategy shows promise for {symbol}!")
            print(f"📊 Consider live testing with small amounts")
        else:
            print(f"⚠️ Micro-grid may not be profitable for {symbol}")
            print(f"📊 Stablecoin volatility too low for current parameters")
        
        print(f"\n🔍 Next steps:")
        print(f"   1. Compare with XRP momentum results")
        print(f"   2. Test arbitrage monitoring")
        print(f"   3. Consider parameter optimization")

if __name__ == "__main__":
    main()