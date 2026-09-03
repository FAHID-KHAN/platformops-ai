# MCP Server

PlatformOps AI can run as an MCP server for AI applications that support the Model Context Protocol.

The MCP server does not run an LLM by itself. It exposes read-only tools; your MCP host owns the model, chat interface, and tool-calling behavior.

```text
User
  -> MCP host and selected LLM
  -> PlatformOps MCP server
  -> Kubernetes API and optional Prometheus API
```

## Install

```bash
pip install platformops-ai
```

## Start The Server

```bash
platformops-mcp-k8s
```

Most users do not run that command manually. They configure an MCP host to launch it.

## Fake Mode

Use fake mode to verify that your MCP host can discover and call tools without a cluster.

```json
{
  "mcpServers": {
    "platformops-kubernetes": {
      "command": "platformops-mcp-k8s",
      "env": {
        "PLATFORMOPS_K8S_PROVIDER": "fake",
        "PLATFORMOPS_PROMETHEUS_PROVIDER": "fake"
      }
    }
  }
}
```

## Real Cluster Mode

Use API mode when the MCP server process has kubeconfig access or runs inside a cluster with a service account.

```json
{
  "mcpServers": {
    "platformops-kubernetes": {
      "command": "platformops-mcp-k8s",
      "env": {
        "PLATFORMOPS_K8S_PROVIDER": "api",
        "PLATFORMOPS_K8S_ALLOWED_NAMESPACES": "argocd,jenkins,monitoring",
        "PLATFORMOPS_PROMETHEUS_URL": "http://localhost:9090"
      }
    }
  }
}
```

## Example Prompts

```text
What nodes and namespaces can PlatformOps see?
Diagnose the jenkins namespace.
Diagnose the argocd-server service in the argocd namespace.
List services and endpoints in the monitoring namespace.
Check Prometheus targets and alerts.
```

## Tools

- `get_nodes()`
- `list_namespaces()`
- `list_pods(namespace=None)`
- `get_pod(namespace, name)`
- `list_events(namespace, pod_name=None)`
- `get_pod_logs(namespace, name, container=None, tail_lines=100)`
- `list_services(namespace)`
- `get_endpoints(namespace, service_name)`
- `list_ingresses(namespace)`
- `investigate_namespace(namespace, tail_lines=50)`
- `diagnose_namespace(namespace, tail_lines=80)`
- `diagnose_service_path(name, namespace, tail_lines=80)`
- `prometheus_query(query)`
- `prometheus_targets()`
- `prometheus_alerts()`

## Security Notes

- The server is read-only in `v0.x`.
- Namespace allowlists restrict namespace-scoped Kubernetes evidence.
- The MCP server does not need an LLM API key.
- Kubernetes credentials stay with the MCP server process.
- Do not expose kubeconfig, service-account tokens, `.env` files, or sensitive logs.

