# AI gateway for thousands of tenants

> One-line answer: a stateless Envoy fleet per region terminates an OpenAI-compatible API and MCP Streamable HTTP; native Envoy does TLS, JWT auth, circuit breaking, retries and provider fallback (composite cluster); one Rust dynamic module does what Envoy core cannot (parse the body once to pick a tenant alias, estimate tokens and translate to each provider's format, resolve the API key from a local policy snapshot, reserve tokens and dollars from a local lease, count usage from the SSE stream); a sharded Quota Service hands out leases so the counter is off the hot path for about 98% of requests and exact near a cap; shared provider quota is rationed by fleet-wide leases plus per-tenant fair queuing; MCP is routed and authorized on the `Mcp-Method` and `Mcp-Name` headers of the stateless 2026-07-28 spec, with a cached per-principal tool catalog and per-user upstream credentials (no token passthrough).

Tier 2, problem #43 in [`hld/README.md`](../README.md). Flagged as a likely prompt for a Databricks Traffic Platform interview (from a prep note, not a verified candidate report). It is their product in disguise: Unity AI Gateway. The interviewer profile and their public work are in [`research/databricks-ai-gateway-and-lb-posts.md`](research/databricks-ai-gateway-and-lb-posts.md) and [`../../popular_systems_deepdive/envoy/interviewer-prep.md`](../../popular_systems_deepdive/envoy/interviewer-prep.md).

## Problem statement (as asked)

Design an AI gateway for thousands of tenants. Applications and coding agents call many model providers (OpenAI, Anthropic, others, and self-hosted models) and many MCP tool servers through one endpoint. The gateway must authenticate every caller, enforce per-tenant and per-key rate limits in requests and tokens, enforce cost budgets, stream responses without adding latency, account for every token accurately, and govern which tools each agent may call. Say how it stays up when a provider does not.

Follow-ups that always come: how do you rate-limit tokens when the output count is known only at the end of a stream; what stops one tenant from using up the provider quota for everyone; what happens when the client disconnects mid-stream; where does the token-counting code run in Envoy; what changed for gateways in the stateless MCP spec.

## Functional requirements

Core:
1. **Unified OpenAI-compatible API.** `POST /v1/chat/completions`, `POST /v1/embeddings`, `GET /v1/models`. The `model` field names a tenant alias that maps to one of about 200 provider deployments or a self-hosted pool. The gateway translates formats.
2. **Authentication and authorization.** API keys (about 300k) and OAuth 2.1 / OIDC tokens from tenant identity providers. Grants per model and per tool, for a principal, a group, or a tenant.
3. **Rate limits and budgets.** Per tenant and per key: requests/min and tokens/min. Per principal: a daily runaway budget and a monthly cap, following Databricks' published budget design (credited in `solution.md` §5.1).
4. **Streaming with accurate usage.** SSE passthrough with no response buffering, and one usage record per request that matches the provider's count.
5. **MCP governance.** A registry of MCP servers per tenant, tool allow-lists per principal, and one aggregated endpoint that merges, filters and prefixes tool catalogs.
6. **Usage logging, tracing, cost attribution.** One usage record and one trace per request, attributable by tenant, principal, key, model, provider and tags.

Below the line: serving the models themselves (#34), response caching, agent orchestration, the batch and fine-tuning APIs, A2A traffic.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 5,000 tenants, 300k API keys, about 1M OAuth users. Peak 40k req/s (20k LLM + 20k MCP), plan for 50k. Average 16k req/s |
| Streams | 1 s to over 10 min. About 400k LLM streams open at peak (Little's law: 20k/s x 20 s mean) |
| Gateway-added latency | p99 < 10 ms on the request path, excluding model time. p99 < 1 ms per SSE event |
| Time to first byte overhead | p99 < 30 ms over the provider's own TTFB |
| Availability | 99.99% for gateway-caused errors (4.3 min/month). Provider outages are handled by fallback |
| Budget overshoot | At most max($5, 1% of the cap), and only through requests already in flight when the cap was reached |
| Rate limit accuracy | Tokens/min within 5% over any 60 s window for steady traffic |
| Config propagation | Limits, budgets, grants effective on every pod within 60 s (p99). Key revocation within 10 s |
| Usage | Dashboards within 2 min. Ledger exactly once per request id. Pod crash loses at most 1 s of that pod's usage, reconciled daily against provider exports |
| Isolation | One tenant at 10x its usual load adds < 1 ms to another tenant's gateway p99 and < 0.1 percentage points to its provider 429 rate |

## What interviewers probe (the ladder)

1. Output tokens are known only when the stream ends. How do you enforce tokens/min before you know? Where does the counter live, and what is the overshoot bound?
2. One tenant launches a batch job and the provider starts returning 429 to everyone. What stops that?
3. Walk the Envoy config for a 10-minute stream. Which default kills it first? What happens when the client disconnects?
4. Where does the token-accounting code run: ext_proc, a dynamic module, a native filter, or Envoy's own rate limit filter? Give latency and CPU numbers.
5. The primary provider returns 429 before the first token. And after the first token?
6. How does routing keep prompt caches warm, and why does per-request "cheapest model" routing cost more?
7. What changed for a gateway in the MCP 2026-07-28 spec? How do you authorize a tool call without parsing the body, and why must you still check the body?
8. The client's OAuth token is for the gateway. How does the call reach GitHub on the user's behalf without token passthrough?
9. A rate limit change must reach every pod in 60 s. Do you put 300k keys in xDS?
10. Can the gateway stop prompt injection? What can it actually guarantee?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram built one FR at a time, deep dives that break and mutate it, final design with seven rehearsal flows, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/token-budgets-and-rate-limiting.md`](deep-dives/token-budgets-and-rate-limiting.md) | Reserve, lease, reconcile. Exact mode near the cap. Overshoot math. The Databricks daily plus monthly budget design |
| [`deep-dives/streaming-and-usage-accounting.md`](deep-dives/streaming-and-usage-accounting.md) | SSE formats, forced usage reporting, the timeout matrix for long streams, buffering, first-event gate, disconnect accounting, reconciliation |
| [`deep-dives/multi-tenant-isolation.md`](deep-dives/multi-tenant-isolation.md) | Provider quota as the scarce resource, fleet-wide provider leases, weighted fair queuing, concurrency caps, circuit breaker and retry budget sizing, cells |
| [`deep-dives/routing-and-fallback.md`](deep-dives/routing-and-fallback.md) | Alias to composite cluster, per-cluster translation, fallback before the first byte, cache-aware sticky routing with bounded load, task-aware model choice |
| [`deep-dives/mcp-governance.md`](deep-dives/mcp-governance.md) | The stateless 2026-07-28 spec for gateways, header routing plus body verification, catalog cache, per-user credentials, registry and SSRF, Envoy MCP filter status |
| [`deep-dives/envoy-extension-placement.md`](deep-dives/envoy-extension-placement.md) | ext_proc vs dynamic module vs native filters vs Lua and Wasm, with latency and CPU math, and how to contain a module's blast radius |
| [`research/`](research/) | Source surveys with URLs: MCP spec and AI gateway products, Databricks posts. Input to the files above |
| `ai-gateway.excalidraw` | My drawing. Missing until I draw it |
