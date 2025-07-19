# 🤖 Crypto Trading Bot for Coins.ph

**Automated momentum trading system featuring research-driven optimization, configurable parameters, and comprehensive risk management.**

---

## 🌟 Meet TITAN

### 🤖 **TITAN** - Advanced Momentum Trading Bot
**Pure momentum-based trading with fully configurable thresholds and optimization-driven recommendations**

- ✅ **Configurable Buy/Sell Thresholds** - No code changes needed, set at startup
- ✅ **Optimization-Driven Recommendations** - Backtesting discoveries integrated into setup
- ✅ **Asset-Specific Parameter Suggestions** - Smart defaults based on volatility analysis
- ✅ **Real-time Parameter Validation** - Market data analysis with live optimization suggestions
- ✅ **4 Position Sizing Strategies** - Fixed, Percentage, Momentum, and Adaptive sizing
- ✅ **Enhanced Setup Wizard** - Comprehensive configuration with performance predictions
- ✅ **Dynamic Risk Management** - Smart position adjustments based on market conditions
- ✅ **Multi-asset Support** - Optimized parameters for each trading pair
- ✅ **Comprehensive Backtesting** - Integration with live parameter feedback

### 🔮 **ORACLE** - AI Trading Bot (Advanced Users)
For users with MarketRaker AI signal subscriptions, we also provide ORACLE in the [`oracle/`](oracle/) folder. This requires premium AI signal access and token purchases. **Most users should use TITAN.**

---

## 📂 Repository Structure

### **🤖 Main Trading System**
- `titan.py` - **TITAN** momentum trading bot with dynamic position sizing
- `prophet.py` - Parameter optimization with ecosystem integration
- `momentum_backtest.py` - Multi-asset backtesting and research analysis

### **🔧 Core Infrastructure**
- `coinsph_api_v2.py` - Enhanced API wrapper with improved signature handling
- `ecosystem_manager.py` - Cross-tool data sharing and optimization

### **📊 Analysis & Utilities**
- `check_volumes.py` - **Enhanced** trading volume analysis with USD pairs support, professional formatting, and quick pair selection
- `test_connection.py` - API connectivity and trading permissions validator

### **🔮 Advanced AI Trading (Optional)**
- `oracle/` - **ORACLE** AI-enhanced trading bot for MarketRaker users
  - Requires premium AI signal subscription
  - See [`oracle/README.md`](oracle/README.md) for details

### **🔐 Configuration**
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies
- `.gitignore` - Git ignore rules

---

## 🚀 Getting Started

### **Step 1: Setup**
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

### **Step 3: Choose Your Approach**

#### **🎯 Option A: Quick Start**
```bash
python titan.py
```
Start TITAN immediately with built-in smart defaults. Good for getting started quickly.

#### **🔬 Option B: Research-Driven (Recommended)**
For optimal performance, use the research workflow:

**1. Market Research & Asset Analysis**
```bash
python momentum_backtest.py
```
- Analyzes multiple assets over 30-60 day periods
- Generates performance rankings and insights
- **Creates:** `ecosystem_data/research_insights.json` with asset performance scores

**2. Parameter Optimization**
```bash
python prophet.py
```
- Loads research insights from Step 1
- Suggests top-performing assets based on analysis
- Tests thousands of parameter combinations
- **Creates:** `prophet_reco.json` with optimized buy/sell/take-profit thresholds

**3. Live Trading with Optimized Settings**
```bash
python titan.py
```
- Automatically detects and loads Prophet's recommendations
- Shows expected performance based on backtesting
- Uses research-driven asset suggestions
- Applies ecosystem intelligence for parameter validation

---

## 📊 How the Research System Works

### **Data Flow**
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

---

## 🤖 TITAN - Advanced Momentum Trading Bot

### **🎯 Fully Configurable Trading System**
TITAN features revolutionary configurability - no hardcoded parameters!

#### **🔧 Configurable at Startup:**
- **Buy Threshold**: 0.5% - 5.0% (ecosystem-optimized suggestions)
- **Sell Threshold**: 0.8% - 4.0% (automatically calculated from buy threshold)
- **Take Profit**: 0.5% - 15.0% with asset-specific recommendations
- **Position Sizing**: Choose from 4 intelligent strategies

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

### **📊 Position Sizing Strategies**

| Strategy | Description | Best For | Risk Level |
|----------|-------------|----------|------------|
| **Fixed** | Same amount every trade | Consistent exposure | Low |
| **Percentage** | % of available balance | Balance scaling | Medium |
| **Momentum** | Size based on signal strength | Strong signals | Medium-High |
| **Adaptive** | Multi-factor intelligent sizing | Maximum optimization | Medium |

### **📊 Risk Management Features**
- **Configurable Thresholds**: Fully customizable buy/sell triggers (0.5%-5.0%)
- **Optimization-Based Defaults**: Smart suggestions based on backtesting discoveries
- **Real-time Parameter Validation**: Market analysis with live optimization suggestions
- **Asset-Specific Risk Management**: Tailored parameters per trading pair
- **Take Profit**: Fully configurable (0.5% - 15.0%) with asset-specific recommendations
- **Emergency Exit**: Strong downtrend protection (-5% trend)
- **Position Limits**: Maximum 10 trades per day
- **Hold Time**: 30-minute minimum position duration

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
- **Bot Configuration Export**: Generate TITAN ready configs

### **Enhanced Volume Analysis**
```bash
python check_volumes.py
```

**NEW Features:**
- **USD Pairs Support**: Complete USDC/USDT pairs listing and volume analysis
- **Professional Formatting**: Perfectly aligned tables with configurable column widths
- **Quick Pair Selection**: No more manual typing - select from numbered lists
- **5-Option Menu System**: Comprehensive analysis options
- **Multi-Currency Display**: Proper ₱ and $ formatting for different pair types

**Menu Options:**
1. **Volume Analysis** - Top trading pairs by 24hr volume (PHP + USD)
2. **PHP Pairs List** - All available PHP trading pairs with minimum orders
3. **USD Pairs List** - All USDC/USDT pairs with advantages breakdown
4. **Complete Analysis** - Combined volume + PHP + USD comprehensive view
5. **Pair Details** - Enhanced lookup with quick selection options

**Perfect for:**
- Discovering high-volume trading opportunities
- Finding new PHP and USD trading pairs
- Analyzing market trends and liquidity
- Quick pair lookup without manual typing
- Comparing PHP vs USD market opportunities

---

## 🔬 Testing & Validation

### **API Connection Testing**
```bash
python test_connection.py
```
- Validates API credentials and permissions
- Checks account balances and trading limits
- Verifies symbol availability

---

## 📈 Performance Monitoring

### **Real-time Monitoring**
TITAN provides comprehensive logging:
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

---

## 🔧 Configuration Options

### **Environment Variables**
```bash
# Required
COINS_API_KEY=your_coins_api_key
COINS_SECRET_KEY=your_coins_secret_key

# Optional (for ORACLE AI bot)
# MARKETRAKER_VERIFICATION_KEY=your_verification_key
```

### **TITAN Configuration**
Revolutionary configurability - no code changes needed:

```python
# All parameters configurable at startup via setup wizard:
buy_threshold             # 0.5% - 5.0% (ecosystem-optimized)
sell_threshold           # 0.8% - 4.0% (calculated from buy)
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

---

## 🚀 Example Workflows

### **New User - Quick Start**
```bash
python test_connection.py    # Validate setup
python titan.py              # Start trading with smart defaults
```

### **Experienced User - Research-Driven**
```bash
python test_connection.py         # Validate setup
python momentum_backtest.py       # Research top assets
python prophet.py                 # Optimize parameters
python titan.py                   # Trade with optimized settings
```

### **Volume Analysis & Pair Discovery**
```bash
python check_volumes.py           # Enhanced volume analysis with USD support
# Choose option 3 → USD pairs list
# Choose option 4 → Complete analysis  
# Choose option 5 → b → Quick PHP pair selection
# Choose option 5 → c → Quick USD pair selection
```

### **Asset Explorer**
```bash
python check_volumes.py           # Find high-volume pairs
python momentum_backtest.py       # Test multiple assets
python prophet.py                 # Optimize best performer
python titan.py                   # Trade optimized asset
```

---

## ⚠️ IMPORTANT LEGAL DISCLAIMER

### **🚨 NOT FINANCIAL ADVICE**
**This trading bot is provided for EDUCATIONAL and RESEARCH purposes ONLY.**

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

**⚠️ TRADE RESPONSIBLY - NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE ⚠️**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional position sizing strategies
- Multi-timeframe analysis integration
- Portfolio management features
- Telegram/Slack notifications
- Advanced backtesting features
- Machine learning integration

---

## 📄 License

This project is open source under MIT License. Use responsibly and at your own risk.

---

## 📞 Support

- **Issues**: Create GitHub issues for bugs or feature requests
- **API Problems**: Contact Coins.ph support for API-related issues
- **Strategy Questions**: Review backtest results and optimization tools
- **AI Trading**: See [`oracle/README.md`](oracle/README.md) for ORACLE support

---

## 🚀 Getting Started Checklist

- [ ] ✅ **Setup Environment** (Python 3.8+, dependencies)
- [ ] ✅ **Configure API Keys** (Coins.ph credentials)
- [ ] ✅ **Validate Connection** (`python test_connection.py`)
- [ ] ✅ **Choose Your Path** (Quick start or research-driven)
- [ ] ✅ **Run Research Analysis** (`python momentum_backtest.py` - optional but recommended)
- [ ] ✅ **Optimize Parameters** (`python prophet.py` - optional but recommended)
- [ ] ✅ **Analyze Volume & Pairs** (`python check_volumes.py` - discover opportunities)
- [ ] ✅ **Start Trading** (`python titan.py`)
- [ ] ✅ **Monitor Performance** (Check logs and real-time analytics)

**Happy Trading with TITAN! 🤖📈**

---

## 🔮 Advanced AI Trading

For users with MarketRaker AI signal subscriptions, we also provide **ORACLE** - an advanced AI-enhanced trading bot with intelligent position sizing. This requires premium signal access and is located in the [`oracle/`](oracle/) folder with its own setup guide.

**Most users should start with TITAN for momentum-based trading.**