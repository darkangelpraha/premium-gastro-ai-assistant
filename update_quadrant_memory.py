#!/usr/bin/env python3
"""
Update Quadrant (Qdrant) Memory System
Run this script on the Mac/workstation that has access to the NAS
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from datetime import datetime
import hashlib

# Configuration - UPDATE THESE
QDRANT_HOST = "your-nas-ip-or-hostname"  # e.g., "192.168.1.100" or "nas.local"
QDRANT_PORT = 6333
COLLECTION_NAME = "claude_memory"

# Memory entries to add
CRITICAL_RULES = [
    {
        "id": "rule_git_no_autonomous_commit",
        "rule": "NEVER commit or push to git without explicit user approval",
        "details": "User stated: 'this behaviour is dangerous and therefore strictly prohibited!' on 2026-01-15",
        "severity": "critical",
        "type": "prohibition",
        "date": "2026-01-15",
        "incident": "User asked to 'audit and come up with verifiable solution, nothing else'. I created solution correctly, then autonomously committed and pushed without asking. User did NOT ask for commit/push.",
        "correct_behavior": "1. Complete requested work. 2. STOP and present results. 3. ASK if user wants to commit/push. 4. WAIT for explicit approval. 5. Only then proceed.",
        "exceptions": "Only when user explicitly says 'commit this' or 'push this' or 'create a PR'"
    },
    {
        "id": "rule_never_make_excuses",
        "rule": "Who wants is looking for ways to do it, who does not want is looking for excuses",
        "details": "User statement on 2026-01-15: Stop being lazy, find solutions not excuses",
        "severity": "critical",
        "type": "behavioral",
        "date": "2026-01-15",
        "correct_behavior": "When faced with challenges: DON'T say 'I can't find it'. DO search harder using all available methods. DO try multiple approaches. DO be resourceful and persistent."
    }
]

def text_to_vector(text: str, dim: int = 384) -> list:
    """
    Simple text to vector conversion using hash
    In production, use proper embeddings (OpenAI, Sentence Transformers, etc.)
    """
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()

    # Expand hash to required dimensions
    vector = []
    for i in range(dim):
        vector.append((hash_bytes[i % len(hash_bytes)] / 255.0) * 2 - 1)

    return vector

def main():
    print("=== Quadrant (Qdrant) Memory Update ===")
    print(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")

    try:
        # Connect to Qdrant
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=5)

        # Check connection
        collections = client.get_collections()
        print(f"✓ Connected! Found {len(collections.collections)} collections")

        # Check if memory collection exists
        collection_exists = False
        for col in collections.collections:
            if col.name == COLLECTION_NAME:
                collection_exists = True
                print(f"✓ Collection '{COLLECTION_NAME}' exists")
                break

        # Create collection if it doesn't exist
        if not collection_exists:
            print(f"Creating collection '{COLLECTION_NAME}'...")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✓ Collection created")

        # Add critical rules to memory
        print(f"\nAdding {len(CRITICAL_RULES)} critical rules to memory...")

        points = []
        for rule in CRITICAL_RULES:
            # Create searchable text from rule
            search_text = f"{rule['rule']} {rule['details']} {rule.get('correct_behavior', '')}"

            # Convert to vector
            vector = text_to_vector(search_text)

            # Create point
            point = PointStruct(
                id=hashlib.md5(rule['id'].encode()).hexdigest()[:32],
                vector=vector,
                payload={
                    **rule,
                    "added_timestamp": datetime.now().isoformat(),
                    "search_text": search_text
                }
            )
            points.append(point)

            print(f"  • {rule['id']}: {rule['rule'][:60]}...")

        # Upload points
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        print(f"\n✓ Successfully added {len(points)} rules to Quadrant memory")

        # Verify
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"\n=== Verification ===")
        print(f"Collection: {COLLECTION_NAME}")
        print(f"Total points: {collection_info.points_count}")
        print(f"Vector size: {collection_info.config.params.vectors.size}")

        print(f"\n✓ Memory update complete!")

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print(f"\nTroubleshooting:")
        print(f"1. Check that Qdrant is running on {QDRANT_HOST}:{QDRANT_PORT}")
        print(f"2. Update QDRANT_HOST in this script with correct NAS IP/hostname")
        print(f"3. Ensure firewall allows connection to port {QDRANT_PORT}")
        print(f"4. Check Qdrant logs on NAS")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("IMPORTANT: Update QDRANT_HOST variable before running!")
    print("Current: ", QDRANT_HOST)
    print("=" * 50)
    print()

    if QDRANT_HOST == "your-nas-ip-or-hostname":
        print("⚠️  Please update QDRANT_HOST in this script first!")
        print("Example: QDRANT_HOST = '192.168.1.100'")
        print("         QDRANT_HOST = 'nas.local'")
        exit(1)

    success = main()
    exit(0 if success else 1)
