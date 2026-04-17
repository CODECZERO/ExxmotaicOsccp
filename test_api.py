import requests
import time
import json
import random

BASE_URL = "http://localhost:5050/api"

print("====================================")
print("Testing ExxmotaicOSCCP API Endpoints")
print("====================================\n")

def check_endpoint(name, url, method="GET", payload=None):
    try:
        print(f"Testing {name} ({method} {url})...")
        if method == "GET":
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, json=payload, timeout=5)
            
        if response.status_code == 200:
            print(f"✅ Success! ({response.status_code})")
            if response.headers.get('content-type') == 'application/json':
                print(f"   Response snippet: {str(response.json())[:150]}...")
            else:
                print(f"   Response snippet: {response.text[:150]}...")
        else:
            print(f"❌ Failed! Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to API: {e}")
    print("\n------------------------------------\n")

# 1. Test Health Endpoint
check_endpoint("Health Check", f"{BASE_URL}/health")

# 2. Test fetching all chargers
check_endpoint("List Chargers", f"{BASE_URL}/chargers")

# 3. Test fetching single charger
check_endpoint("Get Charger DEMO-DC-001", f"{BASE_URL}/chargers/DEMO-DC-001")

# 4. Test fetching sessions
check_endpoint("List Sessions for DEMO-DC-001", f"{BASE_URL}/chargers/DEMO-DC-001/sessions")

# 5. Fetch commands history
check_endpoint("Command History for DEMO-DC-001", f"{BASE_URL}/chargers/DEMO-DC-001/commands")

# 6. Simulate a remote command (Unlock Connector)
fake_payload = {"connector_id": 1}
check_endpoint("Remote Unlock Command", f"{BASE_URL}/chargers/DEMO-DC-001/unlock", method="POST", payload=fake_payload)

print("Finished testing endpoints.")
