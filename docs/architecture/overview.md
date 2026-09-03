# Architecture Overview

PlatformOps AI is a model-agnostic operations platform. MCP servers expose governed tools and structured evidence; an MCP host and the user's selected model decide when to call those tools.

For the implementation that exists today, see the [current setup diagram](current-setup.md).

## First Release

`v0.1.0 - Kubernetes Investigator` proves the architecture with a read-only Kubernetes integration.

```text
MCP host
  -> user-selected LLM
  -> PlatformOps Kubernetes MCP server
  -> Kubernetes API
```

The MCP server does not require an LLM key. Kubernetes credentials stay with the Kubernetes provider and are never sent to a model provider.

## Layers

- Interface layer: MCP server now; CLI/API/UI later.
- Application layer: controlled evidence collection and report workflows.
- Domain layer: evidence envelopes, manifests, health, findings, recommendations.
- Provider layer: Kubernetes first, then observability, GitOps, CI/CD, source control, and incident systems.

## Principles

- Open-source first.
- Read-only first.
- Least privilege.
- Official APIs instead of arbitrary shell access.
- Structured evidence instead of raw command output.
- Evidence-grounded diagnosis with explicit uncertainty.
- Human approval before any future remediation.

## Initial Capabilities

- `kubernetes.get_nodes`
- `kubernetes.list_namespaces`
- `kubernetes.list_pods`

Each capability returns an evidence envelope with source, capability, collection time, scope, schema version, redaction status, payload, and errors.
