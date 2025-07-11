import sys
import os
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI

# Force both stdout and stderr to UTF-8 so emojis and ₱ work in prints and logging
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    # Python < 3.7 doesn't have reconfigure
    pass

# Load environment variables
load_dotenv(override=True)

# Setup logging with UTF-8 encoding for file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('momentum_v3.log', encoding='utf-8'),  # UTF-8 encoding
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MomentumTradingBot_v3')

class MomentumTradingBot:
    def __init__(self, symbol='XRPPHP', take_profit_pct=5.0):
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Trading parameters - now configurable!
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')  # SOL, XRP, etc.
        self.quote_asset = 'PHP'
        
        # Strategy parameters (optimized from backtesting)
        self.buy_threshold = 0.006      # 0.6% momentum trigger
        self.sell_threshold = 0.010     # 1.0% decline trigger
        self.take_profit_pct = take_profit_pct / 100  # Convert to decimal
        self.base_amount = 200          # ₱200 per trade
        self.min_hold_hours = 0.5       # 30 minutes minimum hold
        self.max_trades_per_day = 10    # Safety limit
        self.trend_window = 12          # 12 hours trend analysis
        self.check_interval = 900       # 15 minutes

        # Runtime state
        self.running = False
        self.last_price = None
        self.position = None  # 'long' or None
        self.entry_price = None
        self.entry_time = None
        self.price_history = []
        self.daily_trades = {}

        # Display configuration
        logger.info(f"🚀 Momentum Trading Bot v3.0 initialized")
        logger.info(f"🎯 Asset: {self.symbol} ({self.base_asset}/PHP)")
        logger.info(f"📈 Buy threshold: {self.buy_threshold*100:.1f}%")
        logger.info(f"📉 Sell threshold: {self.sell_threshold*100:.1f}%")
        logger.info(f"🎯 Take profit: {take_profit_pct:.1f}%")
        logger.info(f"💰 Trade amount: ₱{self.base_amount}")
        logger.info(f"⏰ Min hold time: {self.min_hold_hours}h")
        logger.info(f"🔄 Max trades/day: {self.max_trades_per_day}")
        logger.info(f"📊 Check interval: {self.check_interval//60} minutes")

    def get_symbol_info(self):
        """Get trading symbol information"""
        try:
            symbol_info = self.api.get_symbol_info(self.symbol)
            if symbol_info:
                logger.info(f"✅ Symbol {self.symbol} found and active")
                logger.info(f"   Status: {symbol_info.get('status')}")
                logger.info(f"   Base: {symbol_info.get('baseAsset')}")
                logger.info(f"   Quote: {symbol_info.get('quoteAsset')}")
                
                # Check minimum order requirements
                filters = symbol_info.get('filters', [])
                for f in filters:
                    if f.get('filterType') == 'MIN_NOTIONAL':
                        min_notional = float(f.get('minNotional', 0))
                        if min_notional > 0:
                            logger.info(f"   Min order size: ₱{min_notional}")
                            if self.base_amount < min_notional:
                                logger.warning(f"⚠️ Trade amount (₱{self.base_amount}) below minimum (₱{min_notional})")
                
                return symbol_info
            else:
                logger.error(f"❌ Symbol {self.symbol} not found!")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting symbol info: {e}")
            return None

    def get_account_status(self):
        """Check account status and balances"""
        try:
            account = self.api.get_account_info()
            
            if account.get('canTrade'):
                logger.info("✅ Account trading enabled")
                
                # Get current balances
                balances = account.get('balances', [])
                php_balance = 0
                asset_balance = 0
                
                for balance in balances:
                    if balance['asset'] == 'PHP':
                        php_balance = float(balance['free'])
                    elif balance['asset'] == self.base_asset:
                        asset_balance = float(balance['free'])
                
                logger.info(f"💰 PHP Balance: ₱{php_balance:,.2f}")
                logger.info(f"💰 {self.base_asset} Balance: {asset_balance:.6f}")
                
                # Check if we have enough to trade
                if php_balance < self.base_amount * 1.5:
                    logger.warning(f"⚠️ Low PHP balance! Need at least ₱{self.base_amount * 1.5:.0f} for safe trading")
                
                return account
            else:
                logger.error("❌ Account trading disabled!")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error checking account: {e}")
            return None

    def calculate_quantity(self, price, amount_php):
        """Calculate quantity to buy with given PHP amount"""
        return amount_php / price

    def update_price_history(self, price):
        """Update price history for trend analysis"""
        self.price_history.append({'price': price, 'timestamp': datetime.now()})
        cutoff = datetime.now() - timedelta(hours=self.trend_window*2)
        self.price_history = [p for p in self.price_history if p['timestamp'] > cutoff]

    def calculate_trend(self):
        """Calculate trend direction over the trend window"""
        if len(self.price_history) < self.trend_window:
            return 0
        
        recent = [p['price'] for p in self.price_history[-self.trend_window:]]
        mid = len(recent) // 2
        first_half = sum(recent[:mid]) / mid
        second_half = sum(recent[mid:]) / (len(recent) - mid)
        
        return (second_half - first_half) / first_half

    def can_trade_today(self):
        """Check if we can still trade today (daily limit)"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.daily_trades.get(today, 0) < self.max_trades_per_day

    def can_sell_position(self):
        """Check if minimum hold time has passed"""
        if not self.entry_time:
            return True
        return (datetime.now() - self.entry_time) >= timedelta(hours=self.min_hold_hours)

    def update_daily_trades(self):
        """Update daily trade counter"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1

    def momentum_strategy(self):
        """Main trading strategy with configurable take profit"""
        try:
            # Get current price
            current_price = self.api.get_current_price(self.symbol)
            self.update_price_history(current_price)

            if self.last_price is None:
                self.last_price = current_price
                logger.info(f"📊 {self.symbol} current price: ₱{current_price:.4f}")
                return

            # Calculate price change and trend
            price_change = (current_price - self.last_price) / self.last_price
            trend = self.calculate_trend()

            # Get current balances
            php_balance = self.api.get_balance('PHP')
            asset_balance = self.api.get_balance(self.base_asset)
            
            php_free = php_balance['free'] if php_balance else 0
            asset_free = asset_balance['free'] if asset_balance else 0

            logger.info(f"📊 {self.symbol}: ₱{current_price:.4f} ({price_change*100:+.2f}%) | Trend: {trend*100:+.1f}%")
            logger.info(f"💰 Balances: ₱{php_free:.2f} PHP, {asset_free:.6f} {self.base_asset}")

            # BUY CONDITIONS
            if (price_change > self.buy_threshold and           # Strong upward momentum
                trend > -0.02 and                               # Not in strong downtrend
                php_free > self.base_amount * 1.2 and          # Have enough PHP
                self.can_trade_today() and                     # Within daily limit
                self.position is None):                        # No current position
                
                self.place_buy_order(current_price, price_change, trend)

            # SELL CONDITIONS - Momentum Down
            elif (price_change < -self.sell_threshold and      # Strong downward momentum
                  asset_free > 0.001 and                       # Have position
                  self.can_sell_position() and                 # Min hold time met
                  self.can_trade_today()):                     # Within daily limit
                
                self.place_sell_order(current_price, price_change, trend, "Momentum Down")

            # SELL CONDITIONS - Take Profit (CONFIGURABLE!)
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position()):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct > self.take_profit_pct:
                    self.place_sell_order(current_price, price_change, trend, "Take Profit")

            # EMERGENCY EXIT - Strong downtrend
            elif (trend < -0.05 and                            # Very strong downtrend
                  asset_free > 0.001 and                       # Have position
                  self.can_sell_position()):                   # Min hold time met
                
                self.place_sell_order(current_price, price_change, trend, "Emergency Exit")

            self.last_price = current_price

        except Exception as e:
            logger.error(f"❌ Error in strategy execution: {e}")

    def place_buy_order(self, price, change, trend):
        """Place a buy order"""
        try:
            # Calculate order details
            amount_to_spend = min(self.base_amount, self.api.get_balance('PHP')['free'] * 0.9)
            quantity = self.calculate_quantity(price, amount_to_spend)
            
            # Use limit order slightly above market for better fill probability
            buy_price = price * 1.001  # 0.1% above market
            
            logger.info(f"🔄 Attempting BUY: {quantity:.6f} {self.base_asset} at ₱{buy_price:.4f}")
            logger.info(f"   💰 Amount: ₱{amount_to_spend:.2f} | Change: {change*100:+.2f}% | Trend: {trend*100:+.1f}%")
            
            # Place the order
            order = self.api.place_order(
                symbol=self.symbol,
                side='BUY',
                order_type='LIMIT',
                quantity=f"{quantity:.6f}",
                price=f"{buy_price:.4f}",
                timeInForce='GTC'
            )
            
            if order.get('orderId'):
                self.position = 'long'
                self.entry_price = buy_price
                self.entry_time = datetime.now()
                self.update_daily_trades()
                
                logger.info(f"✅ BUY ORDER PLACED!")
                logger.info(f"   Order ID: {order['orderId']}")
                logger.info(f"   Quantity: {quantity:.6f} {self.base_asset}")
                logger.info(f"   Price: ₱{buy_price:.4f}")
                logger.info(f"   Amount: ₱{amount_to_spend:.2f}")
                
                # Send alert if enabled
                self.send_alert(f"🟢 BUY {self.base_asset}: {quantity:.6f} at ₱{buy_price:.4f}")
                
            else:
                logger.error(f"❌ BUY ORDER FAILED: {order}")
                
        except Exception as e:
            logger.error(f"❌ Error placing buy order: {e}")

    def place_sell_order(self, price, change, trend, reason):
        """Place a sell order"""
        try:
            # Get current asset balance
            asset_balance = self.api.get_balance(self.base_asset)
            quantity_to_sell = asset_balance['free'] * 0.99  # Sell 99% to avoid dust
            
            if quantity_to_sell < 0.001:
                logger.warning(f"⚠️ Asset balance too low to sell: {quantity_to_sell:.6f}")
                return
            
            # Use limit order slightly below market for better fill probability
            sell_price = price * 0.999  # 0.1% below market
            gross_amount = quantity_to_sell * sell_price
            
            logger.info(f"🔄 Attempting SELL: {quantity_to_sell:.6f} {self.base_asset} at ₱{sell_price:.4f}")
            logger.info(f"   💰 Amount: ₱{gross_amount:.2f} | Reason: {reason}")
            
            # Calculate P/L if we have entry price
            if self.entry_price:
                profit_loss = (sell_price - self.entry_price) / self.entry_price * 100
                logger.info(f"   📊 P/L: {profit_loss:+.2f}%")
            
            # Place the order
            order = self.api.place_order(
                symbol=self.symbol,
                side='SELL',
                order_type='LIMIT',
                quantity=f"{quantity_to_sell:.6f}",
                price=f"{sell_price:.4f}",
                timeInForce='GTC'
            )
            
            if order.get('orderId'):
                # Clear position
                self.position = None
                self.entry_price = None
                self.entry_time = None
                self.update_daily_trades()
                
                logger.info(f"✅ SELL ORDER PLACED!")
                logger.info(f"   Order ID: {order['orderId']}")
                logger.info(f"   Quantity: {quantity_to_sell:.6f} {self.base_asset}")
                logger.info(f"   Price: ₱{sell_price:.4f}")
                logger.info(f"   Amount: ₱{gross_amount:.2f}")
                logger.info(f"   Reason: {reason}")
                
                # Send alert if enabled
                profit_emoji = "🟢" if reason == "Take Profit" else "🔴"
                self.send_alert(f"{profit_emoji} SELL {self.base_asset}: {quantity_to_sell:.6f} at ₱{sell_price:.4f} ({reason})")
                
            else:
                logger.error(f"❌ SELL ORDER FAILED: {order}")
                
        except Exception as e:
            logger.error(f"❌ Error placing sell order: {e}")

    def send_alert(self, message):
        """Send alert notification (placeholder for future implementation)"""
        # TODO: Implement Slack/Telegram notifications
        logger.info(f"🔔 ALERT: {message}")

    def display_status(self):
        """Display current bot status"""
        status = "🟢 RUNNING" if self.running else "🔴 STOPPED"
        position_status = f"📊 Position: {self.position}" if self.position else "📊 Position: None"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_trades = self.daily_trades.get(today, 0)
        
        logger.info(f"🤖 Bot Status: {status}")
        logger.info(f"🎯 Trading: {self.symbol} with {self.take_profit_pct*100:.1f}% take profit")
        logger.info(f"{position_status}")
        logger.info(f"📈 Daily trades: {daily_trades}/{self.max_trades_per_day}")
        
        if self.entry_price:
            logger.info(f"📊 Entry price: ₱{self.entry_price:.4f}")
            logger.info(f"⏰ Entry time: {self.entry_time.strftime('%H:%M:%S')}")

    def start(self):
        """Start the trading bot"""
        logger.info(f"🚀 Starting Momentum Trading Bot v3.0")
        logger.info(f"🎯 Asset: {self.symbol} | Take Profit: {self.take_profit_pct*100:.1f}%")
        
        # Validate setup
        if not self.get_symbol_info():
            logger.error("❌ Symbol validation failed!")
            return
            
        if not self.get_account_status():
            logger.error("❌ Account validation failed!")
            return
        
        logger.info(f"✅ Setup validated successfully!")
        logger.info(f"🔄 Bot will check every {self.check_interval//60} minutes")
        logger.info(f"📊 Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                self.display_status()
                self.momentum_strategy()
                
                logger.info(f"⏰ Waiting {self.check_interval//60} minutes until next check...")
                logger.info("=" * 60)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.running = False
        logger.info("🛑 Momentum Trading Bot v3.0 stopped")

def get_user_inputs():
    """Get trading parameters from user"""
    print("🚀 MOMENTUM TRADING BOT v3.0")
    print("💡 Choose your trading asset and take profit level")
    print("=" * 60)
    
    # Asset selection
    print("🎯 Select trading asset:")
    print("1. XRPPHP - Recommended (Backtested +1.5% with 5.0% TP)")
    print("2. SOLPHP - High volatility (Backtested -1.3% with 1.8% TP)")
    print("3. Custom symbol")
    
    while True:
        choice = input("Enter choice (1-3): ").strip()
        if choice == '1':
            symbol = 'XRPPHP'
            suggested_tp = 5.0
            break
        elif choice == '2':
            symbol = 'SOLPHP'
            suggested_tp = 1.8
            break
        elif choice == '3':
            symbol = input("Enter symbol (e.g., BTCPHP): ").strip().upper()
            suggested_tp = 2.0
            break
        else:
            print("Please enter 1, 2, or 3")
    
    # Take profit selection
    print(f"\n🎯 Configure take profit for {symbol}:")
    print(f"💡 Suggested: {suggested_tp:.1f}% (based on backtesting)")
    print("📊 Other options:")
    print("   1.0% - Conservative (quick profits)")
    print("   2.0% - Balanced")
    print("   3.0% - Moderate")
    print("   5.0% - Aggressive")
    
    while True:
        try:
            take_profit = input(f"Enter take profit % (suggested: {suggested_tp:.1f}): ").strip()
            if not take_profit:  # Use suggested if empty
                take_profit = suggested_tp
                break
            else:
                take_profit = float(take_profit)
                if 0.1 <= take_profit <= 10.0:
                    break
                else:
                    print("Please enter a value between 0.1% and 10.0%")
        except ValueError:
            print("Please enter a valid number")
    
    # Confirmation
    print(f"\n✅ CONFIGURATION CONFIRMED:")
    print(f"🎯 Asset: {symbol}")
    print(f"📈 Take Profit: {take_profit:.1f}%")
    print(f"💰 Trade Size: ₱200")
    print(f"⏰ Check Interval: 15 minutes")
    
    return symbol, take_profit

def main():
    """Main function"""
    # Check API credentials
    if not os.getenv('COINS_API_KEY') or not os.getenv('COINS_SECRET_KEY'):
        print("❌ API credentials not found!")
        print("Please set COINS_API_KEY and COINS_SECRET_KEY in your .env file")
        return
    
    # Get user configuration
    symbol, take_profit = get_user_inputs()
    
    # Confirm start
    print(f"\n🚀 Ready to start live trading!")
    confirm = input("Start the bot? (y/n): ").lower().strip()
    
    if confirm.startswith('y'):
        # Initialize and start bot
        bot = MomentumTradingBot(symbol=symbol, take_profit_pct=take_profit)
        bot.start()
    else:
        print("👋 Bot startup cancelled")

if __name__ == '__main__':
    main()