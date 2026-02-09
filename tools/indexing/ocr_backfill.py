#!/usr/bin/env python3
import os
import time
import json
import hashlib
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional


STATE_DB = os.environ.get(
    "QDRANT_STATE_DB",
    str(Path.cwd() / ".cache" / "qdrant_dropbox_state.sqlite"),
)
OCR_SIDECAR_DIR = os.environ.get(
    "QDRANT_OCR_SIDECAR_DIR",
    str(Path.cwd() / ".cache" / "ocr_sidecars"),
)
OCR_LANGS = os.environ.get("OCR_LANGS", "eng")
OCR_MAX_FILES = int(os.environ.get("OCR_MAX_FILES", "10"))  # per run
OCR_MAX_PAGES = int(os.environ.get("OCR_MAX_PAGES", "20"))
OCR_RENDER_DPI = int(os.environ.get("OCR_RENDER_DPI", "200"))
OCR_LOG_PATH = os.environ.get("OCR_LOG_PATH", "/tmp/qdrant_ocr_backfill.log")
OCR_FORCE = os.environ.get("OCR_FORCE", "0") == "1"
OCR_EXTS = [e.strip().lower() for e in os.environ.get("OCR_EXTS", ".pdf").split(",") if e.strip()]


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(OCR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def cmd_exists(name: str) -> bool:
    try:
        return shutil.which(name) is not None
    except Exception:
        return False


def ocr_sidecar_path(path: Path) -> Path:
    h = hashlib.sha256(str(path).encode("utf-8", errors="ignore")).hexdigest()
    return Path(OCR_SIDECAR_DIR) / f"{h}.txt"


def ensure_sidecar_dir() -> None:
    d = Path(OCR_SIDECAR_DIR)
    d.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(str(d), 0o700)
    except Exception:
        pass


def page_sample_indices(total_pages: int, max_pages: int) -> List[int]:
    if total_pages <= 0:
        return []
    if max_pages <= 0 or total_pages <= max_pages:
        return list(range(total_pages))
    if max_pages == 1:
        return [0]
    last = total_pages - 1
    idxs = [int(round(i * last / (max_pages - 1))) for i in range(max_pages)]
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


def tesseract_image(image_path: Path) -> str:
    if not cmd_exists("tesseract"):
        raise RuntimeError("tesseract_not_found")
    res = subprocess.run(
        ["tesseract", str(image_path), "stdout", "-l", OCR_LANGS],
        check=False,
        capture_output=True,
        timeout=120,
    )
    out = (res.stdout or b"").decode("utf-8", errors="ignore")
    return out


def ocr_pdf(path: Path) -> str:
    if not cmd_exists("pdftoppm"):
        raise RuntimeError("pdftoppm_not_found")
    pages = pdf_page_count(path)
    if pages <= 0:
        pages = 1
    idxs0 = page_sample_indices(pages, OCR_MAX_PAGES)
    pages_1based = [i + 1 for i in idxs0]
    ranges = indices_to_ranges(pages_1based)
    if not ranges:
        ranges = [(1, 1)]

    with tempfile.TemporaryDirectory(prefix="qdrant-ocr-") as td:
        tmpdir = Path(td)
        texts: List[str] = []
        for start, end in ranges:
            prefix = tmpdir / f"p{start:04d}"
            subprocess.run(
                [
                    "pdftoppm",
                    "-r",
                    str(OCR_RENDER_DPI),
                    "-f",
                    str(start),
                    "-l",
                    str(end),
                    "-png",
                    str(path),
                    str(prefix),
                ],
                check=False,
                capture_output=True,
                timeout=180,
            )
            pngs = sorted(tmpdir.glob(f"{prefix.name}-*.png"))
            for png in pngs:
                t = tesseract_image(png)
                if t and t.strip():
                    texts.append(t)
        return "\n".join(texts)


def convert_heic_to_png(src: Path, dst: Path) -> None:
    if cmd_exists("sips"):
        subprocess.run(
            ["sips", "-s", "format", "png", str(src), "--out", str(dst)],
            check=False,
            capture_output=True,
            timeout=60,
        )
        return
    if cmd_exists("convert"):
        subprocess.run(
            ["convert", str(src), str(dst)],
            check=False,
            capture_output=True,
            timeout=60,
        )
        return
    raise RuntimeError("no_heic_converter")


def ocr_image(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".heic", ".heif"):
        with tempfile.TemporaryDirectory(prefix="qdrant-heic-") as td:
            tmp_png = Path(td) / "img.png"
            convert_heic_to_png(path, tmp_png)
            return tesseract_image(tmp_png)
    return tesseract_image(path)


def db_connect() -> sqlite3.Connection:
    db_path = Path(STATE_DB)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return conn


def fetch_jobs(conn: sqlite3.Connection, limit: int) -> List[Tuple[str, str, int, int, str, int]]:
    exts = OCR_EXTS or [".pdf"]
    ph = ",".join(["?"] * len(exts))
    if OCR_FORCE:
        cur = conn.execute(
            "SELECT path, ext, COALESCE(size, 0), COALESCE(mtime, 0), COALESCE(status, ''), COALESCE(attempts, 0) "
            f"FROM ocr_queue WHERE lower(COALESCE(ext, '')) IN ({ph}) "
            "ORDER BY CASE WHEN lower(COALESCE(ext, '')) = '.pdf' THEN 0 ELSE 1 END, updated_at ASC LIMIT ?",
            tuple(exts) + (int(limit),),
        )
    else:
        cur = conn.execute(
            "SELECT path, ext, COALESCE(size, 0), COALESCE(mtime, 0), COALESCE(status, ''), COALESCE(attempts, 0) "
            f"FROM ocr_queue WHERE COALESCE(status, '') != 'done' AND lower(COALESCE(ext, '')) IN ({ph}) "
            "ORDER BY CASE WHEN lower(COALESCE(ext, '')) = '.pdf' THEN 0 ELSE 1 END, updated_at ASC LIMIT ?",
            tuple(exts) + (int(limit),),
        )
    return [(r[0], r[1] or "", int(r[2]), int(r[3]), r[4] or "", int(r[5])) for r in cur.fetchall()]


def update_job(conn: sqlite3.Connection, path: str, status: str, attempts: int, last_error: str) -> None:
    now = int(time.time())
    conn.execute(
        "UPDATE ocr_queue SET status = ?, attempts = ?, last_error = ?, updated_at = ? WHERE path = ?",
        (status, int(attempts), (last_error or "")[:1000], now, path),
    )


def main() -> int:
    ensure_sidecar_dir()
    conn = db_connect()
    jobs = fetch_jobs(conn, OCR_MAX_FILES if OCR_MAX_FILES > 0 else 10)
    log(f"ocr_backfill_start jobs={len(jobs)} langs={OCR_LANGS} exts={','.join(OCR_EXTS or ['.pdf'])} sidecar_dir={OCR_SIDECAR_DIR}")

    done = 0
    for p, ext, _size, _mtime, status, attempts in jobs:
        path = Path(p)
        try:
            if not path.exists():
                update_job(conn, p, "missing", attempts, "file_missing")
                conn.commit()
                continue
            attempts2 = attempts + 1
            update_job(conn, p, "running", attempts2, "")
            conn.commit()

            text = ""
            if ext.lower() == ".pdf":
                text = ocr_pdf(path)
            else:
                text = ocr_image(path)
            text = (text or "").strip()

            sidecar = ocr_sidecar_path(path)
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            sidecar.write_text(text + "\n", encoding="utf-8", errors="ignore")
            try:
                os.chmod(str(sidecar), 0o600)
            except Exception:
                pass

            update_job(conn, p, "done", attempts2, "")
            conn.commit()
            done += 1
            log(f"ocr_done path={p} chars={len(text)} sidecar={sidecar.name}")
        except Exception as e:
            try:
                update_job(conn, p, "error", attempts + 1, str(e))
                conn.commit()
            except Exception:
                pass
            log(f"ocr_error path={p} err={e}")

    log(json.dumps({"status": "ok", "processed": len(jobs), "done": done, "timestamp": int(time.time())}))
    try:
        conn.close()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
