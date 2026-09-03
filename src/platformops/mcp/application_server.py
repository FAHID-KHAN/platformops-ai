from __future__ import annotations

from platformops.diagnostics.application import investigate_app
from platformops.providers.delivery import DeliveryIntegration
from platformops.providers.kubernetes import KubernetesIntegration
from platformops.providers.prometheus.integration import PrometheusIntegration


async def investigate_app_payload(
    app: str,
    namespace: str,
    service_name: str | None = None,
    argocd_app: str | None = None,
    jenkins_job: str | None = None,
    tail_lines: int = 80,
    kubernetes: KubernetesIntegration | None = None,
    prometheus: PrometheusIntegration | None = None,
    delivery: DeliveryIntegration | None = None,
) -> dict:
    if kubernetes is None:
        from platformops.mcp.kubernetes_server import build_kubernetes_integration

        kubernetes = build_kubernetes_integration()
    if prometheus is None:
        from platformops.mcp.prometheus_server import build_prometheus_integration

        prometheus = build_prometheus_integration()
    if delivery is None:
        from platformops.mcp.delivery_server import build_delivery_integration

        delivery = build_delivery_integration()

    report = await investigate_app(
        app=app,
        namespace=namespace,
        service_name=service_name,
        argocd_app=argocd_app,
        jenkins_job=jenkins_job,
        tail_lines=tail_lines,
        kubernetes=kubernetes,
        prometheus=prometheus,
        delivery=delivery,
    )
    return {"app_investigation": report.to_dict(), "markdown": report.to_markdown()}
