#!/usr/bin/env python3
"""BlueJet -> Qdrant mirror (Phase 1, hourly-safe).

Design goals:
- keep BlueJet business entities mirrored in Qdrant for fast cross-system retrieval
- prioritize correctness and operational safety (no destructive deletes by default)
- preserve existing vectors when possible to avoid breaking legacy search behavior
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error
from urllib import parse, request


BLUEJET_BASE_URL = os.environ.get("BLUEJET_BASE_URL", "https://czeco.bluejet.cz").rstrip("/")
BLUEJET_API_TOKEN_ID = os.environ.get("BLUEJET_API_TOKEN_ID", "").strip()
BLUEJET_API_TOKEN_HASH = os.environ.get("BLUEJET_API_TOKEN_HASH", "").strip()
BLUEJET_API_TOKEN_ID_OP_REF = os.environ.get("BLUEJET_API_TOKEN_ID_OP_REF", "").strip()
BLUEJET_API_TOKEN_HASH_OP_REF = os.environ.get("BLUEJET_API_TOKEN_HASH_OP_REF", "").strip()
BLUEJET_API_DIRECT_TOKEN = os.environ.get("BLUEJET_API_DIRECT_TOKEN", "").strip()
BLUEJET_API_DIRECT_TOKEN_OP_REF = os.environ.get("BLUEJET_API_DIRECT_TOKEN_OP_REF", "").strip()

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") or os.environ.get("QDRANT_APIKEY") or ""
QDRANT_WAIT = os.environ.get("QDRANT_WAIT", "1") != "0"
QDRANT_ORDERING = os.environ.get("QDRANT_ORDERING", "weak").strip().lower() or "weak"

PAGE_LIMIT = int(os.environ.get("BLUEJET_PAGE_LIMIT", "50"))
HTTP_TIMEOUT_SECONDS = float(os.environ.get("BLUEJET_MIRROR_TIMEOUT_SECONDS", "40"))
BLUEJET_API_MIN_INTERVAL_SECONDS = float(os.environ.get("BLUEJET_API_MIN_INTERVAL_SECONDS", "0.75"))
BLUEJET_API_MAX_RETRIES = int(os.environ.get("BLUEJET_API_MAX_RETRIES", "6"))
BLUEJET_API_RETRY_BASE_SECONDS = float(os.environ.get("BLUEJET_API_RETRY_BASE_SECONDS", "2.0"))
BLUEJET_API_MAX_RETRY_SLEEP_SECONDS = float(os.environ.get("BLUEJET_API_MAX_RETRY_SLEEP_SECONDS", "60"))
BLUEJET_MAX_PAGES_PER_EVIDENCE = int(os.environ.get("BLUEJET_MAX_PAGES_PER_EVIDENCE", "0"))
BLUEJET_MAX_ROWS_PER_EVIDENCE = int(os.environ.get("BLUEJET_MAX_ROWS_PER_EVIDENCE", "0"))
BLUEJET_QDRANT_BATCH_SIZE = int(os.environ.get("BLUEJET_QDRANT_BATCH_SIZE", "50"))
BLUEJET_QDRANT_BATCH_PAUSE_SECONDS = float(os.environ.get("BLUEJET_QDRANT_BATCH_PAUSE_SECONDS", "0.4"))
BLUEJET_EVIDENCE_PAUSE_SECONDS = float(os.environ.get("BLUEJET_EVIDENCE_PAUSE_SECONDS", "3"))
BLUEJET_MAX_POINTS_PER_RUN = int(os.environ.get("BLUEJET_MAX_POINTS_PER_RUN", "3000"))
STATE_DB = os.environ.get(
    "BLUEJET_MIRROR_STATE_DB",
    str(Path.cwd() / ".cache" / "bluejet_mirror_state.sqlite"),
)
AUDIT_PATH = os.environ.get("BLUEJET_MIRROR_AUDIT_PATH", "/tmp/bluejet_qdrant_mirror_audit.jsonl")
LOG_PATH = os.environ.get("BLUEJET_MIRROR_LOG_PATH", "/tmp/bluejet_qdrant_mirror.log")


@dataclass(frozen=True)
class EvidenceConfig:
    no: int
    collection: str
    id_fields: tuple[str, ...]
    searchable_fields: tuple[str, ...]


EVIDENCES: tuple[EvidenceConfig, ...] = (
    EvidenceConfig(
        no=225,
        collection="bluejet_companies",
        id_fields=("firmaid", "customerid", "customeridsupl"),
        searchable_fields=("name", "contactperson1", "ico", "dic", "emailaddress1", "town", "street1"),
    ),
    EvidenceConfig(
        no=222,
        collection="bluejet_contacts",
        id_fields=("contactid", "customerid", "contactidsupl"),
        searchable_fields=("firstname", "lastname", "emailaddress1", "mobilephone", "telephone1", "firmaid"),
    ),
    EvidenceConfig(
        no=217,
        collection="bluejet_products",
        id_fields=("productid", "code"),
        searchable_fields=("code", "name", "supplier", "category", "ean", "nazev"),
    ),
    EvidenceConfig(
        no=293,
        collection="bluejet_offers_out",
        id_fields=("nabidkaid", "kodnabidky"),
        searchable_fields=("kodnabidky", "nazev", "statuscode", "customerid", "firmaid"),
    ),
    EvidenceConfig(
        no=356,
        collection="bluejet_orders_out",
        id_fields=("objednavkaid", "kodobjednavky"),
        searchable_fields=("kodobjednavky", "nazev", "statuscode", "customerid", "firmaid", "datumpotvrzeni"),
    ),
    EvidenceConfig(
        no=323,
        collection="bluejet_invoices_out",
        id_fields=("fakturaid", "kodfaktury"),
        searchable_fields=("kodfaktury", "nazev", "statuscode", "stavuhrady", "customerid", "firmaid"),
    ),
)


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def audit(obj: dict[str, Any]) -> None:
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def ensure_state_db() -> sqlite3.Connection:
    p = Path(STATE_DB)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=30)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mirror_runs (
            run_id TEXT PRIMARY KEY,
            started_at INTEGER NOT NULL,
            finished_at INTEGER,
            status TEXT NOT NULL,
            summary_json TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mirror_run_evidence (
            run_id TEXT NOT NULL,
            evidence_no INTEGER NOT NULL,
            collection TEXT NOT NULL,
            rows_seen INTEGER NOT NULL,
            rows_upserted INTEGER NOT NULL,
            rows_failed INTEGER NOT NULL,
            completed_at INTEGER NOT NULL,
            PRIMARY KEY (run_id, evidence_no)
        )
        """
    )
    conn.commit()
    return conn


def _req_json(method: str, url: str, payload: Any | None, headers: dict[str, str], timeout: float) -> dict[str, Any]:
    body: bytes | None = None
    req_headers = dict(headers)
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = request.Request(url, data=body, headers=req_headers, method=method)
    with request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", "replace")
    return json.loads(raw) if raw.strip() else {}


def resolve_secret(env_value: str, op_ref: str) -> str:
    if env_value:
        return env_value
    if not op_ref:
        return ""
    try:
        out = subprocess.check_output(["op", "read", op_ref], text=True, timeout=15)
        return out.strip()
    except Exception as e:
        log(f"op_read_failed ref={op_ref} err={type(e).__name__}")
        return ""


class BlueJetClient:
    def __init__(self, base_url: str, token_id: str, token_hash: str, direct_token: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.token_id = token_id
        self.token_hash = token_hash
        self._token: str | None = direct_token or None
        self._last_request_at: float = 0.0

    def _throttle(self) -> None:
        # Conservative pacing to avoid BlueJet API bursts.
        wait = BLUEJET_API_MIN_INTERVAL_SECONDS - (time.time() - self._last_request_at)
        if wait > 0:
            time.sleep(wait)

    def _request_json_with_retry(
        self,
        method: str,
        url: str,
        payload: Any | None,
        headers: dict[str, str],
    ) -> dict[str, Any]:
        last_err: Exception | None = None
        used_401_fallback = False
        for attempt in range(BLUEJET_API_MAX_RETRIES + 1):
            self._throttle()
            try:
                data = _req_json(
                    method,
                    url,
                    payload,
                    headers=headers,
                    timeout=HTTP_TIMEOUT_SECONDS,
                )
                self._last_request_at = time.time()
                return data
            except error.HTTPError as e:
                self._last_request_at = time.time()
                code = int(getattr(e, "code", 0) or 0)
                if (
                    code == 401
                    and not used_401_fallback
                    and self._token
                    and self.token_id
                    and self.token_hash
                    and headers.get("X-Token")
                ):
                    # Some BlueJet setups provide token id/hash only; if direct token fails,
                    # retry by forcing authenticate() on the next attempt.
                    used_401_fallback = True
                    self._token = None
                    log("bluejet_401_fallback switching from direct-token to auth flow")
                    continue
                retry_after_raw = ""
                try:
                    retry_after_raw = str(e.headers.get("Retry-After") or "").strip()
                except Exception:
                    retry_after_raw = ""
                retry_after = float(retry_after_raw) if retry_after_raw.isdigit() else 0.0
                # Retry only on rate limits / transient upstream errors.
                if code not in (429, 500, 502, 503, 504) or attempt >= BLUEJET_API_MAX_RETRIES:
                    raise
                sleep_s = max(
                    retry_after,
                    BLUEJET_API_RETRY_BASE_SECONDS * (2 ** attempt),
                )
                sleep_s = min(sleep_s, BLUEJET_API_MAX_RETRY_SLEEP_SECONDS)
                log(f"bluejet_retry http={code} attempt={attempt + 1} sleep={round(sleep_s,2)}")
                time.sleep(sleep_s)
                last_err = e
            except Exception as e:
                self._last_request_at = time.time()
                if attempt >= BLUEJET_API_MAX_RETRIES:
                    raise
                sleep_s = BLUEJET_API_RETRY_BASE_SECONDS * (2 ** attempt)
                sleep_s = min(sleep_s, BLUEJET_API_MAX_RETRY_SLEEP_SECONDS)
                log(
                    f"bluejet_retry exception={type(e).__name__} "
                    f"attempt={attempt + 1} sleep={round(sleep_s,2)}"
                )
                time.sleep(sleep_s)
                last_err = e
        if last_err:
            raise last_err
        raise RuntimeError("BlueJet request failed without exception context")

    def authenticate(self) -> str:
        if self._token:
            return self._token
        if not self.token_id or not self.token_hash:
            raise RuntimeError("Missing BlueJet credentials (set direct token or tokenID+tokenHash)")
        data = self._request_json_with_retry(
            "POST",
            f"{self.base_url}/api/v1/users/authenticate",
            {"tokenID": self.token_id, "tokenHash": self.token_hash},
            headers={"Accept": "application/json"},
        )
        token = data.get("token")
        if not isinstance(token, str) or not token:
            raise RuntimeError(f"BlueJet auth failed: {str(data)[:300]}")
        self._token = token
        return token

    def data_page(self, evidence_no: int, limit: int, offset: int) -> dict[str, Any]:
        qs = parse.urlencode({"no": str(evidence_no), "limit": str(limit), "offset": str(offset)})
        url = f"{self.base_url}/api/v1/Data?{qs}"
        return self._request_json_with_retry(
            "GET",
            url,
            payload=None,
            headers={"Accept": "application/json", "X-Token": self.authenticate()},
        )

    @staticmethod
    def row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        cols = row.get("columns") or []
        if not isinstance(cols, list):
            return out
        for c in cols:
            if not isinstance(c, dict):
                continue
            name = c.get("name")
            if isinstance(name, str) and name:
                out[name] = c.get("value")
        return out


class QdrantClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json"}
        if self.api_key:
            h["api-key"] = self.api_key
        return h

    def get_collection_dim(self, collection: str) -> int:
        data = _req_json(
            "GET",
            f"{self.base_url}/collections/{collection}",
            payload=None,
            headers=self._headers(),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        size = (
            data.get("result", {})
            .get("config", {})
            .get("params", {})
            .get("vectors", {})
            .get("size")
        )
        if not isinstance(size, int) or size <= 0:
            raise RuntimeError(f"Cannot detect vector size for collection {collection}")
        return size

    def get_existing_vectors(self, collection: str, point_ids: list[str]) -> dict[str, Any]:
        if not point_ids:
            return {}
        data = _req_json(
            "POST",
            f"{self.base_url}/collections/{collection}/points",
            payload={"ids": point_ids, "with_payload": False, "with_vector": True},
            headers=self._headers(),
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        out: dict[str, Any] = {}
        points = data.get("result") or []
        if isinstance(points, list):
            for p in points:
                if not isinstance(p, dict):
                    continue
                pid = str(p.get("id") or "")
                vec = p.get("vector")
                if pid and vec is not None:
                    out[pid] = vec
        return out

    def upsert_points(self, collection: str, points: list[dict[str, Any]]) -> None:
        if not points:
            return
        qp = {
            "wait": "true" if QDRANT_WAIT else "false",
            "ordering": QDRANT_ORDERING,
        }
        url = f"{self.base_url}/collections/{collection}/points?{parse.urlencode(qp)}"
        _req_json(
            "PUT",
            url,
            payload={"points": points},
            headers=self._headers(),
            timeout=max(HTTP_TIMEOUT_SECONDS, 120),
        )


def sanitize_id(v: Any) -> str:
    return str(v or "").strip()


def choose_business_id(row: dict[str, Any], fields: tuple[str, ...], fallback: str) -> str:
    for f in fields:
        v = sanitize_id(row.get(f))
        if v:
            return v
    h = hashlib.sha256(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:24]
    return f"{fallback}:{h}"


def stable_point_id(collection: str, business_id: str) -> str:
    return hashlib.sha256(f"{collection}::{business_id}".encode("utf-8")).hexdigest()[:32]


def placeholder_vector(dim: int, seed: str) -> list[float]:
    # Deterministic pseudo-vector for collections where semantic vectors are not mandatory.
    if dim <= 1:
        return [1.0]
    buf = hashlib.sha256(seed.encode("utf-8")).digest()
    out: list[float] = []
    while len(out) < dim:
        for b in buf:
            out.append((b / 255.0) * 2.0 - 1.0)
            if len(out) >= dim:
                break
        buf = hashlib.sha256(buf).digest()
    return out


def searchable_text(row: dict[str, Any], fields: tuple[str, ...]) -> str:
    parts: list[str] = []
    for f in fields:
        v = row.get(f)
        s = str(v or "").strip()
        if s:
            parts.append(s)
    return " | ".join(parts)


def iter_evidence_rows(
    bj: BlueJetClient,
    evidence_no: int,
    limit: int,
) -> tuple[list[dict[str, Any]], int, int, str]:
    offset = 0
    pages = 0
    rows_out: list[dict[str, Any]] = []
    stop_reason = "completed"
    while True:
        if BLUEJET_MAX_PAGES_PER_EVIDENCE > 0 and pages >= BLUEJET_MAX_PAGES_PER_EVIDENCE:
            stop_reason = f"page_cap:{BLUEJET_MAX_PAGES_PER_EVIDENCE}"
            break
        data = bj.data_page(evidence_no=evidence_no, limit=limit, offset=offset)
        pages += 1
        rows = data.get("rows") or []
        if not isinstance(rows, list) or not rows:
            stop_reason = "empty_page"
            break
        for r in rows:
            if isinstance(r, dict):
                rows_out.append(BlueJetClient.row_to_dict(r))
                if BLUEJET_MAX_ROWS_PER_EVIDENCE > 0 and len(rows_out) >= BLUEJET_MAX_ROWS_PER_EVIDENCE:
                    stop_reason = f"row_cap:{BLUEJET_MAX_ROWS_PER_EVIDENCE}"
                    return rows_out, offset, pages, stop_reason
        if len(rows) < limit:
            stop_reason = "last_page_short"
            break
        offset += limit
    return rows_out, offset, pages, stop_reason


def process_evidence(
    run_id: str,
    bj: BlueJetClient,
    qdr: QdrantClient,
    cfg: EvidenceConfig,
    dry_run: bool = False,
) -> tuple[int, int, int]:
    dim = qdr.get_collection_dim(cfg.collection) if not dry_run else 0
    rows, last_offset, pages, stop_reason = iter_evidence_rows(bj, cfg.no, PAGE_LIMIT)
    rows_seen = len(rows)
    upserted = 0
    failed = 0
    log(
        "run=%s evidence=%s collection=%s rows_seen=%s pages=%s offset=%s stop=%s"
        % (run_id, cfg.no, cfg.collection, rows_seen, pages, last_offset, stop_reason)
    )

    batch_size = max(1, BLUEJET_QDRANT_BATCH_SIZE)
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        points: list[dict[str, Any]] = []

        pid_to_row: dict[str, dict[str, Any]] = {}
        point_ids: list[str] = []
        for row in batch:
            bj_id = choose_business_id(row, cfg.id_fields, fallback=f"ev{cfg.no}")
            pid = stable_point_id(cfg.collection, bj_id)
            point_ids.append(pid)
            pid_to_row[pid] = row

        existing_vectors = {} if dry_run else qdr.get_existing_vectors(cfg.collection, point_ids)
        now_ts = int(time.time())

        for pid in point_ids:
            row = pid_to_row[pid]
            bj_id = choose_business_id(row, cfg.id_fields, fallback=f"ev{cfg.no}")
            payload = dict(row)
            payload["evidence_no"] = cfg.no
            payload["bj_id"] = bj_id
            payload["imported_at"] = now_ts
            payload["mirror_run_id"] = run_id
            payload["searchable_text"] = searchable_text(row, cfg.searchable_fields)
            if dry_run:
                points.append({"id": pid, "payload": payload})
            else:
                vec = existing_vectors.get(pid)
                if vec is None:
                    vec = placeholder_vector(dim, f"{cfg.collection}:{bj_id}")
                points.append({"id": pid, "vector": vec, "payload": payload})

        try:
            if dry_run:
                upserted += len(points)
                audit(
                    {
                        "ts": now_ts,
                        "run_id": run_id,
                        "evidence_no": cfg.no,
                        "collection": cfg.collection,
                        "pages": pages,
                        "stop_reason": stop_reason,
                        "status": "dry_run",
                        "count": len(points),
                        "first_id": points[0]["id"] if points else "",
                        "last_id": points[-1]["id"] if points else "",
                    }
                )
            else:
                qdr.upsert_points(cfg.collection, points)
                upserted += len(points)
                audit(
                    {
                        "ts": now_ts,
                        "run_id": run_id,
                        "evidence_no": cfg.no,
                        "collection": cfg.collection,
                        "pages": pages,
                        "stop_reason": stop_reason,
                        "status": "ok",
                        "count": len(points),
                        "first_id": points[0]["id"] if points else "",
                        "last_id": points[-1]["id"] if points else "",
                    }
                )
                if BLUEJET_QDRANT_BATCH_PAUSE_SECONDS > 0:
                    time.sleep(BLUEJET_QDRANT_BATCH_PAUSE_SECONDS)
        except Exception as e:
            failed += len(points)
            audit(
                {
                    "ts": now_ts,
                    "run_id": run_id,
                    "evidence_no": cfg.no,
                    "collection": cfg.collection,
                    "pages": pages,
                    "stop_reason": stop_reason,
                    "status": "error",
                    "count": len(points),
                    "error": str(e)[:400],
                }
            )
            log(f"run={run_id} evidence={cfg.no} upsert_error={e}")
        if BLUEJET_MAX_POINTS_PER_RUN > 0 and upserted >= BLUEJET_MAX_POINTS_PER_RUN:
            log(
                f"run={run_id} evidence={cfg.no} stop=max_points_per_run reached "
                f"({upserted}/{BLUEJET_MAX_POINTS_PER_RUN})"
            )
            break

    return rows_seen, upserted, failed


def parse_evidence_selection() -> set[int]:
    raw = (os.environ.get("BLUEJET_MIRROR_EVIDENCES") or "").strip()
    if not raw:
        return {e.no for e in EVIDENCES}
    out: set[int] = set()
    for p in raw.split(","):
        p = p.strip()
        if not p:
            continue
        out.add(int(p))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Mirror BlueJet entities into Qdrant collections")
    ap.add_argument("--evidences", help="Comma-separated evidence numbers override")
    ap.add_argument("--dry-run", action="store_true", help="Fetch and build payloads only, no Qdrant writes")
    args = ap.parse_args()

    if args.evidences:
        os.environ["BLUEJET_MIRROR_EVIDENCES"] = args.evidences

    selected = parse_evidence_selection()
    selected_cfg = [e for e in EVIDENCES if e.no in selected]
    if not selected_cfg:
        raise RuntimeError("No evidences selected.")

    run_id = time.strftime("%Y%m%d-%H%M%S")
    started = int(time.time())
    conn = ensure_state_db()
    conn.execute(
        "INSERT INTO mirror_runs (run_id, started_at, status, summary_json) VALUES (?, ?, 'running', '{}')",
        (run_id, started),
    )
    conn.commit()

    token_id = resolve_secret(BLUEJET_API_TOKEN_ID, BLUEJET_API_TOKEN_ID_OP_REF)
    token_hash = resolve_secret(BLUEJET_API_TOKEN_HASH, BLUEJET_API_TOKEN_HASH_OP_REF)
    direct_token = resolve_secret(BLUEJET_API_DIRECT_TOKEN, BLUEJET_API_DIRECT_TOKEN_OP_REF)
    if direct_token and (not token_id or not token_hash):
        # Compatibility fallback for environments that expose only one value.
        token_id = token_id or direct_token
        token_hash = token_hash or direct_token
    bj = BlueJetClient(BLUEJET_BASE_URL, token_id, token_hash, direct_token=direct_token)
    qdr = QdrantClient(QDRANT_URL, QDRANT_API_KEY)

    summary: dict[str, Any] = {"run_id": run_id, "qdrant_url": QDRANT_URL, "rows_seen": 0, "rows_upserted": 0, "rows_failed": 0}
    status = "ok"

    try:
        for cfg in selected_cfg:
            rows_seen, upserted, failed = process_evidence(run_id, bj, qdr, cfg, dry_run=args.dry_run)
            summary["rows_seen"] += rows_seen
            summary["rows_upserted"] += upserted
            summary["rows_failed"] += failed
            conn.execute(
                """
                INSERT OR REPLACE INTO mirror_run_evidence
                (run_id, evidence_no, collection, rows_seen, rows_upserted, rows_failed, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, cfg.no, cfg.collection, rows_seen, upserted, failed, int(time.time())),
            )
            conn.commit()
            if BLUEJET_EVIDENCE_PAUSE_SECONDS > 0:
                time.sleep(BLUEJET_EVIDENCE_PAUSE_SECONDS)
    except Exception as e:
        status = "error"
        summary["error"] = str(e)
        log(f"run={run_id} fatal_error={e}")
        raise
    finally:
        finished = int(time.time())
        conn.execute(
            "UPDATE mirror_runs SET finished_at = ?, status = ?, summary_json = ? WHERE run_id = ?",
            (finished, status, json.dumps(summary, ensure_ascii=False), run_id),
        )
        conn.commit()
        conn.close()
        audit({"ts": finished, "run_id": run_id, "status": status, "summary": summary})
        print(json.dumps({"status": status, "summary": summary}, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
