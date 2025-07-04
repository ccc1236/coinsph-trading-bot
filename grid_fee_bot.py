import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fee_aware_grid.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('FeeAwareGrid')

class FeeAwareGridBot:
    def __init__(self):
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Fee-optimized configuration
        self.symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')
        self.grid_amount = 300  # Larger trades to dilute fee impact
        
        # Fee-aware grid settings
        self.maker_fee = 0.0025   # 0.25% maker fee
        self.taker_fee = 0.0030   # 0.30% taker fee
        self.round_trip_fee = self.maker_fee * 2  # 0.5% round trip with limit orders
        self.min_profit_margin = 0.01  # 1% minimum profit margin above fees
        
        # Calculated grid spacing (must be > round trip fee + margin)
        self.grid_spacing = self.round_trip_fee + self.min_profit_margin  # 1.5%
        self.num_grids = 2  # Fewer levels = less frequent trading
        
        # Risk management
        self.max_total_investment = 1200  # Max ₱1200 invested
        self.max_position_size = 600      # Max ₱600 per position
        
        # State tracking
        self.center_price = None
        self.active_orders = []
        self.positions = {}
        self.running = False
        self.total_invested = 0
        self.total_fees_paid = 0
        self.gross_profit = 0
        self.net_profit = 0
        
        logger.info(f"🔧 Fee-Aware Grid Bot initialized for {self.symbol}")
        logger.info(f"💰 Grid amount: ₱{self.grid_amount} per level")
        logger.info(f"📊 Maker fee: {self.maker_fee*100}%")
        logger.info(f"📊 Round-trip fee: {self.round_trip_fee*100}%")
        logger.info(f"📏 Grid spacing: {self.grid_spacing*100}% (fee + {self.min_profit_margin*100}% margin)")
        logger.info(f"🔢 Grid levels: {self.num_grids} each side")
    
    def calculate_fees(self, trade_amount, order_type='LIMIT'):
        """Calculate fees for a trade"""
        if order_type == 'LIMIT':
            return trade_amount * self.maker_fee
        else:
            return trade_amount * self.taker_fee
    
    def calculate_min_profitable_price(self, buy_price):
        """Calculate minimum sell price to be profitable after fees"""
        # Need to overcome: buy fee + sell fee + minimum margin
        total_fee_impact = self.round_trip_fee + self.min_profit_margin
        return buy_price * (1 + total_fee_impact)
    
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
    
    def place_fee_aware_grid(self, center_price):
        """Place grid orders optimized for fees"""
        logger.info(f"🔧 Setting up fee-aware grid around ₱{center_price:.2f}")
        
        # Cancel existing orders
        try:
            self.api.cancel_all_orders(self.symbol)
            self.active_orders = []
            time.sleep(2)  # Wait for cancellations
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
        
        orders_placed = 0
        
        # Place BUY orders below current price
        for i in range(1, self.num_grids + 1):
            buy_price = center_price * (1 - self.grid_spacing * i)
            
            # Check if we have budget
            if self.total_invested + self.grid_amount <= self.max_total_investment:
                # Calculate quantity
                quantity = self.grid_amount / buy_price
                
                # Calculate minimum profitable sell price
                min_sell_price = self.calculate_min_profitable_price(buy_price)
                
                try:
                    logger.info(f"📉 Placing BUY: {quantity:.6f} XRP at ₱{buy_price:.2f}")
                    logger.info(f"   Min profitable sell: ₱{min_sell_price:.2f} (+{((min_sell_price/buy_price)-1)*100:.1f}%)")
                    
                    order = self.api.place_order(
                        symbol=self.symbol,
                        side='BUY',
                        order_type='LIMIT',  # Always use limit orders (maker fees)
                        quantity=f'{quantity:.6f}',
                        price=f'{buy_price:.2f}',
                        timeInForce='GTC'
                    )
                    
                    # Track order with fee calculation
                    estimated_fee = self.calculate_fees(self.grid_amount, 'LIMIT')
                    
                    self.active_orders.append({
                        'id': order.get('orderId'),
                        'side': 'BUY',
                        'price': buy_price,
                        'quantity': quantity,
                        'amount': self.grid_amount,
                        'estimated_fee': estimated_fee,
                        'min_sell_price': min_sell_price
                    })
                    
                    orders_placed += 1
                    logger.info(f"✅ BUY order placed: ID {order.get('orderId')}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to place BUY order: {e}")
        
        # Place SELL orders above current price (only if we have XRP)
        balances = self.get_balances()
        xrp_balance = balances.get('XRP', 0)
        
        if xrp_balance > 0.01:
            for i in range(1, self.num_grids + 1):
                sell_price = center_price * (1 + self.grid_spacing * i)
                
                # Use portion of available XRP
                max_sell_quantity = min(xrp_balance / self.num_grids, self.max_position_size / sell_price)
                
                if max_sell_quantity > 0.01:
                    try:
                        logger.info(f"📈 Placing SELL: {max_sell_quantity:.6f} XRP at ₱{sell_price:.2f}")
                        
                        order = self.api.place_order(
                            symbol=self.symbol,
                            side='SELL',
                            order_type='LIMIT',  # Always limit orders
                            quantity=f'{max_sell_quantity:.6f}',
                            price=f'{sell_price:.2f}',
                            timeInForce='GTC'
                        )
                        
                        estimated_fee = self.calculate_fees(max_sell_quantity * sell_price, 'LIMIT')
                        
                        self.active_orders.append({
                            'id': order.get('orderId'),
                            'side': 'SELL',
                            'price': sell_price,
                            'quantity': max_sell_quantity,
                            'amount': max_sell_quantity * sell_price,
                            'estimated_fee': estimated_fee
                        })
                        
                        orders_placed += 1
                        logger.info(f"✅ SELL order placed: ID {order.get('orderId')}")
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to place SELL order: {e}")
        
        logger.info(f"🔧 Fee-aware grid complete: {orders_placed} orders placed")
        return orders_placed > 0
    
    def check_filled_orders(self):
        """Check for filled orders and calculate actual fees"""
        if not self.active_orders:
            return False
        
        logger.info("🔍 Checking for filled orders...")
        
        try:
            # Get current open orders
            open_orders = self.api.get_open_orders(self.symbol)
            open_order_ids = [str(order.get('orderId')) for order in open_orders]
            
            # Find filled orders
            filled_orders = []
            for order in self.active_orders:
                if str(order['id']) not in open_order_ids:
                    filled_orders.append(order)
            
            # Process filled orders
            for order in filled_orders:
                actual_fee = order['estimated_fee']  # Use calculated fee
                self.total_fees_paid += actual_fee
                
                if order['side'] == 'BUY':
                    self.total_invested += order['amount']
                    logger.info(f"💰 BUY FILLED: {order['quantity']:.6f} XRP at ₱{order['price']:.2f}")
                    logger.info(f"   Fee paid: ₱{actual_fee:.2f}")
                    logger.info(f"   Min sell price: ₱{order['min_sell_price']:.2f}")
                    
                else:  # SELL
                    # Calculate gross profit and net profit
                    gross_amount = order['amount']
                    net_amount = gross_amount - actual_fee
                    
                    # Estimate profit (rough calculation)
                    estimated_cost = order['quantity'] * (order['price'] / (1 + self.grid_spacing))
                    gross_profit = gross_amount - estimated_cost
                    net_profit = net_amount - estimated_cost
                    
                    self.gross_profit += gross_profit
                    self.net_profit += net_profit
                    
                    logger.info(f"💵 SELL FILLED: {order['quantity']:.6f} XRP at ₱{order['price']:.2f}")
                    logger.info(f"   Gross amount: ₱{gross_amount:.2f}")
                    logger.info(f"   Fee paid: ₱{actual_fee:.2f}")
                    logger.info(f"   Net amount: ₱{net_amount:.2f}")
                    logger.info(f"   Estimated profit: ₱{net_profit:.2f}")
                
                # Remove from active orders
                self.active_orders.remove(order)
            
            if filled_orders:
                logger.info(f"✅ Processed {len(filled_orders)} filled orders")
                return True
                
        except Exception as e:
            logger.error(f"Error checking filled orders: {e}")
        
        return False
    
    def show_status(self):
        """Display current bot status with fee tracking"""
        balances = self.get_balances()
        current_price = self.get_current_price()
        
        logger.info("=" * 70)
        logger.info("📊 FEE-AWARE GRID BOT STATUS")
        logger.info("=" * 70)
        logger.info(f"💱 Symbol: {self.symbol}")
        logger.info(f"💰 Current price: ₱{current_price:.2f}" if current_price else "💰 Price: N/A")
        logger.info(f"🏦 PHP Balance: ₱{balances.get('PHP', 0):.2f}")
        logger.info(f"🪙 XRP Balance: {balances.get('XRP', 0):.6f}")
        logger.info(f"📋 Active orders: {len(self.active_orders)}")
        logger.info(f"💸 Total invested: ₱{self.total_invested:.2f}")
        logger.info(f"💸 Total fees paid: ₱{self.total_fees_paid:.2f}")
        logger.info(f"💵 Gross profit: ₱{self.gross_profit:.2f}")
        logger.info(f"💵 Net profit: ₱{self.net_profit:.2f}")
        
        if current_price:
            total_value = balances.get('PHP', 0) + (balances.get('XRP', 0) * current_price)
            logger.info(f"💼 Total portfolio value: ₱{total_value:.2f}")
        
        logger.info("=" * 70)
    
    def start(self):
        """Start the fee-aware grid trading bot"""
        logger.info("🚀 Starting Fee-Aware Grid Trading Bot")
        
        current_price = self.get_current_price()
        if not current_price:
            logger.error("❌ Cannot get current price")
            return
        
        self.center_price = current_price
        logger.info(f"📍 Starting price: ₱{current_price:.2f}")
        
        # Show initial status
        self.show_status()
        
        # Set up initial grid
        if not self.place_fee_aware_grid(current_price):
            logger.error("❌ Failed to place initial grid")
            return
        
        self.running = True
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n--- Fee-Aware Grid Cycle {iteration} ---")
                
                # Check for filled orders
                if self.check_filled_orders():
                    current_price = self.get_current_price()
                    if current_price:
                        # Rebalance if price moved significantly
                        price_change = abs(current_price - self.center_price) / self.center_price
                        if price_change > self.grid_spacing * 0.8:  # 80% of grid spacing
                            logger.info(f"📈 Price moved {price_change*100:.1f}%, rebalancing...")
                            self.center_price = current_price
                            self.place_fee_aware_grid(current_price)
                
                # Show status every 3 cycles
                if iteration % 3 == 0:
                    self.show_status()
                
                logger.info("⏰ Waiting 3 minutes...")
                time.sleep(180)  # Check every 3 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user")
                self.stop()
            except Exception as e:
                logger.error(f"❌ Error in bot loop: {e}")
                time.sleep(60)
    
    def stop(self):
        """Stop the bot"""
        self.running = False
        logger.info("🛑 Stopping Fee-Aware Grid Bot")
        
        try:
            self.api.cancel_all_orders(self.symbol)
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
        
        self.show_status()
        logger.info("✅ Fee-aware grid bot stopped")

def main():
    """Main function"""
    print("🔧 Fee-Aware Grid Trading Bot")
    print("=" * 40)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    bot = FeeAwareGridBot()
    
    print(f"Symbol: {bot.symbol}")
    print(f"Grid amount: ₱{bot.grid_amount}")
    print(f"Grid spacing: {bot.grid_spacing*100:.1f}%")
    print(f"Round-trip fees: {bot.round_trip_fee*100}%")
    print(f"Profit margin: {bot.min_profit_margin*100}%")
    print()
    print("⚠️  This bot is optimized for fees but still experimental!")
    print()
    
    response = input("Start fee-aware grid bot? (yes/no): ").lower()
    if response in ['yes', 'y']:
        try:
            bot.start()
        except Exception as e:
            logger.error(f"Bot crashed: {e}")

if __name__ == "__main__":
    main()