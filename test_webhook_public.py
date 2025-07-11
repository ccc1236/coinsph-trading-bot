import requests
import json

# Your public webhook URL
url = "https://daedd88d1e4e.ngrok-free.app/webhook/test"

# Test signal data
signal = {
    "type": "indicator",
    "data": {
        "trading_type": "Long",
        "buy_price": 2.45,
        "sell_price": 2.58,
        "risk": 4,
        "trading_pair": "XRP/USD",
        "percentage_change": 5.3,
        "market_direction": "Bull",
        "stoploss": 2.35,
        "leverage": 1,
        "buy_date": 1640995200,
        "sell_prediction_date": 1641081600
    }
}

print("🧪 Testing public webhook...")
response = requests.post(url, json=signal)
print(f"✅ Response: {response.status_code}")
print(f"📄 Body: {response.text}")