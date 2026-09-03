# Current Setup

This is the `v0.5.0` architecture in plain terms.

PlatformOps AI has two main entrypoints:

- a CLI for humans in a terminal
- an MCP server for AI tools that support the Model Context Protocol

Both entrypoints use the same read-only diagnosis and evidence collection code.

## Big Picture

```mermaid
flowchart TD
    human[Operator / Developer]
    ai[MCP-capable AI host]
    cli[platformops CLI]
    mcp[platformops-mcp-k8s server]

    app[Investigation and diagnosis workflows]
    policy[Read-only policy layer]
    evidence[Evidence envelopes]

    k8sProvider[Kubernetes provider]
    promProvider[Prometheus provider]

    fake[Fake provider]
    fixture[Fixture provider]
    api[Real API provider]

    kube[Kubernetes API]
    prom[Prometheus API]

    human --> cli
    ai --> mcp
    cli --> app
    mcp --> app

    app --> policy
    policy --> k8sProvider
    policy --> promProvider

    k8sProvider --> fake
    k8sProvider --> fixture
    k8sProvider --> api
    promProvider --> fake
    promProvider --> fixture
    promProvider --> api

    api --> kube
    api --> prom

    k8sProvider --> evidence
    promProvider --> evidence
    evidence --> app
    app --> cli
    app --> mcp
```

## How A CLI Request Works

Example:

```bash
platformops scan cluster --allowed-namespaces argocd,jenkins,monitoring
```

Flow:

1. The CLI parses the command and builds Kubernetes and optional Prometheus integrations.
2. The read-only policy receives the namespace allowlist.
3. PlatformOps diagnoses each allowed namespace.
4. Findings are ranked by severity.
5. The CLI prints a human-readable report, JSON, or markdown.

## How An MCP Request Works

Example prompt in an MCP host:

```text
Scan argocd, jenkins, and monitoring and rank what needs attention.
```

Flow:

1. The MCP host launches `platformops-mcp-k8s`.
2. The host calls a tool such as `scan_cluster`.
3. PlatformOps collects read-only evidence from Kubernetes and optional Prometheus.
4. PlatformOps returns structured JSON to the MCP host.
5. The host/model explains the findings to the user.

The MCP server does not run an LLM and does not need an LLM API key.

## Current Capabilities

```mermaid
flowchart LR
    nodes[get_nodes]
    namespaces[list_namespaces]
    pods[list_pods / get_pod]
    events[list_events]
    logs[get_pod_logs]
    services[list_services]
    endpoints[get_endpoints]
    ingresses[list_ingresses]
    nsdiag[diagnose_namespace]
    svcdiag[diagnose_service_path]
    scan[scan_cluster]
    prometheus[prometheus_query / targets / alerts]

    evidence[Structured evidence]
    diagnosis[Deterministic reports]

    nodes --> evidence
    namespaces --> evidence
    pods --> evidence
    events --> evidence
    logs --> evidence
    services --> evidence
    endpoints --> evidence
    ingresses --> evidence
    prometheus --> evidence
    evidence --> nsdiag
    evidence --> svcdiag
    evidence --> scan
    nsdiag --> diagnosis
    svcdiag --> diagnosis
    scan --> diagnosis
```

## Safety Boundaries

PlatformOps AI is read-only in `v0.x`.

It does not:

- run arbitrary shell commands
- run arbitrary `kubectl`
- create, update, patch, or delete Kubernetes resources
- restart pods
- scale workloads
- roll back deployments

It does:

- use official Kubernetes and Prometheus APIs
- enforce namespace allowlists for namespace-scoped Kubernetes reads
- bound log reads
- return structured evidence envelopes
- provide deterministic recommendations that still require a human operator

## Provider Modes

```mermaid
flowchart TD
    workflow[Same CLI and MCP workflows]
    fake[Fake mode: built-in sample data]
    fixture[Fixture mode: local JSON scenarios]
    api[API mode: real Kubernetes / Prometheus APIs]

    workflow --> fake
    workflow --> fixture
    workflow --> api
```

- `fake`: useful for demos and MCP tool discovery.
- `fixture`: useful for tests, examples, and repeatable incident scenarios.
- `api`: useful for a real kubeconfig, in-cluster service account, or Prometheus URL.

## What To Build Next

The strongest next phase is `v0.6.0 - Delivery Investigator`.

Goal: connect Kubernetes symptoms to delivery systems, starting with ArgoCD and Jenkins.

The useful operator questions become:

- Did ArgoCD sync fail before this pod became unhealthy?
- Which app owns this workload?
- Is the application degraded, progressing, or out of sync?
- Did a Jenkins pipeline fail around the same time?
- Which recent delivery event should the operator inspect first?
