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

class TitanTradingBot:
    """
    🤖 TITAN - Advanced Momentum Trading Bot v3.3
    
    Pure momentum-based trading with configurable position sizing, take profit levels, and trade amounts.
    Optimized for high-frequency crypto trading on Coins.ph.
    """
    
    def __init__(self, symbol='XRPPHP', take_profit_pct=5.0, base_amount=200, position_sizing='fixed'):
        # Bot identity
        self.name = "TITAN"
        self.version = "3.3.0"
        self.description = "Advanced Momentum Trading Bot"
        
        # Trading parameters - now configurable!
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')  # SOL, XRP, etc.
        self.quote_asset = 'PHP'
        
        # Setup asset-specific logging BEFORE any logging calls
        self.setup_logging()
        
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Strategy parameters (optimized from backtesting)
        self.buy_threshold = 0.006      # 0.6% momentum trigger
        self.sell_threshold = 0.010     # 1.0% decline trigger
        self.take_profit_pct = take_profit_pct / 100  # Convert to decimal
        self.base_amount = base_amount  # ₱ per trade - NOW CONFIGURABLE!
        self.position_sizing = position_sizing  # Position sizing strategy
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
        self.logger.info(f"🤖 {self.name} - {self.description} v{self.version} initialized")
        self.logger.info(f"🎯 Asset: {self.symbol} ({self.base_asset}/PHP)")
        self.logger.info(f"📈 Buy threshold: {self.buy_threshold*100:.1f}%")
        self.logger.info(f"📉 Sell threshold: {self.sell_threshold*100:.1f}%")
        self.logger.info(f"🎯 Take profit: {take_profit_pct:.1f}%")
        self.logger.info(f"💰 Base amount: ₱{self.base_amount}")
        self.logger.info(f"📊 Position sizing: {self.position_sizing}")
        self.logger.info(f"⏰ Min hold time: {self.min_hold_hours}h")
        self.logger.info(f"🔄 Max trades/day: {self.max_trades_per_day}")
        self.logger.info(f"📊 Check interval: {self.check_interval//60} minutes")

    def setup_logging(self):
        """Setup asset-specific logging with dynamic file names"""
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Create asset-specific log filename
        log_filename = f"logs/titan_{self.base_asset.lower()}.log"
        
        # Create custom logger for this TITAN instance
        self.logger = logging.getLogger(f'TitanTradingBot_{self.base_asset}')
        self.logger.setLevel(logging.INFO)
        
        # CRITICAL: Prevent propagation to root logger (fixes duplicate output)
        self.logger.propagate = False
        
        # Clear any existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File handler with asset-specific filename
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler (optional - shows in terminal)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # Log the setup
        self.logger.info(f"📝 Logging initialized for {self.symbol}")
        self.logger.info(f"📁 Log file: {log_filename}")

    def get_symbol_info(self):
        """Get trading symbol information"""
        try:
            symbol_info = self.api.get_symbol_info(self.symbol)
            if symbol_info:
                self.logger.info(f"✅ Symbol {self.symbol} found and active")
                self.logger.info(f"   Status: {symbol_info.get('status')}")
                self.logger.info(f"   Base: {symbol_info.get('baseAsset')}")
                self.logger.info(f"   Quote: {symbol_info.get('quoteAsset')}")
                
                # Check minimum order requirements
                filters = symbol_info.get('filters', [])
                for f in filters:
                    if f.get('filterType') == 'MIN_NOTIONAL':
                        min_notional = float(f.get('minNotional', 0))
                        if min_notional > 0:
                            self.logger.info(f"   Min order size: ₱{min_notional}")
                            if self.base_amount < min_notional:
                                self.logger.warning(f"⚠️ Trade amount (₱{self.base_amount}) below minimum (₱{min_notional})")
                                self.logger.warning(f"   Consider increasing trade amount to at least ₱{min_notional + 1}")
                
                return symbol_info
            else:
                self.logger.error(f"❌ Symbol {self.symbol} not found!")
                return None
        except Exception as e:
            self.logger.error(f"❌ Error getting symbol info: {e}")
            return None

    def get_account_status(self):
        """Check account status and balances"""
        try:
            account = self.api.get_account_info()
            
            if account.get('canTrade'):
                self.logger.info("✅ Account trading enabled")
                
                # Get current balances
                balances = account.get('balances', [])
                php_balance = 0
                asset_balance = 0
                
                for balance in balances:
                    if balance['asset'] == 'PHP':
                        php_balance = float(balance['free'])
                    elif balance['asset'] == self.base_asset:
                        asset_balance = float(balance['free'])
                
                self.logger.info(f"💰 PHP Balance: ₱{php_balance:,.2f}")
                self.logger.info(f"💰 {self.base_asset} Balance: {asset_balance:.6f}")
                
                # Check if we have enough to trade
                required_balance = self.base_amount * 2  # 2x for safety margin
                if php_balance < required_balance:
                    self.logger.warning(f"⚠️ Low PHP balance!")
                    self.logger.warning(f"   Current: ₱{php_balance:.2f}")
                    self.logger.warning(f"   Recommended: ₱{required_balance:.2f} (2x trade amount)")
                    self.logger.warning(f"   You can make ~{int(php_balance / self.base_amount)} trades")
                else:
                    max_trades = int(php_balance / self.base_amount)
                    self.logger.info(f"✅ Sufficient balance for ~{max_trades} trades")
                
                return account
            else:
                self.logger.error("❌ Account trading disabled!")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error checking account: {e}")
            return None

    def calculate_position_size(self, current_price, momentum, trend):
        """
        Calculate dynamic position size based on selected strategy
        
        Args:
            current_price: Current asset price
            momentum: Current momentum score
            trend: Current trend score
            
        Returns:
            Position size in PHP
        """
        
        if self.position_sizing == 'fixed':
            # Original fixed amount
            return self.base_amount
            
        elif self.position_sizing == 'percentage':
            # Percentage of available balance (conservative)
            php_balance = self.api.get_balance('PHP')
            available_balance = php_balance['free'] if php_balance else 0
            position_pct = 0.10  # 10% of available balance
            calculated_size = available_balance * position_pct
            
            # Ensure within reasonable bounds
            min_size = self.base_amount * 0.5  # At least 50% of base
            max_size = self.base_amount * 2.0  # At most 200% of base
            
            return max(min_size, min(calculated_size, max_size))
            
        elif self.position_sizing == 'momentum':
            # Adjust size based on momentum strength
            base_size = self.base_amount
            
            # Strong momentum = larger position
            if abs(momentum) > 0.012:  # 1.2% momentum
                multiplier = 1.4
            elif abs(momentum) > 0.008:  # 0.8% momentum  
                multiplier = 1.2
            elif abs(momentum) > 0.006:  # 0.6% momentum (threshold)
                multiplier = 1.0
            else:
                multiplier = 0.8  # Weak momentum
            
            # Apply trend filter
            if trend < -0.03:  # Strong downtrend
                multiplier *= 0.7  # Reduce size
            elif trend > 0.02:  # Strong uptrend
                multiplier *= 1.1  # Slightly increase
                
            calculated_size = base_size * multiplier
            
            # Bounds checking
            min_size = self.base_amount * 0.5
            max_size = self.base_amount * 1.5
            
            return max(min_size, min(calculated_size, max_size))
            
        elif self.position_sizing == 'adaptive':
            # Advanced: Combine balance, momentum, and recent performance
            php_balance = self.api.get_balance('PHP')
            available_balance = php_balance['free'] if php_balance else 0
            
            # Base sizing on available balance
            balance_multiplier = min(2.0, available_balance / (self.base_amount * 5))
            
            # Momentum adjustment
            momentum_strength = abs(momentum)
            if momentum_strength > 0.015:
                momentum_multiplier = 1.3
            elif momentum_strength > 0.010:
                momentum_multiplier = 1.1
            elif momentum_strength > 0.006:
                momentum_multiplier = 1.0
            else:
                momentum_multiplier = 0.8
            
            # Trend adjustment
            if trend > 0.02:
                trend_multiplier = 1.1
            elif trend < -0.03:
                trend_multiplier = 0.8
            else:
                trend_multiplier = 1.0
            
            # Daily trades adjustment (reduce size if many trades today)
            today = datetime.now().strftime('%Y-%m-%d')
            trades_today = self.daily_trades.get(today, 0)
            if trades_today >= 7:
                trade_multiplier = 0.7
            elif trades_today >= 5:
                trade_multiplier = 0.9
            else:
                trade_multiplier = 1.0
            
            # Calculate final size
            total_multiplier = balance_multiplier * momentum_multiplier * trend_multiplier * trade_multiplier
            calculated_size = self.base_amount * total_multiplier
            
            # Apply bounds
            min_size = self.base_amount * 0.3  # More flexible bounds
            max_size = self.base_amount * 2.0
            
            final_size = max(min_size, min(calculated_size, max_size))
            
            self.logger.info(f"📊 Adaptive sizing: Balance×{balance_multiplier:.1f}, "
                           f"Momentum×{momentum_multiplier:.1f}, Trend×{trend_multiplier:.1f}, "
                           f"Trades×{trade_multiplier:.1f} = ₱{final_size:.0f}")
            
            return final_size
        
        else:
            # Fallback to fixed
            return self.base_amount

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
                self.logger.info(f"📊 {self.symbol} current price: ₱{current_price:.4f}")
                return

            # Calculate price change and trend
            price_change = (current_price - self.last_price) / self.last_price
            trend = self.calculate_trend()

            # Get current balances
            php_balance = self.api.get_balance('PHP')
            asset_balance = self.api.get_balance(self.base_asset)
            
            php_free = php_balance['free'] if php_balance else 0
            asset_free = asset_balance['free'] if asset_balance else 0

            self.logger.info(f"📊 {self.symbol}: ₱{current_price:.4f} ({price_change*100:+.2f}%) | Trend: {trend*100:+.1f}%")
            self.logger.info(f"💰 Balances: ₱{php_free:.2f} PHP, {asset_free:.6f} {self.base_asset}")

            # BUY CONDITIONS
            if (price_change > self.buy_threshold and           # Strong upward momentum
                trend > -0.02 and                               # Not in strong downtrend
                php_free > self.base_amount * 0.6 and          # Have enough PHP (reduced requirement)
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
            self.logger.error(f"❌ Error in strategy execution: {e}")

    def place_buy_order(self, price, change, trend):
        """Place a buy order with dynamic position sizing"""
        try:
            # Calculate dynamic position size
            position_size = self.calculate_position_size(price, change, trend)
            
            # Ensure we have enough balance
            php_balance = self.api.get_balance('PHP')
            available_balance = php_balance['free'] if php_balance else 0
            
            # Use the smaller of calculated size or 90% of available balance
            amount_to_spend = min(position_size, available_balance * 0.9)
            
            if amount_to_spend < 50:  # Minimum viable trade
                self.logger.warning(f"⚠️ Position size too small: ₱{amount_to_spend:.2f}")
                return
            
            quantity = self.calculate_quantity(price, amount_to_spend)
            
            # Use limit order slightly above market for better fill probability
            buy_price = price * 1.001  # 0.1% above market
            
            self.logger.info(f"🔄 {self.name} attempting BUY: {quantity:.6f} {self.base_asset} at ₱{buy_price:.4f}")
            self.logger.info(f"   💰 Position size: ₱{amount_to_spend:.2f} ({self.position_sizing} sizing)")
            self.logger.info(f"   📊 Change: {change*100:+.2f}% | Trend: {trend*100:+.1f}%")
            
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
                
                self.logger.info(f"✅ {self.name} BUY ORDER PLACED!")
                self.logger.info(f"   Order ID: {order['orderId']}")
                self.logger.info(f"   Quantity: {quantity:.6f} {self.base_asset}")
                self.logger.info(f"   Price: ₱{buy_price:.4f}")
                self.logger.info(f"   Amount: ₱{amount_to_spend:.2f}")
                
                # Send alert if enabled
                self.send_alert(f"🟢 {self.name} BUY {self.base_asset}: {quantity:.6f} at ₱{buy_price:.4f}")
                
            else:
                self.logger.error(f"❌ {self.name} BUY ORDER FAILED: {order}")
                
        except Exception as e:
            self.logger.error(f"❌ Error placing buy order: {e}")

    def place_sell_order(self, price, change, trend, reason):
        """Place a sell order"""
        try:
            # Get current asset balance
            asset_balance = self.api.get_balance(self.base_asset)
            quantity_to_sell = asset_balance['free'] * 0.99  # Sell 99% to avoid dust
            
            if quantity_to_sell < 0.001:
                self.logger.warning(f"⚠️ Asset balance too low to sell: {quantity_to_sell:.6f}")
                return
            
            # Use limit order slightly below market for better fill probability
            sell_price = price * 0.999  # 0.1% below market
            gross_amount = quantity_to_sell * sell_price
            
            self.logger.info(f"🔄 {self.name} attempting SELL: {quantity_to_sell:.6f} {self.base_asset} at ₱{sell_price:.4f}")
            self.logger.info(f"   💰 Amount: ₱{gross_amount:.2f} | Reason: {reason}")
            
            # Calculate P/L if we have entry price
            if self.entry_price:
                profit_loss = (sell_price - self.entry_price) / self.entry_price * 100
                self.logger.info(f"   📊 P/L: {profit_loss:+.2f}%")
            
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
                
                self.logger.info(f"✅ {self.name} SELL ORDER PLACED!")
                self.logger.info(f"   Order ID: {order['orderId']}")
                self.logger.info(f"   Quantity: {quantity_to_sell:.6f} {self.base_asset}")
                self.logger.info(f"   Price: ₱{sell_price:.4f}")
                self.logger.info(f"   Amount: ₱{gross_amount:.2f}")
                self.logger.info(f"   Reason: {reason}")
                
                # Send alert if enabled
                profit_emoji = "🟢" if reason == "Take Profit" else "🔴"
                self.send_alert(f"{profit_emoji} {self.name} SELL {self.base_asset}: {quantity_to_sell:.6f} at ₱{sell_price:.4f} ({reason})")
                
            else:
                self.logger.error(f"❌ {self.name} SELL ORDER FAILED: {order}")
                
        except Exception as e:
            self.logger.error(f"❌ Error placing sell order: {e}")

    def send_alert(self, message):
        """Send alert notification (placeholder for future implementation)"""
        # TODO: Implement Slack/Telegram notifications
        self.logger.info(f"🔔 ALERT: {message}")

    def display_status(self):
        """Display current bot status"""
        status = "🟢 RUNNING" if self.running else "🔴 STOPPED"
        position_status = f"📊 Position: {self.position}" if self.position else "📊 Position: None"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_trades = self.daily_trades.get(today, 0)
        
        self.logger.info(f"🤖 {self.name} Status: {status}")
        self.logger.info(f"🎯 Trading: {self.symbol} with {self.take_profit_pct*100:.1f}% TP, {self.position_sizing} sizing")
        self.logger.info(f"{position_status}")
        self.logger.info(f"📈 Daily trades: {daily_trades}/{self.max_trades_per_day}")
        
        if self.entry_price:
            self.logger.info(f"📊 Entry price: ₱{self.entry_price:.4f}")
            self.logger.info(f"⏰ Entry time: {self.entry_time.strftime('%H:%M:%S')}")

    def start(self):
        """Start the trading bot"""
        self.logger.info(f"🚀 Starting {self.name} - {self.description} v{self.version}")
        self.logger.info(f"🎯 Asset: {self.symbol} | Take Profit: {self.take_profit_pct*100:.1f}% | Position Sizing: {self.position_sizing}")
        
        # Validate setup
        if not self.get_symbol_info():
            self.logger.error("❌ Symbol validation failed!")
            return
            
        if not self.get_account_status():
            self.logger.error("❌ Account validation failed!")
            return
        
        self.logger.info(f"✅ Setup validated successfully!")
        self.logger.info(f"🔄 {self.name} will check every {self.check_interval//60} minutes")
        self.logger.info(f"📊 Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                self.display_status()
                self.momentum_strategy()
                
                self.logger.info(f"⏰ Waiting {self.check_interval//60} minutes until next check...")
                self.logger.info("=" * 60)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f"🛑 {self.name} stopped by user")
            self.stop()
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.running = False
        self.logger.info(f"🛑 {self.name} - {self.description} v{self.version} stopped")

def get_user_inputs():
    """Get trading parameters from user"""
    print("🤖 TITAN - Advanced Momentum Trading Bot v3.3")
    print("💡 Choose your trading asset, position sizing, and take profit level")
    print("=" * 75)
    
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
    
    # Position sizing selection
    print(f"\n📊 Select position sizing strategy:")
    print(f"1. Fixed - Same amount every trade (you choose amount)")
    print(f"2. Percentage - 10% of available balance")
    print(f"3. Momentum - Larger positions on stronger signals")
    print(f"4. Adaptive - Smart sizing based on multiple factors")
    print(f"💡 Recommended: Adaptive (balances risk and opportunity)")
    
    position_sizing_map = {
        '1': 'fixed',
        '2': 'percentage', 
        '3': 'momentum',
        '4': 'adaptive'
    }
    
    while True:
        sizing_choice = input("Enter choice (1-4): ").strip()
        if sizing_choice in position_sizing_map:
            position_sizing = position_sizing_map[sizing_choice]
            break
        else:
            print("Please enter 1, 2, 3, or 4")
    
    # Base amount configuration - different for fixed vs others
    if position_sizing == 'fixed':
        print(f"\n💰 Set fixed trade amount:")
        print(f"💡 Recommended: ₱200 (balanced risk/reward)")
        print(f"📊 This exact amount will be used for every trade")
        print(f"   ₱100 - Conservative (lower risk)")
        print(f"   ₱200 - Balanced")
        print(f"   ₱300 - Moderate")
        print(f"   ₱500 - Aggressive (higher risk)")
        
        while True:
            try:
                amount_input = input("Enter fixed trade amount in PHP (suggested: 200): ").strip()
                if not amount_input:  # Use suggested if empty
                    base_amount = 200
                    break
                else:
                    base_amount = float(amount_input)
                    if 50 <= base_amount <= 2000:
                        break
                    else:
                        print("Please enter an amount between ₱50 and ₱2000")
            except ValueError:
                print("Please enter a valid number")
    else:
        # For dynamic strategies, base amount is just a reference
        print(f"\n💰 Set base reference amount (for dynamic sizing calculations):")
        print(f"💡 Recommended: ₱200")
        print(f"📊 Actual trade sizes will vary based on your {position_sizing} strategy")
        
        while True:
            try:
                amount_input = input("Enter base amount in PHP (suggested: 200): ").strip()
                if not amount_input:  # Use suggested if empty
                    base_amount = 200
                    break
                else:
                    base_amount = float(amount_input)
                    if 50 <= base_amount <= 2000:
                        break
                    else:
                        print("Please enter an amount between ₱50 and ₱2000")
            except ValueError:
                print("Please enter a valid number")
    
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
    
    # Position sizing explanations
    if position_sizing == 'fixed':
        position_description = f"₱{base_amount} every trade (fixed amount)"
    else:
        position_descriptions = {
            'percentage': f"10% of available balance (~₱{base_amount*2}-{base_amount*5})",
            'momentum': f"₱{base_amount*0.5:.0f}-₱{base_amount*1.5:.0f} based on signal strength",
            'adaptive': f"₱{base_amount*0.3:.0f}-₱{base_amount*2:.0f} smart adjustments"
        }
        position_description = position_descriptions[position_sizing]
    
    # Risk calculation for display
    if position_sizing == 'fixed':
        max_daily_risk = base_amount * 10  # Fixed amount × 10 trades
        avg_position = base_amount
    elif position_sizing == 'percentage':
        max_daily_risk = base_amount * 15  # Estimate
        avg_position = base_amount * 2
    else:
        max_daily_risk = base_amount * 12  # Estimate
        avg_position = base_amount * 1.2
    
    # Confirmation
    print(f"\n✅ CONFIGURATION CONFIRMED:")
    print(f"🎯 Asset: {symbol}")
    print(f"📊 Position sizing: {position_sizing.title()} ({position_description})")
    if position_sizing != 'fixed':
        print(f"💰 Base reference: ₱{base_amount}")
    print(f"📈 Take profit: {take_profit:.1f}%")
    print(f"⏰ Check interval: 15 minutes")
    print(f"📁 Log file: logs/titan_{symbol.replace('PHP', '').lower()}.log")
    print(f"\n💡 POSITION SIZING DETAILS:")
    
    if position_sizing == 'fixed':
        print(f"   📊 Every trade: ₱{base_amount} (exact amount)")
        print(f"   📈 Consistent and predictable")
        print(f"   🎯 Simple risk management")
        print(f"   💰 Total daily exposure: Up to ₱{base_amount * 10} (10 trades max)")
    elif position_sizing == 'percentage':
        print(f"   📊 Trade size: 10% of available balance")
        print(f"   📈 Grows with account")
        print(f"   🎯 Conservative scaling")
    elif position_sizing == 'momentum':
        print(f"   📊 Strong momentum: ₱{base_amount*1.4:.0f}")
        print(f"   📊 Normal momentum: ₱{base_amount}")
        print(f"   📊 Weak momentum: ₱{base_amount*0.8:.0f}")
        print(f"   🎯 Signal-based sizing")
    elif position_sizing == 'adaptive':
        print(f"   📊 Considers: Balance, momentum, trend, daily trades")
        print(f"   📈 Range: ₱{base_amount*0.3:.0f} - ₱{base_amount*2:.0f}")
        print(f"   🎯 Most sophisticated approach")
    
    print(f"\n💡 RISK ANALYSIS:")
    print(f"📊 Est. max daily risk: ₱{max_daily_risk:.0f}")
    print(f"💰 Recommended balance: ₱{max_daily_risk * 2:.0f}+")
    print(f"📈 Average position: ~₱{avg_position:.0f}")
    
    return symbol, take_profit, base_amount, position_sizing
    
    return symbol, take_profit, base_amount

def main():
    """Main function"""
    # Check API credentials
    if not os.getenv('COINS_API_KEY') or not os.getenv('COINS_SECRET_KEY'):
        print("❌ API credentials not found!")
        print("Please set COINS_API_KEY and COINS_SECRET_KEY in your .env file")
        return
    
    # Get user configuration
    symbol, take_profit, base_amount, position_sizing = get_user_inputs()
    
    # Confirm start
    print(f"\n🚀 Ready to start live trading with TITAN!")
    print(f"⚠️ Risk: Dynamic position sizing with {position_sizing} strategy")
    confirm = input("Start the bot? (y/n): ").lower().strip()
    
    if confirm.startswith('y'):
        # Initialize and start bot
        bot = TitanTradingBot(symbol=symbol, take_profit_pct=take_profit, base_amount=base_amount, position_sizing=position_sizing)
        bot.start()
    else:
        print("👋 TITAN startup cancelled")

if __name__ == '__main__':
    main()