from __future__ import annotations

import base64
import json
from typing import Any
from urllib import parse, request

from platformops.providers.delivery.models import ArgoCDApplicationSummary, JenkinsBuildSummary


class DeliveryApiProvider:
    def __init__(
        self,
        argocd_url: str | None = None,
        argocd_token: str | None = None,
        jenkins_url: str | None = None,
        jenkins_user: str | None = None,
        jenkins_token: str | None = None,
        timeout_seconds: int = 10,
    ) -> None:
        self.argocd_url = argocd_url.rstrip("/") if argocd_url else None
        self.argocd_token = argocd_token
        self.jenkins_url = jenkins_url.rstrip("/") if jenkins_url else None
        self.jenkins_user = jenkins_user
        self.jenkins_token = jenkins_token
        self.timeout_seconds = timeout_seconds

    async def list_argocd_apps(
        self,
        namespace: str | None = None,
    ) -> list[ArgoCDApplicationSummary]:
        if not self.argocd_url:
            return []
        data = self._json_get(
            f"{self.argocd_url}/api/v1/applications",
            bearer_token=self.argocd_token,
        )
        apps = []
        for item in data.get("items", []):
            destination = item.get("spec", {}).get("destination", {})
            status = item.get("status", {})
            sync = status.get("sync", {})
            health = status.get("health", {})
            source = item.get("spec", {}).get("source", {})
            metadata = item.get("metadata", {})
            app = ArgoCDApplicationSummary(
                name=metadata.get("name", ""),
                namespace=destination.get("namespace"),
                project=item.get("spec", {}).get("project"),
                sync_status=sync.get("status", "Unknown"),
                health_status=health.get("status", "Unknown"),
                repo_url=source.get("repoURL"),
                revision=sync.get("revision"),
                target_revision=source.get("targetRevision"),
                conditions=tuple(
                    condition.get("message", "")
                    for condition in status.get("conditions", [])
                    if condition.get("message")
                ),
            )
            apps.append(app)
        if namespace is None:
            return apps
        return [app for app in apps if app.namespace == namespace]

    async def list_jenkins_builds(
        self,
        job_name: str | None = None,
        limit: int = 10,
    ) -> list[JenkinsBuildSummary]:
        if not self.jenkins_url:
            return []
        api_path = "api/json"
        if job_name:
            encoded = "/job/".join(parse.quote(part) for part in job_name.split("/"))
            api_path = f"job/{encoded}/api/json"
        url = (
            f"{self.jenkins_url}/{api_path}"
            "?tree=builds[number,result,building,timestamp,duration,url]"
        )
        data = self._json_get(url, basic_auth=self._jenkins_auth())
        builds = data.get("builds", [])
        if not builds and {"number", "result", "building"}.issubset(data):
            builds = [data]
        return [
            JenkinsBuildSummary(
                job_name=job_name or data.get("fullName") or data.get("name") or "jenkins",
                number=build["number"],
                result=build.get("result"),
                building=build["building"],
                timestamp=str(build["timestamp"]) if build.get("timestamp") is not None else None,
                duration_ms=build.get("duration"),
                url=build.get("url"),
            )
            for build in builds[:limit]
        ]

    def _jenkins_auth(self) -> str | None:
        if not self.jenkins_user or not self.jenkins_token:
            return None
        token = f"{self.jenkins_user}:{self.jenkins_token}".encode()
        return base64.b64encode(token).decode()

    def _json_get(
        self,
        url: str,
        bearer_token: str | None = None,
        basic_auth: str | None = None,
    ) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        if basic_auth:
            headers["Authorization"] = f"Basic {basic_auth}"
        req = request.Request(url, headers=headers)
        with request.urlopen(req, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode())
