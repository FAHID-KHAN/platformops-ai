from __future__ import annotations

from platformops.providers.kubernetes.models import NamespaceSummary, NodeSummary, PodSummary


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

