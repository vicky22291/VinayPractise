# Warehouse management system (WMS) for a fulfillment network

> One-line answer: each fulfillment center is its own cell, with one inventory database that is the single writer for every bin in that building. Stock is a movement ledger (received, put away, allocated, picked, packed, shipped, adjusted) plus per-bin balances updated in the same transaction, so counts never go negative and every unit has an audit trail. Scanners send idempotent, sequence-numbered events and keep working through Wi-Fi gaps. Orders arrive from commerce, are allocated to bins in per-SKU lanes, released continuously by how much slack each has before its truck, and walked through receive, put away, pick, pack and ship as state machines with humans in the loop. Every change to sellable stock goes out through an outbox to the commerce site within seconds, and a reconciliation job proves the two sides agree. QPS is small, so the red node is not the database: it is the pick floor before the midnight cut-off (~375 pickers in the 23:00 hour with ~15 minutes of slack). The hard parts are short picks, offline scanners, a building's network cut, and keeping commerce's view exact.

Status: **studied** (solution, diagrams, edge cases, 6 deep dives with runnable simulations, facts survey). Missing: `my-attempt.md` and my excalidraw.

Tier 3, problem #62 in [`hld/README.md`](../README.md). Reported at Coupang for Staff (1 Staff report on Hello Interview's community board, mid October 2026), also seen at Amazon and Procore. The candidate's note says the round focused on keeping warehouse inventory updated in real time as shipments and order updates happen. Related: [`../ecommerce-platform/`](../ecommerce-platform/) (#61, sellable stock and reservations), [`../document-approval-system/`](../document-approval-system/) (task claiming, humans as the capacity limit), [`../distributed-job-scheduler/`](../distributed-job-scheduler/), [`../../concepts/temporal-durable-execution.md`](../../concepts/temporal-durable-execution.md), [`../../concepts/stream-processing.md`](../../concepts/stream-processing.md), [`../../concepts/sharding.md`](../../concepts/sharding.md).

## Problem statement (as reported, paraphrased)

Design a warehouse management system: inventory tracking, order fulfillment and warehouse operations, so that storage and distribution run efficiently. The reported round focused on real-time inventory: every shipment and every order update must change inventory right away.

Scoping questions to ask in the first 5 minutes:
- **One warehouse or a network?** A network of ~100 fulfillment centers, each with its own staff and scanners. Coupang reports 100+ logistics centers in 30+ regions and over 78M sq ft of space ([facts survey](research/facts-survey.md)).
- **Who is the truth for stock?** The WMS owns physical stock per bin. The commerce site (#61) owns sellable stock and buyer reservations, fed by WMS events.
- **What is the delivery promise?** For dawn delivery: order by midnight, at the door by 7 am (Coupang FY2024 10-K). That deadline drives pick-wave timing. A center that hits its daily outbound capacity stops accepting new orders (Coupang engineering blog).
- **Robots?** Out of scope. We send tasks to people with handheld scanners. A robot fleet would consume the same task API.

## Functional requirements

Core:
1. **Track inventory.** Stock per bin location and per state (available, allocated, picked, packed, shipped, damaged), with lot and expiry where the product needs it. Cycle counts and adjustments.
2. **Inbound.** Receive a shipment against its advance shipping notice (ASN) or purchase order, inspect it, and put each unit away in a directed bin.
3. **Outbound.** Take orders from commerce, allocate stock to bins, release pick waves to scanners, confirm picks, pack, label and hand off to delivery.
4. **Real-time visibility.** Every receipt, short pick, damage, adjustment and cancel that changes sellable stock reaches the commerce site within seconds. Every physical step (allocate, pick, pack, ship) updates the order's status there. Dashboards show work and exceptions live.

Below the line: robot fleet control, labor management and payroll, slotting optimization models, last-mile routing, 3PL billing, demand forecasting and transfers between centers (named as a seam only).

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | ~100 centers. A large center holds ~1M bin locations and ~500k SKUs, ships ~500k units on a peak day and runs ~2,000 scanners [estimate]. Network ~5M units shipped a day [estimate; Coupang publishes no per-day figure] |
| Event rate | ~5 scans per unit shipped: ~25M scans a day, ~300 a second on average, ~3k a second at the network peak, at most ~300 a second in the busiest center (bounded by handhelds in use; the midnight outbound peak is ~50 a second) [estimate] |
| Scan latency | Scans that need a server decision (put-away bin, short, unknown barcode): p99 under 300 ms. Scans that confirm a planned task step: confirmed on the handheld in under 100 ms and applied on the server in device order. A worker waits on every scan |
| Freshness | A physical change reaches sellable stock on the commerce site within 2 s, p99 |
| Correctness | A bin balance never goes negative. No unit is allocated to two orders. No scan is applied twice. Every movement is in an append-only ledger kept for 2 years [estimate] |
| Deadline | Dawn orders received up to midnight leave on the last truck at ~02:00: last pick by ~00:40, last batch released by ~00:15 [estimate] |
| Availability | Each center is an isolated cell: one center's failure never stops another. A center keeps picking through ~40 minutes of network loss on work already released to it |

## What interviewers probe

1. Two pick waves and a cycle count touch the same bin at once. How do the counts stay exact?
2. An order is placed at 23:59 for next-morning delivery. Walk it to the truck. Where is the time spent, and what is the real bottleneck?
3. A picker reaches a bin and it is empty (short pick). What happens to the order, the bin record, and availability on the website?
4. A scanner loses Wi-Fi in an aisle and sends 30 scans late. How do you handle duplicates and ordering?
5. Commerce says 5 units are sellable, the warehouse says 3. Who is right, how fast do they converge, and how do you prove they agree?

## Files

[`solution.md`](solution.md) · [`diagrams.md`](diagrams.md) · [`edge-cases.md`](edge-cases.md) · deep dives: [inventory ledger and bin model](deep-dives/inventory-ledger-and-bin-model.md), [allocation waves and short picks](deep-dives/allocation-waves-and-short-picks.md), [workflow orchestration and tasks](deep-dives/workflow-orchestration-and-tasks.md), [scanners offline and idempotency](deep-dives/scanners-offline-and-idempotency.md), [realtime sync to commerce](deep-dives/realtime-sync-to-commerce.md), [cutoff and capacity](deep-dives/cutoff-and-capacity.md) · research: [facts survey](research/facts-survey.md) · missing: `warehouse-management.excalidraw` (mine to draw), `my-attempt.md`
