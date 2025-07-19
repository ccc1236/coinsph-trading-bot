import os
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI

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
        print("-" * 70)
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
            
            print(f"🏆 Highest volume PHP pair: {top_php['symbol']}")
            print(f"📊 Popular stable options: BTCPHP, ETHPHP, XRPPHP, SOLPHP")
            print(f"💰 High volume = better liquidity and tighter spreads")
            print(f"🎯 Choose based on your risk tolerance and market knowledge")
            print(f"📈 Volume leaders typically have:")
            print("   - More price movements (trading opportunities)")
            print("   - Better order book depth (easier fills)")
            print("   - Lower spread costs (better entry/exit prices)")
        else:
            print("❌ No volume data available for recommendations")
        
        print()
        
        return symbols, php_pairs
        
    except Exception as e:
        print(f"❌ Error checking volumes: {e}")
        return None, None

def list_all_php_pairs(symbols):
    """List all PHP trading pairs with detailed information"""
    
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )
    
    print("=" * 60)
    print("🏦 ALL PHP TRADING PAIRS ON COINS.PH")
    print("=" * 60)
    
    try:
        # Filter for PHP pairs only
        php_pairs = []
        for symbol in symbols:
            symbol_name = symbol.get('symbol', '')
            base_asset = symbol.get('baseAsset', '')
            quote_asset = symbol.get('quoteAsset', '')
            status = symbol.get('status', '')
            
            # Include ALL PHP pairs (trading, break, etc.)
            if quote_asset == 'PHP':
                php_pairs.append({
                    'symbol': symbol_name,
                    'base_asset': base_asset,
                    'status': status
                })
        
        # Display PHP pairs
        print(f"🇵🇭 COMPLETE PHP TRADING PAIRS LIST ({len(php_pairs)} pairs):")
        print("-" * 70)
        print(f"{'#':<3} {'Symbol':<15} {'Base Asset':<12} {'Status':<8} {'Min Order'}")
        print("-" * 70)
        
        for i, pair in enumerate(php_pairs, 1):
            symbol_name = pair['symbol']
            
            # Get minimum order size
            min_order = "Loading..."
            try:
                symbol_info = api.get_symbol_info(symbol_name)
                if symbol_info and symbol_info.get('filters'):
                    for f in symbol_info['filters']:
                        if f.get('filterType') == 'MIN_NOTIONAL':
                            min_notional = float(f.get('minNotional', 0))
                            if min_notional >= 1000:
                                min_order = f"₱{min_notional/1000:.1f}K"
                            else:
                                min_order = f"₱{min_notional:.0f}"
                            break
                    else:
                        min_order = "N/A"
                else:
                    min_order = "N/A"
            except:
                min_order = "Error"
            
            # Status indicator (use text instead of emojis for better alignment)
            status_upper = pair['status'].upper()
            if status_upper == 'TRADING':
                status_display = "TRADING "
            elif status_upper == 'BREAK':
                status_display = "BREAK   "
            else:
                status_display = f"{status_upper:<8}"
            
            print(f"{i:<3} {pair['symbol']:<15} {pair['base_asset']:<12} {status_display:<8} {min_order}")
        
        print("-" * 60)
        
        # Show some popular ones for reference
        popular_assets = ['BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'DOT', 'MATIC', 'LINK', 'LTC', 'BCH', 'DOGE', 'AVAX']
        available_popular = [pair for pair in php_pairs if pair['base_asset'] in popular_assets and pair['status'].upper() == 'TRADING']
        
        if available_popular:
            print(f"\n🌟 POPULAR TRADEABLE ASSETS:")
            print("-" * 30)
            for pair in available_popular:
                print(f"   ✅ {pair['symbol']} ({pair['base_asset']})")
        
        # Show trading status summary (handle case-insensitive)
        trading_pairs = [p for p in php_pairs if p['status'].upper() == 'TRADING']
        break_pairs = [p for p in php_pairs if p['status'].upper() == 'BREAK']
        other_pairs = [p for p in php_pairs if p['status'].upper() not in ['TRADING', 'BREAK']]
        
        print(f"\n📊 TRADING STATUS SUMMARY:")
        print(f"   ✅ Trading: {len(trading_pairs)} pairs")
        if break_pairs:
            print(f"   ⏸️ Break: {len(break_pairs)} pairs")
        if other_pairs:
            print(f"   ❌ Other: {len(other_pairs)} pairs")
        
        # For trading bot reference
        print(f"\n🤖 FOR TRADING BOTS:")
        print("   Use any TRADING status symbols in your bot:")
        trading_symbols = [p['symbol'] for p in trading_pairs]
        
        # Show examples
        print("   Examples:")
        for symbol in trading_symbols[:8]:  # Show first 8
            print(f"   - {symbol}")
        if len(trading_symbols) > 8:
            print(f"   ... and {len(trading_symbols) - 8} more!")
        
        print(f"\n💡 USAGE TIPS:")
        print(f"   • TITAN: Choose any symbol for momentum trading")
        print(f"   • ORACLE: Add to supported_pairs dict for AI trading")
        print(f"   • Higher volume = better liquidity")
        print(f"   • Check minimum order requirements")
        
        return php_pairs
        
    except Exception as e:
        print(f"❌ Error listing PHP pairs: {e}")
        return None

def get_pair_details(symbol):
    """Get detailed information for a specific trading pair"""
    
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )
    
    try:
        print(f"\n📊 DETAILED INFO FOR {symbol}:")
        print("-" * 50)
        
        # Get symbol info
        symbol_info = api.get_symbol_info(symbol)
        if symbol_info:
            print(f"Symbol: {symbol_info.get('symbol')}")
            print(f"Base Asset: {symbol_info.get('baseAsset')}")
            print(f"Quote Asset: {symbol_info.get('quoteAsset')}")
            print(f"Status: {symbol_info.get('status')}")
            
            # Get filters (trading rules)
            filters = symbol_info.get('filters', [])
            for f in filters:
                filter_type = f.get('filterType')
                if filter_type == 'MIN_NOTIONAL':
                    print(f"Minimum Order: ₱{f.get('minNotional')}")
                elif filter_type == 'LOT_SIZE':
                    print(f"Min Quantity: {f.get('minQty')}")
                    print(f"Max Quantity: {f.get('maxQty')}")
                    print(f"Step Size: {f.get('stepSize')}")
                elif filter_type == 'PRICE_FILTER':
                    print(f"Min Price: ₱{f.get('minPrice')}")
                    print(f"Max Price: ₱{f.get('maxPrice')}")
                    print(f"Tick Size: ₱{f.get('tickSize')}")
        
        # Get current price
        try:
            current_price = api.get_current_price(symbol)
            print(f"Current Price: ₱{current_price}")
        except:
            print("Current Price: Not available")
        
        # Get 24hr stats
        try:
            ticker = api.get_24hr_ticker(symbol)
            print(f"24h Change: {ticker.get('priceChangePercent', 'N/A')}%")
            print(f"24h Volume: {ticker.get('volume', 'N/A')}")
            print(f"24h Quote Volume: ₱{float(ticker.get('quoteVolume', 0)):,.0f}")
            print(f"24h High: ₱{ticker.get('highPrice', 'N/A')}")
            print(f"24h Low: ₱{ticker.get('lowPrice', 'N/A')}")
        except:
            print("24h Stats: Not available")
            
    except Exception as e:
        print(f"❌ Error getting details for {symbol}: {e}")

def main():
    """Enhanced main function with options"""
    
    if not os.getenv('COINS_API_KEY'):
        print("❌ API credentials not found!")
        print("Please set COINS_API_KEY and COINS_SECRET_KEY in .env")
        return
    
    print("🔍 COINS.PH MARKET ANALYSIS TOOL")
    print("=" * 50)
    print("1. Volume Analysis (Top trading pairs by volume)")
    print("2. Complete PHP Pairs List (All available PHP pairs)")
    print("3. Both (Volume analysis + Complete list)")
    print("4. Pair Details (Get details for specific symbol)")
    
    try:
        choice = input("\nEnter choice (1-4, default: 1): ").strip()
        
        if choice in ['1', '3', ''] or not choice:
            # Volume analysis
            symbols, php_volume_pairs = check_trading_volumes()
            
            if choice == '3' and symbols:
                print("\n" + "=" * 60)
                # Complete list
                list_all_php_pairs(symbols)
                
        elif choice == '2':
            # Get symbols first
            print("📡 Fetching exchange information...")
            api = CoinsAPI(
                api_key=os.getenv('COINS_API_KEY'),
                secret_key=os.getenv('COINS_SECRET_KEY')
            )
            exchange_info = api.get_exchange_info()
            symbols = exchange_info.get('symbols', [])
            
            if symbols:
                list_all_php_pairs(symbols)
            else:
                print("❌ Could not fetch symbols")
                
        elif choice == '4':
            # Pair details
            while True:
                symbol = input("\nEnter symbol for detailed info (or 'quit' to exit): ").strip().upper()
                if symbol.lower() in ['quit', 'q', 'exit', '']:
                    break
                elif symbol:
                    get_pair_details(symbol)
        
        else:
            print("❌ Invalid choice. Running volume analysis...")
            check_trading_volumes()
            
    except KeyboardInterrupt:
        print("\n\n👋 Market analysis ended gracefully")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()