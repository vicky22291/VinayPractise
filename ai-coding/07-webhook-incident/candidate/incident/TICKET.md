# INC-2291: merchant webhook escalation (Sev 2)

Opened 2026-10-14 13:40 UTC by Merchant Support. Assigned to: on-call (you).

Three escalations arrived today, all about webhooks. The dispatcher log for
09:00 to 13:30 UTC is in `dispatcher.log` next to this file.

---

**1. Lumen Books (`acct_1Lumen`)**

> We dedupe webhooks on the event `id`, as your docs say. This morning we
> shipped two orders more than once. For charge `ch_3Q00017` we received
> `charge.succeeded` four times, with ids `whd_000157`, `whd_000163`,
> `whd_000172` and `whd_000197`. Our app was slow between about 10:40 and 11:00,
> but every request was processed.

**2. Café Olé (`acct_1CafeOle`) and Müller Fahrräder (`acct_1Muller`)**

> Signature verification fails on most `charge.succeeded` events.
> `payout.paid` and `payment_intent.succeeded` verify fine with the same secret.
> We use your SDK and pass the raw request body. We rotated the secret twice
> and nothing changed.

**3. Northwind Supplies (`acct_1Northwind`)**

> Our server was down from 10:05 to 12:05 UTC for a database migration. Your
> docs promise retries for up to three days, but many events from that window
> never arrived.

---

Notes from the on-call channel:

- `hooks-dispatcher` 1.4.0 rolled out on 2026-10-13 at 16:20 UTC. Release
  note: "Payloads are now compact UTF-8 JSON (about 15% smaller)."
- No other dispatcher deploys in the last 30 days.
