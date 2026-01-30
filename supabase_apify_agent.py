#!/usr/bin/env python3
"""
SUPABASE INTELLIGENCE AGENT - APIFY SCRAPE + QDRANT INGEST

Temporary minimal implementation to trigger Apify website-content-crawler and ingest
results into Qdrant collection tech_docs_vectors. Supports webhook callbacks and
local backfill run (`--run-now`).
"""

import os
import sys
import json
import logging
from typing import Any, Dict, List, Optional

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_env(name: str, minimum_length: int = 1) -> str:
    value = os.getenv(name, "")
    if not value or len(value) < minimum_length:
        raise ValueError(f"{name} environment variable is required and must be valid.")
    return value


def trigger_apify_run(task_id: str, token: str, webhook_url: Optional[str]) -> Dict[str, Any]:
    url = f"https://api.apify.com/v2/actor-tasks/{task_id}/run-sync-get-dataset-items"
    params = {"token": token}
    if webhook_url:
        params["webhookUrl"] = webhook_url

    resp = requests.post(url, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def ingest_qdrant(
    qdrant_url: str,
    api_key: str,
    collection: str,
    items: List[Dict[str, Any]],
) -> None:
    if not items:
        logger.info("No items to ingest to Qdrant.")
        return

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    payload = {
        "points": [
            {
                "id": item.get("id") or item.get("url"),
                "vector": item.get("embedding") or item.get("vector"),
                "payload": {
                    "url": item.get("url"),
                    "text": item.get("text") or item.get("content"),
                    "source": item.get("source"),
                    "checksum": item.get("checksum"),
                },
            }
            for item in items
            if item.get("embedding") or item.get("vector")
        ]
    }

    if not payload["points"]:
        logger.info("No embeddings present in items; skipping ingest.")
        return

    ingest_url = f"{qdrant_url}/collections/{collection}/points"
    resp = requests.put(ingest_url, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    logger.info("Ingested %s points into Qdrant collection %s", len(payload["points"]), collection)


def main(run_now: bool = False) -> None:
    apify_token = get_env("APIFY_API_TOKEN", 10)
    apify_task = get_env("APIFY_TASK_ID", 3)
    qdrant_url = get_env("QDRANT_URL", 8)
    qdrant_key = get_env("QDRANT_API_KEY", 10)
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "tech_docs_vectors")
    webhook_url = os.getenv("APIFY_WEBHOOK_URL", "")

    logger.info("Starting Supabase intelligence agent. run_now=%s", run_now)

    if run_now:
        logger.info("Running Apify task now: %s", apify_task)
        items = trigger_apify_run(apify_task, apify_token, webhook_url)
        ingest_qdrant(qdrant_url, qdrant_key, qdrant_collection, items)
    else:
        logger.info("No action taken. Use --run-now to trigger a run.")


if __name__ == "__main__":
    run_now_flag = "--run-now" in sys.argv
    main(run_now_flag)
