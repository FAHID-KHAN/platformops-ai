from __future__ import annotations

import asyncio

from platformops.providers.kubernetes.models import (
    ContainerSummary,
    EventSummary,
    NamespaceSummary,
    NodeSummary,
    PodDetail,
    PodLogExcerpt,
    PodSummary,
)


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

    async def get_pod(self, namespace: str, name: str) -> PodDetail:
        api = self._core_v1()
        item = await asyncio.to_thread(api.read_namespaced_pod, name=name, namespace=namespace)
        summary = self._pod_summary(item)
        return PodDetail(
            name=summary.name,
            namespace=summary.namespace,
            phase=summary.phase,
            ready=summary.ready,
            restarts=summary.restarts,
            node_name=summary.node_name,
            service_account=item.spec.service_account_name,
            containers=tuple(self._container_summary(status) for status in item.status.container_statuses or []),
            conditions={condition.type: condition.status for condition in item.status.conditions or []},
        )

    async def list_events(self, namespace: str, pod_name: str | None = None) -> list[EventSummary]:
        api = self._core_v1()
        field_selector = f"involvedObject.name={pod_name}" if pod_name else None
        response = await asyncio.to_thread(
            api.list_namespaced_event,
            namespace=namespace,
            field_selector=field_selector,
        )
        return [
            EventSummary(
                namespace=item.metadata.namespace,
                involved_object_name=item.involved_object.name,
                involved_object_kind=item.involved_object.kind,
                type=item.type or "",
                reason=item.reason or "",
                message=item.message or "",
                count=item.count or 1,
                first_timestamp=item.first_timestamp.isoformat() if item.first_timestamp else None,
                last_timestamp=item.last_timestamp.isoformat() if item.last_timestamp else None,
            )
            for item in response.items
        ]

    async def get_pod_logs(
        self,
        namespace: str,
        name: str,
        container: str | None = None,
        tail_lines: int = 100,
    ) -> PodLogExcerpt:
        api = self._core_v1()
        text = await asyncio.to_thread(
            api.read_namespaced_pod_log,
            name=name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
        )
        return PodLogExcerpt(
            namespace=namespace,
            pod_name=name,
            container=container,
            tail_lines=tail_lines,
            text=self._decode_log_text(text),
            truncated=False,
        )

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

    def _container_summary(self, status) -> ContainerSummary:
        state = "unknown"
        reason = None
        if status.state.waiting:
            state = "waiting"
            reason = status.state.waiting.reason
        elif status.state.running:
            state = "running"
        elif status.state.terminated:
            state = "terminated"
            reason = status.state.terminated.reason
        return ContainerSummary(
            name=status.name,
            ready=status.ready,
            restart_count=status.restart_count,
            state=state,
            reason=reason,
        )

    def _decode_log_text(self, text) -> str:
        if isinstance(text, bytes):
            return text.decode("utf-8", errors="replace")
        return str(text)
