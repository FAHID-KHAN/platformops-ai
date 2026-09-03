from __future__ import annotations

from platformops.domain import (
    EvidenceEnvelope,
    IntegrationHealth,
    IntegrationManifest,
    InvocationContext,
    RiskLevel,
    ToolError,
)
from platformops.integrations.capabilities import (
    K8S_GET_NODES,
    K8S_DIAGNOSE_NAMESPACE,
    K8S_GET_ENDPOINTS,
    K8S_GET_POD,
    K8S_GET_POD_LOGS,
    K8S_INVESTIGATE_NAMESPACE,
    K8S_LIST_INGRESSES,
    K8S_LIST_EVENTS,
    K8S_LIST_NAMESPACES,
    K8S_LIST_PODS,
    K8S_LIST_SERVICES,
)
from platformops.policies import KubernetesReadOnlyPolicy, PolicyViolation
from platformops.providers.kubernetes.provider import KubernetesProvider


class KubernetesIntegration:
    def __init__(
        self,
        provider: KubernetesProvider,
        policy: KubernetesReadOnlyPolicy | None = None,
    ) -> None:
        self.provider = provider
        self.policy = policy or KubernetesReadOnlyPolicy()

    @property
    def manifest(self) -> IntegrationManifest:
        return IntegrationManifest(
            id="kubernetes",
            version=1,
            capabilities=(
                K8S_GET_NODES,
                K8S_LIST_NAMESPACES,
                K8S_LIST_PODS,
                K8S_GET_POD,
                K8S_LIST_EVENTS,
                K8S_GET_POD_LOGS,
                K8S_INVESTIGATE_NAMESPACE,
                K8S_DIAGNOSE_NAMESPACE,
                K8S_LIST_SERVICES,
                K8S_GET_ENDPOINTS,
                K8S_LIST_INGRESSES,
            ),
            risk_level=RiskLevel.READ_ONLY,
            evidence_types=(
                "kubernetes-node",
                "kubernetes-namespace",
                "kubernetes-pod",
                "kubernetes-event",
                "kubernetes-log-excerpt",
                "kubernetes-investigation",
                "kubernetes-service",
                "kubernetes-endpoint",
                "kubernetes-ingress",
            ),
            authentication="kubeconfig-or-service-account",
        )

    async def health(self) -> IntegrationHealth:
        try:
            await self.provider.list_namespaces()
        except Exception as exc:  # pragma: no cover - provider/client dependent
            return IntegrationHealth(status="unhealthy", detail=str(exc))
        return IntegrationHealth(status="healthy")

    async def invoke(
        self,
        capability: str,
        arguments: dict,
        context: InvocationContext,
    ) -> EvidenceEnvelope:
        del context
        try:
            if capability == K8S_GET_NODES:
                nodes = await self.provider.list_nodes()
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-node",
                    payload={"nodes": [node.to_dict() for node in nodes]},
                    scope={},
                )

            if capability == K8S_LIST_NAMESPACES:
                namespaces = await self.provider.list_namespaces()
                allowed = self.policy.filter_namespaces([item.name for item in namespaces])
                filtered = [item for item in namespaces if item.name in allowed]
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-namespace",
                    payload={"namespaces": [item.to_dict() for item in filtered]},
                    scope={"allowed_namespaces": sorted(self.policy.allowed_namespaces)},
                )

            if capability == K8S_LIST_PODS:
                namespace = arguments.get("namespace")
                self.policy.ensure_namespace_allowed(namespace)
                pods = await self.provider.list_pods(namespace=namespace)
                if namespace is None and self.policy.allowed_namespaces:
                    pods = [pod for pod in pods if pod.namespace in self.policy.allowed_namespaces]
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-pod",
                    payload={"pods": [pod.to_dict() for pod in pods]},
                    scope={
                        "namespace": namespace,
                        "allowed_namespaces": sorted(self.policy.allowed_namespaces),
                    },
                )

            if capability == K8S_GET_POD:
                namespace = arguments["namespace"]
                name = arguments["name"]
                self.policy.ensure_namespace_allowed(namespace)
                pod = await self.provider.get_pod(namespace=namespace, name=name)
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-pod",
                    payload={"pod": pod.to_dict()},
                    scope={"namespace": namespace, "pod": name},
                )

            if capability == K8S_LIST_EVENTS:
                namespace = arguments["namespace"]
                pod_name = arguments.get("pod_name")
                self.policy.ensure_namespace_allowed(namespace)
                events = await self.provider.list_events(namespace=namespace, pod_name=pod_name)
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-event",
                    payload={"events": [event.to_dict() for event in events]},
                    scope={"namespace": namespace, "pod": pod_name},
                )

            if capability == K8S_GET_POD_LOGS:
                namespace = arguments["namespace"]
                name = arguments["name"]
                container = arguments.get("container")
                previous = bool(arguments.get("previous", False))
                tail_lines = min(max(int(arguments.get("tail_lines", 100)), 1), 500)
                self.policy.ensure_namespace_allowed(namespace)
                logs = await self.provider.get_pod_logs(
                    namespace=namespace,
                    name=name,
                    container=container,
                    tail_lines=tail_lines,
                    previous=previous,
                )
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-log-excerpt",
                    payload={"logs": logs.to_dict()},
                    scope={
                        "namespace": namespace,
                        "pod": name,
                        "container": container,
                        "previous": previous,
                    },
                )

            if capability == K8S_LIST_SERVICES:
                namespace = arguments["namespace"]
                self.policy.ensure_namespace_allowed(namespace)
                services = await self.provider.list_services(namespace=namespace)
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-service",
                    payload={"services": [service.to_dict() for service in services]},
                    scope={"namespace": namespace},
                )

            if capability == K8S_GET_ENDPOINTS:
                namespace = arguments["namespace"]
                service_name = arguments["service_name"]
                self.policy.ensure_namespace_allowed(namespace)
                endpoints = await self.provider.get_endpoints(
                    namespace=namespace,
                    service_name=service_name,
                )
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-endpoint",
                    payload={"endpoints": endpoints.to_dict()},
                    scope={"namespace": namespace, "service": service_name},
                )

            if capability == K8S_LIST_INGRESSES:
                namespace = arguments["namespace"]
                self.policy.ensure_namespace_allowed(namespace)
                ingresses = await self.provider.list_ingresses(namespace=namespace)
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-ingress",
                    payload={"ingresses": [ingress.to_dict() for ingress in ingresses]},
                    scope={"namespace": namespace},
                )

            if capability == K8S_INVESTIGATE_NAMESPACE:
                namespace = arguments["namespace"]
                tail_lines = min(max(int(arguments.get("tail_lines", 50)), 1), 200)
                self.policy.ensure_namespace_allowed(namespace)
                return await self._investigate_namespace(namespace=namespace, tail_lines=tail_lines)

            if capability == K8S_DIAGNOSE_NAMESPACE:
                namespace = arguments["namespace"]
                tail_lines = min(max(int(arguments.get("tail_lines", 80)), 1), 200)
                self.policy.ensure_namespace_allowed(namespace)
                from platformops.diagnostics.kubernetes import diagnose_kubernetes_namespace

                report = await diagnose_kubernetes_namespace(
                    namespace=namespace,
                    tail_lines=tail_lines,
                    integration=self,
                )
                return EvidenceEnvelope(
                    source="kubernetes",
                    capability=capability,
                    evidence_type="kubernetes-diagnosis",
                    payload={"diagnosis": report.to_dict()},
                    scope={"namespace": namespace, "tail_lines": tail_lines},
                )

            return self._error(capability, "unsupported_capability", f"unsupported capability: {capability}")
        except PolicyViolation as exc:
            return self._error(capability, "policy_violation", str(exc))
        except Exception as exc:  # pragma: no cover - provider/client dependent
            return self._error(capability, "provider_error", str(exc), retryable=True)

    def _error(
        self,
        capability: str,
        code: str,
        message: str,
        retryable: bool = False,
    ) -> EvidenceEnvelope:
        return EvidenceEnvelope(
            source="kubernetes",
            capability=capability,
            evidence_type="tool-error",
            payload={},
            errors=(ToolError(code=code, message=message, retryable=retryable),),
        )

    async def _investigate_namespace(self, namespace: str, tail_lines: int) -> EvidenceEnvelope:
        pods = await self.provider.list_pods(namespace=namespace)
        unhealthy_pods = [
            pod
            for pod in pods
            if pod.phase not in {"Running", "Succeeded"} or not self._is_ready(pod.ready)
        ]
        attention_pods = [
            pod
            for pod in pods
            if pod in unhealthy_pods or pod.restarts > 0
        ]
        event_items = await self.provider.list_events(namespace=namespace)
        log_items = []
        for pod in attention_pods[:5]:
            target_containers: list[str | None] = [None]
            try:
                detail = await self.provider.get_pod(namespace=namespace, name=pod.name)
                interesting = [
                    container.name
                    for container in detail.containers
                    if not container.ready or container.restart_count > 0
                ]
                if not interesting and detail.containers:
                    interesting = [detail.containers[0].name]
                if interesting:
                    target_containers = interesting[:3]
            except Exception:
                target_containers = [None]

            for container in target_containers:
                try:
                    log_items.append(
                        (
                            await self.provider.get_pod_logs(
                                namespace=namespace,
                                name=pod.name,
                                container=container,
                                tail_lines=tail_lines,
                            )
                        ).to_dict()
                    )
                except Exception as exc:  # pragma: no cover - provider/client dependent
                    log_items.append(
                        {
                            "namespace": namespace,
                            "pod_name": pod.name,
                            "container": container,
                            "error": str(exc),
                            "tail_lines": tail_lines,
                        }
                    )

        summary = "No pods needing attention detected."
        if unhealthy_pods:
            summary = (
                f"Detected {len(unhealthy_pods)} unhealthy pod(s). "
                "Check events and log excerpts."
            )
        elif attention_pods:
            summary = (
                f"Detected {len(attention_pods)} pod(s) with restarts. "
                "Check events and log excerpts for recent failures."
            )

        return EvidenceEnvelope(
            source="kubernetes",
            capability=K8S_INVESTIGATE_NAMESPACE,
            evidence_type="kubernetes-investigation",
            payload={
                "summary": summary,
                "pods": [pod.to_dict() for pod in pods],
                "unhealthy_pods": [pod.to_dict() for pod in unhealthy_pods],
                "attention_pods": [pod.to_dict() for pod in attention_pods],
                "events": [event.to_dict() for event in event_items],
                "log_excerpts": log_items,
            },
            scope={"namespace": namespace, "tail_lines": tail_lines},
        )

    def _is_ready(self, ready: str) -> bool:
        try:
            ready_count, total_count = ready.split("/", maxsplit=1)
            return int(ready_count) == int(total_count)
        except ValueError:
            return False
