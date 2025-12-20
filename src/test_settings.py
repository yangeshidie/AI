import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/settings"

def make_request(url, method="GET", data=None):
    try:
        req = urllib.request.Request(url, method=method)
        req.add_header('Content-Type', 'application/json')
        
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req.data = json_data
            
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode('utf-8'))
    except Exception as e:
        print(f"Request Error: {e}")
        return 500, {}

def test_save_config():
    print("Testing Save Config...")
    payload = {
        "name": "TestConfig",
        "base_url": "http://test.api/v1",
        "api_key": "sk-test-key-123"
    }
    status, response = make_request(f"{BASE_URL}/configs", "POST", payload)
    print(f"Status: {status}, Response: {response}")
    
    if status == 200:
        print("✅ Save Config Passed")
    else:
        print("❌ Save Config Failed")

def test_list_configs():
    print("\nTesting List Configs...")
    status, response = make_request(f"{BASE_URL}/configs", "GET")
    print(f"Status: {status}, Response: {response}")
    
    if status == 200 and "TestConfig" in response.get("configs", []):
        print("✅ List Configs Passed")
    else:
        print("❌ List Configs Failed")

def test_get_config():
    print("\nTesting Get Config...")
    status, response = make_request(f"{BASE_URL}/config/TestConfig", "GET")
    print(f"Status: {status}, Response: {response}")
    
    if status == 200 and response.get("base_url") == "http://test.api/v1":
        print("✅ Get Config Passed")
    else:
        print("❌ Get Config Failed")

if __name__ == "__main__":
    test_save_config()
    test_list_configs()
    test_get_config()
