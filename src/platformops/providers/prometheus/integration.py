from __future__ import annotations

from platformops.domain import EvidenceEnvelope, ToolError
from platformops.providers.prometheus.provider import PrometheusProvider

PROM_QUERY = "prometheus.query"
PROM_TARGETS = "prometheus.targets"
PROM_ALERTS = "prometheus.alerts"


class PrometheusIntegration:
    def __init__(self, provider: PrometheusProvider) -> None:
        self.provider = provider

    async def invoke(self, capability: str, arguments: dict) -> EvidenceEnvelope:
        try:
            if capability == PROM_QUERY:
                query = arguments["query"]
                result = await self.provider.query(query)
                return EvidenceEnvelope(
                    source="prometheus",
                    capability=capability,
                    evidence_type="prometheus-query-result",
                    payload={"query_result": result.to_dict()},
                    scope={"query": query},
                )
            if capability == PROM_TARGETS:
                targets = await self.provider.targets()
                return EvidenceEnvelope(
                    source="prometheus",
                    capability=capability,
                    evidence_type="prometheus-target",
                    payload={"targets": [target.to_dict() for target in targets]},
                )
            if capability == PROM_ALERTS:
                alerts = await self.provider.alerts()
                return EvidenceEnvelope(
                    source="prometheus",
                    capability=capability,
                    evidence_type="prometheus-alert",
                    payload={"alerts": [alert.to_dict() for alert in alerts]},
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
            source="prometheus",
            capability=capability,
            evidence_type="tool-error",
            payload={},
            errors=(ToolError(code=code, message=message, retryable=retryable),),
        )

