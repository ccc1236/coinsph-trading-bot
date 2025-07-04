import sys
# Force both stdout and stderr to UTF-8 so emojis and ₱ work in prints and logging
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import time
import logging
import yaml
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

# Load environment variables
load_dotenv(override=True)

# Load configuration with debug
CONFIG_PATH = Path(__file__).parent / "config.yaml"
print("CONFIG_PATH ->", CONFIG_PATH.resolve())
print("Exists?     ->", CONFIG_PATH.is_file())

# Dump raw file contents
raw = CONFIG_PATH.read_text()
print("Raw file content:\n", raw)

# Then parse
config = yaml.safe_load(raw)
print("Parsed config:", config)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_sol_momentum.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('EnhancedSOLMomentumBot')

class EnhancedSOLMomentumBot:
    def __init__(self):
        # Initialize API
        self.api = CoinsAPI(
            api_key=os.getenv(config['api']['key_env_var']),
            secret_key=os.getenv(config['api']['secret_env_var'])
        )
        
        # Load parameters from config
        self.symbol              = config['api']['symbol']
        self.buy_threshold       = config['trade']['buy_threshold_pct'] / 100
        self.sell_threshold      = config['trade']['sell_threshold_pct'] / 100
        self.base_amount         = config['trade']['base_amount_php']
        self.min_hold_hours      = config['trade']['min_hold_hours']
        self.max_trades_per_day  = config['trade']['max_trades_per_day']
        self.trend_window        = config['trend']['window_hours']
        self.check_interval      = config['schedule']['check_interval_sec']

        # Runtime state
        self.running     = False
        self.last_price  = None
        self.position    = None  # 'long' or None
        self.entry_price = None
        self.entry_time  = None
        self.price_history = []
        self.daily_trades  = {}

        logger.info(f"   Enhanced SOL Momentum Bot initialized with config.yaml")
        logger.info(f"   Symbol: {self.symbol}")
        logger.info(f"   Buy threshold: {self.buy_threshold*100:.1f}%")
        logger.info(f"   Sell threshold: {self.sell_threshold*100:.1f}%")
        logger.info(f"   Trade amount: {self.base_amount}")
        logger.info(f"   Min hold time: {self.min_hold_hours}h")
        logger.info(f"   Trend window: {self.trend_window}h")
        logger.info(f"   Max trades/day: {self.max_trades_per_day}")
        logger.info(f"   Check interval: {self.check_interval//60}min")

    # ... (other methods unchanged, now refer to config-driven attributes) ...
    def get_symbol_info(self):
        try:
            symbol_info = self.api.get_symbol_info(self.symbol)
            # logging as before
            return symbol_info
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None

    def get_account_status(self):
        # identical to before
        return self.api.get_account_info()

    def calculate_quantity(self, price, amount_php):
        return amount_php / price

    def update_price_history(self, price):
        self.price_history.append({'price': price, 'timestamp': datetime.now()})
        cutoff = datetime.now() - timedelta(hours=self.trend_window*2)
        self.price_history = [p for p in self.price_history if p['timestamp'] > cutoff]

    def calculate_trend(self):
        if len(self.price_history) < self.trend_window:
            return 0
        recent = [p['price'] for p in self.price_history[-self.trend_window:]]
        mid = len(recent)//2
        first = sum(recent[:mid]) / mid
        second = sum(recent[mid:]) / (len(recent)-mid)
        return (second-first)/first

    def can_trade_today(self):
        today = datetime.now().strftime('%Y-%m-%d')
        return self.daily_trades.get(today, 0) < self.max_trades_per_day

    def can_sell_position(self):
        if not self.entry_time:
            return True
        return (datetime.now() - self.entry_time) >= timedelta(hours=self.min_hold_hours)

    def update_daily_trades(self):
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1

    def enhanced_momentum_strategy(self):
        try:
            price = self.api.get_current_price(self.symbol)
            self.update_price_history(price)

            if self.last_price is None:
                self.last_price = price
                return

            change = (price - self.last_price) / self.last_price
            trend = self.calculate_trend()

            sol_bal = self.api.get_balance('SOL')['free']
            php_bal = self.api.get_balance('PHP')['free']

            # BUY
            if (change > self.buy_threshold and trend > -0.02
                    and php_bal > self.base_amount*1.2
                    and self.can_trade_today() and not self.position):
                self.place_enhanced_buy_order(price, trend)

            # SELL
            elif (change < -self.sell_threshold and sol_bal > 0.001
                    and self.can_sell_position() and self.can_trade_today()):
                self.place_enhanced_sell_order(price, trend, "Momentum Down")

            # EMERGENCY EXIT
            elif (trend < -0.05 and sol_bal > 0.001 and self.can_sell_position()):
                self.place_enhanced_sell_order(price, trend, "Emergency Trend Exit")

            self.last_price = price
        except Exception as e:
            logger.error(f"Error in strategy: {e}")

    # place_enhanced_buy_order and place_enhanced_sell_order unchanged...

    def start(self):
        if not self.get_symbol_info() or not self.get_account_status():
            return
        self.running = True
        while self.running:
            self.enhanced_momentum_strategy()
            time.sleep(self.check_interval)

    def stop(self):
        self.running = False


def main():
    bot = EnhancedSOLMomentumBot()
    if input("Start bot? (y/n): ").lower().startswith('y'):
        bot.start()

if __name__ == '__main__':
    main()
