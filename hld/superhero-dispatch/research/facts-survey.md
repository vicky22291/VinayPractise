# Superhero dispatch: facts survey

Raw research notes with source links. Input to the HLD files, not study material.

Capture date: 2026-10-22

Method: web search for each topic, then WebFetch on primary pages where they loaded. Items marked [unverified] come from tutorials, blogs, search snippets, or my own derivation. Check them before quoting in an interview.

---

## 1. Real ride-hailing dispatch (Uber, Lyft, DoorDash)

- Uber built H3, a hexagonal grid, for "efficiently optimizing ride pricing and dispatch." Source: https://uber.com/blog/h3/ (search snippet, not fetched).
- Uber's own DISCO and Ringpop posts were not found. A tutorial says DISCO shards the map with S2 cells and routes cells to workers by consistent hashing. [unverified] Source: https://www.techinterview.org/post/3233476891/design-ride-hailing-system/
- Uber driver location ping: tutorials use about 4 s, with a 2 to 5 s range. Stale after 15 s. [unverified] Source: https://codemia.io/system-design/design-uber-backend/submissions/pnjn011c
- Uber offer window: older window was about 10 s per an anecdotal driver blog. Pilots reportedly extended it to about 15 s in some cities. [unverified] Source: https://therideshareguy.com/uber-extends-offer-acceptance-time-ping-for-drivers/
- Lyft runs batch matching every few seconds, per Lyft's arXiv paper on RL matching. Source: https://arxiv.org/pdf/2310.13810
- Lyft's paper reports a greedy approach increased combined rider wait plus driver navigation from 8 to 12 minutes (50%). Source: https://arxiv.org/pdf/2310.13810
- Lyft batching window in seconds was not found. Lyft's blog says the matching graph is regenerated "at frequent intervals." Source: https://eng.lyft.com/solving-dispatch-in-a-ridesharing-problem-space-821d9606c3ff
- Lyft patent US 11,625,652 covers matching "over extended batching windows." Durations not confirmed. Source: https://patents.google.com/patent/US11625652
- DoorDash dispatch goals: offer to Dashers efficiently, and deliver on time. Source: https://careers.doordash.com/?p=5342 (attributed to Alex Weinstein and Jianzhe Luo via secondary sources).
- DoorDash Dasher selection: proximity to the store matters most, then timing, then batching. Source: same DoorDash post (secondary summary).
- DeepRed: secondary sources say it pairs ML prediction with mixed integer programming (MIP) optimization. [unverified] Source: https://careers.doordash.com/?p=5342
- DoorDash 2020 talk: ML predicts demand and supply, and MIP solves the matching. Source: https://developer.download.nvidia.com/video/gputechconf/gtc/2020/presentations/s22191-how-machine-learning-powers-on-demand-logistics-at-doordash.pdf
- Cadence was built at Uber by Maxim Fateev and Samar Abbas. Temporal was later forked from it. Source: https://softwareengineeringdaily.com/2020/04/08/cadence-ubers-workflow-engine-with-maxim-fateev/
- Uber's Cadence overview says Cadence provides persistence, queue, and timer infrastructure so engineers focus on business logic. Source: https://www.uber.com/blog/open-source-orchestration-tool-cadence-overview
- Cadence architecture: front end, history, and matching services on a Cassandra back end. Source: same Uber Cadence overview.
- Dispatch matching is described as needing sub-100 ms latency. [unverified] Source: https://theheuristicreport.beehiiv.com/p/how-uber-built-temporal-and-why-it-s-the-future-of-distributed-systems

---

## 2. Emergency dispatch (CAD) and 911

### Response-time standards
- NFPA 1710 turnout target: 80 s for fire and special operations, 60 s for EMS, at least 90% of the time. Source (one of several city reports, exact source not confirmed): https://hanfordca.gov/DocumentCenter/View/1010/Monthly-Report---March-2023-PDF
- Call processing target: 60 s at 90% of alarms. Quoted from NFPA 1221 text in a Toronto briefing. Source: https://www.toronto.ca/legdocs/mmis/2012/ex/bgrd/backgroundfile-44192.pdf
- Newer NFPA 1710 edition lists call processing at 64 s (90%) and 106 s (95%). Editions conflict, so name the edition in an interview. Source: https://www.murrietaca.gov/Archive.aspx?ADID=363
- NFPA benchmarks are standards that a department can adopt. They are not law by themselves. Source: https://unifiedfireut.gov/wp-content/uploads/manual/Cottonwood%20Heights%20CRA_SOC_Draft.pdf [unverified exact wording]

### CAD recommendation, AVL, unit status
- AVL (automatic vehicle location) feeds unit positions to CAD. Closest-unit recommendation and unit status models (available, dispatched, en route, on scene): [unverified] not researched in this session. Gap.

### Outages (dated)
- CenturyLink outage began Dec 27, 2018 and lasted about 37 hours. FCC blamed equipment failure made worse by a network configuration error. Source: https://www.npr.org/2018/12/28/680747866/fcc-investigates-widespread-centurylink-outage-that-disrupted-911-service
- FCC report released around Aug 2019. Source: https://www.theregister.com/2019/08/20/centurylink_outage_report_fcc/
- FCC report: at least 886 911 calls were not delivered. FCC knew of no harm to life or property. Source (secondary summary of FCC report): https://benton.org/node/307372
- Outage reached about 22 million customers in 39 states. About 17 million lacked reliable 911 access. Source: https://benton.org/node/307372
- Bucks County, PA, Jan 2024: CAD went down. Officials believed a cyberattack was the cause (unconfirmed). Dispatchers used pen and paper. Source (likely match, not confirmed): https://levittownnow.com/2024/01/22/county-computer-aided-dispatch-system-out-of-service/
- Houston, March 2024: power disruption during electrical upgrades crashed parts of CAD. Police fallback about 1 hour. Fire fallback about 4.5 hours. Source: https://abc13.com/post/houston-emergency-center-was-there-a-911-outage-cad-system-power/14521677/
- San Francisco: CAD failed for about 2 hours, and dispatchers fell back to paper. Year given as 2015 in a search summary. [date unverified] Source: https://abc7news.com/1134441/
- No clear 2025 CAD incident was found. Gap.

---

## 3. Push notifications and SMS

### APNs (Apple Push Notification service)
- apns-priority 10 means send immediately, and it is the default. Priority 5 may be delayed, grouped, or throttled. [unverified against Apple doc] Source to check: https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns
- apns-expiration 0 means APNs does not store or retry the notification. A second source says APNs retries until expiry when delivery fails. Sources conflict. [unverified] Source: https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns
- apns-collapse-id: messages with the same ID are merged into one notification. Max 64 bytes. [unverified] Source: https://aapns.readthedocs.io/en/latest/api.html (secondary)
- APNs does not guarantee delivery. Apple's page was not retrievable, so this is general knowledge. [unverified] Source to check: https://developer.apple.com/documentation/usernotifications/sending-notification-requests-to-apns

### Critical alerts (iOS)
- Critical interruption level bypasses Do Not Disturb and the mute switch. It needs an Apple-approved entitlement. Source: https://developer.apple.com/tutorials/data/documentation/usernotifications/unnotificationinterruptionlevel/critical.md
- Apple's HIG says critical alerts are rare. Typical senders are government and public agencies, and apps for health or home. Source: https://developer-rno.apple.com/design/human-interface-guidelines/patterns/managing-notifications
- Time Sensitive breaks through Focus but not the ring/silent switch. It needs no special entitlement. Source: https://developer.apple.com/tutorials/data/documentation/usernotifications/unnotificationinterruptionlevel/critical.md (table in Apple's page, via search)

### FCM (Firebase Cloud Messaging)
- Default TTL (lifespan) is 4 weeks. TTL can be 0 to 2,419,200 s (28 days). Source: https://firebase.google.com/docs/cloud-messaging/customize-messages/setting-message-lifespan
- TTL 0 means messages that cannot be delivered immediately are discarded. Source: same page.
- A successful send only means FCM accepted the message. "it doesn't mean that the message was already delivered to the device." Source: same page.
- Delivery is not immediate for offline or Doze devices. Undelivered messages are dropped at TTL expiry. Source: same page.
- FCM rate limits: not researched. Gap.

### SMS (Twilio)
- Twilio docs with typical SMS latency: not found. [unverified] Gap.
- Status page incidents show delivery receipts can lag while messages still go through. Source: https://status.twilio.com/incidents/d4mw8hnylcx0 (one of several incident pages)

---

## 4. Conditional writes for the accept race

### DynamoDB
- TransactWriteItems groups up to 100 actions. Actions can be Put, Update, Delete, or ConditionCheck. Source: https://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_TransactWriteItems.md
- Aggregate item size of a transaction cannot exceed 4 MB. Source: same page.
- Each action is all-or-nothing. A failed condition rejects the whole request. Source: same page.
- No two actions in one transaction may target the same item. Source: same page.
- A conditional write is evaluated against the single item identified by its key. A failed condition returns "The conditional request failed." Source: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html
- Example pattern: UpdateItem with a ConditionExpression. Once the condition fails, the update is rejected. Source: same page.
- DynamoDB single-digit ms latency: not verified in this session. [unverified]

### Postgres (row lock and READ COMMITTED)
- Under READ COMMITTED, an UPDATE blocked on a row locked by another transaction re-checks its WHERE clause after that transaction commits. Source (mirrored docs and mailing list): https://www.postgresql.org/message-id/CAKFQuwYyZr0X8dPbknf5CDFW4-YVvH19QEXbUAGuxzRNMKnOAg%40mail.gmail.com
- The target row set is fixed at statement start. New matching rows are not picked up. Source: same mailing-list thread (secondary).
- Official current docs page was not retrieved. [unverified current wording]
- Inference (my analysis, not sourced): a guarded `UPDATE incidents SET status='assigned', hero_id=$1 WHERE id=$2 AND status='offered'` returns 0 rows for the loser. READ COMMITTED is enough for one-row guards. SERIALIZABLE is not needed for this pattern.
- Spanner and CockroachDB: not researched. Gap.

---

## 5. Geospatial indexing

### H3 cell sizes (official H3 table)
- Res 7: average area 5.161293360 km2, average edge 1.406475763 km, total cells 98,825,162. Source: https://h3geo.org/docs/core-library/restable/
- Res 8: average area 0.737327598 km2, average edge 0.531414010 km, total cells 691,776,122. Source: https://h3geo.org/docs/core-library/restable/
- Res 9: average area 0.105332513 km2, average edge 0.200786148 km, total cells 4,842,432,842. Source: https://h3geo.org/docs/core-library/restable/
- Each finer resolution cuts edge length by about 1/sqrt(7), roughly 0.378x. Source: https://h3geo.org/docs/core-library/restable/ (derived from the table)

### Redis GEO
- GEOSEARCH time complexity is O(N+log(M)). N is elements in the grid-aligned bounding box. M is items inside the shape. Available since Redis 6.2.0. Source: https://redis.io/docs/latest/commands/geosearch/
- With COUNT and ANY, the server returns early and results may be unsorted and not the closest. Without ANY, large areas with small COUNT can be slow. Source: https://redis.io/docs/latest/commands/geosearch/
- WITHHASH returns the raw 52-bit geohash-encoded score for each match. Source: https://redis.io/docs/latest/commands/geosearch/
- GEOADD is O(log N) per item added. Source: https://redis.io/docs/latest/commands/geoadd/ (search snippet, not fetched)
- Redis GEO data is stored in a sorted set. Source: https://redis.io/docs/latest/commands/geosearch/ (sorted set and 52-bit score per docs and search summary)

### Other
- S2 cells are what one tutorial says DISCO uses. [unverified] Source: https://www.techinterview.org/post/3233476891/design-ride-hailing-system/
- Uber location update rate in production: not confirmed. See section 1. [unverified]

---

## 6. Transactional outbox and durable workflows

- Uber's Cadence and Temporal provide durable timers as built-in primitives. Source: https://www.uber.com/blog/open-source-orchestration-tool-cadence-overview
- Temporal is a fork of Cadence. Source: https://softwareengineeringdaily.com/2020/04/08/cadence-ubers-workflow-engine-with-maxim-fateev/
- Debezium outbox pattern: not researched in this session. Gap.
- Temporal timer semantics and limits: not researched. Gap.

---

## 7. Kafka durability basics

- With acks=all, the leader waits for the in-sync replica set (ISR), not every replica. Source: https://www.conduktor.io/kafka/kafka-topic-configuration-min-insync-replicas (secondary; Apache doc redirect page did not load)
- min.insync.replicas is the minimum replicas that must acknowledge a write when acks=all. Source: same page.
- Common setting: replication factor 3, min.insync.replicas=2, acks=all. This survives loss of one broker. Source: https://docs.conduktor.io/learn/advanced/topics/min-in-sync-replicas
- If the ISR shrinks to the leader alone, acks=all waits only for that one broker. Source: https://www.netdata.cloud/guides/kafka/kafka-min-insync-replicas-misconfigured/
- When ISR is below min.insync.replicas, the producer gets NotEnoughReplicas. It does not silently under-replicate. Source: https://kafka-options-explorer.conduktor.io/config/min-insync-replicas/ (secondary)
- Retries with acks=all can duplicate records unless idempotence is on. Source: https://codemia.io/archive/kafka-acks-and-durability-tradeoffs
- Kafka end-to-end latency figure: not found. [unverified] Gap.

---

## 8. Double dispatch and dropped dispatch incidents

- Uber, Dec 10, 2010 (post Dec 11, 2010): "a bug that resulted in drivers getting dispatched to multiple Uber riders at the same time." Caused by load-driven system changes. Rolled back. Source: https://www.uber.com/us/en/newsroom/uber-service-disruption-friday-12102010/
- Uber, July 2019: drivers were routed to rider destinations instead of pickup points. Uber said it was resolved. Source: https://www.businessinsider.nl/uber-bug-sending-drivers-to-destinations-before-picking-up-passenger-2019-7
- Uber, 2026 (per search summary): Trip Radar bug showed an offer that disappeared and was re-offered lower. This is a duplicate offer, not a duplicate assignment. Source: https://therideshareguy.beehiiv.com/p/is-this-driver-exploitation-by-uber
- OECD document: repeat dispatches were sent to the same driver after cancellation. [unverified detail] Source: https://oecd-opsi.org/wp-content/uploads/2022/10/DAC-Second-Session-Status-Update.pdf
- LimoAnywhere (dispatch software vendor): fixed a bug where both drivers got two copies of a trip when a second driver was added. Source: https://kb.limoanywhere.com/?p=5258
- No public 911 or CAD double-dispatch incident was found. Gap.

---

## 9. PracHub pages and the Stripe prompt

Both pages were readable without login.

### Question page
Source: https://www.prachub.com/interview-questions/design-a-superhero-dispatch-system

- Prompt: civilians report emergencies, platform finds nearby heroes, notifies them, and exactly one accepts. Dispatchers monitor status end to end.
- Assumed scale: about 1M registered civilians, about 10K active heroes, peak about 500 new incidents per minute (about 8.3/s).
- Hero location pings every 5 to 15 s while on duty.
- Time to first offer: low single-digit seconds. Offer acceptance window: about 10 to 20 s.
- Hard invariant: a single-hero incident is assigned to at most one hero, even under concurrency and partial failures.
- Eventual consistency is fine for location display, dashboards, and analytics. Strong consistency is required for assignment.
- Hints: "Save the incident" and "start dispatch" should share one fate, not write-then-publish. Separate the matching read path from the assignment store.
- Follow-up 1: a 50x incident burst in one neighborhood. What degrades first?
- Follow-up 2: multi-hero incidents with complementary skills, without double-booking.
- Follow-up 3: an assigned hero goes silent mid-rescue. Detect it and reassign safely.
- Follow-up 4: add an ML model for acceptance probability and ETA. Keep matching in seconds.
- Strong-answer criteria include: reliability over throughput, matched storage per service, an explicit justification for each technology choice, and no over-engineering for ride-share scale.

### Interview experience page
Source: https://prachub.com/interview-experiences/stripe-software-engineer-interview-experience-five-onsite-rounds-including-a-superhero-dispatch-system

- Candidate was interviewing for L3. Outcome: rejected after onsite.
- Five onsite rounds: AI programming, debug ("Mako"), integration ("Bike map"), behavioral, and design (superhero dispatch).
- Design round feedback: the justification for technology choices was not strong enough.
- Design prompt in this account: a civilian is in an accident, a dispatch goes out, a superhero accepts and comes to help. No API design was asked.
- Follow-up questions are not listed on this page.
- Hints on the page are the author's advice, not interviewer guidance.

---

## 10. Gaps still open

- Uber DISCO, Ringpop, and offer-timeout primary sources.
- Lyft batch window in seconds.
- Apple APNs primary doc (fetch returned only the title).
- Twilio SMS latency and FCM rate limits.
- Spanner, CockroachDB, Debezium, and Temporal timer docs.
- NFPA current edition check and CAD unit-status and AVL models.
- Kafka end-to-end latency and the official Apache acks doc.
- 2025 CAD incidents.
