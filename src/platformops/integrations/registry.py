from __future__ import annotations

from typing import Protocol

from platformops.domain import EvidenceEnvelope, IntegrationHealth, IntegrationManifest, InvocationContext


class PlatformIntegration(Protocol):
    @property
    def manifest(self) -> IntegrationManifest: ...

    async def health(self) -> IntegrationHealth: ...

    async def invoke(
        self,
        capability: str,
        arguments: dict,
        context: InvocationContext,
    ) -> EvidenceEnvelope: ...


class IntegrationRegistry:
    def __init__(self) -> None:
        self._integrations: dict[str, PlatformIntegration] = {}

    def register(self, integration: PlatformIntegration) -> None:
        self._integrations[integration.manifest.id] = integration

    def get(self, integration_id: str) -> PlatformIntegration:
        try:
            return self._integrations[integration_id]
        except KeyError as exc:
            raise KeyError(f"integration is not registered: {integration_id}") from exc

    def manifests(self) -> list[IntegrationManifest]:
        return [integration.manifest for integration in self._integrations.values()]

