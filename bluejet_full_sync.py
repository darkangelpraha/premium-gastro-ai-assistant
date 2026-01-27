#!/usr/bin/env python3
"""
Complete BlueJet → Qdrant Sync

⚠️  CRITICAL: READ-ONLY OPERATION - NON-DESTRUCTIVE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This script ONLY reads data from BlueJet using GET requests.
NO write operations (POST/PUT/DELETE) are performed.
Your BlueJet data is NEVER modified or deleted.
Safe to run while working in BlueJet CRM.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Syncs ALL entities from BlueJet CRM to Qdrant:
- Products (217)
- Contacts (222)
- Companies (225)
- Activities (227)
- Issued Offers (293)
- Received Orders (321)
- Issued Invoices (323)
- Received Invoices (328)
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from bluejet_qdrant_sync import BlueJetAPI, read_from_1password, VAULT_ID
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# BlueJet entity object numbers from official API docs
BLUEJET_ENTITIES = {
    'products': {'no': 217, 'name_field': 'Nazev', 'description': 'Products/Produkty'},
    'contacts': {'no': 222, 'name_field': 'firstname', 'description': 'Contacts/Kontakty'},
    'companies': {'no': 225, 'name_field': 'name', 'description': 'Companies/Společnosti'},
    'activities': {'no': 227, 'name_field': 'subject', 'description': 'Activities/Aktivity'},
    'issued_offers': {'no': 293, 'name_field': 'offernumber', 'description': 'Issued Offers/Nabídky'},
    'received_orders': {'no': 321, 'name_field': 'ordernumber', 'description': 'Received Orders/Přijaté objednávky'},
    'issued_invoices': {'no': 323, 'name_field': 'invoicenumber', 'description': 'Issued Invoices/Vydané faktury'},
    'received_invoices': {'no': 328, 'name_field': 'invoicenumber', 'description': 'Received Invoices/Přijaté faktury'},
}


class QdrantFullSync:
    """Sync all BlueJet entities to Qdrant"""

    def __init__(self):
        self.host = os.getenv('QDRANT_HOST', '192.168.1.129')
        self.port = int(os.getenv('QDRANT_PORT', '6333'))

        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            timeout=300.0
        )
        logger.info(f"✅ Connected to Qdrant at {self.host}:{self.port}")

    def generate_embedding(self, text: str) -> list:
        """Generate hash-based embedding"""
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        embedding = []
        for i in range(0, len(hash_bytes), 2):
            value = int.from_bytes(hash_bytes[i:i+2], 'big')
            embedding.append(float(value) / 65535.0)

        while len(embedding) < 1536:
            embedding.append(0.0)

        return embedding[:1536]

    def sync_entity(self, bluejet: BlueJetAPI, entity_key: str, entity_config: dict) -> int:
        """Sync specific entity type with 100% verification"""
        logger.info("=" * 60)
        logger.info(f"📥 Syncing {entity_config['description']}")
        logger.info("=" * 60)

        collection_name = f"bluejet_{entity_key}"
        object_no = entity_config['no']

        # Get BlueJet total count for verification
        logger.info(f"🔍 Getting total count from BlueJet (object {object_no})...")
        bluejet_total = bluejet.get_total_count(object_no=object_no)
        if bluejet_total > 0:
            logger.info(f"📊 BlueJet has {bluejet_total:,} total {entity_key}")
        else:
            logger.warning(f"⚠️ Could not determine BlueJet total count for {entity_key}")

        # Create collection
        try:
            collection_info = self.client.get_collection(collection_name)
            logger.info(f"Collection exists: {collection_info.points_count} points")
            initial_qdrant_count = collection_info.points_count
        except:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            logger.info(f"✅ Created collection: {collection_name}")
            initial_qdrant_count = 0

        # Streaming sync
        offset = 0
        batch_size = 200
        total_synced = 0
        consecutive_failures = 0

        while True:
            logger.info(f"📥 Fetching batch at offset {offset}...")

            # Fetch from BlueJet using generic fetch_data method
            items = bluejet.fetch_data(object_no=object_no, limit=batch_size, offset=offset)

            if not items:
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    break
                offset += batch_size
                continue

            consecutive_failures = 0

            # Convert to Qdrant points
            points = []
            for item in items:
                try:
                    # Create searchable text from ALL fields (raw_data)
                    searchable_parts = []
                    raw_data = item.get('raw_data', {})

                    for field_name, field_value in raw_data.items():
                        if field_value and isinstance(field_value, str) and field_value.strip():
                            searchable_parts.append(field_value)

                    searchable_text = " ".join(searchable_parts)
                    embedding = self.generate_embedding(searchable_text)

                    point = PointStruct(
                        id=hash(item['id']),  # Use hash of ID as numeric ID
                        vector=embedding,
                        payload={
                            'id': item['id'],
                            'raw_data': raw_data,  # Store ALL original BlueJet data
                            'entity_type': entity_key,
                            'searchable_text': searchable_text,
                            'synced_at': datetime.now().isoformat()
                        }
                    )
                    points.append(point)
                except Exception as e:
                    logger.warning(f"⚠️ Error processing item: {e}")
                    continue

            # Upload to Qdrant
            if points:
                try:
                    self.client.upsert(collection_name=collection_name, points=points)
                    total_synced += len(points)
                    logger.info(f"✅ Uploaded {len(points)} items (total: {total_synced})")
                except Exception as e:
                    logger.error(f"❌ Upload failed: {e}")

            if len(items) < batch_size:
                break

            offset += batch_size
            time.sleep(2.0)

        # CRITICAL VERIFICATION: BlueJet count must match Qdrant count
        logger.info("🔍 Verifying counts...")
        try:
            collection_info = self.client.get_collection(collection_name)
            qdrant_count = collection_info.points_count

            logger.info(f"📊 BlueJet: {bluejet_total:,} | Qdrant: {qdrant_count:,}")

            if bluejet_total > 0 and qdrant_count != bluejet_total:
                missing = bluejet_total - qdrant_count
                logger.error(f"❌ MISMATCH: {missing:,} items missing from Qdrant!")
                logger.error(f"⚠️  Running verification pass to ensure 100% copy...")

                # Run verification pass
                verification_offset = 0
                while verification_offset < bluejet_total:
                    items = bluejet.fetch_data(object_no=object_no, limit=batch_size, offset=verification_offset)
                    if not items:
                        break

                    # Convert and upload
                    points = []
                    for item in items:
                        try:
                            raw_data = item.get('raw_data', {})
                            searchable_parts = [str(v) for v in raw_data.values() if v and isinstance(v, str)]
                            searchable_text = " ".join(searchable_parts)
                            embedding = self.generate_embedding(searchable_text)

                            point = PointStruct(
                                id=hash(item['id']),
                                vector=embedding,
                                payload={
                                    'id': item['id'],
                                    'raw_data': raw_data,
                                    'entity_type': entity_key,
                                    'searchable_text': searchable_text,
                                    'synced_at': datetime.now().isoformat()
                                }
                            )
                            points.append(point)
                        except Exception as e:
                            logger.warning(f"⚠️ Error processing item: {e}")

                    if points:
                        self.client.upsert(collection_name=collection_name, points=points)

                    verification_offset += batch_size
                    time.sleep(2.0)

                # Final count check
                collection_info = self.client.get_collection(collection_name)
                final_count = collection_info.points_count

                if final_count == bluejet_total:
                    logger.info(f"✅ COUNTS MATCH: {final_count:,} items (100% copy)")
                else:
                    logger.error(f"⚠️ STILL MISSING: {bluejet_total - final_count:,} items")

                return final_count

            elif bluejet_total > 0 and qdrant_count == bluejet_total:
                logger.info(f"✅ COUNTS MATCH: {qdrant_count:,} items (100% copy)")

        except Exception as e:
            logger.warning(f"⚠️ Could not verify count: {e}")

        logger.info(f"✅ {entity_config['description']}: {total_synced} items synced")
        return total_synced


def main():
    """Sync all BlueJet entities"""
    logger.info("=" * 60)
    logger.info("BlueJet → Qdrant COMPLETE Sync")
    logger.info("=" * 60)

    start_time = time.time()

    try:
        bluejet = BlueJetAPI()
        qdrant = QdrantFullSync()

        summary = {}

        for entity_key, entity_config in BLUEJET_ENTITIES.items():
            try:
                count = qdrant.sync_entity(bluejet, entity_key, entity_config)
                summary[entity_key] = count
            except Exception as e:
                logger.error(f"❌ Failed to sync {entity_key}: {e}")
                summary[entity_key] = 0

            time.sleep(3.0)  # Pause between entities

        # Final summary
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info("✅ COMPLETE SYNC FINISHED")
        logger.info("=" * 60)
        for entity, count in summary.items():
            logger.info(f"   {entity}: {count} items")
        logger.info(f"   Total time: {elapsed/60:.1f} minutes")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ Sync failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
