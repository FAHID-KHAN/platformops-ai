from __future__ import annotations

import asyncio
import os
from pathlib import Path

from platformops.domain import InvocationContext
from platformops.diagnostics.cluster import scan_cluster as scan_kubernetes_cluster
from platformops.diagnostics.kubernetes import diagnose_kubernetes_namespace
from platformops.diagnostics.service import diagnose_service
from platformops.integrations.capabilities import (
    K8S_DIAGNOSE_NAMESPACE,
    K8S_GET_ENDPOINTS,
    K8S_GET_NODES,
    K8S_GET_POD,
    K8S_GET_POD_LOGS,
    K8S_INVESTIGATE_NAMESPACE,
    K8S_LIST_INGRESSES,
    K8S_LIST_EVENTS,
    K8S_LIST_NAMESPACES,
    K8S_LIST_PODS,
    K8S_LIST_SERVICES,
)
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import (
    FakeKubernetesProvider,
    FixtureKubernetesProvider,
    KubernetesApiProvider,
    KubernetesIntegration,
)
from platformops.mcp.prometheus_server import (
    build_prometheus_integration,
    prometheus_alerts_payload,
    prometheus_query_payload,
    prometheus_targets_payload,
)
from platformops.mcp.delivery_server import (
    build_delivery_integration,
    diagnose_delivery_payload,
    list_argocd_apps_payload,
    list_jenkins_builds_payload,
)


def _allowed_namespaces() -> set[str]:
    raw = os.getenv("PLATFORMOPS_K8S_ALLOWED_NAMESPACES", "")
    return {item.strip() for item in raw.split(",") if item.strip()}


def build_kubernetes_integration() -> KubernetesIntegration:
    provider_name = os.getenv("PLATFORMOPS_K8S_PROVIDER", "fake").lower()
    if provider_name == "api":
        provider = KubernetesApiProvider(
            context=os.getenv("PLATFORMOPS_K8S_CONTEXT") or None,
            in_cluster=os.getenv("PLATFORMOPS_K8S_IN_CLUSTER", "false").lower() == "true",
        )
    elif provider_name == "fixture":
        fixture = os.getenv("PLATFORMOPS_K8S_FIXTURE", "tests/scenarios/healthy_cluster.json")
        provider = FixtureKubernetesProvider(Path(fixture))
    else:
        provider = FakeKubernetesProvider()

    return KubernetesIntegration(
        provider=provider,
        policy=KubernetesReadOnlyPolicy(allowed_namespaces=_allowed_namespaces()),
    )


async def get_nodes_payload(integration: KubernetesIntegration | None = None) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(K8S_GET_NODES, {}, InvocationContext())
    return envelope.to_dict()


async def list_namespaces_payload(integration: KubernetesIntegration | None = None) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(K8S_LIST_NAMESPACES, {}, InvocationContext())
    return envelope.to_dict()


async def list_pods_payload(
    namespace: str | None = None,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(K8S_LIST_PODS, {"namespace": namespace}, InvocationContext())
    return envelope.to_dict()


async def get_pod_payload(
    namespace: str,
    name: str,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_GET_POD,
        {"namespace": namespace, "name": name},
        InvocationContext(),
    )
    return envelope.to_dict()


async def list_events_payload(
    namespace: str,
    pod_name: str | None = None,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_LIST_EVENTS,
        {"namespace": namespace, "pod_name": pod_name},
        InvocationContext(),
    )
    return envelope.to_dict()


async def get_pod_logs_payload(
    namespace: str,
    name: str,
    container: str | None = None,
    tail_lines: int = 100,
    previous: bool = False,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_GET_POD_LOGS,
        {
            "namespace": namespace,
            "name": name,
            "container": container,
            "tail_lines": tail_lines,
            "previous": previous,
        },
        InvocationContext(),
    )
    return envelope.to_dict()


async def list_services_payload(
    namespace: str,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_LIST_SERVICES,
        {"namespace": namespace},
        InvocationContext(),
    )
    return envelope.to_dict()


async def get_endpoints_payload(
    namespace: str,
    service_name: str,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_GET_ENDPOINTS,
        {"namespace": namespace, "service_name": service_name},
        InvocationContext(),
    )
    return envelope.to_dict()


async def list_ingresses_payload(
    namespace: str,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_LIST_INGRESSES,
        {"namespace": namespace},
        InvocationContext(),
    )
    return envelope.to_dict()


async def investigate_namespace_payload(
    namespace: str,
    tail_lines: int = 50,
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_INVESTIGATE_NAMESPACE,
        {"namespace": namespace, "tail_lines": tail_lines},
        InvocationContext(),
    )
    return envelope.to_dict()


async def diagnose_namespace_payload(
    namespace: str,
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
    prometheus=None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    report = await diagnose_kubernetes_namespace(
        namespace=namespace,
        tail_lines=tail_lines,
        integration=integration,
        prometheus=prometheus,
    )
    return report.to_dict()


async def diagnose_service_payload(
    name: str,
    namespace: str,
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
    prometheus=None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    report = await diagnose_service(
        name=name,
        namespace=namespace,
        tail_lines=tail_lines,
        integration=integration,
        prometheus=prometheus,
    )
    return report.to_dict()


async def scan_cluster_payload(
    namespaces: list[str] | None = None,
    tail_lines: int = 80,
    integration: KubernetesIntegration | None = None,
    prometheus=None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    selected_namespaces = namespaces or sorted(integration.policy.allowed_namespaces)
    report = await scan_kubernetes_cluster(
        namespaces=selected_namespaces,
        tail_lines=tail_lines,
        integration=integration,
        prometheus=prometheus,
    )
    return {"cluster_scan": report.to_dict(), "markdown": report.to_markdown()}


def create_server():
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The MCP server requires the optional 'mcp' dependency. "
            "Install with: pip install platformops-ai"
        ) from exc

    mcp = FastMCP("platformops-kubernetes")
    integration = build_kubernetes_integration()
    prometheus = build_prometheus_integration()
    delivery = build_delivery_integration()

    @mcp.tool()
    async def get_nodes() -> dict:
        """Return read-only Kubernetes node evidence."""
        return await get_nodes_payload(integration)

    @mcp.tool()
    async def list_namespaces() -> dict:
        """Return read-only Kubernetes namespace evidence."""
        return await list_namespaces_payload(integration)

    @mcp.tool()
    async def list_pods(namespace: str | None = None) -> dict:
        """Return read-only Kubernetes pod evidence."""
        return await list_pods_payload(namespace=namespace, integration=integration)

    @mcp.tool()
    async def get_pod(namespace: str, name: str) -> dict:
        """Return read-only Kubernetes pod detail evidence."""
        return await get_pod_payload(namespace=namespace, name=name, integration=integration)

    @mcp.tool()
    async def list_events(namespace: str, pod_name: str | None = None) -> dict:
        """Return read-only Kubernetes event evidence."""
        return await list_events_payload(
            namespace=namespace,
            pod_name=pod_name,
            integration=integration,
        )

    @mcp.tool()
    async def get_pod_logs(
        namespace: str,
        name: str,
        container: str | None = None,
        tail_lines: int = 100,
        previous: bool = False,
    ) -> dict:
        """Return a bounded read-only Kubernetes pod log excerpt."""
        return await get_pod_logs_payload(
            namespace=namespace,
            name=name,
            container=container,
            tail_lines=tail_lines,
            previous=previous,
            integration=integration,
        )

    @mcp.tool()
    async def list_services(namespace: str) -> dict:
        """Return read-only Kubernetes Service evidence."""
        return await list_services_payload(namespace=namespace, integration=integration)

    @mcp.tool()
    async def get_endpoints(namespace: str, service_name: str) -> dict:
        """Return read-only Kubernetes Endpoints evidence for a Service."""
        return await get_endpoints_payload(
            namespace=namespace,
            service_name=service_name,
            integration=integration,
        )

    @mcp.tool()
    async def list_ingresses(namespace: str) -> dict:
        """Return read-only Kubernetes Ingress evidence."""
        return await list_ingresses_payload(namespace=namespace, integration=integration)

    @mcp.tool()
    async def investigate_namespace(namespace: str, tail_lines: int = 50) -> dict:
        """Collect pod, event, and bounded log evidence for a namespace."""
        return await investigate_namespace_payload(
            namespace=namespace,
            tail_lines=tail_lines,
            integration=integration,
        )

    @mcp.tool()
    async def diagnose_namespace(namespace: str, tail_lines: int = 80) -> dict:
        """Return a deterministic Kubernetes diagnosis report for a namespace."""
        return await diagnose_namespace_payload(
            namespace=namespace,
            tail_lines=tail_lines,
            integration=integration,
            prometheus=prometheus,
        )

    @mcp.tool()
    async def diagnose_service_path(name: str, namespace: str, tail_lines: int = 80) -> dict:
        """Return a deterministic service-path diagnosis report."""
        return await diagnose_service_payload(
            name=name,
            namespace=namespace,
            tail_lines=tail_lines,
            integration=integration,
            prometheus=prometheus,
        )

    @mcp.tool()
    async def scan_cluster(namespaces: str | None = None, tail_lines: int = 80) -> dict:
        """Scan one or more allowed namespaces and return ranked findings."""
        selected_namespaces = None
        if namespaces:
            selected_namespaces = [
                item.strip()
                for item in namespaces.split(",")
                if item.strip()
            ]
        return await scan_cluster_payload(
            namespaces=selected_namespaces,
            tail_lines=tail_lines,
            integration=integration,
            prometheus=prometheus,
        )

    @mcp.tool()
    async def list_argocd_apps(namespace: str | None = None) -> dict:
        """Return read-only ArgoCD application evidence."""
        return await list_argocd_apps_payload(namespace=namespace, integration=delivery)

    @mcp.tool()
    async def list_jenkins_builds(job_name: str | None = None, limit: int = 10) -> dict:
        """Return read-only Jenkins build evidence."""
        return await list_jenkins_builds_payload(
            job_name=job_name,
            limit=limit,
            integration=delivery,
        )

    @mcp.tool()
    async def diagnose_delivery(
        namespace: str | None = None,
        app_name: str | None = None,
        job_name: str | None = None,
        build_limit: int = 10,
    ) -> dict:
        """Return a deterministic ArgoCD/Jenkins delivery diagnosis report."""
        return await diagnose_delivery_payload(
            namespace=namespace,
            app_name=app_name,
            job_name=job_name,
            build_limit=build_limit,
            integration=delivery,
        )

    @mcp.tool()
    async def prometheus_query(query: str) -> dict:
        """Run a read-only Prometheus instant query."""
        return await prometheus_query_payload(query=query, integration=prometheus)

    @mcp.tool()
    async def prometheus_targets() -> dict:
        """Return read-only Prometheus scrape target evidence."""
        return await prometheus_targets_payload(integration=prometheus)

    @mcp.tool()
    async def prometheus_alerts() -> dict:
        """Return read-only Prometheus alert evidence."""
        return await prometheus_alerts_payload(integration=prometheus)

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
