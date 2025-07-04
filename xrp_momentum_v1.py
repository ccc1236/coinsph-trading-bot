import os
import time
import logging
from dotenv import load_dotenv
from coins_api import CoinsAPI

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('momentum_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MomentumBot')

class OptimizedMomentumBot:
    def __init__(self):
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # OPTIMIZED Bot configuration (matching backtest results)
        self.symbol = os.getenv('TRADING_SYMBOL', 'XRPPHP')  # XRP like backtest
        self.base_amount = 100  # ₱100 per trade (matching backtest)
        self.price_threshold = 0.01  # 1% threshold (matching backtest)
        self.check_interval = 900  # 15 minutes (matching backtest)
        self.running = False
        
        # State tracking
        self.last_price = None
        self.position = None  # 'long' or None
        self.entry_price = None
        
        logger.info(f"🚀 Optimized Momentum Bot initialized for {self.symbol}")
        logger.info(f"💰 Trade amount: ₱{self.base_amount}")
        logger.info(f"📊 Price threshold: {self.price_threshold*100}%")
        logger.info(f"⏰ Check interval: {self.check_interval//60} minutes")
    
    def get_symbol_info(self):
        """Get trading rules for the symbol"""
        try:
            symbol_info = self.api.get_symbol_info(self.symbol)
            if symbol_info:
                logger.info(f"Symbol {self.symbol} - Status: {symbol_info.get('status')}")
                
                # Extract important filters
                filters = symbol_info.get('filters', [])
                min_qty = None
                min_notional = None
                
                for f in filters:
                    if f.get('filterType') == 'LOT_SIZE':
                        min_qty = float(f.get('minQty', 0))
                    elif f.get('filterType') == 'NOTIONAL':
                        min_notional = float(f.get('minNotional', 0))
                
                logger.info(f"Min quantity: {min_qty}, Min notional: {min_notional}")
                return symbol_info
            else:
                logger.error(f"Symbol {self.symbol} not found")
                return None
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_account_status(self):
        """Check account status and balances"""
        try:
            account = self.api.get_account_info()
            logger.info(f"Account can trade: {account.get('canTrade')}")
            
            balances = self.api.get_balance()
            
            # Show PHP and XRP balances
            for balance in balances:
                if balance['asset'] in ['PHP', 'XRP'] and balance['total'] > 0:
                    logger.info(f"{balance['asset']} balance: {balance['total']:.6f}")
            
            return account
        except Exception as e:
            logger.error(f"Error getting account status: {e}")
            return None
    
    def calculate_quantity(self, price, amount_php):
        """Calculate XRP quantity based on PHP amount"""
        return amount_php / price
    
    def optimized_momentum_strategy(self):
        """
        Optimized momentum strategy (matching backtest):
        - Buy ₱100 when price increases >1%
        - Sell 90% XRP when price decreases >1%
        """
        try:
            current_price = self.api.get_current_price(self.symbol)
            logger.info(f"Current {self.symbol} price: ₱{current_price:.2f}")
            
            if self.last_price is None:
                self.last_price = current_price
                logger.info("First price recorded, waiting for next iteration")
                return
            
            # Calculate price change percentage
            price_change = (current_price - self.last_price) / self.last_price
            logger.info(f"Price change: {price_change*100:.2f}%")
            
            # Check current balances
            xrp_balance = self.api.get_balance('XRP')
            php_balance = self.api.get_balance('PHP')
            
            xrp_amount = xrp_balance['free'] if xrp_balance else 0
            php_amount = php_balance['free'] if php_balance else 0
            
            logger.info(f"Available: {xrp_amount:.6f} XRP, ₱{php_amount:.2f} PHP")
            
            # Trading logic (EXACTLY matching backtest)
            if price_change > self.price_threshold and php_amount > 120:  # Need ₱120 for fees
                # Price went up >1%, buy ₱100 worth of XRP
                self.place_buy_order(current_price, php_amount)
                
            elif price_change < -self.price_threshold and xrp_amount > 0.001:
                # Price went down >1%, sell 90% of XRP
                self.place_sell_order(current_price, xrp_amount)
            
            else:
                logger.info("No trading conditions met, holding position")
            
            self.last_price = current_price
            
        except Exception as e:
            logger.error(f"Error in strategy execution: {e}")
    
    def place_buy_order(self, price, available_php):
        """Place a buy order (EXACTLY matching backtest)"""
        try:
            # Use exactly ₱100 per trade (matching backtest)
            amount_to_spend = min(available_php * 0.9, self.base_amount)
            
            if amount_to_spend < 25:  # Minimum trade size
                logger.warning(f"Insufficient PHP balance for trade: ₱{amount_to_spend}")
                return
            
            quantity = self.calculate_quantity(price, amount_to_spend)
            
            # Place market order
            order = self.api.place_order(
                symbol=self.symbol,
                side='BUY',
                order_type='MARKET',
                quoteOrderQty=str(amount_to_spend)  # Amount in PHP
            )
            
            logger.info(f"✅ BUY order placed: ₱{amount_to_spend:.2f} worth of XRP")
            logger.info(f"📊 Quantity: {quantity:.6f} XRP at ₱{price:.2f}")
            logger.info(f"🆔 Order ID: {order.get('orderId')}")
            
            self.position = 'long'
            self.entry_price = price
            
        except Exception as e:
            logger.error(f"❌ Failed to place buy order: {e}")
    
    def place_sell_order(self, price, xrp_quantity):
        """Place a sell order (EXACTLY matching backtest)"""
        try:
            # Sell 90% of available XRP (matching backtest)
            quantity_to_sell = xrp_quantity * 0.9
            
            if quantity_to_sell < 0.001:
                logger.warning(f"Insufficient XRP balance for trade: {quantity_to_sell}")
                return
            
            order = self.api.place_order(
                symbol=self.symbol,
                side='SELL',
                order_type='MARKET',
                quantity=str(quantity_to_sell)
            )
            
            estimated_php = quantity_to_sell * price
            logger.info(f"✅ SELL order placed: {quantity_to_sell:.6f} XRP")
            logger.info(f"📊 Estimated value: ₱{estimated_php:.2f} at ₱{price:.2f}")
            logger.info(f"🆔 Order ID: {order.get('orderId')}")
            
            # Calculate profit/loss if we have entry price
            if self.entry_price:
                profit_loss = (price - self.entry_price) / self.entry_price * 100
                logger.info(f"📈 P/L vs entry: {profit_loss:+.1f}%")
            
            self.position = None
            self.entry_price = None
            
        except Exception as e:
            logger.error(f"❌ Failed to place sell order: {e}")
    
    def start(self):
        """Start the optimized momentum trading bot"""
        logger.info("🚀 Starting Optimized Momentum Trading Bot")
        logger.info("⚡ Using parameters that matched +1.15% backtest results")
        
        # Initial checks
        if not self.get_symbol_info():
            logger.error("Failed to get symbol info, stopping bot")
            return
        
        if not self.get_account_status():
            logger.error("Failed to get account status, stopping bot")
            return
        
        self.running = True
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n--- Momentum Check {iteration} ---")
                
                # Execute optimized strategy
                self.optimized_momentum_strategy()
                
                # Wait 15 minutes (matching backtest)
                logger.info(f"⏰ Waiting {self.check_interval//60} minutes before next check...")
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Bot stopped by user (Ctrl+C)")
                self.stop()
            except Exception as e:
                logger.error(f"❌ Error in main bot loop: {e}")
                logger.info("⏰ Waiting 1 minute before retrying...")
                time.sleep(60)
    
    def stop(self):
        """Stop the trading bot"""
        self.running = False
        logger.info("🛑 Optimized Momentum Trading Bot stopped")
        
        # Show final status
        try:
            balances = self.api.get_balance()
            logger.info("📊 Final balances:")
            for balance in balances:
                if balance['total'] > 0:
                    logger.info(f"  {balance['asset']}: {balance['total']:.6f}")
            
            # Show current price for reference
            current_price = self.api.get_current_price(self.symbol)
            logger.info(f"💰 Current {self.symbol} price: ₱{current_price:.2f}")
            
        except Exception as e:
            logger.error(f"Error getting final status: {e}")

def main():
    """Main function to run the optimized momentum bot"""
    print("🚀 Optimized Momentum Trading Bot for Coins.ph")
    print("⚡ Matches backtest parameters: 1% threshold, 15-min, ₱100 trades")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv('COINS_API_KEY'):
        print("❌ COINS_API_KEY not found in .env file")
        return
    
    if not os.getenv('COINS_SECRET_KEY'):
        print("❌ COINS_SECRET_KEY not found in .env file")
        return
    
    # Create and start bot
    bot = OptimizedMomentumBot()
    
    print(f"🎯 Symbol: {bot.symbol}")
    print(f"💰 Trading amount: ₱{bot.base_amount}")
    print(f"📊 Price threshold: {bot.price_threshold*100}%")
    print(f"⏰ Check interval: {bot.check_interval//60} minutes")
    print()
    print("📈 Expected based on backtest:")
    print("  • +1.15% return in declining market")
    print("  • Beat buy-and-hold by +5.58%")
    print("  • 6 trades in 41 days")
    print("  • Low fees (0.09% of capital)")
    print()
    
    # Warning
    print("⚠️  WARNING: This bot will place real trades with real money!")
    print("⚠️  Start with small amounts and monitor closely!")
    print("⚠️  Past backtest performance doesn't guarantee future results!")
    print()
    
    response = input("Start optimized momentum bot? (yes/no): ").lower()
    if response in ['yes', 'y']:
        try:
            bot.start()
        except Exception as e:
            logger.error(f"Bot crashed: {e}")
    else:
        print("Bot not started")

if __name__ == "__main__":
    main()