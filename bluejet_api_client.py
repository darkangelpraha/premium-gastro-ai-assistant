#!/usr/bin/env python3
"""
Bluejet REST API Client
Uses the official Bluejet REST API with authentication token
"""
import subprocess
import json
import requests

API_ITEM = "BlueJet API FULL"
VAULT = "AI"

def get_credentials():
    """Fetch credentials from 1Password"""
    cmd = ["/usr/local/bin/op", "item", "get", API_ITEM, "--vault", VAULT, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    # Debug: Show all available fields
    print(f"\n🔍 DEBUG: All fields in 1Password item:")
    for field in data.get("fields", []):
        label = field.get("label", "")
        field_id = field.get("id", "")
        has_value = "value" in field and field["value"]
        print(f"   • {label} (id: {field_id}, has_value: {has_value})")

    # Extract fields - use exact names from 1Password
    creds = {}
    for field in data["fields"]:
        label = field.get("label", "")
        value = field.get("value")

        if not value:
            continue

        # Try both label and id
        if label == "BLUEJET_API_TOKEN_ID" or field.get("id") == "BLUEJET_API_TOKEN_ID":
            creds["api_token_id"] = value
        elif label == "BLUEJET_API_TOKEN_HASH" or field.get("id") == "BLUEJET_API_TOKEN_HASH":
            creds["api_token_hash"] = value
        elif "token" in label.lower() and "id" in label.lower():
            creds["api_token_id"] = value
        elif "token" in label.lower() and "hash" in label.lower():
            creds["api_token_hash"] = value

    return creds

class BluejetAPIClient:
    def __init__(self):
        self.base_url = "https://czeco.bluejet.cz"
        self.session = requests.Session()
        self.authenticated = False

    def authenticate(self):
        """Authenticate with Bluejet REST API"""
        creds = get_credentials()

        print(f"🔐 Authenticating with Bluejet API...")
        print(f"   Token ID: {creds.get('token_id', 'Not found')}")
        print(f"   API Token ID: {'Found' if creds.get('api_token_id') else 'Not found'}")
        print(f"   API Token Hash: {'Found' if creds.get('api_token_hash') else 'Not found'}")

        auth_url = f"{self.base_url}/api/v1/users/authenticate"

        # Bluejet API requires TokenID and TokenHash
        if creds.get('api_token_id') and creds.get('api_token_hash'):
            try:
                auth_data = {
                    "TokenID": creds['api_token_id'],
                    "TokenHash": creds['api_token_hash']
                }

                resp = self.session.post(auth_url, json=auth_data)
                print(f"\n📊 API Token auth response: {resp.status_code}")

                if resp.status_code == 200:
                    print("✅ Authenticated with API tokens!")
                    self.authenticated = True
                    return True
                else:
                    print(f"❌ API token authentication failed: {resp.text}")
                    return False

            except Exception as e:
                print(f"❌ API token authentication error: {e}")
                return False
        else:
            print("❌ Missing API TokenID or TokenHash in 1Password")
            print("   Please ensure these fields are filled in 1Password item")
            return False

    def get_data(self, endpoint=""):
        """Get data from Bluejet API"""
        if not self.authenticated:
            print("❌ Not authenticated")
            return None

        url = f"{self.base_url}/api/v1/data"
        if endpoint:
            url = f"{url}/{endpoint}"

        print(f"\n📥 GET {url}")

        try:
            resp = self.session.get(url)
            print(f"📊 Response: {resp.status_code}")

            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"⚠️  Error: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def explore(self):
        """Explore available API endpoints and data"""
        print("\n" + "="*60)
        print("🔍 EXPLORING BLUEJET API")
        print("="*60)

        # Try to get general data
        data = self.get_data()

        if data:
            print("\n✅ API Response received!")
            print(f"📊 Response type: {type(data)}")

            if isinstance(data, dict):
                print(f"📋 Keys available: {list(data.keys())}")

                for key, value in list(data.items())[:10]:
                    print(f"\n▶ {key}:")
                    if isinstance(value, list):
                        print(f"   Type: List with {len(value)} items")
                        if len(value) > 0:
                            print(f"   First item: {value[0]}")
                    elif isinstance(value, dict):
                        print(f"   Type: Dict with keys: {list(value.keys())}")
                    else:
                        print(f"   Value: {value}")

            elif isinstance(data, list):
                print(f"📋 List with {len(data)} items")
                if len(data) > 0:
                    print(f"\nFirst item:")
                    print(json.dumps(data[0], indent=2))

        print("\n" + "="*60)

def main():
    print("🚀 Bluejet REST API Client")
    print("="*60)

    client = BluejetAPIClient()

    if client.authenticate():
        client.explore()

        print("\n✅ API exploration complete!")
        print("\n📚 Available endpoints:")
        print("   • GET  /api/v1/data")
        print("   • POST /api/v1/data/insertorupdate")
        print("   • POST /api/v1/data/remove")
    else:
        print("\n❌ Failed to authenticate")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
