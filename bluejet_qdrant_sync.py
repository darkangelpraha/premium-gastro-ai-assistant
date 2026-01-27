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
        """Authenticate with BlueJet API"""
        try:
            # Build authentication XML request (xmlns required by BlueJet API)
            auth_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<user xmlns="http://www.bluejet.cz/API">
    <tokenID>{self.token_id}</tokenID>
    <tokenHash>{self.token_hash}</tokenHash>
</user>"""

            logger.info(f"Authenticating to: {self.auth_url}")
            logger.info(f"TokenID length: {len(self.token_id)}, TokenHash length: {len(self.token_hash)}")

            # Debug: Show XML structure (masked for security)
            masked_xml = auth_xml.replace(self.token_id, f"{self.token_id[:4]}...{self.token_id[-4:]}")
            masked_xml = masked_xml.replace(self.token_hash, f"{self.token_hash[:4]}...{self.token_hash[-4:]}")
            logger.info(f"Sending XML:\n{masked_xml}")

            response = requests.post(
                self.auth_url,
                data=auth_xml.encode('utf-8'),
                headers={
                    'Content-Type': 'application/xml; charset=utf-8',
                }
            )

            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")

            if response.status_code == 200:
                # Parse token from response
                root = ET.fromstring(response.text)
                token_element = root.find('.//token')
                if token_element is not None and token_element.text:
                    self.auth_token = token_element.text
                    logger.info("✅ BlueJet authentication successful")
                    return True
                else:
                    logger.error("❌ No token found in response")
                    return False
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False

    def fetch_products(self, limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Fetch products from BlueJet"""
        if not self.auth_token:
            if not self.authenticate():
                return []

        try:
            # Fetch products (adjust endpoint based on BlueJet API structure)
            response = requests.get(
                f"{self.api_base}/products",
                params={'limit': limit, 'offset': offset},
                headers={
                    'Authorization': f'Bearer {self.auth_token}',
                    'Content-Type': 'application/xml'
                }
            )

            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.text)
                products = []

                for product_elem in root.findall('.//product'):
                    product = {
                        'id': product_elem.find('id').text if product_elem.find('id') is not None else '',
                        'name': product_elem.find('name').text if product_elem.find('name') is not None else '',
                        'code': product_elem.find('code').text if product_elem.find('code') is not None else '',
                        'description': product_elem.find('description').text if product_elem.find('description') is not None else '',
                        'category': product_elem.find('category').text if product_elem.find('category') is not None else '',
                        'supplier': product_elem.find('supplier').text if product_elem.find('supplier') is not None else '',
                        'price': float(product_elem.find('price').text) if product_elem.find('price') is not None else 0.0,
                        'currency': product_elem.find('currency').text if product_elem.find('currency') is not None else 'CZK',
                        'availability': product_elem.find('availability').text if product_elem.find('availability') is not None else '',
                        'unit': product_elem.find('unit').text if product_elem.find('unit') is not None else 'ks',
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
        """Fetch all products (paginated)"""
        all_products = []
        limit = 1000
        offset = 0

        while True:
            products = self.fetch_products(limit=limit, offset=offset)
            if not products:
                break

            all_products.extend(products)
            offset += limit

            logger.info(f"Progress: {len(all_products)} products fetched...")

            if len(products) < limit:
                break  # Last page

        logger.info(f"✅ Total products fetched: {len(all_products)}")
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

        # Upload to Qdrant in batches
        batch_size = 100
        total_uploaded = 0

        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                total_uploaded += len(batch)
                logger.info(f"Uploaded batch: {total_uploaded}/{len(points)} products")
            except Exception as e:
                logger.error(f"❌ Error uploading batch: {e}")
                continue

        logger.info(f"✅ Sync complete: {total_uploaded} products uploaded to Qdrant")
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
