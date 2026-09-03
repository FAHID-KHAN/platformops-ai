from platformops.mcp.delivery_server import (
    diagnose_delivery_payload,
    list_argocd_apps_payload,
    list_jenkins_builds_payload,
)
from platformops.mcp.application_server import investigate_app_payload
from platformops.mcp.kubernetes_server import (
    diagnose_namespace_payload,
    diagnose_service_payload,
    get_endpoints_payload,
    get_nodes_payload,
    list_pods_payload,
    list_services_payload,
    scan_cluster_payload,
)
from platformops.mcp.prometheus_server import prometheus_alerts_payload, prometheus_targets_payload
from platformops.policies import KubernetesReadOnlyPolicy
from platformops.providers.delivery import DeliveryIntegration, FakeDeliveryProvider
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


async def test_mcp_service_payload_helpers_return_evidence():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    services = await list_services_payload(namespace="platformops-demo", integration=integration)
    endpoints = await get_endpoints_payload(
        namespace="platformops-demo",
        service_name="checkout-api",
        integration=integration,
    )
    diagnosis = await diagnose_service_payload(
        name="checkout-api",
        namespace="platformops-demo",
        integration=integration,
    )

    assert services["payload"]["services"][0]["name"] == "checkout-api"
    assert endpoints["payload"]["endpoints"]["addresses"][0]["ready"] is True
    assert diagnosis["findings"]


async def test_mcp_cluster_scan_payload_helper_returns_ranked_report():
    integration = KubernetesIntegration(FakeKubernetesProvider())

    payload = await scan_cluster_payload(
        namespaces=["platformops-demo", "kube-system"],
        integration=integration,
    )

    report = payload["cluster_scan"]

    assert report["status"] == "healthy"
    assert report["namespaces"]
    assert "markdown" in payload


async def test_mcp_delivery_payload_helpers_return_evidence():
    integration = DeliveryIntegration(FakeDeliveryProvider())

    apps = await list_argocd_apps_payload(namespace="jenkins", integration=integration)
    builds = await list_jenkins_builds_payload(job_name="platform/jenkins", integration=integration)
    diagnosis = await diagnose_delivery_payload(
        namespace="jenkins",
        job_name="platform/jenkins",
        integration=integration,
    )

    assert apps["payload"]["argocd_apps"][0]["name"] == "jenkins"
    assert builds["payload"]["jenkins_builds"][0]["result"] == "FAILURE"
    assert diagnosis["diagnosis"]["status"] == "critical"


async def test_mcp_app_investigation_payload_returns_narrative():
    integration = KubernetesIntegration(FakeKubernetesProvider())
    delivery = DeliveryIntegration(FakeDeliveryProvider())

    payload = await investigate_app_payload(
        app="jenkins",
        namespace="jenkins",
        jenkins_job="platform/jenkins",
        kubernetes=integration,
        delivery=delivery,
    )

    report = payload["app_investigation"]

    assert report["app"] == "jenkins"
    assert report["status"] == "critical"
    assert report["evidence_chain"]
    assert "markdown" in payload
