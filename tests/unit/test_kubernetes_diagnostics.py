from pathlib import Path

from platformops.diagnostics import diagnose_kubernetes_namespace
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import FixtureKubernetesProvider, KubernetesIntegration


def _integration(fixture: str) -> KubernetesIntegration:
    return KubernetesIntegration(
        FixtureKubernetesProvider(Path(f"tests/scenarios/{fixture}")),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo"}),
    )


async def test_diagnoses_crashloopbackoff():
    report = await diagnose_kubernetes_namespace(
        namespace="platformops-demo",
        integration=_integration("crashloopbackoff.json"),
    )

    data = report.to_dict()

    assert data["status"] == "critical"
    assert "Critical Kubernetes issue" in data["summary"]
    assert any("crash looping" in finding["title"] for finding in data["findings"])
    assert any("previous container logs" in item["action"] for item in data["recommendations"])


async def test_diagnoses_imagepullbackoff():
    report = await diagnose_kubernetes_namespace(
        namespace="platformops-demo",
        integration=_integration("imagepullbackoff.json"),
    )

    data = report.to_dict()

    assert data["status"] == "critical"
    assert any("cannot pull its image" in finding["title"] for finding in data["findings"])


async def test_diagnoses_unschedulable_pod():
    report = await diagnose_kubernetes_namespace(
        namespace="platformops-demo",
        integration=_integration("unschedulable.json"),
    )

    data = report.to_dict()

    assert data["status"] == "critical"
    assert any("not scheduled" in finding["title"] for finding in data["findings"])


async def test_diagnoses_empty_namespace():
    report = await diagnose_kubernetes_namespace(
        namespace="platformops-demo",
        integration=_integration("empty_namespace.json"),
    )

    data = report.to_dict()

    assert data["status"] == "warning"
    assert data["findings"][0]["title"] == "No pods found"

