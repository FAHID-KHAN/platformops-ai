from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformops.providers.kubernetes.models import NamespaceSummary, NodeSummary, PodSummary


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

