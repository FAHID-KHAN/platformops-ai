from pathlib import Path

from platformops.diagnostics.delivery import diagnose_delivery
from platformops.providers.delivery import DeliveryIntegration, FixtureDeliveryProvider


def _integration(fixture: str) -> DeliveryIntegration:
    return DeliveryIntegration(FixtureDeliveryProvider(Path(f"tests/scenarios/{fixture}")))


async def test_diagnoses_unhealthy_delivery_sources():
    report = await diagnose_delivery(
        namespace="jenkins",
        job_name="platform/jenkins",
        integration=_integration("delivery_unhealthy.json"),
    )

    data = report.to_dict()

    assert data["status"] == "critical"
    assert any("ArgoCD app jenkins is Degraded" in item["title"] for item in data["findings"])
    assert any("ended with FAILURE" in item["title"] for item in data["findings"])
    assert any("ArgoCD application resources" in item["action"] for item in data["recommendations"])


async def test_diagnoses_healthy_delivery_sources():
    report = await diagnose_delivery(
        namespace="platformops-demo",
        app_name="checkout-api",
        job_name="platform/checkout-api",
        integration=_integration("delivery_healthy.json"),
    )

    data = report.to_dict()

    assert data["status"] == "healthy"
    assert any("appears healthy" in item["title"] for item in data["findings"])
