#!/usr/bin/env python3
"""
SUPABASE INTELLIGENCE AGENT - APIFY SCRAPE + QDRANT INGEST

Minimal, hardened implementation:
- Triggers Apify website-content-crawler task (task name must be lowercase-hyphen).
- Supports webhook callback.
- Ingests embedding-bearing items into Qdrant collection tech_docs_vectors.
- Offers --run-now for local backfill when Apify public actors are blocked (HTTP 403 public-actor-disabled).
"""

import hashlib
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_env(name: str, min_len: int = 1) -> str:
    value = os.getenv(name, "").strip()
    if len(value) < min_len:
        raise ValueError(f"{name} environment variable is required and must be valid.")
    return value


def is_lower_hyphen(value: str) -> bool:
    return value.replace("-", "").isalnum() and value == value.lower()


def validate_webhook(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise ValueError("APIFY_WEBHOOK_URL must be http or https.")
    return url


def trigger_apify_run(task_id: str, token: str, webhook_url: Optional[str], timeout: int = 300) -> List[Dict[str, Any]]:
    params = {"token": token}
    if webhook_url:
        params["webhookUrl"] = webhook_url

    try:
        resp = requests.post(
            f"https://api.apify.com/v2/actor-tasks/{task_id}/run-sync-get-dataset-items",
            params=params,
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:  # surface common Apify plan issues
        if resp.status_code == 403:
            logger.error("Apify run blocked (public actor disabled). Use private actor or local backfill.")
        raise


def build_point_id(item: Dict[str, Any]) -> str:
    candidate = item.get("id") or item.get("url")
    if candidate and len(candidate) < 256:
        return candidate
    text = item.get("url") or json.dumps(item, sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_qdrant(qdrant_url: str, api_key: str, collection: str, items: List[Dict[str, Any]], timeout: int = 120) -> None:
    points = []
    for item in items:
        vector = item.get("embedding") or item.get("vector")
        if not vector or not isinstance(vector, list) or len(vector) == 0:
            continue
        points.append(
            {
                "id": build_point_id(item),
                "vector": vector,
                "payload": {
                    "url": item.get("url"),
                    "text": item.get("text") or item.get("content"),
                    "source": item.get("source"),
                    "checksum": item.get("checksum"),
                },
            }
        )

    if not points:
        logger.info("No points with embeddings to ingest.")
        return

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key,
    }

    payload = {"points": points}
    ingest_url = f"{qdrant_url}/collections/{collection}/points"
    try:
        resp = requests.put(ingest_url, headers=headers, data=json.dumps(payload), timeout=timeout)
        resp.raise_for_status()
        logger.info("Ingested %s points into Qdrant collection %s", len(points), collection)
    except requests.HTTPError as exc:
        logger.error("Qdrant ingest failed: %s", resp.text if 'resp' in locals() else exc)
        raise


def main(run_now: bool = False) -> None:
    apify_token = get_env("APIFY_API_TOKEN", 10)
    apify_task = get_env("APIFY_TASK_ID", 3)
    if not is_lower_hyphen(apify_task):
        raise ValueError("APIFY_TASK_ID must be lowercase with hyphens (e.g., supabase-docs-crawler).")
    webhook_url = validate_webhook(os.getenv("APIFY_WEBHOOK_URL", ""))

    qdrant_url = get_env("QDRANT_URL", 8)
    qdrant_key = get_env("QDRANT_API_KEY", 10)
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "tech_docs_vectors")

    logger.info("Supabase intelligence agent start. run_now=%s", run_now)

    if run_now:
        try:
            items = trigger_apify_run(apify_task, apify_token, webhook_url)
            ingest_qdrant(qdrant_url, qdrant_key, qdrant_collection, items)
        except Exception as exc:
            logger.error("Run failed: %s", exc)
            sys.exit(1)
    else:
        logger.info("No action taken. Use --run-now to trigger Apify + Qdrant ingest.")


if __name__ == "__main__":
    main("--run-now" in sys.argv)
