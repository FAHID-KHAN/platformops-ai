from __future__ import annotations

from platformops.diagnostics.models import (
    DiagnosisReport,
    EvidenceReference,
    Finding,
    Recommendation,
    Severity,
)
from platformops.integrations.capabilities import (
    DELIVERY_LIST_ARGOCD_APPS,
    DELIVERY_LIST_JENKINS_BUILDS,
)
from platformops.providers.delivery import DeliveryIntegration


async def diagnose_delivery(
    namespace: str | None = None,
    app_name: str | None = None,
    job_name: str | None = None,
    build_limit: int = 10,
    integration: DeliveryIntegration | None = None,
) -> DiagnosisReport:
    if integration is None:
        from platformops.mcp.delivery_server import build_delivery_integration

        integration = build_delivery_integration(provider_name="fake")

    app_envelope = (
        await integration.invoke(DELIVERY_LIST_ARGOCD_APPS, {"namespace": namespace})
    ).to_dict()
    build_envelope = (
        await integration.invoke(
            DELIVERY_LIST_JENKINS_BUILDS,
            {"job_name": job_name, "limit": build_limit},
        )
    ).to_dict()

    evidence_refs = [
        EvidenceReference(
            evidence_id=app_envelope["evidence_id"],
            source=app_envelope["source"],
            capability=app_envelope["capability"],
            note="ArgoCD application evidence",
        ),
        EvidenceReference(
            evidence_id=build_envelope["evidence_id"],
            source=build_envelope["source"],
            capability=build_envelope["capability"],
            note="Jenkins build evidence",
        ),
    ]

    findings: list[Finding] = []
    recommendations: list[Recommendation] = []

    for envelope in (app_envelope, build_envelope):
        if envelope.get("errors"):
            error = envelope["errors"][0]
            findings.append(
                Finding(
                    title=error["code"],
                    severity=Severity.UNKNOWN,
                    summary=error["message"],
                    evidence=(evidence_refs[0] if envelope is app_envelope else evidence_refs[1],),
                    confidence=1.0,
                )
            )

    apps = app_envelope.get("payload", {}).get("argocd_apps", [])
    if app_name:
        apps = [app for app in apps if app["name"] == app_name]
    builds = build_envelope.get("payload", {}).get("jenkins_builds", [])

    for app in apps:
        findings.extend(_argocd_findings(app, evidence_refs[0]))

    for build in builds:
        findings.extend(_jenkins_findings(build, evidence_refs[1]))

    if not apps and not builds and not findings:
        findings.append(
            Finding(
                title="No delivery evidence found",
                severity=Severity.UNKNOWN,
                summary="No matching ArgoCD applications or Jenkins builds were returned.",
                evidence=tuple(evidence_refs),
                confidence=0.7,
            )
        )
        recommendations.append(Recommendation(action="Check delivery provider URLs, credentials, namespace, and job name"))

    if apps and builds:
        recommendations.append(
            Recommendation(
                action="Compare unhealthy Kubernetes timestamps with ArgoCD sync events and Jenkins build times"
            )
        )

    for finding in findings:
        recommendations.extend(_recommendations_for(finding))

    status = _highest_severity(findings)
    return DiagnosisReport(
        status=status,
        summary=_summary_for(status, namespace, app_name, job_name),
        findings=tuple(_rank_findings(findings)),
        recommendations=tuple(_dedupe_recommendations(recommendations)),
        limitations=(
            "Delivery diagnosis is read-only and deterministic.",
            "ArgoCD/Jenkins event timelines are approximate until provider-specific history is expanded.",
            "Kubernetes ownership correlation is not automatic yet.",
        ),
        evidence=tuple(evidence_refs),
    )


def _argocd_findings(app: dict, evidence: EvidenceReference) -> list[Finding]:
    findings: list[Finding] = []
    name = app["name"]
    health = app["health_status"]
    sync = app["sync_status"]
    if health.lower() in {"degraded", "missing", "suspended"}:
        findings.append(
            Finding(
                title=f"ArgoCD app {name} is {health}",
                severity=Severity.CRITICAL,
                summary=f"ArgoCD reports application '{name}' health as {health}.",
                evidence=(evidence,),
                confidence=0.9,
            )
        )
    elif health.lower() not in {"healthy", "progressing"}:
        findings.append(
            Finding(
                title=f"ArgoCD app {name} health is {health}",
                severity=Severity.WARNING,
                summary=f"ArgoCD reports application '{name}' health as {health}.",
                evidence=(evidence,),
                confidence=0.78,
            )
        )
    if sync.lower() != "synced":
        findings.append(
            Finding(
                title=f"ArgoCD app {name} is {sync}",
                severity=Severity.WARNING,
                summary=f"ArgoCD reports application '{name}' sync status as {sync}.",
                evidence=(evidence,),
                confidence=0.86,
            )
        )
    if not findings:
        findings.append(
            Finding(
                title=f"ArgoCD app {name} appears healthy",
                severity=Severity.HEALTHY,
                summary=f"ArgoCD reports application '{name}' as {health} and {sync}.",
                evidence=(evidence,),
                confidence=0.8,
            )
        )
    return findings


def _jenkins_findings(build: dict, evidence: EvidenceReference) -> list[Finding]:
    job = build["job_name"]
    number = build["number"]
    result = build.get("result")
    if build.get("building"):
        return [
            Finding(
                title=f"Jenkins job {job} is still building",
                severity=Severity.INFO,
                summary=f"Jenkins build {job} #{number} is currently running.",
                evidence=(evidence,),
                confidence=0.8,
            )
        ]
    if result in {"FAILURE", "ABORTED", "UNSTABLE"}:
        return [
            Finding(
                title=f"Jenkins job {job} build #{number} ended with {result}",
                severity=Severity.WARNING,
                summary=f"The latest matching Jenkins build finished with result {result}.",
                evidence=(evidence,),
                confidence=0.84,
            )
        ]
    return [
        Finding(
            title=f"Jenkins job {job} build #{number} appears healthy",
            severity=Severity.HEALTHY,
            summary=f"The latest matching Jenkins build finished with result {result or 'UNKNOWN'}.",
            evidence=(evidence,),
            confidence=0.75,
        )
    ]


def _recommendations_for(finding: Finding) -> list[Recommendation]:
    title = finding.title.lower()
    if "argocd app" in title and ("degraded" in title or "missing" in title):
        return [
            Recommendation(action="Inspect ArgoCD application resources, conditions, and sync history"),
            Recommendation(action="Run Kubernetes namespace diagnosis for the application's destination namespace"),
        ]
    if "outofsync" in title or "out of sync" in title:
        return [
            Recommendation(action="Review the ArgoCD diff before approving any sync"),
            Recommendation(action="Check whether the desired revision matches the expected deployment"),
        ]
    if "jenkins job" in title and "failure" in title:
        return [
            Recommendation(action="Open the failed Jenkins build and inspect the first failing stage"),
            Recommendation(action="Compare the failed build time with Kubernetes events and pod restarts"),
        ]
    if "healthy" in title:
        return [Recommendation(action="No delivery remediation is recommended")]
    return [Recommendation(action="Collect more delivery evidence from ArgoCD or Jenkins")]


def _highest_severity(findings: list[Finding]) -> Severity:
    return max((finding.severity for finding in findings), key=_severity_score)


def _rank_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda finding: (-_severity_score(finding.severity), finding.title))


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
    namespace: str | None,
    app_name: str | None,
    job_name: str | None,
) -> str:
    scope = ", ".join(
        item
        for item in (
            f"namespace '{namespace}'" if namespace else None,
            f"app '{app_name}'" if app_name else None,
            f"job '{job_name}'" if job_name else None,
        )
        if item
    ) or "configured delivery sources"
    if status == Severity.CRITICAL:
        return f"Critical delivery issue detected for {scope}."
    if status == Severity.WARNING:
        return f"Delivery source for {scope} needs attention."
    if status == Severity.HEALTHY:
        return f"Delivery source for {scope} appears healthy."
    return f"Delivery diagnosis for {scope} is inconclusive."


def _dedupe_recommendations(items: list[Recommendation]) -> list[Recommendation]:
    seen: set[str] = set()
    result: list[Recommendation] = []
    for item in items:
        if item.action in seen:
            continue
        if item.action == "No delivery remediation is recommended" and any(
            existing.action != item.action for existing in result
        ):
            continue
        seen.add(item.action)
        result.append(item)
    return result
