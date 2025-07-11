# Quick test script
from dotenv import load_dotenv
import os

load_dotenv()
print("Key found:", bool(os.getenv('MARKETRAKER_VERIFICATION_KEY')))
print("Key preview:", os.getenv('MARKETRAKER_VERIFICATION_KEY')[:30] if os.getenv('MARKETRAKER_VERIFICATION_KEY') else "None")