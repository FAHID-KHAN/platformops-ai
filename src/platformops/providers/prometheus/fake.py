from __future__ import annotations

from platformops.providers.prometheus.models import (
    PrometheusAlert,
    PrometheusQueryResult,
    PrometheusTarget,
)


class FakePrometheusProvider:
    async def query(self, query: str) -> PrometheusQueryResult:
        return PrometheusQueryResult(
            query=query,
            result_type="vector",
            result=[{"metric": {"job": "jenkins", "namespace": "jenkins"}, "value": [0, "1"]}],
        )

    async def targets(self) -> list[PrometheusTarget]:
        return [
            PrometheusTarget(
                scrape_url="http://jenkins.jenkins.svc:8080/metrics",
                health="up",
                job="jenkins",
                instance="jenkins-0",
            )
        ]

    async def alerts(self) -> list[PrometheusAlert]:
        return []

