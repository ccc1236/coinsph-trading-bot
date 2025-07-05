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
        """Make API request with proper authentication using EXACT working signature method"""
        params = params or {}
        
        if signed:
            # Use the EXACT method that worked in simple_account_test.py
            current_timestamp = int(time.time() * 1000)
            
            params['recvWindow'] = '5000'
            params['timestamp'] = str(current_timestamp)
            
            # Create signature using exact working method
            query_string = urlencode(sorted(params.items()))
            signature = hmac.new(
                self.secret_key.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params['signature'] = signature
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, data=params, timeout=30)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response: {e.response.text}")
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
        Place a new order
        
        Args:
            symbol: Trading pair (e.g., 'BTCPHP')
            side: 'BUY' or 'SELL'
            order_type: 'LIMIT', 'MARKET', etc.
            **kwargs: Additional parameters like quantity, price, timeInForce
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            **kwargs
        }
        return self._make_request('POST', '/openapi/v1/order', params, signed=True)
    
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