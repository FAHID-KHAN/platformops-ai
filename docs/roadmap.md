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

## v0.3.0 - Observability Correlation

- Prometheus provider.
- Metrics and alerts capabilities.
- Kubernetes and metrics correlation.
- Prometheus target and alert correlation in Kubernetes diagnosis.

## v0.4.0 - Service Path Diagnosis

- Kubernetes Service, Endpoints, and Ingress evidence.
- Service-level diagnosis.
- Previous container logs.
- Markdown incident report output.

## v0.5.0 - Cluster Triage

- Multi-namespace scanning from an explicit namespace allowlist.
- Ranked findings across namespaces.
- Cluster scan CLI, MCP tool, JSON output, and markdown incident notes.
- Homelab-friendly examples for scanning platform namespaces such as ArgoCD, Jenkins, and monitoring.

## v0.6.0 - Delivery Investigator

- Jenkins and ArgoCD read-only providers.
- Correlate deployments, revisions, pipeline failures, and Kubernetes symptoms.
- Delivery CLI, MCP tools, fixture providers, and deterministic diagnosis reports.

## v0.6.1 - Cross-Source App Investigation

- App-level investigation across Kubernetes, service-path, Prometheus, ArgoCD, and Jenkins.
- Ranked evidence chain and likely explanation.
- CLI, MCP, JSON, and markdown outputs for app investigation.

## v0.7.0 - Integration SDK Preview

- Integration manifests.
- Vendor-neutral capability vocabulary.
- Contract-test suite.
- Example community-style integration.

## v0.8.0 - Orchestrated Investigation

- Supervisor and specialist-agent experiments.
- Checkpoints, handoffs, retries, and bounded context.

## v1.0.0 - Approval-Gated Incident Response

- Human-approved remediation proposals.
- Narrow write tools.
- Execution audit trail.
- Post-remediation verification.
