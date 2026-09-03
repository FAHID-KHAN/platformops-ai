# Delivery Investigation

Delivery investigation connects platform symptoms to read-only ArgoCD and Jenkins evidence.

Use it when Kubernetes shows a problem and you want to know whether a recent GitOps or CI/CD signal should be inspected first.

## Basic Usage

List ArgoCD applications:

```bash
platformops delivery argocd apps
platformops delivery argocd apps --namespace jenkins
```

List Jenkins builds:

```bash
platformops delivery jenkins builds
platformops delivery jenkins builds --job platform/jenkins --limit 5
```

Diagnose delivery health:

```bash
platformops diagnose delivery --namespace jenkins --job platform/jenkins
```

## Fixture Demo

```bash
platformops diagnose delivery \
  --delivery-provider fixture \
  --delivery-fixture tests/scenarios/delivery_unhealthy.json \
  --namespace jenkins \
  --job platform/jenkins
```

Example output:

```text
Status: critical
Critical delivery issue detected for namespace 'jenkins', job 'platform/jenkins'.

Findings
- [critical] ArgoCD app jenkins is Degraded
- [warning] ArgoCD app jenkins is OutOfSync
- [warning] Jenkins job platform/jenkins build #42 ended with FAILURE
```

## Real API Mode

Set ArgoCD and Jenkins read-only connection details through environment variables:

```bash
export PLATFORMOPS_DELIVERY_PROVIDER=api
export PLATFORMOPS_ARGOCD_URL=https://argocd.example.com
export PLATFORMOPS_ARGOCD_TOKEN=...
export PLATFORMOPS_JENKINS_URL=https://jenkins.example.com
export PLATFORMOPS_JENKINS_USER=...
export PLATFORMOPS_JENKINS_TOKEN=...
```

Then run:

```bash
platformops diagnose delivery --namespace jenkins --job platform/jenkins
```

## What It Detects

- ArgoCD applications with degraded, missing, suspended, unknown, or out-of-sync status
- Jenkins builds that are failed, unstable, aborted, or still running
- healthy delivery evidence when ArgoCD and Jenkins both look clean

## Current Scope

Delivery investigation is read-only.

It does not:

- sync ArgoCD applications
- retry Jenkins jobs
- edit Git repositories
- patch Kubernetes resources

It provides evidence and next actions for a human operator.
