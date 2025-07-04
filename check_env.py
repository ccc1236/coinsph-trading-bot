import os

# Read the .env file directly
try:
    with open('.env', 'r') as f:
        content = f.read()
    print("=== RAW .env FILE CONTENT ===")
    print(repr(content))  # Shows exact characters including spaces/newlines
    print()
    print("=== LINES IN .env FILE ===")
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        print(f"Line {i}: {repr(line)}")
except Exception as e:
    print(f"Error reading .env file: {e}")

print()
print("=== CURRENT DIRECTORY ===")
print(f"Working directory: {os.getcwd()}")

print()
print("=== FILES IN DIRECTORY ===")
files = os.listdir('.')
for f in files:
    if f.startswith('.env'):
        print(f"Found: {f}")