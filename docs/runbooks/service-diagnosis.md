# Service Path Diagnosis

Use service diagnosis when a workload appears healthy but users still cannot reach it.

```bash
platformops diagnose service jenkins --namespace jenkins --allowed-namespaces jenkins
```

Export markdown for incident notes:

```bash
platformops --output markdown diagnose service jenkins --namespace jenkins --allowed-namespaces jenkins
```

PlatformOps checks:

- namespace pod diagnosis;
- Kubernetes Services;
- Endpoints readiness;
- Ingress rules;
- optional Prometheus targets and alerts.

The current implementation is read-only and deterministic. It does not inspect NetworkPolicy, DNS, TLS, or application-specific health endpoints yet.
