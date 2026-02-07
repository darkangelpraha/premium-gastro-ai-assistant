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
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, Tuple, Dict, Any, List, Optional

QDRANT_URL = os.environ.get("QDRANT_URL", "http://127.0.0.1:6333")
COLLECTION = os.environ.get("QDRANT_COLLECTION", "dropbox_semantic_v2")
VECTOR_SIZE = int(os.environ.get("QDRANT_VECTOR_SIZE", "0"))  # 0 = auto-detect
BATCH_SIZE = int(os.environ.get("QDRANT_BATCH_SIZE", "16"))
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
AUDIT_PATH = os.environ.get("QDRANT_AUDIT_PATH", "/tmp/qdrant_dropbox_audit.jsonl")
LOG_PATH = os.environ.get("QDRANT_LOG_PATH", "/tmp/qdrant_dropbox_index.log")
MAX_FILES = int(os.environ.get("QDRANT_MAX_FILES", "0"))  # 0 = no limit
STATE_DB = os.environ.get(
    "QDRANT_STATE_DB",
    str(Path.cwd() / ".cache" / "qdrant_dropbox_state.sqlite"),
)

EMBEDDING_PROVIDER = os.environ.get("QDRANT_EMBEDDING_PROVIDER", "auto").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "nomic-embed-text")

def default_roots() -> List[str]:
    # macOS Dropbox client mounts under ~/Library/CloudStorage
    base = Path.home() / "Library" / "CloudStorage"
    if not base.is_dir():
        return []

    # Includes historical/duplicated mounts like "Dropbox (....)".
    candidates = [p for p in sorted(base.glob("Dropbox*")) if p.is_dir()]

    seen = set()
    out: List[str] = []
    for p in candidates:
        rp = str(p.resolve())
        if rp in seen:
            continue
        seen.add(rp)
        out.append(str(p))
    return out

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
    ]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    data = None
    if payload is not None:
        data = json.dumps(payload)
        cmd += ["--data-binary", "@-"]
    last_err = ""
    for attempt in range(HTTP_RETRIES + 1):
        res = subprocess.run(cmd, input=data, capture_output=True, text=True)
        if res.returncode == 0:
            out = res.stdout.strip()
            return json.loads(out) if out else {}
        last_err = (res.stderr.strip() or res.stdout.strip() or "curl failed").strip()
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
        if attempt < HTTP_RETRIES and retryable:
            time.sleep(HTTP_RETRY_SLEEP_SECONDS * (attempt + 1))
            continue
        break
    raise RuntimeError(last_err)


def qdrant_check(res: Dict[str, Any]) -> Dict[str, Any]:
    status = res.get("status")
    if status and status != "ok":
        msg = res.get("message") or res.get("result") or str(res)
        raise RuntimeError(f"Qdrant error: {msg}")
    return res


def qdrant_get(path: str) -> Dict[str, Any]:
    return qdrant_check(http_json("GET", QDRANT_URL + path))


def qdrant_put(path: str, payload: Any) -> Dict[str, Any]:
    return qdrant_check(http_json("PUT", QDRANT_URL + path, payload))

def qdrant_post(path: str, payload: Any) -> Dict[str, Any]:
    return qdrant_check(http_json("POST", QDRANT_URL + path, payload))


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


def embed_text_ollama(text: str) -> List[float]:
    payload = {"model": OLLAMA_MODEL, "prompt": text}
    res = http_json("POST", f"{OLLAMA_HOST}/api/embeddings", payload)
    if "embedding" not in res:
        raise RuntimeError(f"Ollama embedding response missing 'embedding': {str(res)[:200]}")
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
            for name in filenames:
                yield Path(dirpath) / name


def upsert_batch(points: List[Dict[str, Any]]) -> None:
    if not points:
        return
    payload = {"points": points}
    qdrant_put(f"/collections/{COLLECTION}/points?wait=true", payload)


def count_files(roots: List[str]) -> int:
    total = 0
    for root in roots:
        if not os.path.exists(root):
            continue
        for _, _, filenames in os.walk(root, onerror=lambda e: None):
            total += len(filenames)
    return total


def ensure_state_db() -> sqlite3.Connection:
    db_path = Path(STATE_DB)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS file_state (
            path TEXT PRIMARY KEY,
            size INTEGER,
            mtime INTEGER,
            text_hash TEXT,
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
    conn.commit()
    return conn


def get_state(conn: sqlite3.Connection, path: str) -> Optional[Tuple[int, int, str]]:
    cur = conn.execute(
        "SELECT size, mtime, text_hash FROM file_state WHERE path = ?",
        (path,),
    )
    row = cur.fetchone()
    return row if row else None


def set_state(conn: sqlite3.Connection, path: str, size: int, mtime: int, text_hash: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO file_state (path, size, mtime, text_hash, updated_at) VALUES (?, ?, ?, ?, ?)",
        (path, size, mtime, text_hash, int(time.time())),
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


def upsert_sig_canonical(conn: sqlite3.Connection, sig: str, path: str) -> Optional[str]:
    now = int(time.time())
    cur = conn.execute("SELECT path FROM content_sig WHERE sig = ?", (sig,))
    row = cur.fetchone()
    if not row:
        conn.execute(
            "INSERT INTO content_sig (sig, path, seen_at) VALUES (?, ?, ?)",
            (sig, path, now),
        )
        return None

    canonical = row[0]
    if canonical == path:
        conn.execute("UPDATE content_sig SET seen_at = ? WHERE sig = ?", (now, sig))
        return canonical

    if not os.path.exists(canonical):
        conn.execute(
            "UPDATE content_sig SET path = ?, seen_at = ? WHERE sig = ?",
            (path, now, sig),
        )
        return None

    conn.execute("UPDATE content_sig SET seen_at = ? WHERE sig = ?", (now, sig))
    return canonical


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


def extract_chunks(path: Path, stat: os.stat_result) -> List[str]:
    max_chunks = max(1, MAX_CHUNKS_PER_FILE)
    budget_chars = max(MAX_CHARS, CHUNK_SIZE * max_chunks)

    # Text files (large-file aware)
    if is_text_file(path):
        if stat.st_size <= MAX_BYTES:
            text, _ = read_text(path, max_chars=budget_chars)
            return chunk_text(text)[:max_chunks]

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

        return out[:max_chunks] if out else [path.name]

    # PDFs
    if path.suffix.lower() == ".pdf":
        try:
            import pdfplumber  # type: ignore
            parts = []
            with pdfplumber.open(str(path)) as pdf:
                idxs = page_sample_indices(len(pdf.pages), PDF_MAX_PAGES)
                for i in idxs:
                    parts.append((pdf.pages[i].extract_text() or ""))
            text = "\n".join(parts)
            return chunk_text(text[:budget_chars])[:max_chunks] if text else [path.name]
        except Exception:
            try:
                from pypdf import PdfReader  # type: ignore
                reader = PdfReader(str(path))
                parts = []
                idxs = page_sample_indices(len(reader.pages), PDF_MAX_PAGES)
                for i in idxs:
                    parts.append((reader.pages[i].extract_text() or ""))
                text = "\n".join(parts)
                return chunk_text(text[:budget_chars])[:max_chunks] if text else [path.name]
            except Exception:
                return [path.name]

    # DOCX
    if path.suffix.lower() == ".docx":
        try:
            import docx  # type: ignore
            doc = docx.Document(str(path))
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
            return chunk_text(text[:budget_chars])[:max_chunks] if text else [path.name]
        except Exception:
            return [path.name]

    # XLSX
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        try:
            import openpyxl  # type: ignore
            wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
            parts = []
            cells = 0
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    parts.append("\t".join([str(c) for c in row if c is not None]))
                    cells += sum(1 for c in row if c is not None)
                    if cells >= XLSX_MAX_CELLS:
                        break
                if cells >= XLSX_MAX_CELLS:
                    break
            text = "\n".join(parts)
            return chunk_text(text[:budget_chars])[:max_chunks] if text else [path.name]
        except Exception:
            return [path.name]

    return [path.name]


def create_payload_indexes() -> None:
    if not CREATE_PAYLOAD_INDEXES:
        return
    for field, schema in [
        ("path", "keyword"),
        ("name", "keyword"),
        ("source", "keyword"),
        ("mtime", "integer"),
    ]:
        try:
            qdrant_put(f"/collections/{COLLECTION}/index", {"field_name": field, "field_schema": schema})
        except Exception as e:
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
        qdrant_post(f"/collections/{COLLECTION}/points/delete?wait=true", payload)
    except Exception as e:
        log(f"delete_path_error path={path} err={e}")


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


def embed_texts(provider: str, texts: List[str], cache: EmbedCache) -> List[Optional[List[float]]]:
    results: List[Optional[List[float]]] = [None] * len(texts)
    missing: List[Tuple[int, str]] = []
    for i, t in enumerate(texts):
        if DEDUP_EMBEDDINGS:
            h = text_hash(t)
            cached = cache.get(h)
            if cached is not None:
                results[i] = cached
                continue
        missing.append((i, t))

    if not missing:
        return results

    # OpenAI batch
    if provider == "openai":
        payload = {"model": OPENAI_EMBED_MODEL, "input": [t for _, t in missing]}
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        res = http_json("POST", "https://api.openai.com/v1/embeddings", payload, headers=headers)
        embs = [d["embedding"] for d in res.get("data", [])]
        for (idx, text), emb in zip(missing, embs):
            results[idx] = emb
            if DEDUP_EMBEDDINGS:
                cache.set(text_hash(text), emb)
        return results

    # Ollama: parallel per text
    with ThreadPoolExecutor(max_workers=max(1, EMBED_CONCURRENCY)) as ex:
        future_map = {ex.submit(embed_text_ollama, t): (i, t) for i, t in missing}
        for fut in as_completed(future_map):
            i, t = future_map[fut]
            try:
                emb = fut.result()
                results[i] = emb
                if DEDUP_EMBEDDINGS:
                    cache.set(text_hash(t), emb)
            except Exception as e:
                results[i] = None
                log(f"embed_error text_hash={text_hash(t)} err={e}")

    return results


def main() -> int:
    roots = default_roots()
    if len(sys.argv) > 1:
        roots = sys.argv[1:]

    provider = choose_provider()
    if provider not in ("openai", "ollama"):
        raise RuntimeError(f"Unsupported embedding provider: {provider}")

    # state db for incremental indexing
    conn = ensure_state_db()
    config_hash = hashlib.sha256(
        f"{provider}|{OPENAI_EMBED_MODEL}|{CHUNK_SIZE}|{CHUNK_OVERLAP}|{MAX_CHARS}|{MAX_BYTES}".encode()
    ).hexdigest()
    prev_hash = get_meta(conn, "config_hash")
    if prev_hash != config_hash:
        log("Config changed; incremental cache invalidated for this run.")
        set_meta(conn, "config_hash", config_hash)
        conn.commit()

    global VECTOR_SIZE
    if VECTOR_SIZE == 0:
        sample = "Dropbox semantic index bootstrap"
        if provider == "openai":
            vec0 = embed_text_openai(sample)
        else:
            vec0 = embed_text_ollama(sample)
        VECTOR_SIZE = len(vec0)
        log(f"Detected vector size: {VECTOR_SIZE} ({provider})")

    ensure_collection(COLLECTION)
    create_payload_indexes()

    batch = []
    points_indexed = 0
    files_seen = 0
    files_indexed = 0
    skipped = 0
    skipped_incremental = 0
    skipped_dedup = 0
    embed_errors = 0
    t0 = time.time()

    total_files = count_files(roots)
    log(f"Starting index. provider={provider} total_files={total_files} collection={COLLECTION}")
    audit = open(AUDIT_PATH, "a", encoding="utf-8")

    batch_id = 0
    cache = EmbedCache(EMBED_CACHE_SIZE)
    for path in iter_files(roots):
        if MAX_FILES and files_indexed >= MAX_FILES:
            break
        files_seen += 1
        try:
            stat = path.stat()
        except Exception:
            skipped += 1
            continue

        # incremental skip by mtime+size
        state = get_state(conn, str(path))
        if state and state[0] == stat.st_size and state[1] == int(stat.st_mtime):
            skipped += 1
            skipped_incremental += 1
            continue
        if state:
            delete_points_for_path(str(path))

        # cross-root file dedup (byte-signature)
        if DEDUP_FILES:
            sig = compute_file_sig(path, stat.st_size)
            if sig:
                canonical = upsert_sig_canonical(conn, sig, str(path))
                if canonical and canonical != str(path):
                    # ensure duplicates do not linger from previous runs
                    delete_points_for_path(str(path))
                    skipped += 1
                    skipped_dedup += 1
                    try:
                        set_state(conn, str(path), stat.st_size, int(stat.st_mtime), sig)
                    except Exception:
                        pass
                    try:
                        audit.write(
                            json.dumps(
                                {
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

        chunks = extract_chunks(path, stat)
        if not chunks:
            skipped += 1
            continue
        chunks = chunks[: max(1, MAX_CHUNKS_PER_FILE)]

        vectors = embed_texts(provider, chunks, cache)
        file_had_points = False
        for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
            if vec is None:
                embed_errors += 1
                skipped += 1
                continue
            pid = str(uuid.UUID(hex=hashlib.md5(f"{path}::{idx}".encode("utf-8")).hexdigest()))
            payload = {
                "path": str(path),
                "name": path.name,
                "size": stat.st_size,
                "mtime": int(stat.st_mtime),
                "source": "dropbox",
                "chunk_index": idx,
                "chunk_total": len(chunks),
                "text_hash": text_hash(chunk),
            }
            batch.append({"id": pid, "vector": vec, "payload": payload})
            points_indexed += 1
            file_had_points = True

        if file_had_points:
            files_indexed += 1

        if len(batch) >= BATCH_SIZE:
            batch_id += 1
            first_path = batch[0]["payload"]["path"]
            last_path = batch[-1]["payload"]["path"]
            try:
                upsert_batch(batch)
                audit.write(json.dumps({
                    "batch_id": batch_id,
                    "status": "ok",
                    "count": len(batch),
                    "first_path": first_path,
                    "last_path": last_path,
                    "timestamp": int(time.time()),
                }) + "\n")
            except Exception as e:
                audit.write(json.dumps({
                    "batch_id": batch_id,
                    "status": "error",
                    "count": len(batch),
                    "first_path": first_path,
                    "last_path": last_path,
                    "error": str(e),
                    "timestamp": int(time.time()),
                }) + "\n")
                audit.flush()
                raise
            audit.flush()
            batch.clear()

        # update state (file-level)
        try:
            set_state(conn, str(path), stat.st_size, int(stat.st_mtime), chunks_fingerprint(chunks))
            if files_seen % 200 == 0:
                conn.commit()
        except Exception:
            pass

    if batch:
        batch_id += 1
        first_path = batch[0]["payload"]["path"]
        last_path = batch[-1]["payload"]["path"]
        try:
            upsert_batch(batch)
            audit.write(json.dumps({
                "batch_id": batch_id,
                "status": "ok",
                "count": len(batch),
                "first_path": first_path,
                "last_path": last_path,
                "timestamp": int(time.time()),
            }) + "\n")
        except Exception as e:
            audit.write(json.dumps({
                "batch_id": batch_id,
                "status": "error",
                "count": len(batch),
                "first_path": first_path,
                "last_path": last_path,
                "error": str(e),
                "timestamp": int(time.time()),
            }) + "\n")
            audit.flush()
            raise
        audit.flush()
        batch.clear()

    dt = time.time() - t0
    audit.close()
    try:
        conn.commit()
        conn.close()
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
