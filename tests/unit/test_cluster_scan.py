from pathlib import Path

from platformops.diagnostics.cluster import scan_cluster
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import FixtureKubernetesProvider, KubernetesIntegration


def _integration() -> KubernetesIntegration:
    return KubernetesIntegration(
        FixtureKubernetesProvider(Path("tests/scenarios/multi_namespace_triage.json")),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo", "jenkins"}),
    )


async def test_cluster_scan_ranks_findings_across_namespaces():
    report = await scan_cluster(
        namespaces=["platformops-demo", "jenkins"],
        integration=_integration(),
    )

    data = report.to_dict()

    assert data["status"] == "critical"
    assert "Scanned 2 namespace" in data["summary"]
    assert data["findings"][0]["namespace"] == "jenkins"
    assert data["findings"][0]["severity"] == "critical"
    assert "crash looping" in data["findings"][0]["title"]
    assert any(namespace["namespace"] == "platformops-demo" for namespace in data["namespaces"])


async def test_cluster_scan_requires_namespaces():
    report = await scan_cluster(namespaces=[], integration=_integration())

    data = report.to_dict()

    assert data["status"] == "unknown"
    assert "requires at least one namespace" in data["summary"]
    assert data["findings"] == []


async def test_cluster_scan_markdown_contains_ranked_findings():
    report = await scan_cluster(
        namespaces=["platformops-demo", "jenkins"],
        integration=_integration(),
    )

    markdown = report.to_markdown()

    assert "# Cluster Scan: critical" in markdown
    assert "## Ranked Findings" in markdown
    assert "`jenkins` - jenkins-0 is crash looping" in markdown
