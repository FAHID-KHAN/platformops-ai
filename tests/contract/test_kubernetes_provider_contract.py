from pathlib import Path

from platformops.providers.kubernetes import FixtureKubernetesProvider


async def test_fixture_provider_matches_kubernetes_provider_contract():
    provider = FixtureKubernetesProvider(Path("tests/scenarios/healthy_cluster.json"))

    nodes = await provider.list_nodes()
    namespaces = await provider.list_namespaces()
    pods = await provider.list_pods(namespace="platformops-demo")
    pod = await provider.get_pod(
        namespace="platformops-demo",
        name="checkout-api-7df45b9b9c-2kq4h",
    )
    events = await provider.list_events(
        namespace="platformops-demo",
        pod_name="checkout-api-7df45b9b9c-2kq4h",
    )
    logs = await provider.get_pod_logs(
        namespace="platformops-demo",
        name="checkout-api-7df45b9b9c-2kq4h",
        tail_lines=1,
    )
    services = await provider.list_services(namespace="platformops-demo")
    endpoints = await provider.get_endpoints(
        namespace="platformops-demo",
        service_name="checkout-api",
    )
    ingresses = await provider.list_ingresses(namespace="platformops-demo")

    assert nodes[0].name == "fixture-control-plane"
    assert namespaces[0].name == "platformops-demo"
    assert pods[0].ready == "1/1"
    assert pod.containers[0].state == "running"
    assert events[0].reason == "Started"
    assert logs.text == "health ok"
    assert services[0].name == "checkout-api"
    assert endpoints.addresses[0].target_name == "checkout-api-7df45b9b9c-2kq4h"
    assert ingresses[0].rules[0].service_name == "checkout-api"
