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
    previous: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ServicePortSummary:
    name: str | None
    port: int
    target_port: str | int | None
    protocol: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ServiceSummary:
    name: str
    namespace: str
    type: str
    selector: dict[str, str]
    cluster_ip: str | None
    ports: tuple[ServicePortSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EndpointAddressSummary:
    ip: str
    target_kind: str | None
    target_name: str | None
    ready: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EndpointSummary:
    service_name: str
    namespace: str
    addresses: tuple[EndpointAddressSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IngressRuleSummary:
    host: str | None
    path: str
    service_name: str | None
    service_port: str | int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class IngressSummary:
    name: str
    namespace: str
    ingress_class: str | None
    rules: tuple[IngressRuleSummary, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
