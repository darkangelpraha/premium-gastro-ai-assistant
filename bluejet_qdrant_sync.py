#!/usr/bin/env python3
"""
BlueJet → Qdrant Product Sync Service
Syncs products from BlueJet CRM to Qdrant vector database for semantic search

Credentials from environment variables (set via 1Password):
- BLUEJET_URL: Your BlueJet instance URL (e.g., https://your-instance.bluejet.cz)
- BLUEJET_TOKEN_ID: API token identifier
- BLUEJET_TOKEN_HASH: API token hash
- QDRANT_HOST: Qdrant host (default: 192.168.1.129)
- QDRANT_PORT: Qdrant port (default: 6333)
"""

import os
import sys
import requests
import json
import subprocess
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


def read_from_1password(reference: str, default: str = None) -> Optional[str]:
    """Read credential from 1Password using op CLI"""
    try:
        result = subprocess.run(
            ['op', 'read', reference],
            capture_output=True,
            text=True,
            check=True
        )
        # Strip all leading/trailing whitespace including newlines
        value = result.stdout.strip()
        return value if value else default
    except subprocess.CalledProcessError:
        if default is not None:
            return default
        logger.warning(f"Could not read from 1Password: {reference}")
        return None
    except FileNotFoundError:
        logger.error("1Password CLI (op) not found. Install: brew install 1password-cli")
        if default is not None:
            return default
        return None


# 1Password vault ID (pipe character | in vault name breaks op read)
VAULT_ID = "5zbrmieoqrroxon4eu6mwfu4li"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Product:
    """Product from BlueJet CRM"""
    id: str
    name: str
    code: str
    description: str
    category: str
    supplier: str
    price: float
    currency: str
    availability: str
    unit: str
    metadata: Dict[str, Any]


class BlueJetAPI:
    """BlueJet CRM API Client"""

    def __init__(self):
        # Load credentials directly from 1Password
        logger.info("Loading credentials from 1Password...")
        self.username = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/username", "svejkovsky")
        self.token_id = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/BLUEJET_API_TOKEN_ID")
        self.token_hash = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/BLUEJET_API_TOKEN_HASH")
        self.base_url = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/w4wjna5zoxuysfdsfdxsyrasmu", "https://czeco.bluejet.cz")
        self.auth_url = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/BLUEJET_REST_AUTH_URL", f'{self.base_url}/api/v1/users/authenticate')
        self.data_url = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/BLUEJET_REST_DATA_URL", f'{self.base_url}/api/v1/data')
        self.environment = read_from_1password(f"op://{VAULT_ID}/BlueJet API FULL/BLUEJET_API_ENVIRONMENT", "production")

        if not all([self.token_id, self.token_hash]):
            raise ValueError(
                "Missing BlueJet credentials from 1Password. Check vault 'Missive | BJ' → 'BlueJet API FULL'"
            )

        self.api_base = f"{self.base_url}/api/v1"
        self.auth_token = None
        logger.info(f"BlueJet API initialized: {self.base_url} (user: {self.username}, env: {self.environment})")

    def authenticate(self) -> bool:
        """Authenticate with BlueJet REST API using JSON"""
        try:
            # Build authentication JSON request (per BlueJet REST API docs)
            auth_data = {
                "tokenID": self.token_id,
                "tokenHash": self.token_hash
            }

            logger.info(f"Authenticating to: {self.auth_url}")
            logger.info(f"TokenID length: {len(self.token_id)}, TokenHash length: {len(self.token_hash)}")
            logger.info(f"Sending JSON: {{\"tokenID\": \"{self.token_id[:4]}...{self.token_id[-4:]}\", \"tokenHash\": \"{self.token_hash[:4]}...{self.token_hash[-4:]}\"}}\"")

            response = requests.post(
                self.auth_url,
                json=auth_data,
                headers={
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json'
                }
            )

            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")

            if response.status_code == 200:
                # Parse JSON response
                result = response.json()
                if result.get('succeeded') and result.get('token'):
                    self.auth_token = result['token']
                    logger.info("✅ BlueJet authentication successful")
                    logger.info(f"Token valid for 24 hours: {self.auth_token[:10]}...")
                    return True
                else:
                    logger.error(f"❌ Authentication failed: {result.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False

    def fetch_products(self, limit: int = 50, offset: int = 0, retry_count: int = 0) -> List[Dict]:
        """Fetch products from BlueJet with rate limit handling"""
        if not self.auth_token:
            if not self.authenticate():
                return []

        try:
            # Fetch products using BlueJet REST API with X-Token header
            response = requests.get(
                f"{self.api_base}/data",  # REST API data endpoint
                params={'limit': limit, 'offset': offset, 'entity': 'products'},
                headers={
                    'X-Token': self.auth_token,  # Token in X-Token header per API docs
                    'Accept': 'application/json',
                    'Content-Type': 'application/json; charset=utf-8'
                }
            )

            # Handle rate limiting (429 Too Many Requests)
            if response.status_code == 429 and retry_count < 3:
                retry_after = int(response.headers.get('Retry-After', 5))
                logger.warning(f"⚠️ Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self.fetch_products(limit, offset, retry_count + 1)

            if response.status_code == 200:
                # Parse JSON response
                data = response.json()
                products = []

                # Handle different response structures
                items = data if isinstance(data, list) else data.get('items', data.get('data', []))

                for item in items:
                    product = {
                        'id': str(item.get('id', item.get('ID', ''))),
                        'name': item.get('name', item.get('Name', '')),
                        'code': item.get('code', item.get('Code', '')),
                        'description': item.get('description', item.get('Description', '')),
                        'category': item.get('category', item.get('Category', '')),
                        'supplier': item.get('supplier', item.get('Supplier', '')),
                        'price': float(item.get('price', item.get('Price', 0.0))),
                        'currency': item.get('currency', item.get('Currency', 'CZK')),
                        'availability': item.get('availability', item.get('Availability', '')),
                        'unit': item.get('unit', item.get('Unit', 'ks')),
                    }
                    products.append(product)

                logger.info(f"✅ Fetched {len(products)} products from BlueJet")
                return products
            else:
                logger.error(f"❌ Failed to fetch products: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Error fetching products: {e}")
            return []

    def fetch_all_products(self) -> List[Dict]:
        """Fetch all products (paginated with rate limiting and verification)"""
        all_products = []
        batch_size = 50  # Reasonable batch size for API stability
        offset = 0
        delay_between_requests = 2.0  # Seconds between API calls
        consecutive_failures = 0
        max_consecutive_failures = 3

        while True:
            logger.info(f"📥 Fetching batch starting at offset {offset}...")
            products = self.fetch_products(limit=batch_size, offset=offset)

            # Verify batch was successful
            if not products:
                consecutive_failures += 1
                logger.warning(f"⚠️ Empty batch at offset {offset} (failure {consecutive_failures}/{max_consecutive_failures})")

                if consecutive_failures >= max_consecutive_failures:
                    logger.info("No more products or max failures reached. Stopping.")
                    break

                # Wait before trying next batch
                time.sleep(delay_between_requests)
                offset += batch_size
                continue

            # Reset failure counter on success
            consecutive_failures = 0

            # Verify product data quality
            valid_products = [p for p in products if p.get('id') and p.get('name')]
            if len(valid_products) < len(products):
                logger.warning(f"⚠️ Filtered out {len(products) - len(valid_products)} invalid products")

            all_products.extend(valid_products)
            offset += batch_size

            logger.info(f"✅ Batch verified: {len(valid_products)} valid products (total: {len(all_products)})")

            if len(products) < batch_size:
                logger.info("📦 Last batch received (smaller than batch size)")
                break  # Last page

            # Rate limiting: Wait between requests to avoid hammering the API
            time.sleep(delay_between_requests)

        logger.info(f"✅ Total products fetched and verified: {len(all_products)}")
        return all_products


class QdrantSync:
    """Qdrant Vector Database Sync"""

    def __init__(self):
        self.host = os.getenv('QDRANT_HOST', '192.168.1.129')
        self.port = int(os.getenv('QDRANT_PORT', '6333'))
        self.collection_name = 'bluejet_products'

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            logger.info(f"✅ Connected to Qdrant at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Qdrant: {e}")
            raise

    def create_collection_if_not_exists(self):
        """Create products collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                )
                logger.info(f"✅ Created collection: {self.collection_name}")
            else:
                logger.info(f"Collection {self.collection_name} already exists")

        except Exception as e:
            logger.error(f"❌ Error creating collection: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text (placeholder - integrate with OpenAI/Anthropic)"""
        # TODO: Integrate with actual embedding service (OpenAI, Cohere, etc.)
        # For now, return dummy embedding
        import hashlib
        import struct

        # Simple hash-based embedding (REPLACE WITH REAL EMBEDDINGS)
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to 1536 floats (match OpenAI embedding size)
        embedding = []
        for i in range(0, len(hash_bytes), 2):
            value = struct.unpack('H', hash_bytes[i:i+2])[0]
            embedding.append(float(value) / 65535.0)

        # Pad to 1536 dimensions
        while len(embedding) < 1536:
            embedding.append(0.0)

        return embedding[:1536]

    def sync_products(self, products: List[Dict]) -> int:
        """Sync products to Qdrant"""
        self.create_collection_if_not_exists()

        points = []
        for product in products:
            try:
                # Create searchable text
                searchable_text = f"""
                {product['name']}
                {product['code']}
                {product['description']}
                {product['category']}
                {product['supplier']}
                """.strip()

                # Generate embedding
                embedding = self.generate_embedding(searchable_text)

                # Create point
                point = PointStruct(
                    id=product['id'],
                    vector=embedding,
                    payload={
                        'name': product['name'],
                        'code': product['code'],
                        'description': product['description'],
                        'category': product['category'],
                        'supplier': product['supplier'],
                        'price': product['price'],
                        'currency': product['currency'],
                        'availability': product['availability'],
                        'unit': product['unit'],
                        'searchable_text': searchable_text,
                        'last_updated': datetime.now().isoformat(),
                    }
                )
                points.append(point)

            except Exception as e:
                logger.warning(f"⚠️ Error processing product {product.get('id')}: {e}")
                continue

        # Upload to Qdrant in batches (with verification and confirmation)
        batch_size = 50  # Reasonable batch size matching fetch size
        total_uploaded = 0
        failed_batches = []

        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(points) + batch_size - 1) // batch_size

            try:
                logger.info(f"📤 Uploading batch {batch_num}/{total_batches} ({len(batch)} products)...")

                # Upload batch
                operation_info = self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )

                # Verify upload was successful
                if operation_info and hasattr(operation_info, 'status'):
                    if operation_info.status == 'completed' or str(operation_info.status).lower() == 'completed':
                        total_uploaded += len(batch)
                        logger.info(f"✅ Batch {batch_num} verified: {len(batch)} products uploaded successfully")
                    else:
                        logger.error(f"❌ Batch {batch_num} upload status unclear: {operation_info.status}")
                        failed_batches.append(batch_num)
                else:
                    # No status returned - assume success if no exception
                    total_uploaded += len(batch)
                    logger.info(f"✅ Batch {batch_num} uploaded: {len(batch)} products (status unknown, no error)")

                # Small delay between batches for smooth operation
                if i + batch_size < len(points):
                    time.sleep(1.0)

            except Exception as e:
                logger.error(f"❌ Batch {batch_num} failed: {e}")
                failed_batches.append(batch_num)
                continue

        # Final verification
        if failed_batches:
            logger.warning(f"⚠️ {len(failed_batches)} batch(es) failed: {failed_batches}")

        logger.info(f"✅ Sync complete: {total_uploaded}/{len(points)} products uploaded to Qdrant")

        # Double-check collection count
        try:
            collection_info = self.client.get_collection(self.collection_name)
            logger.info(f"🔍 Verification: Collection now contains {collection_info.points_count} total points")
        except Exception as e:
            logger.warning(f"Could not verify collection count: {e}")

        return total_uploaded


def main():
    """Main sync process"""
    logger.info("=" * 60)
    logger.info("BlueJet → Qdrant Product Sync Service")
    logger.info("=" * 60)

    try:
        # Initialize clients
        bluejet = BlueJetAPI()
        qdrant = QdrantSync()

        # Fetch products from BlueJet
        logger.info("📥 Fetching products from BlueJet CRM...")
        products = bluejet.fetch_all_products()

        if not products:
            logger.error("❌ No products fetched. Exiting.")
            sys.exit(1)

        # Sync to Qdrant
        logger.info(f"📤 Syncing {len(products)} products to Qdrant...")
        uploaded = qdrant.sync_products(products)

        logger.info("=" * 60)
        logger.info(f"✅ SYNC COMPLETE")
        logger.info(f"   Products fetched: {len(products)}")
        logger.info(f"   Products uploaded: {uploaded}")
        logger.info(f"   Collection: {qdrant.collection_name}")
        logger.info(f"   Qdrant: {qdrant.host}:{qdrant.port}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
