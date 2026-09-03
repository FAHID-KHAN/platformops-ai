# PlatformOps AI

PlatformOps AI is an open-source, model-agnostic operations platform. The first release is a read-only Kubernetes MCP server that exposes structured operational evidence through safe tools.

Kubernetes is the first reference integration, not the product boundary. The architecture is designed to grow into observability, CI/CD, GitOps, source control, and approval-gated remediation while keeping credentials and infrastructure control outside the model.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the Kubernetes MCP server with deterministic fake data:

```bash
pip install -e ".[mcp]"
PLATFORMOPS_K8S_PROVIDER=fake platformops-mcp-k8s
```

For real Kubernetes API access, install the optional Kubernetes dependency and configure kubeconfig or in-cluster credentials:

```bash
pip install -e ".[mcp,kubernetes]"
PLATFORMOPS_K8S_PROVIDER=api \
PLATFORMOPS_K8S_ALLOWED_NAMESPACES=default \
platformops-mcp-k8s
```

## Initial MCP Tools

- `get_nodes()`
- `list_namespaces()`
- `list_pods(namespace=None)`

All tools return structured evidence envelopes. The MCP server does not require an LLM API key.

## Documentation

- [Documentation index](docs/README.md)
- [Architecture overview](docs/architecture/overview.md)
- [Roadmap](docs/roadmap.md)
- [ADR index](docs/adr/README.md)
- [Security policy](SECURITY.md)
- [Original open-source architecture and homelab validation plan](docs/architecture/source/open-source-architecture-and-homelab-validation.md)
- [Original learning project roadmap](docs/project/agentic-platform-engineering-learning-project.md)
