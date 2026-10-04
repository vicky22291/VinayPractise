# TurboTax e-file submission at the April 15 peak

> One-line answer: the deadline is met when **we** durably accept and postmark the return, not when the IRS receives it. So the File click writes the return, its electronic postmark (stamped by the gateway in a signed receipt token that a retry replays) and a pre-minted **submission ID** to a durable store in one transaction and answers in under 2 s, at up to 50x the season's average rate. A separate transmitter drains that store to IRS MeF (Modernized e-File) at whatever rate MeF accepts. Every retry of a send reuses the same submission ID, and an unknown outcome is resolved by asking MeF for that ID's status, never by minting a new one. An ack reconciler polls for acknowledgments, matches each one to its submission ID, notifies the filer, and a sweeper pages a human if any submission has no ack after its SLA. The thing that breaks first is the MeF channel itself (external, slow at peak), so nothing on the accept path waits on it.

Tier 3, problem #49 in [`hld/README.md`](../README.md). From the user's Intuit Principal / Staff practice list (2026-10). Not a reported candidate prompt. The closest reported Intuit prompt is "design a service that provides tax refund status" ([#45](../README.md), the read side after an IRS accept). Scale facts: [`../company-questions.md`](../company-questions.md) §1.5 and [`research/`](research/).

## Problem statement (as asked)

TurboTax e-file submission at the April 15 peak. Crux: exactly-once submission to the IRS and acknowledgment reconciliation under a 20 to 50x deadline spike.

Follow-ups that always come: what "on time" means when the IRS is slow at 11:58 PM; a timeout on the send call; how you know every return got an answer; a reject at 1 AM on April 16; state returns that depend on the federal one; the IRS being down for two hours on deadline day.

## Functional requirements

Core:
- **File.** The filer clicks File on a federal return (and usually one or more state returns). We validate it, postmark it, and confirm "received" in under 2 s.
- **Transmit.** Package submissions into MeF messages and send each one to the IRS exactly once, per submission ID. State returns go through the same MeF Fed/State channel.
- **Acknowledge.** Retrieve every IRS and state acknowledgment (Accepted, Rejected, or Exception for the 1040 family), update the return's status, notify the filer (accepted, or rejected with the reason).
- **Fix and resubmit.** A rejected return can be corrected and resubmitted inside the perfection period and still count as filed on time.

Below the line: computing the tax, refund status after acceptance ([#45](../README.md)), paying a balance due, identity checks (IP PIN, identity protection PIN), paper filing, extensions (Form 4868 uses the same pipeline).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~45 M federal and ~35 M state submissions per season [estimate]. Season average ~10 submissions/s. Deadline evening peak ~500/s (50x), designed for 1,000/s at the accept path. The deadline is midnight in the filer's own time zone, so the peak comes in waves (almost all load in the 6 US zones) |
| Accept latency | File click to "received": p99 under 2 s at peak |
| Availability | 99.99% of File clicks postmarked at their first click (a gateway-signed receipt token keeps the postmark across a retry); 99.9% answered within 2 s. Freeze and pre-scale from April 1. The accept path must not depend on MeF being up |
| Durability | Zero lost returns. A return is durable (replicated across availability zones) before we say "received" |
| Exactly-once | One submission ID per filing attempt, minted before the first send. Never two IRS submissions for one attempt. Never a new ID while the old one's outcome is unknown |
| Transmit deadline | Every postmarked return received by the IRS within 2 days of the postmark. This is a condition of timely filing for the filer (Pub 4164 §1.5.3), not only a transmitter rule (Pub 1345). Target: 99% within 1 h, all within 24 h, even on April 15. Floor: 3 M deadline-day returns in 48 h is ~17/s |
| Ack freshness | Filer notified within 5 min of the ack being available at MeF, p99, off-peak; within 30 min in the deadline week (polling every outstanding id faster would need ~11 more ack ASIDs and barely changes legal outcomes). Every submission acked or escalated within 48 h |
| Security | Return data is taxpayer data under IRC section 7216. Encrypted at rest and in transit. Access logged |

## What interviewers probe (the ladder)

1. The IRS is slow at 11:58 PM on April 15. Is the filer late? What exactly makes a return timely?
2. `SendSubmissions` times out. Did the IRS get it? Do you resend with the same submission ID or a new one? What does the IRS do with each?
3. How do you know every one of 3 M deadline-day submissions got an ack? What pages someone at 2 AM on April 16?
4. A return is rejected at 1 AM on April 16 for a mistyped dependent SSN. Is the filer late? What do you store to prove it?
5. A linked state return can only go once the federal one is accepted (MeF denies it otherwise). How do you model that, and when would you send it unlinked?
6. 50x traffic in 3 hours. What do you pre-scale, what do you shed, and what can never be shed?
7. MeF is down for 2 hours on April 15. What do filers see, and what happens when it comes back?

## Files

| File | What it is |
|---|---|
| [`solution.md`](solution.md) | Full HLD in flow-first form: one incremental diagram, one walkthrough per FR, deep dives that mutate the design, then nitty-gritty |
| [`diagrams.md`](diagrams.md) | The D1 to D12 diagram set |
| [`edge-cases.md`](edge-cases.md) | Every "what if" with a 60-second answer and a confidence box |
| [`deep-dives/postmark-and-peak-intake.md`](deep-dives/postmark-and-peak-intake.md) | Timely filing, the electronic postmark, the accept path at 50x, pre-scaling, what is shed and what is never shed |
| [`deep-dives/exactly-once-submission.md`](deep-dives/exactly-once-submission.md) | Submission ID minting, the send state machine, unknown outcomes, IRS duplicate rules |
| [`deep-dives/ack-reconciliation.md`](deep-dives/ack-reconciliation.md) | Ack polling, matching, the sweeper, ack lag SLOs, notifications |
| [`deep-dives/irs-outage-and-backpressure.md`](deep-dives/irs-outage-and-backpressure.md) | MeF slow or down, transmit rate control, draining the backlog without a storm |
| [`deep-dives/reject-fix-resubmit-and-state-returns.md`](deep-dives/reject-fix-resubmit-and-state-returns.md) | The perfection period, resubmission lineage, linked state returns |
| [`research/`](research/) | Raw web research notes with source links. Input to the files above, not study material |
| `turbotax-efile.excalidraw` | My drawing. Missing until I draw it |
