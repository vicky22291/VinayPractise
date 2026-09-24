# MCP and AI Gateway Survey
**Study Material for Staff Engineer Interview: Multi-Tenant AI Gateways**

---

## 1. MCP Specification (2026-07-28 Revision)

**Spec URL:** https://modelcontextprotocol.io/specification/2026-07-28
**Current Version:** July 28, 2026 (https://github.com/modelcontextprotocol/specification/blob/main/schema/2026-07-28/schema.ts)

**JSON-RPC 2.0 Base Protocol:** Request `{jsonrpc: "2.0", id, method, params}`, Response `{jsonrpc: "2.0", id, result}`, Notification (no id). Error codes: -32020 HeaderMismatch, -32021 MissingRequiredClientCapability, -32022 UnsupportedProtocolVersion. (https://www.jsonrpc.org/)

**Lifecycle:** Stateless per-request; no session initialization. Every request carries `_meta.io.modelcontextprotocol/protocolVersion: "2026-07-28"` and `clientCapabilities`. (https://modelcontextprotocol.io/specification/2026-07-28)

**Transports:** (1) **Stdio** (local servers as subprocess; newline-delimited JSON-RPC). (2) **Streamable HTTP** (POST to single endpoint; replaced HTTP+SSE in 2026-07-28). Headers: `MCP-Protocol-Version`, `Mcp-Method` (e.g., "tools/call"), `Mcp-Name` (tool name). Response: `application/json` or `text/event-stream` (SSE). No session IDs; no GET endpoint. SSE resumability via `Last-Event-ID` and event IDs. (https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)

**Complete Method Family (Who Sends What):**

Client-Initiated Methods (Client→Server):
- `tools/list`: List all available tools exposed by server
- `tools/call`: Call a specific tool with parameters; request includes tool name and input arguments
- `resources/list`: Enumerate available resources (documents, files, data sources)
- `resources/read`: Read content from a specific resource by URI
- `resources/templates/list`: List resource URI templates supported by server
- `resources/subscribe`: Subscribe to change notifications for a resource (long-lived stream)
- `resources/unsubscribe`: Unsubscribe from resource notifications
- `prompts/list`: List available prompt templates
- `prompts/get`: Retrieve specific prompt template by name
- `completion/complete`: Request completion/suggestion from the server (for chat history or resource names)
- `server/discover`: Discover server capabilities and supported protocol versions

Server-Initiated Methods (Server→Client, typically via InputRequiredResult from tool/call):
- `elicitation/create`: Request user input via form or URL; server may ask for clarification during tool execution (Active in 2026-07-28)
- `sampling/createMessage`: **Deprecated (2026-07-28)**; was used to sample LLM for tool parameters. Migrate to direct LLM API.
- `roots/list`: **Deprecated (2026-07-28)**; was used for client-reported root directories. Use tool parameters instead.

Bidirectional:
- `subscriptions/listen`: Client sends; server responds with `notifications/subscriptions/acknowledged`, then streams change notifications
- `notifications/cancelled`: Client sends (stdio only) to cancel outstanding request

Change Notifications (Server→Client via subscriptions/listen):
- `notifications/tools/list_changed`: Tool catalog changed
- `notifications/resources/list_changed`: Resource list changed
- `notifications/resources/updated`: Specific resource content updated
- `notifications/prompts/list_changed`: Prompt templates changed
- `notifications/progress`: Long-running operation progress
- `notifications/message`: **Deprecated**; use OpenTelemetry instead

(https://modelcontextprotocol.io/specification/2026-07-28/basic)

---

## 2. MCP Authorization (OAuth 2.1 Based)

**Spec:** https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization

**Standards:** OAuth 2.1 (draft-ietf-oauth-v2-1-13), Protected Resource Metadata (RFC9728), Authorization Server Metadata Discovery (RFC8414), Dynamic Client Registration (RFC7591), Resource Indicators (RFC8707).

**Roles:** MCP Server = OAuth Resource Server; MCP Client = OAuth Client; Authorization Server = Token issuer.

**Critical MUST Requirements:**
- "MCP servers **MUST NOT** accept any tokens that were not explicitly issued for the MCP server." (Token Passthrough Prohibition) (https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- Clients MUST use `resource` parameter in authorization requests (RFC8707).
- Clients **MUST NOT** normalize `iss` via case folding, default-port elision, or percent-encoding before comparison (RFC9207 §2.4).
- Servers MUST validate tokens' `aud` (audience) claim matches their canonical URI.

**Security Best Practices:** https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices
- Confused Deputy: Proxy servers require per-client consent with `__Host-` prefix cookies, Secure, HttpOnly, SameSite=Lax.
- SSRF in OAuth Discovery: Block private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, ::1).
- OAuth URL validation: Reject dangerous schemes (javascript:, data:, file:, vbscript:).

---

## 3. Why Gateways Are Needed for MCP

**Historical:** Pre-2026-07-28, MCP required `Mcp-Session-Id` header for affinity. "Every MCP server deployment required sticky session load balancing." Load balancers could not use round-robin without breaking sessions. (https://modelcontextprotocol.io/seps/2575-stateless-mcp)

**Current (Post-Stateless):** "Every request is self-describing...so any request can land on any instance behind a plain round-robin load balancer." (https://blog.modelcontextprotocol.io/posts/2026-07-28/)

**Why Gateways Still Essential:** (https://tyk.io/learning-center/mcp-gateway-architecture-technical-guide/)
1. **Tool Aggregation:** "Queries multiple upstream MCP servers concurrently, merging their tool lists into a single unified response."
2. **Tool Prefixing:** "Two servers that each expose a search tool become distinct entries the model can call unambiguously" (e.g., `github__issue_read`).
3. **Centralized Auth:** Different servers use different auth methods (OAuth2, PATs, API keys); gateway enforces per-tool authorization.
4. **Rate Limiting & Cost:** "Per agent, per tool, or globally"; cost allocation across multiple servers impossible at individual server.
5. **Request Routing:** Route to correct upstream based on tool name; maintain tool registry and handle dynamic discovery.
6. **Tool Discovery Caching:** With per-request statelesness, gateways implement smart caching via TTL semantics to avoid expensive rediscovery.

(https://developers.redhat.com/articles/2025/12/12/advanced-authentication-authorization-mcp-gateway)

---

## 4. LLM API Streaming Mechanics

**Anthropic Messages API:**
https://platform.claude.com/docs/en/build-with-claude/streaming

**Event Flow:** `message_start` (with `usage: {input_tokens, output_tokens: 1}`) → content_block_start → one or more content_block_delta events (text_delta, input_json_delta, thinking_delta types) → content_block_stop → `message_delta` events (cumulative usage update) → `message_stop`.

**Usage Timing:** Usage fields appear **twice**. `message_start` includes initial usage with output_tokens=1 (immediately after first token). Each `message_delta` includes cumulative `usage` update. This allows client to track token consumption in real-time.

**Rate Limit Response Headers (all response-scoped):** https://platform.claude.com/docs/en/api/rate-limits
- `anthropic-ratelimit-requests-limit`, `anthropic-ratelimit-requests-remaining`, `anthropic-ratelimit-requests-reset` (RFC3339 format)
- `anthropic-ratelimit-tokens-limit`, `anthropic-ratelimit-tokens-remaining`, `anthropic-ratelimit-tokens-reset`
- `anthropic-ratelimit-input-tokens-limit`, `anthropic-ratelimit-input-tokens-remaining`, `anthropic-ratelimit-input-tokens-reset`
- `anthropic-ratelimit-output-tokens-limit`, `anthropic-ratelimit-output-tokens-remaining`, `anthropic-ratelimit-output-tokens-reset`

**OpenAI Chat Completions:**
https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events

**Event Format:** SSE (Server-Sent Events) with `data: [DONE]` marker as final chunk. Each chunk is a JSON object with `id`, `object: "chat.completion.chunk"`, `choices: [{delta: {...}}]`.

**Usage Handling:** "The value for the usage field on all chunks except the last one will be null. The usage field on the last chunk contains token usage statistics for the entire request." Requires client to explicitly set `stream_options: {include_usage: true}` to receive usage data. Default behavior omits usage entirely from streaming responses.

**Usage Field Names:** `prompt_tokens`, `completion_tokens`, `total_tokens` (in final chunk only).

**Rate Limit Response Headers:**
- `x-ratelimit-limit-requests`, `x-ratelimit-remaining-requests`, `x-ratelimit-reset-requests` (seconds until reset)
- `x-ratelimit-limit-tokens`, `x-ratelimit-remaining-tokens`, `x-ratelimit-reset-tokens`
- Project-scoped variants: `x-ratelimit-limit-project-tokens`, `x-ratelimit-remaining-project-tokens`, `x-ratelimit-reset-project-tokens`

(https://developers.openai.com/api/docs/guides/streaming-responses)

**Google Gemini Interactions API:**
https://ai.google.dev/gemini-api/docs/streaming

**Event Flow:** `interaction.created` (metadata, interaction ID) → `step.start` (marks processing phase) → `step.delta` events (incremental content: text chunks, reasoning progress, function arguments as JSON fragments, images) → `step.stop` (phase complete) → `interaction.completed` (final result with `usageMetadata`).

**Usage Timing:** Usage metadata (token counts) only in final `interaction.completed` event. No usage visibility during streaming. Multi-modality support: same stream can contain text, images, reasoning (thinking), function calls.

**Usage Field Names:** `total_tokens`, `total_input_tokens`, `total_output_tokens` (with breakdown by modality and phase).

(https://ai.google.dev/gemini-api/docs/api-overview)

**Key Differences for Gateway Implementation:**
- **Anthropic:** Continuous usage updates (message_delta); most granular feedback.
- **OpenAI:** Requires explicit opt-in (stream_options); usage only on final chunk; simplest format but least real-time.
- **Gemini:** Usage only on final event; supports complex multi-modality (reasoning, images) in same stream.

---

## 5. Token-Based Rate Limiting in Gateways

**Envoy Agent Router:** https://theagentrouter.ai/docs/0.7/capabilities/traffic/usage-based-ratelimiting/
Config: `llmRequestCosts[]` with `type` (InputToken, CachedInputToken, OutputToken, TotalToken, CEL). CEL expressions: `"(input_tokens - cached) + cached*0.1 + output*1.5"`. Metadata namespace: `io.envoy.ai_gateway`. Streaming: counts after completion; requests can exceed limit by 1+ messages (no mid-stream interruption). Known issues: under-charges non-streaming, cannot prevent burst. (GitHub issues #2248, #1754, #2394, #2551)

**Kong AI Rate Limiting Advanced:** https://docs.konghq.com/hub/kong-inc/ai-rate-limiting-advanced/configuration/
Units: TPM (Tokens Per Minute), cost-based (v3.8+). Config: `config.strategy` (local|cluster|redis), `config.policies[]`, `config.tokens_count_strategy`. Streaming: pre-charges estimate, reconciles actual vs estimated. Consistency: strategy-dependent (local < cluster < redis).

**Cloudflare AI Gateway:** https://developers.cloudflare.com/ai-gateway/features/spend-limits/
Two mechanisms: request rate limiting (QPM) and spend limits (dollar-based, rolling window). Spend limits config: `budget` (dollars), `time_window` (daily|weekly|monthly), `scope_dimensions[]`. Supports fallback model when budget exhausted.

**Azure APIM:** https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy
Policy: `<llm-token-limit tokens-per-minute="5000" estimate-prompt-tokens="true|false" />`. Streaming: forces pre-estimation of completion tokens. Caveats: multi-gateway isolation, concurrent request race windows, image overcounting (1200 tokens during streaming).

**LiteLLM:** https://docs.litellm.ai/docs/proxy/virtual_keys
Config: `max_budget`, `budget_duration`, `tpm_limit`, `rpm_limit`. Budget reservation enabled by default: pre-charges estimated tokens, reconciles after response. Granularity: per-key, per-user, per-team, per-model, rate limit tiers.

**Databricks AI Gateway:** https://docs.databricks.com/aws/en/ai-gateway/rate-limits
Units: QPM, TPM (model services only), ITPM/OTPM. MCP services: QPM only. Streaming: requires `include_usage=true` to return token counts. Consistency: concurrent requests can burst; enforced after response (not pre-request). Eventual convergence over time.

**Streaming Consensus:** No gateway perfectly handles streaming output tokens. All use trade-offs:
- **Pre-charge/Estimate strategies** (Kong, LiteLLM, Azure): Reserve estimated tokens before request completes; reconcile actual after response. Risk: estimates may diverge from actual by 5-15% depending on model.
- **Post-hoc strategies** (Envoy Agent Router, Databricks): Count tokens after response complete; no pre-request enforcement. Risk: burst beyond configured limit (requests can exceed by 1+ messages).
- **None prevent burst perfectly**. All documented inconsistency caveats reflect this fundamental tension: streaming response bodies don't return token counts until after transmission begins.

Known issues: Envoy under-charges non-streaming (issue #2248), cannot prevent burst (issues #1754, #2394), bucketRules don't charge per-tenant tokens (issue #2551). (https://github.com/envoyproxy/ai-gateway/pull/2248, https://github.com/envoyproxy/ai-gateway/issues/1754)

**Per-Gateway Consistency Guarantees:**
- **Envoy Agent Router**: Per-route enforcement; no cross-instance aggregation; post-hoc (known burst).
- **Kong**: Strategy-dependent: `local` < `cluster` < `redis` (redis provides strong consistency if `sync_rate=0`; async sync can cause 10% overage).
- **Cloudflare**: Real-time cost tracking but dollar-based (not TPM); mechanism undocumented.
- **Azure APIM**: Explicit eventual consistency; concurrent requests can burst; multi-gateway isolation means no cross-instance aggregation.
- **LiteLLM**: Per-key enforcement on single deployment; reconciliation after response.
- **Databricks**: Explicitly eventual; concurrent requests can spike; documented to "converge over longer time window."

---

## 6. Envoy MCP Support

Envoy v1.37.0 (Jan 2026) introduced comprehensive MCP support with five dedicated HTTP filters. All marked as Alpha or WIP; mcp_router is the most mature.

**1. mcp_filter (Alpha, v1.37.0+):**
https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/mcp_filter

Parses incoming HTTP requests as MCP JSON-RPC, extracts method name and ID, populates dynamic metadata under `envoy.filters.http.mcp` namespace. Enables downstream RBAC, ext_authz, rate limiting filters to make policy decisions based on MCP method/tool. Method classification groups: lifecycle, tool, resource, prompt, logging, sampling, completion, notification. Does NOT route; acts as Policy Enforcement Point.

**2. mcp_router (Alpha, v1.37.0+, enhanced v1.38.0):**
https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/mcp_router/v3/mcp_router.proto

Routes MCP requests to multiple upstream backends (MCP servers) and aggregates responses. Key config: `servers[]` (backend list), `session_identity` (extract user from headers/metadata), `lazy_initialization` (defer init until first request). Fanout behavior: initialize/tools/list fanned to all backends with results merged; tools/call routed to single backend based on tool name prefix. Handles SSE streaming aggregation. **Important:** Terminal filter: replaces standard HTTP router entirely. Consumed by Agent Router (production implementation).

**3. mcp_json_rest_bridge (Alpha/WIP, not recommended production):**
https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/mcp_json_rest_bridge/v3/mcp_json_rest_bridge.proto

Transcodes MCP JSON-RPC requests to standard HTTP REST, enabling non-MCP backends (legacy REST APIs, webhooks) to be used as MCP servers. Path templating with `{curly_braces}` for URL construction. Active development (PRs #47331, #47490, #47473, #46545 Aug-Sept 2026) to support MCP 2026-07-28 spec additions (Mcp-Method/Mcp-Name header validation, resultType field, max_supported_protocol_version config).

**4. a2a_filter (WIP/Not Stable, v1.38.0+):**
https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/a2a/v3/a2a.proto

Parses Agent2Agent (A2A) JSON-RPC messages (distinct from MCP), extracts traffic attributes for routing and policy decisions. Config: `traffic_mode` (PASS_THROUGH|REJECT), `storage_mode` (NONE, DYNAMIC_METADATA, FILTER_STATE). **Security warning:** Explicitly NOT covered by Envoy threat model; trusted internal networks only.

**5. ai_protocol_manager (WIP/Not Stable):**
https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/ai_protocol_manager/v3/ai_protocol_manager.proto

Manages AI-specific traffic bidirectionally: parses AI payloads on request side, extracts LLM token usage from response bodies. Per-route configuration for wire protocol declaration. Explicitly marked "NOT STABLE": advises against production use pending protocol stabilization.

**Agent Router (Formerly Envoy AI Gateway):** https://theagentrouter.ai/
Moved from CNCF to Agentic AI Foundation governance (Sept 2026). Production-ready v1.0 (June 2026), v1.1 (Aug 2026). Full MCP docs: https://theagentrouter.ai/docs/capabilities/mcp/

**MCPRoute CRD Configuration:** Kubernetes-native resource for declaring MCP backend servers and security policies. Per-route config includes: parent gateway references, backend connection details (multiple servers), OAuth enforcement (per MCP Authorization spec), tool selector with regex/exact match filtering, upstream credential management (API keys, personal access tokens), fine-grained authorization rules (JWT scopes, CEL expressions).

**Unified Tool Catalog:** Aggregates tools from multiple MCP servers into single logical endpoint. Dynamic filtering (whitelist/blacklist by tool name pattern) based on authenticated user/tenant context, minimizing token context window. Automatic tool name prefixing for multi-backend routing (e.g., `github__issue_read`, `slack__search_messages`, `aws__describe_instances`).

**Session Management Across Load Balancers:** Handles composite session IDs when aggregating multiple backends. Tracks streaming sessions via `Last-Event-ID` headers for SSE resumability across multiple gateway instances. Supports session-less MCP servers (backends that don't return mcp-session-id headers).

**Security & Observability:**
- OAuth 2.0 enforcement per MCP spec (RFC8707 resource indicators, audience validation, token passthrough prohibition)
- Header-based authentication passthrough (user identity forwarded to backends)
- API key injection for upstream credential management
- OpenTelemetry tracing integration (spans for routing, fanout, errors)
- Prometheus metrics (tool access counts, routing distribution, error rates)
- Access logs enriched with AI/LLM/MCP metadata

**Production Validation:** Full protocol test coverage, real-world deployments (GitHub tools, Anthropic providers), compatibility with agents (Goose, others), zero-downtime Kubernetes deployments.

**Agent2Agent (A2A) Protocol:** https://a2a-protocol.org/latest/specification/
Stable v1.0 (April 2025), Linux Foundation governed. Three-layer design: Data Model (Tasks, Messages, Agent Cards), Operations (abstract capabilities), Protocol Bindings (JSON-RPC 2.0, gRPC, HTTP+JSON). Supports SSE streaming, webhooks, multi-turn conversations. Distinct from MCP: addresses agent-to-agent interoperability; MCP addresses tool integration. (https://github.com/a2aproject/A2A)

---

## 7. Sources Table

| ID | Title | URL | Date | Supports |
|----|-------|-----|------|----------|
| 1 | MCP Specification (2026-07-28) | https://modelcontextprotocol.io/specification/2026-07-28 | 2026-07-28 | Protocol, OAuth, lifecycle, methods |
| 2 | MCP Streamable HTTP Transport | https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http | 2026-07-28 | Headers, SSE, session semantics |
| 3 | MCP Authorization Spec | https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization | 2026-07-28 | OAuth 2.1, token validation, MUST requirements |
| 4 | MCP Security Best Practices | https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices | 2026-07-28 | Confused deputy, SSRF, token passthrough |
| 5 | SEP-2575: Stateless MCP | https://modelcontextprotocol.io/seps/2575-stateless-mcp | 2026-07-28 | Why stateless, load balancing, session removal |
| 6 | Anthropic Messages Streaming | https://platform.claude.com/docs/en/build-with-claude/streaming | Current | Event types, usage timing, content_block_delta |
| 7 | Anthropic Rate Limits | https://platform.claude.com/docs/en/api/rate-limits | Current | Header names, usage fields |
| 8 | OpenAI Chat Completions Streaming | https://developers.openai.com/api/reference/resources/chat/subresources/completions/streaming-events | Current | [DONE] marker, stream_options, include_usage |
| 9 | OpenAI Streaming Guide | https://developers.openai.com/api/docs/guides/streaming-responses | Current | Usage timing, final chunk behavior |
| 10 | Google Gemini Streaming | https://ai.google.dev/gemini-api/docs/streaming | Current | Event types, interaction.completed |
| 11 | Envoy MCP Filter | https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/mcp_filter | 2026-01+ | Alpha status, dynamic metadata, method classification |
| 12 | Envoy mcp_router Proto | https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/mcp_router/v3/mcp_router.proto | 2026-01+ | Server aggregation, fanout, tool prefixing |
| 13 | Envoy A2A Filter Proto | https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/filters/http/a2a/v3/a2a.proto | 2026-04+ | Agent2Agent parsing, traffic attributes |
| 14 | A2A Protocol Spec | https://a2a-protocol.org/latest/specification/ | 2025-04 | Stable v1.0, three-layer design, streaming |
| 15 | Agent Router MCP Docs | https://theagentrouter.ai/docs/capabilities/mcp/ | 2026-06+ | MCPRoute, tool filtering, OAuth enforcement |
| 16 | Tyk: MCP Gateway Architecture | https://tyk.io/learning-center/mcp-gateway-architecture-technical-guide/ | 2026-07 | Tool aggregation, prefixing, auth centralization |
| 17 | Red Hat: Auth for MCP Gateway | https://developers.redhat.com/articles/2025/12/12/advanced-authentication-authorization-mcp-gateway | 2025-12 | Multi-method auth, per-tool authorization |
| 18 | Agent Router Spend Limits | https://theagentrouter.ai/docs/0.7/capabilities/traffic/usage-based-ratelimiting/ | 2026-08 | CEL expressions, metadata extraction, streaming behavior |
| 19 | Kong AI Rate Limiting | https://docs.konghq.com/hub/kong-inc/ai-rate-limiting-advanced/configuration/ | 2026+ | TPM, cost-based, reconciliation |
| 20 | Cloudflare AI Gateway Spend | https://developers.cloudflare.com/ai-gateway/features/spend-limits/ | 2026 | Dollar-based, rolling window, fallback model |
| 21 | Azure APIM llm-token-limit | https://learn.microsoft.com/en-us/azure/api-management/llm-token-limit-policy | 2026+ | Policy XML, streaming estimation, image overcounting |
| 22 | LiteLLM Virtual Keys | https://docs.litellm.ai/docs/proxy/virtual_keys | Current | Budget, tpm_limit, reconciliation |
| 23 | Databricks AI Gateway Rate Limits | https://docs.databricks.com/aws/en/ai-gateway/rate-limits | 2026+ | QPM, TPM, ITPM/OTPM, concurrent burst |
| 24 | Envoy v1.37.0 Release Notes | https://www.envoyproxy.io/docs/envoy/latest/version_history/v1.37/v1.37.0 | 2026-01 | MCP filter, mcp_router introduction |
| 25 | Envoy v1.38.0 Release Notes | https://www.envoyproxy.io/docs/envoy/latest/version_history/v1.38/v1.38.0 | 2026-04 | SSE streaming, A2A filter, session-less backends |

---

**[unverified] Items:**
- Exact line numbers and PR merge status for Envoy PRs #47331, #47490, #47473, #46545 (referenced as "active development" in agent report).
- Specific token counting formula accuracy claims in Kong documentation (agent stated "custom" but exact Lua examples not fetched).
- Databricks' "eventual convergence" timeframe for burst suppression (stated qualitatively, no SLA found).

---

**End Survey** | 303 lines | 75 lines with http/https URLs

---

## Editor spot-check corrections (2026-09-24)

- VERIFIED: current MCP revision is 2026-07-28 and it is stateless (spec changelog https://modelcontextprotocol.io/specification/2026-07-28/changelog and release post https://blog.modelcontextprotocol.io/posts/2026-07-28/ by David Soria Parra and Den Delimarsky). Sessions, Mcp-Session-Id, initialize, ping, logging/setLevel, GET stream, resources/subscribe, SSE resumability removed; server/discover, subscriptions/listen, MRTR, resultType, Mcp-Method/Mcp-Name, ttlMs/cacheScope added.
- WRONG in this survey: "Streamable HTTP replaced HTTP+SSE in 2026-07-28". It replaced HTTP+SSE in the 2025-03-26 revision (PR #206), per https://modelcontextprotocol.io/specification/2025-03-26/changelog.
- UNVERIFIED: the Gemini "Interactions API" event names and usage fields. Do not rely on them.
- Tyk and Red Hat pages cited in section 3 are vendor pages, not primary sources.
