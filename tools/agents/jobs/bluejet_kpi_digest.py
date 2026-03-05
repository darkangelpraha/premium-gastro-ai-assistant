from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from tools.logistics.bluejet_export_toptrans import BlueJetClient, BlueJetCreds

from .base import BaseJob, JobContext, JobResult, utc_now_iso


class BlueJetKPIDigestJob(BaseJob):
    name = "bluejet_kpi_digest"

    def run(self, context: JobContext) -> JobResult:
        creds = _read_creds(context.env)
        max_rows = int(context.env.get("BLUEJET_KPI_MAX_ROWS", "1000"))
        data_source = "bluejet_api"
        orders: list[dict[str, Any]] = []
        invoices: list[dict[str, Any]] = []

        if creds:
            try:
                client = BlueJetClient(creds)
                orders = _fetch_rows(client, no=356, max_rows=max_rows)
                invoices = _fetch_rows(client, no=323, max_rows=max_rows)
            except Exception:
                orders = []
                invoices = []

        if not orders and not invoices:
            q_orders, q_invoices = _fetch_rows_from_qdrant(context.env, max_rows=max_rows)
            if q_orders or q_invoices:
                orders, invoices = q_orders, q_invoices
                data_source = "qdrant_mirror"

        now = datetime.utcnow()
        lookback_days = int(context.env.get("BLUEJET_KPI_LOOKBACK_DAYS", "180"))
        if lookback_days < 1:
            lookback_days = 180
        windows = {
            "7d": now - timedelta(days=7),
            f"{lookback_days}d": now - timedelta(days=lookback_days),
        }

        order_metrics = _compute_metrics(orders, windows)
        invoice_metrics = _compute_metrics(invoices, windows)

        findings: list[str] = []
        long_window = f"{lookback_days}d"
        if order_metrics[long_window]["count"] == 0:
            findings.append(f"No BlueJet orders detected in last {lookback_days} days")
        if invoice_metrics[long_window]["count"] == 0:
            findings.append(f"No BlueJet invoices detected in last {lookback_days} days")

        payload = {
            "generated_at": utc_now_iso(),
            "data_source": data_source,
            "orders": order_metrics,
            "invoices": invoice_metrics,
            "sample_size": {"orders": len(orders), "invoices": len(invoices)},
        }

        json_artifact = _write_json_artifact(context, "bluejet_kpi_digest.json", payload)
        md_artifact = _write_markdown_artifact(context, "bluejet_kpi_digest.md", payload)

        status = "ok" if not findings else "attention"
        summary = (
            f"BlueJet KPI digest generated from {data_source} "
            f"(orders={len(orders)}, invoices={len(invoices)})"
        )

        return JobResult(
            job_name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            metrics={
                f"orders_{lookback_days}d": order_metrics[long_window]["count"],
                f"invoices_{lookback_days}d": invoice_metrics[long_window]["count"],
            },
            artifacts=[json_artifact, md_artifact],
        )


def _read_creds(env: dict[str, str]) -> BlueJetCreds | None:
    base = env.get("BLUEJET_BASE_URL", "https://czeco.bluejet.cz").strip()
    token_id = _resolve_secret(
        env.get("BLUEJET_API_TOKEN_ID", ""),
        env.get("BLUEJET_API_TOKEN_ID_OP_REF", ""),
    )
    token_hash = _resolve_secret(
        env.get("BLUEJET_API_TOKEN_HASH", ""),
        env.get("BLUEJET_API_TOKEN_HASH_OP_REF", ""),
    )
    if not token_id or not token_hash:
        return None
    return BlueJetCreds(base_url=base, token_id=token_id, token_hash=token_hash)


def _resolve_secret(raw_value: str, op_ref: str) -> str:
    value = (raw_value or "").strip().strip("\"")
    if value:
        return value
    ref = (op_ref or "").strip().strip("\"")
    if not ref:
        return ""
    try:
        proc = subprocess.run(
            ["op", "read", ref],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def _fetch_rows(client: BlueJetClient, *, no: int, max_rows: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    offset = 0
    limit = 100

    while len(out) < max_rows:
        data = client.data(no=no, limit=limit, offset=offset)
        rows = data.get("result", {}).get("data", [])
        if not isinstance(rows, list) or not rows:
            break
        for row in rows:
            if isinstance(row, dict):
                out.append(client.row_to_dict(row))
                if len(out) >= max_rows:
                    break
        offset += limit

    return out


def _fetch_rows_from_qdrant(env: dict[str, str], max_rows: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    qdrant_url = env.get("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
    qdrant_api_key = (env.get("QDRANT_API_KEY", "") or "").strip()

    try:
        orders = _qdrant_scroll_payloads(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            collection="bluejet_orders_out",
            max_rows=max_rows,
        )
    except Exception:
        orders = []
    try:
        invoices = _qdrant_scroll_payloads(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            collection="bluejet_invoices_out",
            max_rows=max_rows,
        )
    except Exception:
        invoices = []
    return orders, invoices


def _qdrant_scroll_payloads(
    *,
    qdrant_url: str,
    qdrant_api_key: str,
    collection: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    headers = {"Content-Type": "application/json"}
    if qdrant_api_key:
        headers["api-key"] = qdrant_api_key

    out: list[dict[str, Any]] = []
    next_offset: Any = None
    page_limit = min(200, max_rows) if max_rows > 0 else 200

    while True:
        payload: dict[str, Any] = {
            "limit": page_limit,
            "with_payload": True,
            "with_vector": False,
        }
        if next_offset is not None:
            payload["offset"] = next_offset

        try:
            resp = requests.post(
                f"{qdrant_url}/collections/{collection}/points/scroll",
                headers=headers,
                data=json.dumps(payload),
                timeout=20,
            )
        except requests.RequestException:
            break
        if resp.status_code >= 400:
            break
        try:
            data = resp.json().get("result", {})
        except Exception:
            break
        points = data.get("points", [])
        if not isinstance(points, list) or not points:
            break
        for point in points:
            row = point.get("payload")
            if isinstance(row, dict):
                out.append(row)
                if max_rows > 0 and len(out) >= max_rows:
                    return out
        next_offset = data.get("next_page_offset")
        if next_offset is None:
            break

    return out


def _compute_metrics(rows: list[dict[str, Any]], windows: dict[str, datetime]) -> dict[str, Any]:
    statuses = Counter()
    metrics: dict[str, dict[str, Any]] = {
        key: {"count": 0, "total_amount_czk": 0.0} for key in windows.keys()
    }

    for row in rows:
        status = str(row.get("statuscode") or row.get("stavuhrady") or "UNKNOWN")
        statuses[status] += 1
        dt = _extract_date(row)
        amount = _extract_amount(row)
        for key, threshold in windows.items():
            if dt and dt >= threshold:
                metrics[key]["count"] += 1
                metrics[key]["total_amount_czk"] += amount

    metrics["top_statuses"] = statuses.most_common(10)
    return metrics


def _extract_date(row: dict[str, Any]) -> datetime | None:
    candidates = [
        "datumpotvrzeni",
        "datumvystaveni",
        "datumobjednavky",
        "datum",
        "createdon",
        "modifiedon",
    ]
    value = None
    for key in candidates:
        if row.get(key):
            value = row.get(key)
            break
    if value is None:
        for key, raw in row.items():
            if "datum" in key.lower() and raw:
                value = raw
                break
    if value is None:
        return None

    text = str(value).strip()
    for fmt in (
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
    ):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _extract_amount(row: dict[str, Any]) -> float:
    preferred = [
        "cenacelkem",
        "cenacelkemscph",
        "celkem",
        "total",
        "price",
        "suma",
    ]
    for key in preferred:
        if key in row:
            val = _to_float(row.get(key))
            if val is not None:
                return val
    for key, raw in row.items():
        lk = key.lower()
        if any(t in lk for t in ["cena", "celkem", "total", "price", "amount", "suma"]):
            val = _to_float(raw)
            if val is not None:
                return val
    return 0.0


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if not text:
        return None
    text = text.replace(",", ".")
    cleaned = "".join(ch for ch in text if ch.isdigit() or ch in ".-")
    if not cleaned or cleaned in {"-", ".", "-."}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _write_json_artifact(context: JobContext, filename: str, payload: dict[str, object]) -> str:
    out = Path(context.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(path)


def _write_markdown_artifact(context: JobContext, filename: str, payload: dict[str, Any]) -> str:
    out = Path(context.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename

    o7 = payload["orders"]["7d"]
    long_window = next((k for k in payload["orders"].keys() if k.endswith("d") and k != "7d"), "180d")
    o30 = payload["orders"].get(long_window, {"count": 0, "total_amount_czk": 0.0})
    i7 = payload["invoices"]["7d"]
    i30 = payload["invoices"].get(long_window, {"count": 0, "total_amount_czk": 0.0})

    lines = [
        "# BlueJet KPI Digest",
        "",
        f"Generated: {payload['generated_at']}",
        "",
        "## Summary",
        "",
        f"| Metric | 7d | {long_window} |",
        "|---|---:|---:|",
        f"| Orders count | {o7['count']} | {o30['count']} |",
        f"| Orders amount (CZK) | {o7['total_amount_czk']:.2f} | {o30['total_amount_czk']:.2f} |",
        f"| Invoices count | {i7['count']} | {i30['count']} |",
        f"| Invoices amount (CZK) | {i7['total_amount_czk']:.2f} | {i30['total_amount_czk']:.2f} |",
        "",
        "## Top Order Statuses",
    ]
    for status, count in payload["orders"].get("top_statuses", []):
        lines.append(f"- {status}: {count}")

    lines.append("")
    lines.append("## Top Invoice Statuses")
    for status, count in payload["invoices"].get("top_statuses", []):
        lines.append(f"- {status}: {count}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)
