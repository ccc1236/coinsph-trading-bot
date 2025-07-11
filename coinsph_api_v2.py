import hmac
import hashlib
import time
import requests
from urllib.parse import urlencode
import logging

class CoinsAPI:
    def __init__(self, api_key, secret_key):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.pro.coins.ph"
        self.session = requests.Session()
        self.session.headers.update({'X-COINS-APIKEY': self.api_key})
    
    def _make_request(self, method, endpoint, params=None, signed=False):
        """Make API request with WORKING signature handling - Natural parameter order"""
        params = params or {}
        
        if signed:
            current_timestamp = int(time.time() * 1000)
            
            # Use consistent recvWindow for all signed requests
            params['recvWindow'] = '5000'
            params['timestamp'] = str(current_timestamp)
            
            # CRITICAL FIX: Use NATURAL parameter order (NOT sorted) for signature
            # This was proven to work in our testing
            query_string = urlencode(list(params.items()))
            
            # Create signature
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params['signature'] = signature
            
            # Debug logging for troubleshooting
            logging.debug(f"Signature debug for {method} {endpoint}:")
            logging.debug(f"  Query string: {query_string}")
            logging.debug(f"  Timestamp: {current_timestamp}")
            logging.debug(f"  Signature: {signature}")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method == 'POST':
                # For POST requests, send data as form data
                response = self.session.post(url, data=params, timeout=30)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=30)
            
            # Enhanced error handling with detailed logging
            if response.status_code == 401:
                logging.error(f"Authentication failed for {method} {endpoint}")
                logging.error(f"Response: {response.text}")
            elif response.status_code == 400:
                logging.error(f"Bad request for {method} {endpoint}")
                logging.error(f"Response: {response.text}")
                logging.error(f"Request params: {params}")
            elif response.status_code != 200:
                logging.error(f"API request failed: {response.status_code}")
                logging.error(f"Endpoint: {method} {endpoint}")
                logging.error(f"Params: {params}")
                logging.error(f"Response: {response.text}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed for {method} {endpoint}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Error response: {e.response.text}")
            raise
    
    # ========== PUBLIC ENDPOINTS (No authentication) ==========
    
    def ping(self):
        """Test connectivity"""
        return self._make_request('GET', '/openapi/v1/ping')
    
    def get_server_time(self):
        """Get server time"""
        return self._make_request('GET', '/openapi/v1/time')
    
    def get_exchange_info(self, symbol=None):
        """Get exchange trading rules and symbol information"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/openapi/v1/exchangeInfo', params)
    
    def get_ticker_price(self, symbol=None):
        """Get latest price for symbol(s)"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/openapi/quote/v1/ticker/price', params)
    
    def get_24hr_ticker(self, symbol=None):
        """Get 24hr price change statistics"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/openapi/quote/v1/ticker/24hr', params)
    
    def get_order_book(self, symbol, limit=100):
        """Get order book for symbol"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/openapi/quote/v1/depth', params)
    
    def get_recent_trades(self, symbol, limit=500):
        """Get recent trades"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/openapi/quote/v1/trades', params)
    
    # ========== AUTHENTICATED ENDPOINTS ==========
    
    def get_account_info(self):
        """Get current account information"""
        return self._make_request('GET', '/openapi/v1/account', signed=True)
    
    def get_crypto_accounts(self, currency=None):
        """Get crypto account balances"""
        params = {'currency': currency} if currency else {}
        return self._make_request('GET', '/openapi/account/v3/crypto-accounts', params, signed=True)
    
    def get_open_orders(self, symbol=None):
        """Get all open orders"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/openapi/v1/openOrders', params, signed=True)
    
    def get_order_history(self, symbol, limit=500):
        """Get order history"""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/openapi/v1/historyOrders', params, signed=True)
    
    # ========== TRADING ENDPOINTS ==========
    
    def place_order(self, symbol, side, order_type, **kwargs):
        """
        Place a new order with WORKING signature and proper tick/step size handling
        
        Args:
            symbol: Trading pair (e.g., 'XRPPHP')
            side: 'BUY' or 'SELL'
            order_type: 'LIMIT', 'MARKET', etc.
            **kwargs: Additional parameters like quantity, price, timeInForce
        """
        # Get symbol info for proper formatting
        symbol_info = self.get_symbol_info(symbol)
        
        # Prepare parameters in the order that works with Coins.ph
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
        }
        
        # Add other parameters with proper formatting
        for key, value in kwargs.items():
            if key == 'price':
                # Format price with proper tick size
                price = float(value)
                if symbol_info:
                    tick_size = self._get_price_tick_size(symbol_info)
                    if tick_size:
                        price = self._round_to_tick_size(price, tick_size)
                    precision = self._get_price_precision(symbol_info)
                    params[key] = f"{price:.{precision}f}"
                else:
                    params[key] = f"{price:.4f}"
            elif key == 'quantity':
                # Format quantity with proper step size
                quantity = float(value)
                if symbol_info:
                    step_size = self._get_quantity_step_size(symbol_info)
                    if step_size:
                        quantity = self._round_to_step_size(quantity, step_size)
                    precision = self._get_quantity_precision(symbol_info)
                    params[key] = f"{quantity:.{precision}f}"
                else:
                    params[key] = f"{quantity:.6f}"
            else:
                params[key] = str(value)
        
        # Log the order attempt for debugging
        logging.info(f"Placing {side} order for {symbol}: {params}")
        
        return self._make_request('POST', '/openapi/v1/order', params, signed=True)
    
    def _get_price_tick_size(self, symbol_info):
        """Get price tick size from symbol info"""
        if not symbol_info or 'filters' not in symbol_info:
            return None
        
        for filter_info in symbol_info['filters']:
            if filter_info.get('filterType') == 'PRICE_FILTER':
                return float(filter_info.get('tickSize', 0))
        return None
    
    def _get_quantity_step_size(self, symbol_info):
        """Get quantity step size from symbol info"""
        if not symbol_info or 'filters' not in symbol_info:
            return None
        
        for filter_info in symbol_info['filters']:
            if filter_info.get('filterType') == 'LOT_SIZE':
                return float(filter_info.get('stepSize', 0))
        return None
    
    def _get_price_precision(self, symbol_info):
        """Get price precision from symbol info"""
        if not symbol_info:
            return 4  # Default precision
        
        tick_size = self._get_price_tick_size(symbol_info)
        if tick_size:
            # Count decimal places in tick size
            tick_str = f"{tick_size:.10f}".rstrip('0')
            if '.' in tick_str:
                return len(tick_str.split('.')[1])
        
        return symbol_info.get('quotePrecision', 4)
    
    def _get_quantity_precision(self, symbol_info):
        """Get quantity precision from symbol info"""
        if not symbol_info:
            return 6  # Default precision
        
        step_size = self._get_quantity_step_size(symbol_info)
        if step_size:
            # Count decimal places in step size
            step_str = f"{step_size:.10f}".rstrip('0')
            if '.' in step_str:
                return len(step_str.split('.')[1])
        
        return symbol_info.get('baseAssetPrecision', 6)
    
    def _round_to_tick_size(self, price, tick_size):
        """Round price to nearest tick size"""
        if tick_size <= 0:
            return price
        return round(price / tick_size) * tick_size
    
    def _round_to_step_size(self, quantity, step_size):
        """Round quantity to nearest step size"""
        if step_size <= 0:
            return quantity
        return round(quantity / step_size) * step_size
    
    def cancel_order(self, symbol=None, order_id=None, client_order_id=None):
        """Cancel an active order"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        if order_id:
            params['orderId'] = order_id
        if client_order_id:
            params['origClientOrderId'] = client_order_id
        return self._make_request('DELETE', '/openapi/v1/order', params, signed=True)
    
    def cancel_all_orders(self, symbol):
        """Cancel all open orders for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('DELETE', '/openapi/v1/openOrders', params, signed=True)
    
    def get_order_status(self, symbol=None, order_id=None, client_order_id=None):
        """Check order status"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        if order_id:
            params['orderId'] = order_id
        if client_order_id:
            params['origClientOrderId'] = client_order_id
        return self._make_request('GET', '/openapi/v1/order', params, signed=True)
    
    # ========== HELPER METHODS ==========
    
    def get_symbol_info(self, symbol):
        """Get specific symbol information"""
        exchange_info = self.get_exchange_info(symbol)
        if exchange_info.get('symbols'):
            return exchange_info['symbols'][0]
        return None
    
    def get_balance(self, asset=None):
        """Get account balance for specific asset or all"""
        account = self.get_account_info()
        balances = account.get('balances', [])
        
        if asset:
            for balance in balances:
                if balance['asset'] == asset:
                    return {
                        'asset': balance['asset'],
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': float(balance['free']) + float(balance['locked'])
                    }
            return None
        
        return [
            {
                'asset': b['asset'],
                'free': float(b['free']),
                'locked': float(b['locked']),
                'total': float(b['free']) + float(b['locked'])
            }
            for b in balances
        ]
    
    def get_current_price(self, symbol):
        """Get current price for symbol"""
        ticker = self.get_ticker_price(symbol)
        return float(ticker['price'])