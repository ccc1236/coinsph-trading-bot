import os
from dotenv import load_dotenv

print("=== BEFORE LOADING .env ===")
print(f"TRADING_SYMBOL = {os.getenv('TRADING_SYMBOL')}")
print(f"BASE_AMOUNT = {os.getenv('BASE_AMOUNT')}")

print("\n=== LOADING .env FILE ===")
result = load_dotenv()
print(f"load_dotenv() returned: {result}")

print("\n=== AFTER LOADING .env ===")
print(f"TRADING_SYMBOL = {os.getenv('TRADING_SYMBOL')}")
print(f"BASE_AMOUNT = {os.getenv('BASE_AMOUNT')}")

print("\n=== MANUAL FILE READING ===")
try:
    with open('.env', 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    print(f"Found: {key} = {value}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== TESTING DIRECT ASSIGNMENT ===")
# Manually set environment variables
os.environ['TRADING_SYMBOL'] = 'XRPPHP'
os.environ['BASE_AMOUNT'] = '100'

print(f"After manual setting:")
print(f"TRADING_SYMBOL = {os.getenv('TRADING_SYMBOL')}")
print(f"BASE_AMOUNT = {os.getenv('BASE_AMOUNT')}")