# PlatformOps AI

## Agentic Platform Engineering Learning Project

> Goal: Build a production-style engineering project that teaches modern
> Agentic AI, MCP, Kubernetes, Platform Engineering, GitOps,
> Observability, and AI orchestration using a real homelab.

------------------------------------------------------------------------

# Vision

PlatformOps AI is an AI Platform Engineer that can investigate
Kubernetes and platform incidents through secure, permission-scoped MCP
tools.

Rather than building a chatbot, the project builds an engineering
platform.

------------------------------------------------------------------------

# Long-Term Architecture

``` text
                    PlatformOps AI
                           │
                    Supervisor Agent
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
 Kubernetes Agent     CI/CD Agent      Observability Agent
        │                  │                  │
       MCP                MCP                MCP
        │                  │                  │
      K3s            Jenkins/ArgoCD    Prometheus/Grafana
        └──────────────────┼──────────────────┘
                           ▼
                    Incident Diagnosis
                           │
                    Human Approval
                           │
                           ▼
                      Remediation
```

------------------------------------------------------------------------

# Core Learning Goals

-   Understand Agentic AI architecture
-   Learn Model Context Protocol (MCP)
-   Build secure AI tooling
-   Learn Kubernetes APIs
-   Practice RBAC and least privilege
-   Deploy through GitOps
-   Instrument software with Prometheus
-   Design production-ready software
-   Learn multi-agent orchestration
-   Build a portfolio-quality Platform Engineering project

------------------------------------------------------------------------

# Guiding Engineering Principles

1.  Read-only first
2.  Least privilege
3.  Kubernetes API over shell commands
4.  Structured tool outputs
5.  Human approval before destructive actions
6.  Everything observable
7.  Everything documented

------------------------------------------------------------------------

# Repository Structure

``` text
platformops-ai/
├── docs/
│   ├── architecture.md
│   ├── security.md
│   ├── development.md
│   └── adr/
├── src/
├── tests/
├── deploy/
├── .github/workflows/
└── README.md
```

------------------------------------------------------------------------

# Roadmap

## Sprint 1

-   Create repository
-   Bootstrap Python project
-   Build first MCP server
-   Connect to Kubernetes API
-   Implement:
    -   get_nodes()
    -   list_namespaces()
    -   list_pods()

Goal:

> "What nodes and pods exist in my homelab?"

answered through our own MCP server.

## Sprint 2

-   Pod details
-   Logs
-   Events
-   Cluster health

## Sprint 3

Prometheus MCP

## Sprint 4

Grafana MCP

## Sprint 5

Jenkins MCP

## Sprint 6

ArgoCD MCP

## Sprint 7

Cross-tool reasoning

## Sprint 8

RBAC and approval workflows

## Sprint 9

Multi-agent architecture

## Sprint 10

Documentation, testing, release, demo

------------------------------------------------------------------------

# Version Plan

## v0.1

Kubernetes Investigator

## v0.2

Observability Investigator

## v0.3

CI/CD Investigator

## v0.4

Multi-Agent PlatformOps

## v1.0

Agentic Kubernetes Incident Response Platform

Capabilities:

Detect → Investigate → Correlate → Diagnose → Recommend → Human Approval
→ Remediate → Verify

------------------------------------------------------------------------

# Success Criteria

By the end of the project I should understand:

-   MCP
-   Kubernetes APIs
-   Agent orchestration
-   Platform Engineering
-   GitOps
-   CI/CD
-   Observability
-   AI security
-   RBAC
-   Human-in-the-loop design
-   Production software architecture

The final project should be something I can confidently demonstrate in
Platform Engineering, DevOps, Cloud Engineering, and SRE interviews.

------------------------------------------------------------------------

# Notes

This repository is intentionally treated like a real engineering product
rather than a tutorial project. Every feature should go through
planning, implementation, testing, CI, deployment, documentation, and
retrospective improvements.
