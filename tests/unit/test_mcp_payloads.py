from platformops.mcp.kubernetes_server import get_nodes_payload, list_pods_payload
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

