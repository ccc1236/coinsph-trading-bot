import os
import time
from datetime import datetime
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv(override=True)

class StablecoinAnalyzer:
    def __init__(self):
        self.api = CoinsAPI(
            api_key=os.getenv('COINS_API_KEY'),
            secret_key=os.getenv('COINS_SECRET_KEY')
        )
        
        # Pairs to analyze
        self.usdt_pair = 'USDTPHP'
        self.usdc_pair = 'USDCPHP'
        
        # Fee structure
        self.maker_fee = 0.0025  # 0.25%
        self.taker_fee = 0.0030  # 0.30%
        self.arbitrage_min_spread = (self.taker_fee * 2) + 0.002  # 0.8% minimum for profit
        
        print(f"🔍 Stablecoin Strategy Analyzer")
        print(f"📊 Analyzing: {self.usdt_pair} vs {self.usdc_pair}")
        print(f"💸 Round-trip fees: {(self.taker_fee * 2)*100:.1f}%")
        print(f"🎯 Minimum arbitrage spread needed: {self.arbitrage_min_spread*100:.1f}%")

    def get_current_prices(self):
        """Get current prices for both stablecoins"""
        try:
            usdt_price = self.api.get_current_price(self.usdt_pair)
            usdc_price = self.api.get_current_price(self.usdc_pair)
            
            return {
                'usdt': usdt_price,
                'usdc': usdc_price,
                'timestamp': datetime.now()
            }
        except Exception as e:
            print(f"❌ Error getting prices: {e}")
            return None

    def calculate_arbitrage_opportunity(self, usdt_price, usdc_price):
        """Calculate arbitrage spread and profitability"""
        # Calculate spreads both directions
        usdt_premium = (usdt_price - usdc_price) / usdc_price  # USDT more expensive
        usdc_premium = (usdc_price - usdt_price) / usdt_price  # USDC more expensive
        
        max_spread = max(abs(usdt_premium), abs(usdc_premium))
        
        # Determine direction
        if usdt_premium > 0:
            direction = "Buy USDC, Sell USDT"
            spread_pct = usdt_premium
        else:
            direction = "Buy USDT, Sell USDC"
            spread_pct = abs(usdc_premium)
        
        # Check profitability
        is_profitable = spread_pct > self.arbitrage_min_spread
        potential_profit = (spread_pct - (self.taker_fee * 2)) * 100  # Net profit %
        
        return {
            'usdt_price': usdt_price,
            'usdc_price': usdc_price,
            'spread_php': abs(usdt_price - usdc_price),
            'spread_pct': spread_pct * 100,
            'direction': direction,
            'is_profitable': is_profitable,
            'potential_profit_pct': potential_profit,
            'min_spread_needed': self.arbitrage_min_spread * 100
        }

    def analyze_micro_grid_opportunity(self, symbol, days=7):
        """Analyze micro-grid potential for a stablecoin"""
        print(f"\n📊 MICRO-GRID ANALYSIS: {symbol}")
        print("=" * 50)
        
        try:
            # Get recent price data
            klines = self.api._make_request(
                'GET', 
                '/openapi/quote/v1/klines',
                {
                    'symbol': symbol,
                    'interval': '1h',
                    'limit': days * 24
                }
            )
            
            prices = [float(kline[4]) for kline in klines]  # Close prices
            
            if not prices:
                print("❌ No price data available")
                return None
            
            # Calculate statistics
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price
            avg_price = sum(prices) / len(prices)
            
            # Calculate potential grid parameters
            range_pct = (price_range / avg_price) * 100
            
            # Micro-grid suggestions
            suggested_spacing = max(0.002, range_pct / 10)  # 0.2% minimum
            suggested_levels = min(5, max(2, int(range_pct / suggested_spacing)))
            
            # Calculate hourly volatility
            hourly_changes = []
            for i in range(1, len(prices)):
                change = abs(prices[i] - prices[i-1]) / prices[i-1]
                hourly_changes.append(change)
            
            avg_hourly_volatility = (sum(hourly_changes) / len(hourly_changes)) * 100
            
            print(f"📈 Price range ({days} days): ₱{min_price:.2f} - ₱{max_price:.2f}")
            print(f"📊 Total range: ₱{price_range:.3f} ({range_pct:.2f}%)")
            print(f"📊 Average price: ₱{avg_price:.2f}")
            print(f"⚡ Average hourly volatility: {avg_hourly_volatility:.3f}%")
            print(f"\n💡 MICRO-GRID RECOMMENDATIONS:")
            print(f"   🎯 Suggested grid spacing: {suggested_spacing*100:.2f}%")
            print(f"   🔢 Suggested grid levels: {suggested_levels}")
            print(f"   💰 Suggested trade size: ₱50-100")
            
            # Profitability check
            if range_pct > 1.0:  # More than 1% total range
                print(f"   ✅ VIABLE: {range_pct:.2f}% range > 1% (covers fees)")
            elif range_pct > 0.5:
                print(f"   🟡 MARGINAL: {range_pct:.2f}% range, tight margins")
            else:
                print(f"   ❌ NOT VIABLE: {range_pct:.2f}% range too small")
            
            return {
                'symbol': symbol,
                'price_range_php': price_range,
                'price_range_pct': range_pct,
                'avg_volatility': avg_hourly_volatility,
                'suggested_spacing': suggested_spacing,
                'suggested_levels': suggested_levels,
                'viable': range_pct > 0.5
            }
            
        except Exception as e:
            print(f"❌ Error analyzing {symbol}: {e}")
            return None

    def monitor_arbitrage(self, duration_minutes=30, check_interval=60):
        """Monitor arbitrage opportunities in real-time"""
        print(f"\n⚖️ ARBITRAGE MONITORING")
        print("=" * 50)
        print(f"⏰ Monitoring for {duration_minutes} minutes, checking every {check_interval} seconds")
        print(f"🎯 Looking for spreads > {self.arbitrage_min_spread*100:.1f}%")
        print()
        
        profitable_opportunities = 0
        max_spread_seen = 0
        
        for i in range(duration_minutes * 60 // check_interval):
            prices = self.get_current_prices()
            
            if prices:
                arb = self.calculate_arbitrage_opportunity(prices['usdt'], prices['usdc'])
                
                timestamp = prices['timestamp'].strftime('%H:%M:%S')
                
                if arb['is_profitable']:
                    print(f"🚨 {timestamp} - PROFITABLE ARBITRAGE!")
                    print(f"   {arb['direction']}")
                    print(f"   Spread: ₱{arb['spread_php']:.3f} ({arb['spread_pct']:.2f}%)")
                    print(f"   Potential profit: {arb['potential_profit_pct']:.2f}%")
                    profitable_opportunities += 1
                else:
                    status = "💚" if arb['spread_pct'] > 0.3 else "🟡" if arb['spread_pct'] > 0.1 else "🔴"
                    print(f"{status} {timestamp} - Spread: ₱{arb['spread_php']:.3f} ({arb['spread_pct']:.2f}%) - Too small")
                
                max_spread_seen = max(max_spread_seen, arb['spread_pct'])
            
            time.sleep(check_interval)
        
        print(f"\n📊 ARBITRAGE MONITORING RESULTS:")
        print(f"   🎯 Profitable opportunities: {profitable_opportunities}")
        print(f"   📈 Maximum spread seen: {max_spread_seen:.2f}%")
        print(f"   💡 Opportunities per hour: {profitable_opportunities * (60/duration_minutes):.1f}")

    def get_trading_recommendations(self):
        """Get overall trading recommendations"""
        print(f"\n💡 STABLECOIN TRADING RECOMMENDATIONS")
        print("=" * 50)
        
        # Analyze both pairs
        usdt_analysis = self.analyze_micro_grid_opportunity(self.usdt_pair, 7)
        usdc_analysis = self.analyze_micro_grid_opportunity(self.usdc_pair, 7)
        
        # Get current arbitrage status
        prices = self.get_current_prices()
        if prices:
            current_arb = self.calculate_arbitrage_opportunity(prices['usdt'], prices['usdc'])
            
            print(f"\n🎯 STRATEGY RECOMMENDATIONS:")
            
            # Micro-grid recommendation
            if usdt_analysis and usdt_analysis['viable']:
                print(f"✅ MICRO-GRID: {self.usdt_pair} looks viable")
                print(f"   Suggested: {usdt_analysis['suggested_spacing']*100:.2f}% spacing, {usdt_analysis['suggested_levels']} levels")
            elif usdc_analysis and usdc_analysis['viable']:
                print(f"✅ MICRO-GRID: {self.usdc_pair} looks viable")
                print(f"   Suggested: {usdc_analysis['suggested_spacing']*100:.2f}% spacing, {usdc_analysis['suggested_levels']} levels")
            else:
                print(f"❌ MICRO-GRID: Neither pair shows sufficient volatility")
            
            # Arbitrage recommendation
            print(f"\n⚖️ ARBITRAGE STATUS:")
            print(f"   Current spread: {current_arb['spread_pct']:.2f}%")
            print(f"   Needed for profit: {current_arb['min_spread_needed']:.1f}%")
            
            if current_arb['spread_pct'] > 0.4:
                print(f"   🟡 MONITOR: Spread approaching profitable levels")
                print(f"   📊 Recommend 30-min monitoring session")
            else:
                print(f"   🔴 WAIT: Spread too small for arbitrage")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Run 30-minute arbitrage monitoring")
        print(f"   2. Test micro-grid backtest if viable")
        print(f"   3. Compare with your XRP momentum results")

def main():
    print("🔍 Stablecoin Strategy Analyzer")
    print("=" * 40)
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API keys not found")
        return
    
    analyzer = StablecoinAnalyzer()
    
    print("\nSelect analysis type:")
    print("1. Quick overview (prices + basic analysis)")
    print("2. Micro-grid analysis (7 days)")
    print("3. Real-time arbitrage monitoring (30 min)")
    print("4. Full analysis (all of the above)")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice in ['1', '4']:
        # Quick overview
        prices = analyzer.get_current_prices()
        if prices:
            arb = analyzer.calculate_arbitrage_opportunity(prices['usdt'], prices['usdc'])
            print(f"\n💰 CURRENT PRICES:")
            print(f"   USDT: ₱{arb['usdt_price']:.2f}")
            print(f"   USDC: ₱{arb['usdc_price']:.2f}")
            print(f"   Spread: ₱{arb['spread_php']:.3f} ({arb['spread_pct']:.2f}%)")
    
    if choice in ['2', '4']:
        # Micro-grid analysis
        analyzer.analyze_micro_grid_opportunity('USDTPHP', 7)
        analyzer.analyze_micro_grid_opportunity('USDCPHP', 7)
    
    if choice in ['3', '4']:
        # Arbitrage monitoring
        monitor_time = 5 if choice == '4' else 30  # Shorter for full analysis
        analyzer.monitor_arbitrage(monitor_time, 30)
    
    if choice == '4':
        analyzer.get_trading_recommendations()

if __name__ == "__main__":
    main()