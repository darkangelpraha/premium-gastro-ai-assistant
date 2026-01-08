#!/usr/bin/env python3
"""
Bluejet Login and Explorer - Direct approach
"""
import subprocess
import json
import requests
from bs4 import BeautifulSoup
import sys

LOGIN_ITEM = "dr7o5x765zikuy52kdspkalone"
VAULT = "AI"

def get_creds():
    """Get credentials from 1Password"""
    cmd = ["/usr/local/bin/op", "item", "get", LOGIN_ITEM, "--vault", VAULT, "--format", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    url = data["urls"][0]["href"]
    username = None
    password = None

    for field in data["fields"]:
        if field.get("purpose") == "USERNAME":
            username = field.get("value")
        elif field.get("purpose") == "PASSWORD":
            password = field.get("value")

    return url, username, password

def login_and_explore():
    url, username, password = get_creds()
    print(f"🔐 Logging into {url}")
    print(f"   Username: {username}")

    session = requests.Session()

    # Get login page
    resp = session.get(url)
    soup = BeautifulSoup(resp.content, 'html.parser')

    # Find ALL input fields
    form = soup.find('form')
    if not form:
        print("❌ No form found")
        sys.exit(1)

    # Get form action
    action = form.get('action', '')
    if action:
        login_url = url.rstrip('/') + '/' + action.lstrip('/')
    else:
        login_url = url

    print(f"   Form action: {login_url}")

    # Build form data with ALL fields
    form_data = {}
    inputs = form.find_all('input')

    print(f"\n📝 Form fields found:")
    for inp in inputs:
        name = inp.get('name')
        value = inp.get('value', '')
        input_type = inp.get('type', 'text')
        if name:
            form_data[name] = value
            print(f"   {name} = '{value}' (type: {input_type})")

    # Now set username and password in the right fields
    for inp in inputs:
        name = inp.get('name', '')
        input_type = inp.get('type', '').lower()

        if input_type == 'password':
            form_data[name] = password
            print(f"\n✅ Set password in field: {name}")
        elif input_type == 'text' or 'user' in name.lower() or 'login' in name.lower():
            if not form_data.get(name) or form_data[name] == '':
                form_data[name] = username
                print(f"✅ Set username in field: {name}")

    # Submit
    print(f"\n🚀 Submitting login...")
    resp = session.post(login_url, data=form_data, allow_redirects=True)

    # Check result
    soup = BeautifulSoup(resp.content, 'html.parser')

    with open('/tmp/bluejet_logged_in.html', 'w', encoding='utf-8') as f:
        f.write(resp.text)

    print(f"\n📊 Response status: {resp.status_code}")
    print(f"📊 Final URL: {resp.url}")

    # Check if we're logged in
    if 'logout' in resp.text.lower() or 'odhlásit' in resp.text.lower():
        print("✅ LOGGED IN SUCCESSFULLY!")
    else:
        title = soup.find('title')
        if title:
            print(f"📌 Page title: {title.get_text()}")

        if 'přihlášení' in resp.text.lower():
            print("❌ Still on login page - login FAILED")
            # Show any error messages
            errors = soup.find_all(class_=lambda x: x and ('error' in x.lower() or 'alert' in x.lower()))
            if errors:
                print("\n⚠️  Error messages:")
                for err in errors:
                    print(f"   {err.get_text(strip=True)}")
            return False
        else:
            print("⚠️  Login status unclear, but we're on a different page")

    # Extract main content
    print("\n" + "="*60)
    print("BLUEJET DASHBOARD CONTENT")
    print("="*60)

    title = soup.find('title')
    if title:
        print(f"\n📌 {title.get_text(strip=True)}")

    # Find headings
    for h in soup.find_all(['h1', 'h2', 'h3'])[:20]:
        text = h.get_text(strip=True)
        if text:
            print(f"\n▶ {text}")

    # Find menu/nav items
    print("\n🗂️  NAVIGATION:")
    links = soup.find_all('a')
    seen = set()
    for link in links[:50]:
        text = link.get_text(strip=True)
        href = link.get('href', '')
        if text and 2 < len(text) < 60 and text not in seen:
            print(f"   • {text}")
            seen.add(text)

    print(f"\n📄 Full HTML saved to: /tmp/bluejet_logged_in.html")
    print("="*60)
    return True

if __name__ == "__main__":
    try:
        login_and_explore()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
