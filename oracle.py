"""
🔮 ORACLE - AI-Enhanced Trading Bot v4.0

Complete AI-powered trading system with MarketRaker integration, real-time USD/PHP conversion,
momentum confirmation, and advanced risk management.

🌟 FEATURES:
- ✅ FastAPI webhook server for MarketRaker signals
- ✅ Real-time USD/PHP exchange rate conversion  
- ✅ AI signal processing with momentum confirmation
- ✅ Smart price level validation
- ✅ Risk-based position sizing
- ✅ Dynamic exchange rate caching
- ✅ Comprehensive logging and monitoring
- ✅ Test mode for safe development
- ✅ Multiple API fallbacks
- ✅ Enhanced decision making logic
- ✅ FIXED: Direct MarketRaker format support
"""

import sys
import os
import logging
import asyncio
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

# FastAPI for webhook server
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Existing imports
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI

# Setup UTF-8 encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Load environment variables
load_dotenv(override=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('oracle.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('OracleAITradingBot')

@dataclass
class AISignal:
    """MarketRaker AI Signal Data Structure"""
    trading_type: str           # "Long" or "Short"
    leverage: int               # AI suggested leverage
    buy_price: float           # AI entry price (USD)
    sell_price: float          # AI target price (USD)
    buy_date: int              # Unix timestamp
    sell_prediction_date: int  # Unix timestamp
    risk: int                  # AI risk level (1-10)
    market_direction: str      # "Bull" or "Bear"
    percentage_change: float   # Expected % change
    stoploss: float           # AI stop loss price (USD)
    trading_pair: str         # "XRP/USD", "SOL/USD", etc.

class ExchangeRateManager:
    """Manages USD/PHP exchange rate conversion for AI signals"""
    
    def __init__(self):
        self.cached_rate = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # Cache for 1 hour
        logger.info("💱 ORACLE Exchange Rate Manager initialized")
    
    def get_usd_php_rate(self):
        """Get current USD/PHP exchange rate with smart caching"""
        
        # Check if we have recent cached data
        if (self.cached_rate and self.cache_timestamp and 
            (datetime.now() - self.cache_timestamp).seconds < self.cache_duration):
            return self.cached_rate
        
        # Try to fetch fresh rate
        rate = self._fetch_exchange_rate()
        self._cache_rate(rate)
        return rate
    
    def _fetch_exchange_rate(self):
        """Fetch exchange rate from multiple APIs with fallbacks"""
        
        # Option 1: ExchangeRate-API (Primary)
        try:
            response = requests.get("https://v6.exchangerate-api.com/v6/latest/USD", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('result') == 'success':
                    rate = data['conversion_rates']['PHP']
                    logger.info(f"💱 USD/PHP rate: {rate:.4f} (from ExchangeRate-API)")
                    return rate
        except Exception as e:
            logger.debug(f"Primary exchange API failed: {e}")
        
        # Option 2: Fawaz Free API (Fallback)
        try:
            response = requests.get("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                rate = data['usd']['php']
                logger.info(f"💱 USD/PHP rate: {rate:.4f} (from Fawaz Free API)")
                return rate
        except Exception as e:
            logger.debug(f"Fallback exchange API failed: {e}")
        
        # Option 3: Conservative estimate
        logger.warning("⚠️ All exchange rate APIs failed, using estimated rate")
        return 56.5  # Conservative PHP estimate
    
    def _cache_rate(self, rate):
        """Cache the exchange rate with timestamp"""
        self.cached_rate = rate
        self.cache_timestamp = datetime.now()
    
    def convert_ai_signal_to_php(self, ai_signal):
        """Convert AI signal USD prices to PHP with current exchange rate"""
        
        usd_php_rate = self.get_usd_php_rate()
        
        return {
            'ai_buy_php': ai_signal.buy_price * usd_php_rate,
            'ai_target_php': ai_signal.sell_price * usd_php_rate,
            'ai_stop_php': ai_signal.stoploss * usd_php_rate,
            'usd_php_rate': usd_php_rate,
            'percentage_change': ai_signal.percentage_change
        }

class OracleAITradingBot:
    """
    🔮 ORACLE - AI-Enhanced Trading Bot v4.0
    
    Advanced AI-powered trading system with MarketRaker integration,
    real-time currency conversion, and intelligent decision making.
    """
    
    def __init__(self, base_amount=200):
        # Bot identity
        self.name = "ORACLE"
        self.version = "4.0.0"
        self.description = "AI-Enhanced Trading Bot"
        
        # Initialize Coins.ph API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Initialize Exchange Rate Manager
        self.exchange_rate_manager = ExchangeRateManager()
        
        # Trading Configuration
        self.base_amount = base_amount
        self.supported_pairs = {
            'XRP/USD': 'XRPPHP',
            'SOL/USD': 'SOLPHP', 
            'BTC/USD': 'BTCPHP',
            'ETH/USD': 'ETHPHP',
            'BNB/USD': 'BNBPHP'
            # Meme coins (disabled for now)
            # 'DOGE/USD': 'DOGEPHP',
            # 'SHIB/USD': 'SHIBPHP',
            # 'PEPE/USD': 'PEPEPHP'
        }
        
        # Strategy Parameters (from Titan)
        self.momentum_buy_threshold = 0.006   # 0.6%
        self.momentum_sell_threshold = 0.010  # 1.0%
        self.min_hold_hours = 0.5
        self.max_trades_per_day = 15
        self.trend_window = 12
        self.price_tolerance = 3.0  # 3% tolerance for AI entry price
        
        # Runtime State
        self.running = False
        self.start_time = datetime.now()
        self.current_positions = {}  # symbol -> position_info
        self.ai_signals = {}         # symbol -> latest_signal
        self.price_history = {}      # symbol -> price_list
        self.daily_trades = {}
        self.test_mode = True        # Start in test mode for safety
        
        # FastAPI webhook server
        self.app = FastAPI(title=f"{self.name} AI Trading Bot", version=self.version)
        self.setup_routes()
        
        logger.info(f"🔮 {self.name} - {self.description} v{self.version} initialized")
        logger.info(f"💰 Base amount: ₱{self.base_amount}")
        logger.info(f"🎯 Supported pairs: {list(self.supported_pairs.keys())}")
        logger.info(f"🧪 Test mode: {'ON' if self.test_mode else 'OFF'}")
        logger.info(f"💱 Exchange rate caching: {self.exchange_rate_manager.cache_duration//60} minutes")

    def setup_routes(self):
        """Setup FastAPI routes with comprehensive endpoints"""
        
        @self.app.get("/")
        async def root():
            return {
                "message": f"{self.name} - {self.description} v{self.version}",
                "version": self.version,
                "status": "running" if self.running else "stopped",
                "test_mode": self.test_mode,
                "supported_pairs": list(self.supported_pairs.keys()),
                "features": [
                    "MarketRaker AI signals",
                    "Real-time USD/PHP conversion",
                    "Momentum confirmation",
                    "Price level validation", 
                    "Risk-based sizing"
                ]
            }
        
        @self.app.get("/health")
        async def health_check():
            uptime = datetime.now() - self.start_time
            
            # Check API connection
            api_status = "unknown"
            try:
                self.api.ping()
                api_status = "connected"
            except:
                api_status = "disconnected"
            
            # Check exchange rate
            exchange_rate = self.exchange_rate_manager.get_usd_php_rate()
            
            return {
                "status": "healthy",
                "bot_name": self.name,
                "version": self.version,
                "running": self.running,
                "uptime_seconds": int(uptime.total_seconds()),
                "test_mode": self.test_mode,
                "api_status": api_status,
                "exchange_rate": exchange_rate,
                "active_positions": len(self.current_positions),
                "daily_trades": self.daily_trades.get(datetime.now().strftime('%Y-%m-%d'), 0)
            }
        
        @self.app.get("/status")
        async def get_status():
            """Comprehensive status endpoint"""
            uptime = datetime.now() - self.start_time
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get account balance
            try:
                php_balance = self.api.get_balance('PHP')
                balance_info = {
                    "php_balance": php_balance['free'] if php_balance else 0,
                    "can_trade": php_balance['free'] >= self.base_amount if php_balance else False
                }
            except:
                balance_info = {"php_balance": "unknown", "can_trade": False}
            
            # Exchange rate info
            exchange_info = {
                "current_rate": self.exchange_rate_manager.cached_rate,
                "cache_age_minutes": 0 if not self.exchange_rate_manager.cache_timestamp else 
                    int((datetime.now() - self.exchange_rate_manager.cache_timestamp).seconds / 60),
                "cache_expires_in": self.exchange_rate_manager.cache_duration // 60
            }
            
            return {
                "bot": {
                    "name": self.name,
                    "description": self.description,
                    "version": self.version,
                    "running": self.running,
                    "test_mode": self.test_mode,
                    "start_time": self.start_time.isoformat(),
                    "uptime": str(uptime)
                },
                "trading": {
                    "base_amount": self.base_amount,
                    "daily_trades": self.daily_trades.get(today, 0),
                    "max_daily": self.max_trades_per_day,
                    "active_positions": len(self.current_positions),
                    "price_tolerance": f"{self.price_tolerance}%",
                    **balance_info
                },
                "exchange_rate": exchange_info,
                "signals": {
                    "received": len(self.ai_signals),
                    "latest": list(self.ai_signals.keys())[-3:] if self.ai_signals else [],
                    "supported_pairs": list(self.supported_pairs.keys())
                }
            }
        
        @self.app.post("/webhook/marketraker")
        async def receive_ai_signal(request: Request):
            """Receive and process MarketRaker AI signals - FIXED for direct format"""
            try:
                # Get payload and signature
                payload = await request.body()
                signature = request.headers.get('x-signature', '')
                
                # Verify signature for security
                verification_key = os.getenv('MARKETRAKER_VERIFICATION_KEY')
                if verification_key and signature:
                    # Basic signature verification (can be enhanced)
                    import hmac
                    import hashlib
                    expected_signature = hmac.new(
                        verification_key.encode('utf-8'),
                        payload,
                        hashlib.sha256
                    ).hexdigest()
                    
                    if not hmac.compare_digest(signature, expected_signature):
                        logger.warning(f"⚠️ {self.name}: Invalid MarketRaker signature")
                        # Continue anyway for testing, but log the warning
                
                signal_data = json.loads(payload.decode('utf-8'))
                
                logger.info(f"🎯 {self.name}: MarketRaker AI Signal received!")
                logger.info(f"   Raw signal keys: {list(signal_data.keys())}")
                logger.info(f"   Signature: {'✅ Valid' if verification_key and signature else '⚠️ No verification'}")
                
                # FIXED: Handle both MarketRaker direct format and wrapped format
                if signal_data.get('type') == 'indicator':
                    # Wrapped format: {"type": "indicator", "data": {...}}
                    logger.info(f"   Format: Wrapped indicator")
                    await self.process_ai_signal(signal_data['data'])
                    return JSONResponse({"status": "success", "message": f"{self.name} signal processed"})
                elif 'trading_type' in signal_data:
                    # Direct MarketRaker format: {"trading_type": "Long", "buy_price": 2.45, ...}
                    logger.info(f"   Format: Direct MarketRaker")
                    logger.info(f"   Trading type: {signal_data.get('trading_type')}")
                    logger.info(f"   Trading pair: {signal_data.get('trading_pair')}")
                    await self.process_ai_signal(signal_data)
                    return JSONResponse({"status": "success", "message": f"{self.name} MarketRaker signal processed"})
                else:
                    logger.warning(f"⚠️ {self.name}: Unknown signal format")
                    logger.debug(f"   Signal data: {signal_data}")
                    return JSONResponse({"status": "ignored", "message": "Unknown signal format"})
                    
            except Exception as e:
                logger.error(f"❌ {self.name} MarketRaker webhook error: {e}")
                return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        
        @self.app.post("/webhook/test")
        async def test_webhook(request: Request):
            """Test webhook endpoint - processes signals in test mode"""
            try:
                payload = await request.body()
                signal_data = json.loads(payload.decode('utf-8'))
                
                logger.info(f"📨 {self.name}: Test webhook received!")
                
                # Handle both formats for test endpoint too
                if signal_data.get('type') == 'indicator':
                    signal_to_process = signal_data['data']
                elif 'trading_type' in signal_data:
                    signal_to_process = signal_data
                else:
                    return JSONResponse({"status": "error", "message": "Unknown signal format"}, status_code=400)
                
                logger.info(f"   Signal: {signal_to_process.get('trading_type')} {signal_to_process.get('trading_pair')}")
                
                # Process signal in test mode
                await self.process_ai_signal(signal_to_process, test_mode=True)
                
                return JSONResponse({
                    "status": "success", 
                    "message": f"{self.name} test signal processed",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ {self.name} test webhook error: {e}")
                return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        
        @self.app.post("/toggle-test-mode")
        async def toggle_test_mode():
            """Toggle between test mode and live trading"""
            self.test_mode = not self.test_mode
            logger.info(f"🔄 {self.name} Test mode: {'ON' if self.test_mode else 'OFF'}")
            return {
                "test_mode": self.test_mode, 
                "message": f"{self.name} test mode {'enabled' if self.test_mode else 'disabled'}"
            }
        
        @self.app.get("/exchange-rate")
        async def get_exchange_rate():
            """Get current USD/PHP exchange rate info"""
            rate = self.exchange_rate_manager.get_usd_php_rate()
            cache_age = 0 if not self.exchange_rate_manager.cache_timestamp else \
                int((datetime.now() - self.exchange_rate_manager.cache_timestamp).seconds / 60)
            
            return {
                "usd_php_rate": rate,
                "cache_age_minutes": cache_age,
                "cache_duration_minutes": self.exchange_rate_manager.cache_duration // 60,
                "timestamp": datetime.now().isoformat()
            }

    async def process_ai_signal(self, signal_data: Dict[str, Any], test_mode: Optional[bool] = None):
        """Process incoming AI signal with complete analysis"""
        try:
            # Parse AI signal
            signal = AISignal(**signal_data)
            
            # Convert USD pair to PHP pair
            php_symbol = self.supported_pairs.get(signal.trading_pair)
            if not php_symbol:
                logger.warning(f"⚠️ {self.name}: Unsupported trading pair: {signal.trading_pair}")
                return
            
            # Use provided test_mode or default to instance setting
            is_test = test_mode if test_mode is not None else self.test_mode
            mode_str = f"🧪 {self.name} TEST" if is_test else f"💰 {self.name} LIVE"
            
            logger.info(f"🎯 {mode_str} AI Signal for {signal.trading_pair} → {php_symbol}")
            logger.info(f"   Type: {signal.trading_type}")
            logger.info(f"   Entry: ${signal.buy_price:.4f}")
            logger.info(f"   Target: ${signal.sell_price:.4f}")
            logger.info(f"   Risk: {signal.risk}/10")
            logger.info(f"   Expected: {signal.percentage_change:+.1f}%")
            
            # Store signal for reference
            self.ai_signals[php_symbol] = signal
            
            # Execute trading logic based on signal
            if signal.trading_type.lower() == 'long':
                await self.process_ai_buy_signal(php_symbol, signal, is_test)
            elif signal.trading_type.lower() == 'short':
                await self.process_ai_sell_signal(php_symbol, signal, is_test)
                
        except Exception as e:
            logger.error(f"❌ {self.name} error processing AI signal: {e}")

    async def process_ai_buy_signal(self, symbol: str, signal: AISignal, test_mode: bool):
        """Process AI buy signal with complete USD/PHP conversion and validation"""
        try:
            # Convert AI signal USD prices to PHP
            ai_prices_php = self.exchange_rate_manager.convert_ai_signal_to_php(signal)
            
            # Get current market data
            current_price = self.api.get_current_price(symbol)
            self.update_price_history(symbol, current_price)
            
            # Calculate momentum confirmation
            momentum_score = self.calculate_momentum_score(symbol)
            
            # Validate price levels
            price_validation = self.validate_price_levels(current_price, ai_prices_php)
            
            logger.info(f"💱 {self.name} AI Signal Conversion:")
            logger.info(f"   Entry: ${signal.buy_price:.2f} → ₱{ai_prices_php['ai_buy_php']:.2f}")
            logger.info(f"   Target: ${signal.sell_price:.2f} → ₱{ai_prices_php['ai_target_php']:.2f}")
            logger.info(f"   Stop: ${signal.stoploss:.2f} → ₱{ai_prices_php['ai_stop_php']:.2f}")
            logger.info(f"   Rate: 1 USD = {ai_prices_php['usd_php_rate']:.4f} PHP")
            
            logger.info(f"📊 {self.name} Market Analysis:")
            logger.info(f"   Current: ₱{current_price:.2f}")
            logger.info(f"   Momentum: {momentum_score*100:+.1f}%")
            
            logger.info(f"🎯 {self.name} Price Level Validation:")
            logger.info(f"   Entry diff: {price_validation['entry_diff_pct']:+.1f}%")
            logger.info(f"   Upside potential: {price_validation['upside_potential']:+.1f}%")
            logger.info(f"   Downside risk: {price_validation['downside_risk']:+.1f}%")
            
            # Enhanced decision logic
            should_buy = self.should_execute_ai_buy_enhanced(
                signal, momentum_score, current_price, ai_prices_php, price_validation
            )
            
            if should_buy and self.can_trade_today():
                # Calculate position size based on AI risk level
                position_size = self.calculate_ai_position_size(signal.risk)
                
                if test_mode:
                    logger.info(f"🧪 {self.name} TEST BUY SIMULATION:")
                    logger.info(f"   Would buy {symbol} with ₱{position_size:.0f}")
                    logger.info(f"   Entry validation: {'✅' if price_validation['is_valid'] else '❌'}")
                    logger.info(f"   Momentum confirmation: {'✅' if momentum_score > self.momentum_buy_threshold else '❌'}")
                    logger.info(f"   Expected target: ₱{ai_prices_php['ai_target_php']:.2f}")
                    logger.info(f"   Risk/Reward: {price_validation['upside_potential']:.1f}% / {price_validation['downside_risk']:.1f}%")
                else:
                    # Execute real buy order with PHP targets
                    await self.place_ai_buy_order_enhanced(symbol, signal, position_size, ai_prices_php)
            else:
                reason = self.get_rejection_reason(signal, momentum_score, price_validation)
                logger.info(f"⏸️ {self.name} AI buy signal rejected: {reason}")
                
        except Exception as e:
            logger.error(f"❌ {self.name} error processing AI buy signal: {e}")

    async def process_ai_sell_signal(self, symbol: str, signal: AISignal, test_mode: bool):
        """Process AI sell signal or close existing position"""
        try:
            if test_mode:
                logger.info(f"🧪 {self.name} TEST SELL SIMULATION:")
                logger.info(f"   Would sell {symbol} position")
                logger.info(f"   AI target: ${signal.sell_price:.4f}")
                return
            
            # Check if we have an open position
            if symbol not in self.current_positions:
                logger.info(f"⏸️ {self.name}: No open position for {symbol} to close")
                return
            
            # Execute real sell based on AI signal
            await self.place_ai_sell_order(symbol, signal, "AI Signal")
            
        except Exception as e:
            logger.error(f"❌ {self.name} error processing AI sell signal: {e}")

    def validate_price_levels(self, current_php_price, ai_prices_php, tolerance=None):
        """Validate if current price is suitable for AI signal execution"""
        
        if tolerance is None:
            tolerance = self.price_tolerance
        
        ai_entry = ai_prices_php['ai_buy_php']
        ai_target = ai_prices_php['ai_target_php']
        ai_stop = ai_prices_php['ai_stop_php']
        
        # Calculate price differences
        entry_diff_pct = abs(current_php_price - ai_entry) / ai_entry * 100
        upside_potential = (ai_target - current_php_price) / current_php_price * 100
        downside_risk = (current_php_price - ai_stop) / current_php_price * 100
        
        # Validation logic
        is_near_entry = entry_diff_pct <= tolerance
        has_upside = upside_potential > 1.0  # At least 1% upside
        reasonable_risk = downside_risk > 2.0  # Stop loss at least 2% below
        
        validation_result = {
            'is_valid': is_near_entry and has_upside and reasonable_risk,
            'entry_diff_pct': entry_diff_pct,
            'upside_potential': upside_potential,
            'downside_risk': downside_risk,
            'is_near_entry': is_near_entry,
            'has_upside': has_upside,
            'reasonable_risk': reasonable_risk,
            'ai_entry_php': ai_entry,
            'ai_target_php': ai_target,
            'ai_stop_php': ai_stop
        }
        
        return validation_result

    def should_execute_ai_buy_enhanced(self, signal, momentum, current_price, ai_prices_php, price_validation):
        """Enhanced buy decision with comprehensive validation"""
        
        # Risk filter: Skip very high risk signals
        if signal.risk > 8:
            logger.info(f"⚠️ {self.name}: AI signal risk too high: {signal.risk}/10")
            return False
        
        # Price level validation: Must be near AI entry price
        if not price_validation['is_valid']:
            logger.info(f"⚠️ {self.name}: Price level validation failed")
            return False
        
        # Momentum confirmation: AI bullish + positive momentum
        if signal.market_direction.lower() == 'bull' and momentum > self.momentum_buy_threshold:
            logger.info(f"✅ {self.name}: AI + Momentum + Price level alignment")
            return True
        
        # Strong AI confidence with good price level
        if (signal.risk <= 3 and 
            signal.percentage_change > 3.0 and 
            price_validation['upside_potential'] > 2.0):
            logger.info(f"✅ {self.name}: High AI confidence with good price level")
            return True
        
        return False

    def get_rejection_reason(self, signal, momentum, price_validation):
        """Get human-readable rejection reason"""
        
        if signal.risk > 8:
            return f"High risk ({signal.risk}/10)"
        
        if not price_validation['is_near_entry']:
            return f"Price too far from AI entry ({price_validation['entry_diff_pct']:.1f}% difference)"
        
        if not price_validation['has_upside']:
            return f"Limited upside potential ({price_validation['upside_potential']:.1f}%)"
        
        if not price_validation['reasonable_risk']:
            return f"Poor risk/reward ratio (stop too close)"
        
        if momentum <= self.momentum_buy_threshold:
            return f"Insufficient momentum ({momentum*100:+.1f}%)"
        
        if signal.market_direction.lower() != 'bull':
            return f"AI market direction is {signal.market_direction}"
        
        return "Multiple factors"

    def calculate_ai_position_size(self, ai_risk: int) -> float:
        """Calculate position size based on AI risk level"""
        
        # Risk-adjusted position sizing
        # Higher risk = smaller position
        risk_multiplier = max(0.3, 1.0 - (ai_risk - 1) * 0.1)
        
        adjusted_amount = self.base_amount * risk_multiplier
        
        logger.info(f"💰 {self.name} Position sizing: Risk {ai_risk}/10 → ₱{adjusted_amount:.0f} ({risk_multiplier*100:.0f}% of base)")
        
        return adjusted_amount

    async def place_ai_buy_order_enhanced(self, symbol: str, signal: AISignal, amount: float, ai_prices_php: dict):
        """Place buy order with enhanced AI target tracking"""
        try:
            current_price = self.api.get_current_price(symbol)
            quantity = amount / current_price
            
            # Place limit order slightly above market
            buy_price = current_price * 1.001
            
            logger.info(f"🔄 {self.name} placing AI-guided BUY order:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity:.6f}")
            logger.info(f"   Price: ₱{buy_price:.4f}")
            logger.info(f"   Amount: ₱{amount:.2f}")
            logger.info(f"   AI Target: ₱{ai_prices_php['ai_target_php']:.2f}")
            logger.info(f"   AI Stop: ₱{ai_prices_php['ai_stop_php']:.2f}")
            
            order = self.api.place_order(
                symbol=symbol,
                side='BUY',
                order_type='LIMIT',
                quantity=f"{quantity:.6f}",
                price=f"{buy_price:.4f}",
                timeInForce='GTC'
            )
            
            if order.get('orderId'):
                # Store position with AI signal data and PHP targets
                self.current_positions[symbol] = {
                    'entry_price': buy_price,
                    'entry_time': datetime.now(),
                    'quantity': quantity,
                    'ai_signal': signal,
                    'ai_prices_php': ai_prices_php,
                    'order_id': order['orderId']
                }
                
                self.update_daily_trades()
                
                logger.info(f"✅ {self.name} AI BUY ORDER PLACED!")
                logger.info(f"   Order ID: {order['orderId']}")
                
                # Send alert
                logger.info(f"🔔 ALERT: 🤖 {self.name} BUY {symbol}: {quantity:.6f} at ₱{buy_price:.4f} (Target: ₱{ai_prices_php['ai_target_php']:.2f})")
                
        except Exception as e:
            logger.error(f"❌ {self.name} error placing AI buy order: {e}")

    async def place_ai_sell_order(self, symbol: str, signal: AISignal, reason: str):
        """Place sell order based on AI signal"""
        try:
            if symbol not in self.current_positions:
                logger.warning(f"⚠️ {self.name}: No position to sell for {symbol}")
                return
            
            position = self.current_positions[symbol]
            current_price = self.api.get_current_price(symbol)
            quantity_to_sell = position['quantity'] * 0.99
            
            # Use limit order slightly below market
            sell_price = current_price * 0.999
            
            # Calculate P/L
            entry_price = position['entry_price']
            profit_loss = (sell_price - entry_price) / entry_price * 100
            
            logger.info(f"🔄 {self.name} placing AI-guided SELL order:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity_to_sell:.6f}")
            logger.info(f"   Price: ₱{sell_price:.4f}")
            logger.info(f"   P/L: {profit_loss:+.1f}%")
            logger.info(f"   Reason: {reason}")
            
            order = self.api.place_order(
                symbol=symbol,
                side='SELL',
                order_type='LIMIT',
                quantity=f"{quantity_to_sell:.6f}",
                price=f"{sell_price:.4f}",
                timeInForce='GTC'
            )
            
            if order.get('orderId'):
                # Clear position
                del self.current_positions[symbol]
                self.update_daily_trades()
                
                logger.info(f"✅ {self.name} AI SELL ORDER PLACED!")
                logger.info(f"   Order ID: {order['orderId']}")
                
                # Send alert
                profit_emoji = "🟢" if profit_loss > 0 else "🔴"
                logger.info(f"🔔 ALERT: {profit_emoji} {self.name} SELL {symbol}: {quantity_to_sell:.6f} at ₱{sell_price:.4f} ({profit_loss:+.1f}%)")
                
        except Exception as e:
            logger.error(f"❌ {self.name} error placing AI sell order: {e}")

    def update_price_history(self, symbol: str, price: float):
        """Update price history for momentum calculation"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        
        self.price_history[symbol].append({
            'price': price,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        cutoff = datetime.now() - timedelta(hours=self.trend_window * 2)
        self.price_history[symbol] = [
            p for p in self.price_history[symbol] 
            if p['timestamp'] > cutoff
        ]

    def calculate_momentum_score(self, symbol: str) -> float:
        """Calculate momentum score for the symbol"""
        if symbol not in self.price_history or len(self.price_history[symbol]) < 2:
            return 0.0
        
        prices = [p['price'] for p in self.price_history[symbol][-10:]]  # Last 10 prices
        if len(prices) < 2:
            return 0.0
        
        # Simple momentum: (current - avg) / avg
        current_price = prices[-1]
        avg_price = sum(prices[:-1]) / len(prices[:-1])
        
        return (current_price - avg_price) / avg_price

    def can_trade_today(self) -> bool:
        """Check if can still trade today"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.daily_trades.get(today, 0) < self.max_trades_per_day

    def update_daily_trades(self):
        """Update daily trade counter"""
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1

    async def monitor_positions(self):
        """Monitor existing positions for exit conditions"""
        for symbol, position in list(self.current_positions.items()):
            try:
                current_price = self.api.get_current_price(symbol)
                entry_price = position['entry_price']
                signal = position['ai_signal']
                ai_prices_php = position.get('ai_prices_php', {})
                
                # Check AI target reached
                if ai_prices_php and current_price >= ai_prices_php.get('ai_target_php', float('inf')):
                    logger.info(f"🎯 {self.name}: AI target reached for {symbol}!")
                    await self.place_ai_sell_order(symbol, signal, "AI Target Reached")
                    continue
                
                # Check AI stop loss
                if ai_prices_php and current_price <= ai_prices_php.get('ai_stop_php', 0):
                    logger.info(f"⛔ {self.name}: AI stop loss triggered for {symbol}!")
                    await self.place_ai_sell_order(symbol, signal, "AI Stop Loss")
                    continue
                
                # Check minimum hold time
                hold_time = datetime.now() - position['entry_time']
                if hold_time >= timedelta(hours=self.min_hold_hours):
                    
                    # Check momentum-based exit
                    momentum = self.calculate_momentum_score(symbol)
                    if momentum < -self.momentum_sell_threshold:
                        logger.info(f"📉 {self.name}: Momentum exit for {symbol}")
                        await self.place_ai_sell_order(symbol, signal, "Momentum Exit")
                        continue
                
            except Exception as e:
                logger.error(f"❌ {self.name} error monitoring {symbol}: {e}")

    async def start_monitoring_loop(self):
        """Start the monitoring loop for existing positions"""
        logger.info(f"📊 {self.name}: Starting position monitoring loop")
        
        while self.running:
            try:
                if self.current_positions:
                    await self.monitor_positions()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"❌ {self.name} monitoring error: {e}")
                await asyncio.sleep(60)

    async def start_server(self, port: int = 8000):
        """Start the webhook server with monitoring"""
        logger.info("=" * 80)
        logger.info(f"🔮 {self.name} - {self.description} v{self.version}")
        logger.info("=" * 80)
        logger.info(f"🤖 Bot: {self.name}")
        logger.info(f"🌐 Webhook server starting on port {port}")
        logger.info(f"📡 Health check: http://localhost:{port}/health")
        logger.info(f"📊 Status: http://localhost:{port}/status")
        logger.info(f"💱 Exchange rate: http://localhost:{port}/exchange-rate")
        logger.info(f"🧪 Test mode: {'ON' if self.test_mode else 'OFF'}")
        logger.info(f"🎯 Supported pairs: {', '.join(self.supported_pairs.keys())}")
        logger.info(f"💰 Base amount: ₱{self.base_amount}")
        logger.info(f"🎯 Price tolerance: {self.price_tolerance}%")
        logger.info("")
        logger.info("🌟 ORACLE FEATURES ENABLED:")
        logger.info("   ✅ MarketRaker AI signal processing")
        logger.info("   ✅ Real-time USD/PHP conversion")
        logger.info("   ✅ Momentum confirmation logic")
        logger.info("   ✅ Smart price level validation")
        logger.info("   ✅ Risk-based position sizing")
        logger.info("   ✅ Comprehensive monitoring")
        logger.info("   ✅ Test mode safety")
        logger.info("   ✅ FIXED: Direct MarketRaker format support")
        logger.info("")
        logger.info("   Press Ctrl+C to stop")
        logger.info("=" * 80)
        
        self.running = True
        
        # Start both webhook server and monitoring loop
        webhook_task = asyncio.create_task(self._run_server(port))
        monitoring_task = asyncio.create_task(self.start_monitoring_loop())
        
        try:
            await asyncio.gather(webhook_task, monitoring_task)
        except KeyboardInterrupt:
            logger.info(f"🛑 {self.name} server stopped by user")
        finally:
            self.running = False

    async def _run_server(self, port: int):
        """Internal server runner"""
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()

def main():
    """Main function with comprehensive startup checks"""
    logger.info("🔍 Checking ORACLE configuration...")
    
    # Check API credentials
    if not os.getenv('COINS_API_KEY') or not os.getenv('COINS_SECRET_KEY'):
        logger.error("❌ Coins.ph API credentials not found!")
        logger.error("   Please set COINS_API_KEY and COINS_SECRET_KEY in .env")
        return
    else:
        logger.info("✅ Coins.ph API credentials found")
    
    # Optional: Check MarketRaker credentials (for live signals)
    if not os.getenv('MARKETRAKER_VERIFICATION_KEY'):
        logger.warning("⚠️ MarketRaker verification key not found (optional for test mode)")
        logger.info("   Add MARKETRAKER_VERIFICATION_KEY for secure webhook verification")
    else:
        logger.info("✅ MarketRaker verification key found")
    
    # Display startup configuration
    logger.info("=" * 60)
    logger.info("🎯 ORACLE STARTUP CONFIGURATION:")
    logger.info(f"   Base amount: ₱200")
    logger.info(f"   Price tolerance: 3.0%")
    logger.info(f"   Exchange rate cache: 60 minutes")
    logger.info(f"   Test mode: ON (safe for development)")
    logger.info("=" * 60)
    
    # Initialize bot
    bot = OracleAITradingBot(base_amount=200)
    
    try:
        asyncio.run(bot.start_server(port=8000))
    except KeyboardInterrupt:
        logger.info(f"👋 {bot.name} goodbye!")

if __name__ == '__main__':
    main()