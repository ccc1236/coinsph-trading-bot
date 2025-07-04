import os
from dotenv import load_dotenv
from coins_api import CoinsAPI

load_dotenv()

def check_trading_volumes():
    """Check 24hr volumes for all trading pairs on Coins.ph"""
    
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )
    
    print("=" * 60)
    print("📊 COINS.PH TRADING VOLUME ANALYSIS")
    print("=" * 60)
    
    try:
        # Get all trading pairs
        print("🔍 Getting all trading pairs...")
        exchange_info = api.get_exchange_info()
        symbols = exchange_info.get('symbols', [])
        
        print(f"Found {len(symbols)} trading pairs")
        print()
        
        # Get 24hr ticker data for all pairs
        print("📈 Getting 24hr volume data...")
        all_tickers = api.get_24hr_ticker()  # Gets all pairs
        
        if not isinstance(all_tickers, list):
            all_tickers = [all_tickers]  # If single ticker returned
        
        # Process and sort by volume
        volume_data = []
        
        for ticker in all_tickers:
            try:
                symbol = ticker.get('symbol', '')
                volume = float(ticker.get('volume', 0))
                quote_volume = float(ticker.get('quoteVolume', 0))
                price_change = float(ticker.get('priceChangePercent', 0))
                last_price = float(ticker.get('lastPrice', 0))
                
                # Only include pairs with significant volume
                if volume > 0:
                    volume_data.append({
                        'symbol': symbol,
                        'volume': volume,
                        'quote_volume': quote_volume,
                        'price_change': price_change,
                        'last_price': last_price,
                        'currency': symbol[-3:] if len(symbol) >= 3 else 'N/A'  # Last 3 chars (PHP, USDT, etc.)
                    })
            except (ValueError, TypeError):
                continue
        
        # Sort by quote volume (value traded, not just quantity)
        volume_data.sort(key=lambda x: x['quote_volume'], reverse=True)
        
        print(f"✅ Processed {len(volume_data)} active trading pairs")
        print()
        
        # Display top trading pairs
        print("🏆 TOP TRADING PAIRS BY 24HR VOLUME:")
        print("-" * 60)
        print(f"{'Rank':<4} {'Symbol':<12} {'Quote Volume':<15} {'Price Change':<12} {'Currency'}")
        print("-" * 60)
        
        for i, data in enumerate(volume_data[:15]):  # Show top 15
            rank = i + 1
            symbol = data['symbol']
            quote_vol = data['quote_volume']
            price_change = data['price_change']
            currency = data['currency']
            
            # Format volume
            if quote_vol >= 1000000:
                vol_str = f"₱{quote_vol/1000000:.1f}M"
            elif quote_vol >= 1000:
                vol_str = f"₱{quote_vol/1000:.1f}K"
            else:
                vol_str = f"₱{quote_vol:.0f}"
            
            # Color code price changes
            change_str = f"{price_change:+.2f}%"
            if price_change > 0:
                change_str = f"📈 {change_str}"
            elif price_change < 0:
                change_str = f"📉 {change_str}"
            else:
                change_str = f"➡️  {change_str}"
            
            print(f"{rank:<4} {symbol:<12} {vol_str:<15} {change_str:<12} {currency}")
        
        print()
        
        # Focus on PHP pairs (most relevant for your bot)
        print("🇵🇭 PHP TRADING PAIRS (Most Relevant for Your Bot):")
        print("-" * 60)
        php_pairs = [d for d in volume_data if d['currency'] == 'PHP']
        
        if php_pairs:
            print(f"{'Rank':<4} {'Symbol':<12} {'Quote Volume':<15} {'Price Change':<12} {'Last Price'}")
            print("-" * 60)
            
            for i, data in enumerate(php_pairs[:10]):  # Show top 10 PHP pairs
                rank = i + 1
                symbol = data['symbol']
                quote_vol = data['quote_volume']
                price_change = data['price_change']
                last_price = data['last_price']
                
                # Format volume
                if quote_vol >= 1000000:
                    vol_str = f"₱{quote_vol/1000000:.1f}M"
                elif quote_vol >= 1000:
                    vol_str = f"₱{quote_vol/1000:.1f}K"
                else:
                    vol_str = f"₱{quote_vol:.0f}"
                
                # Price change
                change_str = f"{price_change:+.2f}%"
                if price_change > 0:
                    change_str = f"📈 {change_str}"
                elif price_change < 0:
                    change_str = f"📉 {change_str}"
                else:
                    change_str = f"➡️  {change_str}"
                
                # Format price
                if last_price >= 1000000:
                    price_str = f"₱{last_price/1000000:.1f}M"
                elif last_price >= 1000:
                    price_str = f"₱{last_price/1000:.1f}K"
                else:
                    price_str = f"₱{last_price:.2f}"
                
                print(f"{rank:<4} {symbol:<12} {vol_str:<15} {change_str:<12} {price_str}")
        else:
            print("No PHP pairs found with significant volume")
        
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS FOR YOUR BOT:")
        print("-" * 40)
        
        if php_pairs:
            top_php = php_pairs[0]
            current_symbol = os.getenv('TRADING_SYMBOL', 'BTCPHP')
            
            print(f"📍 Current symbol: {current_symbol}")
            print(f"🏆 Highest volume PHP pair: {top_php['symbol']}")
            
            if top_php['symbol'] != current_symbol:
                print(f"💡 Consider switching to {top_php['symbol']} for:")
                print("   - Higher liquidity (easier to buy/sell)")
                print("   - Tighter spreads (better prices)")
                print("   - More price movements (more trading opportunities)")
                print()
                print(f"To switch, update your .env file:")
                print(f"TRADING_SYMBOL={top_php['symbol']}")
            else:
                print("✅ You're already using the highest volume PHP pair!")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error checking volumes: {e}")

if __name__ == "__main__":
    check_trading_volumes()