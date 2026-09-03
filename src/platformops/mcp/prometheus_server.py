from __future__ import annotations

import os
from pathlib import Path

from platformops.providers.prometheus import (
    FakePrometheusProvider,
    FixturePrometheusProvider,
    PrometheusApiProvider,
)
from platformops.providers.prometheus.integration import (
    PROM_ALERTS,
    PROM_QUERY,
    PROM_TARGETS,
    PrometheusIntegration,
)


def build_prometheus_integration(
    provider_name: str | None = None,
    url: str | None = None,
    fixture: str | None = None,
) -> PrometheusIntegration | None:
    provider_name = (provider_name or os.getenv("PLATFORMOPS_PROMETHEUS_PROVIDER", "")).lower()
    url = url or os.getenv("PLATFORMOPS_PROMETHEUS_URL")
    fixture = fixture or os.getenv("PLATFORMOPS_PROMETHEUS_FIXTURE")

    if provider_name == "fake":
        provider = FakePrometheusProvider()
    elif provider_name == "fixture":
        provider = FixturePrometheusProvider(Path(fixture or "tests/scenarios/prometheus_healthy.json"))
    elif url:
        provider = PrometheusApiProvider(
            base_url=url,
            bearer_token=os.getenv("PLATFORMOPS_PROMETHEUS_BEARER_TOKEN") or None,
        )
    else:
        return None
    return PrometheusIntegration(provider)


async def prometheus_query_payload(query: str, integration: PrometheusIntegration | None = None) -> dict:
    integration = integration or build_prometheus_integration(provider_name="fake")
    envelope = await integration.invoke(PROM_QUERY, {"query": query})
    return envelope.to_dict()


async def prometheus_targets_payload(integration: PrometheusIntegration | None = None) -> dict:
    integration = integration or build_prometheus_integration(provider_name="fake")
    envelope = await integration.invoke(PROM_TARGETS, {})
    return envelope.to_dict()


async def prometheus_alerts_payload(integration: PrometheusIntegration | None = None) -> dict:
    integration = integration or build_prometheus_integration(provider_name="fake")
    envelope = await integration.invoke(PROM_ALERTS, {})
    return envelope.to_dict()

