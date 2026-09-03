from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ArgoCDApplicationSummary:
    name: str
    namespace: str | None
    project: str | None
    sync_status: str
    health_status: str
    repo_url: str | None = None
    revision: str | None = None
    target_revision: str | None = None
    conditions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JenkinsBuildSummary:
    job_name: str
    number: int
    result: str | None
    building: bool
    timestamp: str | None = None
    duration_ms: int | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
