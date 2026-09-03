# ADR-003: Use the Kubernetes API Instead of Shell Commands

## Status

Accepted

## Decision

PlatformOps talks to Kubernetes through the official Kubernetes API client.

## Consequences

The project avoids arbitrary shell access and can apply typed provider contracts, input validation, and least-privilege RBAC.

