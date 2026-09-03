# Security Policy

PlatformOps AI is experimental software for read-only operational investigation.

## Reporting a Vulnerability

Please report security issues privately to the project maintainers. Do not publish exploit details before maintainers have had time to investigate and respond.

## Current Security Model

- `v0.x` tools are read-only.
- Kubernetes access is performed through the Kubernetes API, not arbitrary shell commands.
- Namespace access can be restricted with `PLATFORMOPS_K8S_ALLOWED_NAMESPACES`.
- The MCP server does not need an LLM API key.
- Cluster credentials must not be sent to an LLM provider.
- Real `.env` files, kubeconfigs, service-account tokens, and sensitive logs must not be committed.

