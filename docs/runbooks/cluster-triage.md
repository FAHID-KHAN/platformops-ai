# Cluster Triage

Cluster triage scans multiple allowed namespaces and ranks the findings so you can start with the highest-risk workload.

Use it when you do not already know which namespace needs attention.

## Basic Usage

```bash
platformops scan cluster --allowed-namespaces argocd,jenkins,monitoring
```

PlatformOps AI intentionally requires an explicit namespace list. It does not perform implicit whole-cluster scans.

## Homelab Example

Start by deciding which namespaces are safe and useful to inspect:

```bash
kubectl get namespaces
```

Then scan those namespaces:

```bash
platformops scan cluster --allowed-namespaces argocd,jenkins,monitoring
```

The output is ranked by severity:

```text
Cluster status: warning
Scanned 3 namespace(s). 1 namespace(s) need attention.

Ranked findings
1. [warning] jenkins - jenkins-0 restarted but is currently ready
   jenkins-0 is currently ready (2/2) but has 4 restart(s).
```

## Markdown Incident Notes

```bash
platformops --output markdown scan cluster \
  --allowed-namespaces argocd,jenkins,monitoring
```

Markdown output is useful for incident notes, pull requests, or handoff summaries.

## JSON Automation

```bash
platformops --output json scan cluster \
  --allowed-namespaces argocd,jenkins,monitoring
```

JSON output includes:

- overall cluster scan status
- per-namespace summaries
- ranked findings
- recommended next actions
- evidence references
- limitations

## Prometheus Correlation

If Prometheus is reachable from your machine or from the MCP server process, include it in the scan:

```bash
platformops scan cluster \
  --allowed-namespaces argocd,jenkins,monitoring \
  --prometheus-url http://localhost:9090
```

PlatformOps will add target-down and firing-alert findings when the Prometheus evidence appears related to the scanned namespace.

## Fixture Demo

```bash
platformops scan cluster \
  --provider fixture \
  --fixture tests/scenarios/multi_namespace_triage.json \
  --allowed-namespaces platformops-demo,jenkins
```

## Current Scope

Cluster triage is still read-only. It does not restart pods, scale deployments, patch resources, run shell commands, or execute `kubectl`.

It scans only the namespaces you provide through `--allowed-namespaces`.
