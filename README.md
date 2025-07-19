# 🤖 Crypto Trading Bots for Coins.ph

**Automated trading systems featuring momentum analysis, AI integration, and comprehensive risk management.**

---

## 🌟 Meet the Bots

### 🤖 **TITAN** - Advanced Momentum Trading Bot
**Pure momentum-based trading with fully configurable thresholds and optimization-driven recommendations**
- ✅ **Configurable Buy/Sell Thresholds** - No code changes needed, set at startup
- ✅ **Optimization-Driven Recommendations** - Backtesting discoveries integrated into setup
- ✅ **Asset-Specific Parameter Suggestions** - Smart defaults based on volatility analysis
- ✅ **Real-time Parameter Validation** - Market data analysis with live optimization suggestions
- ✅ **4 Position Sizing Strategies** - Fixed, Percentage, Momentum, and Adaptive sizing
- ✅ **Enhanced Setup Wizard** - Comprehensive configuration with performance predictions
- ✅ **Dynamic Risk Management** - Smart position adjustments based on market conditions
- ✅ **Multi-asset support** with optimized parameters for each pair
- ✅ **Comprehensive backtesting** integration with live parameter feedback

### 🔮 **ORACLE** - AI-Enhanced Trading Bot
**AI-powered trading with advanced position sizing and intelligent signal assessment**
- ✅ **6 Advanced Position Sizing Strategies** - AI-specific intelligent sizing
- ✅ **Signal Quality Assessment Matrix** - Multi-dimensional signal evaluation
- ✅ **Market Volatility Adaptation** - Dynamic sizing for market conditions
- ✅ **Portfolio Balance Scaling** - Position size grows with account
- ✅ **Risk-Reward Optimization** - Size based on AI target/stop ratios
- ✅ **Adaptive AI Strategy** - Most advanced multi-factor sizing (recommended)
- ✅ **Real-time Performance Tracking** - Position sizing effectiveness analytics
- ✅ **Enhanced Position Monitoring** - Quality-based exit strategies
- ✅ **MarketRaker AI signal processing** with webhook integration
- ✅ **Real-time USD/PHP conversion** with smart caching
- ✅ **AI + Momentum confirmation** for enhanced accuracy
- ✅ **Smart price level validation** with tolerance checking
- ✅ **FastAPI webhook server** with comprehensive monitoring
- ✅ **Test mode safety** for development and validation

---

## 📂 Repository Structure

### **🤖 Trading Bots**
- `titan.py` - **TITAN** momentum trading bot with dynamic position sizing
- `oracle.py` - **ORACLE** AI-enhanced trading bot with advanced position sizing

### **🔧 Core Infrastructure**
- `coinsph_api_v2.py` - Enhanced API wrapper with improved signature handling
- `momentum_backtest.py` - Multi-asset backtesting with TITAN position sizing
- `prophet.py` - Enhanced parameter optimization with ecosystem integration

### **📊 Analysis & Utilities**
- `check_volumes.py` - Trading volume analysis and pair recommendations
- `toggle_oracle_mode.py` - Quick ORACLE test/live mode switcher
- `test_connection.py` - API connectivity and trading permissions validator
- `test_exchange_rates.py` - USD/PHP exchange rate API testing
- `ecosystem_manager.py` - Cross-tool data sharing and optimization

### **🔐 Configuration**
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules
- `README.md` - This comprehensive guide

---

## 🚀 Workflow: From Setup to Trading

### **Step 1: Initial Setup**
```bash
git clone https://github.com/ccc1236/coinsph-trading-bot.git
cd coinsph-trading-bot

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure API credentials
cp .env.example .env
# Edit .env and add your Coins.ph API credentials
```

### **Step 2: Validate Setup**
```bash
python test_connection.py
```
This validates your API credentials and checks account permissions.

### **Step 3: Choose Your Trading Approach**

#### **🎯 Option A: Quick Start (Default Parameters)**
```bash
python titan.py
```
Start TITAN with built-in defaults. Good for immediate trading with proven settings.

#### **🔬 Option B: Research-Driven Approach (Recommended)**
For optimal performance, follow this research workflow:

**1. Market Research & Asset Analysis**
```bash
python momentum_backtest.py
```
- Analyzes multiple assets over 30-60 day periods
- Generates performance rankings and insights
- **Produces:** `ecosystem_data/research_insights.json` with asset performance scores
- **Creates:** Cross-asset volatility analysis and risk assessments

**2. Parameter Optimization**
```bash
python prophet.py
```
- Loads research insights from Step 1
- Suggests top-performing assets based on analysis
- Tests thousands of parameter combinations
- **Produces:** `prophet_reco.json` with optimized buy/sell/take-profit thresholds
- **Creates:** Performance predictions and win rate estimates

**3. Live Trading with Optimized Settings**
```bash
python titan.py
```
- Automatically detects and loads Prophet's recommendations
- Shows expected performance based on backtesting
- Uses research-driven asset suggestions
- Applies ecosystem intelligence for parameter validation

### **Step 4: AI Trading (Optional)**
```bash
python oracle.py
```
For AI-powered trading with MarketRaker signal integration.

---

## 📊 How the Ecosystem Works

### **Data Flow Between Tools**

```
momentum_backtest.py → research_insights.json → prophet.py → prophet_reco.json → titan.py
     ↓                                           ↓                              ↓
Asset Analysis                          Parameter Optimization              Live Trading
Risk Assessment                         Performance Prediction              Profit Tracking
Volatility Study                        Backtesting Validation             Parameter Loading
```

### **What Each Tool Produces**

#### **🔬 Momentum Backtest Output:**
- `ecosystem_data/research_insights.json` - Asset performance rankings (0-10 scores)
- `ecosystem_data/optimization_history.json` - Historical optimization results
- **Used by:** Prophet for smart asset suggestions and parameter ranges

#### **🔮 Prophet Output:**
- `prophet_reco.json` - Optimized parameters for specific assets
- Contains: Buy thresholds, sell thresholds, take profit levels, expected returns
- **Used by:** TITAN for automatic parameter loading and performance predictions

#### **🤖 TITAN Integration:**
- Automatically loads Prophet recommendations when available
- Shows expected performance vs actual during trading
- Logs to asset-specific files: `logs/titan_btc.log`, `logs/titan_xrp.log`, etc.
- Tracks profit performance against ecosystem predictions

---

## ⚙️ Prerequisites

- **Python ≥ 3.8**
- **Coins.ph Pro account** with API access
- **₱500+ balance** recommended for safe trading
- **API permissions**: Trading enabled, IP whitelisted
- **MarketRaker account** (optional, for ORACLE AI signals)

---

## 🤖 TITAN - Advanced Momentum Trading Bot

### **🎯 Fully Configurable Trading Thresholds**
TITAN features revolutionary configurability - no more hardcoded parameters!

#### **🔧 Configurable at Startup:**
- **Buy Threshold**: 0.5% - 5.0% (ecosystem-optimized suggestions)
- **Sell Threshold**: 0.8% - 4.0% (automatically calculated from buy threshold)
- **Take Profit**: 0.5% - 15.0% with asset-specific recommendations
- **Position Sizing**: All 4 strategies with smart suggestions

#### **🎯 Optimization-Driven Recommendations:**
Based on comprehensive backtesting discoveries:

**Example XRPPHP Optimization:**
- **Recommended**: 1.2% buy threshold (vs old 0.6%)
- **Performance**: +1.6% return improvement in backtesting
- **Take Profit**: 5.0% optimal for this pair
- **Evidence**: "1.2% buy threshold showed +1.6% return in backtesting"

**Asset-Specific Intelligence:**
- **High Volatility** (SOL): Lower thresholds (0.8%-1.3%)
- **Medium Volatility** (XRP): Balanced thresholds (1.0%-2.0%)
- **Low Volatility** (BTC): Higher thresholds (1.5%-2.5%)

### **🚀 Starting TITAN**
```bash
python titan.py
```

**Interactive Setup Features:**
1. **Asset Selection** with ecosystem performance rankings
2. **Threshold Configuration** with optimization-based suggestions
3. **Parameter Validation** with real-time market analysis
4. **Performance Prediction** showing expected results
5. **Smart Defaults** based on backtesting discoveries

### **📊 Risk Management Features**
- **Configurable Thresholds**: Fully customizable buy/sell triggers (0.5%-5.0%)
- **Optimization-Based Defaults**: Smart suggestions based on backtesting discoveries
- **Real-time Parameter Validation**: Market analysis with live optimization suggestions
- **Asset-Specific Risk Management**: Tailored parameters per trading pair
- **4 Dynamic Position Sizing Strategies**: From conservative to aggressive
- **Take Profit**: Fully configurable (0.5% - 15.0%) with asset-specific recommendations
- **Emergency Exit**: Strong downtrend protection (-5% trend)
- **Position Limits**: Maximum 10 trades per day
- **Hold Time**: 30-minute minimum position duration

---

## 🔮 ORACLE - AI-Enhanced Trading Bot

### **🎯 Advanced AI-Specific Position Sizing**
Revolutionary position sizing system designed specifically for AI trading signals.

#### **📊 6 Intelligent Position Sizing Strategies:**

1. **🎯 AI Confidence Sizing** - Scale position with AI signal strength
2. **📊 Volatility Adaptive Sizing** - Adjust position size for market volatility
3. **🎪 Signal Quality Matrix Sizing** - Multi-factor signal assessment
4. **💰 Portfolio Scaling Sizing** - Position size grows with account balance
5. **⚖️ Risk-Reward Optimization** - Size based on AI target/stop ratios
6. **🧠 Adaptive AI Sizing (Recommended)** - Advanced multi-factor intelligent sizing

#### **🔬 Signal Quality Assessment System**
ORACLE evaluates every AI signal across multiple dimensions:
- **AI Confidence**: Based on risk level and expected change
- **Risk-Reward Ratio**: Target vs stop loss distance
- **Market Alignment**: How close current price is to AI entry
- **Volatility Factor**: Market stability assessment
- **Overall Quality Score**: Combined 0.0-1.0 rating

### **🌐 Webhook Endpoints**
```
http://localhost:8000/                           # Bot status
http://localhost:8000/health                     # Health check
http://localhost:8000/status                     # Comprehensive status
http://localhost:8000/exchange-rate              # USD/PHP rate info
http://localhost:8000/position-sizing-performance # Sizing analytics
```

### **🚀 Starting ORACLE**
```bash
python oracle.py
```

**Enhanced Interactive Setup:**
1. **Base Amount Configuration**: ₱100-₱1000 reference amount
2. **Position Sizing Strategy Selection**: Choose from 6 advanced strategies
3. **Strategy Explanation**: Detailed description of each approach
4. **Risk Assessment**: Risk level and complexity indicators
5. **Performance Expectations**: Expected position size ranges

---

## 📈 Strategy Optimization

### **Enhanced Parameter Optimizer (Prophet)**
```bash
python prophet.py
```

**Features:**
- **All PHP Pairs Support**: Test any PHP trading pair (72+ pairs supported)
- **Asset-Specific Optimization**: Volatility-based parameter ranges
- **Smart Recommendations**: Based on ecosystem research insights
- **TITAN Integration**: Results ready for TITAN configuration

### **Multi-Asset Backtester**
```bash
python momentum_backtest.py
```

**Features:**
- **Multi-Asset Support**: Test all 72 PHP pairs automatically
- **TITAN Position Sizing Integration**: Test all 4 strategies
- **Asset-Specific Parameters**: Volatility-based optimization ranges
- **Strategy Comparison**: Compare performance across assets
- **Bot Configuration Export**: Generate TITAN/ORACLE ready configs

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

### **TITAN Monitoring**
- Console output with 15-minute updates and threshold analysis
- Asset-specific log files: `logs/titan_xrp.log`, `logs/titan_sol.log`
- **Enhanced logging**: Parameter decisions, optimization suggestions, threshold triggers
- **Real-time validation**: Market analysis and parameter recommendations
- **Performance tracking**: Configurable threshold effectiveness analysis

### **ORACLE Monitoring**
- FastAPI dashboard at `http://localhost:8000`
- Position sizing performance analytics at `/position-sizing-performance`
- Webhook processing logs with AI signal analysis
- Enhanced position monitoring with quality-based decisions
- Log file: `oracle.log`
- **Real-time sizing decisions**: Detailed logging of position size calculations
- **Signal quality tracking**: Performance correlation analysis

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

### **TITAN Configuration**
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

# Asset-specific recommendations based on backtesting:
# XRPPHP: 1.2% buy, 2.0% sell, 5.0% TP (optimized)
# SOLPHP: 0.8% buy, 1.3% sell, 2.0% TP (high volatility)
# BTCPHP: 1.5% buy, 2.5% sell, 3.0% TP (low volatility)
```

### **ORACLE Configuration**
```python
# Base configuration
base_amount = 200                    # ₱200 base reference amount
position_sizing_strategy = 'adaptive_ai'  # Choose from 6 strategies

# Advanced position sizing parameters
ai_confidence_weight = 0.35          # AI confidence importance
risk_reward_weight = 0.25            # Risk-reward ratio importance
market_alignment_weight = 0.25       # Price alignment importance
volatility_weight = 0.15             # Market volatility importance

# Dynamic sizing bounds
min_position_multiplier = 0.25       # Minimum 25% of base
max_position_multiplier = 2.0        # Maximum 200% of base

# Signal quality thresholds
min_signal_quality = 0.3             # Minimum quality to trade
high_quality_threshold = 0.7         # Threshold for bonus sizing
```

---

## 🆚 Bot Comparison

| Feature | 🤖 TITAN | 🔮 ORACLE |
|---------|----------|-----------|
| **Strategy** | Pure Momentum | AI + Advanced Sizing |
| **Signals** | Technical Analysis | MarketRaker AI |
| **Thresholds** | ✅ **Fully Configurable** | Fixed |
| **Setup** | ✅ **Optimization Wizard** | ✅ **Advanced Sizing Wizard** |
| **Recommendations** | ✅ **Backtesting-Based** | ✅ **AI Quality-Based** |
| **Position Sizing** | 4 Dynamic Strategies | ✅ **6 AI-Specific Strategies** |
| **Take Profit** | ✅ **0.5%-15% Configurable** | AI-Calculated + Dynamic |
| **Parameter Validation** | ✅ **Real-time Analysis** | ✅ **Signal Quality Matrix** |
| **Asset Optimization** | ✅ **Per-Pair Suggestions** | ✅ **Volatility Adaptation** |
| **Configuration** | ✅ **No Code Changes** | ✅ **Strategy Selection** |
| **Monitoring** | Enhanced Threshold Logs | ✅ **Sizing Performance Analytics** |
| **Risk Management** | Configurable Thresholds | ✅ **Quality-Based + Dynamic** |
| **Best For** | ✅ **Optimized momentum trading** | ✅ **AI-guided intelligent sizing** |
| **Complexity** | ✅ **Smart & Configurable** | ✅ **Advanced & Intelligent** |

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
- **TITAN**: Optimized momentum trading with configurable thresholds
- **ORACLE**: AI signal trading with intelligent position sizing
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
- **Signal Quality Risk**: Automated assessments may be inaccurate

**⚠️ TRADE RESPONSIBLY - NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE ⚠️**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional position sizing strategies for ORACLE
- Enhanced AI signal processing and quality assessment
- Multi-timeframe analysis integration
- Portfolio management features
- Telegram/Slack notifications
- Advanced backtesting features
- Machine learning signal validation

---

## 📄 License

This project is open source under MIT License. Use responsibly and at your own risk.

---

## 📞 Support

- **Issues**: Create GitHub issues for bugs or feature requests
- **API Problems**: Contact Coins.ph support for API-related issues
- **Strategy Questions**: Review backtest results and optimization tools
- **AI Integration**: Check MarketRaker documentation for signal formats
- **Position Sizing**: Monitor performance analytics and adjust strategies

---

## 🚀 Getting Started Checklist

- [ ] ✅ **Setup Environment** (Python 3.8+, dependencies)
- [ ] ✅ **Configure API Keys** (Coins.ph credentials)
- [ ] ✅ **Validate Connection** (`python test_connection.py`)
- [ ] ✅ **Choose Your Approach** (Quick start or research-driven)
- [ ] ✅ **Run Research Analysis** (`python momentum_backtest.py` - optional but recommended)
- [ ] ✅ **Optimize Parameters** (`python prophet.py` - optional but recommended)
- [ ] ✅ **Configure TITAN** (Revolutionary setup wizard with ecosystem intelligence)
- [ ] ✅ **Configure ORACLE** (Advanced position sizing strategy selection - optional)
- [ ] ✅ **Start Trading** (`python titan.py` or `python oracle.py`)
- [ ] ✅ **Monitor Performance** (Check logs and real-time analytics)

**Happy Trading with TITAN and ORACLE! 🤖🔮📈**