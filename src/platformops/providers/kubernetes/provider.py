from __future__ import annotations

from typing import Protocol

from platformops.providers.kubernetes.models import (
    EventSummary,
    NamespaceSummary,
    NodeSummary,
    PodDetail,
    PodLogExcerpt,
    PodSummary,
)


class KubernetesProvider(Protocol):
    async def list_nodes(self) -> list[NodeSummary]: ...

    async def list_namespaces(self) -> list[NamespaceSummary]: ...

    async def list_pods(self, namespace: str | None = None) -> list[PodSummary]: ...

    async def get_pod(self, namespace: str, name: str) -> PodDetail: ...

    async def list_events(self, namespace: str, pod_name: str | None = None) -> list[EventSummary]: ...

    async def get_pod_logs(
        self,
        namespace: str,
        name: str,
        container: str | None = None,
        tail_lines: int = 100,
    ) -> PodLogExcerpt: ...
