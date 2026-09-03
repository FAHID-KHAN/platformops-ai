from __future__ import annotations

from typing import Protocol

from platformops.providers.delivery.models import ArgoCDApplicationSummary, JenkinsBuildSummary


class DeliveryProvider(Protocol):
    async def list_argocd_apps(
        self,
        namespace: str | None = None,
    ) -> list[ArgoCDApplicationSummary]: ...

    async def list_jenkins_builds(
        self,
        job_name: str | None = None,
        limit: int = 10,
    ) -> list[JenkinsBuildSummary]: ...
