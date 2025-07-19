import sys
import os
import time
import logging
import json
from pathlib import Path
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
    🤖 TITAN - Advanced Momentum Trading Bot v4.1
    
    NEW in v4.1:
    - ✅ Graceful exit handling (like Prophet)
    - ✅ Simplified asset selection interface
    - ✅ Improved error handling throughout
    - ✅ Cleaner user experience
    - ✅ Better keyboard interrupt handling
    """
    
    def __init__(self, symbol='XRPPHP', take_profit_pct=5.0, base_amount=200, 
                 position_sizing='adaptive', buy_threshold=1.2, sell_threshold=2.0):
        # Bot identity
        self.name = "TITAN"
        self.version = "4.1.0"
        self.description = "Advanced Momentum Trading Bot with Graceful Exit"
        
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
        log_filename = f"logs/titan_v41_{self.base_asset.lower()}.log"
        
        # Create custom logger for this TITAN instance
        self.logger = logging.getLogger(f'TitanTradingBot_v41_{self.base_asset}')
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
        self.logger.info(f"📝 TITAN v4.1 logging initialized for {self.symbol}")
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
        
        # Asset-specific recommendations based on Prophet analysis
        if self.symbol == 'XRPPHP':
            if self.buy_threshold < 0.012:  # Less than 1.2%
                suggestions.append(f"🔮 Prophet optimized XRPPHP: 1.2% buy, 2.0% sell, 8.0% TP for best results")
            if self.take_profit_pct < 0.08:  # Less than 8%
                suggestions.append(f"🔮 Prophet analysis: 8.0% take profit optimal for XRPPHP volatility")
        elif self.symbol == 'SOLPHP':
            if self.buy_threshold > 0.008:  # Greater than 0.8%
                suggestions.append(f"🔮 Prophet optimized SOLPHP: 0.6% buy threshold for high volatility")
            if self.take_profit_pct > 0.025:  # Greater than 2.5%
                suggestions.append(f"🔮 Prophet analysis: 2.0% TP optimal for SOL's rapid movements")
        elif self.symbol in ['PEPEPHP', 'DOGEPHP']:
            if self.buy_threshold > 0.010:  # Greater than 1.0%
                suggestions.append(f"🔮 Prophet meme coin optimization: 0.8% buy threshold for volatility")
            if self.position_sizing != 'momentum':
                suggestions.append(f"🔮 Prophet recommendation: Momentum sizing for meme coins")
        elif self.symbol in ['BTCPHP', 'ETHPHP']:
            if self.buy_threshold < 0.010:  # Less than 1.0%
                suggestions.append(f"🔮 Prophet stable coin optimization: 1.0% buy threshold for quality signals")
            if self.take_profit_pct < 0.03:  # Less than 3%
                suggestions.append(f"🔮 Prophet analysis: Higher TP (3-4%) for stable assets like {self.base_asset}")
        
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

def load_prophet_recommendations():
    """Load Prophet's latest optimization results from JSON file"""
    try:
        recommendations_file = Path('prophet_reco.json')
        
        if not recommendations_file.exists():
            print("📝 No Prophet recommendations found - using fallback defaults")
            print("💡 Run prophet.py first to get optimized parameters")
            return None
            
        with open(recommendations_file, 'r') as f:
            data = json.loads(f.read())
        
        # Check if recommendations are recent (within 7 days)
        if 'timestamp' in data:
            from datetime import datetime, timedelta
            recommendation_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - recommendation_time > timedelta(days=7):
                print(f"⚠️  Prophet recommendations are {(datetime.now() - recommendation_time).days} days old")
                print("💡 Consider running prophet.py again for fresh optimization")
        
        print(f"🔮 Loaded Prophet recommendations from {recommendation_time.strftime('%Y-%m-%d %H:%M') if 'timestamp' in data else 'recent analysis'}")
        return data.get('recommendations', {})
        
    except Exception as e:
        print(f"❌ Error loading Prophet recommendations: {e}")
        print("💡 Run prophet.py first to generate optimization data")
        return None

def get_asset_optimization_recommendations(symbol):
    """Get optimization recommendations from Prophet's analysis or fallback defaults"""
    
    # Try to load dynamic Prophet recommendations first
    prophet_data = load_prophet_recommendations()
    
    if prophet_data and symbol in prophet_data:
        # Use Prophet's dynamic recommendations
        rec = prophet_data[symbol]
        return {
            'buy_threshold': rec.get('buy_threshold', 1.0),
            'sell_threshold': rec.get('sell_threshold', 1.7),
            'take_profit': rec.get('take_profit', 4.0),
            'position_sizing': rec.get('position_sizing', 'adaptive'),
            'rationale': f"Prophet optimized on {rec.get('analysis_date', 'recent data')}: {rec.get('rationale', 'Latest Prophet analysis')}",
            'expected_performance': rec.get('expected_performance', 'Prophet-optimized performance'),
            'source': 'prophet_dynamic'
        }
    
    # Fallback to static recommendations if Prophet data not available
    static_recommendations = {
        'XRPPHP': {
            'buy_threshold': 1.2,
            'sell_threshold': 2.0,
            'take_profit': 8.0,
            'position_sizing': 'adaptive',
            'rationale': 'Fallback: Run prophet.py for latest XRPPHP optimization',
            'expected_performance': 'Static fallback - run Prophet for current optimization',
            'source': 'static_fallback'
        },
        'SOLPHP': {
            'buy_threshold': 0.6,
            'sell_threshold': 1.0,
            'take_profit': 2.0,
            'position_sizing': 'momentum',
            'rationale': 'Fallback: Run prophet.py for latest SOLPHP optimization',
            'expected_performance': 'Static fallback - run Prophet for current optimization',
            'source': 'static_fallback'
        },
        'BTCPHP': {
            'buy_threshold': 1.0,
            'sell_threshold': 1.7,
            'take_profit': 3.0,
            'position_sizing': 'adaptive',
            'rationale': 'Fallback: Run prophet.py for latest BTCPHP optimization',
            'expected_performance': 'Static fallback - run Prophet for current optimization',
            'source': 'static_fallback'
        }
    }
    
    # Default for unknown symbols
    default = {
        'buy_threshold': 1.0,
        'sell_threshold': 1.7,
        'take_profit': 4.0,
        'position_sizing': 'adaptive',
        'rationale': 'Default settings - run prophet.py for symbol-specific optimization',
        'expected_performance': 'Generic default - Prophet analysis recommended',
        'source': 'default'
    }
    
    recommendation = static_recommendations.get(symbol, default)
    
    if prophet_data:
        print(f"📝 {symbol} not in Prophet data - using fallback defaults")
        print(f"💡 Run: python prophet.py and select {symbol} for optimization")
    
    return recommendation

def get_user_inputs():
    """Enhanced user input collection with simplified interface and graceful exit handling"""
    try:
        print("🤖 TITAN - Advanced Momentum Trading Bot v4.1")
        print("✨ NEW: Graceful exit handling and simplified interface")
        print("=" * 65)
        
        # Get symbol suggestions
        print("🔍 Getting available trading pairs...")
        suggestions = get_symbol_suggestions()
        
        if suggestions:
            print(f"\n📊 TOP VOLUME PHP PAIRS:")
            for i, pair in enumerate(suggestions[:8], 1):
                volume_str = f"₱{pair['volume']/1000000:.1f}M" if pair['volume'] >= 1000000 else f"₱{pair['volume']/1000:.0f}K"
                change_emoji = "📈" if pair['price_change'] > 0 else "📉"
                print(f"  {i}. {pair['symbol']:<8} - {volume_str:<8} {change_emoji} {pair['price_change']:+.1f}%")
        
        # Simplified asset selection with Prophet optimization notes
        print(f"\n🎯 Select trading asset:")
        print("1. XRPPHP - Prophet optimized")
        print("2. SOLPHP - Prophet optimized") 
        print("3. BTCPHP - Prophet optimized")
        print("4. Custom symbol")
        
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
                    custom_symbol = input("Enter symbol (e.g., ETHPHP): ").strip().upper()
                    if custom_symbol.endswith('PHP') and len(custom_symbol) >= 6:
                        symbol = custom_symbol
                        break
                    else:
                        print("Please enter a valid PHP trading pair")
                break
            else:
                print("Please enter 1-4")
        
        # Get optimization recommendations for selected asset
        recommendations = get_asset_optimization_recommendations(symbol)
        
        # Show recommendation source and details
        source_emoji = "🔮" if recommendations['source'] == 'prophet_dynamic' else "📝" if recommendations['source'] == 'static_fallback' else "⚙️"
        source_text = "PROPHET DYNAMIC" if recommendations['source'] == 'prophet_dynamic' else "FALLBACK" if recommendations['source'] == 'static_fallback' else "DEFAULT"
        
        print(f"\n{source_emoji} {source_text} OPTIMIZATION for {symbol}:")
        print(f"💡 {recommendations['rationale']}")
        print(f"📊 Expected: {recommendations['expected_performance']}")
        print(f"   Buy: {recommendations['buy_threshold']:.1f}%")
        print(f"   Sell: {recommendations['sell_threshold']:.1f}%")
        print(f"   TP: {recommendations['take_profit']:.1f}%")
        
        if recommendations['source'] != 'prophet_dynamic':
            print(f"💡 Pro tip: Run 'python prophet.py' first to get latest optimized parameters for {symbol}")
        
        print(f"\n📝 You can accept these recommendations or enter your own values:")
        
        # Buy threshold configuration
        print(f"\n📈 Configure Buy Threshold:")
        print(f"💡 Prophet/Default: {recommendations['buy_threshold']:.1f}%")
        
        while True:
            try:
                buy_input = input(f"Enter buy threshold % (or press Enter for {recommendations['buy_threshold']:.1f}%): ").strip()
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
        print(f"\n📉 Configure Sell Threshold:")
        print(f"💡 Prophet/Default: {recommendations['sell_threshold']:.1f}%")
        
        while True:
            try:
                sell_input = input(f"Enter sell threshold % (or press Enter for {recommendations['sell_threshold']:.1f}%): ").strip()
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
        print(f"💡 Prophet/Default: {recommendations['take_profit']:.1f}%")
        
        while True:
            try:
                take_profit_input = input(f"Enter take profit % (or press Enter for {recommendations['take_profit']:.1f}%): ").strip()
                if not take_profit_input:
                    take_profit = recommendations['take_profit']
                    break
                else:
                    take_profit = float(take_profit_input)
                    if 0.5 <= take_profit <= 15.0:
                        break
                    else:
                        print("Please enter a value between 0.5% and 15.0%")
            except ValueError:
                print("Please enter a valid number")
        
        # Position sizing selection
        print(f"\n📊 Select position sizing:")
        print(f"1. Fixed")
        print(f"2. Percentage") 
        print(f"3. Momentum")
        print(f"4. Adaptive")
        print(f"💡 Prophet/Default: {recommendations['position_sizing']}")
        
        position_sizing_map = {
            '1': 'fixed',
            '2': 'percentage', 
            '3': 'momentum',
            '4': 'adaptive'
        }
        
        while True:
            sizing_choice = input(f"Enter choice (1-4, or press Enter for {recommendations['position_sizing']}): ").strip()
            if not sizing_choice:
                position_sizing = recommendations['position_sizing']
                break
            elif sizing_choice in position_sizing_map:
                position_sizing = position_sizing_map[sizing_choice]
                break
            else:
                print("Please enter 1, 2, 3, or 4")
        
        # Base amount configuration
        print(f"\n💰 Configure trade amount:")
        
        while True:
            try:
                amount_input = input("Enter base trade amount in PHP (or press Enter for ₱300): ").strip()
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
        
        # Configuration summary with source information
        config_source = "🔮 Prophet Dynamic" if recommendations['source'] == 'prophet_dynamic' else "📝 Fallback/Custom"
        print(f"\n✅ TITAN v4.1 CONFIGURATION ({config_source}):")
        print(f"🎯 Asset: {symbol}")
        print(f"📈 Buy threshold: {buy_threshold:.1f}%")
        print(f"📉 Sell threshold: {sell_threshold:.1f}%")
        print(f"🎯 Take profit: {take_profit:.1f}%")
        print(f"💰 Position sizing: {position_sizing.title()}")
        print(f"💰 Base amount: ₱{base_amount}")
        print(f"📁 Log file: logs/titan_v41_{symbol.replace('PHP', '').lower()}.log")
        
        # Show if user customized vs using recommendations
        customized = []
        if buy_threshold != recommendations['buy_threshold']:
            customized.append(f"Buy: {buy_threshold:.1f}% (was {recommendations['buy_threshold']:.1f}%)")
        if sell_threshold != recommendations['sell_threshold']:
            customized.append(f"Sell: {sell_threshold:.1f}% (was {recommendations['sell_threshold']:.1f}%)")
        if take_profit != recommendations['take_profit']:
            customized.append(f"TP: {take_profit:.1f}% (was {recommendations['take_profit']:.1f}%)")
        if position_sizing != recommendations['position_sizing']:
            customized.append(f"Sizing: {position_sizing} (was {recommendations['position_sizing']})")
        
        if customized:
            print(f"\n📝 Customized settings: {', '.join(customized)}")
        elif recommendations['source'] == 'prophet_dynamic':
            print(f"\n🔮 Using Prophet's optimized settings for {symbol}")
        else:
            print(f"\n📝 Using default settings - run Prophet for optimization")
        
        return symbol, take_profit, base_amount, position_sizing, buy_threshold, sell_threshold
        
    except KeyboardInterrupt:
        print("\n🛑 TITAN v4.1 setup cancelled gracefully")
        print("✨ Thank you for using TITAN")
        return None, None, None, None, None, None

def main():
    """Enhanced main function with graceful exit handling"""
    try:
        # Check API credentials
        if not os.getenv('COINS_API_KEY') or not os.getenv('COINS_SECRET_KEY'):
            print("❌ API credentials not found!")
            print("Please set COINS_API_KEY and COINS_SECRET_KEY in your .env file")
            return
        
        # Get user configuration with graceful exit handling
        result = get_user_inputs()
        if result[0] is None:  # User cancelled
            return
        
        symbol, take_profit, base_amount, position_sizing, buy_threshold, sell_threshold = result
        
        # Final confirmation
        print(f"\n🚀 Ready to start TITAN v4.1!")
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
            print("👋 TITAN v4.1 startup cancelled")
            
    except KeyboardInterrupt:
        print("\n🛑 TITAN v4.1 session ended gracefully")
        print("✨ Thank you for using TITAN")
    except Exception as e:
        print(f"\n❌ TITAN v4.1 encountered an error: {e}")
        print("🔧 Please check your configuration and try again")

if __name__ == '__main__':
    main()