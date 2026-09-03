from __future__ import annotations

from platformops.diagnostics.models import (
    DiagnosisReport,
    EvidenceReference,
    Finding,
    Recommendation,
    Severity,
)
from platformops.domain import InvocationContext
from platformops.integrations.capabilities import K8S_INVESTIGATE_NAMESPACE
from platformops.providers.kubernetes import KubernetesIntegration


async def diagnose_kubernetes_namespace(
    namespace: str,
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
) -> DiagnosisReport:
    if integration is None:
        from platformops.mcp.kubernetes_server import build_kubernetes_integration

        integration = build_kubernetes_integration()

    envelope = await integration.invoke(
        K8S_INVESTIGATE_NAMESPACE,
        {"namespace": namespace, "tail_lines": tail_lines},
        InvocationContext(),
    )
    evidence = envelope.to_dict()
    if evidence.get("errors"):
        return _error_report(evidence)

    payload = evidence["payload"]
    evidence_ref = EvidenceReference(
        evidence_id=evidence["evidence_id"],
        source=evidence["source"],
        capability=evidence["capability"],
        note=f"Namespace investigation for {namespace}",
    )

    pods = payload.get("pods", [])
    events = payload.get("events", [])
    logs = payload.get("log_excerpts", [])
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []

    if not pods:
        return DiagnosisReport(
            status=Severity.WARNING,
            summary=f"No pods were found in namespace '{namespace}'.",
            findings=(
                Finding(
                    title="No pods found",
                    severity=Severity.WARNING,
                    summary=(
                        "The namespace is reachable but has no pods. The workload may not be "
                        "deployed, may use another namespace, or may have been removed."
                    ),
                    evidence=(evidence_ref,),
                ),
            ),
            recommendations=(
                Recommendation(action=f"Check deployments in namespace '{namespace}'"),
                Recommendation(action="Confirm the namespace and release name are correct"),
            ),
            evidence=(evidence_ref,),
        )

    for pod in pods:
        pod_events = [
            event for event in events if event.get("involved_object_name") == pod["name"]
        ]
        pod_logs = [log for log in logs if log.get("pod_name") == pod["name"]]
        reasons = " ".join(
            [event.get("reason", "") for event in pod_events]
            + [event.get("message", "") for event in pod_events]
            + [log.get("text", "") for log in pod_logs]
            + [log.get("error", "") for log in pod_logs]
        )
        findings.extend(_pod_findings(namespace, pod, reasons, evidence_ref))

    if not findings:
        findings.append(
            Finding(
                title="Namespace appears healthy",
                severity=Severity.HEALTHY,
                summary=f"All {len(pods)} pod(s) in namespace '{namespace}' appear ready.",
                evidence=(evidence_ref,),
                confidence=0.75,
            )
        )

    for finding in findings:
        recommendations.extend(_recommendations_for(finding, namespace))

    status = _highest_severity(findings)
    summary = _summary_for(status, namespace, findings)
    return DiagnosisReport(
        status=status,
        summary=summary,
        findings=tuple(findings),
        recommendations=tuple(_dedupe_recommendations(recommendations)),
        limitations=(
            "Diagnosis is deterministic and based only on Kubernetes pod, event, and log evidence.",
            "No Prometheus, Jenkins, ArgoCD, or source-control correlation is included yet.",
        ),
        evidence=(evidence_ref,),
    )


def _pod_findings(
    namespace: str,
    pod: dict,
    reasons: str,
    evidence_ref: EvidenceReference,
) -> list[Finding]:
    del namespace
    findings: list[Finding] = []
    pod_name = pod["name"]
    ready = _ready(pod.get("ready", "0/0"))
    restarts = int(pod.get("restarts", 0))
    phase = pod.get("phase", "")
    lower_reasons = reasons.lower()

    if "crashloopbackoff" in lower_reasons or "back-off restarting" in lower_reasons:
        findings.append(
            Finding(
                title=f"{pod_name} is crash looping",
                severity=Severity.CRITICAL,
                summary=(
                    f"{pod_name} shows CrashLoopBackOff-style evidence and has "
                    f"{restarts} restart(s)."
                ),
                evidence=(evidence_ref,),
                confidence=0.92,
            )
        )
    elif "imagepullbackoff" in lower_reasons or "errimagepull" in lower_reasons:
        findings.append(
            Finding(
                title=f"{pod_name} cannot pull its image",
                severity=Severity.CRITICAL,
                summary=f"{pod_name} has image pull failure evidence.",
                evidence=(evidence_ref,),
                confidence=0.9,
            )
        )
    elif phase == "Pending" or "failedscheduling" in lower_reasons or "unschedulable" in lower_reasons:
        findings.append(
            Finding(
                title=f"{pod_name} is not scheduled",
                severity=Severity.CRITICAL,
                summary=f"{pod_name} is pending or has scheduling failure evidence.",
                evidence=(evidence_ref,),
                confidence=0.88,
            )
        )
    elif not ready:
        findings.append(
            Finding(
                title=f"{pod_name} is not ready",
                severity=Severity.WARNING,
                summary=f"{pod_name} is in phase {phase} with readiness {pod.get('ready')}.",
                evidence=(evidence_ref,),
                confidence=0.82,
            )
        )

    if ready and restarts > 0:
        findings.append(
            Finding(
                title=f"{pod_name} restarted but is currently ready",
                severity=Severity.WARNING,
                summary=(
                    f"{pod_name} is currently ready ({pod.get('ready')}) but has "
                    f"{restarts} restart(s)."
                ),
                evidence=(evidence_ref,),
                confidence=0.78,
            )
        )

    return findings


def _recommendations_for(finding: Finding, namespace: str) -> list[Recommendation]:
    title = finding.title.lower()
    if "crash looping" in title:
        return [
            Recommendation(action="Inspect previous container logs for the crashing container"),
            Recommendation(action="Check recent ConfigMap, Secret, image, and environment changes"),
        ]
    if "pull its image" in title:
        return [
            Recommendation(action="Verify the image name, tag, registry credentials, and pull secret"),
            Recommendation(action="Check registry availability from the cluster network"),
        ]
    if "not scheduled" in title:
        return [
            Recommendation(action="Check node capacity, taints, tolerations, and resource requests"),
            Recommendation(action="Inspect scheduler events for the pending pod"),
        ]
    if "not ready" in title:
        return [
            Recommendation(action="Inspect readiness probe configuration and recent application logs"),
            Recommendation(action=f"List events in namespace '{namespace}'"),
        ]
    if "restarted but is currently ready" in title:
        return [
            Recommendation(action="Compare restart timestamps with node restarts, upgrades, or deploys"),
            Recommendation(action="Inspect previous logs if the restart is recent or recurring"),
        ]
    if "healthy" in title:
        return [Recommendation(action="No Kubernetes remediation is recommended")]
    return [Recommendation(action=f"Collect more Kubernetes evidence from namespace '{namespace}'")]


def _error_report(evidence: dict) -> DiagnosisReport:
    error = evidence["errors"][0]
    ref = EvidenceReference(
        evidence_id=evidence["evidence_id"],
        source=evidence["source"],
        capability=evidence["capability"],
        note="Tool returned an error",
    )
    return DiagnosisReport(
        status=Severity.UNKNOWN,
        summary=f"Diagnosis could not be completed: {error['message']}",
        findings=(
            Finding(
                title=error["code"],
                severity=Severity.UNKNOWN,
                summary=error["message"],
                evidence=(ref,),
                confidence=1.0,
            ),
        ),
        recommendations=(Recommendation(action="Fix the policy or provider error and retry"),),
        evidence=(ref,),
    )


def _ready(value: str) -> bool:
    try:
        ready_count, total_count = value.split("/", maxsplit=1)
        return int(ready_count) == int(total_count)
    except ValueError:
        return False


def _highest_severity(findings: list[Finding]) -> Severity:
    order = {
        Severity.HEALTHY: 0,
        Severity.INFO: 1,
        Severity.WARNING: 2,
        Severity.CRITICAL: 3,
        Severity.UNKNOWN: 4,
    }
    return max((finding.severity for finding in findings), key=lambda severity: order[severity])


def _summary_for(status: Severity, namespace: str, findings: list[Finding]) -> str:
    if status == Severity.HEALTHY:
        return f"Namespace '{namespace}' appears healthy."
    if status == Severity.CRITICAL:
        return f"Critical Kubernetes issue detected in namespace '{namespace}'."
    if status == Severity.WARNING:
        return f"Namespace '{namespace}' needs attention."
    return f"Namespace '{namespace}' diagnosis is inconclusive."


def _dedupe_recommendations(items: list[Recommendation]) -> list[Recommendation]:
    seen: set[str] = set()
    result: list[Recommendation] = []
    for item in items:
        if item.action in seen:
            continue
        seen.add(item.action)
        result.append(item)
    return result
