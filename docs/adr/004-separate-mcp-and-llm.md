# ADR-004: Separate the MCP Server from the LLM Runtime

## Status

Accepted

## Decision

The Kubernetes MCP server exposes tools and evidence but does not own LLM configuration.

## Consequences

The MCP server can run without an LLM API key, and users can bring any MCP host and model provider.

