from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class NodeSummary:
    name: str
    ready: bool
    roles: tuple[str, ...] = ()
    kubernetes_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NamespaceSummary:
    name: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PodSummary:
    name: str
    namespace: str
    phase: str
    ready: str
    restarts: int
    node_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

