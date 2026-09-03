<div align="center">

# PlatformOps AI

**Read-only AI operations tooling for Kubernetes, Prometheus, ArgoCD, Jenkins, and MCP.**

[![PyPI](https://img.shields.io/pypi/v/platformops-ai?label=pypi)](https://pypi.org/project/platformops-ai/)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Kubernetes](https://img.shields.io/badge/kubernetes-read--only-326ce5)
![Prometheus](https://img.shields.io/badge/prometheus-correlation-e6522c)
![Delivery](https://img.shields.io/badge/delivery-ArgoCD%20%2B%20Jenkins-1f883d)
![MCP](https://img.shields.io/badge/MCP-tools-6f42c1)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)

[Quick Start](#quick-start) . [CLI](#cli-reference) . [MCP](#mcp-server) . [Diagnosis](#what-it-can-diagnose) . [Architecture](docs/architecture/current-setup.md) . [Runbooks](docs/README.md) . [Roadmap](docs/roadmap.md) . [Contributing](CONTRIBUTING.md) . [Security](SECURITY.md)

<table>
  <tr>
    <td><strong>Install</strong></td>
    <td><code>pip install platformops-ai</code></td>
  </tr>
</table>

PlatformOps AI collects structured platform evidence from official APIs, applies deterministic diagnosis rules, and exposes the same safe investigation workflows through a CLI and an MCP server.

</div>

## Why PlatformOps AI

PlatformOps AI helps operators investigate platform workloads without giving an AI model unrestricted infrastructure access. It can inspect namespaces, pods, events, logs, Services, Endpoints, Ingresses, Prometheus signals, ArgoCD applications, and Jenkins builds, then return operator-readable reports with evidence and limitations.

The current release focuses on read-only Kubernetes, Prometheus, and delivery investigation. The architecture is designed to grow into source control, controlled orchestration, and approval-gated remediation.

Jenkins appears in examples because it is a familiar platform workload, but PlatformOps AI is not Jenkins-specific. It can inspect any Kubernetes namespace or service that your kubeconfig can read and that you include in the namespace allowlist.

For the current system design, see the [architecture diagram](docs/architecture/current-setup.md).

## Install

```bash
pip install platformops-ai
```

Requirements:

- Python 3.11+
- Kubernetes access through kubeconfig or an in-cluster service account

Confirm your Kubernetes context first:

```bash
kubectl config current-context
kubectl get nodes
```

## Quick Start

List cluster nodes:

```bash
platformops k8s nodes
```

Scan multiple allowed namespaces and rank what needs attention:

```bash
platformops scan cluster --allowed-namespaces argocd,jenkins,monitoring
```

Investigate a namespace with pod status, events, and bounded log excerpts:

```bash
platformops k8s investigate --namespace jenkins --allowed-namespaces jenkins
```

Generate a deterministic diagnosis report:

```bash
platformops diagnose k8s --namespace jenkins --allowed-namespaces jenkins
```

Diagnose a service path:

```bash
platformops diagnose service jenkins --namespace jenkins --allowed-namespaces jenkins
```

Use the same commands for any namespace or service:

```bash
platformops diagnose k8s --namespace argocd --allowed-namespaces argocd
platformops diagnose k8s --namespace monitoring --allowed-namespaces monitoring
platformops diagnose service argocd-server --namespace argocd --allowed-namespaces argocd
```

Correlate Kubernetes diagnosis with Prometheus:

```bash
platformops diagnose k8s \
  --namespace jenkins \
  --allowed-namespaces jenkins \
  --prometheus-url http://prometheus.monitoring.svc:9090
```

Check delivery health from ArgoCD and Jenkins:

```bash
platformops delivery argocd apps --namespace jenkins
platformops delivery jenkins builds --job platform/jenkins
platformops diagnose delivery --namespace jenkins --job platform/jenkins
```

Investigate one app across Kubernetes, service-path, Prometheus, ArgoCD, and Jenkins:

```bash
platformops investigate app jenkins \
  --namespace jenkins \
  --job platform/jenkins
```

Use JSON output when you want machine-readable evidence:

```bash
platformops --output json diagnose k8s --namespace jenkins --allowed-namespaces jenkins
```

Use markdown output for incident notes:

```bash
platformops --output markdown diagnose service jenkins --namespace jenkins --allowed-namespaces jenkins
```

## What It Can Diagnose

`v0.6.1` includes deterministic Kubernetes, service-path, cluster triage, Prometheus correlation, delivery, and app investigation rules for:

- CrashLoopBackOff-style restarts
- ImagePullBackOff and image pull failures
- Pending or unschedulable pods
- readiness failures
- restarted but currently ready pods
- empty namespaces
- ranked findings across allowed namespaces
- policy and provider errors
- Prometheus target-down correlation
- Prometheus firing-alert correlation
- Services with missing ready endpoints
- Ingress routes attached to a service
- ArgoCD degraded, missing, or out-of-sync applications
- failed, unstable, aborted, or running Jenkins builds
- cross-source app evidence chains and likely explanations

Example output:

```text
Status: warning
Namespace 'jenkins' needs attention.

Findings
- [warning] jenkins-0 restarted but is currently ready
  jenkins-0 is currently ready (2/2) but has 4 restart(s).

Recommended next actions
- Compare restart timestamps with node restarts, upgrades, or deploys
- Inspect previous logs if the restart is recent or recurring
```

## CLI Reference

Kubernetes inventory:

```bash
platformops k8s nodes
platformops k8s namespaces
platformops k8s pods --namespace default
```

Kubernetes evidence:

```bash
platformops k8s pod POD_NAME --namespace default
platformops k8s events --namespace default
platformops k8s events --namespace default --pod POD_NAME
platformops k8s logs POD_NAME --namespace default --tail-lines 100
platformops k8s logs POD_NAME --namespace default --previous
platformops k8s services --namespace default
platformops k8s endpoints SERVICE_NAME --namespace default
platformops k8s ingresses --namespace default
```

Kubernetes investigation and diagnosis:

```bash
platformops k8s investigate --namespace default --allowed-namespaces default
platformops diagnose k8s --namespace default --allowed-namespaces default
platformops diagnose service SERVICE_NAME --namespace default --allowed-namespaces default
platformops scan cluster --allowed-namespaces default,jenkins,monitoring
```

Prometheus evidence:

```bash
platformops prometheus --prometheus-url http://localhost:9090 query up
platformops prometheus --prometheus-url http://localhost:9090 targets
platformops prometheus --prometheus-url http://localhost:9090 alerts
```

Delivery evidence:

```bash
platformops delivery argocd apps
platformops delivery argocd apps --namespace jenkins
platformops delivery jenkins builds
platformops delivery jenkins builds --job platform/jenkins --limit 5
platformops diagnose delivery --namespace jenkins --job platform/jenkins
platformops investigate app jenkins --namespace jenkins --job platform/jenkins
```

Connection options:

```bash
platformops k8s --context my-context nodes
platformops k8s --provider fake nodes
platformops k8s --provider fixture --fixture tests/scenarios/crashloopbackoff.json investigate --namespace platformops-demo
```

Safety option:

```bash
--allowed-namespaces default,jenkins,monitoring
```

When set, PlatformOps only returns namespace-scoped evidence from the allowed namespaces.

## Verify Your Cluster

Start by listing namespaces:

```bash
platformops k8s namespaces
```

Then inspect the namespaces that matter in your environment:

```bash
platformops diagnose k8s --namespace argocd --allowed-namespaces argocd
platformops diagnose k8s --namespace jenkins --allowed-namespaces jenkins
platformops diagnose k8s --namespace monitoring --allowed-namespaces monitoring
```

For service-path checks, list services first:

```bash
platformops k8s services --namespace argocd --allowed-namespaces argocd
```

Then diagnose a specific service:

```bash
platformops diagnose service argocd-server --namespace argocd --allowed-namespaces argocd
```

Cluster scans inspect multiple allowed namespaces and rank findings across that selected scope. Single namespace and single service commands are still useful when you already know where to look.

## MCP Server

PlatformOps also ships an MCP server:

```bash
platformops-mcp-k8s
```

The MCP server is for AI applications that support the Model Context Protocol. PlatformOps provides the tools; your MCP host provides the chat UI, model, and tool-calling loop.

```text
User
  -> MCP host and selected LLM
  -> PlatformOps MCP server
  -> Kubernetes, Prometheus, ArgoCD, and Jenkins APIs
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "platformops-kubernetes": {
      "command": "platformops-mcp-k8s",
      "env": {
        "PLATFORMOPS_K8S_PROVIDER": "api",
        "PLATFORMOPS_K8S_ALLOWED_NAMESPACES": "default,jenkins"
      }
    }
  }
}
```

Use fake mode when you want to test tool discovery without a cluster:

```json
{
  "mcpServers": {
    "platformops-kubernetes": {
      "command": "platformops-mcp-k8s",
      "env": {
        "PLATFORMOPS_K8S_PROVIDER": "fake",
        "PLATFORMOPS_PROMETHEUS_PROVIDER": "fake",
        "PLATFORMOPS_DELIVERY_PROVIDER": "fake"
      }
    }
  }
}
```

Use API mode for a real cluster. The MCP server uses the kubeconfig or service account available to the process:

```json
{
  "mcpServers": {
    "platformops-kubernetes": {
      "command": "platformops-mcp-k8s",
      "env": {
        "PLATFORMOPS_K8S_PROVIDER": "api",
        "PLATFORMOPS_K8S_ALLOWED_NAMESPACES": "argocd,jenkins,monitoring",
        "PLATFORMOPS_PROMETHEUS_URL": "http://localhost:9090",
        "PLATFORMOPS_DELIVERY_PROVIDER": "api",
        "PLATFORMOPS_ARGOCD_URL": "https://argocd.example.com",
        "PLATFORMOPS_ARGOCD_TOKEN": "...",
        "PLATFORMOPS_JENKINS_URL": "https://jenkins.example.com",
        "PLATFORMOPS_JENKINS_USER": "...",
        "PLATFORMOPS_JENKINS_TOKEN": "..."
      }
    }
  }
}
```

Example questions to ask your MCP host:

```text
What pods are unhealthy in the jenkins namespace?
Scan argocd, jenkins, and monitoring and rank what needs attention.
Diagnose the argocd-server service in the argocd namespace.
Check whether ArgoCD or Jenkins explains the jenkins namespace issue.
Investigate the jenkins app across Kubernetes, service, Prometheus, ArgoCD, and Jenkins.
Check whether Prometheus has firing alerts related to monitoring.
List Kubernetes services in the jenkins namespace.
```

Available MCP tools:

- `get_nodes()`
- `list_namespaces()`
- `list_pods(namespace=None)`
- `get_pod(namespace, name)`
- `list_events(namespace, pod_name=None)`
- `get_pod_logs(namespace, name, container=None, tail_lines=100)`
- `list_services(namespace)`
- `get_endpoints(namespace, service_name)`
- `list_ingresses(namespace)`
- `investigate_namespace(namespace, tail_lines=50)`
- `diagnose_namespace(namespace, tail_lines=80)`
- `diagnose_service_path(name, namespace, tail_lines=80)`
- `scan_cluster(namespaces=None, tail_lines=80)`
- `list_argocd_apps(namespace=None)`
- `list_jenkins_builds(job_name=None, limit=10)`
- `diagnose_delivery(namespace=None, app_name=None, job_name=None, build_limit=10)`
- `investigate_app(app, namespace, service_name=None, argocd_app=None, jenkins_job=None, tail_lines=80)`
- `prometheus_query(query)`
- `prometheus_targets()`
- `prometheus_alerts()`

The MCP server does not require an LLM API key. It exposes tools and evidence to an MCP-capable host; the host owns model selection.

## Configuration

Environment variables:

```bash
PLATFORMOPS_K8S_PROVIDER=api
PLATFORMOPS_K8S_ALLOWED_NAMESPACES=default,jenkins
PLATFORMOPS_K8S_CONTEXT=
PLATFORMOPS_K8S_IN_CLUSTER=false
PLATFORMOPS_PROMETHEUS_PROVIDER=api
PLATFORMOPS_PROMETHEUS_URL=http://localhost:9090
PLATFORMOPS_PROMETHEUS_BEARER_TOKEN=
PLATFORMOPS_DELIVERY_PROVIDER=api
PLATFORMOPS_ARGOCD_URL=https://argocd.example.com
PLATFORMOPS_ARGOCD_TOKEN=
PLATFORMOPS_JENKINS_URL=https://jenkins.example.com
PLATFORMOPS_JENKINS_USER=
PLATFORMOPS_JENKINS_TOKEN=
```

Provider modes:

- `api`: use the real Kubernetes API through kubeconfig or in-cluster config
- `fake`: use deterministic built-in sample data
- `fixture`: use a local JSON fixture file

Prometheus can be configured with `--prometheus-url`, `PLATFORMOPS_PROMETHEUS_URL`, or fixture/fake provider modes for tests and demos.

Delivery can be configured with `--delivery-provider fake|fixture|api`, `--delivery-fixture`, or ArgoCD/Jenkins environment variables.

## Security Model

PlatformOps AI is read-only in `v0.x`.

It does not support:

- arbitrary shell commands
- arbitrary `kubectl` commands
- create, update, patch, or delete operations
- automatic restarts, scaling, rollbacks, or deployments

It does support:

- official Kubernetes API reads
- official ArgoCD, Jenkins, and Prometheus API reads
- namespace allowlists
- bounded log reads
- structured evidence envelopes
- deterministic diagnosis without an LLM

Do not commit kubeconfigs, service-account tokens, `.env` files, LLM keys, private certificates, or sensitive logs.

## Local Development

```bash
git clone https://github.com/FAHID-KHAN/platformops-ai.git
cd platformops-ai
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run with fixture data:

```bash
platformops k8s --provider fixture \
  --fixture tests/scenarios/crashloopbackoff.json \
  investigate --namespace platformops-demo \
  --allowed-namespaces platformops-demo
```

## Project Status

Current release: `v0.6.1 - Cross-Source App Investigation`

Roadmap:

- `v0.7.0`: orchestrated investigation experiments
- `v1.0.0`: approval-gated remediation

## Documentation

- [Documentation index](docs/README.md)
- [Current setup diagram](docs/architecture/current-setup.md)
- [Architecture overview](docs/architecture/overview.md)
- [Kubernetes diagnosis runbook](docs/runbooks/kubernetes-diagnosis.md)
- [Prometheus correlation runbook](docs/runbooks/prometheus-correlation.md)
- [Service path diagnosis runbook](docs/runbooks/service-diagnosis.md)
- [Cluster triage runbook](docs/runbooks/cluster-triage.md)
- [Delivery investigation runbook](docs/runbooks/delivery-investigation.md)
- [App investigation runbook](docs/runbooks/app-investigation.md)
- [MCP server runbook](docs/runbooks/mcp-server.md)
- [Roadmap](docs/roadmap.md)
- [ADR index](docs/adr/README.md)
- [Security policy](SECURITY.md)
