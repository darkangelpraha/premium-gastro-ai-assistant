from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class JobResult:
    job_name: str
    status: str
    summary: str
    findings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)


@dataclass(slots=True)
class JobContext:
    run_id: str
    profile: str
    output_dir: str
    env: dict[str, str]


class BaseJob:
    name = "base"

    def run(self, context: JobContext) -> JobResult:
        raise NotImplementedError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
