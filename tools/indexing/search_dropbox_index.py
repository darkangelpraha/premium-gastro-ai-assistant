#!/usr/bin/env python3
import os
import sys
import json
import time
import sqlite3
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode


QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") or os.environ.get("QDRANT_APIKEY")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "dropbox_semantic_index")

SNIPPETS_DB = os.environ.get(
    "QDRANT_SNIPPETS_DB",
    str(Path.cwd() / ".cache" / "qdrant_dropbox_snippets.sqlite"),
)

EMBEDDING_PROVIDER = os.environ.get("QDRANT_EMBEDDING_PROVIDER", "auto").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "nomic-embed-text")
OLLAMA_EMBED_ENDPOINT = os.environ.get("OLLAMA_EMBED_ENDPOINT", "/api/embed")

HTTP_CONNECT_TIMEOUT = float(os.environ.get("INDEX_HTTP_CONNECT_TIMEOUT", "3"))
HTTP_MAX_TIME = float(os.environ.get("INDEX_HTTP_MAX_TIME", "60"))


def http_json(method: str, url: str, payload: Any = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    import subprocess

    cmd = [
        "curl",
        "-sS",
        "--connect-timeout",
        str(HTTP_CONNECT_TIMEOUT),
        "--max-time",
        str(HTTP_MAX_TIME),
        "-X",
        method,
        url,
        "-H",
        "Content-Type: application/json",
        "-w",
        "\n__HTTP_STATUS__%{http_code}",
    ]
    if headers:
        for k, v in headers.items():
            cmd.extend(["-H", f"{k}: {v}"])
    if payload is not None:
        cmd.extend(["--data-binary", json.dumps(payload)])
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    out = res.stdout or ""
    if "__HTTP_STATUS__" not in out:
        raise RuntimeError(f"Bad HTTP response: {out[:200]}")
    body, status_s = out.rsplit("__HTTP_STATUS__", 1)
    status = int(status_s.strip() or "0")
    if status < 200 or status >= 300:
        raise RuntimeError(f"HTTP {status}: {body[:200]}")
    try:
        return json.loads(body) if body.strip() else {}
    except Exception:
        return {"raw": body}


def qdrant_headers() -> Dict[str, str]:
    h: Dict[str, str] = {}
    if QDRANT_API_KEY:
        h["api-key"] = QDRANT_API_KEY
    return h


def qdrant_params(**kwargs: Any) -> str:
    filtered = {k: v for k, v in kwargs.items() if v is not None}
    if not filtered:
        return ""
    return "?" + urlencode(filtered)


def choose_provider() -> str:
    if EMBEDDING_PROVIDER != "auto":
        return EMBEDDING_PROVIDER
    if OPENAI_API_KEY:
        return "openai"
    return "ollama"


def embed_query_ollama(text: str) -> List[float]:
    payload = {"model": OLLAMA_MODEL, "input": [text]}
    res = http_json("POST", f"{OLLAMA_HOST}{OLLAMA_EMBED_ENDPOINT}", payload)
    if "embeddings" in res and isinstance(res["embeddings"], list) and res["embeddings"]:
        return res["embeddings"][0]
    raise RuntimeError(f"Unexpected Ollama embed response: {str(res)[:200]}")


def embed_query_openai(text: str) -> List[float]:
    import subprocess

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY missing")
    payload = {"model": OPENAI_EMBED_MODEL, "input": text}
    cmd = [
        "curl",
        "-sS",
        "--connect-timeout",
        str(HTTP_CONNECT_TIMEOUT),
        "--max-time",
        str(HTTP_MAX_TIME),
        "-X",
        "POST",
        "https://api.openai.com/v1/embeddings",
        "-H",
        "Content-Type: application/json",
        "-H",
        f"Authorization: Bearer {OPENAI_API_KEY}",
        "--data-binary",
        json.dumps(payload),
        "-w",
        "\n__HTTP_STATUS__%{http_code}",
    ]
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    out = res.stdout or ""
    if "__HTTP_STATUS__" not in out:
        raise RuntimeError(f"Bad HTTP response: {out[:200]}")
    body, status_s = out.rsplit("__HTTP_STATUS__", 1)
    status = int(status_s.strip() or "0")
    if status < 200 or status >= 300:
        raise RuntimeError(f"HTTP {status}: {body[:200]}")
    js = json.loads(body)
    return js["data"][0]["embedding"]


def embed_query(text: str) -> List[float]:
    provider = choose_provider()
    if provider == "ollama":
        return embed_query_ollama(text)
    if provider == "openai":
        return embed_query_openai(text)
    raise RuntimeError(f"Unsupported provider: {provider}")


def qdrant_vector_search(vec: List[float], limit: int) -> List[Dict[str, Any]]:
    payload = {
        "vector": vec,
        "limit": int(limit),
        "with_payload": True,
    }
    res = http_json(
        "POST",
        f"{QDRANT_URL}/collections/{COLLECTION}/points/search{qdrant_params()}",
        payload,
        headers=qdrant_headers(),
    )
    return res.get("result", []) or []


def snippets_connect() -> Optional[sqlite3.Connection]:
    p = Path(SNIPPETS_DB)
    if not p.exists():
        return None
    conn = sqlite3.connect(str(p), timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return conn


def snippets_by_point_ids(conn: sqlite3.Connection, point_ids: List[str]) -> Dict[str, str]:
    if not point_ids:
        return {}
    out: Dict[str, str] = {}
    # SQLite has a variable limit; keep batches small.
    step = 200
    for i in range(0, len(point_ids), step):
        batch = point_ids[i : i + step]
        qs = ",".join(["?"] * len(batch))
        cur = conn.execute(f"SELECT point_id, text FROM chunks WHERE point_id IN ({qs})", batch)
        for pid, txt in cur.fetchall():
            out[str(pid)] = str(txt or "")
    return out


def fts_search(conn: sqlite3.Connection, query: str, limit: int) -> List[Dict[str, Any]]:
    # Prefer FTS (if present), else fall back to LIKE on chunks.text.
    has_fts = False
    try:
        cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks_fts'")
        has_fts = cur.fetchone() is not None
    except Exception:
        has_fts = False

    rows: List[Dict[str, Any]] = []
    if has_fts:
        cur = conn.execute(
            """
            SELECT chunks.point_id, chunks.path, chunks.chunk_index, chunks.chunk_total, substr(chunks.text, 1, 800) as snippet
            FROM chunks_fts
            JOIN chunks ON chunks.rowid = chunks_fts.rowid
            WHERE chunks_fts MATCH ?
            LIMIT ?
            """,
            (query, int(limit)),
        )
        for pid, path, chunk_index, chunk_total, snippet in cur.fetchall():
            rows.append(
                {
                    "id": str(pid),
                    "payload": {
                        "path": path,
                        "chunk_index": int(chunk_index or 0),
                        "chunk_total": int(chunk_total or 0),
                        "preview": snippet or "",
                    },
                    "score": None,
                    "source": "fts",
                }
            )
        return rows

    cur = conn.execute(
        "SELECT point_id, path, chunk_index, chunk_total, substr(text, 1, 800) FROM chunks WHERE text LIKE ? LIMIT ?",
        (f"%{query}%", int(limit)),
    )
    for pid, path, chunk_index, chunk_total, snippet in cur.fetchall():
        rows.append(
            {
                "id": str(pid),
                "payload": {
                    "path": path,
                    "chunk_index": int(chunk_index or 0),
                    "chunk_total": int(chunk_total or 0),
                    "preview": snippet or "",
                },
                "score": None,
                "source": "like",
            }
        )
    return rows


def rrf_merge(a: List[Dict[str, Any]], b: List[Dict[str, Any]], k: int = 60) -> List[Dict[str, Any]]:
    # Reciprocal Rank Fusion; keeps things simple and robust across different score scales.
    scores: Dict[str, float] = {}
    items: Dict[str, Dict[str, Any]] = {}
    for lst in (a, b):
        for rank, item in enumerate(lst, start=1):
            pid = str(item.get("id") or "")
            if not pid:
                continue
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (k + rank)
            items[pid] = item
    merged = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    out: List[Dict[str, Any]] = []
    for pid, s in merged:
        it = items[pid]
        it["rrf_score"] = s
        out.append(it)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: search_dropbox_index.py <query> [--limit N] [--fts] [--hybrid]")
        return 2

    args = sys.argv[1:]
    limit = 10
    mode_fts = False
    mode_hybrid = False
    query_parts: List[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
            continue
        if args[i] == "--fts":
            mode_fts = True
            i += 1
            continue
        if args[i] == "--hybrid":
            mode_hybrid = True
            i += 1
            continue
        query_parts.append(args[i])
        i += 1
    query = " ".join(query_parts).strip()
    if not query:
        print("Missing query.")
        return 2

    t0 = time.time()
    vec_results: List[Dict[str, Any]] = []
    if not mode_fts:
        vec = embed_query(query)
        vec_results = qdrant_vector_search(vec, limit=max(10, limit))
        for r in vec_results:
            r["source"] = "vector"

    snip_conn = snippets_connect()
    fts_results: List[Dict[str, Any]] = []
    if (mode_fts or mode_hybrid) and snip_conn is not None:
        fts_results = fts_search(snip_conn, query, limit=max(10, limit))

    results: List[Dict[str, Any]]
    if mode_hybrid and fts_results:
        results = rrf_merge(vec_results, fts_results)[:limit]
    elif mode_fts:
        results = fts_results[:limit]
    else:
        results = vec_results[:limit]

    # If snippets DB exists, enrich previews from there (more consistent than payload previews).
    if snip_conn is not None and results:
        pids = [str(r.get("id") or "") for r in results]
        pid2txt = snippets_by_point_ids(snip_conn, pids)
        for r in results:
            pid = str(r.get("id") or "")
            if pid in pid2txt and pid2txt[pid]:
                r.setdefault("payload", {})
                r["payload"]["preview"] = pid2txt[pid][:800]
    if snip_conn is not None:
        try:
            snip_conn.close()
        except Exception:
            pass

    dt_ms = int((time.time() - t0) * 1000)
    print(json.dumps({"query": query, "limit": limit, "mode": "hybrid" if mode_hybrid else ("fts" if mode_fts else "vector"), "ms": dt_ms}))
    for r in results:
        payload = r.get("payload") or {}
        path = payload.get("path") or ""
        chunk_index = payload.get("chunk_index")
        score = r.get("score")
        preview = (payload.get("preview") or "").replace("\n", " ").strip()
        if len(preview) > 200:
            preview = preview[:200] + "..."
        print(
            json.dumps(
                {
                    "score": score,
                    "path": path,
                    "chunk_index": chunk_index,
                    "preview": preview,
                    "source": r.get("source"),
                    "rrf_score": r.get("rrf_score"),
                }
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

