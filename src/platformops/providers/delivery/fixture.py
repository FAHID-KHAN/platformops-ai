from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformops.providers.delivery.models import ArgoCDApplicationSummary, JenkinsBuildSummary


class FixtureDeliveryProvider:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def _data(self) -> dict[str, Any]:
        return json.loads(self.fixture_path.read_text())

    async def list_argocd_apps(
        self,
        namespace: str | None = None,
    ) -> list[ArgoCDApplicationSummary]:
        apps = [
            ArgoCDApplicationSummary(
                name=app["name"],
                namespace=app.get("namespace"),
                project=app.get("project"),
                sync_status=app["sync_status"],
                health_status=app["health_status"],
                repo_url=app.get("repo_url"),
                revision=app.get("revision"),
                target_revision=app.get("target_revision"),
                conditions=tuple(app.get("conditions", [])),
            )
            for app in self._data().get("argocd_apps", [])
        ]
        if namespace is None:
            return apps
        return [app for app in apps if app.namespace == namespace]

    async def list_jenkins_builds(
        self,
        job_name: str | None = None,
        limit: int = 10,
    ) -> list[JenkinsBuildSummary]:
        builds = [
            JenkinsBuildSummary(
                job_name=build["job_name"],
                number=build["number"],
                result=build.get("result"),
                building=build["building"],
                timestamp=build.get("timestamp"),
                duration_ms=build.get("duration_ms"),
                url=build.get("url"),
            )
            for build in self._data().get("jenkins_builds", [])
        ]
        if job_name is not None:
            builds = [build for build in builds if build.job_name == job_name]
        return builds[:limit]
