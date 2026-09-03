# Prometheus Correlation

PlatformOps can add Prometheus evidence to Kubernetes diagnosis reports.

```bash
platformops diagnose k8s \
  --namespace jenkins \
  --allowed-namespaces jenkins \
  --prometheus-url http://localhost:9090
```

Prometheus commands:

```bash
platformops prometheus --prometheus-url http://localhost:9090 query up
platformops prometheus --prometheus-url http://localhost:9090 targets
platformops prometheus --prometheus-url http://localhost:9090 alerts
```

The current correlation is deterministic and read-only. It checks whether scrape targets or firing alerts appear related to the namespace being diagnosed.

