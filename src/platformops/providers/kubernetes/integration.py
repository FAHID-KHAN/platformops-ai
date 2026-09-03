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
    K8S_LIST_NAMESPACES,
    K8S_LIST_PODS,
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
            capabilities=(K8S_GET_NODES, K8S_LIST_NAMESPACES, K8S_LIST_PODS),
            risk_level=RiskLevel.READ_ONLY,
            evidence_types=("kubernetes-node", "kubernetes-namespace", "kubernetes-pod"),
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

