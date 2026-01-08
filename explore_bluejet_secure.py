#!/usr/bin/env python3
"""
Bluejet Explorer - SECURE VERSION
Fetches credentials from 1Password on-demand, NEVER stores them in files
"""

import subprocess
import json
import requests
from bs4 import BeautifulSoup

# 1Password item IDs (safe to hardcode - these are just IDs, not secrets)
API_KEY_ITEM = "xiddgpu4fnwdvx37xiwjdzz3de"
LOGIN_ITEM = "dr7o5x765zikuy52kdspkalone"
VAULT = "AI"

def get_from_1password(item_id, field_path):
    """
    Fetch a value from 1Password using op CLI
    SECURITY: Credentials are fetched on-demand and never stored
    """
    try:
        cmd = ["op", "item", "get", item_id, "--vault", VAULT, "--fields", field_path]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching from 1Password: {e}")
        return None

class BluejetExplorerSecure:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = None
        self.logged_in = False

    def initialize(self):
        """Fetch base URL from 1Password"""
        print("🔐 Fetching credentials from 1Password...")

        # Get URLs from login item
        try:
            cmd = ["op", "item", "get", LOGIN_ITEM, "--vault", VAULT, "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            item_data = json.loads(result.stdout)

            # Extract URL
            if "urls" in item_data and len(item_data["urls"]) > 0:
                self.base_url = item_data["urls"][0]["href"]
                print(f"✅ Base URL retrieved: {self.base_url}")
                return True
            else:
                print("❌ No URL found in 1Password item")
                return False
        except Exception as e:
            print(f"❌ Error initializing: {e}")
            return False

    def login(self):
        """Log in using credentials from 1Password"""
        if not self.base_url:
            print("❌ Base URL not initialized")
            return False

        print(f"🔐 Logging in to {self.base_url}...")

        # Fetch username and password from 1Password (on-demand, not stored)
        username = get_from_1password(LOGIN_ITEM, "username")
        password = get_from_1password(LOGIN_ITEM, "password")

        if not username or not password:
            print("❌ Failed to fetch credentials from 1Password")
            return False

        try:
            # Get login page
            login_page = self.session.get(self.base_url)
            soup = BeautifulSoup(login_page.content, 'html.parser')

            # Find login form
            form = soup.find('form')
            if not form:
                print("❌ Could not find login form")
                return False

            # Extract form details
            action = form.get('action', '')
            login_url = self.base_url + action if action else self.base_url

            inputs = form.find_all('input')
            form_data = {}

            # Collect all form fields
            for input_tag in inputs:
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                if name:
                    form_data[name] = value

            # Find username and password fields
            username_field = None
            password_field = None

            for input_tag in inputs:
                input_type = input_tag.get('type', '').lower()
                name = input_tag.get('name', '')

                if input_type == 'text' or 'user' in name.lower():
                    username_field = name
                elif input_type == 'password':
                    password_field = name

            if username_field and password_field:
                form_data[username_field] = username
                form_data[password_field] = password

                # Submit login
                response = self.session.post(login_url, data=form_data, allow_redirects=True)

                # Clear sensitive variables immediately
                del username, password, form_data

                if response.status_code == 200:
                    if 'logout' in response.text.lower() or 'odhlásit' in response.text.lower():
                        print("✅ Successfully logged in!")
                        self.logged_in = True
                        return True
                    else:
                        # Save response for analysis (no credentials in this)
                        with open('/tmp/bluejet_response.html', 'w', encoding='utf-8') as f:
                            f.write(response.text)
                        print("✅ Login submitted, response saved to /tmp/bluejet_response.html")
                        self.logged_in = True
                        return True
                else:
                    print(f"❌ Login failed with status: {response.status_code}")
                    return False
            else:
                print("❌ Could not identify form fields")
                return False

        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def explore(self):
        """Explore Bluejet and return high-level overview"""
        if not self.logged_in:
            print("❌ Not logged in")
            return None

        print("\n📊 Exploring Bluejet...")

        try:
            response = self.session.get(self.base_url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Save HTML for detailed analysis
            with open('/tmp/bluejet_dashboard.html', 'w', encoding='utf-8') as f:
                f.write(response.text)

            print("✅ Dashboard saved to /tmp/bluejet_dashboard.html")

            # Extract high-level structure
            print("\n" + "="*60)
            print("🔍 BLUEJET HIGH-LEVEL OVERVIEW")
            print("="*60)

            # Title
            title = soup.find('title')
            if title:
                print(f"\n📌 Page: {title.get_text(strip=True)}")

            # Main headings
            headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3']) if h.get_text(strip=True)]
            if headings:
                print(f"\n📑 Sections found:")
                for h in headings[:15]:
                    print(f"   • {h}")

            # Menu items
            links = soup.find_all('a')
            menu_items = []
            for link in links:
                text = link.get_text(strip=True)
                href = link.get('href', '')
                if text and len(text) > 2 and len(text) < 50:
                    menu_items.append({'text': text, 'href': href})

            if menu_items:
                print(f"\n🗂️  Navigation/Menu items ({len(menu_items)} found):")
                seen = set()
                for item in menu_items[:30]:
                    if item['text'] not in seen:
                        print(f"   • {item['text']}")
                        seen.add(item['text'])

            # Tables
            tables = soup.find_all('table')
            if tables:
                print(f"\n📊 Data tables: {len(tables)} found")

            # Forms
            forms = soup.find_all('form')
            if forms:
                print(f"\n📝 Forms: {len(forms)} found")

            print("\n" + "="*60)

            return soup

        except Exception as e:
            print(f"❌ Exploration error: {e}")
            return None

def main():
    print("🚀 SECURE Bluejet Explorer")
    print("🔒 All credentials fetched from 1Password on-demand")
    print("="*60)

    explorer = BluejetExplorerSecure()

    if not explorer.initialize():
        print("\n❌ Initialization failed")
        return

    if not explorer.login():
        print("\n❌ Login failed")
        return

    explorer.explore()

    print("\n✅ Exploration complete!")
    print("\n📁 Files created:")
    print("   • /tmp/bluejet_dashboard.html - Full dashboard HTML")
    print("\n🔒 Security: No credentials stored in any files")

if __name__ == "__main__":
    main()
