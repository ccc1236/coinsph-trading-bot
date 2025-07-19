import requests
response = requests.post('http://localhost:8000/toggle-test-mode')
print(response.json())