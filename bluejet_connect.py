#!/usr/bin/env python3
"""
Bluejet API Connector
Authenticates with Bluejet REST API using credentials from 1Password
"""
import subprocess
import json
import requests
import sys

API_ITEM = "BlueJet API FULL"
VAULT = "AI"
BASE_URL = "https://czeco.bluejet.cz"

def get_credential_from_1password(field_label):
    """Fetch a specific field from 1Password"""
    try:
        # Try using field label directly
        cmd = ["/usr/local/bin/op", "item", "get", API_ITEM,
               "--vault", VAULT, "--fields", f"label={field_label}"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()

        # If that didn't work, get full JSON and search
        cmd = ["/usr/local/bin/op", "item", "get", API_ITEM,
               "--vault", VAULT, "--format", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        for field in data.get("fields", []):
            label = field.get("label", "")
            if label == field_label and field.get("value"):
                return field.get("value")

        return None
    except Exception as e:
        print(f"❌ Error fetching {field_label}: {e}")
        return None

def authenticate():
    """Authenticate with Bluejet API"""
    print("🔐 Fetching credentials from 1Password...")

    # Get credentials
    token_id = get_credential_from_1password("BLUEJET_API_TOKEN_ID")
    token_hash = get_credential_from_1password("BLUEJET_API_TOKEN_HASH")

    if not token_id:
        print("❌ BLUEJET_API_TOKEN_ID not found in 1Password")
        return None

    if not token_hash:
        print("❌ BLUEJET_API_TOKEN_HASH not found in 1Password")
        return None

    print("✅ Credentials retrieved from 1Password")
    print(f"   Token ID: {token_id[:10]}...")
    print(f"   Token Hash: {token_hash[:10]}...")

    # Authenticate
    auth_url = f"{BASE_URL}/api/v1/users/authenticate"
    auth_data = {
        "TokenID": token_id,
        "TokenHash": token_hash
    }

    print(f"\n📤 Authenticating with {auth_url}...")

    try:
        session = requests.Session()
        response = session.post(auth_url, json=auth_data, timeout=10)

        print(f"📊 Status: {response.status_code}")

        result = response.json()

        if result.get("succeeded"):
            print("✅ Authentication SUCCESSFUL!")
            print(f"🎫 Session token received: {result.get('token', '')[:20]}...")
            return session, result.get('token')
        else:
            print(f"❌ Authentication FAILED")
            print(f"   Message: {result.get('message', 'No message')}")
            return None

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def explore_api(session):
    """Explore available API endpoints"""
    print("\n" + "="*60)
    print("🔍 EXPLORING BLUEJET API")
    print("="*60)

    endpoints = [
        "/api/v1/data",
        "/api/v1/data/customers",
        "/api/v1/data/products",
        "/api/v1/data/orders",
        "/api/v1/data/invoices"
    ]

    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        print(f"\n📥 GET {endpoint}")

        try:
            response = session.get(url, timeout=10)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   ✅ List with {len(data)} items")
                        if len(data) > 0:
                            print(f"   First item keys: {list(data[0].keys())}")
                    elif isinstance(data, dict):
                        print(f"   ✅ Dict with keys: {list(data.keys())}")
                except:
                    print(f"   ✅ Response: {response.text[:100]}")
            else:
                print(f"   ⚠️  {response.text[:100]}")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\n" + "="*60)

def main():
    print("🚀 Bluejet API Connector")
    print("="*60)

    result = authenticate()

    if result:
        session, token = result
        explore_api(session)
        print("\n✅ API exploration complete!")
    else:
        print("\n❌ Failed to connect to Bluejet API")
        sys.exit(1)

if __name__ == "__main__":
    main()
