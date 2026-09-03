# ADR-002: Begin with Read-Only Kubernetes Access

## Status

Accepted

## Decision

The initial Kubernetes integration supports read-only investigation only.

## Consequences

`v0.x` avoids create, update, patch, delete, restart, scale, rollback, and deploy operations. Future remediation must cross an explicit human approval boundary.

