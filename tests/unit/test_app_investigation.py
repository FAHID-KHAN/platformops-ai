from pathlib import Path

from platformops.diagnostics.application import investigate_app
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.delivery import DeliveryIntegration, FixtureDeliveryProvider
from platformops.providers.kubernetes import FixtureKubernetesProvider, KubernetesIntegration


def _kubernetes() -> KubernetesIntegration:
    return KubernetesIntegration(
        FixtureKubernetesProvider(Path("tests/scenarios/multi_namespace_triage.json")),
        KubernetesReadOnlyPolicy(allowed_namespaces={"jenkins"}),
    )


def _delivery() -> DeliveryIntegration:
    return DeliveryIntegration(FixtureDeliveryProvider(Path("tests/scenarios/delivery_unhealthy.json")))


async def test_investigates_app_across_sources():
    report = await investigate_app(
        app="jenkins",
        namespace="jenkins",
        jenkins_job="platform/jenkins",
        kubernetes=_kubernetes(),
        delivery=_delivery(),
    )

    data = report.to_dict()

    assert data["status"] == "critical"
    assert "Delivery evidence is correlated" in data["likely_explanation"]
    assert any(item["source"] == "kubernetes" for item in data["evidence_chain"])
    assert any(item["source"] == "delivery" for item in data["evidence_chain"])
    assert data["evidence_chain"][0]["severity"] == "critical"


async def test_app_investigation_markdown_has_evidence_chain():
    report = await investigate_app(
        app="jenkins",
        namespace="jenkins",
        jenkins_job="platform/jenkins",
        kubernetes=_kubernetes(),
        delivery=_delivery(),
    )

    markdown = report.to_markdown()

    assert "# App Investigation: jenkins" in markdown
    assert "## Evidence Chain" in markdown
    assert "ArgoCD app jenkins is Degraded" in markdown
