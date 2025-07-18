# 🤖 Crypto Trading Bots for Coins.ph

**Automated trading systems featuring momentum analysis, AI integration, and comprehensive risk management.**

---

## 🌟 Meet the Bots

### 🤖 **TITAN** - Advanced Momentum Trading Bot v4.0
**Pure momentum-based trading with fully configurable thresholds and optimization-driven recommendations**
- ✅ **NEW: Configurable Buy/Sell Thresholds** - No code changes needed, set at startup
- ✅ **Optimization-Driven Recommendations** - Backtesting discoveries integrated into setup
- ✅ **Asset-Specific Parameter Suggestions** - Smart defaults based on volatility analysis
- ✅ **Real-time Parameter Validation** - Market data analysis with live optimization suggestions
- ✅ **4 Position Sizing Strategies** - Fixed, Percentage, Momentum, and Adaptive sizing
- ✅ **Enhanced Setup Wizard** - Comprehensive configuration with performance predictions
- ✅ **Dynamic Risk Management** - Smart position adjustments based on market conditions
- ✅ **Multi-asset support** with optimized parameters for each pair
- ✅ **Comprehensive backtesting** integration with live parameter feedback

### 🔮 **ORACLE** - AI-Enhanced Trading Bot v4.0
**AI-powered trading with MarketRaker integration and currency conversion**
- ✅ **MarketRaker AI signal processing** with webhook integration
- ✅ **Real-time USD/PHP conversion** with smart caching
- ✅ **AI + Momentum confirmation** for enhanced accuracy
- ✅ **Smart price level validation** with tolerance checking
- ✅ **Risk-based position sizing** based on AI confidence
- ✅ **FastAPI webhook server** with comprehensive monitoring
- ✅ **Test mode safety** for development and validation

---

## 📂 Repository Structure

### **🤖 Trading Bots**
- `titan.py` - **TITAN** momentum trading bot with dynamic position sizing
- `oracle.py` - **ORACLE** AI-enhanced trading bot with MarketRaker integration

### **🔧 Core Infrastructure**
- `coinsph_api_v2.py` - Enhanced API wrapper with improved signature handling
- `momentum_backtest_v45.py` - **NEW:** Multi-asset backtesting with TITAN position sizing
- `take_profit_optimizer.py` - **ENHANCED:** All PHP pairs support with asset-specific optimization

### **📊 Analysis & Utilities**
- `check_volumes.py` - Trading volume analysis and pair recommendations
- `toggle_oracle_mode.py` - Quick ORACLE test/live mode switcher
- `test_connection.py` - API connectivity and trading permissions validator
- `test_exchange_rates.py` - USD/PHP exchange rate API testing

### **🔐 Configuration**
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules
- `README.md` - This comprehensive guide

---

## ⚙️ Prerequisites

- **Python ≥ 3.8**
- **Coins.ph Pro account** with API access
- **₱500+ balance** recommended for safe trading
- **API permissions**: Trading enabled, IP whitelisted
- **MarketRaker account** (optional, for ORACLE AI signals)

---

## 🚀 Quick Start

### 1. **Setup Environment**
```bash
git clone https://github.com/ccc1236/coinsph-trading-bot.git
cd coinsph-trading-bot

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configure API Credentials**
```bash
cp .env.example .env
# Edit .env and add your credentials:
COINS_API_KEY=your_api_key_here
COINS_SECRET_KEY=your_secret_key_here
# MARKETRAKER_VERIFICATION_KEY=your_key_here  # Optional for ORACLE
```

### 3. **Validate Setup**
```bash
python test_connection.py
```

### 4. **Choose Your Bot**

#### **🤖 Start TITAN (Momentum Bot)**
```bash
python titan.py
```
- Interactive setup wizard with intelligent recommendations
- Choose from 4 position sizing strategies
- Configurable take profit levels based on backtesting
- Asset-specific risk analysis

#### **🔮 Start ORACLE (AI Bot)**
```bash
python oracle.py
```
- Webhook server for AI signals
- Test mode enabled by default
- Advanced monitoring dashboard

---

## 🤖 TITAN - Advanced Momentum Trading Bot v4.0

### **🎯 NEW in v4.0: Fully Configurable Trading Thresholds**
TITAN v4.0 introduces revolutionary configurability - no more hardcoded parameters!

#### **🔧 Configurable at Startup:**
- **Buy Threshold**: 0.5% - 5.0% (no more fixed 0.6%)
- **Sell Threshold**: 0.8% - 4.0% (no more fixed 1.0%) 
- **Take Profit**: 0.5% - 15.0% with asset-specific recommendations
- **Position Sizing**: All 4 strategies with smart suggestions

#### **🎯 Optimization-Driven Recommendations:**
Based on comprehensive backtesting discoveries:

**XRPPHP Optimization Discovery:**
- **Recommended**: 1.2% buy threshold (vs old 0.6%)
- **Performance**: +1.6% return improvement in backtesting
- **Take Profit**: 5.0% optimal for this pair
- **Evidence**: "1.2% buy threshold showed +1.6% return in backtesting"

**Asset-Specific Intelligence:**
- **High Volatility** (SOL): Lower thresholds (0.8%-1.3%)
- **Medium Volatility** (XRP): Balanced thresholds (1.0%-2.0%)
- **Low Volatility** (BTC): Higher thresholds (1.5%-2.5%)

### **🎮 Enhanced Interactive Setup Wizard**
TITAN v4.0 features the most advanced configuration system:

1. **Market Data Analysis**: Real-time volatility assessment
2. **Parameter Recommendations**: Based on backtesting discoveries
3. **Performance Predictions**: Expected returns for your configuration
4. **Optimization Validation**: Live parameter analysis with suggestions
5. **Asset-Specific Defaults**: Smart suggestions per trading pair

### **📊 Smart Parameter Validation**
Real-time analysis provides live feedback:
```
📊 Market Analysis for XRPPHP:
   24h Volatility: 3.2%
💡 XRPPHP Optimization: 1.2% buy threshold showed +1.6% return
🎯 Recommended: 5.0% take profit was optimal in backtesting
✅ Parameters look good for XRPPHP!
```

### **🚀 Starting TITAN v4.0**
```bash
python titan.py
```

**Revolutionary Interactive Setup:**
1. **Asset Selection** with volume analysis and recommendations
2. **Threshold Configuration** with optimization-based suggestions
3. **Parameter Validation** with real-time market analysis
4. **Performance Prediction** showing expected results
5. **Smart Defaults** based on backtesting discoveries

**Sample v4.0 Configuration:**
```
🎯 Asset: XRPPHP
📈 Buy threshold: 1.2% (optimized - was 0.6% in v3.3)
📉 Sell threshold: 2.0% (optimized - was 1.0% in v3.3)
🎯 Take profit: 5.0% (backtested optimal for XRPPHP)
📊 Position sizing: Adaptive
💰 Base amount: ₱300
📊 Expected: +1.6% return improvement vs old parameters
```

---

## 🔮 ORACLE - AI-Enhanced Trading Bot

### **🎯 Core Features**
- **MarketRaker Integration**: Real-time AI signal processing
- **USD/PHP Conversion**: Automatic currency conversion with caching
- **AI + Momentum Fusion**: Dual confirmation system
- **Price Level Validation**: 3% tolerance for AI entry points
- **Risk-Based Sizing**: Position size scales with AI confidence
- **Comprehensive Monitoring**: FastAPI dashboard with real-time status

### **🌐 Webhook Endpoints**
```
http://localhost:8000/              # Bot status
http://localhost:8000/health        # Health check
http://localhost:8000/status        # Comprehensive status
http://localhost:8000/exchange-rate # USD/PHP rate info
```

### **📡 Signal Processing**
- **Live Signals**: `/webhook/marketraker` (with signature verification)
- **Test Signals**: `/webhook/test` (for development)
- **Toggle Mode**: `/toggle-test-mode` (switch test/live)

### **🧪 Test Mode Features**
- **Safe Development**: No real trades placed
- **Signal Simulation**: Full analysis without execution
- **Comprehensive Logging**: Detailed decision reasoning

### **🚀 Starting ORACLE**
```bash
python oracle.py
```

**AI Signal Integration:**
1. ORACLE starts in test mode (safe)
2. Send test signals via `/webhook/test`
3. Monitor decisions and analysis
4. Toggle to live mode when ready

---

## 📊 Strategy Optimization

### **Enhanced Take Profit Optimizer (All PHP Pairs)**
```bash
python take_profit_optimizer.py
```

**NEW Features:**
- **All PHP Pairs Support**: Test any PHP trading pair (72+ pairs supported)
- **Asset-Specific Optimization**: Volatility-based parameter ranges
- **Smart Recommendations**: Based on 24h market data analysis
- **TITAN Integration**: Results ready for TITAN v4.0 configuration

**Enhanced Analysis:**
- Tests 10-14 take profit levels per asset (optimized ranges)
- Asset-specific volatility analysis and parameter suggestions
- Volume-based pair recommendations
- Real-time market data integration
- TITAN v4.0 configuration export

**Sample Enhanced Results:**
- **XRPPHP**: 5.0% take profit → +1.5% return, 65% win rate ✅ **OPTIMAL**
- **SOLPHP**: 1.8% take profit → -1.3% return, 58% win rate
- **ETHPHP**: 3.5% take profit → +0.8% return, 62% win rate

### **Enhanced Momentum Backtester v45 (Multi-Asset)**
```bash
python momentum_backtest_v45.py
```

**NEW Features:**
- **Multi-Asset Support**: Test all 72 PHP pairs automatically
- **TITAN Position Sizing Integration**: Test all 4 strategies
- **Asset-Specific Parameters**: Volatility-based optimization ranges
- **Strategy Comparison**: Compare performance across assets
- **Bot Configuration Export**: Generate TITAN/ORACLE ready configs

**Enhanced Analysis:**
- Comprehensive multi-asset testing
- Position sizing strategy comparison
- Asset volatility categorization
- Parameter optimization for each asset
- Performance benchmarking across pairs

### **Volume Analysis**
```bash
python check_volumes.py
```
- Top trading pairs by 24hr volume
- PHP pair rankings and liquidity analysis
- Optimal pair recommendations

---

## 🔬 Testing & Validation

### **API Connection Testing**
```bash
python test_connection.py
```
- Validates API credentials and permissions
- Checks account balances and trading limits
- Verifies symbol availability

### **Exchange Rate Testing (for ORACLE)**
```bash
python test_exchange_rates.py
```
- Tests USD/PHP conversion APIs
- Validates fallback mechanisms
- Price level analysis simulation

---

## 📈 Performance Monitoring

### **Real-time Monitoring**
Both bots provide comprehensive logging:
- **Live price tracking** with momentum analysis
- **Position management** with P/L tracking
- **Trade execution logs** with detailed reasoning
- **Daily trade counters** and limits
- **Performance metrics** vs buy & hold

### **TITAN v4.0 Monitoring**
- Console output with 15-minute updates and threshold analysis
- Asset-specific log files: `logs/titan_v4_xrp.log`, `logs/titan_v4_sol.log`
- **Enhanced logging**: Parameter decisions, optimization suggestions, threshold triggers
- **Real-time validation**: Market analysis and parameter recommendations
- **Performance tracking**: Configurable threshold effectiveness analysis

### **ORACLE Monitoring**
- FastAPI dashboard at `http://localhost:8000`
- Webhook processing logs
- AI signal analysis and decisions
- Log file: `oracle.log`

---

## 🛡️ Risk Management

### **TITAN v4.0 Risk Features**
- **Configurable Thresholds**: Fully customizable buy/sell triggers (0.5%-5.0%)
- **Optimization-Based Defaults**: Smart suggestions based on backtesting discoveries
- **Real-time Parameter Validation**: Market analysis with live optimization suggestions
- **Asset-Specific Risk Management**: Tailored parameters per trading pair
- **4 Dynamic Position Sizing Strategies**: From conservative to aggressive
- **Advanced Setup Wizard**: Pre-trading parameter analysis and validation
- **Take Profit**: Fully configurable (0.5% - 15.0%) with asset-specific recommendations
- **Emergency Exit**: Strong downtrend protection (-5% trend)
- **Position Limits**: Maximum 10 trades per day
- **Hold Time**: 30-minute minimum position duration

### **ORACLE Risk Features**
- **AI Risk Filtering**: Rejects signals with risk > 8/10
- **Price Validation**: 3% tolerance for AI entry points
- **Position Sizing**: Risk-adjusted amounts (30% - 100% of base)
- **Momentum Confirmation**: Dual AI + technical validation
- **Stop Loss**: AI-calculated stop loss levels

---

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Required for both bots
COINS_API_KEY=your_coins_api_key
COINS_SECRET_KEY=your_coins_secret_key

# Optional for ORACLE AI signals
MARKETRAKER_VERIFICATION_KEY=your_verification_key
```

### **TITAN v4.0 Configuration**
Revolutionary configurability - no code changes needed:

```python
# All parameters now configurable at startup via setup wizard:
buy_threshold             # 0.5% - 5.0% (was fixed 0.6%)
sell_threshold           # 0.8% - 4.0% (was fixed 1.0%)
take_profit_pct         # 0.5% - 15.0% (asset-specific suggestions)
base_amount             # ₱50 - ₱2000 reference amount
position_sizing         # fixed, percentage, momentum, adaptive

# Core strategy parameters (optimized and stable):
min_hold_hours = 0.5       # 30 minutes minimum hold
max_trades_per_day = 10    # Daily safety limit
check_interval = 900       # 15 minutes between checks

# NEW: Asset-specific recommendations based on backtesting:
# XRPPHP: 1.2% buy, 2.0% sell, 5.0% TP (optimized)
# SOLPHP: 0.8% buy, 1.3% sell, 2.0% TP (high volatility)
# BTCPHP: 1.5% buy, 2.5% sell, 3.0% TP (low volatility)
```

### **ORACLE Configuration**
```python
# AI-enhanced parameters
momentum_buy_threshold = 0.006    # 0.6% momentum confirmation
price_tolerance = 3.0             # 3% AI entry tolerance
base_amount = 200                 # ₱200 base position
max_trades_per_day = 15          # Higher limit for AI signals
```

---

## 🆚 Bot Comparison

| Feature | 🤖 TITAN v4.0 | 🔮 ORACLE |
|---------|----------|-----------|
| **Strategy** | Pure Momentum | AI + Momentum |
| **Signals** | Technical Analysis | MarketRaker AI |
| **Thresholds** | ✅ **Fully Configurable** | Fixed |
| **Setup** | ✅ **Optimization Wizard** | Webhook Configuration |
| **Recommendations** | ✅ **Backtesting-Based** | AI Risk-Based |
| **Position Sizing** | 4 Dynamic Strategies | AI Risk-Based |
| **Take Profit** | ✅ **0.5%-15% Configurable** | AI-Calculated |
| **Parameter Validation** | ✅ **Real-time Analysis** | AI Risk Scoring |
| **Asset Optimization** | ✅ **Per-Pair Suggestions** | Universal |
| **Configuration** | ✅ **No Code Changes** | FastAPI Dashboard |
| **Monitoring** | Enhanced Threshold Logs | Real-time Dashboard |
| **Best For** | ✅ **Optimized momentum trading** | AI-guided precision |
| **Complexity** | ✅ **Smart & Fully Configurable** | Advanced & Intelligent |

---

## 🔄 Switching Between Bots

You can run both bots simultaneously:

```bash
# Terminal 1: TITAN
python titan.py

# Terminal 2: ORACLE  
python oracle.py
```

**Recommended Usage:**
- **TITAN v4.0**: Optimized momentum trading with configurable thresholds
- **ORACLE**: AI signal trading on multiple pairs
- **Both**: Diversified strategy with TITAN handling momentum and ORACLE handling AI signals

---

## ⚠️ IMPORTANT LEGAL DISCLAIMER

### **🚨 NOT FINANCIAL ADVICE**
**These trading bots are provided for EDUCATIONAL and RESEARCH purposes ONLY.**

- This is **NOT financial advice, investment advice, or trading advice**
- The authors are **NOT licensed financial advisors**
- All trading strategies are experimental and **high-risk**
- **Consult qualified financial professionals** before trading

### **💸 NO LIABILITY FOR LOSSES**
**BY USING THIS SOFTWARE, YOU ACKNOWLEDGE:**

- **You use this software entirely AT YOUR OWN RISK**
- Authors are **NOT LIABLE** for any financial losses
- **Cryptocurrency trading can result in TOTAL LOSS**
- **Only trade with money you can afford to LOSE COMPLETELY**

### **🛡️ Risk Factors**
- **Market Risk**: Highly volatile and unpredictable markets
- **Technical Risk**: Software bugs, API failures, connectivity issues
- **Strategy Risk**: Algorithms may perform poorly in changing conditions
- **AI Risk**: AI signals may be incorrect or misleading
- **Position Sizing Risk**: Dynamic sizing may increase exposure

**⚠️ TRADE RESPONSIBLY - NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE ⚠️**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional position sizing strategies for TITAN
- Enhanced AI signal processing for ORACLE
- Multi-timeframe analysis
- Portfolio management features
- Telegram/Slack notifications
- Advanced backtesting features

---

## 📄 License

This project is open source. Use responsibly and at your own risk.

---

## 📞 Support

- **Issues**: Create GitHub issues for bugs or feature requests
- **API Problems**: Contact Coins.ph support for API-related issues
- **Strategy Questions**: Review backtest results and optimization tools
- **AI Integration**: Check MarketRaker documentation for signal formats

---

## 🚀 Getting Started Checklist

- [ ] ✅ **Setup Environment** (Python 3.8+, dependencies)
- [ ] ✅ **Configure API Keys** (Coins.ph credentials)
- [ ] ✅ **Validate Connection** (`python test_connection.py`)
- [ ] ✅ **Choose Your Bot** (TITAN for momentum, ORACLE for AI)
- [ ] ✅ **Configure TITAN v4.0** (Revolutionary setup wizard with configurable thresholds)
- [ ] ✅ **Optimize Parameters** (Use enhanced backtesting tools for your chosen pairs)
- [ ] ✅ **Start with Recommended Settings** (Use backtesting-proven configurations)
- [ ] ✅ **Monitor Enhanced Logs** (Check threshold analysis and optimization suggestions)

**Happy Trading with TITAN v3.3 and ORACLE! 🤖🔮📈**