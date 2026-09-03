# Roadmap

## v0.1.0 - Kubernetes Investigator

Goal: from an MCP-capable client, ask what nodes, namespaces, and pods exist in a cluster and receive structured evidence from PlatformOps.

Required capabilities:

- Python project bootstrap.
- Domain response models.
- Integration manifest and evidence envelope.
- Kubernetes provider protocol.
- Fake, fixture, and real Kubernetes API providers.
- MCP tools for nodes, namespaces, and pods.
- Unit and contract tests.
- Docker image and minimal Helm chart.
- MCP host example configuration.

## v0.1.x

- Pod details.
- Logs with bounded line counts.
- Events.
- Deployments.
- Cluster health.
- Redaction rules.
- Reproducible failure scenarios.

## v0.2.0 - Kubernetes Diagnosis

- Deterministic diagnosis reports.
- Kubernetes findings, severity, evidence references, and recommendations.
- Rules for common pod failure modes.
- CLI and MCP diagnosis entrypoints.

## v0.3.0 - Observability Investigator

- Prometheus provider.
- Metrics and alerts capabilities.
- Kubernetes and metrics correlation.
- PlatformOps self-metrics.

## v0.4.0 - Delivery Investigator

- Jenkins and ArgoCD read-only providers.
- Correlate deployments, revisions, pipeline failures, and Kubernetes symptoms.

## v0.4.x - Integration SDK Preview

- Integration manifests.
- Vendor-neutral capability vocabulary.
- Contract-test suite.
- Example community-style integration.

## v0.5.0 - Orchestrated Investigation

- Supervisor and specialist-agent experiments.
- Checkpoints, handoffs, retries, and bounded context.

## v1.0.0 - Approval-Gated Incident Response

- Human-approved remediation proposals.
- Narrow write tools.
- Execution audit trail.
- Post-remediation verification.
