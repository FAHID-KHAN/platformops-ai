from __future__ import annotations

from typing import Protocol

from platformops.providers.prometheus.models import (
    PrometheusAlert,
    PrometheusQueryResult,
    PrometheusTarget,
)


class PrometheusProvider(Protocol):
    async def query(self, query: str) -> PrometheusQueryResult: ...

    async def targets(self) -> list[PrometheusTarget]: ...

    async def alerts(self) -> list[PrometheusAlert]: ...

