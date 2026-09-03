from __future__ import annotations

import asyncio
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from platformops.providers.prometheus.models import (
    PrometheusAlert,
    PrometheusQueryResult,
    PrometheusTarget,
)


class PrometheusApiProvider:
    def __init__(self, base_url: str, bearer_token: str | None = None, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token
        self.timeout = timeout

    async def query(self, query: str) -> PrometheusQueryResult:
        data = await self._get_json("/api/v1/query", {"query": query})
        result = data["data"]
        return PrometheusQueryResult(
            query=query,
            result_type=result.get("resultType", ""),
            result=result.get("result", []),
        )

    async def targets(self) -> list[PrometheusTarget]:
        data = await self._get_json("/api/v1/targets")
        active_targets = data["data"].get("activeTargets", [])
        return [
            PrometheusTarget(
                scrape_url=target.get("scrapeUrl", ""),
                health=target.get("health", "unknown"),
                job=target.get("labels", {}).get("job"),
                instance=target.get("labels", {}).get("instance"),
                last_error=target.get("lastError") or None,
            )
            for target in active_targets
        ]

    async def alerts(self) -> list[PrometheusAlert]:
        data = await self._get_json("/api/v1/alerts")
        alerts = data["data"].get("alerts", [])
        return [
            PrometheusAlert(
                name=alert.get("labels", {}).get("alertname", "unknown"),
                state=alert.get("state", "unknown"),
                severity=alert.get("labels", {}).get("severity"),
                summary=alert.get("annotations", {}).get("summary"),
            )
            for alert in alerts
        ]

    async def _get_json(self, path: str, params: dict[str, str] | None = None) -> dict:
        return await asyncio.to_thread(self._get_json_sync, path, params or {})

    def _get_json_sync(self, path: str, params: dict[str, str]) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        headers = {"Accept": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        request = Request(url, headers=headers)
        with urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("status") != "success":
            raise RuntimeError(f"Prometheus API returned status: {payload.get('status')}")
        return payload

