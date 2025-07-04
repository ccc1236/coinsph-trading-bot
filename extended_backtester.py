import os
from datetime import datetime
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class ExtendedGridBacktester:
    def __init__(self, symbol='XRPPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        self.symbol = symbol
        self.grid_amount = 100  # ₱100 per grid level
        self.grid_spacing = 0.015  # 1.5%
        self.num_grids = 3
        self.initial_balance = 2000  # ₱2000 starting balance
        
        # Backtest state
        self.php_balance = self.initial_balance
        self.xrp_balance = 0
        self.active_orders = []
        self.trade_history = []
        self.total_trades = 0
        self.portfolio_history = []
        
    def get_historical_data(self, days=30):
        """Get historical kline data with smart interval selection"""
        print(f"📊 Fetching {days} days of historical data for {self.symbol}...")
        
        # Choose interval based on time period
        if days <= 7:
            interval = '1h'
            limit = days * 24
            print(f"Using 1-hour intervals ({limit} data points)")
        elif days <= 30:
            interval = '1h'
            limit = days * 24
            print(f"Using 1-hour intervals ({limit} data points)")
        elif days <= 90:
            interval = '4h'
            limit = days * 6  # 6 data points per day (24h / 4h)
            print(f"Using 4-hour intervals ({limit} data points)")
        else:
            interval = '1d'
            limit = days  # 1 data point per day
            print(f"Using daily intervals ({limit} data points)")
        
        try:
            klines = self.api._make_request(
                'GET', 
                '/openapi/quote/v1/klines',
                {
                    'symbol': self.symbol,
                    'interval': interval,
                    'limit': min(limit, 1000)  # Most APIs limit to 1000
                }
            )
            
            # Process data
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
                print(f"✅ Got {len(processed_data)} data points covering {actual_days} days")
                print(f"From: {processed_data[0]['timestamp'].strftime('%Y-%m-%d')}")
                print(f"To: {processed_data[-1]['timestamp'].strftime('%Y-%m-%d')}")
                return processed_data, interval
            else:
                print("❌ No data received")
                return None, None
            
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
            return None, None
    
    def place_grid_orders(self, current_price):
        """Simulate placing grid orders"""
        self.active_orders = []
        orders_placed = 0
        
        # BUY orders below current price
        for i in range(1, self.num_grids + 1):
            buy_price = current_price * (1 - self.grid_spacing * i)
            if self.php_balance >= self.grid_amount:
                quantity = self.grid_amount / buy_price
                self.active_orders.append({
                    'side': 'BUY',
                    'price': buy_price,
                    'quantity': quantity,
                    'amount': self.grid_amount
                })
                orders_placed += 1
        
        # SELL orders above current price
        if self.xrp_balance > 0:
            available_xrp = self.xrp_balance
            for i in range(1, self.num_grids + 1):
                sell_price = current_price * (1 + self.grid_spacing * i)
                quantity = min(available_xrp / self.num_grids, self.grid_amount / sell_price)
                
                if quantity > 0.001:
                    self.active_orders.append({
                        'side': 'SELL',
                        'price': sell_price,
                        'quantity': quantity,
                        'amount': quantity * sell_price
                    })
                    orders_placed += 1
                    available_xrp -= quantity
        
        return orders_placed
    
    def check_order_fills(self, candle):
        """Check if any orders should be filled"""
        high_price = candle['high']
        low_price = candle['low']
        timestamp = candle['timestamp']
        filled_orders = []
        
        for order in self.active_orders[:]:
            if order['side'] == 'BUY' and low_price <= order['price']:
                if self.php_balance >= order['amount']:
                    self.php_balance -= order['amount']
                    self.xrp_balance += order['quantity']
                    
                    filled_orders.append({
                        'timestamp': timestamp,
                        'side': 'BUY',
                        'price': order['price'],
                        'quantity': order['quantity'],
                        'amount': order['amount']
                    })
                    
                    self.trade_history.append(filled_orders[-1])
                    self.total_trades += 1
                    self.active_orders.remove(order)
            
            elif order['side'] == 'SELL' and high_price >= order['price']:
                if self.xrp_balance >= order['quantity']:
                    self.php_balance += order['amount']
                    self.xrp_balance -= order['quantity']
                    
                    filled_orders.append({
                        'timestamp': timestamp,
                        'side': 'SELL',
                        'price': order['price'],
                        'quantity': order['quantity'],
                        'amount': order['amount']
                    })
                    
                    self.trade_history.append(filled_orders[-1])
                    self.total_trades += 1
                    self.active_orders.remove(order)
        
        return filled_orders
    
    def calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.php_balance + (self.xrp_balance * current_price)
    
    def run_backtest(self, days=30):
        """Run the extended grid trading backtest"""
        print("🔲 Starting Extended Grid Trading Backtest")
        print("=" * 60)
        
        # Get historical data
        data, interval = self.get_historical_data(days)
        if not data:
            return None
        
        actual_days = (data[-1]['timestamp'] - data[0]['timestamp']).days
        print(f"📊 Testing strategy on {len(data)} {interval} candles ({actual_days} actual days)")
        print(f"💰 Starting balance: ₱{self.initial_balance}")
        print(f"🔲 Grid spacing: {self.grid_spacing*100}%")
        print(f"📏 Grid levels: {self.num_grids} each side")
        print()
        
        # Initialize
        start_price = data[0]['close']
        self.place_grid_orders(start_price)
        
        grid_rebalances = 0
        min_price = float('inf')
        max_price = 0
        
        # Process each candle
        for i, candle in enumerate(data):
            current_price = candle['close']
            min_price = min(min_price, candle['low'])
            max_price = max(max_price, candle['high'])
            
            # Check for order fills
            filled_orders = self.check_order_fills(candle)
            
            # Rebalance grid if orders filled
            if filled_orders:
                self.place_grid_orders(current_price)
                grid_rebalances += 1
            
            # Track portfolio value
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
        
        # Buy and hold comparison
        initial_xrp_if_bought = self.initial_balance / start_price
        buy_hold_value = initial_xrp_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Display results
        print("🎯 EXTENDED BACKTEST RESULTS")
        print("=" * 60)
        print(f"📅 Period: {data[0]['timestamp'].strftime('%Y-%m-%d')} to {data[-1]['timestamp'].strftime('%Y-%m-%d')}")
        print(f"📊 Actual days tested: {actual_days}")
        print(f"📊 Data interval: {interval}")
        print(f"📊 Price range: ₱{min_price:.2f} - ₱{max_price:.2f}")
        print(f"💹 Start price: ₱{start_price:.2f}")
        print(f"💹 End price: ₱{final_price:.2f}")
        print(f"📈 XRP price change: {((final_price - start_price) / start_price) * 100:+.2f}%")
        print()
        print("🔲 GRID STRATEGY PERFORMANCE:")
        print(f"💰 Starting value: ₱{self.initial_balance:.2f}")
        print(f"💰 Final value: ₱{final_portfolio_value:.2f}")
        print(f"📈 Total return: ₱{total_return:.2f} ({return_percentage:+.2f}%)")
        print(f"📊 Annualized return: {annualized_return:+.1f}%")
        print(f"🔄 Total trades: {self.total_trades}")
        print(f"⚖️  Grid rebalances: {grid_rebalances}")
        print(f"📈 Trades per day: {self.total_trades / max(actual_days, 1):.1f}")
        print()
        print("📊 BUY & HOLD COMPARISON:")
        print(f"💰 Buy & hold value: ₱{buy_hold_value:.2f}")
        print(f"📈 Buy & hold return: ₱{buy_hold_return:.2f} ({buy_hold_percentage:+.2f}%)")
        print()
        
        if return_percentage > buy_hold_percentage:
            outperformance = return_percentage - buy_hold_percentage
            print(f"🏆 Grid strategy OUTPERFORMED buy & hold by {outperformance:+.2f}%!")
        else:
            underperformance = buy_hold_percentage - return_percentage
            print(f"📉 Grid strategy underperformed buy & hold by {underperformance:.2f}%")
        
        # Performance metrics
        if self.total_trades > 0:
            avg_return_per_trade = total_return / self.total_trades
            print(f"\n📊 PERFORMANCE METRICS:")
            print(f"   Average return per trade: ₱{avg_return_per_trade:.2f}")
            
            # Calculate max drawdown
            max_value = self.initial_balance
            max_drawdown = 0
            for record in self.portfolio_history:
                max_value = max(max_value, record['portfolio_value'])
                current_drawdown = (max_value - record['portfolio_value']) / max_value
                max_drawdown = max(max_drawdown, current_drawdown)
            
            print(f"   Maximum drawdown: {max_drawdown*100:.2f}%")
        
        print("=" * 60)
        
        return {
            'total_return': total_return,
            'return_percentage': return_percentage,
            'annualized_return': annualized_return,
            'total_trades': self.total_trades,
            'actual_days': actual_days,
            'outperformed_buy_hold': return_percentage > buy_hold_percentage
        }

def main():
    """Main function"""
    print("🔲 Extended Grid Trading Strategy Backtester")
    print("=" * 50)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ COINS_API_KEY not found in .env file")
        return
    
    symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')
    print(f"Testing symbol: {symbol}")
    
    try:
        days_input = input("How many days of history to test? (7-365): ").strip()
        days = int(days_input) if days_input else 30
        days = max(7, min(days, 365))  # Limit to 7-365 days
    except ValueError:
        days = 30
    
    print(f"Testing {days} days of history...")
    print()
    
    # Run extended backtest
    backtester = ExtendedGridBacktester(symbol)
    results = backtester.run_backtest(days)
    
    if results:
        print(f"\n💡 CONCLUSION after {results['actual_days']} days of backtesting:")
        
        if results['return_percentage'] > 5:
            print("🚀 Excellent returns! Grid strategy highly profitable!")
        elif results['return_percentage'] > 2:
            print("✅ Good returns! Grid strategy profitable!")
        elif results['return_percentage'] > 0:
            print("🟡 Modest positive returns")
        else:
            print("⚠️  Negative returns - consider different parameters")
        
        if results['annualized_return'] > 20:
            print(f"🔥 Amazing annualized return: {results['annualized_return']:.1f}%!")
        elif results['annualized_return'] > 10:
            print(f"💰 Great annualized return: {results['annualized_return']:.1f}%")
        
        if results['outperformed_buy_hold']:
            print("🎯 Grid trading strategy is working!")
        
        print(f"\n🤖 Total trades in {results['actual_days']} days: {results['total_trades']}")

if __name__ == "__main__":
    main()