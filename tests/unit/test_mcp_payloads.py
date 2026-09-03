from platformops.mcp.kubernetes_server import (
    diagnose_namespace_payload,
    get_nodes_payload,
    list_pods_payload,
)
from platformops.mcp.prometheus_server import prometheus_alerts_payload, prometheus_targets_payload
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import FakeKubernetesProvider, KubernetesIntegration


async def test_mcp_payload_helper_returns_serializable_dict():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    payload = await get_nodes_payload(integration)

    assert payload["source"] == "kubernetes"
    assert payload["payload"]["nodes"]


async def test_mcp_payload_helper_accepts_namespace():
    integration = KubernetesIntegration(
        FakeKubernetesProvider(),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo"}),
    )

    payload = await list_pods_payload(namespace="platformops-demo", integration=integration)

    assert payload["payload"]["pods"][0]["namespace"] == "platformops-demo"


async def test_mcp_diagnose_payload_helper_returns_report():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    payload = await diagnose_namespace_payload(namespace="platformops-demo", integration=integration)

    assert payload["status"] == "healthy"
    assert payload["findings"]


async def test_mcp_prometheus_payload_helpers_return_evidence():
    targets = await prometheus_targets_payload()
    alerts = await prometheus_alerts_payload()

    assert targets["source"] == "prometheus"
    assert "targets" in targets["payload"]
    assert alerts["source"] == "prometheus"
