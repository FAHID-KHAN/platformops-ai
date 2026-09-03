from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformops.providers.prometheus.models import (
    PrometheusAlert,
    PrometheusQueryResult,
    PrometheusTarget,
)


class FixturePrometheusProvider:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def _data(self) -> dict[str, Any]:
        return json.loads(self.fixture_path.read_text())

    async def query(self, query: str) -> PrometheusQueryResult:
        data = self._data().get("query", {})
        return PrometheusQueryResult(
            query=query,
            result_type=data.get("result_type", "vector"),
            result=data.get("result", []),
        )

    async def targets(self) -> list[PrometheusTarget]:
        return [PrometheusTarget(**target) for target in self._data().get("targets", [])]

    async def alerts(self) -> list[PrometheusAlert]:
        return [PrometheusAlert(**alert) for alert in self._data().get("alerts", [])]

