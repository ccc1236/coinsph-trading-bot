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
    
    def _generate_signature(self, query_string):
        """Generate HMAC SHA256 signature exactly as Coins.ph expects"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method, endpoint, params=None, signed=False):
        """Make API request with proper authentication"""
        params = params or {}
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['recvWindow'] = 5000
            
            # Create query string exactly as in Coins.ph documentation
            # Sort parameters alphabetically (excluding signature)
            sorted_params = sorted(params.items())
            query_string = urlencode(sorted_params)
            
            # Generate signature
            signature = self._generate_signature(query_string)
            params['signature'] = signature
            
            # Debug print (remove after testing)
            print(f"DEBUG - Query string: {query_string}")
            print(f"DEBUG - Signature: {signature}")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method == 'POST':
                response = self.session.post(url, data=params, timeout=30)
            elif method == 'DELETE':
                response = self.session.delete(url, params=params, timeout=30)
            
            # Debug print response
            print(f"DEBUG - Response status: {response.status_code}")
            print(f"DEBUG - Response: {response.text}")
            
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
    
    def get_current_price(self, symbol):
        """Get current price for symbol"""
        ticker = self.get_ticker_price(symbol)
        return float(ticker['price'])
    
    # ========== AUTHENTICATED ENDPOINTS ==========
    
    def get_account_info(self):
        """Get current account information"""
        return self._make_request('GET', '/openapi/v1/account', signed=True)
    
    def get_crypto_accounts(self, currency=None):
        """Get crypto account balances"""
        params = {'currency': currency} if currency else {}
        return self._make_request('GET', '/openapi/account/v3/crypto-accounts', params, signed=True)
    
    def get_balance(self, asset=None):
        """Get account balance for specific asset or all"""
        try:
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
                for b in balances if float(b['free']) + float(b['locked']) > 0
            ]
        except Exception as e:
            print(f"Error getting balance: {e}")
            return []
    
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
    
    def get_open_orders(self, symbol=None):
        """Get all open orders"""
        params = {'symbol': symbol} if symbol else {}
        return self._make_request('GET', '/openapi/v1/openOrders', params, signed=True)