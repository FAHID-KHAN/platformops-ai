from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from platformops.diagnostics.delivery import diagnose_delivery
from platformops.diagnostics.kubernetes import diagnose_kubernetes_namespace
from platformops.diagnostics.models import DiagnosisReport, EvidenceReference, Recommendation, Severity
from platformops.diagnostics.service import diagnose_service
from platformops.providers.delivery import DeliveryIntegration
from platformops.providers.kubernetes import KubernetesIntegration
from platformops.providers.prometheus.integration import PrometheusIntegration


@dataclass(frozen=True)
class EvidenceChainItem:
    source: str
    severity: Severity
    title: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "severity": self.severity.value,
            "title": self.title,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class AppInvestigationReport:
    app: str
    namespace: str
    status: Severity
    summary: str
    likely_explanation: str
    evidence_chain: tuple[EvidenceChainItem, ...]
    recommendations: tuple[Recommendation, ...]
    limitations: tuple[str, ...]
    evidence: tuple[EvidenceReference, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "app": self.app,
            "namespace": self.namespace,
            "status": self.status.value,
            "summary": self.summary,
            "likely_explanation": self.likely_explanation,
            "evidence_chain": [item.to_dict() for item in self.evidence_chain],
            "recommendations": [
                recommendation.to_dict() for recommendation in self.recommendations
            ],
            "limitations": list(self.limitations),
            "evidence": [item.to_dict() for item in self.evidence],
        }

    def to_markdown(self) -> str:
        lines = [
            f"# App Investigation: {self.app}",
            "",
            f"Status: **{self.status.value}**",
            "",
            self.summary,
            "",
            "## Likely Explanation",
            "",
            self.likely_explanation,
        ]
        if self.evidence_chain:
            lines.extend(["", "## Evidence Chain"])
            for index, item in enumerate(self.evidence_chain, start=1):
                lines.extend(
                    [
                        f"{index}. **{item.severity.value}** `{item.source}` - {item.title}",
                        f"   {item.summary}",
                    ]
                )
        if self.recommendations:
            lines.extend(["", "## Recommended Next Checks"])
            for recommendation in self.recommendations:
                lines.append(f"- {recommendation.action}")
        if self.limitations:
            lines.extend(["", "## Limitations"])
            for limitation in self.limitations:
                lines.append(f"- {limitation}")
        return "\n".join(lines) + "\n"


async def investigate_app(
    app: str,
    namespace: str,
    service_name: str | None = None,
    argocd_app: str | None = None,
    jenkins_job: str | None = None,
    tail_lines: int = 80,
    kubernetes: KubernetesIntegration | None = None,
    prometheus: PrometheusIntegration | None = None,
    delivery: DeliveryIntegration | None = None,
) -> AppInvestigationReport:
    service_name = service_name or app
    argocd_app = argocd_app or app

    namespace_report = await diagnose_kubernetes_namespace(
        namespace=namespace,
        tail_lines=tail_lines,
        integration=kubernetes,
        prometheus=prometheus,
    )
    service_report = await diagnose_service(
        name=service_name,
        namespace=namespace,
        tail_lines=tail_lines,
        integration=kubernetes,
        prometheus=prometheus,
    )
    delivery_report = await diagnose_delivery(
        namespace=namespace,
        app_name=argocd_app,
        job_name=jenkins_job,
        integration=delivery,
    )

    source_reports = (
        ("kubernetes", namespace_report),
        ("service", service_report),
        ("delivery", delivery_report),
    )
    chain = _rank_chain(
        EvidenceChainItem(
            source=source,
            severity=finding.severity,
            title=finding.title,
            summary=finding.summary,
        )
        for source, report in source_reports
        for finding in report.findings
    )
    status = _highest([report.status for _, report in source_reports])
    recommendations = _dedupe_recommendations(
        recommendation
        for _, report in source_reports
        for recommendation in report.recommendations
    )
    evidence = _dedupe_evidence(
        item
        for _, report in source_reports
        for item in report.evidence
    )

    return AppInvestigationReport(
        app=app,
        namespace=namespace,
        status=status,
        summary=_summary_for(app, namespace, status),
        likely_explanation=_likely_explanation(chain),
        evidence_chain=chain,
        recommendations=recommendations,
        limitations=(
            "App investigation is read-only and deterministic.",
            "Timeline correlation uses available status evidence, not full event history yet.",
            "Ownership detection is not automatic yet; pass app, service, ArgoCD app, and Jenkins job names explicitly when they differ.",
        ),
        evidence=evidence,
    )


def _rank_chain(items: Any) -> tuple[EvidenceChainItem, ...]:
    return tuple(
        sorted(
            items,
            key=lambda item: (-_severity_score(item.severity), item.source, item.title),
        )
    )


def _highest(statuses: list[Severity]) -> Severity:
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


def _summary_for(app: str, namespace: str, status: Severity) -> str:
    if status == Severity.CRITICAL:
        return f"Application '{app}' in namespace '{namespace}' has critical evidence."
    if status == Severity.WARNING:
        return f"Application '{app}' in namespace '{namespace}' needs attention."
    if status == Severity.HEALTHY:
        return f"Application '{app}' in namespace '{namespace}' appears healthy."
    return f"Application '{app}' in namespace '{namespace}' investigation is inconclusive."


def _likely_explanation(chain: tuple[EvidenceChainItem, ...]) -> str:
    delivery_bad = [
        item for item in chain
        if item.source == "delivery" and item.severity in {Severity.CRITICAL, Severity.WARNING}
    ]
    kubernetes_bad = [
        item for item in chain
        if item.source in {"kubernetes", "service"}
        and item.severity in {Severity.CRITICAL, Severity.WARNING}
    ]
    if delivery_bad and kubernetes_bad:
        return (
            "Delivery evidence is correlated with Kubernetes symptoms. Start with the "
            "highest-severity delivery finding, then compare it with pod events, logs, "
            "and service-path evidence."
        )
    if kubernetes_bad:
        return (
            "Kubernetes or service-path evidence is the clearest signal. Start with the "
            "highest-severity pod, event, log, or endpoint finding."
        )
    if delivery_bad:
        return (
            "Delivery evidence needs attention, but Kubernetes evidence does not show a "
            "matching critical symptom yet."
        )
    if chain:
        return "No critical cross-source issue was detected from the available evidence."
    return "No evidence was collected for this application investigation."


def _dedupe_recommendations(items: Any) -> tuple[Recommendation, ...]:
    seen: set[str] = set()
    result: list[Recommendation] = []
    for item in items:
        if item.action in seen:
            continue
        if item.action in {
            "No Kubernetes remediation is recommended",
            "No delivery remediation is recommended",
        } and result:
            continue
        seen.add(item.action)
        result.append(item)
    return tuple(result)


def _dedupe_evidence(items: Any) -> tuple[EvidenceReference, ...]:
    seen: set[str] = set()
    result: list[EvidenceReference] = []
    for item in items:
        if item.evidence_id in seen:
            continue
        seen.add(item.evidence_id)
        result.append(item)
    return tuple(result)
