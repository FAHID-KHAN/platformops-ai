# Changelog

## 0.5.0

- Added cluster-level triage with `platformops scan cluster`.
- Added ranked findings across multiple allowed namespaces.
- Added cluster scan markdown and JSON output for incident notes and automation.
- Added MCP `scan_cluster` support for AI hosts.
- Added fixture coverage and tests for multi-namespace triage.

## 0.4.0

- Added Kubernetes Service, Endpoints, and Ingress evidence.
- Added previous pod log support.
- Added service-path diagnosis with `platformops diagnose service`.
- Added markdown diagnosis output for incident reports.
- Added service-path MCP helpers and tools.
- Added fixtures and tests for ready endpoints and missing endpoint failures.

## 0.3.0

- Added read-only Prometheus provider support.
- Added Prometheus CLI commands for instant queries, scrape targets, and alerts.
- Added Prometheus MCP payload helpers and tools.
- Added optional Prometheus correlation to Kubernetes diagnosis.
- Added fixture Prometheus provider and tests for target-down and alert-firing scenarios.

## 0.2.1

- Improved the public README and PyPI long description.
- Added clearer install, CLI, MCP, configuration, and safety guidance for new users.

## 0.2.0

- Added deterministic Kubernetes diagnosis reports.
- Added `platformops diagnose k8s --namespace ...`.
- Added MCP diagnosis support through `diagnose_namespace`.
- Added diagnosis models for findings, severity, evidence references, and recommendations.
- Added rules for CrashLoopBackOff, ImagePullBackOff, pending/unschedulable pods, readiness failures, restarted-but-ready pods, and empty namespaces.
- Added scenario fixtures and tests for common Kubernetes failure modes.

## 0.1.4

- Cleaned up remaining install messages to use `pip install platformops-ai`.
- Updated Docker packaging to use the default dependency set.

## 0.1.3

- Moved Kubernetes and MCP dependencies into the default installation.
- Simplified install instructions to `pip install platformops-ai`.
- Kept empty `kubernetes` and `mcp` extras as compatibility aliases.

## 0.1.2

- Fixed CLI placement for `--allowed-namespaces` after Kubernetes subcommands.
- Fixed namespace investigation readiness detection for multi-container pods.
- Fixed multi-container pod log collection by selecting a concrete container.
- Decoded Kubernetes byte log responses before printing CLI output.
- Added PyPI package metadata and release automation.

## 0.1.1

- Added the direct `platformops` CLI.
- Added Kubernetes pod detail, event, and bounded log excerpt capabilities.
- Added `platformops k8s investigate` for namespace-level investigation.
- Added MCP tools for pod details, events, pod logs, and namespace investigation.
- Expanded fake and fixture providers for incident-style evidence.
- Added CrashLoopBackOff fixture coverage and CLI tests.

## 0.1.0

- Bootstrapped the open-source Python project.
- Added the read-only Kubernetes investigation architecture.
- Added fake, fixture, and optional real Kubernetes providers.
- Added MCP tools for nodes, namespaces, and pods.
- Added tests, examples, Docker packaging, Helm scaffolding, and CI.
