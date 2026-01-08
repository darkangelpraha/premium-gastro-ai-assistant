#!/usr/bin/env python3
"""
Bluejet REST API Client
Uses the official Bluejet REST API with authentication token
"""
import subprocess
import json
import requests

LOGIN_ITEM = "dr7o5x765zikuy52kdspkalone"
VAULT = "AI"

def get_credentials():
    """Fetch credentials from 1Password"""
    cmd = ["/usr/local/bin/op", "item", "get", LOGIN_ITEM, "--vault", VAULT, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    # Extract fields
    creds = {}
    for field in data["fields"]:
        label = field.get("label", "").lower()
        value = field.get("value")

        if "tokenid" in label:
            creds["token_id"] = value
        elif field.get("purpose") == "USERNAME":
            creds["username"] = value
        elif field.get("purpose") == "PASSWORD":
            creds["password"] = value

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
        print(f"   Username: {creds['username']}")
        print(f"   Token ID: {creds.get('token_id', 'Not found')}")

        auth_url = f"{self.base_url}/api/v1/users/authenticate"

        # Try authentication with token
        if creds.get('token_id'):
            headers = {
                "Authorization": f"Bearer {creds['token_id']}",
                "Content-Type": "application/json"
            }

            try:
                resp = self.session.get(auth_url, headers=headers)
                print(f"\n📊 Auth response: {resp.status_code}")

                if resp.status_code == 200:
                    print("✅ Authenticated with token!")
                    self.session.headers.update(headers)
                    self.authenticated = True
                    return True
                else:
                    print(f"⚠️  Token auth failed, trying username/password...")
            except Exception as e:
                print(f"⚠️  Token auth error: {e}")

        # Try username/password authentication
        try:
            auth_data = {
                "username": creds['username'],
                "password": creds['password']
            }

            resp = self.session.post(auth_url, json=auth_data)
            print(f"📊 Username/password response: {resp.status_code}")

            if resp.status_code == 200:
                result = resp.json()
                print("✅ Authenticated with username/password!")

                # Store any returned token
                if 'token' in result:
                    self.session.headers.update({
                        "Authorization": f"Bearer {result['token']}"
                    })

                self.authenticated = True
                return True
            else:
                print(f"❌ Authentication failed: {resp.text}")
                return False

        except Exception as e:
            print(f"❌ Authentication error: {e}")
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
