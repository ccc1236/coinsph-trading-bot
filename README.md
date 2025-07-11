# coinsph-trading-bot

Beginner momentum-based automated trading bot for Coins.ph cryptocurrency markets, featuring comprehensive backtesting, live trading capabilities, and take profit optimization.

---

## 🌟 Key Features

- **Live Momentum Trading**: Real-time SOL/PHP and XRP/PHP trading with configurable take profit levels
- **Advanced Backtesting**: Comprehensive historical analysis with performance metrics
- **Take Profit Optimization**: Systematic testing to find optimal profit-taking levels
- **Multi-Asset Support**: Optimized strategies for different volatility profiles
- **Real-time Monitoring**: Live trading status with detailed logging and performance tracking
- **Risk Management**: Daily trade limits, minimum hold times, and emergency exit conditions

---

## 📂 Repository Structure

### **Live Trading Bots**
- `momentum_v3.py` - **Main trading bot** with configurable take profit and interactive setup
- `coinsph_api_v2.py` - Enhanced API wrapper with improved signature handling for trading endpoints

### **Strategy Optimization**
- `take_profit_optimizer.py` - Comprehensive take profit level testing and optimization
- `momentum_backtest_v44.py` - Advanced backtesting engine with detailed performance metrics

### **Utilities & Analysis**
- `check_volumes.py` - Trading volume analysis and pair recommendations
- `test_connection.py` - API connectivity and trading permissions validator
- `test_signature.py` - API authentication debugging tools
- `test_account.py` - Simple account access verification

### **Configuration**
- `.env.example` - Environment variables template (API keys)
- `requirements.txt` - Python dependencies

---

**Strategy Parameters:**
- Buy Threshold: 0.6% momentum
- Sell Threshold: 1.0% decline
- Trade Amount: ₱200 per position
- Min Hold Time: 30 minutes
- Max Trades/Day: 10

---

## ⚙️ Prerequisites

- **Python ≥ 3.8**
- **Coins.ph Pro account** with API access
- **₱500+ balance** recommended for safe trading
- **API permissions**: Trading enabled, IP whitelisted

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
```

### 3. **Validate Setup**
```bash
python test_connection.py
```
This will verify your API connection, trading permissions, and account balances.

### 4. **Start Live Trading**
```bash
python momentum_v3.py
```

**Interactive Setup:**
- Choose trading asset (XRPPHP recommended)
- Set take profit level (5.0% recommended for XRPPHP)
- Confirm configuration and start trading

---

## 🔬 Strategy Optimization

### **Find Optimal Take Profit Levels**
```bash
python take_profit_optimizer.py
```

**Features:**
- Tests 14 different take profit levels (0.5% - 5.0%)
- Comprehensive performance analysis
- Risk-adjusted return calculations
- Detailed recommendations based on your risk tolerance

### **Volume Analysis for Asset Selection**
```bash
python check_volumes.py
```

**Shows:**
- Top trading pairs by 24hr volume
- PHP pair rankings and liquidity
- Recommendations for optimal trading pairs

---

## 📊 Live Trading Features

### **Real-time Monitoring**
- Live price tracking with momentum analysis
- Position management with P/L tracking
- Trade execution logs with detailed reasoning
- Daily trade counters and limits

### **Risk Management**
- **Take Profit**: Configurable profit-taking levels
- **Stop Loss**: Momentum-based exit conditions
- **Emergency Exit**: Strong downtrend protection
- **Position Limits**: Maximum trades per day
- **Hold Time**: Minimum position duration

### **Smart Entry/Exit Conditions**

**Buy Signals:**
- ✅ Price momentum > 0.6%
- ✅ Not in strong downtrend
- ✅ Sufficient PHP balance
- ✅ Within daily trade limits
- ✅ No existing position

**Sell Signals:**
- 🎯 **Take Profit**: Configurable % gain reached
- 📉 **Momentum Down**: Price decline > 1.0%
- 🚨 **Emergency Exit**: Strong downtrend detected

---

## 💡 Configuration Options

### **Strategy Parameters**
All strategy parameters are **optimized and hard-coded** in `momentum_v3.py` for stability and performance:

```python
# Optimized parameters (tested via backtesting)
self.buy_threshold = 0.006      # 0.6% momentum trigger
self.sell_threshold = 0.010     # 1.0% decline trigger  
self.base_amount = 200          # ₱200 per trade
self.min_hold_hours = 0.5       # 30 minutes minimum hold
self.max_trades_per_day = 10    # Daily safety limit
self.check_interval = 900       # 15 minutes between checks
```

### **Interactive Configuration**
When starting the bot, you'll configure:
- **Trading Asset**: XRPPHP (recommended), SOLPHP, or custom pair
- **Take Profit Level**: Optimized suggestions provided based on backtesting

### **Asset Selection**
- **XRPPHP**: Recommended (stable, good liquidity, proven profitable)
- **SOLPHP**: High volatility (requires lower take profit levels)
- **Custom**: Any PHP trading pair supported

---

## 📈 Performance Monitoring

### **Trading Logs**
All trades are logged with:
- Entry/exit prices and times
- Profit/loss calculations
- Trade reasoning (momentum, take profit, emergency)
- Fee calculations
- Portfolio value tracking

### **Daily Reports**
- Total trades executed
- Win/loss ratio
- Net profit/loss
- Fees paid
- Performance vs buy & hold

---

## 🛡️ Safety Features

- **Paper Trading Mode**: Test strategies without real money (coming soon)
- **Emergency Stop**: Ctrl+C to safely halt all trading
- **Connection Monitoring**: Automatic reconnection on API failures
- **Balance Validation**: Prevents trades with insufficient funds
- **Order Confirmation**: Detailed logging of all order placements

---

## 🔧 Troubleshooting

### **Common Issues**

**"Authentication failed"**
```bash
python test_signature.py
```
Checks API signature generation and server time sync.

**"Insufficient balance"**
- Verify PHP balance > ₱300 minimum
- Check minimum order requirements for your symbol

**"Symbol not found"**
```bash
python check_volumes.py
```
Verify symbol is actively traded and correctly formatted.

**"Trading disabled"**
- Ensure API keys have trading permissions
- Check IP whitelist settings in Coins.ph Pro

---

## 📚 Advanced Usage

### **Custom Strategy Development**
The bot architecture supports easy strategy modifications:
- Adjust momentum thresholds in `momentum_v3.py`
- Modify risk management rules
- Add technical indicators
- Implement portfolio rebalancing

### **Multi-Asset Trading**
Run multiple bot instances for different assets:
```bash
# Terminal 1: XRPPHP bot
python momentum_v3.py

# Terminal 2: SOLPHP bot (different config)
python momentum_v3.py
```

---

## 📋 Requirements

### **System Requirements**
- Stable internet connection (15-minute check intervals)
- Python 3.8+ with required packages
- ~10MB RAM per bot instance

### **Trading Requirements**
- Coins.ph Pro account with verified identity
- API keys with trading permissions
- ₱500+ recommended starting balance
- IP address whitelisted (if required)

---

## ⚠️ IMPORTANT LEGAL DISCLAIMER

### **🚨 NOT FINANCIAL ADVICE**
**This trading bot and all associated documentation are provided for EDUCATIONAL and RESEARCH purposes ONLY.**

- This is **NOT financial advice, investment advice, or trading advice**
- The author(s) are **NOT licensed financial advisors** or investment professionals
- All trading strategies are experimental and should be considered **high-risk**
- You should **consult with qualified financial professionals** before making any trading decisions

### **💸 NO LIABILITY FOR LOSSES**
**BY USING THIS SOFTWARE, YOU ACKNOWLEDGE AND AGREE:**

- **You use this software entirely AT YOUR OWN RISK**
- The author(s) are **NOT LIABLE** for any financial losses, damages, or consequences
- You are **SOLELY RESPONSIBLE** for any trading decisions and their outcomes
- **Cryptocurrency trading can result in TOTAL LOSS** of your investment
- Past performance shown in backtests **DOES NOT GUARANTEE future results**

### **⚖️ USER RESPONSIBILITIES**
- **Test thoroughly** with small amounts before any significant trading
- **Understand the code** and strategy before running live trades
- **Monitor positions actively** - automated trading can fail or behave unexpectedly
- **Have exit strategies** and be prepared to manually intervene
- **Only trade with money you can afford to LOSE COMPLETELY**
- **Comply with local laws** and tax obligations in your jurisdiction

### **🛡️ Risk Factors**
- **Market Risk**: Cryptocurrency markets are highly volatile and unpredictable
- **Technical Risk**: Software bugs, API failures, or connectivity issues may cause losses
- **Strategy Risk**: Trading algorithms may perform poorly in changing market conditions
- **Regulatory Risk**: Cryptocurrency regulations may change and affect trading
- **Exchange Risk**: Third-party exchanges may experience outages, hacks, or closure

**⚠️ TRADE RESPONSIBLY - NEVER RISK MORE THAN YOU CAN AFFORD TO LOSE ⚠️**

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional technical indicators
- Multi-timeframe analysis  
- Portfolio management features
- Enhanced risk management
- Paper trading mode
- Telegram/Slack notifications

---

## 📄 License

This project is open source. Use responsibly and at your own risk.

---

## 📞 Support

- **Issues**: Create GitHub issues for bugs or feature requests
- **API Problems**: Contact Coins.ph support for API-related issues
- **Strategy Questions**: Review backtest results and optimization tools

**Happy Trading! 🚀📈**