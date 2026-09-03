from platformops.integrations.capabilities import (
    K8S_GET_NODES,
    K8S_GET_POD_LOGS,
    K8S_INVESTIGATE_NAMESPACE,
    K8S_LIST_NAMESPACES,
    K8S_LIST_PODS,
)
from platformops.domain import InvocationContext
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.kubernetes import FakeKubernetesProvider, KubernetesIntegration
from platformops.providers.kubernetes.models import (
    ContainerSummary,
    EventSummary,
    NamespaceSummary,
    NodeSummary,
    PodDetail,
    PodLogExcerpt,
    PodSummary,
)


class RestartedMultiContainerProvider:
    async def list_nodes(self):
        return [NodeSummary(name="node-1", ready=True)]

    async def list_namespaces(self):
        return [NamespaceSummary(name="jenkins", status="Active")]

    async def list_pods(self, namespace=None):
        return [
            PodSummary(
                name="jenkins-0",
                namespace="jenkins",
                phase="Running",
                ready="2/2",
                restarts=4,
                node_name="node-1",
            )
        ]

    async def get_pod(self, namespace, name):
        return PodDetail(
            name=name,
            namespace=namespace,
            phase="Running",
            ready="2/2",
            restarts=4,
            node_name="node-1",
            service_account="jenkins",
            containers=(
                ContainerSummary(
                    name="jenkins",
                    ready=True,
                    restart_count=4,
                    state="running",
                ),
                ContainerSummary(
                    name="config-reload",
                    ready=True,
                    restart_count=0,
                    state="running",
                ),
            ),
            conditions={"Ready": "True", "PodScheduled": "True"},
        )

    async def list_events(self, namespace, pod_name=None):
        return [
            EventSummary(
                namespace=namespace,
                involved_object_name="jenkins-0",
                involved_object_kind="Pod",
                type="Warning",
                reason="BackOff",
                message="Restarted container jenkins",
                count=4,
            )
        ]

    async def get_pod_logs(self, namespace, name, container=None, tail_lines=100):
        if container is None:
            raise ValueError("container name must be specified")
        return PodLogExcerpt(
            namespace=namespace,
            pod_name=name,
            container=container,
            tail_lines=tail_lines,
            text="jenkins recovered",
            truncated=False,
        )


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


async def test_get_pod_logs_bounds_tail_lines():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    envelope = await integration.invoke(
        K8S_GET_POD_LOGS,
        {
            "namespace": "platformops-demo",
            "name": "checkout-api-7df45b9b9c-2kq4h",
            "tail_lines": 999,
        },
        InvocationContext(),
    )

    assert envelope.to_dict()["payload"]["logs"]["tail_lines"] == 500


async def test_investigate_namespace_returns_summary():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    envelope = await integration.invoke(
        K8S_INVESTIGATE_NAMESPACE,
        {"namespace": "platformops-demo"},
        InvocationContext(),
    )
    data = envelope.to_dict()

    assert data["evidence_type"] == "kubernetes-investigation"
    assert "summary" in data["payload"]


async def test_investigate_ready_restarted_multicontainer_pod_uses_container_logs():
    integration = KubernetesIntegration(RestartedMultiContainerProvider())

    envelope = await integration.invoke(
        K8S_INVESTIGATE_NAMESPACE,
        {"namespace": "jenkins"},
        InvocationContext(),
    )
    data = envelope.to_dict()

    assert data["payload"]["unhealthy_pods"] == []
    assert data["payload"]["attention_pods"][0]["name"] == "jenkins-0"
    assert data["payload"]["log_excerpts"][0]["container"] == "jenkins"
    assert data["payload"]["log_excerpts"][0]["text"] == "jenkins recovered"
