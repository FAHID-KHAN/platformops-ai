from __future__ import annotations

import os
from pathlib import Path

from platformops.diagnostics.delivery import diagnose_delivery
from platformops.integrations.capabilities import (
    DELIVERY_LIST_ARGOCD_APPS,
    DELIVERY_LIST_JENKINS_BUILDS,
)
from platformops.providers.delivery import (
    DeliveryApiProvider,
    DeliveryIntegration,
    FakeDeliveryProvider,
    FixtureDeliveryProvider,
)


def build_delivery_integration(
    provider_name: str | None = None,
    fixture: str | None = None,
) -> DeliveryIntegration:
    provider_name = (provider_name or os.getenv("PLATFORMOPS_DELIVERY_PROVIDER", "fake")).lower()
    fixture = fixture or os.getenv("PLATFORMOPS_DELIVERY_FIXTURE")

    if provider_name == "fixture":
        provider = FixtureDeliveryProvider(Path(fixture or "tests/scenarios/delivery_unhealthy.json"))
    elif provider_name == "api":
        provider = DeliveryApiProvider(
            argocd_url=os.getenv("PLATFORMOPS_ARGOCD_URL") or None,
            argocd_token=os.getenv("PLATFORMOPS_ARGOCD_TOKEN") or None,
            jenkins_url=os.getenv("PLATFORMOPS_JENKINS_URL") or None,
            jenkins_user=os.getenv("PLATFORMOPS_JENKINS_USER") or None,
            jenkins_token=os.getenv("PLATFORMOPS_JENKINS_TOKEN") or None,
        )
    else:
        provider = FakeDeliveryProvider()
    return DeliveryIntegration(provider)


async def list_argocd_apps_payload(
    namespace: str | None = None,
    integration: DeliveryIntegration | None = None,
) -> dict:
    integration = integration or build_delivery_integration()
    envelope = await integration.invoke(DELIVERY_LIST_ARGOCD_APPS, {"namespace": namespace})
    return envelope.to_dict()


async def list_jenkins_builds_payload(
    job_name: str | None = None,
    limit: int = 10,
    integration: DeliveryIntegration | None = None,
) -> dict:
    integration = integration or build_delivery_integration()
    envelope = await integration.invoke(
        DELIVERY_LIST_JENKINS_BUILDS,
        {"job_name": job_name, "limit": limit},
    )
    return envelope.to_dict()


async def diagnose_delivery_payload(
    namespace: str | None = None,
    app_name: str | None = None,
    job_name: str | None = None,
    build_limit: int = 10,
    integration: DeliveryIntegration | None = None,
) -> dict:
    integration = integration or build_delivery_integration()
    report = await diagnose_delivery(
        namespace=namespace,
        app_name=app_name,
        job_name=job_name,
        build_limit=build_limit,
        integration=integration,
    )
    return {"diagnosis": report.to_dict(), "markdown": report.to_markdown()}
