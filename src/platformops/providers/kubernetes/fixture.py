from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformops.providers.kubernetes.models import (
    ContainerSummary,
    EndpointAddressSummary,
    EndpointSummary,
    EventSummary,
    IngressRuleSummary,
    IngressSummary,
    NamespaceSummary,
    NodeSummary,
    PodDetail,
    PodLogExcerpt,
    PodSummary,
    ServicePortSummary,
    ServiceSummary,
)


class FixtureKubernetesProvider:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def _data(self) -> dict[str, Any]:
        return json.loads(self.fixture_path.read_text())

    async def list_nodes(self) -> list[NodeSummary]:
        return [NodeSummary(**node) for node in self._data().get("nodes", [])]

    async def list_namespaces(self) -> list[NamespaceSummary]:
        return [NamespaceSummary(**namespace) for namespace in self._data().get("namespaces", [])]

    async def list_pods(self, namespace: str | None = None) -> list[PodSummary]:
        pods = [PodSummary(**pod) for pod in self._data().get("pods", [])]
        if namespace is None:
            return pods
        return [pod for pod in pods if pod.namespace == namespace]

    async def get_pod(self, namespace: str, name: str) -> PodDetail:
        for pod in self._data().get("pod_details", []):
            if pod["namespace"] == namespace and pod["name"] == name:
                containers = tuple(ContainerSummary(**item) for item in pod.get("containers", []))
                return PodDetail(
                    name=pod["name"],
                    namespace=pod["namespace"],
                    phase=pod["phase"],
                    ready=pod["ready"],
                    restarts=pod["restarts"],
                    node_name=pod.get("node_name"),
                    service_account=pod.get("service_account"),
                    containers=containers,
                    conditions=pod.get("conditions", {}),
                )
        raise KeyError(f"pod not found: {namespace}/{name}")

    async def list_events(self, namespace: str, pod_name: str | None = None) -> list[EventSummary]:
        events = [
            EventSummary(**event)
            for event in self._data().get("events", [])
            if event["namespace"] == namespace
        ]
        if pod_name is None:
            return events
        return [event for event in events if event.involved_object_name == pod_name]

    async def get_pod_logs(
        self,
        namespace: str,
        name: str,
        container: str | None = None,
        tail_lines: int = 100,
        previous: bool = False,
    ) -> PodLogExcerpt:
        log_key = "previous_logs" if previous else "logs"
        key = f"{namespace}/{name}"
        logs = self._data().get(log_key, {}).get(key)
        if logs is None:
            await self.get_pod(namespace, name)
            logs = ""
        lines = logs.splitlines()
        excerpt = "\n".join(lines[-tail_lines:])
        return PodLogExcerpt(
            namespace=namespace,
            pod_name=name,
            container=container,
            tail_lines=tail_lines,
            text=excerpt,
            truncated=len(lines) > tail_lines,
            previous=previous,
        )

    async def list_services(self, namespace: str) -> list[ServiceSummary]:
        services = []
        for service in self._data().get("services", []):
            if service["namespace"] != namespace:
                continue
            services.append(
                ServiceSummary(
                    name=service["name"],
                    namespace=service["namespace"],
                    type=service["type"],
                    selector=service.get("selector", {}),
                    cluster_ip=service.get("cluster_ip"),
                    ports=tuple(ServicePortSummary(**port) for port in service.get("ports", [])),
                )
            )
        return services

    async def get_endpoints(self, namespace: str, service_name: str) -> EndpointSummary:
        for endpoint in self._data().get("endpoints", []):
            if endpoint["namespace"] == namespace and endpoint["service_name"] == service_name:
                return EndpointSummary(
                    service_name=endpoint["service_name"],
                    namespace=endpoint["namespace"],
                    addresses=tuple(
                        EndpointAddressSummary(**address)
                        for address in endpoint.get("addresses", [])
                    ),
                )
        return EndpointSummary(service_name=service_name, namespace=namespace, addresses=())

    async def list_ingresses(self, namespace: str) -> list[IngressSummary]:
        ingresses = []
        for ingress in self._data().get("ingresses", []):
            if ingress["namespace"] != namespace:
                continue
            ingresses.append(
                IngressSummary(
                    name=ingress["name"],
                    namespace=ingress["namespace"],
                    ingress_class=ingress.get("ingress_class"),
                    rules=tuple(
                        IngressRuleSummary(**rule)
                        for rule in ingress.get("rules", [])
                    ),
                )
            )
        return ingresses
