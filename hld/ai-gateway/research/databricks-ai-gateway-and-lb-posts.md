# Rohit Agrawal: Public Work Research Survey

**Prepared:** September 24, 2026 | **Target Interviewer:** Rohit Agrawal (agrawroh), Sr. Staff Engineer, Databricks Traffic Platform; Senior Maintainer, Envoy Proxy

---

## 1. Intelligent Kubernetes Load Balancing (Databricks Blog)

**Title:** Intelligent Kubernetes Load Balancing at Databricks  
**URL:** https://www.databricks.com/blog/intelligent-kubernetes-load-balancing-databricks  
**Date:** October 1, 2025  
**Authors:** Gaurav Nanda, Vincent Cheng, Rohit Agrawal

### Problem & Architecture

Databricks identified critical limitations in Kubernetes' default load balancing for high-throughput, persistent gRPC connections. "Before client-side load balancing, most requests were sent over long-lived connections, so new pods were rarely hit until existing connections were recycled." https://www.databricks.com/blog/intelligent-kubernetes-load-balancing-databricks

The team built a three-component control plane: endpoint discovery service monitoring Kubernetes API for Service/EndpointSlices changes; RPC client integration embedded in a shared Scala framework; xDS protocol with Envoy serving ClusterLoadAssignment resources.

### Algorithms

Primary strategy: Power of Two Choices (P2C), randomly selecting two backend servers and choosing the one with fewer active connections. Zone-affinity-based routing minimizes cross-zone hops, intelligently spilling overflow traffic to healthy zones when capacity is constrained.

### Key Numbers

Approximately 20% reduction in pod count across several services without compromising reliability. P90 latency became more stable across pods; variation in latency dropped noticeably. Server-side QPS became evenly distributed across backend pods. https://www.databricks.com/blog/intelligent-kubernetes-load-balancing-databricks

### Lessons Learned

"Metrics like CPU were often trailing indicators rather than real-time signals of capacity": leading to abandonment of metrics-based routing despite initial appeal. https://www.databricks.com/blog/intelligent-kubernetes-load-balancing-databricks

System maintains eventual consistency through real-time xDS updates and clients bypassing DNS and kube-proxy entirely for live endpoint visibility.

---

## 2. Governing Coding Agent Sprawl with Unity AI Gateway

**Title:** Governing coding agent sprawl with Unity AI Gateway  
**URL:** https://www.databricks.com/blog/governing-coding-agent-sprawl-unity-ai-gateway  
**Date:** April 17, 2026  
**Authors:** Aarushi Shah, Ankit Mathur, Bilal, Kevin Stumpf, Rohit Agrawal, Harish Gaur, Ana Nieto

### MCP Governance Architecture

Centralizes Model Context Protocol (MCP) server management within Databricks, enabling organizations to govern agent access to sensitive company data. "MCP tools are most useful when they have access to critical data within your organization, so it's easy to accidentally make them the most privileged developer." https://www.databricks.com/blog/governing-coding-agent-sprawl-unity-ai-gateway

Security mechanisms include centralized audit logging of all agent data access in Unity Catalog, MCP servers managed directly through Databricks infrastructure, and MLflow centralized tracing for agent interactions.

### Budget & Cost Control

Single unified budget across multiple coding tools (Cursor, Codex, Claude Code, etc.). "Give developers a single budget across all coding tools to burn down on their agent of choice." https://www.databricks.com/blog/governing-coding-agent-sprawl-unity-ai-gateway

Integration with Foundation Model API offering inference for OpenAI, Anthropic, and Gemini models. One consolidated bill from Databricks covering all token usage. Capacity management prevents runaway costs.

### Observability & Authentication

Metrics and traces automatically flow to Unity Catalog-managed Delta tables via OpenTelemetry ingestion, tracking lines of code written per user, cost per month per user, and token usage patterns. Single identity across all services: developers authenticate once with Databricks credentials for all tools including GitHub, Atlassian, and others.

### Key Metric

"A 20% increase in token usage per developer drove a 15% reduction in pull request cycle time, directly linking AI tool usage to increased developer velocity." https://www.databricks.com/blog/governing-coding-agent-sprawl-unity-ai-gateway

---

## 3. How Databricks Manages Coding Agent Spend with Unity AI Gateway Budgets

**Title:** How Databricks manages its own coding agent spend with Unity Gateway Budgets  
**URL:** https://www.databricks.com/blog/how-databricks-manages-its-own-coding-agent-spend-unity-ai-gateway-budgets  
**Date:** July 28, 2026  
**Authors:** Rohit Agrawal, Shuyu Cao, Darming Zhao, Zack Siegel, Aaron Davidson

### Budget System

Dual-budget approach: daily budget catches short-term runaway spend with self-service acknowledgment; monthly budget governs long-term extraordinary expenditure with manager approval. Both budgets route through Unity Gateway, centralizing all coding agent traffic regardless of tool or model. "All usage lands in Unity Catalog" for centralized spend tracking. https://www.databricks.com/blog/how-databricks-manages-its-own-coding-agent-spend-unity-ai-gateway-budgets

### Key Numbers

Thousands of engineers use coding agents daily across multiple platforms. Monthly limit baseline approximately $500 per engineer. "Somewhere between 500 and 1,000 engineers were hitting the limit every month." https://www.databricks.com/blog/how-databricks-manages-its-own-coding-agent-spend-unity-ai-gateway-budgets

Budget tiers use fixed increments (roughly 2x, 5x multipliers) rather than arbitrary values. Daily limit notifications trigger at roughly 90% of daily threshold. Monthly resets prevent permanent carry-over of temporary spikes.

---

## 4. Smart Routing in Unity Gateway: Match Frontier Quality with 30%+ Lower Cost

**Title:** Smart Routing in Unity Gateway: Match frontier quality with 30%+ lower cost per task  
**URL:** https://www.databricks.com/blog/smart-routing-unity-ai-gateway-match-frontier-quality-30-lower-cost-task  
**Date:** August 13, 2026  
**Authors:** Ankit Mathur, Ivan Zhou, Bryan Qiu, Rohit Agrawal, Elise Gonzales, Kelly Albano

### Routing Architecture

Task-aware routing classifies tasks using a cheaper, low-latency model analyzing task descriptions and semantic fields (system changes, code evidence, failure patterns, fix localization, project type). Triangulates model selection by defaulting to a medium-sized model and adjusting based on complexity labels, escalating to expensive models for frontier-level work or delegating to cheaper alternatives for simpler tasks.

Integrates with Omnigent, the meta-harness for coding agents, enabling routing across both models and harnesses simultaneously. Preserves cache efficiency through task-aware routing that maintains consecutive turns on the same model rather than routing per-request.

### Key Numbers

30%+ cost savings on coding tasks. 35% savings against internal benchmarks. 56% cost savings on public coding benchmarks. 65% of the cost of leading models like Opus 5 while matching performance. Less than half the cost of Opus 5 on public benchmarks. 50%+ savings possible from leveraging lower-cost models alone. https://www.databricks.com/blog/smart-routing-unity-ai-gateway-match-frontier-quality-30-lower-cost-task

---

## 5. Talks and Speaking Engagements

### KubeCon + CloudNativeCon Europe 2026

**Talk 1: The Next Generation of Envoy Extensibility: Dynamic Modules for Network, Listener, and HTTP Filters**
- **URL:** https://kccnceu2026.sched.com/
- **Date:** March 22-27, 2026 (Amsterdam)
- **Track:** EnvoyCon, Cloud Native Theater (Hall 1-5 | Tram Zone)
- **Speaker:** Rohit Agrawal

**Talk 2: The End of a Decade, the Start of an Age: Reflecting on the Past, Present, and Future of Envoy**
- **URL:** https://kccnceu2026.sched.com/
- **Date:** March 22-27, 2026
- **Track:** EnvoyCon, Cloud Native Theater (Hall 1-5 | Tram Zone)
- **Speakers:** Rohit Agrawal, Erica Hughberg (Tetrate), Kateryna Nezdolii (Isovalent), Yan Avlasov (Google)

### KubeCon + CloudNativeCon North America 2026: Maintainer Summit

**Talk: Reviewing AI-Generated PRs When Every Bug Is a CVE: Envoy's Playbook**
- **URL:** https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/
- **Time:** 10:15 AM to 10:50 AM
- **Co-speaker:** Kateryna Nezdolii
- **Content:** Shares the review playbook Envoy maintainers built in response to challenges with AI-generated pull requests, covering failure patterns in AI-written changes and how reviewer expectations were adjusted without banning AI outright.

### KubeCon + CloudNativeCon Japan 2025

**Talk: Access AI Models Anywhere: Scaling AI Traffic With Envoy AI Gateway**
- **URL:** https://kccncjpn2025.sched.com/list/descriptions
- **Date:** June 13-18, 2025
- **Co-speakers:** Dan Sun (Bloomberg), Takeshi Yoneda (Tetrate.io)
- **Content:** [unverified]: Rohit Agrawal's involvement in this session not directly confirmed; listed speakers are Dan Sun and Takeshi Yoneda.

---

## 6. Envoy Project & Dynamic Modules

### Role in Envoy Proxy

**Position:** Senior Maintainer of Envoy Proxy, CNCF graduated project; member of Envoy Security Team  
**GitHub:** https://github.com/agrawroh  
**Email:** rohit.agrawal@databricks.com  
**Areas of Responsibility:** Dynamic Modules, Reverse Tunnels, Lua, ExtAuthZ, Matchers, CI, Dependencies, Docs (per OWNERS.md) https://github.com/envoyproxy/envoy/blob/main/OWNERS.md

### Dynamic Modules Overview

Dynamic modules are "shared libraries that implement the ABI written in a pure C header file," enabling runtime extension of Envoy functionality without recompilation. https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/advanced/dynamic_modules

**Supported SDK Languages:** C++, Go, Rust (officially; any language capable of producing shared libraries theoretically supported) https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/advanced/dynamic_modules

**Extension Points:** 21+ extension points including bootstrap extensions, cluster configuration, HTTP and network filters, access loggers, formatters, stats sinks, transport sockets, TLS certificate validators, load balancing policies, tracers, DNS resolvers, and health checkers https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/advanced/dynamic_modules

**Key Features:** ABI stability: "Released ABI is frozen"; modules access HTTP headers and bodies without copying, matching built-in C++ extension efficiency; SDKs provide high-level abstractions over Envoy internals. Error handling (Rust): SDK wraps panics in fail-closed mechanism, terminating affected requests while preserving system stability. https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/advanced/dynamic_modules

### Recent Envoy Dynamic Modules Contributions

Rohit Agrawal actively contributes to Envoy dynamic modules development:
- PR #47674: dynamic_modules: report the real sampling decision for tracer spans https://github.com/envoyproxy/envoy/pull/47674
- PR #47454: dynamic_modules: migrate DM metrics to shared MetricRegistry [1/4] https://github.com/envoyproxy/envoy/pull/47454
- PR #47349: dynamic_modules: log the module source location of log statements https://github.com/envoyproxy/envoy/pull/47349
- PR #47189: fcds: add listener integration test https://github.com/envoyproxy/envoy/pull/47189

---

## 7. Databricks AI Gateway (Unity AI Gateway): Public Docs

**Documentation URL:** https://docs.databricks.com/aws/en/ai-gateway/

### Rate Limiting

Enforce consumption limits on model services and MCP services to manage capacity and cost. Model services: Set requests-per-minute (QPM) and tokens-per-minute (TPM) limits. MCP services: Set requests-per-minute (QPM) limits. Updates to Unity Gateway configurations take about 20-40 seconds; rate limiting updates can take up to 60 seconds. https://docs.databricks.com/aws/en/ai-gateway/rate-limits

### Guardrails & Service Policies

Service policies (also called guardrails) control how each request and response proceeds, based on its content and caller identity. Databricks provides built-in service policies for common risks such as PII, prompt injection, and unsafe content; users can author custom ones. https://docs.databricks.com/aws/en/ai-gateway/guardrails

### MCP Governance

MCP servers are registered as Unity Catalog securables with tool filtering and service policies. Platform supports governing custom tools as Catalog functions and HTTP connections used to reach external APIs and MCP servers. https://docs.databricks.com/aws/en/ai-gateway/

### Budget & Cost Management

Monitor spend and set per-user thresholds and hard caps. Track requests, token usage, and latency across Unity Gateway using system tables. Cost attribution by services, target models, principals, and tags. Request/response logging to Delta tables for monitoring and debugging. https://docs.databricks.com/aws/en/ai-gateway/

### Pricing

Paid features: payload logging and usage tracking. Free features: query permissions, rate limiting, fallbacks, and traffic splitting. https://docs.databricks.com/aws/en/ai-gateway/

---

## 8. Background: Rohit Agrawal at Databricks

**Title:** Sr. Staff Engineer, Traffic Platform team (leading the team)  
**Focus:** Improving data movement through Databricks' internal service mesh  
**Key Project:** Building and scaling Databricks' service mesh with Envoy Proxy at its core  
**Broader Role:** Contributing to ArgoRollouts for progressive deployment automation  
**Security Advisory Credits:** 9 security advisory credits on GitHub, indicating security-focused contributions  
**Education:** M.S. from Boston University; B.E. from University of Pune

---

## Sources Table

| ID | Title | URL | Date | Type | Supports |
|---|---|---|---|---|---|
| 1 | Intelligent Kubernetes Load Balancing at Databricks | https://www.databricks.com/blog/intelligent-kubernetes-load-balancing-databricks | Oct 1, 2025 | Blog | K8s LB, L4/L7, Envoy, xDS, algorithms |
| 2 | Governing coding agent sprawl with Unity AI Gateway | https://www.databricks.com/blog/governing-coding-agent-sprawl-unity-ai-gateway | Apr 17, 2026 | Blog | MCP, governance, auth, observability |
| 3 | How Databricks manages coding agent spend with Unity Gateway Budgets | https://www.databricks.com/blog/how-databricks-manages-its-own-coding-agent-spend-unity-ai-gateway-budgets | Jul 28, 2026 | Blog | Budgets, cost control, scale |
| 4 | Smart Routing in Unity Gateway: Match frontier quality with 30%+ lower cost | https://www.databricks.com/blog/smart-routing-unity-ai-gateway-match-frontier-quality-30-lower-cost-task | Aug 13, 2026 | Blog | Routing, cost optimization |
| 5 | KubeCon + CloudNativeCon Europe 2026 Schedule | https://kccnceu2026.sched.com/ | Mar 22-27, 2026 | Event | Envoy dynamic modules, future talks |
| 6 | KubeCon North America Maintainer Summit | https://events.linuxfoundation.org/kubecon-cloudnativecon-north-america/ | 2026 | Event | AI-generated PRs, review playbook |
| 7 | Envoy OWNERS.md (GitHub) | https://github.com/envoyproxy/envoy/blob/main/OWNERS.md | Current | Project | Maintainer roles, responsibilities |
| 8 | Envoy Dynamic Modules Documentation | https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/advanced/dynamic_modules | Current | Docs | DM architecture, SDKs, ABI |
| 9 | Databricks AI Gateway Docs | https://docs.databricks.com/aws/en/ai-gateway/ | Current | Docs | Rate limits, guardrails, budgets, MCP |
| 10 | Rohit Agrawal GitHub Profile | https://github.com/agrawroh | Current | Profile | Contributions, security work |
| 11 | Rohit Agrawal Author Page (Databricks Blog) | https://www.databricks.com/blog/author/rohit-agrawal | Current | Author Page | Published articles, bio |

---

## Interview Preparation Notes

**Key Themes:**
1. **Kubernetes & networking:** Pragmatic client-side load balancing over kube-proxy; Power of Two Choices; zone affinity
2. **Envoy expertise:** 21+ dynamic module extension points; ABI stability; Rust/Go/C++ SDKs; security-first design
3. **AI governance at scale:** MCP servers, unified budgets, rate limiting, observability via OpenTelemetry/Delta tables
4. **Cost-performance tradeoffs:** 30%+ savings with smart routing while maintaining quality; metrics (CPU) as trailing indicators
5. **Security mindset:** 9 GitHub security advisory credits; tight review practices for AI-generated code in critical paths

**Unverified Items:**
- [unverified] Rohit Agrawal's specific involvement in KubeCon Japan 2025 "Scaling AI Traffic With Envoy AI Gateway" talk: session listed with Dan Sun and Takeshi Yoneda as speakers

---

## Editor spot-check (2026-09-24, fetched every page myself)

- **LB post verified in full** (databricks.com/blog/intelligent-kubernetes-load-balancing-databricks, 2025-10-01, Gaurav Nanda, Vincent Cheng, Rohit Agrawal). Additions the survey missed:
  - "hundreds of stateless services communicating over gRPC within each Kubernetes cluster"; future work mentions "thousands of Kubernetes clusters across multiple regions".
  - Clients are **Armeria** clients ("Both Armeria clients and API proxies stream requests to it"), embedded in the shared Scala framework. The client subscribes "during the connection setup" to the services it depends on. Fallback clusters as backup.
  - Control plane watches Services and EndpointSlices, keeps "zone, readiness, and shard labels".
  - P2C picks "the one with fewer active connections or lower load". Zone affinity spills to other healthy zones when a zone "lacks sufficient capacity or becomes overloaded". "Zone-aware routing required careful tuning ... a topic to explore in a dedicated follow-up post." "In practice, keeping it simple (and consistent) has worked best."
  - Envoy integration: the same control plane serves **EDS (ClusterLoadAssignment) to Envoy** for ingress / public-facing traffic, so gateways and internal clients share one source of truth.
  - Cold starts: fixed with "slow-start ramp-up and biasing traffic away from pods with higher observed error rates", and it "reinforced the need for a dedicated warmup framework".
  - Metrics-based routing rejected: "monitoring systems had different SLOs than serving workloads, and metrics like CPU were often trailing indicators"; they "chose to rely on more dependable signals such as server health".
  - Gaps: "Languages without the library, or traffic flows that still depend on infrastructure load balancers, remain outside the scope".
  - Rejected: headless services (no endpoint weights, DNS caching staleness, no metadata for zone/shard); Istio sidecars (operational complexity of thousands of sidecars, per-pod CPU/memory/latency, limited request-aware flexibility); Istio Ambient evaluated (they already had proprietary cert distribution, routing fairly static, small infra team, Scala monorepo). They concede sidecars' main advantage is language-agnosticism.
  - Results: QPS evenly distributed, P90 variation across pods "dropped noticeably", "approximately a 20% reduction in pod count" across several services.
  - Future: cross-cluster and cross-region LB (flat L3, multi-region EDS), weighted LB for AI workloads.
- **Budgets post verified** (2026-07-28, first author Rohit Agrawal). Mechanism: every coding agent routes through Unity Gateway; two budgets, daily (runaway protection, self-serve raise by one increment after a Slack acknowledgement, eligible at about 90% of daily limit, resets each evening at the lowest-usage hour) and monthly (extraordinary spend, manager approval, coarse tiers roughly 2x, 5x, up to effectively unlimited, time-limited to the project). Effective cap = min(month-to-date usage + one runaway increment, monthly max). Tiers implemented as group membership in the gateway. The two are coupled by a fixed ratio. "Dollar figures in this post are illustrative." Old system: single $500-style monthly limit, "somewhere between 500 and 1,000 engineers were hitting the limit every month". Quote: "An unattended cron job cannot click a Slack button."
- **Governing post verified** (2026-04-17). "Coding Agent Support in Unity Gateway": three pillars (centralized security and audit with MCP servers managed in Databricks and MLflow tracing; single bill and cost limits via Foundation Model API plus bring-your-own external capacity; observability via OpenTelemetry ingestion into Unity Catalog Delta tables). Single identity across tools. Cursor, Gemini CLI, Codex CLI supported at launch.
- **Smart Routing post verified** (2026-08-13). Task-aware routing chosen over per-request routing because "at scale, costs are dominated by cache hit rate"; a small fast classifier labels the task; default to a medium model, escalate or delegate; 35% savings on the internal benchmark, 56% on public coding benchmarks; implemented in Omnigent at harness and model level; future: route after a few turns, switch models at context compaction where a cache miss already happens.
- **Talks verified**: KubeCon EU 2026 EnvoyCon (2026-03-25, Amsterdam) "The Next Generation of Envoy Extensibility: Dynamic Modules for Network, Listener, and HTTP Filters" (Rohit Agrawal) and the 10th-anniversary panel. KubeCon Japan 2026: "Beyond Wasm: How Dynamic Modules Let You Extend Envoy Proxy in Go, Rust, or Any Language" (Rohit Agrawal, Takeshi Yoneda); abstract says Databricks and Netflix are "replacing C++ forks and Wasm with native Rust", "12+ extension points", live demo of "a Rust TLS Transport Socket enabling kernel TLS (kTLS) which is impossible today with BoringSSL" (events.linuxfoundation.org/kubecon-cloudnativecon-japan/program/schedule/). The KubeCon Japan 2025 AI Gateway talk is NOT Rohit's (Dan Sun, Takeshi Yoneda).
- **Maintainer facts from OWNERS.md history**: moved to senior maintainer 2026-06-29 (#45862), not "two months ago" exactly; Envoy security team member. The "9 security advisory credits", education and "ArgoRollouts" items were not checked; do not raise them.
- **Dynamic modules ABI policy**: v1.39.1 docs promise X.Y module works on X.Y and X.(Y+1). On main, #47435 (@wbpcode, 2026-09-14) made "Released ABI is frozen", growth by `_v2` additions, and the ABI version string no longer a gate. The survey's "Released ABI is frozen" quote is from main, not from v1.39.1.
