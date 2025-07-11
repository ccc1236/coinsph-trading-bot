# 🤖 Crypto Trading Bots for Coins.ph

**Automated trading systems featuring momentum analysis, AI integration, and comprehensive risk management.**

---

## 🌟 Meet the Bots

### 🤖 **TITAN** - Momentum Trading Bot v3.0
**Pure momentum-based trading with configurable take profit levels**
- ✅ **High-frequency momentum trading** with optimized parameters
- ✅ **Configurable take profit levels** (0.5% - 10%)
- ✅ **Real-time trend analysis** with 12-hour windows
- ✅ **Smart risk management** with daily limits and minimum hold times
- ✅ **Multi-asset support** (XRPPHP, SOLPHP, BTCPHP)
- ✅ **Comprehensive backtesting** integration

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
- `titan.py` - **TITAN** momentum trading bot with configurable take profit
- `oracle.py` - **ORACLE** AI-enhanced trading bot with MarketRaker integration

### **🔧 Core Infrastructure**
- `coinsph_api_v2.py` - Enhanced API wrapper with improved signature handling
- `momentum_backtest_v44.py` - Advanced backtesting engine with comprehensive analysis
- `take_profit_optimizer.py` - Comprehensive take profit level optimization

### **📊 Analysis & Utilities**
- `check_volumes.py` - Trading volume analysis and pair recommendations
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
# COINS_API_KEY=your_api_key_here
# COINS_SECRET_KEY=your_secret_key_here
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
- Interactive setup with asset selection
- Configurable take profit levels
- Immediate momentum-based trading

#### **🔮 Start ORACLE (AI Bot)**
```bash
python oracle.py
```
- Webhook server for AI signals
- Test mode enabled by default
- Advanced monitoring dashboard

---

## 🤖 TITAN - Momentum Trading Bot

### **🎯 Core Features**
- **Pure Momentum Strategy**: 0.6% buy threshold, 1.0% sell threshold
- **Configurable Take Profit**: 0.5% - 10% customizable levels
- **Smart Position Management**: 30-minute minimum hold, emergency exits
- **Multi-Asset Support**: Optimized for XRPPHP, SOLPHP, BTCPHP
- **Daily Safety Limits**: Maximum 10 trades per day

### **📊 Optimized Parameters**
```python
# Backtested and optimized settings
Buy Threshold: 0.6% momentum
Sell Threshold: 1.0% decline  
Trade Amount: ₱200 per position
Min Hold Time: 30 minutes
Max Trades/Day: 10
Check Interval: 15 minutes
```

### **🎯 Asset Recommendations**
- **XRPPHP**: Recommended (5.0% take profit, +1.5% backtested return at the time of writing)
- **SOLPHP**: High volatility (1.8% take profit, -1.3% backtested return at the time of writing)
- **Custom**: Any PHP trading pair

### **🚀 Starting TITAN**
```bash
python titan.py
```
**Interactive Configuration:**
1. Choose trading asset (XRPPHP recommended)
2. Set take profit level (5.0% recommended for XRPPHP)
3. Confirm and start trading

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

### **Take Profit Optimization (for TITAN)**
```bash
python take_profit_optimizer.py
```

**Comprehensive Analysis:**
- Tests 14 different take profit levels (0.5% - 5.0%)
- Risk-adjusted return calculations
- Win rate and trade frequency analysis
- Detailed recommendations based on risk tolerance

**Sample Results:**
- **XRPPHP**: 5.0% take profit → +1.5% return, 65% win rate
- **SOLPHP**: 1.8% take profit → -1.3% return, 58% win rate

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

### **AI Signal Testing (for ORACLE)**
```bash
python test_signals.py
```
- Sends fake MarketRaker signals to ORACLE
- Tests webhook processing
- Validates decision logic

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
- Console output with 15-minute updates
- Log file: `titan.log`
- Trade alerts with P/L calculations

### **ORACLE Monitoring**
- FastAPI dashboard at `http://localhost:8000`
- Webhook processing logs
- AI signal analysis and decisions
- Log file: `oracle.log`

---

## 🛡️ Risk Management

### **TITAN Risk Features**
- **Take Profit**: Configurable profit-taking (0.5% - 10%)
- **Stop Loss**: Momentum-based exit conditions
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

### **TITAN Configuration**
All parameters optimized and hardcoded for stability:
```python
# Optimized parameters (tested via backtesting)
buy_threshold = 0.006      # 0.6% momentum trigger
sell_threshold = 0.010     # 1.0% decline trigger  
base_amount = 200          # ₱200 per trade
min_hold_hours = 0.5       # 30 minutes minimum hold
max_trades_per_day = 10    # Daily safety limit
check_interval = 900       # 15 minutes between checks
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

| Feature | 🤖 TITAN | 🔮 ORACLE |
|---------|----------|-----------|
| **Strategy** | Pure Momentum | AI + Momentum |
| **Signals** | Technical Analysis | MarketRaker AI |
| **Currency** | PHP Native | USD→PHP Conversion |
| **Take Profit** | Configurable (0.5%-10%) | AI-Calculated |
| **Risk Management** | Rule-Based | AI Risk Scoring |
| **Monitoring** | Console Logging | FastAPI Dashboard |
| **Best For** | Consistent momentum trading | AI-guided precision |
| **Complexity** | Simple & Reliable | Advanced & Intelligent |

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
- **TITAN**: Continuous momentum trading on XRPPHP
- **ORACLE**: AI signal trading on multiple pairs
- **Both**: Diversified strategy with different approaches

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

**⚠️ TRADE RESPONSIBLY - NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE ⚠️**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional technical indicators for TITAN
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
- [ ] ✅ **Start Small** (₱200 base amount recommended)
- [ ] ✅ **Monitor Performance** (check logs and dashboard)
- [ ] ✅ **Optimize Strategy** (use backtesting tools)

**Happy Trading with TITAN and ORACLE! 🤖🔮📈**