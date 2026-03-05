from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

# Make script robust when executed as a direct file path.
ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.logistics.bluejet_export_toptrans import BlueJetClient, BlueJetCreds


def _run(cmd: list[str], *, allow_fail: bool = False) -> None:
    env = os.environ.copy()
    cwd = None
    if cmd and cmd[0] == "bq":
        # Avoid local module shadowing (repo has utils/ package).
        env.pop("PYTHONPATH", None)
        cwd = "/tmp"
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env, cwd=cwd)
    if proc.returncode != 0 and not allow_fail:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")


def _resolve_secret(raw_value: str, op_ref: str) -> str:
    value = (raw_value or "").strip().strip('"')
    if value:
        return value
    ref = (op_ref or "").strip().strip('"')
    if not ref:
        return ""
    proc = subprocess.run(["op", "read", ref], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _fetch_rows(client: BlueJetClient, evidence_no: int, max_rows: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    limit = min(200, max_rows if max_rows > 0 else 200)

    while True:
        if max_rows > 0 and len(out) >= max_rows:
            break
        data = client.data(no=evidence_no, limit=limit, offset=offset)
        rows = data.get("result", {}).get("data", [])
        if not isinstance(rows, list) or not rows:
            break

        for row in rows:
            if not isinstance(row, dict):
                continue
            record = client.row_to_dict(row)
            record["_evidence_no"] = evidence_no
            out.append(record)
            if max_rows > 0 and len(out) >= max_rows:
                break

        if len(rows) < limit:
            break
        offset += limit

    return out


def _fetch_rows_via_mcp_helper(evidence_no: int, max_rows: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    # MCP payloads can be truncated on very large pages; keep page size conservative.
    limit = min(50, max_rows if max_rows > 0 else 50)
    helper = Path(__file__).resolve().parents[3] / "tools" / "mcp" / "bluejet_query.sh"

    while True:
        if max_rows > 0 and len(out) >= max_rows:
            break
        endpoint = f"api/v1/Data?no={evidence_no}&limit={limit}&offset={offset}"
        proc = subprocess.run(
            [str(helper), "GET", endpoint],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            break
        raw = proc.stdout
        marker = "Response: "
        idx = raw.find(marker)
        if idx < 0:
            break
        payload_txt = raw[idx + len(marker):].strip()
        try:
            payload = json.loads(payload_txt)
        except Exception:
            # Retry with smaller chunks when MCP response gets truncated.
            if limit > 1:
                limit = max(1, limit // 2)
                continue
            break
        rows = payload.get("rows", [])
        if not rows and isinstance(payload.get("result"), dict):
            rows = payload.get("result", {}).get("data", [])
        if not isinstance(rows, list) or not rows:
            break
        for row in rows:
            if not isinstance(row, dict):
                continue
            columns = row.get("columns", [])
            if not isinstance(columns, list):
                continue
            rec: dict[str, Any] = {"_evidence_no": evidence_no}
            for col in columns:
                if not isinstance(col, dict):
                    continue
                name = col.get("name")
                if isinstance(name, str) and name:
                    rec[name] = col.get("value")
            out.append(rec)
            if max_rows > 0 and len(out) >= max_rows:
                break

        if len(rows) < limit:
            break
        offset += limit

    return out


def _write_ndjson(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main() -> int:
    load_dotenv(override=False)

    ap = argparse.ArgumentParser(description="Sync BlueJet orders/invoices to BigQuery for Looker")
    ap.add_argument("--project", default=os.environ.get("LOOKER_BQ_PROJECT", "premium-gastro-35094"))
    ap.add_argument("--dataset", default=os.environ.get("LOOKER_BQ_DATASET", "bluejet_reporting"))
    ap.add_argument("--orders-table", default=os.environ.get("LOOKER_BQ_ORDERS_TABLE", "orders_out"))
    ap.add_argument("--invoices-table", default=os.environ.get("LOOKER_BQ_INVOICES_TABLE", "invoices_out"))
    ap.add_argument("--max-rows", type=int, default=int(os.environ.get("BLUEJET_BQ_MAX_ROWS", "20000")))
    args = ap.parse_args()

    token_id = _resolve_secret(
        os.environ.get("BLUEJET_API_TOKEN_ID", ""),
        os.environ.get("BLUEJET_API_TOKEN_ID_OP_REF", ""),
    )
    token_hash = _resolve_secret(
        os.environ.get("BLUEJET_API_TOKEN_HASH", ""),
        os.environ.get("BLUEJET_API_TOKEN_HASH_OP_REF", ""),
    )

    orders: list[dict[str, Any]] = []
    invoices: list[dict[str, Any]] = []
    used_source = "bluejet_api"

    if token_id and token_hash:
        base_url = os.environ.get("BLUEJET_BASE_URL", "https://czeco.bluejet.cz")
        client = BlueJetClient(BlueJetCreds(base_url=base_url, token_id=token_id, token_hash=token_hash))
        orders = _fetch_rows(client, evidence_no=356, max_rows=args.max_rows)
        invoices = _fetch_rows(client, evidence_no=323, max_rows=args.max_rows)

    if not orders and not invoices:
        used_source = "bluejet_mcp_helper"
        orders = _fetch_rows_via_mcp_helper(356, args.max_rows)
        invoices = _fetch_rows_via_mcp_helper(323, args.max_rows)

    if not orders and not invoices:
        raise RuntimeError(
            "BlueJet returned no orders/invoices rows for evidences 356/323 "
            "(both BlueJet API and MCP helper)."
        )

    _run(
        ["bq", "--project_id", args.project, "mk", "--dataset", "--location=EU", f"{args.project}:{args.dataset}"],
        allow_fail=True,
    )

    with tempfile.TemporaryDirectory(prefix="bluejet_bq_sync_") as tmpdir:
        tmp = Path(tmpdir)
        orders_file = tmp / "orders.ndjson"
        invoices_file = tmp / "invoices.ndjson"
        _write_ndjson(orders_file, orders)
        _write_ndjson(invoices_file, invoices)

        if orders:
            _run(
                [
                    "bq",
                    "--project_id",
                    args.project,
                    "load",
                    "--replace=true",
                    "--source_format=NEWLINE_DELIMITED_JSON",
                    "--autodetect",
                    f"{args.project}:{args.dataset}.{args.orders_table}",
                    str(orders_file),
                ]
            )
        if invoices:
            _run(
                [
                    "bq",
                    "--project_id",
                    args.project,
                    "load",
                    "--replace=true",
                    "--source_format=NEWLINE_DELIMITED_JSON",
                    "--autodetect",
                    f"{args.project}:{args.dataset}.{args.invoices_table}",
                    str(invoices_file),
                ]
            )

    print("Sync complete")
    print(f"Source: {used_source}")
    print(f"Project: {args.project}")
    print(f"Dataset: {args.dataset}")
    print(f"Orders table: {args.orders_table} (rows={len(orders)})")
    print(f"Invoices table: {args.invoices_table} (rows={len(invoices)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
