#!/usr/bin/env python3
"""
Test Bluejet API Connection
This script tests the connection to Bluejet REST API
"""
import requests
import json
import os

# Credentials - these should come from 1Password in production
# For testing from container, we need the actual values
BLUEJET_API_TOKEN_ID = os.getenv('BLUEJET_API_TOKEN_ID', '')
BLUEJET_API_TOKEN_HASH = os.getenv('BLUEJET_API_TOKEN_HASH', '')

def test_connection():
    """Test connection to Bluejet API"""
    base_url = "https://czeco.bluejet.cz"
    auth_url = f"{base_url}/api/v1/users/authenticate"

    print("🔐 Testing Bluejet API Connection")
    print(f"📍 URL: {auth_url}")
    print(f"🔑 Token ID provided: {'Yes' if BLUEJET_API_TOKEN_ID else 'No'}")
    print(f"🔑 Token Hash provided: {'Yes' if BLUEJET_API_TOKEN_HASH else 'No'}")

    if not BLUEJET_API_TOKEN_ID or not BLUEJET_API_TOKEN_HASH:
        print("\n❌ Missing credentials")
        print("   Set BLUEJET_API_TOKEN_ID and BLUEJET_API_TOKEN_HASH environment variables")
        return False

    # Prepare authentication data
    auth_data = {
        "TokenID": BLUEJET_API_TOKEN_ID,
        "TokenHash": BLUEJET_API_TOKEN_HASH
    }

    print(f"\n📤 Sending authentication request...")

    try:
        response = requests.post(auth_url, json=auth_data, timeout=10)

        print(f"📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("\n✅ Authentication SUCCESSFUL!")
            print(f"📄 Response data:")
            try:
                data = response.json()
                print(json.dumps(data, indent=2))
            except:
                print(response.text[:500])
            return True
        else:
            print(f"\n❌ Authentication FAILED")
            print(f"📄 Response:")
            print(response.text[:500])
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
