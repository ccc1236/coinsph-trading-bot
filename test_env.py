# test_env.py
import os
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.getenv('COINS_API_KEY')
secret_key = os.getenv('COINS_SECRET_KEY')

print(f"API Key found: {api_key is not None}")
print(f"Secret Key found: {secret_key is not None}")

if api_key:
    print(f"API Key starts with: {api_key[:10]}...")