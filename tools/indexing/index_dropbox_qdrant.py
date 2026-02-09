#!/usr/bin/env python3
import os
import sys
import json
import time
import hashlib
import mimetypes
import subprocess
import uuid
import sqlite3
import shutil
import zipfile
from io import BytesIO
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Tuple, Dict, Any, List, Optional
from urllib.parse import urlencode
from xml.etree import ElementTree as ET

INDEXER_VERSION = "2026-02-07.ollama-embed-batch-state-v4-snippets-ocr-ooxml"

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY") or os.environ.get("QDRANT_APIKEY")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "dropbox_semantic_index")
VECTOR_SIZE = int(os.environ.get("QDRANT_VECTOR_SIZE", "0"))  # 0 = auto-detect
BATCH_SIZE = int(os.environ.get("QDRANT_BATCH_SIZE", "16"))  # points per upsert
MAX_BYTES = int(os.environ.get("QDRANT_MAX_BYTES", str(2 * 1024 * 1024)))  # 2MB per file
MAX_CHARS = int(os.environ.get("QDRANT_MAX_CHARS", "12000"))
CHUNK_SIZE = int(os.environ.get("QDRANT_CHUNK_SIZE", "2000"))
CHUNK_OVERLAP = int(os.environ.get("QDRANT_CHUNK_OVERLAP", "200"))
PDF_MAX_PAGES = int(os.environ.get("QDRANT_PDF_MAX_PAGES", "30"))
SAMPLE_WINDOWS = int(os.environ.get("QDRANT_SAMPLE_WINDOWS", "5"))
MAX_CHUNKS_PER_FILE = int(os.environ.get("QDRANT_MAX_CHUNKS_PER_FILE", "32"))
XLSX_MAX_CELLS = int(os.environ.get("QDRANT_XLSX_MAX_CELLS", "20000"))
EMBED_CONCURRENCY = int(os.environ.get("QDRANT_EMBED_CONCURRENCY", "2"))
EMBED_CACHE_SIZE = int(os.environ.get("QDRANT_EMBED_CACHE_SIZE", "5000"))
DEDUP_EMBEDDINGS = os.environ.get("QDRANT_DEDUP_EMBEDDINGS", "1") != "0"
DEDUP_FILES = os.environ.get("QDRANT_DEDUP_FILES", "1") != "0"
DEDUP_HASH_BYTES = int(os.environ.get("QDRANT_DEDUP_HASH_BYTES", str(256 * 1024)))
DEDUP_HASH_SUFFIX_BYTES = int(os.environ.get("QDRANT_DEDUP_HASH_SUFFIX_BYTES", str(256 * 1024)))
CREATE_PAYLOAD_INDEXES = os.environ.get("QDRANT_CREATE_PAYLOAD_INDEXES", "1") != "0"
PAYLOAD_INDEX_ON_DISK = os.environ.get("QDRANT_PAYLOAD_INDEX_ON_DISK", "0") == "1"
MTIME_IS_PRINCIPAL = os.environ.get("QDRANT_MTIME_IS_PRINCIPAL", "1") != "0"
QDRANT_WAIT = os.environ.get("QDRANT_WAIT", "1") != "0"
QDRANT_ORDERING = os.environ.get("QDRANT_ORDERING", "weak").lower()
AUDIT_PATH = os.environ.get("QDRANT_AUDIT_PATH", "/tmp/qdrant_dropbox_audit.jsonl")
LOG_PATH = os.environ.get("QDRANT_LOG_PATH", "/tmp/qdrant_dropbox_index.log")
MAX_FILES = int(os.environ.get("QDRANT_MAX_FILES", "0"))  # 0 = no limit
STATE_DB = os.environ.get(
    "QDRANT_STATE_DB",
    str(Path.cwd() / ".cache" / "qdrant_dropbox_state.sqlite"),
)

SNIPPETS_ENABLED = os.environ.get("QDRANT_SNIPPETS_ENABLED", "1") != "0"
SNIPPETS_DB = os.environ.get(
    "QDRANT_SNIPPETS_DB",
    str(Path.cwd() / ".cache" / "qdrant_dropbox_snippets.sqlite"),
)
SNIPPET_MAX_CHARS = int(os.environ.get("QDRANT_SNIPPET_MAX_CHARS", "800"))  # 0 = store full text (not recommended)
SNIPPETS_FTS = os.environ.get("QDRANT_SNIPPETS_FTS", "1") != "0"
PAYLOAD_PREVIEW_MAX_CHARS = int(os.environ.get("QDRANT_PAYLOAD_PREVIEW_MAX_CHARS", "400"))  # 0 = store full chunk text

OCR_SIDECAR_DIR = os.environ.get(
    "QDRANT_OCR_SIDECAR_DIR",
    str(Path.cwd() / ".cache" / "ocr_sidecars"),
)
OCR_PDF_MIN_TEXT_CHARS = int(os.environ.get("QDRANT_OCR_PDF_MIN_TEXT_CHARS", "200"))
OCR_IMAGES_ENABLED = os.environ.get("QDRANT_OCR_IMAGES", "0") == "1"

QDRANT_OP_RETRIES = int(os.environ.get("QDRANT_OP_RETRIES", "10"))
QDRANT_OP_RETRY_SLEEP_SECONDS = float(os.environ.get("QDRANT_OP_RETRY_SLEEP_SECONDS", "2"))
QDRANT_OP_MAX_SLEEP_SECONDS = float(os.environ.get("QDRANT_OP_MAX_SLEEP_SECONDS", "60"))
QDRANT_STARTUP_WAIT_SECONDS = int(os.environ.get("QDRANT_STARTUP_WAIT_SECONDS", "30"))
EXCLUDE_DIR_NAMES = {
    s.strip()
    for s in os.environ.get("QDRANT_EXCLUDE_DIRS", ".dropbox.cache,.git,.hg,.svn,node_modules,.venv").split(",")
    if s.strip()
}
EXCLUDE_FILE_NAMES = {
    s.strip()
    for s in os.environ.get("QDRANT_EXCLUDE_FILES", ".DS_Store,Thumbs.db,desktop.ini").split(",")
    if s.strip()
}

EMBEDDING_PROVIDER = os.environ.get("QDRANT_EMBEDDING_PROVIDER", "auto").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "nomic-embed-text")
OLLAMA_EMBED_ENDPOINT = os.environ.get("OLLAMA_EMBED_ENDPOINT", "/api/embed")
OLLAMA_EMBED_LEGACY_ENDPOINT = os.environ.get("OLLAMA_EMBED_LEGACY_ENDPOINT", "/api/embeddings")
OLLAMA_TRUNCATE = os.environ.get("OLLAMA_TRUNCATE", "1") != "0"
OLLAMA_KEEP_ALIVE = os.environ.get("OLLAMA_KEEP_ALIVE", "5m")
OLLAMA_USE_BATCH = os.environ.get("OLLAMA_USE_BATCH", "1") != "0"
OLLAMA_BATCH_SIZE = int(os.environ.get("OLLAMA_BATCH_SIZE", "32"))
EMBED_MAX_CHARS = int(os.environ.get("QDRANT_EMBED_MAX_CHARS", "8000"))  # 0 = no clamp

def discover_dropbox_roots() -> List[str]:
    base = Path.home() / "Library" / "CloudStorage"
    if not base.exists():
        return []
    roots = [p for p in base.glob("Dropbox*") if p.is_dir()]
    # Prefer the canonical "Dropbox" first if present, then stable order.
    roots_sorted = sorted(roots, key=lambda p: (p.name != "Dropbox", p.name.lower()))
    return [str(p) for p in roots_sorted]


DEFAULT_ROOTS = discover_dropbox_roots()

TEXT_EXTS = {
    ".txt", ".md", ".markdown", ".csv", ".tsv", ".json", ".yaml", ".yml",
    ".log", ".ini", ".conf", ".toml", ".xml", ".html", ".htm",
}

HTTP_CONNECT_TIMEOUT = float(os.environ.get("INDEX_HTTP_CONNECT_TIMEOUT", "3"))
HTTP_MAX_TIME = float(os.environ.get("INDEX_HTTP_MAX_TIME", "60"))
HTTP_RETRIES = int(os.environ.get("INDEX_HTTP_RETRIES", "2"))
HTTP_RETRY_SLEEP_SECONDS = float(os.environ.get("INDEX_HTTP_RETRY_SLEEP_SECONDS", "1"))


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}\n"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)


def http_json(method: str, url: str, payload: Any = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Lightweight HTTP JSON helper with retries.

    We intentionally avoid shelling out to curl:
    - improves performance (no subprocess per request)
    - avoids curl-specific error strings and timeouts
    - makes retry/timeout behavior consistent across hosts
    """
    import socket
    from urllib import error, request

    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    data_bytes: Optional[bytes] = None
    if payload is not None:
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    last_err = ""
    for attempt in range(HTTP_RETRIES + 1):
        try:
            req = request.Request(url, data=data_bytes, headers=req_headers, method=method)
            with request.urlopen(req, timeout=float(HTTP_MAX_TIME)) as resp:
                raw = resp.read()
                body = raw.decode("utf-8", "replace").strip()
                if body:
                    try:
                        return json.loads(body)
                    except Exception:
                        return {"_raw": body[:2000]}
                return {}
        except error.HTTPError as e:
            raw = e.read(2000)
            body = raw.decode("utf-8", "replace").strip()
            msg = body[:200] if body else str(e)
            raise RuntimeError(f"HTTP {e.code} {method} {url}: {msg}")
        except (error.URLError, socket.timeout, TimeoutError, ConnectionResetError, ConnectionAbortedError) as e:
            last_err = str(e) or repr(e)
            retryable = True
            if attempt < HTTP_RETRIES and retryable:
                time.sleep(HTTP_RETRY_SLEEP_SECONDS * (attempt + 1))
                continue
            break
        except Exception as e:
            last_err = str(e) or repr(e)
            break
    raise RuntimeError(last_err or "http_json failed")


def qdrant_check(res: Dict[str, Any]) -> Dict[str, Any]:
    status = res.get("status")
    if status and status != "ok":
        msg = res.get("message") or res.get("result") or str(res)
        raise RuntimeError(f"Qdrant error: {msg}")
    return res


def qdrant_headers() -> Dict[str, str]:
    if not QDRANT_API_KEY:
        return {}
    return {"api-key": QDRANT_API_KEY}


def qdrant_params(wait: Optional[bool] = None, ordering: Optional[str] = None) -> str:
    qp: Dict[str, str] = {}
    if wait is not None:
        qp["wait"] = "true" if wait else "false"
    if ordering:
        ordering_l = ordering.lower()
        if ordering_l not in ("weak", "medium", "strong"):
            raise RuntimeError(f"Invalid QDRANT_ORDERING={ordering!r} (expected weak|medium|strong)")
        qp["ordering"] = ordering_l
    return ("?" + urlencode(qp)) if qp else ""


def qdrant_get(path: str) -> Dict[str, Any]:
    return qdrant_check(http_json("GET", QDRANT_URL + path, headers=qdrant_headers()))


def qdrant_put(path: str, payload: Any) -> Dict[str, Any]:
    return qdrant_check(http_json("PUT", QDRANT_URL + path, payload, headers=qdrant_headers()))

def qdrant_post(path: str, payload: Any) -> Dict[str, Any]:
    return qdrant_check(http_json("POST", QDRANT_URL + path, payload, headers=qdrant_headers()))


def collection_exists(name: str) -> bool:
    try:
        r = qdrant_get("/collections")
        cols = {c["name"] for c in r.get("result", {}).get("collections", [])}
        return name in cols
    except Exception:
        return False


def ensure_collection(name: str) -> None:
    if collection_exists(name):
        try:
            info = qdrant_get(f"/collections/{name}")
            size = info.get("result", {}).get("config", {}).get("params", {}).get("vectors", {}).get("size")
            if size and int(size) != int(VECTOR_SIZE):
                raise RuntimeError(
                    f"Collection '{name}' exists with size {size}, expected {VECTOR_SIZE}. "
                    f"Set QDRANT_COLLECTION to a new name."
                )
        except Exception:
            raise
        return
    payload = {
        "vectors": {
            "size": VECTOR_SIZE,
            "distance": "Cosine"
        }
    }
    qdrant_put(f"/collections/{name}", payload)


def wait_for_qdrant() -> None:
    while True:
        try:
            qdrant_get("/collections")
            return
        except Exception as e:
            log(f"qdrant_unreachable url={QDRANT_URL} err={e}")
            time.sleep(max(1, int(QDRANT_STARTUP_WAIT_SECONDS)))


def embed_text_openai(text: str) -> List[float]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing")
    payload = {
        "model": OPENAI_EMBED_MODEL,
        "input": text,
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    res = http_json("POST", "https://api.openai.com/v1/embeddings", payload, headers=headers)
    return res["data"][0]["embedding"]


def clamp_embedding_text(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    if EMBED_MAX_CHARS > 0 and len(text) > EMBED_MAX_CHARS:
        return text[:EMBED_MAX_CHARS]
    return text


def embed_texts_ollama_modern(texts: List[str]) -> List[List[float]]:
    payload: Dict[str, Any] = {"model": OLLAMA_MODEL, "input": texts}
    if OLLAMA_TRUNCATE:
        payload["truncate"] = True
    else:
        payload["truncate"] = False
    if OLLAMA_KEEP_ALIVE:
        payload["keep_alive"] = OLLAMA_KEEP_ALIVE
    res = http_json("POST", f"{OLLAMA_HOST}{OLLAMA_EMBED_ENDPOINT}", payload)
    embs = res.get("embeddings")
    if not isinstance(embs, list) or not embs:
        raise RuntimeError(f"Ollama /api/embed response missing 'embeddings': {str(res)[:200]}")
    if len(embs) != len(texts):
        raise RuntimeError(f"Ollama /api/embed embeddings count mismatch: got={len(embs)} expected={len(texts)}")
    return embs  # type: ignore[return-value]


def embed_text_ollama_legacy(text: str) -> List[float]:
    payload: Dict[str, Any] = {"model": OLLAMA_MODEL, "prompt": text}
    res = http_json("POST", f"{OLLAMA_HOST}{OLLAMA_EMBED_LEGACY_ENDPOINT}", payload)
    if "embedding" not in res:
        raise RuntimeError(f"Ollama legacy embedding response missing 'embedding': {str(res)[:200]}")
    return res["embedding"]


def choose_provider() -> str:
    if EMBEDDING_PROVIDER != "auto":
        return EMBEDDING_PROVIDER
    if OPENAI_API_KEY:
        return "openai"
    return "ollama"


def read_text(path: Path, max_chars: Optional[int] = None) -> Tuple[str, int]:
    try:
        with path.open("rb") as f:
            data = f.read(MAX_BYTES)
    except Exception:
        return "", 0
    try:
        text = data.decode("utf-8", errors="ignore")
    except Exception:
        text = ""
    budget = MAX_CHARS if max_chars is None else max(0, int(max_chars))
    if budget and len(text) > budget:
        text = text[:budget]
    return text, len(data)


def read_text_window(f, offset: int, limit: int) -> str:
    try:
        f.seek(max(0, offset), os.SEEK_SET)
        data = f.read(max(0, limit))
    except Exception:
        return ""
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def page_sample_indices(total_pages: int, max_pages: int) -> List[int]:
    if total_pages <= 0:
        return []
    if max_pages <= 0 or total_pages <= max_pages:
        return list(range(total_pages))
    if max_pages == 1:
        return [0]
    last = total_pages - 1
    idxs = [int(round(i * last / (max_pages - 1))) for i in range(max_pages)]
    # de-dupe while preserving order
    seen = set()
    out = []
    for i in idxs:
        if i not in seen:
            out.append(i)
            seen.add(i)
    return out


def indices_to_ranges(pages_1based: List[int]) -> List[Tuple[int, int]]:
    if not pages_1based:
        return []
    pages = sorted(set(int(p) for p in pages_1based if int(p) > 0))
    ranges: List[Tuple[int, int]] = []
    start = pages[0]
    end = pages[0]
    for p in pages[1:]:
        if p == end + 1:
            end = p
            continue
        ranges.append((start, end))
        start = p
        end = p
    ranges.append((start, end))
    return ranges


def cmd_exists(name: str) -> bool:
    try:
        return shutil.which(name) is not None
    except Exception:
        return False


def pdf_page_count(path: Path) -> int:
    if not cmd_exists("pdfinfo"):
        return 0
    try:
        res = subprocess.run(
            ["pdfinfo", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = (res.stdout or "") + "\n" + (res.stderr or "")
        for line in out.splitlines():
            if line.lower().startswith("pages:"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return int(parts[1].strip())
    except Exception:
        return 0
    return 0


def extract_pdf_text_pdftotext(path: Path, max_pages: int) -> str:
    if not cmd_exists("pdftotext"):
        return ""
    pages = pdf_page_count(path)
    if pages <= 0:
        # pdftotext still might work, but prefer bounded work.
        pages = 1
    idxs0 = page_sample_indices(pages, max_pages)
    pages_1based = [i + 1 for i in idxs0]
    ranges = indices_to_ranges(pages_1based)
    parts: List[str] = []
    for start, end in ranges:
        try:
            res = subprocess.run(
                ["pdftotext", "-f", str(start), "-l", str(end), "-layout", "-nopgbrk", str(path), "-"],
                check=False,
                capture_output=True,
                timeout=60,
            )
            if res.stdout:
                parts.append(res.stdout.decode("utf-8", errors="ignore"))
        except Exception:
            continue
    return "\n".join(parts)


def chunks_fingerprint(chunks: List[str]) -> str:
    h = hashlib.sha256()
    for c in chunks:
        h.update(c.encode("utf-8", errors="ignore"))
        h.update(b"\0")
    return h.hexdigest()


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTS:
        return True
    mt, _ = mimetypes.guess_type(str(path))
    return bool(mt and mt.startswith("text/"))


def iter_files(roots: List[str]) -> Iterable[Path]:
    for root in roots:
        if not os.path.exists(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            if EXCLUDE_DIR_NAMES:
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
            for name in filenames:
                if name in EXCLUDE_FILE_NAMES:
                    continue
                if name.startswith("._"):
                    continue
                yield Path(dirpath) / name


def upsert_batch(points: List[Dict[str, Any]]) -> None:
    if not points:
        return
    payload = {"points": points}
    last_err = ""
    for attempt in range(QDRANT_OP_RETRIES + 1):
        try:
            qdrant_put(
                f"/collections/{COLLECTION}/points{qdrant_params(wait=QDRANT_WAIT, ordering=QDRANT_ORDERING)}",
                payload,
            )
            return
        except Exception as e:
            last_err = str(e)
            retryable = any(
                s in last_err.lower()
                for s in (
                    "failed to connect",
                    "couldn't connect",
                    "connection refused",
                    "timed out",
                    "empty reply",
                    "connection reset",
                )
            )
            if attempt < QDRANT_OP_RETRIES and retryable:
                sleep_s = min(QDRANT_OP_RETRY_SLEEP_SECONDS * (attempt + 1), QDRANT_OP_MAX_SLEEP_SECONDS)
                time.sleep(sleep_s)
                continue
            raise RuntimeError(last_err) from e


def count_files(roots: List[str]) -> int:
    total = 0
    for root in roots:
        if not os.path.exists(root):
            continue
        for _, dirnames, filenames in os.walk(root, onerror=lambda e: None):
            if EXCLUDE_DIR_NAMES:
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
            if EXCLUDE_FILE_NAMES:
                total += sum(1 for n in filenames if n not in EXCLUDE_FILE_NAMES and not n.startswith("._"))
            else:
                total += sum(1 for n in filenames if not n.startswith("._"))
    return total


def ensure_state_db() -> sqlite3.Connection:
    db_path = Path(STATE_DB)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # WAL + busy_timeout makes the DB far more resilient to transient locking (e.g., restarts).
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS file_state (
            path TEXT PRIMARY KEY,
            size INTEGER,
            mtime INTEGER,
            aux_mtime INTEGER,
            aux_size INTEGER,
            cfg_hash TEXT,
            complete INTEGER DEFAULT 1,
            text_hash TEXT,
            last_error TEXT,
            updated_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS content_sig (
            sig TEXT PRIMARY KEY,
            path TEXT,
            seen_at INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ocr_queue (
            path TEXT PRIMARY KEY,
            ext TEXT,
            size INTEGER,
            mtime INTEGER,
            status TEXT,
            attempts INTEGER,
            last_error TEXT,
            updated_at INTEGER
        )
        """
    )
    # Backward-compatible schema upgrades.
    cols = {r[1] for r in conn.execute("PRAGMA table_info(file_state)")}
    if "cfg_hash" not in cols:
        conn.execute("ALTER TABLE file_state ADD COLUMN cfg_hash TEXT")
    if "complete" not in cols:
        conn.execute("ALTER TABLE file_state ADD COLUMN complete INTEGER DEFAULT 1")
    if "last_error" not in cols:
        conn.execute("ALTER TABLE file_state ADD COLUMN last_error TEXT")
    if "aux_mtime" not in cols:
        conn.execute("ALTER TABLE file_state ADD COLUMN aux_mtime INTEGER")
    if "aux_size" not in cols:
        conn.execute("ALTER TABLE file_state ADD COLUMN aux_size INTEGER")
    conn.commit()
    try:
        os.chmod(str(db_path), 0o600)
    except Exception:
        pass
    return conn


def ensure_snippets_db() -> Optional[sqlite3.Connection]:
    if not SNIPPETS_ENABLED:
        return None
    db_path = Path(SNIPPETS_DB)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chunks (
            point_id TEXT PRIMARY KEY,
            path TEXT,
            chunk_index INTEGER,
            chunk_total INTEGER,
            mtime INTEGER,
            size INTEGER,
            source TEXT,
            cfg_hash TEXT,
            text_hash TEXT,
            text TEXT,
            updated_at INTEGER
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_path ON chunks(path)")

    if SNIPPETS_FTS:
        conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                text,
                content='chunks',
                content_rowid='rowid',
                tokenize='unicode61'
            )
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
              INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
              INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
            END;
            """
        )
        conn.execute(
            """
            CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
              INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.rowid, old.text);
              INSERT INTO chunks_fts(rowid, text) VALUES (new.rowid, new.text);
            END;
            """
        )

    conn.commit()
    try:
        os.chmod(str(db_path), 0o600)
    except Exception:
        pass
    return conn


def delete_snippets_for_path(conn: Optional[sqlite3.Connection], path: str) -> None:
    if conn is None:
        return
    try:
        conn.execute("DELETE FROM chunks WHERE path = ?", (path,))
    except Exception as e:
        log(f"snippets_delete_error path={path} err={e}")


def upsert_snippets(conn: Optional[sqlite3.Connection], rows: List[Tuple[Any, ...]]) -> None:
    if conn is None or not rows:
        return
    try:
        conn.executemany(
            """
            INSERT OR REPLACE INTO chunks
              (point_id, path, chunk_index, chunk_total, mtime, size, source, cfg_hash, text_hash, text, updated_at)
            VALUES
              (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    except Exception as e:
        log(f"snippets_upsert_error err={e}")


def delete_snippets_stale(conn: Optional[sqlite3.Connection], path: str, min_chunk_index: int) -> None:
    if conn is None:
        return
    try:
        conn.execute("DELETE FROM chunks WHERE path = ? AND chunk_index >= ?", (path, int(min_chunk_index)))
    except Exception as e:
        log(f"snippets_delete_stale_error path={path} err={e}")


def ocr_sidecar_path(path: Path) -> Path:
    h = hashlib.sha256(str(path).encode("utf-8", errors="ignore")).hexdigest()
    return Path(OCR_SIDECAR_DIR) / f"{h}.txt"


def ocr_sidecar_stat(path: Path) -> Tuple[int, int]:
    sp = ocr_sidecar_path(path)
    try:
        st = sp.stat()
        return int(st.st_mtime), int(st.st_size)
    except Exception:
        return 0, 0


def read_ocr_sidecar(path: Path, max_chars: int) -> str:
    sp = ocr_sidecar_path(path)
    try:
        data = sp.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    if max_chars > 0 and len(data) > max_chars:
        return data[:max_chars]
    return data


IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".bmp",
    ".gif",
    ".webp",
    ".heic",
    ".heif",
}


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTS


def enqueue_ocr(conn: sqlite3.Connection, path: Path, stat: os.stat_result, reason: str) -> None:
    p = str(path)
    ext = path.suffix.lower()
    now = int(time.time())
    try:
        row = conn.execute("SELECT status, size, mtime FROM ocr_queue WHERE path = ?", (p,)).fetchone()
        if row and (row[0] or "") == "done" and int(row[1] or 0) == int(stat.st_size) and int(row[2] or 0) == int(stat.st_mtime):
            return
        if row:
            if (row[0] or "") != "done":
                conn.execute(
                    "UPDATE ocr_queue SET ext = ?, size = ?, mtime = ?, status = 'pending', last_error = ?, updated_at = ? WHERE path = ?",
                    (ext, int(stat.st_size), int(stat.st_mtime), reason[:500], now, p),
                )
        else:
            conn.execute(
                "INSERT INTO ocr_queue (path, ext, size, mtime, status, attempts, last_error, updated_at) VALUES (?, ?, ?, ?, 'pending', 0, ?, ?)",
                (p, ext, int(stat.st_size), int(stat.st_mtime), reason[:500], now),
            )
    except Exception as e:
        log(f"ocr_queue_error path={p} err={e}")


def get_state(conn: sqlite3.Connection, path: str) -> Optional[Tuple[int, int, Optional[str], int, int, int]]:
    cur = conn.execute(
        "SELECT size, mtime, cfg_hash, COALESCE(complete, 1), COALESCE(aux_mtime, 0), COALESCE(aux_size, 0) FROM file_state WHERE path = ?",
        (path,),
    )
    row = cur.fetchone()
    return row if row else None


def set_state(
    conn: sqlite3.Connection,
    path: str,
    size: int,
    mtime: int,
    aux_mtime: int,
    aux_size: int,
    cfg_hash: str,
    complete: bool,
    text_hash: str,
    last_error: str = "",
) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO file_state (path, size, mtime, aux_mtime, aux_size, cfg_hash, complete, text_hash, last_error, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (path, size, mtime, aux_mtime, aux_size, cfg_hash, 1 if complete else 0, text_hash, last_error, int(time.time())),
    )


def get_meta(conn: sqlite3.Connection, key: str) -> Optional[str]:
    cur = conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    return row[0] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (key, value))


def compute_file_sig(path: Path, size: int) -> str:
    # Used only for deduplicating identical files across multiple roots.
    # Prefix+suffix hashing keeps reads bounded while keeping false positives extremely unlikely.
    try:
        with path.open("rb") as f:
            prefix = f.read(max(1, DEDUP_HASH_BYTES))
            prefix_h = hashlib.sha256(prefix).hexdigest()
            suffix_h = ""
            if size > max(1, DEDUP_HASH_SUFFIX_BYTES):
                try:
                    f.seek(-max(1, DEDUP_HASH_SUFFIX_BYTES), os.SEEK_END)
                    suffix = f.read(max(1, DEDUP_HASH_SUFFIX_BYTES))
                    suffix_h = hashlib.sha256(suffix).hexdigest()
                except Exception:
                    suffix_h = ""
        return f"{size}:{prefix_h}:{suffix_h}"
    except Exception:
        return ""


def is_under_any_root(path: str, roots: List[str]) -> bool:
    p = os.path.abspath(path)
    for r in roots:
        rr = os.path.abspath(r)
        if p == rr or p.startswith(rr.rstrip(os.sep) + os.sep):
            return True
    return False


def upsert_sig_canonical(conn: sqlite3.Connection, sig: str, path: str, roots: List[str]) -> Tuple[Optional[str], Optional[str]]:
    now = int(time.time())
    cur = conn.execute("SELECT path FROM content_sig WHERE sig = ?", (sig,))
    row = cur.fetchone()
    if not row:
        conn.execute(
            "INSERT INTO content_sig (sig, path, seen_at) VALUES (?, ?, ?)",
            (sig, path, now),
        )
        return None, None

    canonical = row[0]
    if canonical == path:
        conn.execute("UPDATE content_sig SET seen_at = ? WHERE sig = ?", (now, sig))
        return None, None

    # Canonical path can become stale (file moved/deleted) or outside this run's roots.
    # In that case, promote current path so we still index at least one copy.
    if (not os.path.exists(canonical)) or (roots and not is_under_any_root(canonical, roots)):
        conn.execute(
            "UPDATE content_sig SET path = ?, seen_at = ? WHERE sig = ?",
            (path, now, sig),
        )
        return None, canonical

    conn.execute("UPDATE content_sig SET seen_at = ? WHERE sig = ?", (now, sig))
    return canonical, None


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def chunk_text(text: str) -> List[str]:
    if not text:
        return []
    if CHUNK_SIZE <= 0 or len(text) <= CHUNK_SIZE:
        return [text]
    chunks = []
    step = max(CHUNK_SIZE - CHUNK_OVERLAP, 1)
    for i in range(0, len(text), step):
        chunk = text[i:i + CHUNK_SIZE]
        if chunk:
            chunks.append(chunk)
    return chunks


def extract_docx_text_ooxml(path: Path) -> str:
    try:
        with zipfile.ZipFile(str(path), "r") as z:
            xml = z.read("word/document.xml")
    except Exception:
        return ""
    try:
        root = ET.fromstring(xml)
    except Exception:
        return ""
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paras: List[str] = []
    for p in root.iter(ns + "p"):
        parts: List[str] = []
        for t in p.iter(ns + "t"):
            if t.text:
                parts.append(t.text)
        if parts:
            paras.append("".join(parts))
    return "\n".join(paras)


def extract_xlsx_text_ooxml(path: Path, max_cells: int) -> str:
    try:
        with zipfile.ZipFile(str(path), "r") as z:
            shared: List[str] = []
            try:
                ss_xml = z.read("xl/sharedStrings.xml")
                ss_root = ET.fromstring(ss_xml)
                ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
                for si in ss_root.iter(ns + "si"):
                    t_parts = [t.text or "" for t in si.iter(ns + "t")]
                    shared.append("".join(t_parts))
            except Exception:
                shared = []

            ws_files = sorted([n for n in z.namelist() if n.startswith("xl/worksheets/") and n.endswith(".xml")])
            ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

            def cell_value(c) -> str:
                t = (c.get("t") or "").strip()
                v = c.find(ns + "v")
                if v is None or v.text is None:
                    is_el = c.find(ns + "is")
                    if is_el is not None:
                        t_parts = [t2.text or "" for t2 in is_el.iter(ns + "t")]
                        return "".join(t_parts)
                    return ""
                raw = v.text
                if t == "s":
                    try:
                        return shared[int(raw)]
                    except Exception:
                        return raw
                return raw

            out_lines: List[str] = []
            cells = 0

            class _Stop(Exception):
                pass

            for ws in ws_files:
                if cells >= max_cells:
                    break
                try:
                    with z.open(ws) as f:
                        for _ev, elem in ET.iterparse(f, events=("end",)):
                            if elem.tag != ns + "row":
                                continue
                            if cells >= max_cells:
                                raise _Stop()
                            row_parts: List[str] = []
                            for c in elem.iter(ns + "c"):
                                val = cell_value(c)
                                if val:
                                    row_parts.append(val)
                                    cells += 1
                                    if cells >= max_cells:
                                        break
                            if row_parts:
                                out_lines.append("\t".join(row_parts))
                            elem.clear()
                except _Stop:
                    break
                except Exception:
                    continue
            return "\n".join(out_lines)
    except Exception:
        return ""


def extract_chunks(path: Path, stat: os.stat_result) -> Tuple[List[str], str]:
    max_chunks = max(1, MAX_CHUNKS_PER_FILE)
    budget_chars = max(MAX_CHARS, CHUNK_SIZE * max_chunks)

    # Text files (large-file aware)
    if is_text_file(path):
        if stat.st_size <= MAX_BYTES:
            text, _ = read_text(path, max_chars=budget_chars)
            return chunk_text(text)[:max_chunks], "text"

        # Sample evenly across the file; total bytes read stays bounded by MAX_BYTES.
        windows = max(1, min(SAMPLE_WINDOWS, max_chunks))
        window_bytes = max(64 * 1024, MAX_BYTES // windows)
        max_start = max(int(stat.st_size) - window_bytes, 0)
        offsets = [int(round(i * max_start / (windows - 1))) for i in range(windows)] if windows > 1 else [0]

        per_window = max(1, max_chunks // windows)
        out: List[str] = []
        try:
            with path.open("rb") as f:
                for off in offsets:
                    t = read_text_window(f, off, window_bytes)
                    if not t:
                        continue
                    cs = chunk_text(t)
                    if not cs:
                        continue
                    out.extend(cs[:per_window])
                    if len(out) >= max_chunks:
                        break
        except Exception:
            return [path.name]

        return (out[:max_chunks] if out else [path.name]), ("text_sampled" if out else "fallback_name")

    # PDFs
    if path.suffix.lower() == ".pdf":
        text = ""
        # Prefer builtin CLIs (present on macOS via Poppler) over optional Python deps.
        try:
            text = extract_pdf_text_pdftotext(path, PDF_MAX_PAGES)
        except Exception:
            text = ""
        if text and len(text.strip()) >= OCR_PDF_MIN_TEXT_CHARS:
            return chunk_text(text[:budget_chars])[:max_chunks], "pdf_pdftotext"
        ocr = read_ocr_sidecar(path, budget_chars)
        if ocr and len(ocr.strip()) >= 10:
            return chunk_text(ocr[:budget_chars])[:max_chunks], "pdf_ocr_sidecar"
        return [path.name], "pdf_no_text"

    # DOCX
    if path.suffix.lower() == ".docx":
        text = extract_docx_text_ooxml(path)
        return (chunk_text(text[:budget_chars])[:max_chunks] if text else [path.name]), ("docx_ooxml" if text else "docx_no_text")

    # XLSX
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        text = extract_xlsx_text_ooxml(path, XLSX_MAX_CELLS)
        return (chunk_text(text[:budget_chars])[:max_chunks] if text else [path.name]), ("xlsx_ooxml" if text else "xlsx_no_text")

    # Images (OCR sidecar)
    if is_image_file(path):
        ocr = read_ocr_sidecar(path, budget_chars)
        if ocr and len(ocr.strip()) >= 10:
            return chunk_text(ocr[:budget_chars])[:max_chunks], "image_ocr_sidecar"
        # Keep some context so semantic search can still hit filenames/folders.
        parts: List[str] = []
        cur = path
        for _ in range(6):
            if cur.name:
                parts.append(cur.name)
            if cur.parent == cur:
                break
            cur = cur.parent
        return [" / ".join(reversed(parts))] if parts else [path.name], "image_no_text"

    # Non-text/binary: index a short path context instead of only basename.
    parts: List[str] = []
    cur = path
    for _ in range(6):
        if cur.name:
            parts.append(cur.name)
        if cur.parent == cur:
            break
        cur = cur.parent
    return ([" / ".join(reversed(parts))] if parts else [path.name]), "path_context"


def create_payload_indexes() -> None:
    if not CREATE_PAYLOAD_INDEXES:
        return
    items: List[Tuple[str, str, bool]] = [
        ("path", "keyword", False),
        ("name", "keyword", False),
        ("source", "keyword", False),
        ("text_source", "keyword", False),
        ("chunk_index", "integer", False),
        ("chunk_total", "integer", False),
        ("mtime", "integer", MTIME_IS_PRINCIPAL),
    ]
    for field, schema_type, principal in items:
        schema: Any = schema_type
        if PAYLOAD_INDEX_ON_DISK or principal:
            schema = {"type": schema_type}
            if PAYLOAD_INDEX_ON_DISK:
                schema["on_disk"] = True
            if principal:
                schema["is_principal"] = True
        req = {"field_name": field, "field_schema": schema}
        try:
            qdrant_put(
                f"/collections/{COLLECTION}/index{qdrant_params(wait=QDRANT_WAIT, ordering=QDRANT_ORDERING)}",
                req,
            )
        except Exception as e:
            # Older Qdrant may not support schema objects; fall back to string schemas.
            if isinstance(schema, dict):
                try:
                    qdrant_put(
                        f"/collections/{COLLECTION}/index{qdrant_params(wait=QDRANT_WAIT, ordering=QDRANT_ORDERING)}",
                        {"field_name": field, "field_schema": schema_type},
                    )
                    continue
                except Exception as e2:
                    log(f"payload_index_error field={field} err={e2}")
                    continue
            log(f"payload_index_error field={field} err={e}")


def delete_points_for_path(path: str) -> None:
    payload = {
        "filter": {
            "must": [
                {"key": "path", "match": {"value": path}},
            ]
        }
    }
    try:
        qdrant_post(
            f"/collections/{COLLECTION}/points/delete{qdrant_params(wait=QDRANT_WAIT, ordering=QDRANT_ORDERING)}",
            payload,
        )
    except Exception as e:
        log(f"delete_path_error path={path} err={e}")


def delete_points_for_path_chunk_index_ge(path: str, min_chunk_index: int) -> None:
    payload = {
        "filter": {
            "must": [
                {"key": "path", "match": {"value": path}},
                {"key": "chunk_index", "range": {"gte": int(min_chunk_index)}},
            ]
        }
    }
    try:
        qdrant_post(
            f"/collections/{COLLECTION}/points/delete{qdrant_params(wait=QDRANT_WAIT, ordering=QDRANT_ORDERING)}",
            payload,
        )
    except Exception as e:
        log(f"delete_path_stale_error path={path} err={e}")


class EmbedCache:
    def __init__(self, max_size: int) -> None:
        self.max_size = max_size
        self.cache: OrderedDict[str, List[float]] = OrderedDict()

    def get(self, key: str) -> Optional[List[float]]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: List[float]) -> None:
        self.cache[key] = value
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)


def embed_texts(provider: str, texts: List[str], cache: EmbedCache) -> Tuple[List[Optional[List[float]]], List[Optional[str]]]:
    results: List[Optional[List[float]]] = [None] * len(texts)
    errors: List[Optional[str]] = [None] * len(texts)

    missing: List[Tuple[int, str, str]] = []
    for i, raw in enumerate(texts):
        t = clamp_embedding_text(raw)
        h = text_hash(t)
        if DEDUP_EMBEDDINGS:
            cached = cache.get(h)
            if cached is not None:
                results[i] = cached
                continue
        missing.append((i, t, h))

    if not missing:
        return results, errors

    if provider == "openai":
        payload = {"model": OPENAI_EMBED_MODEL, "input": [t for _, t, _ in missing]}
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        try:
            res = http_json("POST", "https://api.openai.com/v1/embeddings", payload, headers=headers)
            embs = [d["embedding"] for d in res.get("data", [])]
            for (idx, text, h), emb in zip(missing, embs):
                results[idx] = emb
                if DEDUP_EMBEDDINGS:
                    cache.set(h, emb)
        except Exception as e:
            for idx, _, _ in missing:
                errors[idx] = str(e)
        return results, errors

    # Ollama: modern batch first, fallback to legacy (possibly parallel).
    if OLLAMA_USE_BATCH:
        i = 0
        while i < len(missing):
            batch = missing[i:i + max(1, OLLAMA_BATCH_SIZE)]
            batch_texts = [t for _, t, _ in batch]
            try:
                embs = embed_texts_ollama_modern(batch_texts)
                for (idx, _t, h), emb in zip(batch, embs):
                    results[idx] = emb
                    if DEDUP_EMBEDDINGS:
                        cache.set(h, emb)
            except Exception as e:
                # Legacy fallback per text to salvage progress.
                with ThreadPoolExecutor(max_workers=max(1, EMBED_CONCURRENCY)) as ex:
                    fut_map = {ex.submit(embed_text_ollama_legacy, t): (idx, h) for idx, t, h in batch}
                    for fut in as_completed(fut_map):
                        idx, h = fut_map[fut]
                        try:
                            emb = fut.result()
                            results[idx] = emb
                            if DEDUP_EMBEDDINGS:
                                cache.set(h, emb)
                        except Exception as e2:
                            errors[idx] = str(e2 or e)
            i += len(batch)
        return results, errors

    with ThreadPoolExecutor(max_workers=max(1, EMBED_CONCURRENCY)) as ex:
        fut_map = {ex.submit(embed_text_ollama_legacy, t): (idx, h) for idx, t, h in missing}
        for fut in as_completed(fut_map):
            idx, h = fut_map[fut]
            try:
                emb = fut.result()
                results[idx] = emb
                if DEDUP_EMBEDDINGS:
                    cache.set(h, emb)
            except Exception as e:
                errors[idx] = str(e)
    return results, errors


def run_config_hash(provider: str) -> str:
    payload = {
        "indexer_version": INDEXER_VERSION,
        "provider": provider,
        "collection": COLLECTION,
        "qdrant_url": QDRANT_URL,
        "openai_model": OPENAI_EMBED_MODEL if provider == "openai" else "",
        "ollama_model": OLLAMA_MODEL if provider == "ollama" else "",
        "ollama_embed_endpoint": OLLAMA_EMBED_ENDPOINT,
        "ollama_legacy_endpoint": OLLAMA_EMBED_LEGACY_ENDPOINT,
        "ollama_truncate": OLLAMA_TRUNCATE,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "max_bytes": MAX_BYTES,
        "max_chars": MAX_CHARS,
        "pdf_max_pages": PDF_MAX_PAGES,
        "sample_windows": SAMPLE_WINDOWS,
        "max_chunks_per_file": MAX_CHUNKS_PER_FILE,
        "xlsx_max_cells": XLSX_MAX_CELLS,
        "embed_max_chars": EMBED_MAX_CHARS,
        "payload_preview_max_chars": PAYLOAD_PREVIEW_MAX_CHARS,
        "snippet_max_chars": SNIPPET_MAX_CHARS,
        "ocr_pdf_min_text_chars": OCR_PDF_MIN_TEXT_CHARS,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def main() -> int:
    roots = DEFAULT_ROOTS
    if len(sys.argv) > 1:
        roots = sys.argv[1:]

    provider = choose_provider()
    if provider not in ("openai", "ollama"):
        raise RuntimeError(f"Unsupported embedding provider: {provider}")

    # state db for incremental indexing
    conn = ensure_state_db()
    snip_conn = ensure_snippets_db()
    cfg_hash = run_config_hash(provider)
    prev_cfg = get_meta(conn, "run_cfg_hash")
    if prev_cfg != cfg_hash:
        log("Run config changed; files will be reprocessed as needed.")
        set_meta(conn, "run_cfg_hash", cfg_hash)
        conn.commit()

    global VECTOR_SIZE
    if VECTOR_SIZE == 0:
        sample = "Dropbox semantic index bootstrap"
        cache = EmbedCache(EMBED_CACHE_SIZE)
        vecs, errs = embed_texts(provider, [sample], cache)
        if vecs[0] is None:
            raise RuntimeError(f"Failed to compute vector size: {errs[0]}")
        vec0 = vecs[0]
        VECTOR_SIZE = len(vec0)
        log(f"Detected vector size: {VECTOR_SIZE} ({provider})")

    wait_for_qdrant()
    ensure_collection(COLLECTION)
    create_payload_indexes()

    effective_batch_size = max(1, max(BATCH_SIZE, MAX_CHUNKS_PER_FILE))
    batch: List[Dict[str, Any]] = []
    pending_states: List[Tuple[str, int, int, int, int, bool, str, str]] = []
    pending_snippets: List[Tuple[Any, ...]] = []
    pending_qdrant_stale_deletes: List[Tuple[str, int]] = []
    pending_snippet_stale_deletes: List[Tuple[str, int]] = []
    points_indexed = 0
    files_seen = 0
    files_indexed = 0
    skipped = 0
    skipped_incremental = 0
    skipped_dedup = 0
    embed_errors = 0
    t0 = time.time()

    total_files = count_files(roots)
    run_id = uuid.uuid4().hex
    log(f"Starting index. run_id={run_id} provider={provider} total_files={total_files} collection={COLLECTION}")
    audit = open(AUDIT_PATH, "a", encoding="utf-8")

    batch_id = 0
    cache = EmbedCache(EMBED_CACHE_SIZE)

    def flush_batch() -> None:
        nonlocal batch_id, batch, pending_states, pending_snippets, pending_qdrant_stale_deletes, pending_snippet_stale_deletes
        if not batch:
            return
        batch_id += 1
        first_path = batch[0]["payload"]["path"]
        last_path = batch[-1]["payload"]["path"]
        try:
            upsert_batch(batch)
            try:
                upsert_snippets(snip_conn, pending_snippets)
                if snip_conn is not None:
                    for p, min_idx in pending_snippet_stale_deletes:
                        delete_snippets_stale(snip_conn, p, min_idx)
                    snip_conn.commit()
            except Exception as e:
                log(f"snippets_flush_error err={e}")
            audit.write(
                json.dumps(
                    {
                        "run_id": run_id,
                        "batch_id": batch_id,
                        "status": "ok",
                        "count": len(batch),
                        "first_path": first_path,
                        "last_path": last_path,
                        "timestamp": int(time.time()),
                    }
                )
                + "\n"
            )
            for p, size, mtime, aux_mtime, aux_size, complete, fp, last_err in pending_states:
                set_state(conn, p, size, mtime, aux_mtime, aux_size, cfg_hash, complete, fp, last_err)
            conn.commit()
            for p, min_idx in pending_qdrant_stale_deletes:
                try:
                    delete_points_for_path_chunk_index_ge(p, min_idx)
                except Exception as e:
                    log(f"delete_stale_error path={p} err={e}")
        except Exception as e:
            audit.write(
                json.dumps(
                    {
                        "run_id": run_id,
                        "batch_id": batch_id,
                        "status": "error",
                        "count": len(batch),
                        "first_path": first_path,
                        "last_path": last_path,
                        "error": str(e),
                        "timestamp": int(time.time()),
                    }
                )
                + "\n"
            )
            audit.flush()
            raise
        audit.flush()
        batch.clear()
        pending_states.clear()
        pending_snippets.clear()
        pending_qdrant_stale_deletes.clear()
        pending_snippet_stale_deletes.clear()

    for path in iter_files(roots):
        if MAX_FILES and files_indexed >= MAX_FILES:
            break
        files_seen += 1
        try:
            stat = path.stat()
        except Exception:
            skipped += 1
            continue

        # incremental skip by mtime+size+config hash and only if the last attempt was complete
        aux_mtime, aux_size = ocr_sidecar_stat(path)
        state = get_state(conn, str(path))
        if (
            state
            and state[0] == stat.st_size
            and state[1] == int(stat.st_mtime)
            and state[2] == cfg_hash
            and int(state[3]) == 1
            and int(state[4]) == int(aux_mtime)
            and int(state[5]) == int(aux_size)
        ):
            skipped += 1
            skipped_incremental += 1
            continue
        had_prev = state is not None

        # cross-root file dedup (byte-signature)
        if DEDUP_FILES:
            sig = compute_file_sig(path, stat.st_size)
            if sig:
                canonical, stale_canonical = upsert_sig_canonical(conn, sig, str(path), roots)
                if stale_canonical:
                    delete_points_for_path(stale_canonical)
                if canonical and canonical != str(path):
                    # ensure duplicates do not linger from previous runs
                    delete_points_for_path(str(path))
                    delete_snippets_for_path(snip_conn, str(path))
                    skipped += 1
                    skipped_dedup += 1
                    try:
                        set_state(conn, str(path), stat.st_size, int(stat.st_mtime), aux_mtime, aux_size, cfg_hash, True, sig, "")
                        conn.commit()
                    except Exception:
                        pass
                    try:
                        audit.write(
                            json.dumps(
                                {
                                    "run_id": run_id,
                                    "batch_id": batch_id,
                                    "status": "dedup_skip",
                                    "path": str(path),
                                    "canonical_path": canonical,
                                    "sig": sig,
                                    "timestamp": int(time.time()),
                                }
                            )
                            + "\n"
                        )
                        audit.flush()
                    except Exception:
                        pass
                    continue

        chunks, source = extract_chunks(path, stat)
        if not chunks:
            skipped += 1
            continue
        chunks = chunks[: max(1, MAX_CHUNKS_PER_FILE)]
        if source == "pdf_no_text" and aux_mtime == 0 and aux_size == 0:
            enqueue_ocr(conn, path, stat, f"low_text source={source}")
        if OCR_IMAGES_ENABLED and source == "image_no_text" and aux_mtime == 0 and aux_size == 0:
            enqueue_ocr(conn, path, stat, f"low_text source={source}")

        vectors, vec_errs = embed_texts(provider, chunks, cache)
        file_had_points = False
        file_complete = True
        last_err = ""
        file_points: List[Dict[str, Any]] = []
        now_ts = int(time.time())
        for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
            if vec is None:
                embed_errors += 1
                skipped += 1
                file_complete = False
                last_err = vec_errs[idx] or last_err or "embedding_failed"
                continue
            pid = str(uuid.UUID(hex=hashlib.md5(f"{path}::{idx}".encode("utf-8")).hexdigest()))
            # Hash the exact text sent for embeddings (after clamping) so the payload reflects reality.
            chunk_for_embed = clamp_embedding_text(chunk)
            preview = chunk if PAYLOAD_PREVIEW_MAX_CHARS == 0 else chunk[: max(0, PAYLOAD_PREVIEW_MAX_CHARS)]
            snippet_text = chunk if SNIPPET_MAX_CHARS == 0 else chunk[: max(0, SNIPPET_MAX_CHARS)]
            payload = {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "mtime": int(stat.st_mtime),
                "source": "dropbox",
                "text_source": source,
                "chunk_index": idx,
                "chunk_total": len(chunks),
                "text_hash": text_hash(chunk_for_embed),
                "preview": preview,
            }
            file_points.append({"id": pid, "vector": vec, "payload": payload})
            pending_snippets.append(
                (
                    pid,
                    str(path),
                    idx,
                    len(chunks),
                    int(stat.st_mtime),
                    int(stat.st_size),
                    source,
                    cfg_hash,
                    payload["text_hash"],
                    snippet_text,
                    now_ts,
                )
            )
            points_indexed += 1
            file_had_points = True

        if file_had_points:
            files_indexed += 1
        else:
            # Do not mark as complete; this file should be retried later.
            try:
                set_state(
                    conn,
                    str(path),
                    int(stat.st_size),
                    int(stat.st_mtime),
                    int(aux_mtime),
                    int(aux_size),
                    cfg_hash,
                    False,
                    chunks_fingerprint(chunks),
                    last_err or "no_vectors",
                )
                if files_seen % 200 == 0:
                    conn.commit()
            except Exception:
                pass
            continue

        # Keep file points together (no partial splits across upserts) so state only advances on successful write.
        if batch and (len(batch) + len(file_points) > effective_batch_size):
            flush_batch()

        batch.extend(file_points)
        if had_prev:
            pending_qdrant_stale_deletes.append((str(path), int(len(chunks))))
            pending_snippet_stale_deletes.append((str(path), int(len(chunks))))
        pending_states.append(
            (
                str(path),
                int(stat.st_size),
                int(stat.st_mtime),
                int(aux_mtime),
                int(aux_size),
                file_complete,
                chunks_fingerprint(chunks),
                last_err,
            )
        )

        if len(batch) >= effective_batch_size:
            flush_batch()

    flush_batch()

    dt = time.time() - t0
    audit.close()
    try:
        conn.commit()
        conn.close()
        if snip_conn is not None:
            snip_conn.commit()
            snip_conn.close()
    except Exception:
        pass
    log(
        "Completed index. "
        f"files_seen={files_seen} files_indexed={files_indexed} "
        f"points_indexed={points_indexed} skipped={skipped} "
        f"skipped_incremental={skipped_incremental} skipped_dedup={skipped_dedup} "
        f"embed_errors={embed_errors} total_files={total_files} seconds={round(dt,2)}"
    )
    print(json.dumps({
        "points_indexed": points_indexed,
        "files_seen": files_seen,
        "files_indexed": files_indexed,
        "skipped": skipped,
        "skipped_incremental": skipped_incremental,
        "skipped_dedup": skipped_dedup,
        "embed_errors": embed_errors,
        "total_files": total_files,
        "seconds": round(dt, 2),
        "collection": COLLECTION,
        "qdrant": QDRANT_URL,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
