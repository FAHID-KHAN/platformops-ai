from __future__ import annotations

from platformops.providers.kubernetes.models import (
    ContainerSummary,
    EventSummary,
    NamespaceSummary,
    NodeSummary,
    PodDetail,
    PodLogExcerpt,
    PodSummary,
)


class FakeKubernetesProvider:
    async def list_nodes(self) -> list[NodeSummary]:
        return [
            NodeSummary(
                name="platformops-control-plane",
                ready=True,
                roles=("control-plane",),
                kubernetes_version="v1.30.0",
            )
        ]

    async def list_namespaces(self) -> list[NamespaceSummary]:
        return [
            NamespaceSummary(name="default", status="Active"),
            NamespaceSummary(name="platformops-demo", status="Active"),
            NamespaceSummary(name="kube-system", status="Active"),
        ]

    async def list_pods(self, namespace: str | None = None) -> list[PodSummary]:
        pods = [
            PodSummary(
                name="checkout-api-7df45b9b9c-2kq4h",
                namespace="platformops-demo",
                phase="Running",
                ready="1/1",
                restarts=0,
                node_name="platformops-control-plane",
            ),
            PodSummary(
                name="coredns-55cb58b774-n9vzt",
                namespace="kube-system",
                phase="Running",
                ready="1/1",
                restarts=0,
                node_name="platformops-control-plane",
            ),
        ]
        if namespace is None:
            return pods
        return [pod for pod in pods if pod.namespace == namespace]

    async def get_pod(self, namespace: str, name: str) -> PodDetail:
        pods = await self.list_pods(namespace)
        match = next((pod for pod in pods if pod.name == name), None)
        if match is None:
            raise KeyError(f"pod not found: {namespace}/{name}")
        return PodDetail(
            name=match.name,
            namespace=match.namespace,
            phase=match.phase,
            ready=match.ready,
            restarts=match.restarts,
            node_name=match.node_name,
            service_account="default",
            containers=(
                ContainerSummary(
                    name="checkout-api",
                    ready=True,
                    restart_count=match.restarts,
                    state="running",
                ),
            ),
            conditions={"Ready": "True", "PodScheduled": "True"},
        )

    async def list_events(self, namespace: str, pod_name: str | None = None) -> list[EventSummary]:
        events = [
            EventSummary(
                namespace="platformops-demo",
                involved_object_name="checkout-api-7df45b9b9c-2kq4h",
                involved_object_kind="Pod",
                type="Normal",
                reason="Started",
                message="Started container checkout-api",
                count=1,
            )
        ]
        filtered = [event for event in events if event.namespace == namespace]
        if pod_name is None:
            return filtered
        return [event for event in filtered if event.involved_object_name == pod_name]

    async def get_pod_logs(
        self,
        namespace: str,
        name: str,
        container: str | None = None,
        tail_lines: int = 100,
    ) -> PodLogExcerpt:
        await self.get_pod(namespace, name)
        return PodLogExcerpt(
            namespace=namespace,
            pod_name=name,
            container=container,
            tail_lines=tail_lines,
            text="2026-09-03T21:00:00Z checkout-api started\n2026-09-03T21:00:01Z health ok",
            truncated=False,
        )
