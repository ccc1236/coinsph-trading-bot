import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class GridBacktester:
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
        self.total_profit = 0
        
    def get_historical_data(self, days=7):
        """Get historical kline data"""
        print(f"📊 Fetching {days} days of historical data for {self.symbol}...")
        
        try:
            # Get kline data (1 hour intervals for better granularity)
            klines = self.api._make_request(
                'GET', 
                '/openapi/quote/v1/klines',
                {
                    'symbol': self.symbol,
                    'interval': '1h',
                    'limit': days * 24  # 24 hours per day
                }
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_volume', 'taker_buy_quote_volume'
            ])
            
            # Convert to proper types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            print(f"✅ Got {len(df)} data points from {df['timestamp'].min()} to {df['timestamp'].max()}")
            return df
            
        except Exception as e:
            print(f"❌ Error getting historical data: {e}")
            return None
    
    def place_grid_orders(self, current_price):
        """Simulate placing grid orders"""
        # Clear existing orders
        self.active_orders = []
        
        orders_placed = 0
        
        # Place BUY orders below current price
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
        
        # Place SELL orders above current price (if we have XRP)
        if self.xrp_balance > 0:
            available_xrp = self.xrp_balance
            for i in range(1, self.num_grids + 1):
                sell_price = current_price * (1 + self.grid_spacing * i)
                
                # Use portion of available XRP
                quantity = min(available_xrp / self.num_grids, self.grid_amount / sell_price)
                
                if quantity > 0.001:  # Minimum amount
                    self.active_orders.append({
                        'side': 'SELL',
                        'price': sell_price,
                        'quantity': quantity,
                        'amount': quantity * sell_price
                    })
                    orders_placed += 1
                    available_xrp -= quantity
        
        return orders_placed
    
    def check_order_fills(self, row):
        """Check if any orders should be filled based on price action"""
        high_price = row['high']
        low_price = row['low']
        timestamp = row['timestamp']
        
        filled_orders = []
        
        for order in self.active_orders[:]:  # Create copy to iterate safely
            if order['side'] == 'BUY' and low_price <= order['price']:
                # Buy order filled
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
                # Sell order filled
                if self.xrp_balance >= order['quantity']:
                    self.php_balance += order['amount']
                    self.xrp_balance -= order['quantity']
                    
                    # Calculate profit (assuming we bought lower)
                    profit = order['amount'] - self.grid_amount
                    self.total_profit += profit
                    
                    filled_orders.append({
                        'timestamp': timestamp,
                        'side': 'SELL',
                        'price': order['price'],
                        'quantity': order['quantity'],
                        'amount': order['amount'],
                        'profit': profit
                    })
                    
                    self.trade_history.append(filled_orders[-1])
                    self.total_trades += 1
                    self.active_orders.remove(order)
        
        return filled_orders
    
    def calculate_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        xrp_value = self.xrp_balance * current_price
        return self.php_balance + xrp_value
    
    def run_backtest(self, days=7):
        """Run the grid trading backtest"""
        print("🔲 Starting Grid Trading Backtest")
        print("=" * 50)
        
        # Get historical data
        df = self.get_historical_data(days)
        if df is None or len(df) == 0:
            print("❌ No historical data available")
            return
        
        print(f"📊 Testing strategy on {len(df)} hours of data")
        print(f"💰 Starting balance: ₱{self.initial_balance}")
        print(f"🔲 Grid spacing: {self.grid_spacing*100}%")
        print(f"📏 Grid levels: {self.num_grids} each side")
        print()
        
        # Initialize with first price
        start_price = df.iloc[0]['close']
        self.place_grid_orders(start_price)
        
        portfolio_values = []
        grid_rebalances = 0
        
        # Process each hour
        for idx, row in df.iterrows():
            current_price = row['close']
            
            # Check for order fills
            filled_orders = self.check_order_fills(row)
            
            # Rebalance grid if needed (when orders are filled)
            if filled_orders:
                self.place_grid_orders(current_price)
                grid_rebalances += 1
            
            # Track portfolio value
            portfolio_value = self.calculate_portfolio_value(current_price)
            portfolio_values.append({
                'timestamp': row['timestamp'],
                'price': current_price,
                'portfolio_value': portfolio_value,
                'php_balance': self.php_balance,
                'xrp_balance': self.xrp_balance
            })
        
        # Calculate final results
        final_price = df.iloc[-1]['close']
        final_portfolio_value = self.calculate_portfolio_value(final_price)
        total_return = final_portfolio_value - self.initial_balance
        return_percentage = (total_return / self.initial_balance) * 100
        
        # Buy and hold comparison
        initial_xrp_if_bought = self.initial_balance / start_price
        buy_hold_value = initial_xrp_if_bought * final_price
        buy_hold_return = buy_hold_value - self.initial_balance
        buy_hold_percentage = (buy_hold_return / self.initial_balance) * 100
        
        # Display results
        print("🎯 BACKTEST RESULTS")
        print("=" * 50)
        print(f"📅 Period: {df.iloc[0]['timestamp'].strftime('%Y-%m-%d %H:%M')} to {df.iloc[-1]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 Price range: ₱{df['low'].min():.2f} - ₱{df['high'].max():.2f}")
        print(f"💹 Start price: ₱{start_price:.2f}")
        print(f"💹 End price: ₱{final_price:.2f}")
        print()
        print("🔲 GRID STRATEGY PERFORMANCE:")
        print(f"💰 Starting value: ₱{self.initial_balance:.2f}")
        print(f"💰 Final value: ₱{final_portfolio_value:.2f}")
        print(f"📈 Total return: ₱{total_return:.2f} ({return_percentage:+.2f}%)")
        print(f"🔄 Total trades: {self.total_trades}")
        print(f"⚖️  Grid rebalances: {grid_rebalances}")
        print(f"💵 Trading profits: ₱{self.total_profit:.2f}")
        print()
        print("📊 BUY & HOLD COMPARISON:")
        print(f"💰 Buy & hold value: ₱{buy_hold_value:.2f}")
        print(f"📈 Buy & hold return: ₱{buy_hold_return:.2f} ({buy_hold_percentage:+.2f}%)")
        print()
        
        if return_percentage > buy_hold_percentage:
            print("🏆 Grid strategy OUTPERFORMED buy & hold!")
        else:
            print("📉 Grid strategy underperformed buy & hold")
        
        print("=" * 50)
        
        # Show recent trades
        if self.trade_history:
            print("\n📋 RECENT TRADES (Last 10):")
            for trade in self.trade_history[-10:]:
                profit_str = f" (Profit: ₱{trade.get('profit', 0):.2f})" if trade['side'] == 'SELL' else ""
                print(f"   {trade['timestamp'].strftime('%m-%d %H:%M')} | "
                      f"{trade['side']} {trade['quantity']:.4f} XRP at ₱{trade['price']:.2f}{profit_str}")
        
        return {
            'portfolio_values': portfolio_values,
            'total_return': total_return,
            'return_percentage': return_percentage,
            'total_trades': self.total_trades,
            'buy_hold_return': buy_hold_return,
            'buy_hold_percentage': buy_hold_percentage
        }

def main():
    """Main function to run backtest"""
    print("🔲 Grid Trading Strategy Backtester")
    print("=" * 40)
    
    # Check API keys
    if not os.getenv('COINS_API_KEY'):
        print("❌ COINS_API_KEY not found in .env file")
        return
    
    # Get parameters
    symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')
    print(f"Testing symbol: {symbol}")
    
    try:
        days = int(input("How many days of history to test? (1-30): ") or "7")
        days = max(1, min(days, 30))  # Limit to 1-30 days
    except ValueError:
        days = 7
    
    # Run backtest
    backtester = GridBacktester(symbol)
    results = backtester.run_backtest(days)
    
    if results:
        print(f"\n💡 Based on {days} days of backtesting:")
        if results['return_percentage'] > 0:
            print("✅ Grid strategy shows positive returns!")
        else:
            print("⚠️  Grid strategy shows negative returns")
        
        if results['total_trades'] > 0:
            avg_profit_per_trade = results['total_return'] / results['total_trades']
            print(f"📊 Average profit per trade: ₱{avg_profit_per_trade:.2f}")
        
        print(f"\n🎯 Ready to run live grid bot? The backtest completed {results['total_trades']} trades.")

if __name__ == "__main__":
    main()