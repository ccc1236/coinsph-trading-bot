import os
import math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class SignalDebugger:
    def __init__(self, symbol='SOLPHP'):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        self.symbol = symbol
        
        # v3 parameters
        self.base_buy_threshold = 0.012
        self.volume_threshold = 1.3
        self.short_trend_window = 4
        self.medium_trend_window = 12
        self.long_trend_window = 48
        
        self.price_history = []
        self.volume_history = []
        
    def get_historical_data(self, days=30):
        try:
            klines = self.api._make_request(
                'GET', 
                '/openapi/quote/v1/klines',
                {
                    'symbol': self.symbol,
                    'interval': '1h',
                    'limit': min(days * 24, 1000)
                }
            )
            
            processed_data = []
            for kline in klines:
                processed_data.append({
                    'timestamp': datetime.fromtimestamp(int(kline[0]) / 1000),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            return processed_data
        except Exception as e:
            print(f"Error: {e}")
            return None

    def calculate_multi_timeframe_trend(self, prices):
        trends = {}
        
        # Short-term trend
        if len(prices) >= self.short_trend_window:
            recent = prices[-self.short_trend_window:]
            mid = len(recent) // 2
            first_half = sum(recent[:mid]) / mid
            second_half = sum(recent[mid:]) / (len(recent) - mid)
            trends['short'] = (second_half - first_half) / first_half
        else:
            trends['short'] = 0
        
        # Medium-term trend
        if len(prices) >= self.medium_trend_window:
            recent = prices[-self.medium_trend_window:]
            mid = len(recent) // 2
            first_half = sum(recent[:mid]) / mid
            second_half = sum(recent[mid:]) / (len(recent) - mid)
            trends['medium'] = (second_half - first_half) / first_half
        else:
            trends['medium'] = 0
        
        # Long-term trend
        if len(prices) >= self.long_trend_window:
            recent = prices[-self.long_trend_window:]
            mid = len(recent) // 2
            first_half = sum(recent[:mid]) / mid
            second_half = sum(recent[mid:]) / (len(recent) - mid)
            trends['long'] = (second_half - first_half) / first_half
        else:
            trends['long'] = 0
        
        return trends

    def calculate_volume_signal(self, volumes):
        if len(volumes) < 20:
            return 1.0
        
        recent_volume = volumes[-1]
        avg_volume = sum(volumes[-20:]) / 20
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
        return volume_ratio

    def debug_signals(self):
        print("🔍 Debugging why v3 made 0 trades...")
        
        data = self.get_historical_data(30)
        if not data:
            return
        
        signals_blocked = {
            'price_momentum': 0,
            'medium_trend': 0,
            'long_trend': 0,
            'volume': 0,
            'total_checks': 0,
            'potential_buys': 0
        }
        
        last_price = None
        
        for i, candle in enumerate(data):
            self.price_history.append(candle['close'])
            self.volume_history.append(candle['volume'])
            
            if last_price is None:
                last_price = candle['close']
                continue
            
            # Calculate signals
            price_change = (candle['close'] - last_price) / last_price
            trends = self.calculate_multi_timeframe_trend(self.price_history)
            volume_ratio = self.calculate_volume_signal(self.volume_history)
            
            signals_blocked['total_checks'] += 1
            
            # Check each condition
            if price_change > self.base_buy_threshold:
                signals_blocked['potential_buys'] += 1
                
                if trends['medium'] <= -0.03:
                    signals_blocked['medium_trend'] += 1
                elif trends['long'] <= -0.08:
                    signals_blocked['long_trend'] += 1
                elif volume_ratio < self.volume_threshold * 0.8:
                    signals_blocked['volume'] += 1
                else:
                    # This would have been a buy!
                    print(f"✅ MISSED BUY SIGNAL at {candle['timestamp'].strftime('%Y-%m-%d %H:%M')}")
                    print(f"   Price change: {price_change*100:+.2f}%")
                    print(f"   Trends: ST:{trends['short']*100:+.1f}% MT:{trends['medium']*100:+.1f}% LT:{trends['long']*100:+.1f}%")
                    print(f"   Volume: {volume_ratio:.2f}x (need {self.volume_threshold*0.8:.1f}x)")
                    print()
            
            last_price = candle['close']
        
        print(f"\n📊 SIGNAL BLOCKING ANALYSIS:")
        print(f"Total price checks: {signals_blocked['total_checks']}")
        print(f"Price momentum signals: {signals_blocked['potential_buys']}")
        print(f"Blocked by medium trend: {signals_blocked['medium_trend']}")
        print(f"Blocked by long trend: {signals_blocked['long_trend']}")
        print(f"Blocked by volume: {signals_blocked['volume']}")
        
        if signals_blocked['potential_buys'] == 0:
            print(f"\n❌ NO price momentum signals exceeded {self.base_buy_threshold*100:.1f}% threshold!")
            print(f"   Recommendation: Lower base_buy_threshold to 0.8-1.0%")
        elif signals_blocked['volume'] > signals_blocked['potential_buys'] * 0.8:
            print(f"\n❌ VOLUME filter blocking {signals_blocked['volume']} signals!")
            print(f"   Recommendation: Lower volume_threshold to 1.1-1.2x")
        elif signals_blocked['medium_trend'] > signals_blocked['potential_buys'] * 0.6:
            print(f"\n❌ MEDIUM TREND filter blocking {signals_blocked['medium_trend']} signals!")
            print(f"   Recommendation: Relax medium trend from -3% to -5%")
        
        print(f"\n🔧 SUGGESTED FIXES:")
        print(f"1. Lower buy threshold: 1.2% → 0.8%")
        print(f"2. Relax volume filter: 1.3x → 1.1x") 
        print(f"3. Relax medium trend: -3% → -5%")
        print(f"4. Test with these relaxed parameters")

if __name__ == "__main__":
    debugger = SignalDebugger('SOLPHP')
    debugger.debug_signals()