from __future__ import annotations

from platformops.providers.delivery.models import ArgoCDApplicationSummary, JenkinsBuildSummary


class FakeDeliveryProvider:
    async def list_argocd_apps(
        self,
        namespace: str | None = None,
    ) -> list[ArgoCDApplicationSummary]:
        apps = [
            ArgoCDApplicationSummary(
                name="checkout-api",
                namespace="platformops-demo",
                project="default",
                sync_status="Synced",
                health_status="Healthy",
                repo_url="https://github.com/example/checkout-api",
                revision="abc1234",
                target_revision="main",
            ),
            ArgoCDApplicationSummary(
                name="jenkins",
                namespace="jenkins",
                project="platform",
                sync_status="OutOfSync",
                health_status="Degraded",
                repo_url="https://github.com/example/platform",
                revision="def5678",
                target_revision="main",
                conditions=("Deployment rollout has not completed",),
            ),
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
                job_name="platform/jenkins",
                number=42,
                result="FAILURE",
                building=False,
                timestamp="2026-09-04T10:00:00Z",
                duration_ms=120000,
                url="https://jenkins.example/job/platform/job/jenkins/42/",
            ),
            JenkinsBuildSummary(
                job_name="platform/checkout-api",
                number=108,
                result="SUCCESS",
                building=False,
                timestamp="2026-09-04T09:45:00Z",
                duration_ms=90000,
                url="https://jenkins.example/job/platform/job/checkout-api/108/",
            ),
        ]
        if job_name is not None:
            builds = [build for build in builds if build.job_name == job_name]
        return builds[:limit]
