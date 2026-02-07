#!/usr/bin/env python3
import os
import sys
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode


QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") or os.environ.get("QDRANT_APIKEY")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "dropbox_semantic_index")

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
    return json.loads(body) if body.strip() else {}


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


def load_queries(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        items.append(json.loads(line))
    return items


def is_match(result: Dict[str, Any], expect_any: List[str]) -> bool:
    payload = result.get("payload") or {}
    path = str(payload.get("path") or "")
    preview = str(payload.get("preview") or "")
    hay = (path + "\n" + preview).lower()
    return any(str(x).lower() in hay for x in expect_any if str(x).strip())


def main() -> int:
    if "--queries" not in sys.argv:
        print("Usage: eval_index.py --queries <queries.jsonl> [--k N]")
        return 2
    qpath = Path(sys.argv[sys.argv.index("--queries") + 1])
    k = 10
    if "--k" in sys.argv:
        k = int(sys.argv[sys.argv.index("--k") + 1])
    if not qpath.exists():
        print(f"Missing queries file: {qpath}")
        return 2

    queries = load_queries(qpath)
    if not queries:
        print("No queries found.")
        return 2

    total = 0
    passed = 0
    lat_ms: List[int] = []

    for item in queries:
        q = str(item.get("query") or "").strip()
        if not q:
            continue
        expect_any = item.get("expect_any") or []
        if isinstance(expect_any, str):
            expect_any = [expect_any]
        expect_any = [str(x) for x in expect_any if str(x).strip()]
        kk = int(item.get("k") or k)
        t0 = time.time()
        vec = embed_query(q)
        results = qdrant_vector_search(vec, kk)
        dt = int((time.time() - t0) * 1000)
        lat_ms.append(dt)
        total += 1
        ok = True if not expect_any else any(is_match(r, expect_any) for r in results)
        if ok:
            passed += 1
        print(json.dumps({"query": q, "k": kk, "ok": ok, "ms": dt, "top_path": (results[0].get("payload") or {}).get("path") if results else ""}))

    avg = int(sum(lat_ms) / max(1, len(lat_ms)))
    p95 = sorted(lat_ms)[int(0.95 * (len(lat_ms) - 1))] if lat_ms else 0
    print(json.dumps({"total": total, "passed": passed, "pass_rate": (passed / max(1, total)), "avg_ms": avg, "p95_ms": p95}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

