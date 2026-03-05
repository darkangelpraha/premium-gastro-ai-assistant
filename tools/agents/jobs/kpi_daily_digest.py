from __future__ import annotations

import json
from pathlib import Path

from .base import BaseJob, JobContext, JobResult, utc_now_iso
from .google_api import GoogleApiClient, GoogleApiError


class KPIDailyDigestJob(BaseJob):
    name = "kpi_daily_digest"

    def __init__(self) -> None:
        self.client = GoogleApiClient()

    def run(self, context: JobContext) -> JobResult:
        property_ids = _csv_env(context.env, "GA4_PROPERTY_IDS")
        if not property_ids:
            return JobResult(
                job_name=self.name,
                status="skipped",
                summary="No GA4 properties configured. Set GA4_PROPERTY_IDS.",
            )

        rows: list[dict[str, object]] = []
        findings: list[str] = []
        for property_id in property_ids:
            try:
                yesterday = self._read_metrics(property_id, "yesterday", "yesterday")
                trailing = self._read_metrics(property_id, "7daysAgo", "today")
                row = {
                    "property_id": property_id,
                    "yesterday": yesterday,
                    "last_7d": trailing,
                }
                rows.append(row)
                if yesterday.get("sessions", 0) == 0:
                    findings.append(f"{property_id}: 0 sessions yesterday")
                if trailing.get("transactions", 0) == 0:
                    findings.append(f"{property_id}: 0 transactions over last 7d")
            except GoogleApiError as err:
                findings.append(f"{property_id}: KPI pull failed: {err}")

        json_artifact = _write_json_artifact(context, "kpi_daily_digest.json", {"rows": rows})
        md_artifact = _write_markdown_artifact(context, "kpi_daily_digest.md", rows)

        status = "ok" if not findings else "attention"
        summary = f"Generated KPI digest for {len(rows)} properties"

        return JobResult(
            job_name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            metrics={"properties_in_digest": len(rows), "generated_at": utc_now_iso()},
            artifacts=[json_artifact, md_artifact],
        )

    def _read_metrics(self, property_id: str, start_date: str, end_date: str) -> dict[str, float]:
        payload = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "metrics": [
                {"name": "sessions"},
                {"name": "transactions"},
                {"name": "totalRevenue"},
            ],
        }
        report = self.client.post_json(
            f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
            payload=payload,
        )
        values = (
            report.get("rows", [{}])[0]
            .get("metricValues", [])
        )
        # Expected order follows payload metric order.
        return {
            "sessions": _as_number(values, 0),
            "transactions": _as_number(values, 1),
            "totalRevenue": _as_number(values, 2),
        }


def _as_number(values: list[dict[str, object]], index: int) -> float:
    try:
        raw = str(values[index].get("value", "0"))
    except Exception:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _csv_env(env: dict[str, str], key: str) -> list[str]:
    raw = env.get(key, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _write_json_artifact(context: JobContext, filename: str, payload: dict[str, object]) -> str:
    out = Path(context.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(path)


def _write_markdown_artifact(context: JobContext, filename: str, rows: list[dict[str, object]]) -> str:
    out = Path(context.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename

    lines = [
        "# KPI Daily Digest",
        "",
        "| Property | Sessions (Yesterday) | Transactions (Yesterday) | Revenue (Yesterday) | Sessions (7d) | Transactions (7d) | Revenue (7d) |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        y = row.get("yesterday", {})
        w = row.get("last_7d", {})
        lines.append(
            "| {pid} | {ys:.0f} | {yt:.0f} | {yr:.2f} | {ws:.0f} | {wt:.0f} | {wr:.2f} |".format(
                pid=row.get("property_id", "-"),
                ys=float(y.get("sessions", 0)),
                yt=float(y.get("transactions", 0)),
                yr=float(y.get("totalRevenue", 0)),
                ws=float(w.get("sessions", 0)),
                wt=float(w.get("transactions", 0)),
                wr=float(w.get("totalRevenue", 0)),
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(path)
