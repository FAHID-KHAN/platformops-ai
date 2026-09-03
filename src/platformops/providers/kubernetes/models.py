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


@dataclass(frozen=True)
class ContainerSummary:
    name: str
    ready: bool
    restart_count: int
    state: str
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PodDetail:
    name: str
    namespace: str
    phase: str
    ready: str
    restarts: int
    node_name: str | None
    service_account: str | None
    containers: tuple[ContainerSummary, ...]
    conditions: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EventSummary:
    namespace: str
    involved_object_name: str
    involved_object_kind: str
    type: str
    reason: str
    message: str
    count: int
    first_timestamp: str | None = None
    last_timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PodLogExcerpt:
    namespace: str
    pod_name: str
    container: str | None
    tail_lines: int
    text: str
    truncated: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
