from platformops.integrations.capabilities import K8S_GET_NODES, K8S_LIST_NAMESPACES, K8S_LIST_PODS
from platformops.domain import InvocationContext
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import FakeKubernetesProvider, KubernetesIntegration


async def test_get_nodes_returns_evidence_envelope():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    envelope = await integration.invoke(K8S_GET_NODES, {}, InvocationContext())
    data = envelope.to_dict()

    assert data["source"] == "kubernetes"
    assert data["capability"] == K8S_GET_NODES
    assert data["evidence_type"] == "kubernetes-node"
    assert data["payload"]["nodes"][0]["name"] == "platformops-control-plane"
    assert data["errors"] == []


async def test_list_namespaces_filters_to_allowlist():
    integration = KubernetesIntegration(
        FakeKubernetesProvider(),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo"}),
    )

    envelope = await integration.invoke(K8S_LIST_NAMESPACES, {}, InvocationContext())
    namespaces = envelope.to_dict()["payload"]["namespaces"]

    assert namespaces == [{"name": "platformops-demo", "status": "Active"}]


async def test_list_pods_rejects_disallowed_namespace():
    integration = KubernetesIntegration(
        FakeKubernetesProvider(),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo"}),
    )

    envelope = await integration.invoke(
        K8S_LIST_PODS,
        {"namespace": "kube-system"},
        InvocationContext(),
    )
    data = envelope.to_dict()

    assert data["evidence_type"] == "tool-error"
    assert data["errors"][0]["code"] == "policy_violation"


async def test_list_pods_without_namespace_filters_to_allowlist():
    integration = KubernetesIntegration(
        FakeKubernetesProvider(),
        KubernetesReadOnlyPolicy(allowed_namespaces={"platformops-demo"}),
    )

    envelope = await integration.invoke(K8S_LIST_PODS, {}, InvocationContext())
    pods = envelope.to_dict()["payload"]["pods"]

    assert len(pods) == 1
    assert pods[0]["namespace"] == "platformops-demo"

