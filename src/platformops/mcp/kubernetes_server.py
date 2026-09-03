from __future__ import annotations

import asyncio
import os
from pathlib import Path

from platformops.domain import InvocationContext
from platformops.integrations.capabilities import (
    K8S_GET_NODES,
    K8S_GET_POD,
    K8S_GET_POD_LOGS,
    K8S_INVESTIGATE_NAMESPACE,
    K8S_LIST_EVENTS,
    K8S_LIST_NAMESPACES,
    K8S_LIST_PODS,
)
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import (
    FakeKubernetesProvider,
    FixtureKubernetesProvider,
    KubernetesApiProvider,
    KubernetesIntegration,
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
    integration: KubernetesIntegration | None = None,
) -> dict:
    integration = integration or build_kubernetes_integration()
    envelope = await integration.invoke(
        K8S_GET_POD_LOGS,
        {"namespace": namespace, "name": name, "container": container, "tail_lines": tail_lines},
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
    ) -> dict:
        """Return a bounded read-only Kubernetes pod log excerpt."""
        return await get_pod_logs_payload(
            namespace=namespace,
            name=name,
            container=container,
            tail_lines=tail_lines,
            integration=integration,
        )

    @mcp.tool()
    async def investigate_namespace(namespace: str, tail_lines: int = 50) -> dict:
        """Collect pod, event, and bounded log evidence for a namespace."""
        return await investigate_namespace_payload(
            namespace=namespace,
            tail_lines=tail_lines,
            integration=integration,
        )

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
