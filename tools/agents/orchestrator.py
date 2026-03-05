from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

from tools.agents.jobs.base import JobContext, JobResult
from tools.agents.jobs.ga4_audit import GA4AuditJob
from tools.agents.jobs.gtm_audit import GTMAuditJob
from tools.agents.jobs.internal_ops_snapshot import InternalOpsSnapshotJob
from tools.agents.jobs.kpi_daily_digest import KPIDailyDigestJob
from tools.agents.jobs.bluejet_kpi_digest import BlueJetKPIDigestJob

JOB_REGISTRY = {
    "bluejet_kpi_digest": BlueJetKPIDigestJob,
    "ga4_audit": GA4AuditJob,
    "gtm_audit": GTMAuditJob,
    "kpi_daily_digest": KPIDailyDigestJob,
    "internal_ops_snapshot": InternalOpsSnapshotJob,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Premium Gastro multi-agent orchestrator")
    parser.add_argument("command", choices=["run", "list-profiles", "list-jobs"])
    parser.add_argument("--profile", default="client_impact")
    parser.add_argument(
        "--config",
        default="tools/agents/config.json",
        help="Path to JSON config with profiles/jobs",
    )
    args = parser.parse_args()

    if args.command == "list-jobs":
        for name in sorted(JOB_REGISTRY):
            print(name)
        return 0

    config = _load_config(args.config)

    if args.command == "list-profiles":
        for name in sorted(config.get("profiles", {}).keys()):
            print(name)
        return 0

    return _run_profile(config=config, profile=args.profile)


def _load_config(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise SystemExit(
            f"Config not found: {path}. Copy tools/agents/config.template.json to tools/agents/config.json"
        )
    return json.loads(file_path.read_text(encoding="utf-8"))


def _run_profile(config: dict[str, Any], profile: str) -> int:
    profiles = config.get("profiles", {})
    if profile not in profiles:
        raise SystemExit(f"Unknown profile: {profile}")

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path("reports") / "agent_runs" / f"{run_id}_{profile}"
    output_dir.mkdir(parents=True, exist_ok=True)

    job_names = profiles[profile].get("jobs", [])
    if not job_names:
        raise SystemExit(f"Profile {profile} has no jobs")

    load_dotenv(override=False)
    env = dict(os.environ)
    context = JobContext(
        run_id=run_id,
        profile=profile,
        output_dir=str(output_dir),
        env=env,
    )

    results: list[JobResult] = []
    for job_name in job_names:
        job_class = JOB_REGISTRY.get(job_name)
        if not job_class:
            results.append(
                JobResult(
                    job_name=job_name,
                    status="error",
                    summary=f"Job not registered: {job_name}",
                )
            )
            continue
        job = job_class()
        try:
            result = job.run(context)
        except Exception as err:  # pragma: no cover
            result = JobResult(
                job_name=job_name,
                status="error",
                summary=f"Unhandled exception: {err}",
            )
        results.append(result)

    _write_run_summary(output_dir, profile, run_id, results)
    _print_console_summary(output_dir, results)

    return 0 if all(r.status in {"ok", "skipped", "attention"} for r in results) else 1


def _write_run_summary(
    output_dir: Path,
    profile: str,
    run_id: str,
    results: list[JobResult],
) -> None:
    summary_json = {
        "run_id": run_id,
        "profile": profile,
        "results": [
            {
                "job_name": r.job_name,
                "status": r.status,
                "summary": r.summary,
                "findings": r.findings,
                "metrics": r.metrics,
                "artifacts": r.artifacts,
            }
            for r in results
        ],
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )

    lines = [
        f"# Agent Run Summary ({profile})",
        "",
        f"Run ID: `{run_id}`",
        "",
        "| Job | Status | Summary |",
        "|---|---|---|",
    ]
    for r in results:
        lines.append(f"| {r.job_name} | {r.status} | {r.summary} |")
        for f in r.findings:
            lines.append(f"- {r.job_name}: {f}")
        for a in r.artifacts:
            lines.append(f"- artifact: {a}")

    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_console_summary(output_dir: Path, results: list[JobResult]) -> None:
    print(f"Run output: {output_dir}")
    for r in results:
        print(f"[{r.status}] {r.job_name}: {r.summary}")
        for finding in r.findings[:10]:
            print(f"  - {finding}")


if __name__ == "__main__":
    sys.exit(main())
