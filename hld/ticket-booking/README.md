# Hotel booking: search, reserve, partner ARI, last room

> One-line answer: hotel metadata and a coarse "sold out on these nights" signal live in Elasticsearch for geo search, exact remaining counts and prices come from a CDC-fed Redis cache, and inventory is counted per **room type per night** in Postgres sharded by `hotel_id`, where one conditional `UPDATE` across every night of the stay decides who gets the last room. Partner ARI (availability, rates, inventory) arrives by push, pull, or our extranet, is normalized into one canonical event, and is applied in order with a per-night sequence guard. Booking is a saga: hold, authorize, partner confirms (the pivot), capture.

Tier 3, problem #25 in [`hld/README.md`](../README.md) ("Global ticket / hotel booking"). This folder solves the **hotel** variant. Reported at Rippling (hotel reservation, 2 candidate posts plus PracHub pages), Google, and Airbnb. Problem source: [Hello Interview: Hotel Booking System](https://www.hellointerview.com/community/questions/hotel-booking-system/cm80nptng04jg2pu4cq8rpxzm) (only the statement is public: search, reserve, manage bookings, with a focus on data modeling and SQL for availability, pricing, and reservations).

## Problem statement

> Focus on ability to ingest, search and reserve rooms. Booking service: booking flow, booking states (reserved, pending, confirmed), locking mechanism. Search service: search by location and date. Storing metadata (100k hotels, 1000 rooms per hotel): better go by room type (AC, suite, deluxe) to avoid storing a lot of metadata, because each hotel has only a few room types. Search by geo location. API adaptors from hotel partners who push data to us vs where we pull data from hotels. Hotels include large chains as well as small hotels. SQL vs NoSQL trade-offs. Push vs pull trade-offs. Detailed data modeling for each service. APIs. Monitoring and security. Observability. Data freshness and consistency issues because data is not accurate when it comes from hotel partners: how will you solve it? Concurrency in booking the last available room when it is available on multiple platforms (the last-room problem). Data freshness and consistency, overbooking.

## Functional requirements

Core:
- Search hotels near a place (point + radius, map viewport, city) for given dates and guests, with filters.
- Show a hotel's room types and rate plans with exact prices for the stay.
- Hold a room type for every night of the stay without overselling.
- Pay, get a confirmation from the hotel, and cancel per policy.
- Ingest ARI from partners (push, pull, extranet) and deliver our bookings back to them.

Below the line (say it out loud):
- Reviews, loyalty, ML ranking, personalization, flights and packages.
- Revenue management. Hotels set prices, we do not.
- Physical room assignment. Done at check-in.
- Hotel onboarding, KYC, contracts.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 100k hotels, ~5 room types each, 100M physical rooms. 500k bookings/day (~60/s peak). ~6k search QPS peak. ~1.2k partner ARI messages/s peak |
| Latency | Search p99 < 500 ms. Hotel page p99 < 300 ms. Hold p99 < 300 ms local, < 3 s with a chain live check |
| Availability | Booking path 99.95%. Search 99.9%. Ingestion may lag, never drops a message |
| Consistency | Strong for the hold decision. Eventual for search (≤ 2 min) and prices (≤ 5 s). Read-your-writes for "my booking" |
| Correctness | Oversell (we confirm, hotel has no room) < 0.01% of bookings |
| Freshness | Partner change to bookable p99 < 10 s (push) |
| Durability | Zero confirmed-booking loss (RPO 0). RTO 15 min per shard |
| Security | No card data in our systems. Signed partner traffic. Bots cannot hoard holds |

## Interview clock (60 min)

| Min | Block | Lands on |
|---|---|---|
| 0-5 | Clarify, FRs, NFRs | "We are one channel among many. That is why the last room is contested." |
| 5-12 | Back-of-envelope | "Partner ARI writes are ~200x booking writes." |
| 12-22 | Data model + DB design | Room type per night. Shard by `hotel_id`. |
| 22-37 | Components, APIs, deep dive | Final design diagram, then the last-room SQL. |
| 37-45 | SQL vs NoSQL, push vs pull | Trade-off table. |
| 45-50 | E2E booking + payment | Saga with partner confirm as the pivot. |
| 50-60 | Scale, monitoring, security | Red nodes, SLOs, hold hoarding. |

## What interviewers probe

1. Why room type per night and not physical room? Show the row count.
2. Two users click Book on the last room at the same instant. Show the SQL.
3. The same room is on three other sites. How do you not sell it twice? What if you still do?
4. Reserved, pending, confirmed: what does each state mean and what moves it?
5. Payment succeeds 30 s after the hold expired. What now?
6. Partners push or you pull. Which, for whom, and why?
7. A partner sends updates out of order, or sends garbage. How do you notice and what do you do?
8. Search is minutes stale but the price must be right. How?
9. SQL or NoSQL for inventory, bookings, search, catalog?
10. A big chain's reservation system is down on New Year's Eve. What happens?
11. What pages someone at 3 am?

## Files

[`solution.md`](solution.md) · [`diagrams.md`](diagrams.md) · [`edge-cases.md`](edge-cases.md) · deep dives: [last room and inventory locking](deep-dives/last-room-and-inventory-locking.md), [partner ingestion push vs pull](deep-dives/partner-ingestion-push-vs-pull.md), [geo search and availability](deep-dives/geo-search-and-availability.md), [booking saga and payment](deep-dives/booking-saga-and-payment.md)
