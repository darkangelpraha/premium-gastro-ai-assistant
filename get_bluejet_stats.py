#!/usr/bin/env python3
"""
Get Bluejet Statistics
Retrieves counts and status information from Bluejet API
"""
import subprocess
import json
import requests
import sys

def get_credential(field_label):
    """Fetch credential from 1Password"""
    cmd = ["/usr/local/bin/op", "item", "get", "BlueJet API FULL",
           "--vault", "AI", "--fields", f"label={field_label}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None

def authenticate():
    """Authenticate with Bluejet API"""
    token_id = get_credential("BLUEJET_API_TOKEN_ID")
    token_hash = get_credential("BLUEJET_API_TOKEN_HASH")

    if not token_id or not token_hash:
        print("❌ Could not retrieve credentials from 1Password")
        sys.exit(1)

    auth_url = "https://czeco.bluejet.cz/api/v1/users/authenticate"
    response = requests.post(auth_url, json={
        "TokenID": token_id,
        "TokenHash": token_hash
    }, timeout=10)

    result = response.json()
    if result.get("succeeded"):
        return result.get("token")
    else:
        print(f"❌ Authentication failed: {result.get('message')}")
        sys.exit(1)

def get_count(token, evidence_no, name):
    """Get count of records for an evidence type"""
    url = f"https://czeco.bluejet.cz/api/v1/data?no={evidence_no}&offset=0&limit=1"
    headers = {"X-Token": token}

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        total = response.headers.get('X-Total-Count', '0')
        return int(total)
    else:
        return None

def get_offers_by_status(token):
    """Get offers grouped by status"""
    url = "https://czeco.bluejet.cz/api/v1/data?no=230&offset=0&limit=1000&fields=ID,Status"
    headers = {"X-Token": token}

    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code == 200:
        data = response.json()
        rows = data.get('dataObjectResult', {}).get('dataObjectRows', [])

        status_counts = {}
        for row in rows:
            fields = row.get('fields', {})
            status = fields.get('Status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts
    else:
        return {}

def main():
    print("🔐 Authenticating with Bluejet...")
    token = authenticate()
    print("✅ Authenticated successfully!\n")

    print("=" * 60)
    print("BLUEJET STATISTICS")
    print("=" * 60)

    # Get contacts count
    contacts = get_count(token, 222, "Contacts")
    if contacts is not None:
        print(f"\n👥 Contacts (Kontakty): {contacts:,}")

    # Get products count
    products = get_count(token, 217, "Products")
    if products is not None:
        print(f"📦 Products (Produkty): {products:,}")

    # Get offers count and status breakdown
    offers_total = get_count(token, 230, "Offers")
    if offers_total is not None:
        print(f"\n💼 Offers/Quotes (Nabídky): {offers_total:,}")

        print("\n   Status Breakdown:")
        status_counts = get_offers_by_status(token)
        if status_counts:
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   • {status}: {count:,}")
        else:
            print("   (Could not retrieve status breakdown)")

    # Additional useful stats
    print("\n" + "-" * 60)
    print("Additional Statistics:")
    print("-" * 60)

    companies = get_count(token, 225, "Companies")
    if companies is not None:
        print(f"🏢 Companies (Firmy): {companies:,}")

    orders = get_count(token, 321, "Orders")
    if orders is not None:
        print(f"📋 Orders (Objednávky): {orders:,}")

    invoices = get_count(token, 323, "Issued Invoices")
    if invoices is not None:
        print(f"🧾 Issued Invoices (Faktury vydané): {invoices:,}")

    print("\n" + "=" * 60)
    print("✅ Statistics retrieved successfully")
    print("=" * 60)

if __name__ == "__main__":
    main()
