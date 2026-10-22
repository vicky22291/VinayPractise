# Webhook Delivery Service: Facts Survey

Crux: at-least-once delivery to untrusted endpoints, with retries over days, signing, and SSRF-safe egress.

## Checklist

| Fact | Value | URL | Status |
|------|-------|-----|--------|
| Stripe live-mode retry window | Up to three days, exponential backoff | https://docs.stripe.com/webhooks | verified |
| Stripe sandbox retry | Three retries over a few hours | https://docs.stripe.com/webhooks | verified |
| Stripe exact retry intervals | Not published (only "exponential backoff") | https://docs.stripe.com/webhooks | verified (absence) |
| Stripe endpoint timeout | Not published. Docs only say "quickly return" and list "Timed out" as an error | https://docs.stripe.com/webhooks | verified (absence) |
| Stripe timeout value | Often cited as 20 s. Not confirmed by Stripe | https://www.svix.com/resources/webhook-university/reliability/webhook-timeout-best-practices/ | secondary |
| Stripe redirects | 3xx counts as failure. Redirects are not followed | https://docs.stripe.com/events/manage-webhook-endpoints | verified |
| Stripe success definition | 2xx status code | https://docs.stripe.com/webhooks | verified |
| Stripe endpoint disable rule and merchant emails | Not found on fetched pages | https://docs.stripe.com/webhooks | unverified |
| Stripe-Signature format | `t=<timestamp>,v1=<sig>,v0=<sig>` | https://docs.stripe.com/webhooks | verified |
| Stripe signature algorithm | HMAC with SHA-256, over `timestamp.payload` | https://docs.stripe.com/webhooks | verified |
| Stripe v0 scheme | Test events only. Ignore non-v1 schemes | https://docs.stripe.com/webhooks | verified |
| Stripe default tolerance | 5 minutes (libraries) | https://docs.stripe.com/webhooks | verified |
| Stripe tolerance of 0 | Disables recency check. Docs say do not use | https://docs.stripe.com/webhooks | verified |
| Stripe secret rotation overlap | Old secret active for up to 24 hours. Multiple v1 signatures sent | https://docs.stripe.com/webhooks | verified |
| Stripe retry signature | New signature and timestamp on every attempt | https://docs.stripe.com/webhooks | verified |
| Stripe ordering | Not guaranteed | https://docs.stripe.com/webhooks | verified |
| Stripe duplicates | Possible. Dedupe by event ID | https://docs.stripe.com/webhooks | verified |
| Stripe `created` ordering | Seconds resolution. Do not use for ordering | https://docs.stripe.com/webhooks | verified |
| Stripe thin vs snapshot | Thin is recommended for new integrations | https://docs.stripe.com/webhooks | verified |
| Stripe event destinations per account | Up to 16 | https://docs.stripe.com/webhooks | verified |
| Stripe event retention for listing | Last 30 days | https://docs.stripe.com/events/manage-webhook-endpoints | verified |
| Stripe dashboard resend window | Up to 15 days after creation | https://docs.stripe.com/webhooks | verified |
| Stripe CLI resend window | Up to 30 days after creation | https://docs.stripe.com/webhooks | verified |
| Stripe manual resend and auto-retry | Manual resend does not cancel auto-retry | https://docs.stripe.com/webhooks | verified |
| Stripe API versioning of events | Event shape fixed at creation time | https://docs.stripe.com/webhooks | verified |
| Stripe webhook IP list | 15 IPs listed for webhooks | https://docs.stripe.com/ips | verified |
| Stripe IP change notice | Seven days via api-announce list | https://docs.stripe.com/ips | verified |
| Stripe HTTPS requirement | Required in live mode. TLS 1.2 and 1.3 only | https://docs.stripe.com/webhooks | verified |
| Stripe raw body rule | Signature check needs the unmodified raw body | https://docs.stripe.com/webhooks | verified |
| Stripe Smokescreen | HTTP CONNECT proxy for outbound webhooks. Resolves DNS and denies non-public IPs | https://github.com/stripe/smokescreen | verified |
| Stripe idempotency key pruning | Keys may be pruned after at least 24 hours (API v1) | https://docs.stripe.com/api/idempotent_requests | verified |
| Stripe engineering blog on webhook infra | Post exists (stripe.dev), body not retrieved | https://stripe.dev/blog/topic/event%20destinations | unverified |
| Standard Webhooks headers | `webhook-id`, `webhook-timestamp`, `webhook-signature` | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md | verified |
| Standard Webhooks signed content | `msg_id.timestamp.payload` | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md | verified |
| Standard Webhooks signature scheme | HMAC-SHA256, `v1,<base64>`, space-delimited list | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md | verified |
| Standard Webhooks tolerance | "Some allowable tolerance". No 5-minute value in spec | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md | verified |
| Standard Webhooks retry | Guidance: multi-day schedule, exponential backoff, jitter. Example only | https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md | verified |
| Svix retry schedule | Immediate, 5 s, 5 min, 30 min, 2 h, 5 h, 10 h, 10 h (8 attempts) | https://docs.svix.com/retries | verified |
| Svix total retry span | About 27.5 hours (summed from schedule) | https://docs.svix.com/retries | verified (calculated) |
| Svix endpoint disable rule | Disabled if all attempts fail for 5 days | https://docs.svix.com/retries | verified |
| Svix response timeout | 30 s ("within a reasonable time-frame (30s with Svix)") | https://docs.svix.com/retries | verified |
| Svix non-2xx handling | Any non-2xx, including 3xx, is a failure | https://docs.svix.com/retries | verified |
| Svix free-tier volume | 50,000 messages/month included, then $0.0001 per message | https://svix.com/pricing | secondary (pricing page seen via search summary) |
| GitHub webhook timeout | 10 seconds | https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries | verified |
| GitHub auto-redelivery | None ("GitHub does not automatically redeliver failed deliveries") | https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries | verified |
| GitHub redelivery window | Not on page | https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries | unverified |
| GitHub payload cap | Not on page | https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries | unverified |
| Shopify timeout | 1 s connect, 5 s total | https://shopify.dev/docs/apps/build/webhooks/subscribe/https | verified |
| Shopify retries | 8 times over the next 4 hours | https://shopify.dev/docs/apps/build/webhooks/subscribe/https | verified |
| Shopify subscription removal | Deleted after 8 consecutive failures (Admin API subscriptions) | https://shopify.dev/docs/apps/build/webhooks/subscribe/https | verified |
| Shopify "billions of webhooks" | No primary source found | https://shopify.dev/docs/apps/build/webhooks/subscribe/https | unverified |
| Slack response requirement | 2xx within three seconds | https://docs.slack.dev/apis/events-api/ | verified |
| Slack retries | Three retries: near immediate, 1 min, 5 min. Header `x-slack-retry-num` | https://docs.slack.dev/apis/events-api/ | verified |
| Slack disable rule | Disabled if more than 95% of attempts fail within 60 minutes | https://docs.slack.dev/apis/events-api/ | verified |
| Twilio timeout and retries | Configurable via Webhooks API. Defaults not on page | https://www.twilio.com/docs/usage/webhooks/webhooks-overview | unverified |
| PayPal webhook retry and timeout | Not checked | n/a | unverified |
| Adyen webhook retry and timeout | Not checked | n/a | unverified |
| AWS EventBridge retry window | 24 hours (default for event buses) | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html | verified |
| AWS EventBridge max retries | 185 (default for event buses) | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html | verified |
| AWS EventBridge timeout | 5 seconds client execution timeout | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html | verified |
| AWS EventBridge retry codes | Retries 401, 407, 409, 429, 5xx. Does not retry other 4xx | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html | verified |
| AWS EventBridge per-destination rate limit | Invocation rate is user-set. No default limit found | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html | unverified |
| AWS IMDS address | 169.254.169.254 | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html | verified |
| IMDSv2 session token | PUT to `/latest/api/token`, TTL up to 21,600 s. Token required when set to required | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html | verified |
| IMDSv2 hop limit | Default response hop limit of 1. PUT rejected with X-Forwarded-For | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html | verified |
| DNS rebinding | Allowlist by domain alone does not stop it | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | verified |
| Resolve-validate-connect | Validate resolved IP, connect only to that IP, keep Host and SNI | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | verified |
| Redirect handling for SSRF | Disable redirect following in the client | https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html | verified |
| Stripe event volume | No public figure found | n/a | unverified |
| Svix or Hookdeck volume | No platform-wide total found | https://svix.com/pricing | unverified |

## Stripe Quotes

- Retries: "Stripe attempts to deliver events to your destination for up to three days with an exponential backoff in live mode." Sandbox: "We retry event deliveries created in a sandbox three times over the course of a few hours." (https://docs.stripe.com/webhooks)
- Success and speed: "Quickly returns a successful status code (`2xx`) before any complex logic that might cause a timeout." (https://docs.stripe.com/webhooks)
- Redirects: "We consider redirect responses to webhook requests as failures." (https://docs.stripe.com/events/manage-webhook-endpoints)
- Signature header: "The timestamp has a `t=` prefix, and each signature has a *scheme* prefix." Test events add a fake v0. "To prevent downgrade attacks, ignore all schemes that aren't `v1`." (https://docs.stripe.com/webhooks)
- Tolerance: "Our libraries have a default tolerance of 5 minutes between the timestamp and the current time." (https://docs.stripe.com/webhooks)
- Rotation: "You can have multiple signatures with the same scheme-secret pair when you roll an endpoint's secret, and keep the previous secret active for up to 24 hours." (https://docs.stripe.com/webhooks)
- Retry signatures: "If Stripe retries an event ... then we generate a new signature and timestamp for the new delivery attempt." (https://docs.stripe.com/webhooks)
- Ordering: "Stripe doesn't guarantee the delivery of events in the order that they're generated." (https://docs.stripe.com/webhooks)
- Duplicates: "Webhook endpoints might occasionally receive the same event more than once." (https://docs.stripe.com/webhooks)
- Timestamps: "Snapshot events record `created` in seconds, so distinct events can share a timestamp. Don't use `created` to determine event order." (https://docs.stripe.com/webhooks)
- Manual resend: "In the Stripe Dashboard, click **Resend** ... This works for up to 15 days after the event creation." CLI: "This works for up to 30 days after the event creation." (https://docs.stripe.com/webhooks)
- Listing window: "Stripe only returns events created in the last 30 days." (https://docs.stripe.com/events/manage-webhook-endpoints)
- Destinations: "You can register up to 16 event destinations with Stripe." (https://docs.stripe.com/webhooks)
- IPs: "Stripe sends webhook events from a set list of IP addresses." Changes: "We provide seven days' notice through that mailing list before making changes." (https://docs.stripe.com/ips)
- TLS: "Stripe webhooks support only TLS versions v1.2 and v1.3." (https://docs.stripe.com/webhooks)
- Idempotency: "you can remove keys from the system automatically after they're at least 24 hours old." (https://docs.stripe.com/api/idempotent_requests)
- Smokescreen: "Smokescreen is a HTTP CONNECT proxy." It "also resolves each domain name that is requested, and ensures that it is a publicly routable IP address." (https://github.com/stripe/smokescreen)

## Comparison Quotes

- Svix retries: "If all attempts to a specific endpoint fail for a period of 5 days, the endpoint will be disabled." Timeout: "within a reasonable time-frame (30s with Svix)." (https://docs.svix.com/retries)
- GitHub: "GitHub does not automatically redeliver failed deliveries." Timeout: "takes longer than 10 seconds to respond." (https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries)
- Shopify: "it retries 8 times over the next 4 hours." "After 8 consecutive failures, the subscription is automatically deleted if it was configured using the Admin API." (https://shopify.dev/docs/apps/build/webhooks/subscribe/https)
- Slack: "Your app should respond to the event request with an HTTP 2xx within three seconds." "more than 95% of delivery attempts within 60 minutes, your application's event subscriptions will be temporarily disabled." (https://docs.slack.dev/apis/events-api/)
- EventBridge: "EventBridge requests to an API destination endpoint must have a maximum client execution timeout of 5 seconds." "For event buses, by default the maximums are 24 hours and 185 times." (https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-api-destinations.html)
- Standard Webhooks: "It's recommended to retry delivery following a retry schedule spanning multiple days, with an exponential backoff." (https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md)

## SSRF and Egress Quotes

- IMDS: the instance metadata endpoint is `169.254.169.254`. IMDSv2 "PUT request ... returns a token that must be included in subsequent GET requests." (https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
- DNS rebinding: "Domain allowlisting alone does not prevent DNS rebinding." "A second, unchecked DNS lookup between validation and connection can bypass these checks." (https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- OWASP connect step: "ensure the HTTP client connects only to validated addresses." (same URL)

## Assumption Check (user estimates)

| Assumption | Result |
|------------|--------|
| 3-day retry | Matches Stripe live mode ("up to three days"). Svix is about 27.5 hours. Standard Webhooks suggests multi-day. |
| 5-minute tolerance | Matches Stripe default. Standard Webhooks sets no value. |
| 30 s timeout | Matches Svix (30 s). Stripe publishes no value. Third-party posts say about 20 s. GitHub is 10 s, Slack 3 s, Shopify 5 s. |
| ~1M endpoints | Not verified. No source. |
| ~500M deliveries/day | Not verified. No source. |

## Could not verify

- Stripe endpoint timeout value. Only third-party sources (about 20 s) found.
- Stripe rule for disabling an endpoint and the merchant notification emails (number of days).
- Stripe exact retry intervals (only "exponential backoff" is documented).
- Stripe engineering blog body text on webhook infrastructure (stripe.dev post exists, body not fetched).
- Stripe event volume figures.
- Shopify "billions of webhooks" claim. No primary source. Shopify community posts show spikes of 2 million events in 1.5 hours, which is anecdotal.
- GitHub redelivery window (3 days) and 25 MB payload cap. Not on the fetched page.
- Twilio retry count and default timeout.
- PayPal and Adyen webhook retry and timeout behavior. Not checked.
- EventBridge default per-destination rate limit.
- Svix total platform volume. Only pricing is public.
- Svix chunking rule: the pricing page says 256 KiB chunks, and a third-party teardown says 64 KiB. Conflict, not resolved.
