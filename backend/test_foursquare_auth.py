"""
Simple test to verify Foursquare API authentication is working.
Tests both authentication formats (with and without Bearer).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Add parent directory to path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

load_dotenv()

api_key = os.getenv("FOURSQUARE_API_KEY")
if not api_key:
    print("ERROR: FOURSQUARE_API_KEY not set")
    sys.exit(1)

api_key = api_key.strip()

# Test simple API call
url = "https://api.foursquare.com/v3/places/search"
params = {
    "query": "Starbucks",
    "near": "New York, NY",
    "limit": 1
}

print("Testing Foursquare API authentication...")
print(f"URL: {url}")
print(f"API Key (first 20 chars): {api_key[:20]}...")
print(f"API Key length: {len(api_key)}")
print(f"Params: {params}")
print("=" * 70)

# Test 1: Without Bearer (Legacy format)
print("\n[Test 1] Trying WITHOUT Bearer prefix (Legacy v3 format)...")
headers1 = {
    "Authorization": api_key,
    "Accept": "application/json",
    "X-Places-Api-Version": "1970-01-01"
}
print(f"Authorization header: {headers1['Authorization'][:30]}...")

try:
    response1 = requests.get(url, headers=headers1, params=params, timeout=10)
    print(f"Status Code: {response1.status_code}")
    
    if response1.status_code == 200:
        data = response1.json()
        print(f"✓ SUCCESS! Response has {len(data.get('results', []))} results")
    else:
        print(f"✗ FAILED: {response1.status_code}")
        print(f"Response: {response1.text[:200]}")
        try:
            error_data = response1.json()
            print(f"Error JSON: {error_data}")
        except:
            pass
except Exception as e:
    print(f"✗ EXCEPTION: {e}")

# Test 2: With Bearer (New format)
print("\n[Test 2] Trying WITH Bearer prefix (Service Key format)...")
headers2 = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json",
    "X-Places-Api-Version": "1970-01-01"
}
print(f"Authorization header: Bearer {headers2['Authorization'].split('Bearer ')[1][:30]}...")

try:
    response2 = requests.get(url, headers=headers2, params=params, timeout=10)
    print(f"Status Code: {response2.status_code}")
    
    if response2.status_code == 200:
        data = response2.json()
        print(f"✓ SUCCESS! Response has {len(data.get('results', []))} results")
    else:
        print(f"✗ FAILED: {response2.status_code}")
        print(f"Response: {response2.text[:200]}")
        try:
            error_data = response2.json()
            print(f"Error JSON: {error_data}")
        except:
            pass
except Exception as e:
    print(f"✗ EXCEPTION: {e}")

print("\n" + "=" * 70)
print("Authentication test completed.")

