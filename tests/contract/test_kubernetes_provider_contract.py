from pathlib import Path

from platformops.providers.kubernetes import FixtureKubernetesProvider


async def test_fixture_provider_matches_kubernetes_provider_contract():
    provider = FixtureKubernetesProvider(Path("tests/scenarios/healthy_cluster.json"))

    nodes = await provider.list_nodes()
    namespaces = await provider.list_namespaces()
    pods = await provider.list_pods(namespace="platformops-demo")

    assert nodes[0].name == "fixture-control-plane"
    assert namespaces[0].name == "platformops-demo"
    assert pods[0].ready == "1/1"

