from __future__ import annotations

from platformops.diagnostics.kubernetes import diagnose_kubernetes_namespace
from platformops.diagnostics.models import (
    DiagnosisReport,
    EvidenceReference,
    Finding,
    Recommendation,
    Severity,
)
from platformops.domain import InvocationContext
from platformops.integrations.capabilities import (
    K8S_GET_ENDPOINTS,
    K8S_LIST_INGRESSES,
    K8S_LIST_SERVICES,
)
from platformops.providers.kubernetes import KubernetesIntegration
from platformops.providers.prometheus.integration import PrometheusIntegration


async def diagnose_service(
    name: str,
    namespace: str,
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
    prometheus: PrometheusIntegration | None = None,
) -> DiagnosisReport:
    namespace_report = await diagnose_kubernetes_namespace(
        namespace=namespace,
        tail_lines=tail_lines,
        integration=integration,
        prometheus=prometheus,
    )
    if integration is None:
        from platformops.mcp.kubernetes_server import build_kubernetes_integration

        integration = build_kubernetes_integration()

    services_envelope = (
        await integration.invoke(
            K8S_LIST_SERVICES,
            {"namespace": namespace},
            InvocationContext(),
        )
    ).to_dict()
    ingresses_envelope = (
        await integration.invoke(
            K8S_LIST_INGRESSES,
            {"namespace": namespace},
            InvocationContext(),
        )
    ).to_dict()

    refs = list(namespace_report.evidence)
    findings = list(namespace_report.findings)
    recommendations = list(namespace_report.recommendations)

    service_ref = _ref(services_envelope, f"Services in namespace {namespace}")
    ingress_ref = _ref(ingresses_envelope, f"Ingresses in namespace {namespace}")
    refs.extend([service_ref, ingress_ref])

    services = services_envelope.get("payload", {}).get("services", [])
    service = _find_service(services, name)
    if service is None:
        findings.append(
            Finding(
                title=f"Service {name} was not found",
                severity=Severity.CRITICAL,
                summary=f"No Kubernetes Service named or matching '{name}' was found in namespace '{namespace}'.",
                evidence=(service_ref,),
                confidence=0.9,
            )
        )
        recommendations.append(Recommendation(action=f"Create or verify the Service for workload '{name}'"))
    else:
        endpoints_envelope = (
            await integration.invoke(
                K8S_GET_ENDPOINTS,
                {"namespace": namespace, "service_name": service["name"]},
                InvocationContext(),
            )
        ).to_dict()
        endpoint_ref = _ref(endpoints_envelope, f"Endpoints for Service {service['name']}")
        refs.append(endpoint_ref)
        endpoints = endpoints_envelope.get("payload", {}).get("endpoints", {})
        ready_addresses = [address for address in endpoints.get("addresses", []) if address.get("ready")]
        if not ready_addresses:
            findings.append(
                Finding(
                    title=f"Service {service['name']} has no ready endpoints",
                    severity=Severity.CRITICAL,
                    summary=(
                        f"The Service exists, but Kubernetes reports no ready endpoint addresses. "
                        f"Traffic to '{service['name']}' is unlikely to reach a ready pod."
                    ),
                    evidence=(endpoint_ref,),
                    confidence=0.9,
                )
            )
            recommendations.append(
                Recommendation(action="Check Service selector labels against pod labels and readiness state")
            )
        else:
            findings.append(
                Finding(
                    title=f"Service {service['name']} has ready endpoints",
                    severity=Severity.INFO,
                    summary=f"Kubernetes reports {len(ready_addresses)} ready endpoint(s) for the Service.",
                    evidence=(endpoint_ref,),
                    confidence=0.78,
                )
            )

    ingresses = ingresses_envelope.get("payload", {}).get("ingresses", [])
    linked_ingresses = [
        ingress
        for ingress in ingresses
        for rule in ingress.get("rules", [])
        if rule.get("service_name") == (service or {}).get("name", name)
    ]
    if linked_ingresses:
        findings.append(
            Finding(
                title="Ingress routes to the service",
                severity=Severity.INFO,
                summary=f"Found {len(linked_ingresses)} ingress object(s) routing to the service.",
                evidence=(ingress_ref,),
                confidence=0.76,
            )
        )

    status = _highest(findings)
    return DiagnosisReport(
        status=status,
        summary=_summary(status, name, namespace),
        findings=tuple(findings),
        recommendations=tuple(_dedupe(_filter_recommendations(recommendations, status))),
        limitations=(
            "Service diagnosis is deterministic and read-only.",
            "NetworkPolicy, DNS, TLS, and application-level probes are not inspected yet.",
        ),
        evidence=tuple(refs),
    )


def _find_service(services: list[dict], name: str) -> dict | None:
    for service in services:
        if service["name"] == name:
            return service
    for service in services:
        if name in service["name"]:
            return service
    return None


def _ref(envelope: dict, note: str) -> EvidenceReference:
    return EvidenceReference(
        evidence_id=envelope["evidence_id"],
        source=envelope["source"],
        capability=envelope["capability"],
        note=note,
    )


def _highest(findings: list[Finding]) -> Severity:
    order = {
        Severity.HEALTHY: 0,
        Severity.INFO: 1,
        Severity.WARNING: 2,
        Severity.CRITICAL: 3,
        Severity.UNKNOWN: 4,
    }
    return max((finding.severity for finding in findings), key=lambda severity: order[severity])


def _summary(status: Severity, name: str, namespace: str) -> str:
    if status == Severity.CRITICAL:
        return f"Critical service issue detected for '{name}' in namespace '{namespace}'."
    if status == Severity.WARNING:
        return f"Service '{name}' in namespace '{namespace}' needs attention."
    return f"Service '{name}' in namespace '{namespace}' has no critical Kubernetes service-path findings."


def _dedupe(items: list[Recommendation]) -> list[Recommendation]:
    seen: set[str] = set()
    result: list[Recommendation] = []
    for item in items:
        if item.action in seen:
            continue
        seen.add(item.action)
        result.append(item)
    return result


def _filter_recommendations(items: list[Recommendation], status: Severity) -> list[Recommendation]:
    if status in {Severity.CRITICAL, Severity.WARNING}:
        return [
            item
            for item in items
            if item.action != "No Kubernetes remediation is recommended"
        ]
    return items
