# PlatformOps AI

Read-only, model-agnostic MCP tools and CLI workflows for evidence-grounded platform operations.

PlatformOps AI helps operators investigate Kubernetes workloads without giving an AI model unrestricted infrastructure access. It collects structured evidence from official APIs, correlates Kubernetes and Prometheus signals, applies deterministic diagnosis rules, and returns operator-readable reports with evidence and limitations.

The current release focuses on Kubernetes. The architecture is designed to grow into observability, CI/CD, GitOps, source control, and approval-gated remediation.

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

Correlate Kubernetes diagnosis with Prometheus:

```bash
platformops diagnose k8s \
  --namespace jenkins \
  --allowed-namespaces jenkins \
  --prometheus-url http://prometheus.monitoring.svc:9090
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

`v0.4.0` includes deterministic Kubernetes, service-path, and Prometheus correlation rules for:

- CrashLoopBackOff-style restarts
- ImagePullBackOff and image pull failures
- Pending or unschedulable pods
- readiness failures
- restarted but currently ready pods
- empty namespaces
- policy and provider errors
- Prometheus target-down correlation
- Prometheus firing-alert correlation
- Services with missing ready endpoints
- Ingress routes attached to a service

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
```

Prometheus evidence:

```bash
platformops prometheus --prometheus-url http://localhost:9090 query up
platformops prometheus --prometheus-url http://localhost:9090 targets
platformops prometheus --prometheus-url http://localhost:9090 alerts
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

## MCP Server

PlatformOps also ships an MCP server:

```bash
platformops-mcp-k8s
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
```

Provider modes:

- `api`: use the real Kubernetes API through kubeconfig or in-cluster config
- `fake`: use deterministic built-in sample data
- `fixture`: use a local JSON fixture file

Prometheus can be configured with `--prometheus-url`, `PLATFORMOPS_PROMETHEUS_URL`, or fixture/fake provider modes for tests and demos.

## Security Model

PlatformOps AI is read-only in `v0.x`.

It does not support:

- arbitrary shell commands
- arbitrary `kubectl` commands
- create, update, patch, or delete operations
- automatic restarts, scaling, rollbacks, or deployments

It does support:

- official Kubernetes API reads
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

Current release: `v0.4.0 - Service Path Diagnosis`

Roadmap:

- `v0.5.0`: Jenkins and ArgoCD read-only delivery investigation
- `v0.6.0`: orchestrated investigation experiments
- `v1.0.0`: approval-gated remediation

## Documentation

- [Documentation index](docs/README.md)
- [Architecture overview](docs/architecture/overview.md)
- [Kubernetes diagnosis runbook](docs/runbooks/kubernetes-diagnosis.md)
- [Prometheus correlation runbook](docs/runbooks/prometheus-correlation.md)
- [Service path diagnosis runbook](docs/runbooks/service-diagnosis.md)
- [Roadmap](docs/roadmap.md)
- [ADR index](docs/adr/README.md)
- [Security policy](SECURITY.md)
