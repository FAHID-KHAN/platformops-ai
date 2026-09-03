from __future__ import annotations

from typing import Protocol

from platformops.providers.kubernetes.models import NamespaceSummary, NodeSummary, PodSummary


class KubernetesProvider(Protocol):
    async def list_nodes(self) -> list[NodeSummary]: ...

    async def list_namespaces(self) -> list[NamespaceSummary]: ...

    async def list_pods(self, namespace: str | None = None) -> list[PodSummary]: ...

