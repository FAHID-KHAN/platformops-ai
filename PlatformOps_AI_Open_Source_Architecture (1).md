# PlatformOps AI

## Open-Source Architecture and Homelab Validation Plan

**Status:** Living design document  
**Initial release:** `v0.1.0 — Kubernetes Investigator`  
**Project type:** Open-source, model-agnostic agentic operations platform

---

## 1. Vision

PlatformOps AI is an open-source, model-agnostic agentic operations platform. It investigates and correlates evidence across infrastructure, cloud, observability, CI/CD, GitOps, source control, databases, networking, security, and incident-management systems through governed MCP integrations.

Kubernetes is the first reference integration and the first complete vertical slice. It is not the architectural boundary of the product.

PlatformOps AI allows an agent to collect operational evidence through controlled tools, correlate signals from multiple systems, explain likely causes, recommend actions, and—only in later versions—perform human-approved remediation.

The project begins as a portable open-source product. Fahid's K3s homelab is its first real integration and staging environment, not a hard-coded dependency.

> Build a safe, extensible, evidence-grounded AI operations platform that works across a user's existing toolchain and can be validated against real infrastructure.

Long-term incident lifecycle:

```text
Detect
  ↓
Investigate
  ↓
Correlate
  ↓
Diagnose
  ↓
Recommend
  ↓
Human approval
  ↓
Remediate
  ↓
Verify
```

---

## 2. Core design principles

1. **Open-source first** — no dependency on one person's cluster, toolchain, network, credentials, or model account.
2. **Read-only first** — `v0.x` investigates but cannot mutate infrastructure.
3. **Least privilege** — every integration uses narrowly scoped identities and permissions.
4. **Official APIs, not arbitrary shell access** — integrations use supported service APIs and narrowly scoped capabilities.
5. **Model agnostic** — users can use an existing MCP host or configure their preferred LLM provider.
6. **Structured evidence** — tools return typed, predictable data rather than raw command output.
7. **Evidence-grounded diagnosis** — every important claim references collected evidence.
8. **Human approval for remediation** — future write operations require an explicit approval boundary.
9. **Observable and testable** — tool calls, latency, errors, decisions, and outcomes are measurable.
10. **Portable deployment** — the same artifact should work with fixtures, disposable environments, the homelab, or a production-style platform stack.
11. **Integration independence** — the core reasons about common capabilities and evidence, not vendor-specific implementation details.
12. **Community extensibility** — contributors can add integrations without modifying the core agent.

---

## 3. Critical architectural distinction: MCP is not the LLM

The MCP server does not need an LLM underneath it. It exposes tools and data to an AI application.

```text
User
  ↓
Agent / MCP host
  ↕
User-selected LLM
  ↓ MCP calls
PlatformOps MCP server
  ↓
Kubernetes API
```

Example flow:

1. The user asks, “Why is Jenkins unavailable?”
2. The LLM determines that Kubernetes evidence is required.
3. The MCP host invokes `list_pods(namespace="jenkins")`.
4. PlatformOps queries the Kubernetes API.
5. PlatformOps returns normalized, structured evidence.
6. The LLM evaluates it and may request events or logs.
7. The agent returns a diagnosis with evidence, uncertainty, and recommended next steps.

This separation makes the MCP server useful to many AI applications and prevents Kubernetes integration code from being tied to one model vendor.

---

## 4. Supported operating modes

### 4.1 MCP-server-only mode

Users connect PlatformOps to an existing MCP-capable host.

```text
Existing MCP host
  ├── its configured LLM
  └── PlatformOps Kubernetes MCP server
          ↓
      Kubernetes API
```

Properties:

- PlatformOps requires no LLM API key.
- The user's host owns model selection and tool-calling behavior.
- PlatformOps supplies safe, documented Kubernetes capabilities.
- This is the smallest and most interoperable installation.

### 4.2 Standalone PlatformOps Agent mode

The project also provides an optional reference agent and CLI.

```text
User
  ↓
PlatformOps Agent
  ├── configurable LLM provider
  └── MCP client
          ↓
  PlatformOps MCP server
          ↓
      Kubernetes API
```

Properties:

- Users bring their own model and credentials.
- The project supplies a controlled investigation workflow.
- Cloud and local models can be supported through provider adapters.
- CI can run without a paid model through deterministic test implementations.

---

## 5. High-level product architecture

```text
Interface layer
├── MCP server
├── CLI
└── future API/UI
        ↓
Investigation application layer
├── scope investigation
├── gather evidence
├── validate evidence
├── diagnose
└── produce report
        ↓
Domain layer
├── Evidence
├── Finding
├── Diagnosis
├── Recommendation
└── ApprovalRequest
        ↓
Provider layer
├── Kubernetes
├── Prometheus
├── ArgoCD
├── Jenkins
└── LLM providers
        ↓
External systems
```

The MCP layer must not contain Kubernetes-specific business reasoning. MCP tools invoke application services, which use stable provider contracts.

### 5.1 Supported integration domains

| Domain | Example systems |
|---|---|
| Container orchestration | Kubernetes, K3s, EKS, AKS, GKE, OpenShift |
| Observability | Prometheus, Grafana, Loki, InfluxDB, OpenTelemetry, Datadog |
| CI/CD | Jenkins, GitHub Actions, GitLab CI, Azure DevOps |
| GitOps | ArgoCD, Flux |
| Source control | GitHub, GitLab, Bitbucket |
| Cloud platforms | AWS, Azure, GCP, Cloudflare |
| Infrastructure as code | Terraform, OpenTofu, Pulumi |
| Containers and registries | Docker, containerd, OCI registries |
| Databases and data stores | PostgreSQL, MySQL, Redis |
| Networking | DNS, ingress controllers, gateways, load balancers |
| Security | Trivy, Falco, policy engines, cloud-security services |
| Incident management | PagerDuty, Opsgenie, ServiceNow |
| Work tracking | Jira, Linear |
| Communication | Slack, Microsoft Teams |

This table is a direction, not a promise to implement every integration in the initial releases.

### 5.2 Integration registry

PlatformOps should discover enabled integrations through a registry rather than hard-coded agent branches.

```text
PlatformOps Agent
        ↓
Integration Registry
        ├── Kubernetes integration
        ├── Prometheus integration
        ├── Jenkins integration
        ├── ArgoCD integration
        ├── GitHub integration
        └── community integrations
```

Each integration declares its identity, capabilities, risk level, configuration schema, health state, and authentication requirements.

```yaml
integration:
  id: prometheus
  version: 1
  capabilities:
    - metrics.query
    - alerts.list
    - targets.inspect
  risk_level: read-only
  authentication:
    type: bearer-token
  evidence_types:
    - metric-series
    - alert
    - scrape-target
```

The registry must not contain credentials. It contains metadata and references to secret configuration.

### 5.3 Vendor-neutral capabilities

The core agent should reason about operational intent through common capability names:

```text
workload.list
workload.get_status
logs.query
metrics.query
alerts.list
deployment.get_status
pipeline.get_failure
source.get_recent_changes
incident.create
```

A provider maps a capability to a vendor-specific operation:

```text
metrics.query
├── Prometheus
├── InfluxDB
├── Datadog
└── Azure Monitor
```

Vendor-specific tools remain possible when a system has unique functionality. The common capability vocabulary should cover shared operational intent without forcing every provider into an inaccurate abstraction.

### 5.4 Integration SDK

The public project should eventually include an Integration Development Kit that enables contributors to implement adapters consistently.

An integration package should provide:

- a manifest and configuration schema;
- one or more capability implementations;
- typed input and output contracts;
- authentication and secret references;
- declared risk levels;
- health and readiness checks;
- data-redaction rules;
- unit and contract tests;
- fixtures and example configuration;
- documentation and compatibility metadata.

The core application loads only explicitly enabled and trusted integrations. Installing an integration must not automatically grant it credentials or permissions.

### 5.5 Example cross-system investigation

```text
Question: Why did checkout become unavailable?

Kubernetes
  → pods began restarting at 13:42

Prometheus
  → error rate increased at 13:41

ArgoCD
  → a new revision synchronized at 13:39

GitHub
  → the revision changed DATABASE_URL

Jenkins
  → deployment completed but its smoke test was skipped

Diagnosis
  → the latest release likely introduced an invalid database endpoint
```

The report references evidence from every contributing system and distinguishes observed facts from inferred causality.

---

## 6. Proposed repository structure

```text
platformops-ai/
├── README.md
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── CHANGELOG.md
├── Makefile
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── packages/
│   ├── platformops-core/          # Domain models and workflows
│   ├── platformops-agent/         # Optional standalone agent
│   ├── platformops-policy/        # Shared authorization and risk controls
│   ├── platformops-integration-sdk/
│   └── platformops-mcp-k8s/       # First reference integration
│
├── src/platformops/
│   ├── agent/                     # Controlled investigation workflow
│   ├── domain/                    # Evidence, findings and reports
│   ├── policies/                  # Authorization and safety policies
│   ├── integrations/
│   │   ├── registry.py
│   │   ├── capabilities.py
│   │   └── manifests.py
│   ├── providers/
│   │   ├── kubernetes/
│   │   ├── prometheus/
│   │   ├── argocd/
│   │   └── jenkins/
│   ├── llm/
│   │   ├── base.py
│   │   ├── openai.py
│   │   ├── anthropic.py
│   │   ├── gemini.py
│   │   ├── ollama.py
│   │   └── openai_compatible.py
│   ├── reports/
│   └── telemetry/
│
├── integrations/
│   ├── kubernetes/
│   ├── prometheus/
│   ├── grafana/
│   ├── influxdb/
│   ├── jenkins/
│   ├── argocd/
│   └── github/
│
├── deploy/
│   ├── docker/
│   ├── helm/platformops-ai/
│   ├── kubernetes/
│   └── demo/
│
├── tests/
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── scenarios/
│   └── homelab/
│
├── examples/
│   ├── mcp-only/
│   ├── standalone-agent/
│   └── provider-configurations/
│
├── docs/
│   ├── architecture/
│   ├── security/
│   ├── adapters/
│   ├── runbooks/
│   └── adr/
│
└── .github/workflows/
    ├── test.yml
    ├── integration.yml
    ├── security.yml
    └── release.yml
```

The exact packaging may evolve, but the architectural boundaries should remain.

---

## 7. Integration and provider contracts

External integrations should implement stable internal interfaces.

The generic contract describes an integration independently of its vendor:

```python
from typing import Protocol

class PlatformIntegration(Protocol):
    @property
    def manifest(self) -> "IntegrationManifest": ...

    async def health(self) -> "IntegrationHealth": ...

    async def invoke(
        self,
        capability: str,
        arguments: dict,
        context: "InvocationContext",
    ) -> "EvidenceEnvelope": ...
```

Specific provider protocols can offer stronger typing inside an integration:

```python
from typing import Protocol

class KubernetesProvider(Protocol):
    async def list_nodes(self) -> list["NodeSummary"]: ...
    async def list_namespaces(self) -> list["NamespaceSummary"]: ...
    async def list_pods(
        self,
        namespace: str | None = None,
    ) -> list["PodSummary"]: ...
```

Implementations:

```text
KubernetesProvider
├── KubernetesApiProvider   # Real cluster through Kubernetes API
├── FixtureProvider         # Reproducible example incidents
└── FakeProvider            # Fast deterministic unit tests
```

Benefits:

- Contributors need no homelab to run tests.
- Vendor client code is replaceable without changing the investigation core.
- Failure scenarios can be replayed deterministically.
- Future providers follow the same architectural pattern.
- Community adapters can be validated through shared contract tests.

An `EvidenceEnvelope` should include source integration, capability, collection time, resource scope, redaction status, payload schema version, and a unique evidence ID.

---

## 8. Model-provider architecture

The standalone agent should depend on an internal protocol rather than a specific SDK.

```python
from typing import Protocol

class ModelProvider(Protocol):
    async def generate(
        self,
        messages: list["Message"],
        tools: list["ToolDefinition"],
    ) -> "ModelResponse": ...
```

Initial or future adapters may support:

| Provider type | Example configuration |
|---|---|
| OpenAI | API key and model name |
| Anthropic | API key and model name |
| Gemini | API key and model name |
| Azure OpenAI | Endpoint, deployment and credentials |
| Ollama | Local endpoint and model |
| vLLM | OpenAI-compatible endpoint |
| LM Studio | OpenAI-compatible local endpoint |
| Custom | Community implementation of `ModelProvider` |

A deterministic provider should exist for CI so tests do not require network calls, paid tokens, or nondeterministic model output.

---

## 9. Bring-your-own-LLM configuration

Example application configuration:

```yaml
agent:
  model_provider: openai
  model: example-model-name
  temperature: 0.1

llm:
  api_key_env: PLATFORMOPS_LLM_API_KEY
  base_url: null

mcp:
  kubernetes:
    transport: stdio

kubernetes:
  mode: kubeconfig
  context: kind-platformops
  allowed_namespaces:
    - platformops-demo
  read_only: true
```

The configuration contains the name of the secret-bearing environment variable, not the secret itself:

```bash
export PLATFORMOPS_LLM_API_KEY="your-key"
platformops investigate "Why is the API unavailable?"
```

Example `.env.example`:

```dotenv
PLATFORMOPS_LLM_PROVIDER=openai
PLATFORMOPS_LLM_MODEL=example-model-name
PLATFORMOPS_LLM_API_KEY=
PLATFORMOPS_LLM_BASE_URL=
```

The real `.env` must be excluded from Git.

### Local-model example

```yaml
agent:
  model_provider: ollama
  model: example-local-model

llm:
  base_url: http://localhost:11434
```

### OpenAI-compatible endpoint example

```yaml
agent:
  model_provider: openai-compatible
  model: example-model

llm:
  base_url: http://localhost:8000/v1
  api_key_env: PLATFORMOPS_LLM_API_KEY
```

Provider names and model identifiers in documentation should be examples rather than hard-coded product dependencies.

---

## 10. Credential boundaries

Credentials must remain separated by component.

| Credential | Used by | Must not be sent to |
|---|---|---|
| LLM API key | Agent runtime | MCP servers or Kubernetes |
| Kubernetes identity | Kubernetes MCP server | LLM provider |
| Prometheus token | Prometheus provider/server | LLM provider |
| Jenkins token | Jenkins provider/server | LLM provider |
| ArgoCD token | ArgoCD provider/server | LLM provider |

The model sees sanitized operational evidence, never infrastructure credentials.

---

## 11. Kubernetes security model

PlatformOps uses defense in depth:

```text
Agent policy
  ↓ permits a named tool
MCP input validation
  ↓ permits bounded parameters
Provider policy
  ↓ enforces namespaces and limits
Kubernetes RBAC
  ↓ authorizes the actual API request
Kubernetes API
```

For `v0.1`, allow only read operations such as:

- verbs: `get`, `list`, and possibly `watch`;
- resources: namespaces, nodes, pods, pod logs, deployments, ReplicaSets, and events;
- configurable namespace allowlists;
- bounded log line counts and time windows;
- request timeouts and rate limits;
- secret-pattern redaction.

Do not initially support:

- arbitrary shell commands;
- arbitrary `kubectl` commands;
- `create`, `update`, `patch`, or `delete`;
- unrestricted cluster-resource access;
- automatic restarts, scaling, rollbacks, or deployments.

The Helm chart should create a dedicated ServiceAccount and minimal RBAC. Namespace-scoped installation should be the safe default; cluster-wide observation should be an explicit choice.

---

## 12. Privacy and operational-data handling

When a cloud model is used, selected operational evidence may be included in the model request. PlatformOps must make that visible and configurable.

```yaml
privacy:
  redact_secrets: true
  include_logs: true
  max_log_lines: 200
  blocked_patterns:
    - Authorization
    - password
    - api_key
    - token
```

Required protections:

- redact common secret formats and sensitive fields;
- cap log and event sizes;
- allow logs to be disabled;
- restrict namespaces and resources;
- document which data can leave the cluster;
- support local models for sensitive environments;
- avoid recording raw prompts or logs by default;
- provide configurable telemetry retention.

---

## 13. Structured evidence and diagnosis

MCP tools return stable data contracts rather than unstructured command output.

Example evidence-backed diagnosis:

```json
{
  "status": "degraded",
  "summary": "Jenkins is unavailable because its pod is repeatedly restarting",
  "findings": [
    {
      "claim": "jenkins-0 is in CrashLoopBackOff",
      "evidence_ids": ["k8s-pod-17", "k8s-event-42"],
      "confidence": 0.96
    }
  ],
  "recommended_actions": [
    {
      "action": "inspect_previous_container_logs",
      "risk": "read-only",
      "approval_required": false
    }
  ],
  "limitations": []
}
```

Important rules:

- Every major claim references one or more evidence IDs.
- Confidence is not a substitute for evidence.
- Missing data is reported explicitly.
- Recommendations are separated from observed facts.
- Tool errors are preserved rather than hidden from the final report.

---

## 14. Controlled agent workflow

The first agent should be a bounded workflow, not a free-form autonomous system.

```text
Operational question
  ↓
Determine investigation scope
  ↓
Gather permitted evidence
  ↓
Validate and normalize evidence
  ↓
Generate candidate findings
  ↓
Is evidence sufficient?
  ├── No → report uncertainty and missing evidence
  └── Yes → rank likely causes
                 ↓
        evidence-backed report
```

Multi-agent orchestration should only be introduced after the single-agent investigation workflow is reliable, observable, and evaluated.

---

## 15. Testing strategy

### Level A: no cluster and no LLM required

Unit and contract tests use fakes, fixtures, and deterministic responses.

Example scenario:

```text
fixture: crashloopbackoff.json
question: Why is checkout-api unavailable?
expected category: container_start_failure
required evidence: BackOff event
```

These tests run on every pull request.

### Level B: disposable Kubernetes cluster

CI creates a `kind` or `k3d` cluster and deploys controlled scenarios:

- healthy deployment;
- CrashLoopBackOff;
- missing ConfigMap;
- failing readiness probe;
- unschedulable pod;
- image pull failure.

This validates the real Kubernetes API adapter without requiring the homelab.

### Level C: private homelab acceptance testing

The same released artifact is deployed into Fahid's K3s environment and tested against real workloads.

```text
Public pull request
  ↓
Unit + contract + disposable-cluster tests
  ↓
Merge and versioned container image
  ↓
Private GitOps configuration
  ↓
ArgoCD
  ↓
K3s homelab
  ↓
Manual and automated acceptance tests
```

Homelab tests should be isolated:

```bash
pytest -m homelab
```

They must never be required for an external contributor's pull request.

---

## 16. Public and private configuration

### Public project repository

```text
platformops-ai/
├── application source
├── integration registry and SDK
├── first-party integrations
├── generic Helm chart
├── example configuration
├── controlled failure scenarios
├── tests
└── documentation
```

### Private environment repository

```text
platformops-homelab/
├── clusters/homelab/
├── apps/platformops-ai/
│   ├── values.yaml
│   └── application.yaml
└── encrypted secrets
```

Never commit:

- kubeconfig files;
- service-account tokens;
- LLM API keys;
- Jenkins, Grafana, Prometheus, or ArgoCD credentials;
- private certificates;
- real `.env` files;
- sensitive logs;
- unnecessary internal network information.

---

## 17. Observability

PlatformOps should observe itself from the first release.

Suggested metrics:

```text
platformops_mcp_requests_total
platformops_tool_calls_total
platformops_tool_call_duration_seconds
platformops_tool_errors_total
platformops_agent_requests_total
platformops_investigation_duration_seconds
platformops_evidence_items_total
platformops_redactions_total
```

Also use structured logs and traces containing safe metadata such as:

- request and investigation IDs;
- selected tool name;
- duration and status;
- evidence type and source;
- policy decisions;
- model provider category without exposing keys;
- approval state in future remediation workflows.

Avoid storing raw cluster logs or complete model prompts by default.

---

## 18. Open-source release requirements

Before public release, include:

- an appropriate open-source license, likely Apache License 2.0;
- a clear README and five-minute quick start;
- `SECURITY.md` with responsible disclosure instructions;
- `CONTRIBUTING.md` and development setup;
- Code of Conduct;
- architecture and threat-model documentation;
- automated linting, tests, dependency scanning, and secret scanning;
- versioned Docker images;
- a minimal Helm chart with least-privilege RBAC;
- reproducible demo incidents;
- Architecture Decision Records;
- an experimental-status warning and production-safety guidance.

A credible industry project should demonstrate:

```text
Reproducible installation
+ stable tool contracts
+ security boundaries
+ meaningful tests
+ observable execution
+ realistic incidents
+ documented decisions
= industry credibility
```

---

## 19. Release roadmap

### `v0.1.0 — Kubernetes Investigator`

Goal: prove the generic PlatformOps integration, evidence, policy, and MCP architecture through a model-independent, read-only Kubernetes reference integration, plus an optional reference agent.

Initial MCP tools:

- `get_nodes()`
- `list_namespaces()`
- `list_pods(namespace=None)`
- later within `v0.1`: pod details, logs, events, deployments, and cluster health

Required release capabilities:

- typed responses and consistent errors;
- fake and fixture providers;
- real Kubernetes API provider;
- unit and contract tests;
- disposable-cluster integration tests;
- container image;
- minimal Helm chart and RBAC;
- MCP-host configuration example;
- one reproducible failure demonstration.

### `v0.2.0 — Observability Investigator`

- Prometheus provider and MCP capabilities;
- correlate Kubernetes health with CPU, memory, restarts, and latency;
- add investigation metrics and initial Grafana dashboard.
- validate the first cross-integration investigation using common evidence contracts.

### `v0.3.0 — Delivery Investigator`

- Jenkins and ArgoCD read-only providers;
- correlate deployment state, revisions, pipeline failures, and cluster symptoms;
- maintain evidence attribution across providers.

### `v0.3.x — Integration SDK Preview`

- publish integration manifests and lifecycle contracts;
- publish the initial vendor-neutral capability vocabulary;
- provide a project template and shared contract-test suite;
- document authentication, redaction, permissions, and risk declaration;
- demonstrate one small community-style example integration.

### `v0.4.0 — Orchestrated Investigation`

- supervisor and specialist-agent experiments;
- state, checkpoints, handoffs, retries, and bounded context;
- evaluate whether multi-agent execution materially improves results.

### `v1.0.0 — Approval-Gated Incident Response`

- policy-scoped remediation proposals;
- explicit human approval;
- narrowly defined write tools;
- execution audit trail;
- post-remediation verification;
- rollback and failure-handling strategy.

---

## 20. Initial Sprint 1

### Sprint goal

From an MCP-capable client, ask:

> What nodes, namespaces, and pods exist in this cluster?

The result must come through PlatformOps from the real Kubernetes API and use structured responses.

### Sprint backlog

1. Create the public repository and governance files.
2. Bootstrap the Python project.
3. Define initial domain response models.
4. Define the initial integration manifest and evidence envelope.
5. Create the generic integration registry and capability contract.
6. Create the Kubernetes provider protocol.
7. Implement `FakeKubernetesProvider`.
8. Implement the real Kubernetes API provider.
9. Implement `get_nodes()`.
10. Implement `list_namespaces()`.
11. Implement `list_pods()`.
12. Expose the operations as MCP tools.
13. Add unit and contract tests.
14. Create a disposable `kind` integration test.
15. Document connection from an existing MCP host.
16. Add Docker packaging.
17. Validate locally against the K3s homelab.

### Sprint acceptance criteria

- A stranger can clone the project and run fixture-mode tests without a cluster.
- CI validates the real adapter using a disposable cluster.
- An MCP host can discover and call all three tools.
- The same code can connect to Fahid's K3s cluster.
- No LLM API key is required to run the MCP server.
- No cluster credentials are transmitted to the LLM provider.
- Kubernetes permissions are read-only and documented.
- No homelab secrets or environment-specific assumptions exist in the public repository.

---

## 21. Architecture Decision Records to create first

1. **ADR-001: Use MCP as the tool integration protocol**
2. **ADR-002: Begin with read-only Kubernetes access**
3. **ADR-003: Use the Kubernetes API instead of shell commands**
4. **ADR-004: Separate the MCP server from the LLM runtime**
5. **ADR-005: Support bring-your-own-model provider adapters**
6. **ADR-006: Use structured evidence and attributable diagnoses**
7. **ADR-007: Separate public product configuration from private environments**
8. **ADR-008: Validate with fixtures, disposable clusters, and homelab staging**
9. **ADR-009: Treat Kubernetes as the first reference integration, not the product boundary**
10. **ADR-010: Introduce an integration registry and vendor-neutral capability vocabulary**
11. **ADR-011: Provide a contract-tested SDK for trusted community integrations**

---

## 22. Definition of project success

The project is succeeding when:

- an external user can understand and run it without Fahid's infrastructure;
- the core platform remains useful beyond Kubernetes;
- Kubernetes remains the first reference integration rather than a hard-coded architectural dependency;
- an MCP-only user can use the Kubernetes server without configuring an LLM inside PlatformOps;
- a standalone-agent user can bring a cloud or local model without modifying core code;
- users can enable only the integrations required by their environment;
- contributors can add an integration through the SDK and shared contracts without changing the agent core;
- investigations cite real evidence and clearly state uncertainty;
- security boundaries remain enforceable even when the model makes a bad decision;
- CI reproduces real Kubernetes failure scenarios;
- the released artifact works unchanged in the K3s homelab;
- each new integration follows documented contracts, tests, and least-privilege policies.

The central product promise is:

> PlatformOps AI gives agents governed access to operational evidence across the platform toolchain. It does not give models unrestricted control of infrastructure or operational systems.
