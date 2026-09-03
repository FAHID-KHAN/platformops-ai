# App Investigation

App investigation combines multiple read-only reports into one ranked evidence chain.

Use it when you want to ask:

```text
What is wrong with this app, and what should I check first?
```

## Basic Usage

```bash
platformops investigate app jenkins \
  --namespace jenkins \
  --job platform/jenkins
```

By default, the app name is also used as the Kubernetes Service name and ArgoCD app name. If your names differ, pass them explicitly:

```bash
platformops investigate app checkout \
  --namespace payments \
  --service checkout-api \
  --argocd-app payments-checkout \
  --job platform/payments-checkout
```

## What It Combines

- Kubernetes namespace diagnosis
- Kubernetes service-path diagnosis
- optional Prometheus target and alert correlation
- ArgoCD application health and sync status
- Jenkins build status

## Fixture Demo

```bash
platformops investigate app jenkins \
  --provider fixture \
  --fixture tests/scenarios/multi_namespace_triage.json \
  --allowed-namespaces jenkins \
  --delivery-provider fixture \
  --delivery-fixture tests/scenarios/delivery_unhealthy.json \
  --namespace jenkins \
  --job platform/jenkins
```

Example output:

```text
Application status: critical
Application 'jenkins' in namespace 'jenkins' has critical evidence.

Likely explanation
Delivery evidence is correlated with Kubernetes symptoms.

Evidence chain
1. [critical] delivery - ArgoCD app jenkins is Degraded
2. [critical] kubernetes - jenkins-0 is crash looping
3. [critical] service - Service jenkins was not found
```

## Prometheus Correlation

```bash
platformops investigate app jenkins \
  --namespace jenkins \
  --job platform/jenkins \
  --prometheus-url http://localhost:9090
```

Prometheus is optional. If configured, Kubernetes diagnosis can include target-down and firing-alert evidence related to the namespace.

## JSON And Markdown

```bash
platformops --output json investigate app jenkins --namespace jenkins --job platform/jenkins
platformops --output markdown investigate app jenkins --namespace jenkins --job platform/jenkins
```

Use JSON for automation and markdown for incident notes.

## Current Scope

App investigation is still read-only.

It does not:

- sync ArgoCD applications
- retry Jenkins jobs
- restart pods
- scale deployments
- patch Kubernetes resources

It provides a likely explanation, evidence chain, and next checks for a human operator.
