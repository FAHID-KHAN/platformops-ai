from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class RiskLevel(StrEnum):
    READ_ONLY = "read-only"
    WRITE = "write"


@dataclass(frozen=True)
class IntegrationManifest:
    id: str
    version: int
    capabilities: tuple[str, ...]
    risk_level: RiskLevel
    evidence_types: tuple[str, ...]
    authentication: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risk_level"] = self.risk_level.value
        return data


@dataclass(frozen=True)
class IntegrationHealth:
    status: str
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InvocationContext:
    request_id: str = field(default_factory=lambda: str(uuid4()))
    actor: str = "mcp-client"


@dataclass(frozen=True)
class ToolError:
    code: str
    message: str
    retryable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceEnvelope:
    source: str
    capability: str
    evidence_type: str
    payload: dict[str, Any]
    scope: dict[str, Any] = field(default_factory=dict)
    errors: tuple[ToolError, ...] = ()
    redacted: bool = False
    schema_version: int = 1
    evidence_id: str = field(default_factory=lambda: f"ev-{uuid4()}")
    collected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "source": self.source,
            "capability": self.capability,
            "evidence_type": self.evidence_type,
            "schema_version": self.schema_version,
            "collected_at": self.collected_at.isoformat(),
            "scope": self.scope,
            "redacted": self.redacted,
            "payload": self.payload,
            "errors": [error.to_dict() for error in self.errors],
        }

