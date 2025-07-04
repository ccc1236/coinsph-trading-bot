import os
import time
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from coins_api import CoinsAPI

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('grid_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('GridBot')

class GridTradingBot:
    def __init__(self):
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Bot configuration
        self.symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')
        self.grid_amount = float(os.getenv('BASE_AMOUNT', 100))  # ₱100 per grid level
        
        # Grid settings
        self.grid_spacing = 0.015  # 1.5% between grid levels
        self.num_grids = 3         # 3 levels above and below
        self.max_total_investment = 1000  # Maximum ₱1000 invested at once
        
        # State tracking
        self.center_price = None
        self.active_orders = []    # Track our placed orders
        self.positions = {}        # Track our XRP holdings from grid
        self.running = False
        self.total_invested = 0
        self.total_profit = 0
        
        logger.info(f"🔲 Grid Bot initialized for {self.symbol}")
        logger.info(f"💰 Grid amount: ₱{self.grid_amount} per level")
        logger.info(f"📏 Grid spacing: {self.grid_spacing*100}%")
        logger.info(f"🔢 Grid levels: {self.num_grids} above and below")
    
    def get_current_price(self):
        """Get current market price"""
        try:
            return self.api.get_current_price(self.symbol)
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return None
    
    def get_balances(self):
        """Get current balances"""
        try:
            account = self.api.get_account_info()
            balances = {}
            
            for balance in account.get('balances', []):
                asset = balance['asset']
                free = float(balance['free'])
                if free > 0:
                    balances[asset] = free
            
            return balances
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
            return {}
    
    def cancel_all_orders(self):
        """Cancel all active orders for our symbol"""
        try:
            result = self.api.cancel_all_orders(self.symbol)
            logger.info(f"✅ Cancelled all orders: {result}")
            self.active_orders = []
            return True
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            return False
    
    def place_grid_orders(self, center_price):
        """Place grid buy and sell orders around center price"""
        logger.info(f"🔲 Setting up grid around ₱{center_price:.2f}")
        
        # Cancel any existing orders first
        self.cancel_all_orders()
        time.sleep(1)  # Wait a moment
        
        orders_placed = 0
        
        # Place BUY orders below current price
        for i in range(1, self.num_grids + 1):
            buy_price = center_price * (1 - self.grid_spacing * i)
            
            # Check if we have enough balance and haven't exceeded max investment
            if self.total_invested + self.grid_amount <= self.max_total_investment:
                try:
                    # Calculate quantity to buy
                    quantity = self.grid_amount / buy_price
                    
                    logger.info(f"📉 Placing BUY order: {quantity:.6f} XRP at ₱{buy_price:.2f} (₱{self.grid_amount})")
                    
                    order = self.api.place_order(
                        symbol=self.symbol,
                        side='BUY',
                        order_type='LIMIT',
                        quantity=f'{quantity:.6f}',
                        price=f'{buy_price:.2f}',
                        timeInForce='GTC'
                    )
                    
                    self.active_orders.append({
                        'id': order.get('orderId'),
                        'side': 'BUY',
                        'price': buy_price,
                        'quantity': quantity,
                        'amount': self.grid_amount
                    })
                    
                    orders_placed += 1
                    logger.info(f"✅ BUY order placed: Order ID {order.get('orderId')}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to place BUY order at ₱{buy_price:.2f}: {e}")
        
        # Place SELL orders above current price (only if we have XRP)
        balances = self.get_balances()
        xrp_balance = balances.get('XRP', 0)
        
        if xrp_balance > 0.01:  # If we have XRP to sell
            for i in range(1, self.num_grids + 1):
                sell_price = center_price * (1 + self.grid_spacing * i)
                
                # Use a portion of available XRP for each sell level
                max_sell_quantity = xrp_balance / self.num_grids
                sell_quantity = min(max_sell_quantity, self.grid_amount / sell_price)
                
                if sell_quantity > 0.01:  # Minimum meaningful amount
                    try:
                        logger.info(f"📈 Placing SELL order: {sell_quantity:.6f} XRP at ₱{sell_price:.2f}")
                        
                        order = self.api.place_order(
                            symbol=self.symbol,
                            side='SELL',
                            order_type='LIMIT',
                            quantity=f'{sell_quantity:.6f}',
                            price=f'{sell_price:.2f}',
                            timeInForce='GTC'
                        )
                        
                        self.active_orders.append({
                            'id': order.get('orderId'),
                            'side': 'SELL',
                            'price': sell_price,
                            'quantity': sell_quantity,
                            'amount': sell_quantity * sell_price
                        })
                        
                        orders_placed += 1
                        logger.info(f"✅ SELL order placed: Order ID {order.get('orderId')}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to place SELL order at ₱{sell_price:.2f}: {e}")
        
        logger.info(f"🔲 Grid setup complete: {orders_placed} orders placed")
        return orders_placed > 0
    
    def check_filled_orders(self):
        """Check if any of our orders have been filled"""
        if not self.active_orders:
            return
        
        logger.info("🔍 Checking for filled orders...")
        
        try:
            # Get current open orders
            open_orders = self.api.get_open_orders(self.symbol)
            open_order_ids = [str(order.get('orderId')) for order in open_orders]
            
            # Check which of our orders are no longer open (i.e., filled)
            filled_orders = []
            for order in self.active_orders:
                if str(order['id']) not in open_order_ids:
                    filled_orders.append(order)
            
            # Process filled orders
            for order in filled_orders:
                logger.info(f"🎯 Order FILLED: {order['side']} {order['quantity']:.6f} XRP at ₱{order['price']:.2f}")
                
                if order['side'] == 'BUY':
                    self.total_invested += order['amount']
                    logger.info(f"💰 Bought XRP - Total invested: ₱{self.total_invested:.2f}")
                else:  # SELL
                    profit = order['amount'] - self.grid_amount  # Assuming we bought at lower price
                    self.total_profit += profit
                    logger.info(f"💵 Sold XRP - Profit: ₱{profit:.2f} | Total profit: ₱{self.total_profit:.2f}")
                
                # Remove filled order from active list
                self.active_orders.remove(order)
            
            if filled_orders:
                logger.info(f"✅ Processed {len(filled_orders)} filled orders")
                return True
            
        except Exception as e:
            logger.error(f"Error checking filled orders: {e}")
        
        return False
    
    def show_status(self):
        """Display current bot status"""
        balances = self.get_balances()
        current_price = self.get_current_price()
        
        logger.info("=" * 60)
        logger.info("📊 GRID BOT STATUS")
        logger.info("=" * 60)
        logger.info(f"💱 Symbol: {self.symbol}")
        logger.info(f"💰 Current price: ₱{current_price:.2f}" if current_price else "💰 Price: N/A")
        logger.info(f"🏦 PHP Balance: ₱{balances.get('PHP', 0):.2f}")
        logger.info(f"🪙 XRP Balance: {balances.get('XRP', 0):.6f}")
        logger.info(f"📋 Active orders: {len(self.active_orders)}")
        logger.info(f"💸 Total invested: ₱{self.total_invested:.2f}")
        logger.info(f"💵 Total profit: ₱{self.total_profit:.2f}")
        
        if self.active_orders:
            logger.info("📋 Active Grid Orders:")
            for order in self.active_orders:
                logger.info(f"   {order['side']}: {order['quantity']:.6f} XRP at ₱{order['price']:.2f}")
        
        logger.info("=" * 60)
    
    def start(self):
        """Start the grid trading bot"""
        logger.info("🚀 Starting Grid Trading Bot")
        
        # Initial status check
        current_price = self.get_current_price()
        if not current_price:
            logger.error("❌ Cannot get current price. Stopping bot.")
            return
        
        self.center_price = current_price
        logger.info(f"📍 Starting price: ₱{current_price:.2f}")
        
        # Show initial status
        self.show_status()
        
        # Set up initial grid
        if not self.place_grid_orders(current_price):
            logger.error("❌ Failed to place initial grid orders. Stopping bot.")
            return
        
        self.running = True
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n--- Grid Bot Cycle {iteration} ---")
                
                # Check for filled orders
                if self.check_filled_orders():
                    # If orders were filled, rebalance the grid
                    current_price = self.get_current_price()
                    if current_price:
                        # Only rebalance if price has moved significantly
                        price_change = abs(current_price - self.center_price) / self.center_price
                        if price_change > self.grid_spacing:
                            logger.info(f"📈 Price moved {price_change*100:.1f}%, rebalancing grid...")
                            self.center_price = current_price
                            self.place_grid_orders(current_price)
                
                # Show status every 5 cycles
                if iteration % 5 == 0:
                    self.show_status()
                
                # Wait before next check
                logger.info("⏰ Waiting 2 minutes before next check...")
                time.sleep(120)  # Check every 2 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user (Ctrl+C)")
                self.stop()
            except Exception as e:
                logger.error(f"❌ Error in main bot loop: {e}")
                logger.info("⏰ Waiting 1 minute before retrying...")
                time.sleep(60)
    
    def stop(self):
        """Stop the grid trading bot"""
        self.running = False
        logger.info("🛑 Stopping Grid Trading Bot")
        
        # Cancel all orders
        self.cancel_all_orders()
        
        # Show final status
        self.show_status()
        
        logger.info("✅ Grid bot stopped successfully")

def main():
    """Main function to run the grid bot"""
    print("🔲 Grid Trading Bot for Coins.ph")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('COINS_API_KEY'):
        print("❌ COINS_API_KEY not found in .env file")
        return
    
    if not os.getenv('COINS_SECRET_KEY'):
        print("❌ COINS_SECRET_KEY not found in .env file")
        return
    
    # Create and start bot
    bot = GridTradingBot()
    
    print(f"Symbol: {bot.symbol}")
    print(f"Grid amount: ₱{bot.grid_amount} per level")
    print(f"Grid spacing: {bot.grid_spacing*100}%")
    print(f"Number of grids: {bot.num_grids} each side")
    print(f"Max investment: ₱{bot.max_total_investment}")
    print()
    
    # Warning
    print("⚠️  WARNING: This bot will place real limit orders!")
    print("⚠️  Make sure you understand grid trading before proceeding!")
    print()
    
    response = input("Do you want to start the grid bot? (yes/no): ").lower()
    if response in ['yes', 'y']:
        try:
            bot.start()
        except Exception as e:
            logger.error(f"Grid bot crashed: {e}")
    else:
        print("Grid bot not started")

if __name__ == "__main__":
    main()