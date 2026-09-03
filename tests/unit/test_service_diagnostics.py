from pathlib import Path

from platformops.diagnostics.service import diagnose_service
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import FixtureKubernetesProvider, KubernetesIntegration


def _integration(fixture: str) -> KubernetesIntegration:
    return KubernetesIntegration(
        FixtureKubernetesProvider(Path(f"tests/scenarios/{fixture}")),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo"}),
    )


async def test_service_diagnosis_reports_ready_endpoints():
    report = await diagnose_service(
        name="checkout-api",
        namespace="platformops-demo",
        integration=_integration("healthy_cluster.json"),
    )
    data = report.to_dict()

    assert data["status"] == "info"
    assert any("has ready endpoints" in finding["title"] for finding in data["findings"])
    assert "# Diagnosis:" in report.to_markdown()


async def test_service_diagnosis_reports_missing_endpoints():
    report = await diagnose_service(
        name="checkout-api",
        namespace="platformops-demo",
        integration=_integration("service_no_endpoints.json"),
    )
    data = report.to_dict()

    assert data["status"] == "critical"
    assert any("has no ready endpoints" in finding["title"] for finding in data["findings"])
