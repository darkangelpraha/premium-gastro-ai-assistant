from __future__ import annotations

import json
import os
from pathlib import Path

from .base import BaseJob, JobContext, JobResult
from .google_api import GoogleApiClient, GoogleApiError


class GA4AuditJob(BaseJob):
    name = "ga4_audit"

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

        findings: list[str] = []
        metrics: dict[str, int] = {
            "properties_checked": 0,
            "properties_ok": 0,
            "properties_with_findings": 0,
        }
        audit_rows: list[dict[str, object]] = []

        for property_id in property_ids:
            metrics["properties_checked"] += 1
            property_findings: list[str] = []

            try:
                streams = self.client.get_json(
                    f"https://analyticsadmin.googleapis.com/v1beta/properties/{property_id}/dataStreams"
                )
                stream_count = len(streams.get("dataStreams", []))
                if stream_count == 0:
                    property_findings.append("No data streams configured")
            except GoogleApiError as err:
                property_findings.append(f"Failed to read data streams: {err}")
                stream_count = 0

            event_counts: dict[str, int] = {}
            try:
                report = self.client.post_json(
                    f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport",
                    payload={
                        "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                        "dimensions": [{"name": "eventName"}],
                        "metrics": [{"name": "eventCount"}],
                        "limit": 200,
                    },
                )
                for row in report.get("rows", []):
                    dims = row.get("dimensionValues", [])
                    mets = row.get("metricValues", [])
                    if not dims or not mets:
                        continue
                    event_name = dims[0].get("value", "")
                    try:
                        count = int(mets[0].get("value", "0"))
                    except ValueError:
                        count = 0
                    event_counts[event_name] = count

                if event_counts.get("session_start", 0) == 0:
                    property_findings.append("No session_start events in last 7 days")
                if event_counts.get("page_view", 0) == 0:
                    property_findings.append("No page_view events in last 7 days")
                if event_counts.get("purchase", 0) == 0:
                    property_findings.append("No purchase events in last 7 days")
            except GoogleApiError as err:
                property_findings.append(f"Failed to run GA4 report: {err}")

            key_event_count = -1
            try:
                key_events = self.client.get_json(
                    f"https://analyticsadmin.googleapis.com/v1beta/properties/{property_id}/keyEvents"
                )
                key_event_count = len(key_events.get("keyEvents", []))
                if key_event_count == 0:
                    property_findings.append("No key events configured")
            except GoogleApiError:
                # Some accounts/API versions may not expose keyEvents.
                pass

            audit_rows.append(
                {
                    "property_id": property_id,
                    "stream_count": stream_count,
                    "key_event_count": key_event_count,
                    "event_counts": {
                        "session_start": event_counts.get("session_start", 0),
                        "page_view": event_counts.get("page_view", 0),
                        "purchase": event_counts.get("purchase", 0),
                    },
                    "findings": property_findings,
                }
            )

            if property_findings:
                metrics["properties_with_findings"] += 1
                findings.extend([f"{property_id}: {f}" for f in property_findings])
            else:
                metrics["properties_ok"] += 1

        artifact = _write_json_artifact(context, "ga4_audit.json", {"rows": audit_rows})
        status = "ok" if not findings else "attention"
        summary = (
            f"GA4 audited {metrics['properties_checked']} properties, "
            f"{metrics['properties_with_findings']} with findings"
        )

        return JobResult(
            job_name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            metrics=metrics,
            artifacts=[artifact],
        )


def _csv_env(env: dict[str, str], key: str) -> list[str]:
    raw = env.get(key, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _write_json_artifact(context: JobContext, filename: str, payload: dict[str, object]) -> str:
    out = Path(context.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(path)
