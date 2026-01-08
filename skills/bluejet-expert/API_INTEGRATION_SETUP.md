# Bluejet API Integration with Claude

This guide shows you how to connect Claude to Bluejet's API so Claude can actually READ and WRITE data, not just guide you through the UI.

---

## 🎯 What This Enables

With API integration, Claude can:

✅ **Read data from Bluejet**:
- Customer information
- Order history
- Product catalog
- Reports and analytics
- Inventory levels

✅ **Write data to Bluejet**:
- Create orders
- Update customer records
- Add products
- Generate reports
- Trigger workflows

✅ **Automate tasks**:
- Daily report generation
- Data syncing with Supabase
- Order notifications
- Inventory alerts

---

## 🔐 Step 1: Get API Credentials from 1Password

### Retrieve from 1Password:

1. Open **1Password**
2. Search for **"Bluejet"** or **"Bluejet API"**
3. You should find:
   - **API Key** or **API Token**
   - **API Secret** (if applicable)
   - **API Base URL** (e.g., `https://api.bluejet.com/v1`)
   - **Workspace ID** or **Account ID** (if applicable)

### What You Need:

```
BLUEJET_API_KEY=your_api_key_here
BLUEJET_API_SECRET=your_api_secret_here (if applicable)
BLUEJET_API_BASE_URL=https://api.bluejet.com/v1
BLUEJET_WORKSPACE_ID=your_workspace_id (if applicable)
```

---

## 🔧 Step 2: Add to Environment Variables

### Update `.env` File:

1. Open `/home/user/premium-gastro-ai-assistant/.env`

2. Add Bluejet API credentials:

```bash
# Bluejet API Configuration
BLUEJET_API_KEY=your_actual_key_from_1password
BLUEJET_API_SECRET=your_actual_secret_from_1password
BLUEJET_API_BASE_URL=https://api.bluejet.com/v1
BLUEJET_WORKSPACE_ID=your_workspace_id

# If Bluejet uses OAuth instead:
BLUEJET_CLIENT_ID=your_client_id
BLUEJET_CLIENT_SECRET=your_client_secret
BLUEJET_REFRESH_TOKEN=your_refresh_token
```

3. **Important**: Never commit `.env` to Git!
   - Already in `.gitignore` ✅
   - Keep credentials secure

---

## 📚 Step 3: Understand Bluejet API

### Find Bluejet API Documentation:

**Look for:**
- Developer portal: Usually `developers.bluejet.com` or similar
- API docs in Bluejet app: Settings → Integrations → API
- Support documentation
- Swagger/OpenAPI docs

**Document the key endpoints YOU need:**

```markdown
## Bluejet API Endpoints (Your Use Cases)

### Authentication
- Method: [Bearer Token / OAuth / API Key in header]
- Header: [Authorization: Bearer {token}]

### Common Endpoints:

#### Get Customer List
- Endpoint: GET /customers
- Parameters: ?limit=100&page=1
- Response: Array of customer objects

#### Get Single Customer
- Endpoint: GET /customers/{id}
- Response: Customer object with full details

#### Create Order
- Endpoint: POST /orders
- Body: {customer_id, products[], total, etc.}
- Response: Created order object

#### Get Orders
- Endpoint: GET /orders
- Parameters: ?start_date=2026-01-01&end_date=2026-01-31
- Response: Array of orders

#### Update Inventory
- Endpoint: PATCH /products/{id}/inventory
- Body: {quantity: 100}
- Response: Updated product

[Add more endpoints as you discover them]
```

---

## 💻 Step 4: Create Python Integration Module

Create a new file for Bluejet API interactions:

### File: `bluejet_api.py`

```python
"""
Bluejet API Integration Module
Handles all API calls to Bluejet platform
"""

import os
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BluejetAPI:
    """
    Bluejet API client for Premium Gastro
    """

    def __init__(self):
        self.api_key = os.getenv('BLUEJET_API_KEY')
        self.api_secret = os.getenv('BLUEJET_API_SECRET')
        self.base_url = os.getenv('BLUEJET_API_BASE_URL', 'https://api.bluejet.com/v1')
        self.workspace_id = os.getenv('BLUEJET_WORKSPACE_ID')

        if not self.api_key:
            raise ValueError("BLUEJET_API_KEY not found in environment variables")

        # Set up session with authentication
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'X-Workspace-ID': self.workspace_id or ''
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make API request to Bluejet

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., '/customers')
            **kwargs: Additional arguments for requests library

        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {response.text}")
            raise
        except Exception as e:
            print(f"Error making request to Bluejet: {e}")
            raise

    # ==================== CUSTOMER METHODS ====================

    def get_customers(self, limit: int = 100, page: int = 1) -> List[Dict]:
        """Get list of customers"""
        params = {'limit': limit, 'page': page}
        response = self._request('GET', '/customers', params=params)
        return response.get('data', [])

    def get_customer(self, customer_id: str) -> Dict:
        """Get single customer by ID"""
        return self._request('GET', f'/customers/{customer_id}')

    def create_customer(self, customer_data: Dict) -> Dict:
        """
        Create new customer

        Args:
            customer_data: Dict with customer info
                {
                    'name': 'Restaurant Name',
                    'email': 'contact@restaurant.com',
                    'phone': '+420123456789',
                    'address': {...}
                }
        """
        return self._request('POST', '/customers', json=customer_data)

    def update_customer(self, customer_id: str, updates: Dict) -> Dict:
        """Update existing customer"""
        return self._request('PATCH', f'/customers/{customer_id}', json=updates)

    # ==================== ORDER METHODS ====================

    def get_orders(self,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   customer_id: Optional[str] = None) -> List[Dict]:
        """
        Get orders with optional filters

        Args:
            start_date: ISO format date (e.g., '2026-01-01')
            end_date: ISO format date
            customer_id: Filter by customer
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if customer_id:
            params['customer_id'] = customer_id

        response = self._request('GET', '/orders', params=params)
        return response.get('data', [])

    def get_order(self, order_id: str) -> Dict:
        """Get single order by ID"""
        return self._request('GET', f'/orders/{order_id}')

    def create_order(self, order_data: Dict) -> Dict:
        """
        Create new order

        Args:
            order_data: Dict with order info
                {
                    'customer_id': 'cust_123',
                    'products': [
                        {'product_id': 'prod_456', 'quantity': 2, 'price': 1500},
                        {'product_id': 'prod_789', 'quantity': 1, 'price': 3000}
                    ],
                    'shipping_address': {...},
                    'notes': 'Delivery instructions...'
                }
        """
        return self._request('POST', '/orders', json=order_data)

    def update_order_status(self, order_id: str, status: str) -> Dict:
        """
        Update order status

        Args:
            order_id: Order ID
            status: New status (e.g., 'processing', 'shipped', 'delivered')
        """
        return self._request('PATCH', f'/orders/{order_id}',
                           json={'status': status})

    # ==================== PRODUCT METHODS ====================

    def get_products(self, category: Optional[str] = None) -> List[Dict]:
        """Get product catalog"""
        params = {'category': category} if category else {}
        response = self._request('GET', '/products', params=params)
        return response.get('data', [])

    def get_product(self, product_id: str) -> Dict:
        """Get single product by ID"""
        return self._request('GET', f'/products/{product_id}')

    def update_product_inventory(self, product_id: str, quantity: int) -> Dict:
        """Update product inventory quantity"""
        return self._request('PATCH', f'/products/{product_id}/inventory',
                           json={'quantity': quantity})

    # ==================== REPORT METHODS ====================

    def get_sales_report(self, start_date: str, end_date: str) -> Dict:
        """
        Get sales report for date range

        Args:
            start_date: ISO format (e.g., '2026-01-01')
            end_date: ISO format
        """
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'report_type': 'sales'
        }
        return self._request('GET', '/reports/sales', params=params)

    def get_inventory_report(self) -> Dict:
        """Get current inventory status report"""
        return self._request('GET', '/reports/inventory')

    # ==================== UTILITY METHODS ====================

    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            # Try to get current user/account info
            response = self._request('GET', '/account')
            print("✅ Bluejet API connection successful!")
            print(f"Connected to workspace: {response.get('workspace_name', 'Unknown')}")
            return True
        except Exception as e:
            print(f"❌ Bluejet API connection failed: {e}")
            return False


# ==================== USAGE EXAMPLES ====================

def example_usage():
    """Example of how to use the Bluejet API"""

    # Initialize API client
    api = BluejetAPI()

    # Test connection
    if not api.test_connection():
        print("Failed to connect to Bluejet API")
        return

    # Get customers
    customers = api.get_customers(limit=10)
    print(f"Found {len(customers)} customers")

    # Get orders from last month
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    orders = api.get_orders(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )
    print(f"Found {len(orders)} orders in last 30 days")

    # Get products
    products = api.get_products()
    print(f"Found {len(products)} products in catalog")


if __name__ == "__main__":
    example_usage()
```

---

## 🤖 Step 5: Integrate with Claude

### Update Bluejet Expert Skill

Add this section to `skills/bluejet-expert/SKILL.md`:

```markdown
## 🔌 API Integration

You have access to the Bluejet API via Python. Use the `BluejetAPI` class to:

### Available Methods:

**Customers:**
- `api.get_customers()` - List all customers
- `api.get_customer(customer_id)` - Get specific customer
- `api.create_customer(data)` - Create new customer
- `api.update_customer(customer_id, updates)` - Update customer

**Orders:**
- `api.get_orders(start_date, end_date, customer_id)` - List orders
- `api.get_order(order_id)` - Get specific order
- `api.create_order(order_data)` - Create new order
- `api.update_order_status(order_id, status)` - Update order

**Products:**
- `api.get_products(category)` - List products
- `api.get_product(product_id)` - Get specific product
- `api.update_product_inventory(product_id, quantity)` - Update inventory

**Reports:**
- `api.get_sales_report(start_date, end_date)` - Sales report
- `api.get_inventory_report()` - Inventory status

### Example Usage with Claude:

When user asks: "Show me orders from last week"

You should:
1. Calculate the date range
2. Use API to fetch orders:
   ```python
   from bluejet_api import BluejetAPI
   from datetime import datetime, timedelta

   api = BluejetAPI()

   end_date = datetime.now()
   start_date = end_date - timedelta(days=7)

   orders = api.get_orders(
       start_date=start_date.strftime('%Y-%m-%d'),
       end_date=end_date.strftime('%Y-%m-%d')
   )

   print(f"Found {len(orders)} orders:")
   for order in orders:
       print(f"- Order #{order['id']}: {order['customer_name']} - ${order['total']}")
   ```
3. Format results for user
4. Offer analysis or next steps
```

---

## 🔄 Step 6: Create N8n Integration

### N8n Workflow: Bluejet → Claude → Action

Create a workflow that:

1. **Trigger**: New order in Bluejet (webhook)
2. **Fetch Details**: Call Bluejet API for order details
3. **Claude Analysis**: Send to Claude for processing
   - Check if VIP customer
   - Calculate priority
   - Draft confirmation email
   - Identify any issues
4. **Take Action**:
   - Update Supabase CRM
   - Create task in Asana if needed
   - Send email via Missive
   - Update Notion

### N8n Node Example:

```json
{
  "name": "Call Bluejet API",
  "type": "n8n-nodes-base.httpRequest",
  "parameters": {
    "url": "={{$env.BLUEJET_API_BASE_URL}}/orders/{{$json.order_id}}",
    "authentication": "predefinedCredentialType",
    "nodeCredentialType": "bluejetApi",
    "method": "GET",
    "options": {
      "headers": {
        "Authorization": "Bearer ={{$credentials.bluejetApi.apiKey}}"
      }
    }
  }
}
```

---

## 🧪 Step 7: Test the Integration

### Test Script: `test_bluejet_api.py`

```python
"""
Test Bluejet API integration
Run this to verify everything works
"""

from bluejet_api import BluejetAPI
import json

def run_tests():
    print("🧪 Testing Bluejet API Integration\n")
    print("="*50)

    # Initialize
    print("\n1. Initializing API client...")
    try:
        api = BluejetAPI()
        print("   ✅ API client initialized")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return

    # Test connection
    print("\n2. Testing connection...")
    if api.test_connection():
        print("   ✅ Connection successful")
    else:
        print("   ❌ Connection failed")
        return

    # Test customers endpoint
    print("\n3. Testing customers endpoint...")
    try:
        customers = api.get_customers(limit=5)
        print(f"   ✅ Retrieved {len(customers)} customers")
        if customers:
            print(f"   First customer: {customers[0].get('name', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test orders endpoint
    print("\n4. Testing orders endpoint...")
    try:
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        orders = api.get_orders(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        print(f"   ✅ Retrieved {len(orders)} orders from last 30 days")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Test products endpoint
    print("\n5. Testing products endpoint...")
    try:
        products = api.get_products()
        print(f"   ✅ Retrieved {len(products)} products")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    print("\n" + "="*50)
    print("🎉 API integration test complete!")
    print("\nNext steps:")
    print("1. Update SKILL.md with actual API endpoints")
    print("2. Create N8n workflows")
    print("3. Test with real Claude queries")

if __name__ == "__main__":
    run_tests()
```

**Run the test:**
```bash
python test_bluejet_api.py
```

---

## 📝 Step 8: Update Your .env.example

Add Bluejet configuration to `.env.example`:

```bash
# Add to .env.example (for documentation)

# ============================================
# Bluejet API Configuration
# ============================================
BLUEJET_API_KEY=your_api_key_from_1password
BLUEJET_API_SECRET=your_api_secret_from_1password
BLUEJET_API_BASE_URL=https://api.bluejet.com/v1
BLUEJET_WORKSPACE_ID=your_workspace_id

# Alternative OAuth configuration (if Bluejet uses OAuth)
# BLUEJET_CLIENT_ID=your_client_id
# BLUEJET_CLIENT_SECRET=your_client_secret
# BLUEJET_REFRESH_TOKEN=your_refresh_token
```

---

## 🎯 Use Cases with Claude + Bluejet API

### Use Case 1: Daily Order Summary

**You ask Claude:**
> "Give me a summary of today's orders from Bluejet"

**Claude does:**
1. Calls `api.get_orders(start_date=today, end_date=today)`
2. Analyzes data
3. Returns formatted summary:
   ```
   📊 Today's Orders Summary (2026-01-08)

   Total Orders: 12
   Total Revenue: 145,000 CZK
   Average Order: 12,083 CZK

   Top Customers:
   1. Hotel Maximilian - 35,000 CZK (3 orders)
   2. Restaurant U Fleků - 28,000 CZK (2 orders)

   Status Breakdown:
   - Pending: 5 orders
   - Processing: 4 orders
   - Shipped: 3 orders

   ⚠️ Urgent: 2 orders need attention (VIP customers)
   ```

### Use Case 2: Customer Lookup

**You ask:**
> "Find customer 'Hotel Maximilian' in Bluejet and show me their recent orders"

**Claude does:**
1. Searches customers via API
2. Gets customer ID
3. Fetches recent orders for that customer
4. Returns complete profile with history

### Use Case 3: Create Order

**You ask:**
> "Create an order in Bluejet for Restaurant XYZ: 2x convection ovens, 1x dishwasher"

**Claude does:**
1. Looks up customer ID
2. Looks up product IDs
3. Calculates pricing
4. Creates order via API
5. Confirms with order number

### Use Case 4: Inventory Alert

**Automated (via N8n):**
1. N8n checks inventory daily
2. If low stock detected
3. Claude generates alert email
4. Sends to you and supplier

---

## 🔒 Security Best Practices

### Do:
✅ Store credentials in `.env` (never in code)
✅ Keep `.env` in `.gitignore`
✅ Use 1Password for backup/sharing
✅ Rotate API keys periodically
✅ Use environment-specific keys (dev vs production)
✅ Log API errors (but not sensitive data)

### Don't:
❌ Commit credentials to Git
❌ Share API keys in chat/email
❌ Use production keys for testing
❌ Log full API responses (may contain sensitive data)
❌ Hard-code credentials anywhere

---

## 🎓 Next Steps

**Today:**
1. [ ] Get Bluejet API credentials from 1Password
2. [ ] Add to `.env` file
3. [ ] Create `bluejet_api.py`
4. [ ] Run `test_bluejet_api.py`

**This Week:**
1. [ ] Update Bluejet Expert skill with actual API endpoints
2. [ ] Test common operations
3. [ ] Create first N8n workflow
4. [ ] Train Claude on API responses

**This Month:**
1. [ ] Automate daily reports
2. [ ] Set up inventory alerts
3. [ ] Integrate with Supabase
4. [ ] Build complete automation workflows

---

## 🆘 Troubleshooting

### "API Key Invalid"
→ Check credentials in 1Password, ensure copied correctly
→ Check if key has expired or been rotated
→ Verify workspace ID is correct

### "403 Forbidden"
→ API key may not have required permissions
→ Check Bluejet account settings → API access
→ May need admin approval for API access

### "Connection Timeout"
→ Check internet connection
→ Verify API base URL is correct
→ Check if Bluejet has rate limits

### "Unexpected Response Format"
→ API documentation may have changed
→ Check Bluejet version/updates
→ Log full response to debug

---

## 📞 Support

**Bluejet API Support:**
- Documentation: [Find in Bluejet app or developer portal]
- Support Email: [Check 1Password or Bluejet settings]
- Support Phone: [From Bluejet account]

**Internal:**
- Your Developer: [Name if you have one]
- This Documentation: `skills/bluejet-expert/API_INTEGRATION_SETUP.md`

---

## ✅ Integration Checklist

- [ ] Retrieved credentials from 1Password
- [ ] Added to `.env` file
- [ ] Created `bluejet_api.py`
- [ ] Ran test script successfully
- [ ] Updated Bluejet Expert skill
- [ ] Tested with Claude query
- [ ] Created first N8n workflow
- [ ] Documented custom endpoints
- [ ] Set up error monitoring
- [ ] Celebrating successful integration! 🎉

---

**With API integration, Claude becomes 10x more powerful for Bluejet!** 🚀

No more manually copying data - Claude can read and write directly to Bluejet, fully automating your workflows.
