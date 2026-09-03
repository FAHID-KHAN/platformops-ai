from __future__ import annotations

import asyncio

from platformops.providers.kubernetes.models import NamespaceSummary, NodeSummary, PodSummary


class KubernetesApiProvider:
    def __init__(self, context: str | None = None, in_cluster: bool = False) -> None:
        self.context = context
        self.in_cluster = in_cluster
        self._client = None

    def _core_v1(self):
        try:
            from kubernetes import client, config
        except ImportError as exc:
            raise RuntimeError(
                "KubernetesApiProvider requires the optional 'kubernetes' dependency. "
                "Install with: pip install -e '.[kubernetes]'"
            ) from exc

        if self._client is None:
            if self.in_cluster:
                config.load_incluster_config()
            else:
                config.load_kube_config(context=self.context)
            self._client = client.CoreV1Api()
        return self._client

    async def list_nodes(self) -> list[NodeSummary]:
        api = self._core_v1()
        response = await asyncio.to_thread(api.list_node)
        nodes: list[NodeSummary] = []
        for item in response.items:
            ready = any(
                condition.type == "Ready" and condition.status == "True"
                for condition in item.status.conditions
            )
            labels = item.metadata.labels or {}
            roles = tuple(
                key.removeprefix("node-role.kubernetes.io/")
                for key in labels
                if key.startswith("node-role.kubernetes.io/")
            )
            nodes.append(
                NodeSummary(
                    name=item.metadata.name,
                    ready=ready,
                    roles=roles,
                    kubernetes_version=item.status.node_info.kubelet_version,
                )
            )
        return nodes

    async def list_namespaces(self) -> list[NamespaceSummary]:
        api = self._core_v1()
        response = await asyncio.to_thread(api.list_namespace)
        return [
            NamespaceSummary(name=item.metadata.name, status=item.status.phase)
            for item in response.items
        ]

    async def list_pods(self, namespace: str | None = None) -> list[PodSummary]:
        api = self._core_v1()
        if namespace is None:
            response = await asyncio.to_thread(api.list_pod_for_all_namespaces)
        else:
            response = await asyncio.to_thread(api.list_namespaced_pod, namespace)
        return [self._pod_summary(item) for item in response.items]

    def _pod_summary(self, item) -> PodSummary:
        container_statuses = item.status.container_statuses or []
        ready_count = sum(1 for status in container_statuses if status.ready)
        restart_count = sum(status.restart_count for status in container_statuses)
        return PodSummary(
            name=item.metadata.name,
            namespace=item.metadata.namespace,
            phase=item.status.phase,
            ready=f"{ready_count}/{len(container_statuses)}",
            restarts=restart_count,
            node_name=item.spec.node_name,
        )

