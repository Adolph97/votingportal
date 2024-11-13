import requests
import time
import os

def ping_server():
    url = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:10000')
    while True:
        try:
            response = requests.get(f"{url}/ping")
            print(f"Ping status: {response.status_code}")
        except Exception as e:
            print(f"Ping failed: {str(e)}")
        time.sleep(600)  # Ping every 10 minutes

if __name__ == "__main__":
    ping_server() 