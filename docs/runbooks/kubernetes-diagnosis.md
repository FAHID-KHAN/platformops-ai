# Kubernetes Diagnosis

Use deterministic diagnosis when you want PlatformOps to explain Kubernetes evidence instead of only listing raw objects.

```bash
platformops diagnose k8s --namespace jenkins --allowed-namespaces jenkins
```

The report includes:

- status;
- likely findings;
- evidence references;
- recommended next actions;
- limitations.

The current diagnosis engine is intentionally deterministic. It does not call an LLM and does not mutate the cluster.

## Covered Cases

- healthy namespace;
- restarted but currently ready pods;
- CrashLoopBackOff;
- ImagePullBackOff;
- pending or unschedulable pods;
- readiness failures;
- empty namespaces;
- policy or provider errors.

