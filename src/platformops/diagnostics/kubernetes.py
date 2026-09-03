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
from platformops.providers.prometheus.integration import PROM_ALERTS, PROM_TARGETS, PrometheusIntegration


async def diagnose_kubernetes_namespace(
    namespace: str,
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
    prometheus: PrometheusIntegration | None = None,
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
    evidence_refs: list[EvidenceReference] = [evidence_ref]

    if not pods:
        findings.append(
            Finding(
                title="No pods found",
                severity=Severity.WARNING,
                summary=(
                    "The namespace is reachable but has no pods. The workload may not be "
                    "deployed, may use another namespace, or may have been removed."
                ),
                evidence=(evidence_ref,),
            )
        )
        recommendations.extend(
            [
                Recommendation(action=f"Check deployments in namespace '{namespace}'"),
                Recommendation(action="Confirm the namespace and release name are correct"),
            ]
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

    if prometheus is not None:
        prom_findings, prom_recommendations, prom_refs = await _prometheus_findings(
            prometheus=prometheus,
            namespace=namespace,
        )
        findings.extend(prom_findings)
        recommendations.extend(prom_recommendations)
        evidence_refs.extend(prom_refs)

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
            "Diagnosis is deterministic and does not use an LLM.",
            "Jenkins, ArgoCD, and source-control correlation are not included yet.",
        ),
        evidence=tuple(evidence_refs),
    )


async def _prometheus_findings(
    prometheus: PrometheusIntegration,
    namespace: str,
) -> tuple[list[Finding], list[Recommendation], list[EvidenceReference]]:
    findings: list[Finding] = []
    recommendations: list[Recommendation] = []
    refs: list[EvidenceReference] = []

    targets_envelope = (await prometheus.invoke(PROM_TARGETS, {})).to_dict()
    alerts_envelope = (await prometheus.invoke(PROM_ALERTS, {})).to_dict()

    if targets_envelope.get("errors"):
        refs.append(_prom_ref(targets_envelope, "Prometheus targets returned an error"))
        findings.append(
            Finding(
                title="Prometheus targets could not be inspected",
                severity=Severity.UNKNOWN,
                summary=targets_envelope["errors"][0]["message"],
                evidence=(refs[-1],),
                confidence=1.0,
            )
        )
        recommendations.append(Recommendation(action="Verify Prometheus URL, authentication, and network access"))
        return findings, recommendations, refs

    target_ref = _prom_ref(targets_envelope, "Prometheus scrape targets")
    refs.append(target_ref)
    targets = targets_envelope["payload"].get("targets", [])
    relevant_targets = [
        target
        for target in targets
        if _matches_namespace(target, namespace) or _matches_text(target.get("job"), namespace)
    ]
    down_targets = [target for target in relevant_targets if target.get("health") != "up"]
    if down_targets:
        findings.append(
            Finding(
                title="Prometheus target is down",
                severity=Severity.CRITICAL,
                summary=(
                    f"Prometheus reports {len(down_targets)} target(s) related to "
                    f"namespace '{namespace}' as not up."
                ),
                evidence=(target_ref,),
                confidence=0.86,
            )
        )
        recommendations.append(Recommendation(action="Check ServiceMonitor, endpoints, service labels, and target errors"))

    if alerts_envelope.get("errors"):
        refs.append(_prom_ref(alerts_envelope, "Prometheus alerts returned an error"))
    else:
        alert_ref = _prom_ref(alerts_envelope, "Prometheus alerts")
        refs.append(alert_ref)
        alerts = alerts_envelope["payload"].get("alerts", [])
        firing_alerts = [
            alert
            for alert in alerts
            if alert.get("state") == "firing"
            and (
                _matches_text(alert.get("name"), namespace)
                or _matches_text(alert.get("summary"), namespace)
            )
        ]
        if firing_alerts:
            findings.append(
                Finding(
                    title="Prometheus alert is firing",
                    severity=Severity.WARNING,
                    summary=(
                        f"Prometheus has {len(firing_alerts)} firing alert(s) that appear "
                        f"related to namespace '{namespace}'."
                    ),
                    evidence=(alert_ref,),
                    confidence=0.8,
                )
            )
            recommendations.append(Recommendation(action="Inspect the firing Prometheus alert annotations and runbook"))

    return findings, recommendations, refs


def _prom_ref(envelope: dict, note: str) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=envelope["evidence_id"],
        source=envelope["source"],
        capability=envelope["capability"],
        note=note,
    )


def _matches_namespace(target: dict, namespace: str) -> bool:
    haystack = " ".join(
        str(value)
        for value in (
            target.get("scrape_url"),
            target.get("job"),
            target.get("instance"),
            target.get("last_error"),
        )
        if value
    )
    return namespace.lower() in haystack.lower()


def _matches_text(value: str | None, needle: str) -> bool:
    return bool(value) and needle.lower() in value.lower()


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
    if "no pods found" in title:
        return [
            Recommendation(action=f"Check deployments in namespace '{namespace}'"),
            Recommendation(action="Confirm the namespace and release name are correct"),
        ]
    if "prometheus target is down" in title:
        return [Recommendation(action="Check ServiceMonitor, endpoints, service labels, and target errors")]
    if "prometheus alert is firing" in title:
        return [Recommendation(action="Inspect the firing Prometheus alert annotations and runbook")]
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
