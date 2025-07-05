# coinsph-trading-bot

Automated trading scripts for the Coins.ph PHP markets (SOL/PHP), plus volume sanity checks and a backtest engine.

---

## 📂 Repo Contents

- **Live Trading Bot**  
  - `sol_momentum_v2.py`  
    SOL/PHP momentum trader (v2).

- **Utilities**  
  - `check_volumes.py`  
    Basic volume sanity checks (on‐chain or orderbook).  
  - `coins_api.py`  
    Lightweight wrapper around the Coins.ph REST API.

- **Backtest Engine**  
  - `momentum_backtest_v43.py`  
    Backtest your SOL momentum strategy with configurable parameters.

- **Configuration & Secrets**  
  - `config.yaml`  
    Strategy parameters (thresholds, trade sizes, timing).  
  - `.env.example`  
    Template for environment variables (`API_KEY`, `API_SECRET`, optional `WEBHOOK_URL`).  

- **Tests**  
  - `test_connection.py`  
  - `test_signature.py`  

- **Misc**  
  - `requirements.txt`  
  - `.gitignore`  

---

## ⚙️ Prerequisites

- Python ≥ 3.8  
- A Coins.ph API key & secret  
- *(Optional)* Slack or Telegram webhook URL

---

## 🚀 Quick Start

1. **Clone the repo**  
   ```bash
   git clone https://github.com/ccc1236/coinsph-trading-bot.git
   cd coinsph-trading-bot

2. **Create & activate a virtualenv**
   ```bash
   python -m venv venv
   # macOS/Linux
   source venv/bin/activate
   # Windows
   venv\Scripts\activate

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt

4. **Configure credentials**
   ```bash
   cp .env.example .env
   # then edit .env to add your API_KEY, API_SECRET, etc.

5. **Adjust strategy parameters**

   Open config.yaml and tweak your thresholds, amounts, and timing.


