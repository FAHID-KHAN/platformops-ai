from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from platformops.diagnostics.kubernetes import diagnose_kubernetes_namespace
from platformops.diagnostics.models import (
    DiagnosisReport,
    EvidenceReference,
    Finding,
    Recommendation,
    Severity,
)
from platformops.providers.kubernetes import KubernetesIntegration
from platformops.providers.prometheus.integration import PrometheusIntegration


@dataclass(frozen=True)
class NamespaceScan:
    namespace: str
    status: Severity
    summary: str
    finding_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "status": self.status.value,
            "summary": self.summary,
            "finding_count": self.finding_count,
        }


@dataclass(frozen=True)
class RankedFinding:
    namespace: str
    finding: Finding

    def to_dict(self) -> dict[str, Any]:
        data = self.finding.to_dict()
        data["namespace"] = self.namespace
        return data


@dataclass(frozen=True)
class ClusterScanReport:
    status: Severity
    summary: str
    namespaces: tuple[NamespaceScan, ...]
    findings: tuple[RankedFinding, ...]
    recommendations: tuple[Recommendation, ...]
    limitations: tuple[str, ...]
    evidence: tuple[EvidenceReference, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "summary": self.summary,
            "namespaces": [namespace.to_dict() for namespace in self.namespaces],
            "findings": [finding.to_dict() for finding in self.findings],
            "recommendations": [
                recommendation.to_dict() for recommendation in self.recommendations
            ],
            "limitations": list(self.limitations),
            "evidence": [item.to_dict() for item in self.evidence],
        }

    def to_markdown(self) -> str:
        lines = [f"# Cluster Scan: {self.status.value}", "", self.summary]
        if self.findings:
            lines.extend(["", "## Ranked Findings"])
            for index, ranked in enumerate(self.findings, start=1):
                finding = ranked.finding
                lines.extend(
                    [
                        "",
                        f"{index}. **{finding.severity.value}** `{ranked.namespace}` - {finding.title}",
                        f"   {finding.summary}",
                    ]
                )
        if self.namespaces:
            lines.extend(["", "## Namespace Summary"])
            for namespace in self.namespaces:
                lines.append(
                    f"- `{namespace.namespace}`: {namespace.status.value} - {namespace.summary}"
                )
        if self.recommendations:
            lines.extend(["", "## Recommended Next Actions"])
            for recommendation in self.recommendations:
                lines.append(f"- {recommendation.action}")
        if self.evidence:
            lines.extend(["", "## Evidence"])
            for item in self.evidence:
                lines.append(
                    f"- `{item.evidence_id}` from `{item.source}` via `{item.capability}`: {item.note}"
                )
        if self.limitations:
            lines.extend(["", "## Limitations"])
            for limitation in self.limitations:
                lines.append(f"- {limitation}")
        return "\n".join(lines) + "\n"


async def scan_cluster(
    namespaces: list[str],
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
    prometheus: PrometheusIntegration | None = None,
) -> ClusterScanReport:
    if not namespaces:
        return ClusterScanReport(
            status=Severity.UNKNOWN,
            summary="Cluster scan requires at least one namespace.",
            namespaces=(),
            findings=(),
            recommendations=(Recommendation(action="Provide one or more allowed namespaces to scan"),),
            limitations=("Cluster scan intentionally avoids implicit whole-cluster scans.",),
            evidence=(),
        )

    reports: list[tuple[str, DiagnosisReport]] = []
    for namespace in namespaces:
        reports.append(
            (
                namespace,
                await diagnose_kubernetes_namespace(
                    namespace=namespace,
                    tail_lines=tail_lines,
                    integration=integration,
                    prometheus=prometheus,
                ),
            )
        )

    namespace_scans = tuple(
        NamespaceScan(
            namespace=namespace,
            status=report.status,
            summary=report.summary,
            finding_count=len(report.findings),
        )
        for namespace, report in reports
    )
    findings = _rank_findings(
        RankedFinding(namespace=namespace, finding=finding)
        for namespace, report in reports
        for finding in report.findings
    )
    status = _highest_status([report.status for _, report in reports])
    recommendations = _cluster_recommendations(
        status,
        (
            recommendation
            for _, report in reports
            for recommendation in report.recommendations
        ),
    )
    evidence = _dedupe_evidence(
        item
        for _, report in reports
        for item in report.evidence
    )

    attention_count = sum(
        1
        for namespace in namespace_scans
        if namespace.status not in {Severity.HEALTHY, Severity.INFO}
    )
    return ClusterScanReport(
        status=status,
        summary=_summary_for(status, namespace_scans, attention_count),
        namespaces=namespace_scans,
        findings=findings,
        recommendations=recommendations,
        limitations=(
            "Cluster scan only inspects namespaces explicitly provided by the allowlist.",
            "Diagnosis is deterministic and does not use an LLM.",
            "Cross-namespace ownership, CI/CD, and GitOps correlation are not included yet.",
        ),
        evidence=evidence,
    )


def _rank_findings(findings: Any) -> tuple[RankedFinding, ...]:
    return tuple(
        sorted(
            findings,
            key=lambda item: (
                -_severity_score(item.finding.severity),
                item.namespace,
                item.finding.title,
            ),
        )
    )


def _highest_status(statuses: list[Severity]) -> Severity:
    return max(statuses, key=_severity_score)


def _severity_score(severity: Severity) -> int:
    order = {
        Severity.HEALTHY: 0,
        Severity.INFO: 1,
        Severity.UNKNOWN: 2,
        Severity.WARNING: 3,
        Severity.CRITICAL: 4,
    }
    return order[severity]


def _summary_for(
    status: Severity,
    namespaces: tuple[NamespaceScan, ...],
    attention_count: int,
) -> str:
    scanned = len(namespaces)
    if status == Severity.HEALTHY:
        return f"Scanned {scanned} namespace(s). No issues were detected."
    if status == Severity.CRITICAL:
        return f"Scanned {scanned} namespace(s). Critical issues were detected."
    if status == Severity.WARNING:
        return f"Scanned {scanned} namespace(s). {attention_count} namespace(s) need attention."
    return f"Scanned {scanned} namespace(s). Some results are inconclusive."


def _dedupe_recommendations(items: Any) -> tuple[Recommendation, ...]:
    seen: set[str] = set()
    result: list[Recommendation] = []
    for item in items:
        if item.action in seen:
            continue
        seen.add(item.action)
        result.append(item)
    return tuple(result)


def _cluster_recommendations(
    status: Severity,
    items: Any,
) -> tuple[Recommendation, ...]:
    recommendations = _dedupe_recommendations(items)
    if status in {Severity.HEALTHY, Severity.INFO}:
        return recommendations
    return tuple(
        item
        for item in recommendations
        if item.action != "No Kubernetes remediation is recommended"
    )


def _dedupe_evidence(items: Any) -> tuple[EvidenceReference, ...]:
    seen: set[str] = set()
    result: list[EvidenceReference] = []
    for item in items:
        if item.evidence_id in seen:
            continue
        seen.add(item.evidence_id)
        result.append(item)
    return tuple(result)
