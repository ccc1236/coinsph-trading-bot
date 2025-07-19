# 🔮 ORACLE - AI-Enhanced Trading Bot

**Advanced AI-powered trading system with intelligent position sizing and MarketRaker integration.**

---

## ⚠️ **Prerequisites for ORACLE**

ORACLE is a **specialized AI trading bot** that requires:

- ✅ **All standard requirements** (Python, Coins.ph API, etc.)
- 🔑 **MarketRaker Account** - AI signal provider
- 💰 **MarketRaker Tokens** - Purchase on Cardano blockchain
- 🔗 **Active Subscription** - For live AI signals
- 🧠 **Advanced Trading Knowledge** - AI signal interpretation

**If you don't have MarketRaker access, use [TITAN](../README.md) instead.**

---

## 🌟 ORACLE Features

### **🎯 Advanced AI-Specific Position Sizing**
Revolutionary position sizing system designed specifically for AI trading signals:

1. **🎯 AI Confidence Sizing** - Scale position with AI signal strength
2. **📊 Volatility Adaptive Sizing** - Adjust position size for market volatility  
3. **🎪 Signal Quality Matrix Sizing** - Multi-factor signal assessment
4. **💰 Portfolio Scaling Sizing** - Position size grows with account balance
5. **⚖️ Risk-Reward Optimization** - Size based on AI target/stop ratios
6. **🧠 Adaptive AI Sizing (Recommended)** - Advanced multi-factor intelligent sizing

### **🔬 Signal Quality Assessment**
ORACLE evaluates every AI signal across multiple dimensions:
- **AI Confidence**: Based on risk level and expected change
- **Risk-Reward Ratio**: Target vs stop loss distance  
- **Market Alignment**: How close current price is to AI entry
- **Volatility Factor**: Market stability assessment
- **Overall Quality Score**: Combined 0.0-1.0 rating

### **💱 Real-time USD/PHP Conversion**
- Automatic conversion of MarketRaker USD signals to PHP prices
- Smart caching with fallback APIs
- Price level validation with tolerance checking

### **📊 Enhanced Position Monitoring**
- Quality-based exit strategies
- Signal degradation detection
- Time-based exits for low quality signals
- Dynamic stop loss and target management

---

## 🚀 Quick Start

### **1. MarketRaker Setup** 
Before running ORACLE, you need:

1. **Create MarketRaker Account**
   - Visit MarketRaker website
   - Complete account registration

2. **Purchase MarketRaker Tokens**
   - Buy tokens on Cardano blockchain
   - Required for AI signal subscriptions

3. **Get Verification Key**
   - Obtain webhook verification key from MarketRaker
   - Add to your `.env` file

### **2. Environment Configuration**
Update your `.env` file:
```bash
# Required for ORACLE
COINS_API_KEY=your_coins_api_key
COINS_SECRET_KEY=your_coins_secret_key
MARKETRAKER_VERIFICATION_KEY=your_verification_key_here
```

### **3. Test Exchange Rate APIs**
```bash
python oracle/test_exchange_rates.py
```
Validates USD/PHP conversion functionality.

### **4. Start ORACLE**
```bash
python oracle/oracle.py
```

---

## 🔧 Configuration

### **Interactive Setup**
ORACLE provides an enhanced setup wizard:

1. **Base Amount Configuration**: ₱100-₱1000 reference amount
2. **Position Sizing Strategy Selection**: Choose from 6 advanced strategies
3. **Strategy Explanation**: Detailed description of each approach
4. **Risk Assessment**: Risk level and complexity indicators
5. **Performance Expectations**: Expected position size ranges

### **Position Sizing Strategies**

| Strategy | Description | Best For | Risk Level |
|----------|-------------|----------|------------|
| **AI Confidence** | Scale with signal strength | Trusting AI quality | Medium |
| **Volatility Adaptive** | Adjust for market volatility | Volatile markets | Low-Medium |
| **Signal Quality** | Multi-factor assessment | Comprehensive evaluation | Medium |
| **Portfolio Scaling** | Grows with account balance | Growing accounts | Medium-High |
| **Risk-Reward** | Based on target/stop ratios | Risk-conscious trading | Low-Medium |
| **Adaptive AI** ⭐ | Advanced multi-factor | Maximum optimization | Medium |

### **Core Parameters**
```python
base_amount = 200                    # ₱200 base reference amount
position_sizing_strategy = 'adaptive_ai'  # Recommended strategy

# Advanced position sizing weights
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

## 🌐 Webhook Server

ORACLE runs a FastAPI webhook server to receive AI signals:

### **Endpoints**
```
http://localhost:8000/                           # Bot status
http://localhost:8000/health                     # Health check
http://localhost:8000/status                     # Comprehensive status
http://localhost:8000/exchange-rate              # USD/PHP rate info
http://localhost:8000/position-sizing-performance # Sizing analytics
```

### **Signal Processing**
- **Live Signals**: `/webhook/marketraker` (with signature verification)
- **Test Signals**: `/webhook/test` (for development)
- **Toggle Mode**: `/toggle-test-mode` (switch test/live)

### **Test Mode**
ORACLE starts in **test mode** by default for safety:
```bash
# Toggle between test and live mode
python oracle/toggle_oracle_mode.py
```

---

## 📊 Signal Processing

### **Supported Trading Pairs**
```python
supported_pairs = {
    'XRP/USD': 'XRPPHP',
    'SOL/USD': 'SOLPHP', 
    'BTC/USD': 'BTCPHP',
    'ETH/USD': 'ETHPHP'
}
```

### **AI Signal Format**
MarketRaker signals are automatically converted:
```python
{
    "trading_type": "Long",           # Buy signal
    "leverage": 1,                    # Position leverage
    "buy_price": 2.45,               # Entry price (USD)
    "sell_price": 2.58,              # Target price (USD)
    "stoploss": 2.35,                # Stop loss (USD)
    "risk": 5,                       # Risk level (1-10)
    "percentage_change": 5.3,        # Expected % change
    "trading_pair": "XRP/USD"        # Asset pair
}
```

### **Conversion Process**
1. **USD → PHP**: Convert all prices using live exchange rate
2. **Quality Assessment**: Evaluate signal across multiple dimensions
3. **Position Sizing**: Calculate optimal position size
4. **Price Validation**: Check current market price vs AI entry
5. **Execution**: Place order if all conditions met

---

## 📈 Performance Monitoring

### **Real-time Analytics**
- **Position Sizing Performance**: Track strategy effectiveness
- **Signal Quality Metrics**: Monitor AI signal quality over time
- **Risk-Reward Analysis**: Actual vs predicted performance
- **Quality-Based Exits**: Track exit reason effectiveness

### **Logging**
- **File**: `oracle.log` (detailed operation logs)
- **Console**: Real-time status and decision explanations
- **Webhook**: Signal processing and conversion logs

### **Dashboard**
Access comprehensive status at `http://localhost:8000/status`:
- Bot configuration and uptime
- Position sizing strategy performance
- Exchange rate information
- Active positions and daily trades
- Signal reception history

---

## 🛡️ Risk Management

### **Signal Filtering**
- **Risk Level**: Rejects signals with risk > 8/10
- **Price Validation**: 3% tolerance for AI entry points
- **Quality Threshold**: Minimum 0.3 quality score
- **Market Alignment**: Price proximity to AI entry

### **Position Management**
- **AI Target Monitoring**: Automatic exit when target reached
- **AI Stop Loss**: Strict adherence to AI stop levels
- **Quality Degradation**: Exit if signal quality drops
- **Time-based Exits**: Exit low quality signals after 24h
- **Emergency Protection**: Strong downtrend exits

### **Dynamic Bounds**
Position sizes automatically adjust:
- **Minimum**: ₱50 (very low quality signals)
- **Typical**: ₱200 (your base amount)  
- **Maximum**: ₱400 (exceptional high-quality signals)

---

## 🔧 Troubleshooting

### **Common Issues**

#### **Exchange Rate Errors**
```bash
# Test USD/PHP conversion
python oracle/test_exchange_rates.py
```

#### **MarketRaker Connection**
- Verify webhook verification key
- Check MarketRaker subscription status
- Ensure token balance sufficient

#### **Signal Not Processing**
- Check webhook endpoint accessibility
- Verify signal format matches expected structure
- Review logs for processing errors

#### **Position Sizing Issues**
- Monitor `/position-sizing-performance` endpoint
- Check account balance sufficiency
- Verify position sizing strategy selection

### **Debug Mode**
Enable detailed logging in `oracle.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## 🚫 Limitations

- **MarketRaker Dependency**: Requires active subscription
- **Limited Pairs**: Currently supports 4 major pairs
- **USD Signals Only**: Designed for USD-based AI signals
- **Premium Service**: Requires token purchase on Cardano
- **Advanced Setup**: More complex than basic momentum trading

---

## 🆚 ORACLE vs TITAN

| Feature | 🔮 ORACLE | 🤖 TITAN |
|---------|-----------|----------|
| **Signal Source** | MarketRaker AI | Price momentum |
| **Setup Complexity** | Advanced | Simple |
| **Cost** | Requires tokens | Free |
| **Position Sizing** | 6 AI strategies | 4 standard strategies |
| **Entry Requirements** | AI subscription | Market analysis |
| **Best For** | AI signal trading | Momentum trading |

---

## ⚠️ **Important Notes**

### **🚨 Premium Service Requirements**
- MarketRaker requires **paid subscription**
- Tokens must be **purchased on Cardano**
- **Not suitable** for casual traders
- Consider **TITAN** for free momentum trading

### **🔐 Security**
- Keep MarketRaker verification key secure
- Use test mode for development
- Monitor webhook access logs
- Validate all incoming signals

### **💰 Risk Warning**
- AI signals can be **incorrect**
- Position sizing amplifies both **gains and losses**
- **Start small** with test amounts
- **Never risk** more than you can afford to lose

---

## 📞 Support

- **ORACLE Issues**: Check logs and webhook connectivity
- **MarketRaker Problems**: Contact MarketRaker support
- **Signal Processing**: Review exchange rate APIs
- **Position Sizing**: Monitor performance analytics

For general trading bot support, see the [main README](../README.md).

---

**🔮 ORACLE is designed for advanced traders with AI signal access. For most users, [TITAN](../README.md) provides excellent momentum-based trading without external dependencies.**