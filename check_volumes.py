import os
from dotenv import load_dotenv
from coinsph_api_v2 import CoinsAPI

load_dotenv()

# ================== COLUMN WIDTH CONSTANTS ==================
RANK_W = 3        # width for rank (right-aligned)
SYMBOL_W = 12
BASE_ASSET_W = 10
STATUS_W = 8
# Min Order column will be variable after the fixed columns.

# Format strings (no emojis inside rows to preserve strict monospace alignment)
PHP_ROW_FMT = f"{{rank:>{RANK_W}}}  {{symbol:<{SYMBOL_W}}} {{base:<{BASE_ASSET_W}}} {{status:<{STATUS_W}}} {{min_order}}"
PHP_HEADER_FMT = PHP_ROW_FMT.replace("{rank:>{RANK_W}}", f"{'#':>{RANK_W}}").replace("{symbol:", "{symbol:").replace("{base:", "{base:").replace("{status:", "{status:").replace("{min_order}", "Min Order")

TOP_ROW_FMT = " {rank:>2}. {symbol:<12} {qvol:<15} {change:<12} {curr}"
TOP_HEADER_FMT = " {rank:>2}  {symbol:<12} {qvol:<15} {change:<12} {curr}".format(
    rank="Rk", symbol="Symbol", qvol="Quote Volume", change="Price Change", curr="Currency"
)

# Table width for separators (adjust if you change formats)
PHP_TABLE_WIDTH = len(PHP_ROW_FMT.format(rank='999', symbol='X'*SYMBOL_W, base='X'*BASE_ASSET_W,
                                         status='X'*STATUS_W, min_order='MinOrderExample'))


def format_compact(amount: float, currency_symbol: str = '₱', decimals_small: int = 0):
    """Format a numeric amount with K/M suffix, else plain."""
    try:
        if amount >= 1_000_000:
            return f"{currency_symbol}{amount / 1_000_000:.1f}M"
        if amount >= 1_000:
            return f"{currency_symbol}{amount / 1_000:.1f}K"
        fmt = f"{{:{'.' + str(decimals_small) + 'f' if decimals_small else '.0f'}}}"
        return f"{currency_symbol}{fmt.format(amount)}"
    except (TypeError, ValueError):
        return f"{currency_symbol}{amount}"


def map_quote_currency(quote_asset: str):
    if quote_asset in ('USDC', 'USDT'):
        return '$', 'USD'
    if quote_asset == 'PHP':
        return '₱', 'PHP'
    return '', quote_asset or 'N/A'


def check_trading_volumes():
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )

    print("=" * 60)
    print("COINS.PH TRADING VOLUME ANALYSIS")
    print("=" * 60)

    try:
        print("Getting all trading pairs...")
        exchange_info = api.get_exchange_info()
        symbols = exchange_info.get('symbols', [])
        print(f"Found {len(symbols)} trading pairs\n")

        print("Getting 24hr volume data...")
        all_tickers = api.get_24hr_ticker()
        if not isinstance(all_tickers, list):
            all_tickers = [all_tickers]

        volume_data = []
        for ticker in all_tickers:
            try:
                symbol = ticker.get('symbol', '')
                volume = float(ticker.get('volume', 0) or 0)
                quote_volume = float(ticker.get('quoteVolume', 0) or 0)
                price_change = float(ticker.get('priceChangePercent', 0) or 0)
                last_price = float(ticker.get('lastPrice', 0) or 0)
                if volume > 0:
                    volume_data.append({
                        'symbol': symbol,
                        'volume': volume,
                        'quote_volume': quote_volume,
                        'price_change': price_change,
                        'last_price': last_price,
                        'currency': symbol[-3:] if len(symbol) >= 3 else 'N/A'
                    })
            except (ValueError, TypeError):
                continue

        volume_data.sort(key=lambda x: x['quote_volume'], reverse=True)
        print(f"Processed {len(volume_data)} active trading pairs\n")

        print("TOP TRADING PAIRS BY 24HR VOLUME:")
        print("-" * 70)
        print(TOP_HEADER_FMT)
        print("-" * 70)

        for i, data in enumerate(volume_data[:15], start=1):
            quote_vol = data['quote_volume']
            price_change = data['price_change']
            vol_str = format_compact(quote_vol, '₱')
            change_str = f"{price_change:+.2f}%"
            if price_change > 0:
                change_str = f"↑ {change_str}"
            elif price_change < 0:
                change_str = f"↓ {change_str}"
            else:
                change_str = f"→ {change_str}"
            print(TOP_ROW_FMT.format(
                rank=i,
                symbol=data['symbol'],
                qvol=vol_str,
                change=change_str,
                curr=data['currency']
            ))

        print()
        print("PHP TRADING PAIRS (Most Relevant for Your Bot):")
        print("-" * 60)
        php_pairs = [d for d in volume_data if d['currency'] == 'PHP']

        if php_pairs:
            header = f"{'Rk':>2}  {'Symbol':<12} {'Quote Volume':<15} {'Price Change':<12} {'Last Price'}"
            print(header)
            print("-" * 60)
            for i, data in enumerate(php_pairs[:10], start=1):
                quote_vol = data['quote_volume']
                price_change = data['price_change']
                last_price = data['last_price']
                vol_str = format_compact(quote_vol, '₱')
                change_str = f"{price_change:+.2f}%"
                if price_change > 0:
                    change_str = f"↑ {change_str}"
                elif price_change < 0:
                    change_str = f"↓ {change_str}"
                else:
                    change_str = f"→ {change_str}"

                if last_price >= 1_000_000:
                    price_str = f"₱{last_price / 1_000_000:.1f}M"
                elif last_price >= 1_000:
                    price_str = f"₱{last_price / 1_000:.1f}K"
                else:
                    price_str = f"₱{last_price:.2f}"

                print(f"{i:>2}. {data['symbol']:<12} {vol_str:<15} {change_str:<12} {price_str}")
        else:
            print("No PHP pairs found with significant volume")

        print()
        print("RECOMMENDATIONS FOR YOUR BOT:")
        print("-" * 40)
        if php_pairs:
            top_php = php_pairs[0]
            print(f"Highest volume PHP pair: {top_php['symbol']}")
            print("Popular high-liquidity examples: BTCPHP, ETHPHP, XRPPHP, SOLPHP")
            print("High volume => better depth & tighter spreads")
        else:
            print("No PHP pair data for recommendations")
        print()

        return symbols, php_pairs

    except Exception as e:
        print(f"Error checking volumes: {e}")
        return None, None


def list_all_php_pairs(symbols):
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )

    print("=" * 60)
    print("ALL PHP TRADING PAIRS ON COINS.PH")
    print("=" * 60)

    try:
        php_pairs = []
        for symbol in symbols:
            s_name = symbol.get('symbol', '')
            base_asset = symbol.get('baseAsset', '')
            quote_asset = symbol.get('quoteAsset', '')
            status = symbol.get('status', '')
            if quote_asset == 'PHP':
                php_pairs.append({
                    'symbol': s_name,
                    'base_asset': base_asset,
                    'status': status
                })

        print(f"PHP COMPLETE PHP TRADING PAIRS LIST ({len(php_pairs)} pairs):")
        print("-" * PHP_TABLE_WIDTH)
        print(PHP_HEADER_FMT.format(
            rank='#', symbol='Symbol', base='Base Asset',
            status='Status', min_order='Min Order'
        ))
        print("-" * PHP_TABLE_WIDTH)

        for idx, pair in enumerate(php_pairs, start=1):
            min_order = "N/A"
            try:
                info = api.get_symbol_info(pair['symbol'])
                if info:
                    for f in info.get('filters', []):
                        if f.get('filterType') == 'MIN_NOTIONAL':
                            mn = float(f.get('minNotional', 0))
                            min_order = f"₱{mn / 1_000:.1f}K" if mn >= 1_000 else f"₱{mn:.0f}"
                            break
            except Exception:
                min_order = "Error"

            status_display = pair['status'].upper()[:STATUS_W]
            print(PHP_ROW_FMT.format(
                rank=idx,
                symbol=pair['symbol'],
                base=pair['base_asset'],
                status=status_display,
                min_order=min_order
            ))

        print("-" * PHP_TABLE_WIDTH)

        popular = ['BTC', 'ETH', 'XRP', 'SOL', 'ADA', 'DOT', 'MATIC', 'LINK', 'LTC', 'BCH', 'DOGE', 'AVAX']
        popular_available = [
            p for p in php_pairs if p['base_asset'] in popular and p['status'].upper() == 'TRADING'
        ]

        if popular_available:
            print("\nPOPULAR TRADEABLE ASSETS:")
            for p in popular_available:
                print(f"  - {p['symbol']} ({p['base_asset']})")

        trading = [p for p in php_pairs if p['status'].upper() == 'TRADING']
        brk = [p for p in php_pairs if p['status'].upper() == 'BREAK']
        other = [p for p in php_pairs if p['status'].upper() not in ['TRADING', 'BREAK']]

        print("\nTRADING STATUS SUMMARY:")
        print(f"  Trading: {len(trading)} pairs")
        if brk:
            print(f"  Break:   {len(brk)} pairs")
        if other:
            print(f"  Other:   {len(other)} pairs")

        print("\nFOR TRADING BOTS (examples):")
        for sym in [p['symbol'] for p in trading[:8]]:
            print(f"  - {sym}")
        if len(trading) > 8:
            print(f"  ... and {len(trading) - 8} more")

        print("\nTIPS:")
        print("  • Momentum: focus on highest quote volume")
        print("  • Add symbols to supported list programmatically")
        print("  • Monitor min notional before sending orders\n")

        return php_pairs

    except Exception as e:
        print(f"Error listing PHP pairs: {e}")
        return None


def get_pair_details(symbol: str):
    api = CoinsAPI(
        api_key=os.getenv('COINS_API_KEY'),
        secret_key=os.getenv('COINS_SECRET_KEY')
    )

    try:
        print(f"\nDETAILS FOR {symbol}:")
        print("-" * 50)

        currency_symbol = ''
        symbol_info = api.get_symbol_info(symbol)
        if symbol_info:
            quote_asset = symbol_info.get('quoteAsset', '')
            currency_symbol, _ = map_quote_currency(quote_asset)
            print(f"Symbol:      {symbol_info.get('symbol')}")
            print(f"Base Asset:  {symbol_info.get('baseAsset')}")
            print(f"Quote Asset: {symbol_info.get('quoteAsset')}")
            print(f"Status:      {symbol_info.get('status')}")
            for f in symbol_info.get('filters', []):
                ft = f.get('filterType')
                if ft == 'MIN_NOTIONAL':
                    mn = f.get('minNotional')
                    print(f"Minimum Order: {currency_symbol}{mn}")
                elif ft == 'LOT_SIZE':
                    print(f"Qty Range: {f.get('minQty')} - {f.get('maxQty')} (step {f.get('stepSize')})")
                elif ft == 'PRICE_FILTER':
                    print(f"Price Range: {currency_symbol}{f.get('minPrice')} - {currency_symbol}{f.get('maxPrice')} (tick {f.get('tickSize')})")
        else:
            print("Symbol info not available.")

        try:
            price = api.get_current_price(symbol)
            if price is not None:
                print(f"Current Price: {currency_symbol}{price}")
            else:
                print("Current Price: N/A")
        except Exception:
            print("Current Price: N/A")

        try:
            ticker = api.get_24hr_ticker(symbol)
            if ticker:
                chg = ticker.get('priceChangePercent', 'N/A')
                vol = ticker.get('volume', 'N/A')
                qv = ticker.get('quoteVolume', 0)
                high = ticker.get('highPrice', 'N/A')
                low = ticker.get('lowPrice', 'N/A')
                print(f"24h Change: {chg}%")
                print(f"24h Volume: {vol}")
                try:
                    qv_f = float(qv)
                    print(f"24h Quote Volume: {currency_symbol}{qv_f:,.0f}")
                except (TypeError, ValueError):
                    print(f"24h Quote Volume: {qv}")
                if high != 'N/A':
                    print(f"24h High: {currency_symbol}{high}")
                if low != 'N/A':
                    print(f"24h Low:  {currency_symbol}{low}")
            else:
                print("24h Stats: N/A")
        except Exception:
            print("24h Stats: N/A")

    except Exception as e:
        print(f"Error getting details for {symbol}: {e}")


def main():
    if not os.getenv('COINS_API_KEY'):
        print("API credentials not found! Set COINS_API_KEY / COINS_SECRET_KEY in .env")
        return

    print("COINS.PH MARKET ANALYSIS TOOL")
    print("=" * 50)
    print("1. Volume Analysis (Top trading pairs by volume)")
    print("2. Complete PHP Pairs List (All available PHP pairs)")
    print("3. Both (Volume + List)")
    print("4. Pair Details (Specific symbol)")

    try:
        choice = input("\nEnter choice (1-4, default: 1): ").strip()
        if choice in ('1', '3', ''):
            symbols, _php_pairs = check_trading_volumes()
            if choice == '3' and symbols:
                print()
                list_all_php_pairs(symbols)
        elif choice == '2':
            print("Fetching exchange information...")
            api = CoinsAPI(
                api_key=os.getenv('COINS_API_KEY'),
                secret_key=os.getenv('COINS_SECRET_KEY')
            )
            exchange_info = api.get_exchange_info()
            symbols = exchange_info.get('symbols', [])
            if symbols:
                list_all_php_pairs(symbols)
            else:
                print("Could not fetch symbols.")
        elif choice == '4':
            while True:
                sym = input("\nEnter symbol (or blank to quit): ").strip().upper()
                if not sym or sym.lower() in ('q', 'quit', 'exit'):
                    break
                get_pair_details(sym)
        else:
            print("Invalid choice. Running volume analysis...")
            check_trading_volumes()
    except KeyboardInterrupt:
        print("\nStopped.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
