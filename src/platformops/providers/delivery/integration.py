from __future__ import annotations

from platformops.domain import EvidenceEnvelope, ToolError
from platformops.integrations.capabilities import (
    DELIVERY_LIST_ARGOCD_APPS,
    DELIVERY_LIST_JENKINS_BUILDS,
)
from platformops.providers.delivery.provider import DeliveryProvider


class DeliveryIntegration:
    def __init__(self, provider: DeliveryProvider) -> None:
        self.provider = provider

    async def invoke(self, capability: str, arguments: dict) -> EvidenceEnvelope:
        try:
            if capability == DELIVERY_LIST_ARGOCD_APPS:
                namespace = arguments.get("namespace")
                apps = await self.provider.list_argocd_apps(namespace=namespace)
                return EvidenceEnvelope(
                    source="delivery",
                    capability=capability,
                    evidence_type="argocd-application",
                    payload={"argocd_apps": [app.to_dict() for app in apps]},
                    scope={"namespace": namespace},
                )
            if capability == DELIVERY_LIST_JENKINS_BUILDS:
                job_name = arguments.get("job_name")
                limit = min(max(int(arguments.get("limit", 10)), 1), 50)
                builds = await self.provider.list_jenkins_builds(
                    job_name=job_name,
                    limit=limit,
                )
                return EvidenceEnvelope(
                    source="delivery",
                    capability=capability,
                    evidence_type="jenkins-build",
                    payload={"jenkins_builds": [build.to_dict() for build in builds]},
                    scope={"job_name": job_name, "limit": limit},
                )
            return self._error(capability, "unsupported_capability", f"unsupported capability: {capability}")
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
            source="delivery",
            capability=capability,
            evidence_type="tool-error",
            payload={},
            errors=(ToolError(code=code, message=message, retryable=retryable),),
        )
