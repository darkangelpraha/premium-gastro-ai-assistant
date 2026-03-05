from __future__ import annotations

import json
from pathlib import Path

from .base import BaseJob, JobContext, JobResult
from .google_api import GoogleApiClient, GoogleApiError


class GTMAuditJob(BaseJob):
    name = "gtm_audit"

    def __init__(self) -> None:
        self.client = GoogleApiClient()

    def run(self, context: JobContext) -> JobResult:
        containers = _csv_env(context.env, "GTM_CONTAINER_IDS")
        if not containers:
            return JobResult(
                job_name=self.name,
                status="skipped",
                summary="No GTM containers configured. Set GTM_CONTAINER_IDS.",
            )

        findings: list[str] = []
        rows: list[dict[str, object]] = []

        for raw in containers:
            container_path = _normalize_container_path(raw)
            if not container_path:
                findings.append(f"{raw}: invalid container format")
                continue

            container_findings: list[str] = []
            workspace_count = 0
            tag_count = 0
            trigger_count = 0

            try:
                workspaces = self.client.get_json(
                    f"https://tagmanager.googleapis.com/tagmanager/v2/{container_path}/workspaces"
                )
                ws = workspaces.get("workspace", [])
                workspace_count = len(ws)
                if workspace_count == 0:
                    container_findings.append("No workspaces found")
                else:
                    first_ws = ws[0].get("path", "")
                    if first_ws:
                        tags = self.client.get_json(
                            f"https://tagmanager.googleapis.com/tagmanager/v2/{first_ws}/tags"
                        ).get("tag", [])
                        triggers = self.client.get_json(
                            f"https://tagmanager.googleapis.com/tagmanager/v2/{first_ws}/triggers"
                        ).get("trigger", [])
                        tag_count = len(tags)
                        trigger_count = len(triggers)
                        if tag_count == 0:
                            container_findings.append("No tags in primary workspace")
                        if trigger_count == 0:
                            container_findings.append("No triggers in primary workspace")
                        if not _has_ga4_signal(tags):
                            container_findings.append(
                                "No obvious GA4 tag found (name/type check)"
                            )
            except GoogleApiError as err:
                container_findings.append(f"GTM API error: {err}")

            rows.append(
                {
                    "container": container_path,
                    "workspace_count": workspace_count,
                    "tag_count": tag_count,
                    "trigger_count": trigger_count,
                    "findings": container_findings,
                }
            )
            findings.extend([f"{container_path}: {f}" for f in container_findings])

        artifact = _write_json_artifact(context, "gtm_audit.json", {"rows": rows})
        status = "ok" if not findings else "attention"
        summary = f"GTM audited {len(rows)} containers, {len(findings)} findings"

        return JobResult(
            job_name=self.name,
            status=status,
            summary=summary,
            findings=findings,
            metrics={"containers_checked": len(rows), "findings_count": len(findings)},
            artifacts=[artifact],
        )


def _csv_env(env: dict[str, str], key: str) -> list[str]:
    raw = env.get(key, "")
    return [x.strip() for x in raw.split(",") if x.strip()]


def _normalize_container_path(raw: str) -> str | None:
    value = raw.strip()
    if value.startswith("accounts/") and "/containers/" in value:
        return value
    if "/" in value:
        account_id, container_id = value.split("/", 1)
        account_id = account_id.strip()
        container_id = container_id.strip()
        if account_id.isdigit() and container_id.isdigit():
            return f"accounts/{account_id}/containers/{container_id}"
    return None


def _has_ga4_signal(tags: list[dict[str, object]]) -> bool:
    for tag in tags:
        name = str(tag.get("name", "")).lower()
        tag_type = str(tag.get("type", "")).lower()
        if "ga4" in name or "google tag" in name:
            return True
        if tag_type in {"gaawc", "gaawe", "googtag", "gawe"}:
            return True
    return False


def _write_json_artifact(context: JobContext, filename: str, payload: dict[str, object]) -> str:
    out = Path(context.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return str(path)
