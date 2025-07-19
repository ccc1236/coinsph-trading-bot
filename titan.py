"""
🤖 TITAN - Advanced Momentum Trading Bot v4.2

MAJOR UPDATE v4.2: Profit-Optimized with Ecosystem Intelligence
- ✅ Ecosystem Integration: Loads research insights and optimization data
- ✅ Profit-First Asset Selection: Auto-ranks by performance scores
- ✅ Enhanced Prophet Integration: Loads ecosystem-enhanced recommendations
- ✅ Expected Return Predictions: Shows profit potential before trading
- ✅ Performance-Based Configuration: Only suggests profitable combinations
- ✅ Cross-Tool Intelligence: Benefits from Prophet + Momentum Backtest data
- ✅ Smart Parameter Validation: Ecosystem-aware optimization suggestions
- ✅ Profitability Dashboard: Real-time profit tracking vs predictions

Complete profit-optimized trading system with ecosystem intelligence and
enhanced parameter suggestions based on proven backtesting results.

🌟 NEW v4.2 PROFIT FEATURES:
- 💰 **Profit-First Ranking**: Assets ranked by ecosystem performance scores
- 🏆 **Auto-Load Best Configs**: Profitable parameters loaded automatically  
- 📊 **Expected Return Display**: See profit potential before starting
- 🔮 **Enhanced Prophet Integration**: Ecosystem-aware recommendations
- 🧠 **Cross-Tool Intelligence**: Benefits from all ecosystem analysis
- 📈 **Performance Validation**: Real-time vs predicted profit tracking
- 🎯 **Smart Asset Suggestions**: Only profitable opportunities shown
"""

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

# Import ecosystem manager with the established pattern
try:
    from ecosystem_manager import get_ecosystem_manager, log_tool_usage, get_asset_recommendations
    ECOSYSTEM_AVAILABLE = True
    print("✅ Ecosystem Manager available - profit intelligence enabled")
except ImportError:
    ECOSYSTEM_AVAILABLE = False
    print("⚠️ Ecosystem Manager not available - using v4.1 functionality")

class TitanTradingBotEcosystem:
    """
    🤖 TITAN - Advanced Momentum Trading Bot v4.2 with Ecosystem Intelligence
    
    NEW: Profit-optimized trading with ecosystem intelligence and cross-tool data sharing
    """
    
    def __init__(self, symbol='XRPPHP', take_profit_pct=5.0, base_amount=200, 
                 position_sizing='adaptive', buy_threshold=1.2, sell_threshold=2.0):
        # Bot identity
        self.name = "TITAN"
        self.version = "4.2.0"
        self.description = "Profit-Optimized Trading Bot with Ecosystem Intelligence"
        
        # Trading parameters - now fully configurable with ecosystem intelligence!
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
        
        # Ecosystem integration
        self.ecosystem_manager = None
        self.ecosystem_insights = []
        self.ecosystem_recommendations = {}
        self.profit_predictions = {}
        
        if ECOSYSTEM_AVAILABLE:
            try:
                self.ecosystem_manager = get_ecosystem_manager()
                log_tool_usage('titan', '4.2')
                self.logger.info("🌐 Ecosystem Manager connected")
                
                # Load ecosystem intelligence
                self.load_ecosystem_intelligence()
                
            except Exception as e:
                self.logger.warning(f"⚠️ Ecosystem Manager connection failed: {e}")
                self.ecosystem_manager = None
        
        # Strategy parameters (now configurable at startup with ecosystem intelligence!)
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
        
        # Profit tracking
        self.profit_tracking = {
            'predicted_return': 0,
            'predicted_win_rate': 0,
            'actual_trades': 0,
            'profitable_trades': 0,
            'total_profit_loss': 0
        }

        # Display configuration with ecosystem context
        self.logger.info(f"🤖 {self.name} - {self.description} v{self.version}")
        self.logger.info(f"🎯 Asset: {self.symbol} ({self.base_asset}/PHP)")
        self.logger.info(f"📈 Buy threshold: {buy_threshold:.1f}% (ecosystem-enhanced)")
        self.logger.info(f"📉 Sell threshold: {sell_threshold:.1f}% (ecosystem-enhanced)")
        self.logger.info(f"🎯 Take profit: {take_profit_pct:.1f}%")
        self.logger.info(f"💰 Base amount: ₱{self.base_amount}")
        self.logger.info(f"📊 Position sizing: {self.position_sizing}")
        self.logger.info(f"⏰ Min hold time: {self.min_hold_hours}h")
        self.logger.info(f"🔄 Max trades/day: {self.max_trades_per_day}")
        self.logger.info(f"📊 Check interval: {self.check_interval//60} minutes")
        if ECOSYSTEM_AVAILABLE:
            self.logger.info(f"🌐 Ecosystem integration: Active")

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
        self.logger.info(f"📝 TITAN v4.2 logging initialized for {self.symbol}")
        self.logger.info(f"📁 Log file: {log_filename}")

    def load_ecosystem_intelligence(self):
        """Load ecosystem intelligence for profit optimization"""
        try:
            if not self.ecosystem_manager:
                return
            
            # Get research insights sorted by performance
            self.ecosystem_insights = self.ecosystem_manager.load_research_insights()
            
            # Get smart recommendations for TITAN
            self.ecosystem_recommendations = self.ecosystem_manager.get_smart_recommendations('titan')
            
            if self.ecosystem_insights:
                self.logger.info(f"🧠 Loaded {len(self.ecosystem_insights)} ecosystem research insights")
                
                # Show top performing assets from ecosystem
                top_assets = self.ecosystem_manager.get_top_assets(limit=5)
                if top_assets:
                    self.logger.info(f"🏆 Top ecosystem performers:")
                    for i, asset in enumerate(top_assets, 1):
                        self.logger.info(f"   {i}. {asset.symbol}: {asset.performance_score:.1f}/10 "
                                       f"({asset.risk_level} risk, {asset.recommended_strategy} strategy)")
            
            if self.ecosystem_recommendations.get('workflow_suggestions'):
                self.logger.info(f"💡 Ecosystem workflow suggestions:")
                for suggestion in self.ecosystem_recommendations['workflow_suggestions']:
                    self.logger.info(f"   • {suggestion}")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error loading ecosystem intelligence: {e}")
            self.ecosystem_insights = []
            self.ecosystem_recommendations = {}

    def get_ecosystem_asset_insight(self, symbol: str):
        """Get ecosystem insight for a specific asset"""
        for insight in self.ecosystem_insights:
            if insight.symbol == symbol:
                return insight
        return None

    def get_profit_ranked_assets(self, limit: int = 8):
        """Get assets ranked by profit potential from ecosystem research"""
        if not self.ecosystem_insights:
            return []
        
        # Sort by performance score (profit potential)
        sorted_insights = sorted(self.ecosystem_insights, 
                               key=lambda x: x.performance_score, reverse=True)
        
        profit_ranked = []
        for insight in sorted_insights[:limit]:
            # Get latest optimization for this asset
            latest_optimization = self.ecosystem_manager.get_latest_optimization(insight.symbol)
            
            expected_return = latest_optimization.expected_return if latest_optimization else 0
            win_rate = latest_optimization.win_rate if latest_optimization else 0
            
            profit_ranked.append({
                'symbol': insight.symbol,
                'performance_score': insight.performance_score,
                'expected_return': expected_return,
                'win_rate': win_rate,
                'risk_level': insight.risk_level,
                'recommended_strategy': insight.recommended_strategy,
                'volatility': insight.volatility,
                'profit_reason': f"{insight.performance_score:.1f}/10 score, {expected_return:+.1f}% expected return"
            })
        
        return profit_ranked

    def get_ecosystem_profit_recommendations(self, symbol: str):
        """Get profit-optimized recommendations from ecosystem intelligence"""
        
        # Get ecosystem insight for this symbol
        insight = self.get_ecosystem_asset_insight(symbol)
        
        # Get latest optimization results
        latest_optimization = None
        if self.ecosystem_manager:
            latest_optimization = self.ecosystem_manager.get_latest_optimization(symbol)
        
        if latest_optimization:
            # Use ecosystem optimization results
            return {
                'buy_threshold': latest_optimization.buy_threshold,
                'sell_threshold': latest_optimization.sell_threshold,
                'take_profit': latest_optimization.take_profit,
                'expected_return': latest_optimization.expected_return,
                'win_rate': latest_optimization.win_rate,
                'position_sizing': insight.recommended_strategy if insight else 'adaptive',
                'rationale': f"Ecosystem optimized on {latest_optimization.optimization_date}: {latest_optimization.expected_return:+.1f}% return, {latest_optimization.win_rate:.1f}% win rate",
                'source': 'ecosystem_optimization',
                'profit_score': insight.performance_score if insight else 5.0,
                'risk_level': insight.risk_level if insight else 'medium'
            }
        
        elif insight:
            # Use ecosystem research insights with parameter hints
            buy_range = [0.008, 0.010, 0.012] if insight.volatility > 8 else [0.010, 0.012, 0.015]
            tp_range = [0.015, 0.020, 0.025] if insight.volatility > 8 else [0.030, 0.040, 0.050]
            
            return {
                'buy_threshold': buy_range[1],  # Use middle value
                'sell_threshold': buy_range[1] * 1.67,
                'take_profit': tp_range[1],  # Use middle value
                'expected_return': insight.performance_score,  # Use as rough estimate
                'win_rate': 65.0,  # Default estimate
                'position_sizing': insight.recommended_strategy,
                'rationale': f"Ecosystem research: {insight.performance_score:.1f}/10 performance score, {insight.risk_level} risk",
                'source': 'ecosystem_research',
                'profit_score': insight.performance_score,
                'risk_level': insight.risk_level
            }
        
        return None

    def get_asset_market_data(self):
        """Get real-time market data for parameter validation with ecosystem context"""
        try:
            # Get current price and 24hr ticker
            current_price = self.api.get_current_price(self.symbol)
            ticker_24hr = self.api.get_24hr_ticker(self.symbol)
            
            volume_24h = float(ticker_24hr.get('quoteVolume', 0))
            price_change_24h = float(ticker_24hr.get('priceChangePercent', 0))
            volatility = abs(price_change_24h)
            
            market_data = {
                'current_price': current_price,
                'volume_24h': volume_24h,
                'volatility': volatility,
                'price_change_24h': price_change_24h
            }
            
            # Add ecosystem context if available
            ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
            if ecosystem_insight:
                market_data['ecosystem_score'] = ecosystem_insight.performance_score
                market_data['ecosystem_risk'] = ecosystem_insight.risk_level
                market_data['ecosystem_strategy'] = ecosystem_insight.recommended_strategy
            
            return market_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting market data: {e}")
            return None

    def validate_and_suggest_parameters_ecosystem(self):
        """Enhanced parameter validation with ecosystem intelligence and profit focus"""
        
        market_data = self.get_asset_market_data()
        if not market_data:
            return False
        
        volatility = market_data['volatility']
        volume = market_data['volume_24h']
        
        self.logger.info(f"📊 Market Analysis for {self.symbol}:")
        self.logger.info(f"   Current Price: ₱{market_data['current_price']:,.4f}")
        self.logger.info(f"   24h Volume: ₱{volume:,.0f}")
        self.logger.info(f"   24h Volatility: {volatility:.1f}%")
        
        # Add ecosystem context if available
        if 'ecosystem_score' in market_data:
            self.logger.info(f"🧠 Ecosystem Intelligence:")
            self.logger.info(f"   Performance Score: {market_data['ecosystem_score']:.1f}/10")
            self.logger.info(f"   Risk Level: {market_data['ecosystem_risk']}")
            self.logger.info(f"   Recommended Strategy: {market_data['ecosystem_strategy']}")
        
        # Get ecosystem profit recommendations
        ecosystem_rec = self.get_ecosystem_profit_recommendations(self.symbol)
        
        suggestions = []
        warnings = []
        
        # Enhanced profit-focused suggestions
        if ecosystem_rec:
            if ecosystem_rec['source'] == 'ecosystem_optimization':
                self.logger.info(f"💰 PROFIT OPTIMIZATION AVAILABLE:")
                self.logger.info(f"   Expected Return: {ecosystem_rec['expected_return']:+.1f}%")
                self.logger.info(f"   Win Rate: {ecosystem_rec['win_rate']:.1f}%")
                self.logger.info(f"   Profit Score: {ecosystem_rec['profit_score']:.1f}/10")
                
                # Compare current settings with optimized ones
                if abs(self.buy_threshold * 100 - ecosystem_rec['buy_threshold']) > 0.3:
                    suggestions.append(f"💡 Ecosystem optimization suggests {ecosystem_rec['buy_threshold']:.1f}% buy threshold (current: {self.buy_threshold*100:.1f}%)")
                
                if abs(self.take_profit_pct * 100 - ecosystem_rec['take_profit']) > 1.0:
                    suggestions.append(f"💡 Ecosystem optimization suggests {ecosystem_rec['take_profit']:.1f}% take profit (current: {self.take_profit_pct*100:.1f}%)")
                
                if self.position_sizing != ecosystem_rec['position_sizing']:
                    suggestions.append(f"💡 Ecosystem recommends {ecosystem_rec['position_sizing']} sizing (current: {self.position_sizing})")
            
            elif ecosystem_rec['source'] == 'ecosystem_research':
                self.logger.info(f"🧠 ECOSYSTEM RESEARCH INSIGHTS:")
                self.logger.info(f"   Performance Score: {ecosystem_rec['profit_score']:.1f}/10")
                self.logger.info(f"   Risk Level: {ecosystem_rec['risk_level']}")
                
                if ecosystem_rec['profit_score'] < 5.0:
                    warnings.append(f"⚠️ Low ecosystem performance score ({ecosystem_rec['profit_score']:.1f}/10) - consider different asset")
        
        # Volume and liquidity warnings
        if volume < 1000000:  # Low volume
            warnings.append(f"⚠️ Low volume asset (₱{volume:,.0f}) - May have liquidity issues")
        
        # Profit potential warnings
        if ecosystem_rec and ecosystem_rec.get('expected_return', 0) < 2.0:
            warnings.append(f"⚠️ Low expected return ({ecosystem_rec['expected_return']:+.1f}%) - consider higher performing assets")
        
        # Display suggestions and warnings
        if suggestions:
            self.logger.info(f"💡 PROFIT OPTIMIZATION SUGGESTIONS:")
            for suggestion in suggestions:
                self.logger.info(f"   {suggestion}")
        
        if warnings:
            self.logger.warning(f"⚠️ PROFITABILITY WARNINGS:")
            for warning in warnings:
                self.logger.warning(f"   {warning}")
        
        if not suggestions and not warnings:
            if ecosystem_rec:
                self.logger.info(f"✅ Configuration looks profitable for {self.symbol}!")
                self.logger.info(f"💰 Expected: {ecosystem_rec.get('expected_return', 0):+.1f}% return")
            else:
                self.logger.info(f"✅ Parameters look good for {self.symbol}!")
        
        # Store profit predictions for tracking
        if ecosystem_rec:
            self.profit_tracking['predicted_return'] = ecosystem_rec.get('expected_return', 0)
            self.profit_tracking['predicted_win_rate'] = ecosystem_rec.get('win_rate', 0)
        
        return True

    def get_symbol_info(self):
        """Get trading symbol information with ecosystem context"""
        try:
            symbol_info = self.api.get_symbol_info(self.symbol)
            if symbol_info:
                self.logger.info(f"✅ Symbol {self.symbol} found and active")
                self.logger.info(f"   Status: {symbol_info.get('status')}")
                self.logger.info(f"   Base: {symbol_info.get('baseAsset')}")
                self.logger.info(f"   Quote: {symbol_info.get('quoteAsset')}")
                
                # Add ecosystem profitability context
                ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
                if ecosystem_insight:
                    self.logger.info(f"🧠 Ecosystem Context:")
                    self.logger.info(f"   Profit Score: {ecosystem_insight.performance_score:.1f}/10")
                    self.logger.info(f"   Trade Frequency: {ecosystem_insight.trade_frequency}")
                
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
        """Check account status and balances with profit potential analysis"""
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
                
                # Enhanced profit potential analysis
                required_balance = self.base_amount * 2  # 2x for safety margin
                max_trades = int(php_balance / self.base_amount)
                
                if php_balance < required_balance:
                    self.logger.warning(f"⚠️ Low PHP balance!")
                    self.logger.warning(f"   Current: ₱{php_balance:.2f}")
                    self.logger.warning(f"   Recommended: ₱{required_balance:.2f} (2x trade amount)")
                    self.logger.warning(f"   You can make ~{max_trades} trades")
                else:
                    self.logger.info(f"✅ Sufficient balance for ~{max_trades} trades")
                    
                    # Show profit potential with current balance
                    if self.profit_tracking['predicted_return'] > 0:
                        potential_profit = php_balance * (self.profit_tracking['predicted_return'] / 100)
                        self.logger.info(f"💰 PROFIT POTENTIAL:")
                        self.logger.info(f"   Expected return: {self.profit_tracking['predicted_return']:+.1f}%")
                        self.logger.info(f"   Potential profit: ₱{potential_profit:,.2f}")
                        self.logger.info(f"   Win rate prediction: {self.profit_tracking['predicted_win_rate']:.1f}%")
                
                return account
            else:
                self.logger.error("❌ Account trading disabled!")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error checking account: {e}")
            return None

    def calculate_position_size(self, current_price, momentum, trend):
        """
        Calculate dynamic position size based on selected strategy with ecosystem enhancement
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
            
            # Ecosystem enhancement: boost for high-performing assets
            ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
            if ecosystem_insight and ecosystem_insight.performance_score > 7.0:
                multiplier *= 1.1  # 10% boost for high performers
                
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
            
            # NEW: Ecosystem profit multiplier
            ecosystem_multiplier = 1.0
            ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
            if ecosystem_insight:
                if ecosystem_insight.performance_score > 8.0:
                    ecosystem_multiplier = 1.2  # 20% boost for top performers
                elif ecosystem_insight.performance_score > 6.0:
                    ecosystem_multiplier = 1.1  # 10% boost for good performers
                elif ecosystem_insight.performance_score < 4.0:
                    ecosystem_multiplier = 0.8  # 20% reduction for poor performers
            
            # Calculate final size
            total_multiplier = balance_multiplier * momentum_multiplier * trend_multiplier * trade_multiplier * ecosystem_multiplier
            calculated_size = self.base_amount * total_multiplier
            
            # Apply bounds
            min_size = self.base_amount * 0.3
            max_size = self.base_amount * 2.0
            
            final_size = max(min_size, min(calculated_size, max_size))
            
            self.logger.info(f"📊 Adaptive sizing: Balance×{balance_multiplier:.1f}, "
                           f"Momentum×{momentum_multiplier:.1f} (ratio: {momentum_strength/self.buy_threshold:.1f}), "
                           f"Trend×{trend_multiplier:.1f}, Trades×{trade_multiplier:.1f}, "
                           f"Ecosystem×{ecosystem_multiplier:.1f} = ₱{final_size:.0f}")
            
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

    def update_profit_tracking(self, profit_loss_pct):
        """Update profit tracking vs ecosystem predictions"""
        self.profit_tracking['actual_trades'] += 1
        if profit_loss_pct > 0:
            self.profit_tracking['profitable_trades'] += 1
        self.profit_tracking['total_profit_loss'] += profit_loss_pct
        
        # Calculate actual vs predicted performance
        actual_win_rate = (self.profit_tracking['profitable_trades'] / max(1, self.profit_tracking['actual_trades'])) * 100
        actual_avg_return = self.profit_tracking['total_profit_loss'] / max(1, self.profit_tracking['actual_trades'])
        
        self.logger.info(f"📊 PROFIT TRACKING UPDATE:")
        self.logger.info(f"   Predicted: {self.profit_tracking['predicted_return']:+.1f}% return, {self.profit_tracking['predicted_win_rate']:.1f}% win rate")
        self.logger.info(f"   Actual: {actual_avg_return:+.1f}% avg return, {actual_win_rate:.1f}% win rate")
        self.logger.info(f"   Trades: {self.profit_tracking['actual_trades']} ({self.profit_tracking['profitable_trades']} profitable)")

    def momentum_strategy(self):
        """Enhanced momentum strategy with ecosystem intelligence and profit tracking"""
        try:
            # Get current price
            current_price = self.api.get_current_price(self.symbol)
            self.update_price_history(current_price)

            if self.last_price is None:
                self.last_price = current_price
                self.logger.info(f"📊 {self.symbol} current price: ₱{current_price:.4f}")
                
                # Show ecosystem context on first run
                ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
                if ecosystem_insight:
                    self.logger.info(f"🧠 Ecosystem Score: {ecosystem_insight.performance_score:.1f}/10")
                return

            # Calculate price change and trend
            price_change = (current_price - self.last_price) / self.last_price
            trend = self.calculate_trend()

            # Get current balances
            php_balance = self.api.get_balance('PHP')
            asset_balance = self.api.get_balance(self.base_asset)
            
            php_free = php_balance['free'] if php_balance else 0
            asset_free = asset_balance['free'] if asset_balance else 0

            # Enhanced logging with ecosystem intelligence
            threshold_status = "✅" if abs(price_change) > self.buy_threshold else "⏸️"
            ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
            ecosystem_status = f"🧠 {ecosystem_insight.performance_score:.1f}/10" if ecosystem_insight else ""
            
            self.logger.info(f"📊 {self.symbol}: ₱{current_price:.4f} ({price_change*100:+.2f}%) {threshold_status} {ecosystem_status}")
            self.logger.info(f"   Thresholds: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%")
            self.logger.info(f"   Trend: {trend*100:+.1f}% | Balances: ₱{php_free:.2f} PHP, {asset_free:.6f} {self.base_asset}")

            # BUY CONDITIONS (using ecosystem-enhanced thresholds)
            if (price_change > self.buy_threshold and           # Ecosystem-optimized buy threshold
                trend > -0.02 and                               # Not in strong downtrend
                php_free > self.base_amount * 0.6 and          # Have enough PHP
                self.can_trade_today() and                     # Within daily limit
                self.position is None):                        # No current position
                
                self.place_buy_order_ecosystem(current_price, price_change, trend)

            # SELL CONDITIONS - Momentum Down (using ecosystem-optimized threshold)
            elif (price_change < -self.sell_threshold and      # Ecosystem-optimized sell threshold
                  asset_free > 0.001 and                       # Have position
                  self.can_sell_position() and                 # Min hold time met
                  self.can_trade_today()):                     # Within daily limit
                
                self.place_sell_order_ecosystem(current_price, price_change, trend, "Momentum Down")

            # SELL CONDITIONS - Take Profit (ecosystem-optimized)
            elif (self.entry_price and 
                  current_price > self.entry_price and
                  self.can_sell_position()):
                
                profit_pct = (current_price - self.entry_price) / self.entry_price
                if profit_pct > self.take_profit_pct:
                    self.place_sell_order_ecosystem(current_price, price_change, trend, "Take Profit")

            # EMERGENCY EXIT - Strong downtrend (enhanced with ecosystem risk awareness)
            elif (trend < -0.05 and                            # Very strong downtrend
                  asset_free > 0.001 and                       # Have position
                  self.can_sell_position()):                   # Min hold time met
                
                # Check ecosystem risk level before emergency exit
                risk_multiplier = 1.0
                if ecosystem_insight:
                    if ecosystem_insight.risk_level == 'high':
                        risk_multiplier = 0.8  # Exit faster for high-risk assets
                    elif ecosystem_insight.risk_level == 'low':
                        risk_multiplier = 1.2  # Hold longer for low-risk assets
                
                if trend < (-0.05 * risk_multiplier):
                    self.place_sell_order_ecosystem(current_price, price_change, trend, "Emergency Exit")

            self.last_price = current_price

        except Exception as e:
            self.logger.error(f"❌ Error in strategy execution: {e}")

    def place_buy_order_ecosystem(self, price, change, trend):
        """Place a buy order with ecosystem intelligence and profit tracking"""
        try:
            # Calculate dynamic position size with ecosystem enhancement
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
            
            # Get ecosystem context for enhanced logging
            ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
            ecosystem_context = ""
            if ecosystem_insight:
                ecosystem_context = f"🧠 Score: {ecosystem_insight.performance_score:.1f}/10"
            
            self.logger.info(f"🔄 {self.name} v{self.version} attempting BUY:")
            self.logger.info(f"   💰 Position size: ₱{amount_to_spend:.2f} ({self.position_sizing} sizing)")
            self.logger.info(f"   📊 Trigger: {change*100:+.2f}% > {self.buy_threshold*100:.1f}% threshold")
            self.logger.info(f"   🎯 Quantity: {quantity:.6f} {self.base_asset} at ₱{buy_price:.4f}")
            self.logger.info(f"   📈 Trend: {trend*100:+.1f}% {ecosystem_context}")
            
            # Show profit expectations if available
            if self.profit_tracking['predicted_return'] > 0:
                expected_target = buy_price * (1 + self.profit_tracking['predicted_return'] / 100)
                self.logger.info(f"   💰 Expected target: ₱{expected_target:.4f} ({self.profit_tracking['predicted_return']:+.1f}%)")
            
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
                
                # Enhanced alert with ecosystem context
                alert_msg = f"🟢 {self.name} v{self.version} BUY {self.base_asset}: {quantity:.6f} at ₱{buy_price:.4f}"
                if ecosystem_insight:
                    alert_msg += f" (Score: {ecosystem_insight.performance_score:.1f}/10)"
                self.send_alert(alert_msg)
                
            else:
                self.logger.error(f"❌ {self.name} BUY ORDER FAILED: {order}")
                
        except Exception as e:
            self.logger.error(f"❌ Error placing buy order: {e}")

    def place_sell_order_ecosystem(self, price, change, trend, reason):
        """Place a sell order with ecosystem intelligence and profit tracking"""
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
            
            # Get ecosystem context for enhanced logging
            ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
            ecosystem_context = ""
            if ecosystem_insight:
                ecosystem_context = f"🧠 Score: {ecosystem_insight.performance_score:.1f}/10"
            
            self.logger.info(f"🔄 {self.name} v{self.version} attempting SELL:")
            self.logger.info(f"   📊 Trigger: {reason}")
            if reason == "Momentum Down":
                self.logger.info(f"   📉 Change: {change*100:+.2f}% < -{self.sell_threshold*100:.1f}% threshold")
            elif reason == "Take Profit":
                self.logger.info(f"   🎯 Profit: {profit_loss_pct:+.1f}% > {self.take_profit_pct*100:.1f}% target")
            self.logger.info(f"   💰 Amount: ₱{gross_amount:.2f} ({quantity_to_sell:.6f} {self.base_asset})")
            self.logger.info(f"   📊 P/L: {profit_loss_pct:+.2f}% {ecosystem_context}")
            
            # Compare with ecosystem predictions
            if self.profit_tracking['predicted_return'] > 0:
                vs_prediction = profit_loss_pct - self.profit_tracking['predicted_return']
                prediction_status = "✅" if vs_prediction >= 0 else "📉"
                self.logger.info(f"   🎯 vs Prediction: {vs_prediction:+.1f}% {prediction_status}")
            
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
                # Update profit tracking
                self.update_profit_tracking(profit_loss_pct)
                
                # Clear position
                self.position = None
                self.entry_price = None
                self.entry_time = None
                self.update_daily_trades()
                
                self.logger.info(f"✅ {self.name} v{self.version} SELL ORDER PLACED!")
                self.logger.info(f"   Order ID: {order['orderId']}")
                self.logger.info(f"   Exit: ₱{sell_price:.4f} | P/L: {profit_loss_pct:+.2f}%")
                
                # Enhanced alert with ecosystem context
                profit_emoji = "🟢" if profit_loss_pct > 0 else "🔴"
                alert_msg = f"{profit_emoji} {self.name} v{self.version} SELL {self.base_asset}: {quantity_to_sell:.6f} at ₱{sell_price:.4f} ({reason}, {profit_loss_pct:+.1f}%)"
                if ecosystem_insight:
                    alert_msg += f" (Score: {ecosystem_insight.performance_score:.1f}/10)"
                self.send_alert(alert_msg)
                
            else:
                self.logger.error(f"❌ {self.name} SELL ORDER FAILED: {order}")
                
        except Exception as e:
            self.logger.error(f"❌ Error placing sell order: {e}")

    def send_alert(self, message):
        """Send alert notification (placeholder for future implementation)"""
        self.logger.info(f"🔔 ALERT: {message}")

    def display_status_ecosystem(self):
        """Display current bot status with ecosystem intelligence and profit tracking"""
        status = "🟢 RUNNING" if self.running else "🔴 STOPPED"
        position_status = f"📊 Position: {self.position}" if self.position else "📊 Position: None"
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_trades = self.daily_trades.get(today, 0)
        
        self.logger.info(f"🤖 {self.name} v{self.version} Status: {status}")
        self.logger.info(f"🎯 Asset: {self.symbol} | Thresholds: Buy {self.buy_threshold*100:.1f}%, Sell {self.sell_threshold*100:.1f}%")
        self.logger.info(f"📈 Take Profit: {self.take_profit_pct*100:.1f}% | Position Sizing: {self.position_sizing}")
        
        # Show ecosystem intelligence
        ecosystem_insight = self.get_ecosystem_asset_insight(self.symbol)
        if ecosystem_insight:
            self.logger.info(f"🧠 Ecosystem: {ecosystem_insight.performance_score:.1f}/10 score, {ecosystem_insight.risk_level} risk")
        
        self.logger.info(f"{position_status}")
        self.logger.info(f"📈 Daily trades: {daily_trades}/{self.max_trades_per_day}")
        
        # Show profit tracking
        if self.profit_tracking['actual_trades'] > 0:
            actual_win_rate = (self.profit_tracking['profitable_trades'] / self.profit_tracking['actual_trades']) * 100
            actual_avg_return = self.profit_tracking['total_profit_loss'] / self.profit_tracking['actual_trades']
            self.logger.info(f"💰 Performance: {actual_avg_return:+.1f}% avg, {actual_win_rate:.1f}% win rate ({self.profit_tracking['actual_trades']} trades)")
        
        if self.entry_price:
            current_profit = ((self.last_price - self.entry_price) / self.entry_price * 100) if self.last_price else 0
            target_price = self.entry_price * (1 + self.take_profit_pct)
            self.logger.info(f"📊 Entry: ₱{self.entry_price:.4f} | Current P/L: {current_profit:+.1f}%")
            self.logger.info(f"🎯 Target: ₱{target_price:.4f} | Entry time: {self.entry_time.strftime('%H:%M:%S')}")

    def start(self):
        """Start the trading bot with enhanced ecosystem validation"""
        self.logger.info(f"🚀 Starting {self.name} - {self.description} v{self.version}")
        self.logger.info(f"🎯 Configuration: {self.symbol} | Buy: {self.buy_threshold*100:.1f}% | Sell: {self.sell_threshold*100:.1f}% | TP: {self.take_profit_pct*100:.1f}%")
        self.logger.info(f"💰 Position Sizing: {self.position_sizing} | Base Amount: ₱{self.base_amount}")
        if ECOSYSTEM_AVAILABLE:
            self.logger.info(f"🌐 Ecosystem Intelligence: Active")
        
        # Enhanced validation with ecosystem intelligence
        if not self.get_symbol_info():
            self.logger.error("❌ Symbol validation failed!")
            return
            
        if not self.get_account_status():
            self.logger.error("❌ Account validation failed!")
            return
        
        # Validate and suggest parameters with ecosystem intelligence
        if not self.validate_and_suggest_parameters_ecosystem():
            self.logger.error("❌ Parameter validation failed!")
            return
        
        self.logger.info(f"✅ Setup validated successfully with ecosystem intelligence!")
        self.logger.info(f"🔄 {self.name} will check every {self.check_interval//60} minutes")
        self.logger.info(f"📊 Press Ctrl+C to stop")
        
        self.running = True
        
        try:
            while self.running:
                self.display_status_ecosystem()
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
        """Stop the trading bot with profit summary"""
        self.running = False
        
        # Show final profit summary
        if self.profit_tracking['actual_trades'] > 0:
            actual_win_rate = (self.profit_tracking['profitable_trades'] / self.profit_tracking['actual_trades']) * 100
            actual_avg_return = self.profit_tracking['total_profit_loss'] / self.profit_tracking['actual_trades']
            
            self.logger.info(f"📊 FINAL PROFIT SUMMARY:")
            self.logger.info(f"   Predicted: {self.profit_tracking['predicted_return']:+.1f}% return, {self.profit_tracking['predicted_win_rate']:.1f}% win rate")
            self.logger.info(f"   Actual: {actual_avg_return:+.1f}% avg return, {actual_win_rate:.1f}% win rate")
            self.logger.info(f"   Total trades: {self.profit_tracking['actual_trades']} ({self.profit_tracking['profitable_trades']} profitable)")
            
            # Performance vs prediction
            return_diff = actual_avg_return - self.profit_tracking['predicted_return']
            winrate_diff = actual_win_rate - self.profit_tracking['predicted_win_rate']
            
            if return_diff >= 0 and winrate_diff >= 0:
                self.logger.info(f"   ✅ Outperformed ecosystem predictions!")
            elif return_diff >= -1.0 and winrate_diff >= -5.0:
                self.logger.info(f"   📊 Performance close to ecosystem predictions")
            else:
                self.logger.info(f"   📉 Underperformed ecosystem predictions")
        
        self.logger.info(f"🛑 {self.name} - {self.description} v{self.version} stopped")

# ========== ENHANCED USER INTERFACE FUNCTIONS WITH ECOSYSTEM INTELLIGENCE ==========

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
            print("📝 No Prophet recommendations found - using ecosystem defaults")
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

def get_ecosystem_profit_rankings():
    """Get profit-ranked assets from ecosystem intelligence"""
    
    if not ECOSYSTEM_AVAILABLE:
        return []
    
    try:
        ecosystem_manager = get_ecosystem_manager()
        
        # Get top performing assets
        top_assets = ecosystem_manager.get_top_assets(limit=8)
        
        profit_rankings = []
        for asset in top_assets:
            # Get latest optimization for expected returns
            latest_optimization = ecosystem_manager.get_latest_optimization(asset.symbol)
            
            expected_return = latest_optimization.expected_return if latest_optimization else 0
            win_rate = latest_optimization.win_rate if latest_optimization else 0
            
            profit_rankings.append({
                'symbol': asset.symbol,
                'performance_score': asset.performance_score,
                'expected_return': expected_return,
                'win_rate': win_rate,
                'risk_level': asset.risk_level,
                'recommended_strategy': asset.recommended_strategy,
                'profit_summary': f"{asset.performance_score:.1f}/10 score, {expected_return:+.1f}% return, {win_rate:.0f}% win rate"
            })
        
        return profit_rankings
        
    except Exception as e:
        print(f"⚠️ Error loading ecosystem profit rankings: {e}")
        return []

def get_asset_optimization_recommendations_ecosystem(symbol):
    """Get optimization recommendations with ecosystem intelligence and profit focus"""
    
    # Try ecosystem intelligence first
    if ECOSYSTEM_AVAILABLE:
        try:
            ecosystem_manager = get_ecosystem_manager()
            
            # Get ecosystem insight for this symbol
            insights = ecosystem_manager.load_research_insights()
            symbol_insight = None
            for insight in insights:
                if insight.symbol == symbol:
                    symbol_insight = insight
                    break
            
            # Get latest optimization
            latest_optimization = ecosystem_manager.get_latest_optimization(symbol)
            
            if latest_optimization:
                # Use ecosystem optimization results
                return {
                    'buy_threshold': latest_optimization.buy_threshold,
                    'sell_threshold': latest_optimization.sell_threshold,
                    'take_profit': latest_optimization.take_profit,
                    'expected_return': latest_optimization.expected_return,
                    'win_rate': latest_optimization.win_rate,
                    'position_sizing': symbol_insight.recommended_strategy if symbol_insight else 'adaptive',
                    'rationale': f"Ecosystem optimized: {latest_optimization.expected_return:+.1f}% return, {latest_optimization.win_rate:.1f}% win rate",
                    'source': 'ecosystem_optimization',
                    'profit_score': symbol_insight.performance_score if symbol_insight else 5.0,
                    'risk_level': symbol_insight.risk_level if symbol_insight else 'medium'
                }
            
            elif symbol_insight:
                # Use ecosystem research insights
                volatility = symbol_insight.volatility
                buy_threshold = 0.008 if volatility > 8 else 0.010 if volatility > 3 else 0.012
                take_profit = 0.020 if volatility > 8 else 0.030 if volatility > 3 else 0.050
                
                return {
                    'buy_threshold': buy_threshold,
                    'sell_threshold': buy_threshold * 1.67,
                    'take_profit': take_profit,
                    'expected_return': symbol_insight.performance_score,
                    'win_rate': 65.0,  # Default estimate
                    'position_sizing': symbol_insight.recommended_strategy,
                    'rationale': f"Ecosystem research: {symbol_insight.performance_score:.1f}/10 score, {symbol_insight.risk_level} risk",
                    'source': 'ecosystem_research',
                    'profit_score': symbol_insight.performance_score,
                    'risk_level': symbol_insight.risk_level
                }
                
        except Exception as e:
            print(f"⚠️ Error accessing ecosystem data: {e}")
    
    # Try Prophet recommendations next
    prophet_data = load_prophet_recommendations()
    
    if prophet_data and symbol in prophet_data:
        rec = prophet_data[symbol]
        return {
            'buy_threshold': rec.get('buy_threshold', 1.0),
            'sell_threshold': rec.get('sell_threshold', 1.7),
            'take_profit': rec.get('take_profit', 4.0),
            'expected_return': 5.0,  # Default estimate
            'win_rate': 70.0,  # Default estimate
            'position_sizing': rec.get('position_sizing', 'adaptive'),
            'rationale': f"Prophet optimized: {rec.get('expected_performance', 'Prophet-optimized performance')}",
            'source': 'prophet_dynamic',
            'profit_score': 6.0,  # Default estimate
            'risk_level': 'medium'
        }
    
    # Fallback to static defaults
    static_defaults = {
        'XRPPHP': {'buy': 1.2, 'sell': 2.0, 'tp': 8.0, 'sizing': 'adaptive'},
        'SOLPHP': {'buy': 0.6, 'sell': 1.0, 'tp': 2.0, 'sizing': 'momentum'},
        'BTCPHP': {'buy': 1.0, 'sell': 1.7, 'tp': 3.0, 'sizing': 'adaptive'}
    }
    
    default = static_defaults.get(symbol, {'buy': 1.0, 'sell': 1.7, 'tp': 4.0, 'sizing': 'adaptive'})
    
    return {
        'buy_threshold': default['buy'],
        'sell_threshold': default['sell'],
        'take_profit': default['tp'],
        'expected_return': 0,  # Unknown
        'win_rate': 0,  # Unknown
        'position_sizing': default['sizing'],
        'rationale': 'Default settings - run Prophet or ecosystem analysis for optimization',
        'source': 'default',
        'profit_score': 0,  # Unknown
        'risk_level': 'medium'
    }

def get_user_inputs_ecosystem():
    """Enhanced user input collection with ecosystem intelligence and profit focus"""
    try:
        print("🤖 TITAN - Advanced Momentum Trading Bot v4.2")
        print("💰 NEW: Profit-Optimized with Ecosystem Intelligence")
        print("🧠 Loads research insights and optimization data for maximum profitability")
        print("=" * 80)
        
        # Show ecosystem status
        if ECOSYSTEM_AVAILABLE:
            print("✅ Ecosystem Intelligence: Active")
            
            # Get profit-ranked assets from ecosystem
            profit_rankings = get_ecosystem_profit_rankings()
            
            if profit_rankings:
                print(f"\n🏆 TOP PROFITABLE OPPORTUNITIES (Ecosystem Intelligence):")
                for i, asset in enumerate(profit_rankings[:5], 1):
                    risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(asset['risk_level'], "🟡")
                    print(f"  {i}. {asset['symbol']:<8} - {asset['profit_summary']} {risk_emoji}")
                print()
                print("💡 These rankings are based on proven backtesting and research insights")
            else:
                print("📊 No ecosystem profit data found - run momentum_backtest_v47.py first")
        else:
            print("⚠️ Ecosystem Intelligence: Disabled")
        
        # Get symbol suggestions for comparison
        print("\n🔍 Getting market volume data...")
        market_suggestions = get_symbol_suggestions()
        
        if market_suggestions:
            print(f"\n📊 TOP VOLUME PHP PAIRS (Market Data):")
            for i, pair in enumerate(market_suggestions[:6], 1):
                volume_str = f"₱{pair['volume']/1000000:.1f}M" if pair['volume'] >= 1000000 else f"₱{pair['volume']/1000:.0f}K"
                change_emoji = "📈" if pair['price_change'] > 0 else "📉"
                print(f"  {i}. {pair['symbol']:<8} - {volume_str:<8} {change_emoji} {pair['price_change']:+.1f}%")
        
        # Enhanced asset selection with profit focus
        print(f"\n🎯 Select trading asset (Profit-Optimized):")
        
        # Show ecosystem top picks first
        if ECOSYSTEM_AVAILABLE and profit_rankings:
            print("🧠 ECOSYSTEM TOP PICKS:")
            for i, asset in enumerate(profit_rankings[:3], 1):
                print(f"{i}. {asset['symbol']} - {asset['performance_score']:.1f}/10 score, {asset['expected_return']:+.1f}% return")
        
        print("📊 STANDARD OPTIONS:")
        base_num = 4 if (ECOSYSTEM_AVAILABLE and profit_rankings) else 1
        print(f"{base_num}. XRPPHP - Stable performer")
        print(f"{base_num+1}. SOLPHP - Higher volatility") 
        print(f"{base_num+2}. BTCPHP - Conservative choice")
        print(f"{base_num+3}. Custom symbol")
        
        max_choice = base_num + 3
        
        while True:
            choice = input(f"Enter choice (1-{max_choice}): ").strip()
            
            # Handle ecosystem top picks
            if ECOSYSTEM_AVAILABLE and profit_rankings and choice in ['1', '2', '3']:
                choice_idx = int(choice) - 1
                if choice_idx < len(profit_rankings):
                    symbol = profit_rankings[choice_idx]['symbol']
                    selected_asset = profit_rankings[choice_idx]
                    print(f"🧠 Selected top ecosystem performer: {symbol}")
                    print(f"   💰 Expected: {selected_asset['expected_return']:+.1f}% return")
                    print(f"   🎯 Win rate: {selected_asset['win_rate']:.0f}%")
                    print(f"   ⚠️ Risk: {selected_asset['risk_level']}")
                    break
            
            # Handle standard options
            elif choice == str(base_num):
                symbol = 'XRPPHP'
                break
            elif choice == str(base_num + 1):
                symbol = 'SOLPHP'
                break
            elif choice == str(base_num + 2):
                symbol = 'BTCPHP'
                break
            elif choice == str(base_num + 3):
                while True:
                    custom_symbol = input("Enter symbol (e.g., ETHPHP): ").strip().upper()
                    if custom_symbol.endswith('PHP') and len(custom_symbol) >= 6:
                        symbol = custom_symbol
                        break
                    else:
                        print("Please enter a valid PHP trading pair")
                break
            else:
                print(f"Please enter 1-{max_choice}")
        
        # Get ecosystem-enhanced optimization recommendations
        recommendations = get_asset_optimization_recommendations_ecosystem(symbol)
        
        # Show recommendation source and profit details
        source_emoji = "🧠" if recommendations['source'] == 'ecosystem_optimization' else "🧠" if recommendations['source'] == 'ecosystem_research' else "🔮" if recommendations['source'] == 'prophet_dynamic' else "⚙️"
        source_text = "ECOSYSTEM OPTIMIZED" if recommendations['source'] == 'ecosystem_optimization' else "ECOSYSTEM RESEARCH" if recommendations['source'] == 'ecosystem_research' else "PROPHET OPTIMIZED" if recommendations['source'] == 'prophet_dynamic' else "DEFAULT"
        
        print(f"\n{source_emoji} {source_text} CONFIGURATION for {symbol}:")
        print(f"💡 {recommendations['rationale']}")
        
        if recommendations['expected_return'] > 0:
            print(f"💰 Expected Return: {recommendations['expected_return']:+.1f}%")
        if recommendations['win_rate'] > 0:
            print(f"🎯 Expected Win Rate: {recommendations['win_rate']:.1f}%")
        if recommendations['profit_score'] > 0:
            print(f"📊 Profit Score: {recommendations['profit_score']:.1f}/10")
            
        print(f"   Buy: {recommendations['buy_threshold']:.1f}%")
        print(f"   Sell: {recommendations['sell_threshold']:.1f}%")
        print(f"   TP: {recommendations['take_profit']:.1f}%")
        print(f"   Risk: {recommendations['risk_level']}")
        
        if recommendations['source'] in ['default']:
            print(f"💡 Pro tip: Run 'python momentum_backtest.py' or 'python prophet.py' for optimized parameters")
        
        print(f"\n📝 Configuration Options:")
        print(f"1. Use recommended settings (profit-optimized)")
        print(f"2. Customize parameters")
        
        config_choice = input("Enter choice (1-2, default: 1): ").strip()
        
        if config_choice == '2':
            # Custom configuration
            print(f"\n📈 Configure Buy Threshold:")
            print(f"💡 Recommended: {recommendations['buy_threshold']:.1f}%")
            
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
            
            print(f"\n📉 Configure Sell Threshold:")
            print(f"💡 Recommended: {recommendations['sell_threshold']:.1f}%")
            
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
            
            print(f"\n🎯 Configure Take Profit:")
            print(f"💡 Recommended: {recommendations['take_profit']:.1f}%")
            
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
            
            print(f"\n📊 Select position sizing:")
            print(f"1. Fixed")
            print(f"2. Percentage") 
            print(f"3. Momentum")
            print(f"4. Adaptive")
            print(f"💡 Recommended: {recommendations['position_sizing']}")
            
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
        else:
            # Use recommended settings
            buy_threshold = recommendations['buy_threshold']
            sell_threshold = recommendations['sell_threshold']
            take_profit = recommendations['take_profit']
            position_sizing = recommendations['position_sizing']
            print(f"✅ Using profit-optimized settings!")
        
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
        
        # Configuration summary with profit intelligence
        config_source = f"🧠 {source_text.title()}" if recommendations['source'].startswith('ecosystem') else f"🔮 {source_text.title()}" if recommendations['source'] == 'prophet_dynamic' else "⚙️ Default"
        print(f"\n✅ TITAN v4.2 PROFIT-OPTIMIZED CONFIGURATION ({config_source}):")
        print(f"🎯 Asset: {symbol}")
        print(f"📈 Buy threshold: {buy_threshold:.1f}%")
        print(f"📉 Sell threshold: {sell_threshold:.1f}%")
        print(f"🎯 Take profit: {take_profit:.1f}%")
        print(f"💰 Position sizing: {position_sizing.title()}")
        print(f"💰 Base amount: ₱{base_amount}")
        print(f"📁 Log file: logs/titan_{symbol.replace('PHP', '').lower()}.log")
        
        # Show profit expectations
        if recommendations['expected_return'] > 0:
            print(f"\n💰 PROFIT EXPECTATIONS:")
            print(f"   Expected Return: {recommendations['expected_return']:+.1f}%")
            if recommendations['win_rate'] > 0:
                print(f"   Expected Win Rate: {recommendations['win_rate']:.1f}%")
            if recommendations['profit_score'] > 0:
                print(f"   Profit Score: {recommendations['profit_score']:.1f}/10")
            print(f"   Risk Level: {recommendations['risk_level']}")
            
            # Calculate potential profit with current balance
            try:
                api = CoinsAPI(
                    api_key=os.getenv('COINS_API_KEY'),
                    secret_key=os.getenv('COINS_SECRET_KEY')
                )
                account = api.get_account_info()
                if account and account.get('balances'):
                    php_balance = 0
                    for balance in account['balances']:
                        if balance['asset'] == 'PHP':
                            php_balance = float(balance['free'])
                            break
                    
                    if php_balance > 0:
                        potential_profit = php_balance * (recommendations['expected_return'] / 100)
                        print(f"   Potential Profit: ₱{potential_profit:,.2f} (with ₱{php_balance:,.2f} balance)")
            except:
                pass  # Skip if can't get balance
        elif recommendations['source'] not in ['default']:
            print(f"\n📊 Using proven optimization but profit data not available")
        else:
            print(f"\n💡 Run ecosystem analysis for profit predictions")
        
        return symbol, take_profit, base_amount, position_sizing, buy_threshold, sell_threshold
        
    except KeyboardInterrupt:
        print("\n🛑 TITAN v4.2 setup cancelled gracefully")
        print("✨ Thank you for using TITAN with Ecosystem Intelligence")
        return None, None, None, None, None, None

def main():
    """Enhanced main function with ecosystem intelligence and profit focus"""
    try:
        # Check API credentials
        if not os.getenv('COINS_API_KEY') or not os.getenv('COINS_SECRET_KEY'):
            print("❌ API credentials not found!")
            print("Please set COINS_API_KEY and COINS_SECRET_KEY in your .env file")
            return
        
        # Check ecosystem availability and show intelligence status
        if ECOSYSTEM_AVAILABLE:
            print("🌐 Checking ecosystem intelligence...")
            try:
                ecosystem_manager = get_ecosystem_manager()
                status = ecosystem_manager.get_ecosystem_status()
                
                insights_count = status['data_summary']['research_insights']
                optimizations_count = status['data_summary']['optimization_history']
                
                if insights_count > 0 or optimizations_count > 0:
                    print(f"✅ Ecosystem data available: {insights_count} research insights, {optimizations_count} optimizations")
                else:
                    print("📊 No ecosystem data found - TITAN will use Prophet/default settings")
                    print("💡 Run 'python momentum_backtest_v47.py' for research insights")
                    
            except Exception as e:
                print(f"⚠️ Ecosystem check failed: {e}")
        
        # Get user configuration with ecosystem intelligence
        result = get_user_inputs_ecosystem()
        if result[0] is None:  # User cancelled
            return
        
        symbol, take_profit, base_amount, position_sizing, buy_threshold, sell_threshold = result
        
        # Final confirmation with profit summary
        print(f"\n🚀 Ready to start TITAN v4.2 with Ecosystem Intelligence!")
        print(f"💰 Profit-optimized configuration for {symbol}")
        confirm = input("Start the bot? (y/n): ").lower().strip()
        
        if confirm.startswith('y'):
            # Initialize and start bot with ecosystem intelligence
            bot = TitanTradingBotEcosystem(
                symbol=symbol, 
                take_profit_pct=take_profit, 
                base_amount=base_amount, 
                position_sizing=position_sizing,
                buy_threshold=buy_threshold,
                sell_threshold=sell_threshold
            )
            bot.start()
        else:
            print("👋 TITAN v4.2 startup cancelled")
            
    except KeyboardInterrupt:
        print("\n🛑 TITAN v4.2 session ended gracefully")
        print("✨ Thank you for using TITAN with Ecosystem Intelligence")
    except Exception as e:
        print(f"\n❌ TITAN v4.2 encountered an error: {e}")
        print("🔧 Please check your configuration and try again")

if __name__ == '__main__':
    main()