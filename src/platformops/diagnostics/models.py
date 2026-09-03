from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    HEALTHY = "healthy"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    source: str
    capability: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Finding:
    title: str
    severity: Severity
    summary: str
    evidence: tuple[EvidenceReference, ...] = ()
    confidence: float = 0.8

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["severity"] = self.severity.value
        data["evidence"] = [item.to_dict() for item in self.evidence]
        return data


@dataclass(frozen=True)
class Recommendation:
    action: str
    risk: str = "read-only"
    approval_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DiagnosisReport:
    status: Severity
    summary: str
    findings: tuple[Finding, ...] = ()
    recommendations: tuple[Recommendation, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
            "recommendations": [
                recommendation.to_dict() for recommendation in self.recommendations
            ],
            "limitations": list(self.limitations),
            "evidence": [item.to_dict() for item in self.evidence],
        }

