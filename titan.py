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
    🤖 TITAN - Advanced Momentum Trading Bot v4.0
    
    NEW in v4.0:
    - ✅ Configurable buy/sell thresholds at startup (no code changes needed)
    - ✅ Enhanced optimization discoveries integrated (1.2% buy threshold)
    - ✅ Asset-specific parameter suggestions based on backtesting
    - ✅ Advanced parameter validation and recommendations
    - ✅ Real-time parameter adjustment guidance
    - ✅ Improved user interface with optimization insights
    - ✅ Smart defaults based on asset volatility analysis
    """
    
    def __init__(self, symbol='XRPPHP', take_profit_pct=5.0, base_amount=200, 
                 position_sizing='adaptive', buy_threshold=1.2, sell_threshold=2.0):
        # Bot identity
        self.name = "TITAN"
        self.version = "4.0.0"
        self.description = "Advanced Momentum Trading Bot with Configurable Thresholds"
        
        # Trading parameters - now fully configurable!
        self.symbol = symbol
        self.base_asset = symbol.replace('PHP', '')
        self.quote_asset = 'PHP'
        
        # Setup asset-specific logging BEFORE any logging calls
        self.setup_logging()
        
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Strategy parameters (now configurable at startup!)
        self.buy_threshold = buy_threshold / 100        # Convert to decimal
        self.sell_threshold = sell_threshold / 100      # Convert to decimal
        self.take_profit_pct = take_profit_pct / 100    # Convert to decimal
        self.base_amount = base_amount                  # ₱ per trade
        self.position_sizing = position_sizing          # Position sizing strategy
        self.min_hold_hours = 0.5                       # 30 minutes minimum hold
        self.max_trades_per_day = 10                    # Safety limit
        self.trend_window = 12                          # 12 hours trend analysis
        self.check_interval = 900                       # 15 minutes

        # Runtime state
        self.running = False
        self.last_price = None
        self.position = None  # 'long' or None
        self.entry_price = None
        self.entry_time = None
        self.price_history = []
        self.daily_trades = {}

        # Display configuration
        self.logger.info(f"🤖 {self.name} - {self.description} v{self.version}")
        self.logger.info(f"🎯 Asset: {self.symbol} ({self.base_asset}/PHP)")
        self.logger.info(f"📈 Buy threshold: {buy_threshold:.1f}% (configurable)")
        self.logger.info(f"📉 Sell threshold: {sell_threshold:.1f}% (configurable)")
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
        log_filename = f"logs/titan_v4_{self.base_asset.lower()}.log"
        
        # Create custom logger for this TITAN instance
        self.logger = logging.getLogger(f'TitanTradingBot_v4_{self.base_asset}')
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
        self.logger.info(f"📝 TITAN v4.0 logging initialized for {self.symbol}")
        self.logger.info(f"📁 Log file: {log_filename}")

    def get_asset_market_data(self):
        """Get real-time market data for parameter validation"""
        try:
            # Get current price and 24hr ticker
            current_price = self.api.get_current_price(self.symbol)
            ticker_24hr = self.api.get_24hr_ticker(self.symbol)
            
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            volatility = abs(price_change_24h)
            
            return {
                'current_price': current_price,
                'volume_24h': volume_24h,
                'volatility': volatility,
                'price_change_24h': price_change_24h
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting market data: {e}")
            return None

    def validate_and_suggest_parameters(self):
        """Validate current parameters and provide optimization suggestions"""
        
        market_data = self.get_asset_market_data()
        if not market_data:
            return False
        
        volatility = market_data['volatility']
        volume = market_data['volume_24h']
        
        self.logger.info(f"📊 Market Analysis for {self.symbol}:")
        self.logger.info(f"   Current Price: ₱{market_data['current_price']:,.4f}")
        self.logger.info(f"   24h Volume: ₱{volume:,.0f}")
        self.logger.info(f"   24h Volatility: {volatility:.1f}%")
        
        # Parameter suggestions based on volatility
        suggestions = []
        warnings = []
        
        # Buy threshold analysis
        if volatility > 8:  # High volatility
            optimal_buy_range = (0.8, 1.5)
            if self.buy_threshold * 100 < optimal_buy_range[0]:
                suggestions.append(f"💡 Consider higher buy threshold ({optimal_buy_range[0]:.1f}%-{optimal_buy_range[1]:.1f}%) for high volatility asset")
        elif volatility > 3:  # Medium volatility  
            optimal_buy_range = (1.0, 2.0)
            if self.buy_threshold * 100 < optimal_buy_range[0]:
                suggestions.append(f"💡 Consider buy threshold {optimal_buy_range[0]:.1f}%-{optimal_buy_range[1]:.1f}% for medium volatility")
        else:  # Low volatility
            optimal_buy_range = (1.2, 2.5)
            if self.buy_threshold * 100 < optimal_buy_range[0]:
                suggestions.append(f"💡 Consider higher buy threshold ({optimal_buy_range[0]:.1f}%-{optimal_buy_range[1]:.1f}%) for low volatility asset")
        
        # Take profit analysis
        if volatility > 8:  # High volatility
            optimal_tp_range = (1.5, 3.0)
        elif volatility > 3:  # Medium volatility
            optimal_tp_range = (2.0, 5.0)
        else:  # Low volatility
            optimal_tp_range = (4.0, 8.0)
        
        if self.take_profit_pct * 100 < optimal_tp_range[0]:
            suggestions.append(f"💡 Consider higher take profit ({optimal_tp_range[0]:.1f}%-{optimal_tp_range[1]:.1f}%) for this volatility level")
        elif self.take_profit_pct * 100 > optimal_tp_range[1]:
            suggestions.append(f"💡 Consider lower take profit ({optimal_tp_range[0]:.1f}%-{optimal_tp_range[1]:.1f}%) for this volatility level")
        
        # Volume warnings
        if volume < 1000000:  # Low volume
            warnings.append(f"⚠️ Low volume asset (₱{volume:,.0f}) - May have liquidity issues")
        
        # Asset-specific recommendations based on backtesting discoveries
        if self.symbol == 'XRPPHP':
            if self.buy_threshold < 0.012:  # Less than 1.2%
                suggestions.append(f"🎯 XRPPHP Optimization: 1.2% buy threshold showed +1.6% return in backtesting")
            if self.take_profit_pct < 0.05:  # Less than 5%
                suggestions.append(f"🎯 XRPPHP Optimization: 5.0% take profit was optimal in backtesting")
        
        # Display suggestions
        if suggestions:
            self.logger.info(f"💡 PARAMETER OPTIMIZATION SUGGESTIONS:")
            for suggestion in suggestions:
                self.logger.info(f"   {suggestion}")
        
        if warnings:
            self.logger.warning(f"⚠️ TRADING WARNINGS:")
            for warning in warnings:
                self.logger.warning(f"   {warning}")
        
        if not suggestions and not warnings:
            self.logger.info(f"✅ Parameters look good for {self.symbol}!")
        
        return True

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
        Calculate dynamic position size based on selected strategy (from TITAN v3.3)
        """
        
        if self.position_sizing == 'fixed':
            return self.base_amount
            
        elif self.position_sizing == 'percentage':
            php_balance = self.api.get_balance('PHP')
            available_balance = php_balance['free'] if php_balance else 0
            position_pct = 0.10  # 10% of available balance
            calculated_size = available_balance * position_pct
            
            min_size = self.base_amount * 0.5
            max_size = self.base_amount * 2.0
            
            return max(min_size, min(calculated_size, max_size))
            
        elif self.position_sizing == 'momentum':
            base_size = self.base_amount
            
            # Strong momentum = larger position
            if abs(momentum) > self.buy_threshold * 2:  # 2x buy threshold
                multiplier = 1.4
            elif abs(momentum) > self.buy_threshold * 1.5:  # 1.5x buy threshold
                multiplier = 1.2
            elif abs(momentum) > self.buy_threshold:  # At threshold
                multiplier = 1.0
            else:
                multiplier = 0.8
            
            # Apply trend filter
            if trend < -0.03:
                multiplier *= 0.7
            elif trend > 0.02:
                multiplier *= 1.1
                
            calculated_size = base_size * multiplier
            
            min_size = self.base_amount * 0.5
            max_size = self.base_amount * 1.5
            
            return max(min_size, min(calculated_size, max_size))
            
        elif self.position_sizing == 'adaptive':
            php_balance = self.api.get_balance('PHP')
            available_balance = php_balance['free'] if php_balance else 0
            
            # Base sizing on available balance
            balance_multiplier = min(2.0, available_balance / (self.base_amount * 5))
            
            # Momentum adjustment (relative to threshold)
            momentum_strength = abs(momentum)
            momentum_ratio = momentum_strength / self.buy_threshold
            
            if momentum_ratio > 2.5:
                momentum_multiplier = 1.3
            elif momentum_ratio > 2.0:
                momentum_multiplier = 1.1
            elif momentum_ratio > 1.0:
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
            
            # Daily trades adjustment
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
            min_size = self.base_amount * 0.3
            max_size = self.base_amount * 2.0
            
            final_size = max(min_size, min(calculated_size, max_size))
            
            self.logger.info(f"📊 Adaptive sizing: Balance×{balance_multiplier:.1f}, "
                           f"Momentum×{momentum_multiplier:.1f} (ratio: {momentum_strength/self.buy_threshold:.1f}), "
                           f"Trend×{trend_multiplier:.1f}, Trades×{trade_multiplier:.1f} = ₱{final_size:.0f}")
            
            return final_size
        
        else:
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
        """Enhanced momentum strategy with configurable thresholds"""
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

            # Enhanced logging with threshold information
            threshold_status = "✅" if abs(price_change) > self.buy_threshold else "⏸️"
            self.logger.info(f"📊 {self.symbol}: ₱{current_price:.4f} ({price_change*100:+.2f}%) {threshold_status}")
            self.logger.info(f"   Thresholds: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%")
            self.logger.info(f"   Trend: {trend*100:+.1f}% | Balances: ₱{php_free:.2f} PHP, {asset_free:.6f} {self.base_asset}")

            # BUY CONDITIONS (using configurable threshold)
            if (price_change > self.buy_threshold and           # CONFIGURABLE buy threshold
                trend > -0.02 and                               # Not in strong downtrend
                php_free > self.base_amount * 0.6 and          # Have enough PHP
                self.can_trade_today() and                     # Within daily limit
                self.position is None):                        # No current position
                
                self.place_buy_order(current_price, price_change, trend)

            # SELL CONDITIONS - Momentum Down (using configurable threshold)
            elif (price_change < -self.sell_threshold and      # CONFIGURABLE sell threshold
                  asset_free > 0.001 and                       # Have position
                  self.can_sell_position() and                 # Min hold time met
                  self.can_trade_today()):                     # Within daily limit
                
                self.place_sell_order(current_price, price_change, trend, "Momentum Down")

            # SELL CONDITIONS - Take Profit (configurable)
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
            
            self.logger.info(f"🔄 {self.name} v{self.version} attempting BUY:")
            self.logger.info(f"   💰 Position size: ₱{amount_to_spend:.2f} ({self.position_sizing} sizing)")
            self.logger.info(f"   📊 Trigger: {change*100:+.2f}% > {self.buy_threshold*100:.1f}% threshold")
            self.logger.info(f"   🎯 Quantity: {quantity:.6f} {self.base_asset} at ₱{buy_price:.4f}")
            self.logger.info(f"   📈 Trend: {trend*100:+.1f}%")
            
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
                
                self.logger.info(f"✅ {self.name} v{self.version} BUY ORDER PLACED!")
                self.logger.info(f"   Order ID: {order['orderId']}")
                self.logger.info(f"   Entry: ₱{buy_price:.4f} | Target: ₱{buy_price * (1 + self.take_profit_pct):.4f}")
                
                # Send alert
                self.send_alert(f"🟢 {self.name} v{self.version} BUY {self.base_asset}: {quantity:.6f} at ₱{buy_price:.4f}")
                
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
            
            # Calculate P/L if we have entry price
            profit_loss_pct = 0
            if self.entry_price:
                profit_loss_pct = (sell_price - self.entry_price) / self.entry_price * 100
            
            self.logger.info(f"🔄 {self.name} v{self.version} attempting SELL:")
            self.logger.info(f"   📊 Trigger: {reason}")
            if reason == "Momentum Down":
                self.logger.info(f"   📉 Change: {change*100:+.2f}% < -{self.sell_threshold*100:.1f}% threshold")
            elif reason == "Take Profit":
                self.logger.info(f"   🎯 Profit: {profit_loss_pct:+.1f}% > {self.take_profit_pct*100:.1f}% target")
            self.logger.info(f"   💰 Amount: ₱{gross_amount:.2f} ({quantity_to_sell:.6f} {self.base_asset})")
            self.logger.info(f"   📊 P/L: {profit_loss_pct:+.2f}%")
            
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
                
                self.logger.info(f"✅ {self.name} v{self.version} SELL ORDER PLACED!")
                self.logger.info(f"   Order ID: {order['orderId']}")
                self.logger.info(f"   Exit: ₱{sell_price:.4f} | P/L: {profit_loss_pct:+.2f}%")
                
                # Send alert
                profit_emoji = "🟢" if profit_loss_pct > 0 else "🔴"
                self.send_alert(f"{profit_emoji} {self.name} v{self.version} SELL {self.base_asset}: {quantity_to_sell:.6f} at ₱{sell_price:.4f} ({reason}, {profit_loss_pct:+.1f}%)")
                
            else:
                self.logger.error(f"❌ {self.name} SELL ORDER FAILED: {order}")
                
        except Exception as e:
            self.logger.error(f"❌ Error placing sell order: {e}")

    def send_alert(self, message):
        """Send alert notification (placeholder for future implementation)"""
        self.logger.info(f"🔔 ALERT: {message}")

    def display_status(self):
        """Display current bot status with enhanced parameter information"""
        status = "🟢 RUNNING" if self.running else "🔴 STOPPED"
        position_status = f"📊 Position: {self.position}" if self.position else "📊 Position: None"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_trades = self.daily_trades.get(today, 0)
        
        self.logger.info(f"🤖 {self.name} v{self.version} Status: {status}")
        self.logger.info(f"🎯 Asset: {self.symbol} | Thresholds: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%")
        self.logger.info(f"📈 Take Profit: {self.take_profit_pct*100:.1f}% | Position Sizing: {self.position_sizing}")
        self.logger.info(f"{position_status}")
        self.logger.info(f"📈 Daily trades: {daily_trades}/{self.max_trades_per_day}")
        
        if self.entry_price:
            current_profit = ((self.last_price - self.entry_price) / self.entry_price * 100) if self.last_price else 0
            target_price = self.entry_price * (1 + self.take_profit_pct)
            self.logger.info(f"📊 Entry: ₱{self.entry_price:.4f} | Current P/L: {current_profit:+.1f}%")
            self.logger.info(f"🎯 Target: ₱{target_price:.4f} | Entry time: {self.entry_time.strftime('%H:%M:%S')}")

    def start(self):
        """Start the trading bot with enhanced validation"""
        self.logger.info(f"🚀 Starting {self.name} - {self.description} v{self.version}")
        self.logger.info(f"🎯 Configuration: {self.symbol} | Buy: {self.buy_threshold*100:.1f}% | Sell: {self.sell_threshold*100:.1f}% | TP: {self.take_profit_pct*100:.1f}%")
        self.logger.info(f"💰 Position Sizing: {self.position_sizing} | Base Amount: ₱{self.base_amount}")
        
        # Enhanced validation with parameter suggestions
        if not self.get_symbol_info():
            self.logger.error("❌ Symbol validation failed!")
            return
            
        if not self.get_account_status():
            self.logger.error("❌ Account validation failed!")
            return
        
        # Validate and suggest parameters
        if not self.validate_and_suggest_parameters():
            self.logger.error("❌ Parameter validation failed!")
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
                self.logger.info("=" * 80)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f"🛑 {self.name} v{self.version} stopped by user")
            self.stop()
        except Exception as e:
            self.logger.error(f"❌ Unexpected error: {e}")
            self.stop()

    def stop(self):
        """Stop the trading bot"""
        self.running = False
        self.logger.info(f"🛑 {self.name} - {self.description} v{self.version} stopped")

# ========== ENHANCED USER INTERFACE FUNCTIONS ==========

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

def get_asset_optimization_recommendations(symbol):
    """Get optimization recommendations based on backtesting discoveries"""
    
    # Backtesting-based recommendations
    recommendations = {
        'XRPPHP': {
            'buy_threshold': 1.2,
            'sell_threshold': 2.0,
            'take_profit': 5.0,
            'position_sizing': 'adaptive',
            'rationale': 'Backtesting showed +1.6% return with 1.2% buy threshold and 5.0% TP',
            'expected_performance': '+1.6% return, 58% win rate'
        },
        'SOLPHP': {
            'buy_threshold': 0.8,
            'sell_threshold': 1.3,
            'take_profit': 2.0,
            'position_sizing': 'momentum',
            'rationale': 'High volatility asset - lower thresholds with momentum sizing',
            'expected_performance': 'Variable based on volatility'
        },
        'BTCPHP': {
            'buy_threshold': 1.5,
            'sell_threshold': 2.5,
            'take_profit': 3.0,
            'position_sizing': 'percentage',
            'rationale': 'Low volatility - higher thresholds for signal quality',
            'expected_performance': 'Conservative, steady performance'
        }
    }
    
    # Default recommendations for other assets
    default = {
        'buy_threshold': 1.0,
        'sell_threshold': 1.7,
        'take_profit': 3.0,
        'position_sizing': 'adaptive',
        'rationale': 'Balanced settings for medium volatility assets',
        'expected_performance': 'Moderate performance expected'
    }
    
    return recommendations.get(symbol, default)

def get_user_inputs():
    """Enhanced user input collection with optimization recommendations"""
    print("🤖 TITAN - Advanced Momentum Trading Bot v4.0")
    print("💡 NEW: Configurable buy/sell thresholds with optimization recommendations")
    print("=" * 85)
    
    # Get symbol suggestions
    print("🔍 Getting available trading pairs...")
    suggestions = get_symbol_suggestions()
    
    if suggestions:
        print(f"\n📊 TOP VOLUME PHP PAIRS (Recommended):")
        for i, pair in enumerate(suggestions[:8], 1):
            volume_str = f"₱{pair['volume']/1000000:.1f}M" if pair['volume'] >= 1000000 else f"₱{pair['volume']/1000:.0f}K"
            change_emoji = "📈" if pair['price_change'] > 0 else "📉"
            print(f"  {i}. {pair['symbol']:<8} - {volume_str:<8} {change_emoji} {pair['price_change']:+.1f}%")
    
    # Asset selection
    print(f"\n🎯 Select trading asset:")
    print("1. XRPPHP - OPTIMIZED (1.2% buy, 5.0% TP = +1.6% backtested return)")
    print("2. SOLPHP - High volatility (Good for momentum strategies)")
    print("3. BTCPHP - Lower volatility (Stable, conservative)")
    print("4. Custom symbol - Enter any PHP trading pair")
    
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice == '1':
            symbol = 'XRPPHP'
            break
        elif choice == '2':
            symbol = 'SOLPHP'
            break
        elif choice == '3':
            symbol = 'BTCPHP'
            break
        elif choice == '4':
            while True:
                custom_symbol = input("Enter symbol (e.g., ETHPHP, ADAPHP): ").strip().upper()
                if custom_symbol.endswith('PHP') and len(custom_symbol) >= 6:
                    symbol = custom_symbol
                    break
                else:
                    print("Please enter a valid PHP trading pair (e.g., ETHPHP)")
            break
        else:
            print("Please enter 1-4")
    
    # Get optimization recommendations for selected asset
    recommendations = get_asset_optimization_recommendations(symbol)
    
    print(f"\n🎯 OPTIMIZATION RECOMMENDATIONS for {symbol}:")
    print(f"💡 Based on: {recommendations['rationale']}")
    print(f"📊 Expected: {recommendations['expected_performance']}")
    print(f"   Recommended Buy Threshold: {recommendations['buy_threshold']:.1f}%")
    print(f"   Recommended Sell Threshold: {recommendations['sell_threshold']:.1f}%")
    print(f"   Recommended Take Profit: {recommendations['take_profit']:.1f}%")
    print(f"   Recommended Position Sizing: {recommendations['position_sizing']}")
    
    # Buy threshold configuration
    print(f"\n📈 Configure Buy Threshold (Momentum trigger):")
    print(f"💡 Recommended: {recommendations['buy_threshold']:.1f}% (optimized for {symbol})")
    print(f"📊 Range: 0.5% (aggressive) to 2.5% (conservative)")
    print(f"   Higher = fewer but higher quality trades")
    print(f"   Lower = more frequent but potentially noisier trades")
    
    while True:
        try:
            buy_input = input(f"Enter buy threshold % (recommended: {recommendations['buy_threshold']:.1f}): ").strip()
            if not buy_input:
                buy_threshold = recommendations['buy_threshold']
                break
            else:
                buy_threshold = float(buy_input)
                if 0.1 <= buy_threshold <= 5.0:
                    break
                else:
                    print("Please enter a value between 0.1% and 5.0%")
        except ValueError:
            print("Please enter a valid number")
    
    # Sell threshold configuration
    print(f"\n📉 Configure Sell Threshold (Momentum down trigger):")
    print(f"💡 Recommended: {recommendations['sell_threshold']:.1f}% (typically 1.5-2x buy threshold)")
    print(f"📊 Range: 0.8% to 4.0%")
    
    while True:
        try:
            sell_input = input(f"Enter sell threshold % (recommended: {recommendations['sell_threshold']:.1f}): ").strip()
            if not sell_input:
                sell_threshold = recommendations['sell_threshold']
                break
            else:
                sell_threshold = float(sell_input)
                if 0.1 <= sell_threshold <= 5.0:
                    break
                else:
                    print("Please enter a value between 0.1% and 5.0%")
        except ValueError:
            print("Please enter a valid number")
    
    # Take profit configuration
    print(f"\n🎯 Configure Take Profit:")
    print(f"💡 Recommended: {recommendations['take_profit']:.1f}% (optimized for {symbol})")
    
    while True:
        try:
            take_profit = input(f"Enter take profit % (recommended: {recommendations['take_profit']:.1f}): ").strip()
            if not take_profit:
                take_profit = recommendations['take_profit']
                break
            else:
                take_profit = float(take_profit)
                if 0.5 <= take_profit <= 15.0:
                    break
                else:
                    print("Please enter a value between 0.5% and 15.0%")
        except ValueError:
            print("Please enter a valid number")
    
    # Position sizing selection
    print(f"\n📊 Select position sizing strategy:")
    print(f"1. Fixed - Same amount every trade")
    print(f"2. Percentage - 10% of available balance")
    print(f"3. Momentum - Larger positions on stronger signals")
    print(f"4. Adaptive - Multi-factor intelligent sizing (recommended)")
    print(f"💡 Recommended: {recommendations['position_sizing']} (optimized for {symbol})")
    
    position_sizing_map = {
        '1': 'fixed',
        '2': 'percentage', 
        '3': 'momentum',
        '4': 'adaptive'
    }
    
    # Find recommended option number
    recommended_option = None
    for key, value in position_sizing_map.items():
        if value == recommendations['position_sizing']:
            recommended_option = key
            break
    
    while True:
        sizing_choice = input(f"Enter choice (1-4, recommended: {recommended_option}): ").strip()
        if not sizing_choice and recommended_option:
            position_sizing = recommendations['position_sizing']
            break
        elif sizing_choice in position_sizing_map:
            position_sizing = position_sizing_map[sizing_choice]
            break
        else:
            print("Please enter 1, 2, 3, or 4")
    
    # Base amount configuration
    print(f"\n💰 Configure trade amount:")
    print(f"💡 Recommended: ₱200-400 range")
    
    while True:
        try:
            amount_input = input("Enter base trade amount in PHP (recommended: 300): ").strip()
            if not amount_input:
                base_amount = 300
                break
            else:
                base_amount = float(amount_input)
                if 50 <= base_amount <= 2000:
                    break
                else:
                    print("Please enter an amount between ₱50 and ₱2000")
        except ValueError:
            print("Please enter a valid number")
    
    # Configuration summary
    print(f"\n✅ TITAN v4.0 CONFIGURATION:")
    print(f"🎯 Asset: {symbol}")
    print(f"📈 Buy threshold: {buy_threshold:.1f}% (trigger for long entries)")
    print(f"📉 Sell threshold: {sell_threshold:.1f}% (trigger for exits)")
    print(f"🎯 Take profit: {take_profit:.1f}%")
    print(f"💰 Position sizing: {position_sizing.title()}")
    print(f"💰 Base amount: ₱{base_amount}")
    print(f"📁 Log file: logs/titan_v4_{symbol.replace('PHP', '').lower()}.log")
    
    # Parameter analysis
    print(f"\n📊 PARAMETER ANALYSIS:")
    ratio = sell_threshold / buy_threshold
    if ratio < 1.2:
        print("⚠️ Sell threshold might be too close to buy threshold")
    elif ratio > 3.0:
        print("⚠️ Sell threshold might be too far from buy threshold")
    else:
        print(f"✅ Good buy/sell ratio: {ratio:.1f}x")
    
    if buy_threshold < 0.8:
        print("💡 Low buy threshold = more frequent trading")
    elif buy_threshold > 1.5:
        print("💡 High buy threshold = more selective trading")
    
    print(f"\n🎯 Expected trading frequency: {'High' if buy_threshold < 1.0 else 'Medium' if buy_threshold < 1.5 else 'Low'}")
    
    return symbol, take_profit, base_amount, position_sizing, buy_threshold, sell_threshold

def main():
    """Enhanced main function"""
    # Check API credentials
    if not os.getenv('COINS_API_KEY') or not os.getenv('COINS_SECRET_KEY'):
        print("❌ API credentials not found!")
        print("Please set COINS_API_KEY and COINS_SECRET_KEY in your .env file")
        return
    
    # Get user configuration
    symbol, take_profit, base_amount, position_sizing, buy_threshold, sell_threshold = get_user_inputs()
    
    # Final confirmation
    print(f"\n🚀 Ready to start TITAN v4.0 with configurable thresholds!")
    print(f"💡 You can now adjust buy/sell thresholds without code changes")
    confirm = input("Start the bot? (y/n): ").lower().strip()
    
    if confirm.startswith('y'):
        # Initialize and start bot with all configurable parameters
        bot = TitanTradingBot(
            symbol=symbol, 
            take_profit_pct=take_profit, 
            base_amount=base_amount, 
            position_sizing=position_sizing,
            buy_threshold=buy_threshold,
            sell_threshold=sell_threshold
        )
        bot.start()
    else:
        print("👋 TITAN v4.0 startup cancelled")

if __name__ == '__main__':
    main()