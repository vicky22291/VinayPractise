# Superhero dispatch: exactly one hero per emergency

> Status: **todo**. Registered 2026-10-08 so a later session can build the full set. The crux: ride-hailing dispatch at low volume, where a dropped or double-assigned emergency is the worst failure. One conditional write decides the winner of the accept race. Live location lives in a fast, lossy index that is never trusted at commit time.

Tier 3, problem #57 in [`hld/README.md`](../README.md). Reported at **Stripe**, 2 onsite design rounds in 2026, both rejected:

- **L3, May 2026.** The candidate was "completely unprepared for this one". It was "Kind of like Uber, except the dispatch traffic wouldn't be nearly as crazy as Uber's, and this design didn't involve any API design at all". Feedback: "my justification for the technology choices wasn't strong enough" ([PracHub write-up](https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-five-onsite-rounds-including-a-superhero-dispatch-system)).
- **Feb 2026, level not stated.** The write-up is titled "Rejected on a Surprise System Design Question" and is locked ([PracHub question](https://prachub.com/interview-questions/design-a-superhero-incident-dispatch-system)).

Evidence and the rest of the Stripe loop: [`../company-questions.md` §3](../company-questions.md#3-stripe-staff-l4). Related: [`../uber-ride-hailing/`](../uber-ride-hailing/) (my attempt only), [`../payments-ledger/`](../payments-ledger/) for idempotency, [`../../concepts/geospatial-index.md`](../../concepts/geospatial-index.md), [`../../concepts/leases-fencing-clocks.md`](../../concepts/leases-fencing-clocks.md).

## Problem statement (as given)

From the [PracHub question page](https://prachub.com/interview-questions/design-a-superhero-dispatch-system) (captured 2026-10-08; PracHub's write-up of the May 2026 round):

> Design the backend for a **superhero rescue marketplace**, a dispatch platform that connects civilians in distress with nearby superheroes. Civilians report emergencies (accidents, fires, crimes). For each report the platform must create a **rescue request**, identify appropriate nearby superheroes, notify them, let **exactly one** hero accept the request and travel to the incident, and let dispatchers monitor request status end to end. The problem is structurally similar to ride-hailing dispatch (Uber/Lyft), but with two important differences: request volume is far **lower** than a major ride-sharing platform, and **reliability matters more than maximizing throughput**. A dropped or double-assigned emergency is a much worse failure than a dropped ride request.
>
> Focus on **system architecture and technical tradeoffs**, not on REST/RPC endpoint design. The interviewer's primary signal is the strength of your *justification* for each technology and consistency choice.

The page asks the design to cover: requirements; the main services and the storage for each; the data model for civilians, heroes, incidents, offers and assignments; tracking hero location and availability and querying it by radius; matching and dispatch logic; the incident state machine; concurrency control for the accept race; notifications, offer timeouts, retries and failure handling; observability.

## Functional requirements

Core:
1. A civilian reports an incident. It is stored durably and dispatch starts. Neither can happen without the other.
2. Find suitable heroes near the incident and send offers.
3. Exactly one hero accepts. Every other hero learns that they lost.
4. The incident moves through a validated state machine to a terminal state, including timeout, decline, cancel, hero drop-off and no hero found.
5. Dispatchers watch every incident live and can override, cancel or reassign.

Below the line (the page calls these extensions): multi-hero incidents, travel-time ETA instead of a straight-line radius, ML ranking of heroes, escalation to SMS or voice.

## Non-functional requirements

Working numbers from the prompt page ("state your own numbers, but a reasonable working set is"):

| Dimension | Target |
|---|---|
| Users | ~1,000,000 registered civilians. ~10,000 heroes on duty in one large metro |
| Incident rate | Peak ~500 new incidents a minute metro-wide (~8 a second). "Write-light but correctness-critical" |
| Location pings | Every 5 to 15 s per on-duty hero: ~670 to 2,000 pings a second at 10,000 heroes |
| Latency | Time to first offer: low single-digit seconds. Offer window: ~10 to 20 s |
| Correctness | **A single-hero incident is assigned to at most one hero**, even under concurrent accepts and partial failure. No incident is persisted without dispatch starting |
| Consistency | Strong for the final assignment. Eventual for live location, dashboards and analytics |

## What interviewers probe

1. Two heroes tap "accept" at the same instant. What single operation lets only one win, which component enforces it, and how does the loser find out?
2. The incident row commits but the "start dispatching" message is lost. How do the two side effects share one fate (outbox, or a log as the source of truth)?
3. Where does live location live, and why is it not the store you trust when you commit an assignment?
4. The assigned hero stops sending heartbeats mid-rescue. How do you detect it and reassign without double-dispatching?
5. A disaster sends a 50x burst into one neighbourhood. What degrades first?
6. For every box: why this technology and not the obvious alternative? (This is the stated grading signal.)

## Files

| File | What it is |
|---|---|
| `solution.md` | Not written yet |
| `diagrams.md` | Not written yet |
| `edge-cases.md` | Not written yet |
| `deep-dives/` | Planned: accept race and assignment store, outbox and reliable dispatch start, location index vs truth, offer strategy and timeouts, incident state machine and stuck-incident detection |
| `superhero-dispatch.excalidraw` | My drawing. Missing until I draw it |
