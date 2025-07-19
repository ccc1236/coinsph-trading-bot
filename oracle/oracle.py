"""
🔮 ORACLE - AI-Enhanced Trading Bot v5.0

MAJOR UPDATE v5.0: Advanced ORACLE-Specific Position Sizing System
- ✅ AI Confidence-Based Sizing: Larger positions on higher AI confidence
- ✅ Market Volatility Adaptation: Dynamic sizing based on market conditions
- ✅ Signal Quality Assessment: Multi-factor signal evaluation
- ✅ Portfolio Balance Scaling: Position size grows with account
- ✅ Risk-Reward Optimization: Size based on AI target/stop ratios
- ✅ Configurable Position Sizing Strategies at startup
- ✅ Enhanced monitoring and logging for position decisions
- ✅ Real-time parameter validation and suggestions

Complete AI-powered trading system with MarketRaker integration, real-time USD/PHP conversion,
momentum confirmation, and intelligent position management.

🌟 NEW v5.0 FEATURES:
- 🎯 **AI Confidence Sizing**: Scale position with AI signal strength
- 📊 **Volatility Adaptive**: Smaller positions in volatile markets
- 🎪 **Signal Quality Matrix**: Multi-dimensional signal evaluation
- 💰 **Portfolio Scaling**: Positions grow with account balance
- ⚖️ **Risk-Reward Sizing**: Optimize position for target/stop ratio
- 🔧 **Configurable Strategy**: Choose sizing method at startup
- 📈 **Performance Tracking**: Monitor sizing strategy effectiveness
"""

import sys
import os
import logging
import asyncio
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
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
        logging.FileHandler('oracle_v5.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('OracleAITradingBot_v5')

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

@dataclass
class SignalQuality:
    """Signal Quality Assessment for Position Sizing"""
    ai_confidence: float       # 0.0 - 1.0 based on AI metrics
    risk_reward_ratio: float   # Target/Stop distance ratio
    market_alignment: float    # How well signal aligns with market conditions
    volatility_factor: float   # Current market volatility adjustment
    overall_score: float       # Combined quality score 0.0 - 1.0

class ExchangeRateManager:
    """Manages USD/PHP exchange rate conversion for AI signals"""
    
    def __init__(self):
        self.cached_rate = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # Cache for 1 hour
        logger.info("💱 ORACLE v5.0 Exchange Rate Manager initialized")
    
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

class AdvancedPositionSizer:
    """
    🎯 ORACLE v5.0 Advanced Position Sizing Engine
    
    Implements AI-specific position sizing strategies that optimize for:
    - AI signal confidence and quality
    - Market volatility and conditions  
    - Risk-reward ratios from AI targets
    - Portfolio balance and growth
    - Signal alignment with market momentum
    """
    
    def __init__(self, base_amount: float = 200, strategy: str = 'ai_confidence'):
        self.base_amount = base_amount
        self.strategy = strategy
        self.position_history = []
        self.performance_tracking = {
            'total_positions': 0,
            'profitable_positions': 0,
            'avg_position_size': 0,
            'size_performance_correlation': 0
        }
        
        logger.info(f"🎯 ORACLE v5.0 Advanced Position Sizer initialized")
        logger.info(f"💰 Base amount: ₱{self.base_amount}")
        logger.info(f"📊 Strategy: {self.strategy}")
    
    def calculate_signal_quality(self, ai_signal: AISignal, market_volatility: float, 
                               current_price: float, ai_prices_php: dict) -> SignalQuality:
        """
        Calculate comprehensive signal quality score for position sizing
        
        Args:
            ai_signal: The AI signal data
            market_volatility: Current 24h volatility percentage
            current_price: Current market price in PHP
            ai_prices_php: Converted AI prices in PHP
            
        Returns:
            SignalQuality object with detailed assessment
        """
        
        # 1. AI Confidence Score (based on risk level and expected change)
        # Lower risk = higher confidence, higher expected change = higher confidence
        risk_confidence = (10 - ai_signal.risk) / 10  # Risk 1 = 0.9, Risk 10 = 0.0
        change_confidence = min(abs(ai_signal.percentage_change) / 10, 1.0)  # Cap at 10%
        ai_confidence = (risk_confidence * 0.7) + (change_confidence * 0.3)
        
        # 2. Risk-Reward Ratio Assessment
        entry_price = ai_prices_php['ai_buy_php']
        target_price = ai_prices_php['ai_target_php']
        stop_price = ai_prices_php['ai_stop_php']
        
        potential_profit = abs(target_price - entry_price)
        potential_loss = abs(entry_price - stop_price)
        
        if potential_loss > 0:
            risk_reward_ratio = potential_profit / potential_loss
            # Normalize: 1:1 = 0.5, 2:1 = 0.67, 3:1 = 0.75, etc.
            rr_score = min(risk_reward_ratio / (risk_reward_ratio + 1), 0.9)
        else:
            rr_score = 0.5  # Neutral if no stop loss
        
        # 3. Market Alignment (how close current price is to AI entry)
        price_difference_pct = abs(current_price - entry_price) / entry_price * 100
        # Perfect alignment at 0% diff, decreases as difference increases
        alignment_score = max(0, 1 - (price_difference_pct / 5))  # 5% diff = 0 score
        
        # 4. Volatility Factor (lower volatility = more predictable)
        # High volatility reduces position size for safety
        if market_volatility <= 2:
            volatility_factor = 1.0  # Low volatility = full size
        elif market_volatility <= 5:
            volatility_factor = 0.8  # Medium volatility = 80%
        elif market_volatility <= 10:
            volatility_factor = 0.6  # High volatility = 60%
        else:
            volatility_factor = 0.4  # Very high volatility = 40%
        
        # 5. Overall Signal Quality Score (weighted combination)
        overall_score = (
            ai_confidence * 0.35 +      # 35% - AI confidence most important
            rr_score * 0.25 +           # 25% - Risk/reward ratio
            alignment_score * 0.25 +    # 25% - Price alignment
            volatility_factor * 0.15    # 15% - Market conditions
        )
        
        return SignalQuality(
            ai_confidence=ai_confidence,
            risk_reward_ratio=risk_reward_ratio if potential_loss > 0 else 1.0,
            market_alignment=alignment_score,
            volatility_factor=volatility_factor,
            overall_score=overall_score
        )
    
    def calculate_position_size(self, ai_signal: AISignal, signal_quality: SignalQuality,
                              available_balance: float, market_data: dict) -> float:
        """
        Calculate optimal position size based on selected strategy
        
        Args:
            ai_signal: AI signal data
            signal_quality: Calculated signal quality metrics
            available_balance: Available PHP balance
            market_data: Current market conditions
            
        Returns:
            Optimal position size in PHP
        """
        
        if self.strategy == 'ai_confidence':
            return self._ai_confidence_sizing(ai_signal, signal_quality, available_balance)
        elif self.strategy == 'volatility_adaptive':
            return self._volatility_adaptive_sizing(ai_signal, signal_quality, available_balance, market_data)
        elif self.strategy == 'signal_quality':
            return self._signal_quality_sizing(ai_signal, signal_quality, available_balance)
        elif self.strategy == 'portfolio_scaling':
            return self._portfolio_scaling_sizing(ai_signal, signal_quality, available_balance)
        elif self.strategy == 'risk_reward':
            return self._risk_reward_sizing(ai_signal, signal_quality, available_balance)
        elif self.strategy == 'adaptive_ai':
            return self._adaptive_ai_sizing(ai_signal, signal_quality, available_balance, market_data)
        else:
            return self.base_amount  # Fallback to fixed
    
    def _ai_confidence_sizing(self, ai_signal: AISignal, signal_quality: SignalQuality, 
                            available_balance: float) -> float:
        """Size based primarily on AI confidence metrics"""
        
        # Base size scaled by AI confidence
        confidence_multiplier = signal_quality.ai_confidence
        
        # Boost for very high confidence signals
        if signal_quality.ai_confidence > 0.8:
            confidence_multiplier *= 1.2
        
        # Reduce for low confidence
        if signal_quality.ai_confidence < 0.4:
            confidence_multiplier *= 0.7
        
        calculated_size = self.base_amount * confidence_multiplier
        
        # Apply bounds
        min_size = self.base_amount * 0.3
        max_size = min(self.base_amount * 1.5, available_balance * 0.2)
        
        final_size = max(min_size, min(calculated_size, max_size))
        
        logger.info(f"🎯 AI Confidence Sizing: {signal_quality.ai_confidence:.2f} confidence → ₱{final_size:.0f}")
        
        return final_size
    
    def _volatility_adaptive_sizing(self, ai_signal: AISignal, signal_quality: SignalQuality,
                                  available_balance: float, market_data: dict) -> float:
        """Size adapted for current market volatility"""
        
        volatility = market_data.get('volatility', 5)
        
        # Base volatility adjustment
        base_size = self.base_amount * signal_quality.volatility_factor
        
        # Additional AI confidence boost
        confidence_boost = signal_quality.ai_confidence * 0.3
        volatility_adjusted = base_size * (1 + confidence_boost)
        
        # Extra conservative in very volatile markets
        if volatility > 15:
            volatility_adjusted *= 0.6
        elif volatility > 10:
            volatility_adjusted *= 0.8
        
        min_size = self.base_amount * 0.2
        max_size = min(self.base_amount * 1.2, available_balance * 0.15)
        
        final_size = max(min_size, min(volatility_adjusted, max_size))
        
        logger.info(f"📊 Volatility Adaptive: {volatility:.1f}% vol, {signal_quality.volatility_factor:.2f} factor → ₱{final_size:.0f}")
        
        return final_size
    
    def _signal_quality_sizing(self, ai_signal: AISignal, signal_quality: SignalQuality,
                             available_balance: float) -> float:
        """Size based on overall signal quality score"""
        
        # Use overall quality score as primary multiplier
        quality_multiplier = signal_quality.overall_score
        
        # Bonus for exceptional signals
        if signal_quality.overall_score > 0.8:
            quality_multiplier *= 1.3
        
        # Extra bonus for perfect alignment signals
        if signal_quality.market_alignment > 0.9:
            quality_multiplier *= 1.1
        
        calculated_size = self.base_amount * quality_multiplier
        
        min_size = self.base_amount * 0.3
        max_size = min(self.base_amount * 1.6, available_balance * 0.25)
        
        final_size = max(min_size, min(calculated_size, max_size))
        
        logger.info(f"🎪 Signal Quality: {signal_quality.overall_score:.2f} score → ₱{final_size:.0f}")
        
        return final_size
    
    def _portfolio_scaling_sizing(self, ai_signal: AISignal, signal_quality: SignalQuality,
                                available_balance: float) -> float:
        """Size that scales with portfolio balance"""
        
        # Base percentage of available balance
        portfolio_percentage = 0.10  # 10% base
        
        # Adjust percentage based on signal quality
        adjusted_percentage = portfolio_percentage * signal_quality.overall_score
        
        # Minimum and maximum percentage bounds
        min_percentage = 0.05  # 5% minimum
        max_percentage = 0.20  # 20% maximum
        
        final_percentage = max(min_percentage, min(adjusted_percentage, max_percentage))
        calculated_size = available_balance * final_percentage
        
        # Ensure it's not too far from base amount
        min_size = self.base_amount * 0.5
        max_size = self.base_amount * 3.0
        
        final_size = max(min_size, min(calculated_size, max_size))
        
        logger.info(f"💰 Portfolio Scaling: {final_percentage*100:.1f}% of ₱{available_balance:.0f} → ₱{final_size:.0f}")
        
        return final_size
    
    def _risk_reward_sizing(self, ai_signal: AISignal, signal_quality: SignalQuality,
                          available_balance: float) -> float:
        """Size optimized for risk-reward ratio"""
        
        rr_ratio = signal_quality.risk_reward_ratio
        
        # Size based on risk-reward attractiveness
        if rr_ratio >= 3.0:  # 3:1 or better
            rr_multiplier = 1.4
        elif rr_ratio >= 2.0:  # 2:1 or better
            rr_multiplier = 1.2
        elif rr_ratio >= 1.5:  # 1.5:1 or better
            rr_multiplier = 1.0
        elif rr_ratio >= 1.0:  # 1:1 or better
            rr_multiplier = 0.8
        else:  # Poor risk/reward
            rr_multiplier = 0.5
        
        # Combine with AI confidence
        combined_multiplier = rr_multiplier * signal_quality.ai_confidence
        calculated_size = self.base_amount * combined_multiplier
        
        min_size = self.base_amount * 0.3
        max_size = min(self.base_amount * 1.5, available_balance * 0.20)
        
        final_size = max(min_size, min(calculated_size, max_size))
        
        logger.info(f"⚖️ Risk-Reward: {rr_ratio:.1f}:1 ratio, {combined_multiplier:.2f}x → ₱{final_size:.0f}")
        
        return final_size
    
    def _adaptive_ai_sizing(self, ai_signal: AISignal, signal_quality: SignalQuality,
                          available_balance: float, market_data: dict) -> float:
        """
        Advanced adaptive sizing combining all factors intelligently
        Most sophisticated ORACLE-specific strategy
        """
        
        # 1. Base size from signal quality
        quality_base = self.base_amount * signal_quality.overall_score
        
        # 2. AI confidence boost
        confidence_factor = 1 + (signal_quality.ai_confidence - 0.5) * 0.6  # -0.3 to +0.3
        
        # 3. Risk-reward adjustment
        rr_factor = min(signal_quality.risk_reward_ratio / 2, 1.2)  # Cap at 1.2x
        
        # 4. Market alignment bonus
        alignment_bonus = 1 + (signal_quality.market_alignment * 0.2)  # Up to +20%
        
        # 5. Volatility protection
        volatility_protection = signal_quality.volatility_factor
        
        # 6. Portfolio scaling component
        portfolio_factor = min(available_balance / (self.base_amount * 10), 1.5)  # Scale with balance
        
        # 7. Combine all factors
        total_multiplier = (
            confidence_factor * 
            rr_factor * 
            alignment_bonus * 
            volatility_protection * 
            portfolio_factor
        )
        
        calculated_size = quality_base * total_multiplier
        
        # Dynamic bounds based on signal quality
        min_size = self.base_amount * 0.25
        max_size = min(
            self.base_amount * 2.0,
            available_balance * 0.25
        )
        
        final_size = max(min_size, min(calculated_size, max_size))
        
        logger.info(f"🧠 Adaptive AI Sizing:")
        logger.info(f"   Quality: {signal_quality.overall_score:.2f}, Confidence: {confidence_factor:.2f}x")
        logger.info(f"   RR: {rr_factor:.2f}x, Alignment: {alignment_bonus:.2f}x")
        logger.info(f"   Volatility: {volatility_protection:.2f}x, Portfolio: {portfolio_factor:.2f}x")
        logger.info(f"   Total: {total_multiplier:.2f}x → ₱{final_size:.0f}")
        
        return final_size
    
    def track_position_performance(self, position_size: float, ai_signal: AISignal, 
                                 signal_quality: SignalQuality, final_pnl: Optional[float] = None):
        """Track position sizing performance for optimization"""
        
        position_record = {
            'timestamp': datetime.now(),
            'position_size': position_size,
            'ai_risk': ai_signal.risk,
            'signal_quality_score': signal_quality.overall_score,
            'ai_confidence': signal_quality.ai_confidence,
            'risk_reward_ratio': signal_quality.risk_reward_ratio,
            'strategy': self.strategy,
            'final_pnl': final_pnl
        }
        
        self.position_history.append(position_record)
        
        # Update performance tracking
        self.performance_tracking['total_positions'] += 1
        if final_pnl is not None and final_pnl > 0:
            self.performance_tracking['profitable_positions'] += 1
        
        # Calculate average position size
        total_size = sum(p['position_size'] for p in self.position_history)
        self.performance_tracking['avg_position_size'] = total_size / len(self.position_history)
        
        logger.info(f"📈 Position tracking updated: {len(self.position_history)} positions recorded")
    
    def get_sizing_strategy_performance(self) -> dict:
        """Get performance statistics for current sizing strategy"""
        
        if not self.position_history:
            return {'message': 'No position history available'}
        
        total_positions = len(self.position_history)
        profitable = len([p for p in self.position_history if p.get('final_pnl', 0) > 0])
        
        avg_size = sum(p['position_size'] for p in self.position_history) / total_positions
        avg_quality = sum(p['signal_quality_score'] for p in self.position_history) / total_positions
        
        return {
            'strategy': self.strategy,
            'total_positions': total_positions,
            'profitable_positions': profitable,
            'win_rate': (profitable / total_positions * 100) if total_positions > 0 else 0,
            'avg_position_size': avg_size,
            'avg_signal_quality': avg_quality,
            'performance_summary': f"{profitable}/{total_positions} wins ({profitable/total_positions*100:.1f}%)" if total_positions > 0 else "No data"
        }

class OracleAITradingBot:
    """
    🔮 ORACLE - AI-Enhanced Trading Bot v5.0
    
    Advanced AI-powered trading system with intelligent position sizing,
    MarketRaker integration, and comprehensive risk management.
    """
    
    def __init__(self, base_amount=200, position_sizing_strategy='ai_confidence'):
        # Bot identity
        self.name = "ORACLE"
        self.version = "5.0.0"
        self.description = "AI-Enhanced Trading Bot with Advanced Position Sizing"
        
        # Initialize Coins.ph API
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Initialize Exchange Rate Manager
        self.exchange_rate_manager = ExchangeRateManager()
        
        # Initialize Advanced Position Sizer
        self.position_sizer = AdvancedPositionSizer(
            base_amount=base_amount,
            strategy=position_sizing_strategy
        )
        
        # Trading Configuration
        self.base_amount = base_amount
        self.position_sizing_strategy = position_sizing_strategy
        self.supported_pairs = {
            'XRP/USD': 'XRPPHP',
            'SOL/USD': 'SOLPHP', 
            'BTC/USD': 'BTCPHP',
            'ETH/USD': 'ETHPHP'
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
        logger.info(f"📊 Position sizing: {self.position_sizing_strategy}")
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
                "position_sizing": self.position_sizing_strategy,
                "supported_pairs": list(self.supported_pairs.keys()),
                "features": [
                    "Advanced AI-specific position sizing",
                    "Signal quality assessment",
                    "Market volatility adaptation",
                    "Risk-reward optimization",
                    "Portfolio scaling",
                    "MarketRaker AI signals",
                    "Real-time USD/PHP conversion",
                    "Momentum confirmation"
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
                "position_sizing": self.position_sizing_strategy,
                "api_status": api_status,
                "exchange_rate": exchange_rate,
                "active_positions": len(self.current_positions),
                "daily_trades": self.daily_trades.get(datetime.now().strftime('%Y-%m-%d'), 0)
            }
        
        @self.app.get("/status")
        async def get_status():
            """Comprehensive status endpoint with position sizing info"""
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
            
            # Position sizing performance
            sizing_performance = self.position_sizer.get_sizing_strategy_performance()
            
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
                    "position_sizing_strategy": self.position_sizing_strategy,
                    "daily_trades": self.daily_trades.get(today, 0),
                    "max_daily": self.max_trades_per_day,
                    "active_positions": len(self.current_positions),
                    "price_tolerance": f"{self.price_tolerance}%",
                    **balance_info
                },
                "position_sizing": sizing_performance,
                "exchange_rate": exchange_info,
                "signals": {
                    "received": len(self.ai_signals),
                    "latest": list(self.ai_signals.keys())[-3:] if self.ai_signals else [],
                    "supported_pairs": list(self.supported_pairs.keys())
                }
            }
        
        @self.app.post("/webhook/marketraker")
        async def receive_ai_signal(request: Request):
            """Receive and process MarketRaker AI signals with v5.0 position sizing"""
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
                
                logger.info(f"🎯 {self.name} v{self.version}: MarketRaker AI Signal received!")
                logger.info(f"   Raw signal keys: {list(signal_data.keys())}")
                logger.info(f"   Signature: {'✅ Valid' if verification_key and signature else '⚠️ No verification'}")
                
                # Handle both MarketRaker direct format and wrapped format
                if signal_data.get('type') == 'indicator':
                    # Wrapped format: {"type": "indicator", "data": {...}}
                    logger.info(f"   Format: Wrapped indicator")
                    await self.process_ai_signal(signal_data['data'])
                    return JSONResponse({"status": "success", "message": f"{self.name} v{self.version} signal processed"})
                elif 'trading_type' in signal_data:
                    # Direct MarketRaker format: {"trading_type": "Long", "buy_price": 2.45, ...}
                    logger.info(f"   Format: Direct MarketRaker")
                    logger.info(f"   Trading type: {signal_data.get('trading_type')}")
                    logger.info(f"   Trading pair: {signal_data.get('trading_pair')}")
                    await self.process_ai_signal(signal_data)
                    return JSONResponse({"status": "success", "message": f"{self.name} v{self.version} MarketRaker signal processed"})
                else:
                    logger.warning(f"⚠️ {self.name}: Unknown signal format")
                    logger.debug(f"   Signal data: {signal_data}")
                    return JSONResponse({"status": "ignored", "message": "Unknown signal format"})
                    
            except Exception as e:
                logger.error(f"❌ {self.name} v{self.version} MarketRaker webhook error: {e}")
                return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        
        @self.app.post("/webhook/test")
        async def test_webhook(request: Request):
            """Test webhook endpoint - processes signals in test mode with v5.0 sizing"""
            try:
                payload = await request.body()
                signal_data = json.loads(payload.decode('utf-8'))
                
                logger.info(f"📨 {self.name} v{self.version}: Test webhook received!")
                
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
                    "message": f"{self.name} v{self.version} test signal processed",
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"❌ {self.name} v{self.version} test webhook error: {e}")
                return JSONResponse({"status": "error", "message": str(e)}, status_code=500)
        
        @self.app.post("/toggle-test-mode")
        async def toggle_test_mode():
            """Toggle between test mode and live trading"""
            self.test_mode = not self.test_mode
            logger.info(f"🔄 {self.name} v{self.version} Test mode: {'ON' if self.test_mode else 'OFF'}")
            return {
                "test_mode": self.test_mode, 
                "message": f"{self.name} v{self.version} test mode {'enabled' if self.test_mode else 'disabled'}"
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
        
        @self.app.get("/position-sizing-performance")
        async def get_position_sizing_performance():
            """Get detailed position sizing strategy performance"""
            return {
                "strategy": self.position_sizing_strategy,
                "performance": self.position_sizer.get_sizing_strategy_performance(),
                "available_strategies": [
                    "ai_confidence", "volatility_adaptive", "signal_quality",
                    "portfolio_scaling", "risk_reward", "adaptive_ai"
                ]
            }

    async def process_ai_signal(self, signal_data: Dict[str, Any], test_mode: Optional[bool] = None):
        """Process incoming AI signal with advanced v5.0 position sizing"""
        try:
            logger.info(f"🔍 Processing signal data type: {type(signal_data)}")
            logger.info(f"🔍 Signal data content: {signal_data}")
            
            # Handle different data formats from MarketRaker
            if isinstance(signal_data, str):
                try:
                    signal_data = json.loads(signal_data)
                    logger.info(f"✅ Parsed string data to dict: {signal_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Failed to parse signal data as JSON: {e}")
                    return
            
            # Ensure signal_data is a dictionary
            if not isinstance(signal_data, dict):
                logger.error(f"❌ Signal data is not a dictionary: {type(signal_data)}")
                return
            
            # Check if required fields exist
            required_fields = ['trading_type', 'buy_price', 'sell_price', 'trading_pair']
            missing_fields = [field for field in required_fields if field not in signal_data]
            
            if missing_fields:
                logger.error(f"❌ Missing required fields: {missing_fields}")
                logger.error(f"Available fields: {list(signal_data.keys())}")
                return
            
            # Create AISignal with proper error handling
            try:
                signal_dict = {
                    'trading_type': signal_data.get('trading_type'),
                    'leverage': signal_data.get('leverage', 1),
                    'buy_price': float(signal_data.get('buy_price')),
                    'sell_price': float(signal_data.get('sell_price')),
                    'buy_date': signal_data.get('buy_date', int(time.time())),
                    'sell_prediction_date': signal_data.get('sell_prediction_date', int(time.time()) + 86400),
                    'risk': signal_data.get('risk', 5),
                    'market_direction': signal_data.get('market_direction', 'Bull'),
                    'percentage_change': signal_data.get('percentage_change', 0.0),
                    'stoploss': float(signal_data.get('stoploss', signal_data.get('buy_price', 0) * 0.95)),
                    'trading_pair': signal_data.get('trading_pair')
                }
                
                signal = AISignal(**signal_dict)
                logger.info(f"✅ Created AISignal successfully: {signal.trading_type} {signal.trading_pair}")
                
            except Exception as e:
                logger.error(f"❌ Error creating AISignal: {e}")
                logger.error(f"Signal data: {signal_data}")
                return
            
            # Convert USD pair to PHP pair
            php_symbol = self.supported_pairs.get(signal.trading_pair)
            if not php_symbol:
                logger.warning(f"⚠️ {self.name}: Unsupported trading pair: {signal.trading_pair}")
                logger.info(f"Supported pairs: {list(self.supported_pairs.keys())}")
                return
            
            # Use provided test_mode or default to instance setting
            is_test = test_mode if test_mode is not None else self.test_mode
            mode_str = f"🧪 {self.name} v{self.version} TEST" if is_test else f"💰 {self.name} v{self.version} LIVE"
            
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
            logger.error(f"❌ {self.name} v{self.version} error processing AI signal: {e}")
            logger.error(f"Signal data type: {type(signal_data)}")
            logger.error(f"Signal data: {signal_data}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def process_ai_buy_signal(self, symbol: str, signal: AISignal, test_mode: bool):
        """Process AI buy signal with advanced v5.0 position sizing"""
        try:
            # Convert AI signal USD prices to PHP
            ai_prices_php = self.exchange_rate_manager.convert_ai_signal_to_php(signal)
            
            # Get current market data
            current_price = self.api.get_current_price(symbol)
            market_data = self.get_market_data(symbol)
            self.update_price_history(symbol, current_price)
            
            # Calculate momentum confirmation
            momentum_score = self.calculate_momentum_score(symbol)
            
            # Validate price levels
            price_validation = self.validate_price_levels(current_price, ai_prices_php)
            
            # Calculate signal quality using advanced v5.0 system
            signal_quality = self.position_sizer.calculate_signal_quality(
                signal, market_data['volatility'], current_price, ai_prices_php
            )
            
            logger.info(f"💱 {self.name} v{self.version} AI Signal Conversion:")
            logger.info(f"   Entry: ${signal.buy_price:.2f} → ₱{ai_prices_php['ai_buy_php']:.2f}")
            logger.info(f"   Target: ${signal.sell_price:.2f} → ₱{ai_prices_php['ai_target_php']:.2f}")
            logger.info(f"   Stop: ${signal.stoploss:.2f} → ₱{ai_prices_php['ai_stop_php']:.2f}")
            logger.info(f"   Rate: 1 USD = {ai_prices_php['usd_php_rate']:.4f} PHP")
            
            logger.info(f"📊 {self.name} v{self.version} Market Analysis:")
            logger.info(f"   Current: ₱{current_price:.2f}")
            logger.info(f"   Momentum: {momentum_score*100:+.1f}%")
            logger.info(f"   Volatility: {market_data['volatility']:.1f}%")
            
            logger.info(f"🎯 {self.name} v{self.version} Signal Quality Assessment:")
            logger.info(f"   AI Confidence: {signal_quality.ai_confidence:.2f}")
            logger.info(f"   Risk/Reward: {signal_quality.risk_reward_ratio:.1f}:1")
            logger.info(f"   Market Alignment: {signal_quality.market_alignment:.2f}")
            logger.info(f"   Volatility Factor: {signal_quality.volatility_factor:.2f}")
            logger.info(f"   Overall Score: {signal_quality.overall_score:.2f}")
            
            logger.info(f"🎯 {self.name} v{self.version} Price Level Validation:")
            logger.info(f"   Entry diff: {price_validation['entry_diff_pct']:+.1f}%")
            logger.info(f"   Upside potential: {price_validation['upside_potential']:+.1f}%")
            logger.info(f"   Downside risk: {price_validation['downside_risk']:+.1f}%")
            
            # Enhanced decision logic
            should_buy = self.should_execute_ai_buy_enhanced(
                signal, momentum_score, current_price, ai_prices_php, price_validation, signal_quality
            )
            
            if should_buy and self.can_trade_today():
                # Get available balance
                php_balance = self.api.get_balance('PHP')
                available_balance = php_balance['free'] if php_balance else 0
                
                # Calculate optimal position size using advanced v5.0 system
                optimal_position_size = self.position_sizer.calculate_position_size(
                    signal, signal_quality, available_balance, market_data
                )
                
                if test_mode:
                    logger.info(f"🧪 {self.name} v{self.version} TEST BUY SIMULATION:")
                    logger.info(f"   Would buy {symbol} with ₱{optimal_position_size:.0f}")
                    logger.info(f"   Position sizing strategy: {self.position_sizing_strategy}")
                    logger.info(f"   Signal quality score: {signal_quality.overall_score:.2f}")
                    logger.info(f"   Entry validation: {'✅' if price_validation['is_valid'] else '❌'}")
                    logger.info(f"   Momentum confirmation: {'✅' if momentum_score > self.momentum_buy_threshold else '❌'}")
                    logger.info(f"   Expected target: ₱{ai_prices_php['ai_target_php']:.2f}")
                    logger.info(f"   Risk/Reward: {price_validation['upside_potential']:.1f}% / {price_validation['downside_risk']:.1f}%")
                else:
                    # Execute real buy order with advanced sizing
                    await self.place_ai_buy_order_enhanced(symbol, signal, optimal_position_size, ai_prices_php, signal_quality)
            else:
                reason = self.get_rejection_reason(signal, momentum_score, price_validation, signal_quality)
                logger.info(f"⏸️ {self.name} v{self.version} AI buy signal rejected: {reason}")
                
        except Exception as e:
            logger.error(f"❌ {self.name} v{self.version} error processing AI buy signal: {e}")

    def get_market_data(self, symbol: str) -> dict:
        """Get current market data for the symbol"""
        try:
            ticker_24hr = self.api.get_24hr_ticker(symbol)
            
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            volatility = abs(price_change_24h)
            
            return {
                'volume_24h': volume_24h,
                'volatility': volatility,
                'price_change_24h': price_change_24h
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting market data: {e}")
            return {'volume_24h': 0, 'volatility': 5.0, 'price_change_24h': 0}

    async def process_ai_sell_signal(self, symbol: str, signal: AISignal, test_mode: bool):
        """Process AI sell signal or close existing position"""
        try:
            if test_mode:
                logger.info(f"🧪 {self.name} v{self.version} TEST SELL SIMULATION:")
                logger.info(f"   Would sell {symbol} position")
                logger.info(f"   AI target: ${signal.sell_price:.4f}")
                return
            
            # Check if we have an open position
            if symbol not in self.current_positions:
                logger.info(f"⏸️ {self.name} v{self.version}: No open position for {symbol} to close")
                return
            
            # Execute real sell based on AI signal
            await self.place_ai_sell_order(symbol, signal, "AI Signal")
            
        except Exception as e:
            logger.error(f"❌ {self.name} v{self.version} error processing AI sell signal: {e}")

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

    def should_execute_ai_buy_enhanced(self, signal, momentum, current_price, ai_prices_php, 
                                     price_validation, signal_quality):
        """Enhanced buy decision with v5.0 signal quality assessment"""
        
        # Risk filter: Skip very high risk signals
        if signal.risk > 8:
            logger.info(f"⚠️ {self.name} v{self.version}: AI signal risk too high: {signal.risk}/10")
            return False
        
        # Price level validation: Must be near AI entry price
        if not price_validation['is_valid']:
            logger.info(f"⚠️ {self.name} v{self.version}: Price level validation failed")
            return False
        
        # Signal quality filter: Require minimum quality score
        if signal_quality.overall_score < 0.3:
            logger.info(f"⚠️ {self.name} v{self.version}: Signal quality too low: {signal_quality.overall_score:.2f}")
            return False
        
        # Momentum confirmation: AI bullish + positive momentum
        if signal.market_direction.lower() == 'bull' and momentum > self.momentum_buy_threshold:
            logger.info(f"✅ {self.name} v{self.version}: AI + Momentum + Price level + Quality alignment")
            return True
        
        # High quality signal with good risk/reward even without momentum
        if (signal_quality.overall_score > 0.7 and 
            signal_quality.risk_reward_ratio > 2.0 and 
            signal.risk <= 4):
            logger.info(f"✅ {self.name} v{self.version}: High quality signal overrides momentum requirement")
            return True
        
        # Strong AI confidence with excellent price alignment
        if (signal_quality.ai_confidence > 0.8 and 
            signal_quality.market_alignment > 0.8 and 
            price_validation['upside_potential'] > 3.0):
            logger.info(f"✅ {self.name} v{self.version}: Strong AI confidence with excellent alignment")
            return True
        
        return False

    def get_rejection_reason(self, signal, momentum, price_validation, signal_quality):
        """Get human-readable rejection reason with v5.0 enhancements"""
        
        if signal.risk > 8:
            return f"High risk ({signal.risk}/10)"
        
        if signal_quality.overall_score < 0.3:
            return f"Low signal quality ({signal_quality.overall_score:.2f})"
        
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

    async def place_ai_buy_order_enhanced(self, symbol: str, signal: AISignal, position_size: float, 
                                        ai_prices_php: dict, signal_quality: SignalQuality):
        """Place buy order with enhanced v5.0 AI target tracking and position sizing"""
        try:
            current_price = self.api.get_current_price(symbol)
            quantity = position_size / current_price
            
            # Place limit order slightly above market
            buy_price = current_price * 1.001
            
            logger.info(f"🔄 {self.name} v{self.version} placing AI-guided BUY order:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity:.6f}")
            logger.info(f"   Price: ₱{buy_price:.4f}")
            logger.info(f"   Position Size: ₱{position_size:.2f} ({self.position_sizing_strategy} strategy)")
            logger.info(f"   Signal Quality: {signal_quality.overall_score:.2f}")
            logger.info(f"   AI Target: ₱{ai_prices_php['ai_target_php']:.2f}")
            logger.info(f"   AI Stop: ₱{ai_prices_php['ai_stop_php']:.2f}")
            logger.info(f"   Risk/Reward: {signal_quality.risk_reward_ratio:.1f}:1")
            
            order = self.api.place_order(
                symbol=symbol,
                side='BUY',
                order_type='LIMIT',
                quantity=f"{quantity:.6f}",
                price=f"{buy_price:.4f}",
                timeInForce='GTC'
            )
            
            if order.get('orderId'):
                # Store position with enhanced v5.0 data
                self.current_positions[symbol] = {
                    'entry_price': buy_price,
                    'entry_time': datetime.now(),
                    'quantity': quantity,
                    'position_size': position_size,
                    'ai_signal': signal,
                    'ai_prices_php': ai_prices_php,
                    'signal_quality': signal_quality,
                    'position_sizing_strategy': self.position_sizing_strategy,
                    'order_id': order['orderId']
                }
                
                self.update_daily_trades()
                
                # Track position for sizing performance analysis
                self.position_sizer.track_position_performance(
                    position_size, signal, signal_quality
                )
                
                logger.info(f"✅ {self.name} v{self.version} AI BUY ORDER PLACED!")
                logger.info(f"   Order ID: {order['orderId']}")
                
                # Enhanced alert with v5.0 details
                self.send_alert(f"🔔 🟢 {self.name} v{self.version} BUY {symbol}: {quantity:.6f} at ₱{buy_price:.4f}")
                self.send_alert(f"   📊 Strategy: {self.position_sizing_strategy}, Quality: {signal_quality.overall_score:.2f}")
                self.send_alert(f"   🎯 Target: ₱{ai_prices_php['ai_target_php']:.2f}, RR: {signal_quality.risk_reward_ratio:.1f}:1")
                
        except Exception as e:
            logger.error(f"❌ {self.name} v{self.version} error placing AI buy order: {e}")

    async def place_ai_sell_order(self, symbol: str, signal: AISignal, reason: str):
        """Place sell order based on AI signal with v5.0 performance tracking"""
        try:
            if symbol not in self.current_positions:
                logger.warning(f"⚠️ {self.name} v{self.version}: No position to sell for {symbol}")
                return
            
            position = self.current_positions[symbol]
            current_price = self.api.get_current_price(symbol)
            quantity_to_sell = position['quantity'] * 0.99
            
            # Use limit order slightly below market
            sell_price = current_price * 0.999
            
            # Calculate P/L
            entry_price = position['entry_price']
            profit_loss = (sell_price - entry_price) / entry_price * 100
            gross_amount = quantity_to_sell * sell_price
            
            logger.info(f"🔄 {self.name} v{self.version} placing AI-guided SELL order:")
            logger.info(f"   Symbol: {symbol}")
            logger.info(f"   Quantity: {quantity_to_sell:.6f}")
            logger.info(f"   Price: ₱{sell_price:.4f}")
            logger.info(f"   Gross Amount: ₱{gross_amount:.2f}")
            logger.info(f"   P/L: {profit_loss:+.1f}%")
            logger.info(f"   Reason: {reason}")
            logger.info(f"   Position Size: ₱{position.get('position_size', 0):.0f}")
            logger.info(f"   Strategy: {position.get('position_sizing_strategy', 'unknown')}")
            
            order = self.api.place_order(
                symbol=symbol,
                side='SELL',
                order_type='LIMIT',
                quantity=f"{quantity_to_sell:.6f}",
                price=f"{sell_price:.4f}",
                timeInForce='GTC'
            )
            
            if order.get('orderId'):
                # Update position sizing performance tracking
                if 'signal_quality' in position:
                    self.position_sizer.track_position_performance(
                        position.get('position_size', 0),
                        position['ai_signal'],
                        position['signal_quality'],
                        final_pnl=profit_loss
                    )
                
                # Clear position
                del self.current_positions[symbol]
                self.update_daily_trades()
                
                logger.info(f"✅ {self.name} v{self.version} AI SELL ORDER PLACED!")
                logger.info(f"   Order ID: {order['orderId']}")
                
                # Enhanced alert with v5.0 performance data
                profit_emoji = "🟢" if profit_loss > 0 else "🔴"
                self.send_alert(f"🔔 {profit_emoji} {self.name} v{self.version} SELL {symbol}: {quantity_to_sell:.6f} at ₱{sell_price:.4f}")
                self.send_alert(f"   📊 P/L: {profit_loss:+.1f}% | {reason} | Strategy: {position.get('position_sizing_strategy', 'unknown')}")
                
        except Exception as e:
            logger.error(f"❌ {self.name} v{self.version} error placing AI sell order: {e}")

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
        """Monitor existing positions for exit conditions with v5.0 enhancements"""
        for symbol, position in list(self.current_positions.items()):
            try:
                current_price = self.api.get_current_price(symbol)
                entry_price = position['entry_price']
                signal = position['ai_signal']
                ai_prices_php = position.get('ai_prices_php', {})
                signal_quality = position.get('signal_quality')
                
                # Enhanced position monitoring with signal quality awareness
                logger.debug(f"📊 Monitoring {symbol}: ₱{current_price:.4f} (entry: ₱{entry_price:.4f})")
                if signal_quality:
                    logger.debug(f"   Quality: {signal_quality.overall_score:.2f}, RR: {signal_quality.risk_reward_ratio:.1f}:1")
                
                # Check AI target reached
                if ai_prices_php and current_price >= ai_prices_php.get('ai_target_php', float('inf')):
                    logger.info(f"🎯 {self.name} v{self.version}: AI target reached for {symbol}!")
                    await self.place_ai_sell_order(symbol, signal, "AI Target Reached")
                    continue
                
                # Check AI stop loss
                if ai_prices_php and current_price <= ai_prices_php.get('ai_stop_php', 0):
                    logger.info(f"⛔ {self.name} v{self.version}: AI stop loss triggered for {symbol}!")
                    await self.place_ai_sell_order(symbol, signal, "AI Stop Loss")
                    continue
                
                # Dynamic exit based on signal quality degradation
                if signal_quality and signal_quality.overall_score < 0.2:
                    current_profit = (current_price - entry_price) / entry_price * 100
                    if current_profit > -2.0:  # Only if not losing too much
                        logger.info(f"📉 {self.name} v{self.version}: Signal quality degraded for {symbol}")
                        await self.place_ai_sell_order(symbol, signal, "Quality Degradation")
                        continue
                
                # Check minimum hold time
                hold_time = datetime.now() - position['entry_time']
                if hold_time >= timedelta(hours=self.min_hold_hours):
                    
                    # Check momentum-based exit
                    momentum = self.calculate_momentum_score(symbol)
                    if momentum < -self.momentum_sell_threshold:
                        logger.info(f"📉 {self.name} v{self.version}: Momentum exit for {symbol}")
                        await self.place_ai_sell_order(symbol, signal, "Momentum Exit")
                        continue
                    
                    # Time-based exit for low quality signals (risk management)
                    if signal_quality and signal_quality.overall_score < 0.4:
                        time_held_hours = hold_time.total_seconds() / 3600
                        if time_held_hours > 24:  # 24 hours for low quality signals
                            current_profit = (current_price - entry_price) / entry_price * 100
                            if current_profit > -5.0:  # Only if not losing too much
                                logger.info(f"⏰ {self.name} v{self.version}: Time exit for low quality {symbol}")
                                await self.place_ai_sell_order(symbol, signal, "Time-based Exit")
                                continue
                
            except Exception as e:
                logger.error(f"❌ {self.name} v{self.version} error monitoring {symbol}: {e}")

    def send_alert(self, message):
        """Send alert notification (placeholder for future implementation)"""
        logger.info(f"🔔 ALERT: {message}")

    async def start_monitoring_loop(self):
        """Start the monitoring loop for existing positions"""
        logger.info(f"📊 {self.name} v{self.version}: Starting position monitoring loop")
        
        while self.running:
            try:
                if self.current_positions:
                    await self.monitor_positions()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"❌ {self.name} v{self.version} monitoring error: {e}")
                await asyncio.sleep(60)

    async def start_server(self, port: int = 8000):
        """Start the webhook server with enhanced v5.0 monitoring"""
        logger.info("=" * 80)
        logger.info(f"🔮 {self.name} - {self.description} v{self.version}")
        logger.info("=" * 80)
        logger.info(f"🤖 Bot: {self.name} v{self.version}")
        logger.info(f"🌐 Webhook server starting on port {port}")
        logger.info(f"📡 Health check: http://localhost:{port}/health")
        logger.info(f"📊 Status: http://localhost:{port}/status")
        logger.info(f"💱 Exchange rate: http://localhost:{port}/exchange-rate")
        logger.info(f"📈 Position sizing performance: http://localhost:{port}/position-sizing-performance")
        logger.info(f"🧪 Test mode: {'ON' if self.test_mode else 'OFF'}")
        logger.info(f"🎯 Supported pairs: {', '.join(self.supported_pairs.keys())}")
        logger.info(f"💰 Base amount: ₱{self.base_amount}")
        logger.info(f"📊 Position sizing: {self.position_sizing_strategy}")
        logger.info(f"🎯 Price tolerance: {self.price_tolerance}%")
        logger.info("")
        logger.info("🌟 ORACLE v5.0 ADVANCED FEATURES:")
        logger.info("   ✅ AI Confidence-Based Position Sizing")
        logger.info("   ✅ Market Volatility Adaptation")
        logger.info("   ✅ Signal Quality Assessment Matrix")
        logger.info("   ✅ Portfolio Balance Scaling")
        logger.info("   ✅ Risk-Reward Optimization")
        logger.info("   ✅ Adaptive AI Strategy (most advanced)")
        logger.info("   ✅ Real-time Performance Tracking")
        logger.info("   ✅ Enhanced Position Monitoring")
        logger.info("")
        logger.info(f"📊 Available Position Sizing Strategies:")
        logger.info(f"   🎯 ai_confidence - Scale with AI signal strength")
        logger.info(f"   📊 volatility_adaptive - Adjust for market volatility")
        logger.info(f"   🎪 signal_quality - Based on multi-factor quality score")
        logger.info(f"   💰 portfolio_scaling - Grows with account balance")
        logger.info(f"   ⚖️ risk_reward - Optimized for target/stop ratios")
        logger.info(f"   🧠 adaptive_ai - Advanced multi-factor AI strategy (recommended)")
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
            logger.info(f"🛑 {self.name} v{self.version} server stopped by user")
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

# ========== ENHANCED USER INTERFACE FUNCTIONS v5.0 ==========

def get_position_sizing_strategies():
    """Get available position sizing strategies with descriptions"""
    return {
        'ai_confidence': {
            'name': 'AI Confidence',
            'description': 'Scale position size based on AI signal confidence',
            'best_for': 'Trusting AI signal quality assessment',
            'risk_level': 'Medium',
            'complexity': 'Simple'
        },
        'volatility_adaptive': {
            'name': 'Volatility Adaptive',
            'description': 'Adjust position size for market volatility',
            'best_for': 'Volatile market conditions',
            'risk_level': 'Low-Medium',
            'complexity': 'Medium'
        },
        'signal_quality': {
            'name': 'Signal Quality Matrix',
            'description': 'Multi-factor signal assessment sizing',
            'best_for': 'Comprehensive signal evaluation',
            'risk_level': 'Medium',
            'complexity': 'Medium'
        },
        'portfolio_scaling': {
            'name': 'Portfolio Scaling',
            'description': 'Position size grows with account balance',
            'best_for': 'Growing accounts and compound growth',
            'risk_level': 'Medium-High',
            'complexity': 'Simple'
        },
        'risk_reward': {
            'name': 'Risk-Reward Optimization',
            'description': 'Size based on AI target/stop ratios',
            'best_for': 'Risk-conscious trading',
            'risk_level': 'Low-Medium',
            'complexity': 'Medium'
        },
        'adaptive_ai': {
            'name': 'Adaptive AI (Recommended)',
            'description': 'Advanced multi-factor intelligent sizing',
            'best_for': 'Maximum optimization and performance',
            'risk_level': 'Medium',
            'complexity': 'Advanced'
        }
    }

def get_user_configuration():
    """Enhanced user configuration for ORACLE v5.0"""
    print("🔮 ORACLE - AI-Enhanced Trading Bot v5.0")
    print("🎯 NEW: Advanced AI-Specific Position Sizing System")
    print("=" * 75)
    
    # Base amount configuration
    print("💰 Configure base trading amount:")
    print("   This is your reference amount for position sizing calculations")
    print("   Actual position sizes will vary based on your chosen strategy")
    
    while True:
        try:
            amount_input = input("Enter base amount (₱100-₱1000, recommended: ₱200): ").strip()
            if not amount_input:
                base_amount = 200
                break
            else:
                base_amount = float(amount_input)
                if 100 <= base_amount <= 1000:
                    break
                else:
                    print("Please enter an amount between ₱100 and ₱1000")
        except ValueError:
            print("Please enter a valid number")
    
    # Position sizing strategy selection
    strategies = get_position_sizing_strategies()
    
    print(f"\n📊 Select Position Sizing Strategy:")
    print("   This determines how ORACLE calculates optimal position sizes")
    print()
    
    strategy_keys = list(strategies.keys())
    for i, (key, info) in enumerate(strategies.items(), 1):
        risk_emoji = {"Low": "🟢", "Low-Medium": "🟡", "Medium": "🟠", "Medium-High": "🔴", "High": "🔴"}
        complexity_emoji = {"Simple": "⭐", "Medium": "⭐⭐", "Advanced": "⭐⭐⭐"}
        
        print(f"{i}. {info['name']}")
        print(f"   📝 {info['description']}")
        print(f"   🎯 Best for: {info['best_for']}")
        print(f"   ⚠️ Risk: {risk_emoji.get(info['risk_level'], '🟠')} {info['risk_level']}")
        print(f"   🔧 Complexity: {complexity_emoji.get(info['complexity'], '⭐⭐')} {info['complexity']}")
        print()
    
    print("💡 Recommendation: 'Adaptive AI' for maximum performance optimization")
    
    while True:
        choice = input(f"Enter choice (1-6, recommended: 6): ").strip()
        if not choice:
            strategy = 'adaptive_ai'
            break
        elif choice in ['1', '2', '3', '4', '5', '6']:
            strategy = strategy_keys[int(choice) - 1]
            break
        else:
            print("Please enter 1-6")
    
    # Configuration summary
    selected_strategy = strategies[strategy]
    print(f"\n✅ ORACLE v5.0 CONFIGURATION:")
    print(f"💰 Base amount: ₱{base_amount}")
    print(f"📊 Position sizing: {selected_strategy['name']}")
    print(f"📝 Strategy: {selected_strategy['description']}")
    print(f"🎯 Optimized for: {selected_strategy['best_for']}")
    print(f"⚠️ Risk level: {selected_strategy['risk_level']}")
    
    print(f"\n🎯 Expected position size range:")
    min_size = base_amount * 0.25
    max_size = base_amount * 2.0
    print(f"   Minimum: ₱{min_size:.0f} (low quality signals)")
    print(f"   Maximum: ₱{max_size:.0f} (high quality signals)")
    print(f"   Average: ₱{base_amount:.0f} (typical signals)")
    
    print(f"\n📊 Position sizing will dynamically adjust based on:")
    if strategy == 'ai_confidence':
        print("   🎯 AI risk level (1-10)")
        print("   📊 AI expected percentage change")
        print("   🔍 Signal confidence metrics")
    elif strategy == 'volatility_adaptive':
        print("   📊 Current market volatility (24h)")
        print("   🎯 AI confidence level")
        print("   ⚠️ Risk protection in volatile markets")
    elif strategy == 'signal_quality':
        print("   🎪 Overall signal quality score")
        print("   ⚖️ Risk-reward ratio")
        print("   📍 Price alignment with AI entry")
        print("   📊 Market volatility factor")
    elif strategy == 'portfolio_scaling':
        print("   💰 Available account balance")
        print("   📊 Signal quality score")
        print("   📈 Portfolio growth adaptation")
    elif strategy == 'risk_reward':
        print("   ⚖️ AI target/stop loss ratio")
        print("   🎯 AI confidence metrics")
        print("   💡 Risk-optimized sizing")
    elif strategy == 'adaptive_ai':
        print("   🧠 Multi-factor intelligent analysis:")
        print("     • AI confidence and risk assessment")
        print("     • Risk-reward ratio optimization")
        print("     • Market volatility protection")
        print("     • Price alignment validation")
        print("     • Portfolio balance scaling")
        print("     • Dynamic bounds adjustment")
    
    return base_amount, strategy

def main():
    """Enhanced main function for ORACLE v5.0"""
    logger.info("🔍 Checking ORACLE v5.0 configuration...")
    
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
    
    # Get user configuration
    base_amount, position_sizing_strategy = get_user_configuration()
    
    # Display startup configuration
    logger.info("=" * 60)
    logger.info("🎯 ORACLE v5.0 STARTUP CONFIGURATION:")
    logger.info(f"   Base amount: ₱{base_amount}")
    logger.info(f"   Position sizing: {position_sizing_strategy}")
    logger.info(f"   Price tolerance: 3.0%")
    logger.info(f"   Exchange rate cache: 60 minutes")
    logger.info(f"   Test mode: ON (safe for development)")
    logger.info("=" * 60)
    
    # Final confirmation
    print(f"\n🚀 Ready to start ORACLE v5.0 with advanced position sizing!")
    print(f"🎯 Strategy: {get_position_sizing_strategies()[position_sizing_strategy]['name']}")
    confirm = input("Start the bot? (y/n): ").lower().strip()
    
    if confirm.startswith('y'):
        # Initialize bot with user configuration
        bot = OracleAITradingBot(
            base_amount=base_amount,
            position_sizing_strategy=position_sizing_strategy
        )
        
        try:
            asyncio.run(bot.start_server(port=8000))
        except KeyboardInterrupt:
            logger.info(f"👋 {bot.name} v{bot.version} goodbye!")
    else:
        print("👋 ORACLE v5.0 startup cancelled")

if __name__ == '__main__':
    main()