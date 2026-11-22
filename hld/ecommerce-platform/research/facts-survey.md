# Facts survey: e-commerce marketplace (Coupang-style) order path, inventory, flash sales, payments

Scope: verified facts for the study note on a Coupang or eBay style marketplace. Focus areas: order placement, inventory registration, overselling and double booking during flash sales, payment idempotency.

Status key:
- **verified**: I opened the primary page or extracted the primary PDF text and checked the exact wording.
- **secondary**: the figure came from a search-result summary or a translated or mirrored copy of a primary source. Recheck before quoting in an interview.
- **unverified**: I could not open a primary source. Do not use as a fact.

Method notes:
- Coupang IR site (ir.aboutcoupang.com) returned HTTP 403 to curl. Coupang's Q4 2025 earnings release and 2025 Form 10-K were downloaded from the company's q4cdn host (s206.q4cdn.com) and text-extracted with pdftotext. Those are primary.
- medium.com/coupang-engineering returned a Cloudflare challenge to curl and WebFetch. Two posts were read from the Wayback Machine copy (web.archive.org/web/2025id_/...).
- Alibaba group release (alibabagroup.com) could not be fetched directly. Its figure is taken from the search summary, so it is marked secondary.
- Several vendor docs returned 404 to the URL I guessed. Where that happened I say so and use the closest page that did open.

Search and fetch calls made: about 45 (WebSearch, WebFetch, curl). Dead ends: Stripe idempotency-page guesses that 404'd, Stripe payment-intent-lifecycle slug, Toss reference sub-pages, AWS Virtual Waiting Room English pages, Cloudflare how-it-works (404), Alibaba group document (fetch failed), Shopify BFCM 2025 ByteByteGo claim (not found at source).

---

## 1. Coupang scale (2025 10-K and Q4 2025 release)

Checklist table (Fact | Value | URL | Status)

| Fact | Value | URL | Status |
|---|---|---|---|
| Product Commerce active customers, Q4 2025 | 24.6 million, up 8% YoY from 22.8 million | https://s206.q4cdn.com/919117365/files/doc_financials/2025/q4/2025-Q4_Earnings-Release_Final.pdf (Key metrics table) and 10-K Key Business Metrics table | verified |
| Product Commerce active customers by quarter, 2025 (Mar, Jun, Sep, Dec) | 23.4, 23.9, 24.7, 24.6 million | https://s206.q4cdn.com/919117365/files/doc_financials/2026/ar/Coupang-Inc-_10-K_2026_V3_PWO-65955-FINAL.pdf | verified |
| Product Commerce active customers, Q4 2024 | 22.8 million | same 10-K | verified |
| Total net revenues, FY2025 | $34,534 million (+14% reported, +18% constant currency) | same 10-K, Item 7 summary table | verified |
| Total net revenues, FY2024 | $30,268 million | same 10-K | verified |
| Free cash flow, FY2025 | $527 million (down 48% from $1,016 million) | https://s206.q4cdn.com/919117365/files/doc_financials/2025/q4/2025-Q4_Earnings-Release_Final.pdf | verified |
| Adjusted EBITDA, FY2025 | $1,490 million (4.3% margin) | same release | verified |
| Net income, FY2025 | $214 million | same release | verified |
| Owned and leased floor space | "over 78 million square feet of fulfillment, logistics, and other operating spaces throughout Korea and Taiwan, as well as other parts of Asia and the United States" | 10-K Item 2 Properties | verified |
| Number of fulfillment and logistics centers | Not stated in the 10-K or Q4 release text I searched. The 10-K speaks of "strategically located fulfillment centers, logistics centers, and delivery vehicles" but gives no count. | 10-K Item 1A, Item 2 | unverified (count not found) |
| Rocket Delivery share of orders or revenue | Not disclosed in the documents I searched. The 10-K describes Rocket Delivery as "free, next-day delivery for orders placed anytime of the day, even seconds before midnight - across millions of products in Korea." | 10-K Item 7 Overview | verified for the description; share unverified |
| WOW membership count | No member count found in the 10-K or the Q4 release. Both say WOW membership was hit by the data incident. | Q4 release, "Q4 2025 Data Incident" section | unverified (count not published in these docs) |
| Orders per day or items shipped per day | Not found in either document | n/a | unverified |
| Employees | "approximately 108,000 employees" directly employed, "majority... located in Korea", as of Dec 31, 2025 | 10-K Item 1, Human Capital | verified |
| Merchants or SMEs | "more than 75% of our SME sellers are based outside Seoul" (Korea) | 10-K Item 1, Merchant Experience | verified |
| Data incident | Former employee illegally accessed data from "over 33 million user accounts"; data limited to "names, email addresses, phone numbers, delivery addresses, and limited order histories"; "No financial or payment card data, no login credentials or passwords" | Q4 release, "Q4 2025 Data Incident" | verified |
| Incident effect on metrics | "estimated to have adversely impacted Q4 2025 revenue growth rates, active customers and WOW membership, as well as profitability, beginning in December" | Q4 release | verified |
| Product Commerce revenue, FY2025 | $29.6 billion, +11% reported | search summary of the Q4 release | secondary (not located in the text I extracted) |
| Customers "18 million" | Stated in a 2022 engineering post: "to serve our 18 million customers" | https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2 (via Wayback copy) | verified, but a 2022 figure and a different metric from Product Commerce active customers |
| Revenue growth 2018 to 2022 | "Compared to 2018, Coupang has quadrupled in revenue" | same 2022 post | verified (as the post's own claim) |

Key reading for the design:
- The company frames its moat as end-to-end integration: "Our unique end-to-end integrated fulfillment, logistics, and technology network enables Rocket Delivery" (10-K Item 7 Overview). This matters for inventory: Coupang sells owned stock from its own FCs and also marketplace stock, and the two paths differ.
- Marketplace stock for FLC (fulfillment and logistics by Coupang): merchants ship to Coupang, "Coupang's... teams receive, store, pick, pack, and ship those products" (10-K Item 1, U.S. example). The Korean FLC offering is described in the same section.
- Seasonality and the data incident both lowered Q4 2025 growth. The 10-K states: "we experienced a lower growth rate in Product Commerce Active Customers in the fourth quarter of 2025 primarily due to seasonality and the impact of the Incident" (10-K Item 7).

---

## 2. Coupang engineering posts (medium.com/coupang-engineering)

Access note: the live Medium pages return a Cloudflare "Just a moment" challenge. The Wayback Machine copy (`https://web.archive.org/web/2025id_/<url>`) returned full text for the posts below.

### 2.1 "Our backend strategy to handle massive traffic" (Part 1, Aug 12, 2022)
URL: https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2
Authors per the post: Gogi (Du Hyeong) Kim and Key (Ki Hyeon) Kim. Status: verified (Wayback copy).

What it says, with exact figures:
- "Compared to 2018, Coupang has quadrupled in revenue with fast growth in active users."
- Serves "our 18 million customers".
- Product data is split across microservices. Example: "the product image and title data is managed by the Catalog microservice and the guaranteed delivery date data by the Stock and Fulfillment microservice."
- Capacity rule: "if the daily outbound capacity of a fulfillment center (FC) is met, the FC cannot take any new customer orders, and the relevant inventory and guaranteed delivery date information must be updated on the frontend for affected customers." This is the closest primary statement I found on inventory availability being derived from FC capacity, not a single stock counter.
- Core serving layer goal: "ensure high availability of 99.99% without fail".
- Storage: each microservice "sends the updated data to the queue and saves it to the common storage, a NoSQL database. The NoSQL database allows us to leverage eventual consistency and fetch data from all microservices in a single read."
- Cache: "we were able to serve data with ten times higher throughput and three times less latency compared to the common storage."
- Staleness: "This mechanism ensures that data in the common storage and the cache layer is 99.99% identical on a minutes-basis."
- Streaming: the read-through cache "provides minutes latency, but some data needs to be updated in a matter of seconds" (realtime streaming section, partly read).

### 2.2 "Lessons learned from handling massive traffic with cache" (Aug 18, 2022)
URL listed on the Infrastructure tag page: https://medium.com/coupang-engineering/tagged/infrastructure
Status: secondary. Listed by title and date on the tag page only. I did not open the post body.

### 2.3 "How Coupang built a microservice architecture" and "Integrating Coupang platform services to a microservice architecture" (May 25, 2018)
Part II URL (English): https://medium.com/coupang-engineering/행복을-찾기-위한-우리의-여정-a31fc2d5a572 (Korean slug, same post). Status: Part II verified via Wayback copy.
Part I (English): search result title only, status secondary.

Verified statements from Part II:
- "we were using more than 10,000 servers to maintain our microservice architecture."
- "services that were previously tightly coupled were separated as hundreds of loosely coupled microservices."
- Built the Configuration Management Database (CMDB) "in 2015", a metadatabase of services and their assets.
- "The microservice architecture at Coupang enables our engineers to independently deploy and test the hundreds of new features that are developed every day."

Secondary (search summary of Part I, not opened): the monolith's order component failure took down other components, and placing an order triggered payment and delivery requests directly. Use only as a hint.

### 2.4 Data platform posts (June 2022)
"Data platform 2022: Global expansion in petabytes" and "Data platform 2022: Transforming bytes to business insights" are on the Data tag. Status: listed only.

### 2.5 "Rocket Growth's ML platform ..." / "Simplifying large-scale ML training with an orchestration layer"
URL: https://medium.com/coupang-engineering/simplifying-large-scale-ml-training-with-an-orchestration-layer-9b90d8d28e39
Status: secondary (search title). Not relevant to order path, skipped.

### 2.6 What was not found
- No Coupang engineering post on inventory registration, stock reservation, flash deals, checkout idempotency or payments. I searched "coupang engineering blog order payment idempotency inventory reservation flash sale" and got only interview-prep sites (Educative, PrepHub) and generic articles. Those are not primary and are not Coupang's production design.
- A Coupang Engineering post on order allocation via mixed-integer programming was mentioned by an INFORMS Roundtable result (https://pubsonline.informs.org/do/10.1287/orms.2026.02.20/full/). Status: secondary (not opened). Treat as a hint that Coupang's fulfillment allocation is optimization-based.
- Coupang careers pages say the company runs "all Coupang services" on microservices and that Coupang Eats has "dozens of microservices" (coupang.jobs). Status: secondary (search summary).

---

## 3. Flash sale peaks

### 3.1 Alibaba Singles' Day (11.11) peak order rate
| Fact | Value | URL | Status |
|---|---|---|---|
| 2020 peak order creation rate | "583,000 orders per second" at peak | https://www.alibabagroup.com/document-1491144671282331648 (Alibaba release, "Alibaba Generates RMB498.2 billion (US$74.1 billion) in GMV during the 2020 11.11 Global Shopping Festival") | secondary (figure taken from search summary; direct fetch failed) |
| Timing of the 2020 peak | "26 seconds after shopping began at midnight" | https://www.alibabacloud.com/press-room/magic-behind-the-worlds-largest-online-shopping-festival | secondary (search summary) |
| 2020 GMV | RMB 498.2 billion (US$74.1 billion) | Alibaba group document above | secondary |
| 2019 peak (prior year) | 544,000 orders per second | cited on an Alibaba Cloud page (search summary) | secondary |
| Peak vs first festival | "1,400 times peak volume at the festival's debut 12 years ago" | Alibaba Cloud press room | secondary |
| Peak figures for 2021 to 2025 | Not found in my searches | n/a | unverified |

### 3.2 Alibaba hot-row handling (primary, verified)
Article: "How to Process Hot Spot Data in E-commerce Scenarios" by Hu Wei, Senior Database Technical Expert, Alibaba Cloud, dated August 12, 2020.
URL: https://www.alibabacloud.com/blog/how-to-process-hot-spot-data-in-e-commerce-scenarios_596491
Status: verified (fetched).

Exact statements:
- "Open-source MySQL implements pessimistic concurrency control through locking."
- "In pessimistic concurrency control through locking, the database can reach its optimal throughput when only one transaction is updating a row at a given moment."
- "AliSQL and MySQL 8.0 provide the no_wait function, which implements optimistic concurrency control in hot spot scenarios. Any transaction in the lock-wait state is directly rolled back."
- Thread pool: "If the thread pool contains 128 worker threads, the throughput is stabilized at the value when there are 128 concurrent threads."
- Queueing: "queue up the transactions that update the same row to reduce the overhead of InnoDB lock wakeup. In this case, the throughput approaches 1s / trxrt."
- Shorten lock hold time: "a hot spot transaction includes five SQL statements and nine network sessions", so the fix is to reduce SQL statements and network round trips inside the locked section.
- The product fix is ApsaraDB for RDS Enterprise hot-update plus group commit ("Commit transactions in group mode").

### 3.3 Alibaba flash-sale row lock on PostgreSQL (primary, verified in part)
Article: "Double Eleven Technology Series: Flash Sales Optimization on PostgreSQL"
URL: https://www.alibabacloud.com/blog/double-eleven-technology-series-flash-sales-optimization-on-postgresql_594096
Status: verified (partial fetch). Exact framing: "When one customer is updating this record, the other 999,999 customers are waiting. But ideally, the database should only process the 100 lucky winners in the flash sales." The post's counter approach is an update with a guard: `update tbl set ... upd_cnt=upd_cnt+1 where id=pk and upd_cnt+1<=5;` (five iPhones). This is the same idea as an atomic conditional decrement.

### 3.4 AliSQL inventory hotspot patch (secondary)
Summary from an Alibaba Cloud decade-of-evolution article (https://www.alibabacloud.com/blog/a-decade-of-evolution-of-alibabas-databases---part-1_594444): AliSQL gained "inventory hotspot patching, SQL throttling protection, and thread pools" and the 00:00 inventory-database overload motivated the work. Status: secondary (search summary). I did not find a primary 2020 post that gives the inventory patch's numbers.

### 3.5 Shopify BFCM (primary, verified)
Post: "BFCM Readiness 2025", published November 20, 2025.
URL: https://shopify.engineering/bfcm-readiness-2025
Status: verified (fetched).

- "By the fourth test, we hit 146 million requests per minute and 80,000+ checkouts per minute."
- "On the last test of the year, we tested p99, which was 200M RPM."
- 2024 production peak: "We peaked at 284 million requests per minute on edge and 80 million on app servers."
- 2024 volume: "57.3 PB of data, 10.5 trillion database queries, 1.19 trillion edge requests, and 1.17 trillion database writes."
- "pushing 12TB per minute on Black Friday alone."

Scale-testing method: https://shopify.engineering/scale-performance-testing (search summary): Shopify measures tests "in terms of Requests Per Minute (RPM) achieved as well as Checkouts Completed Per Minute (CCPM)". Status: secondary.

Not found in an official post: a 2025 production checkouts-per-minute peak. A community forum figure of about 4,000 CPM is unofficial and I do not use it.

### 3.6 Amazon Prime Day
I did not search for Prime Day order counts in this pass. Status: unverified (not checked).

### 3.7 Flash-sale engineering from non-primary sources
The top search hits for "flash sale system design oversell" (matthewswong.com, raunakbaliyan.substack.com, renekin.com, hackernoon, sujeet.pro, singhajit.com, GitHub demos) all describe the same pattern: a single atomic conditional UPDATE, a unique order key, and a reservation with TTL. These are folklore-grade sources. I cite them only to show common practice, not as facts about Coupang.

---

## 4. Database limits that bound a hot inventory row

### 4.1 DynamoDB per-partition limits (verified)
URL: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html
Status: verified (fetched).

- "Every partition in a DynamoDB table is designed to deliver a maximum capacity of 3,000 read units per second and 1,000 write units per second."
- One read unit = one strongly consistent read per second for an item up to 4 KB. One write unit = one write per second for an item up to 1 KB.
- Item size: "if the table has an item size of 20 KB, a single consistent read operation will consume 5 read units."
- "Adaptive capacity applies to on-demand mode and provisioned capacity."
- "You should design your application for uniform activity across all partition keys in the table."

Inference (not stated by AWS): one hot inventory item lives on one partition key, so its write rate is capped near 1,000 writes per second for items up to 1 KB, no matter how large the table's provisioned capacity is. Adaptive capacity moves capacity between partitions, but it cannot split a single key. Use "write sharding" (the page links bp-partition-key-sharding.md) to split the stock counter into N sub-keys. The page's sharding and adaptive-capacity sections were linked but not opened.

Service quotas page (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/ServiceQuotas.html) was opened only for its per-partition wording in search results. Status for account-level table limits: unverified.

### 4.2 Redis single-thread throughput (verified docs, numbers from examples)
URL: https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/benchmarks/
Status: verified (fetched).

- "Redis is, mostly, a single-threaded server from the POV of commands execution (actually modern versions of Redis use threads for different things). It is not designed to benefit from multiple CPU cores."
- Example from the page: `redis-benchmark -t set,lpush -n 100000 -q` gives "SET: 180180.17 requests per second, p50=0.143 msec" (hardware not stated in that example).
- Pipelining example on a MacBook Air 11": "SET: 1536098.25 requests per second", "GET: 1811594.25 requests per second" with `-P 16`.
- Default benchmark is "exploiting concurrency only", no pipelining.
- Order of magnitude I would use in a design: roughly 100k to 200k unpipelined ops/s per instance, and more with pipelining. This is a reading of the doc's examples, not a published SLA. Status: secondary (derived from examples).

Implication for a hot SKU counter in Redis: one key lives on one shard and is served by one thread, so a flash-sale decrement on a single key is bounded by that thread's rate, not by the cluster size. Note this is inference.

### 4.3 PostgreSQL row locks (verified)
URL: https://www.postgresql.org/docs/current/sql-select.html
Status: verified (fetched).

- "FOR UPDATE, FOR NO KEY UPDATE, FOR SHARE and FOR KEY SHARE are locking clauses; they affect how SELECT locks rows as they are obtained from the table."
- "If FOR UPDATE ... is specified, the SELECT statement locks the selected rows against concurrent updates."
- NOWAIT: "the statement reports an error, rather than waiting, if a selected row cannot be locked immediately."
- SKIP LOCKED: "any selected rows that cannot be immediately locked are skipped."
- Caveat from the same page: "Skipping locked rows provides an inconsistent view of the data, so this is not suitable for general purpose work, but can be used to avoid lock contention with multiple consumers accessing a queue-like table."
- Scope: "NOWAIT and SKIP LOCKED apply only to the row-level lock(s)."

Implication: SKIP LOCKED is the wrong tool for stock checks (it hides rows that are locked, so a buyer could see "not available" when stock exists). It fits a work queue of reservation jobs. For stock, use a conditional UPDATE or SELECT FOR UPDATE with a short lock. (Inference from the caveat.)

---

## 5. Payments

### 5.1 Stripe idempotency keys (verified)
URL: https://docs.stripe.com/api/idempotent_requests
Status: verified (fetched). Earlier search summary said the same thing.

- "For API v1, you can remove keys from the system automatically after they're at least 24 hours old."
- "We generate a new request if a key is reused after the original is pruned."
- "For API v1, Stripe saves the status code and body of the first request made with a given idempotency key after endpoint execution begins. Retries with the same key return the saved response, including 500 errors."
- "With API v2, retries don't repeat successful operations."
- "For API v1, we save results only after the execution of an endpoint begins. If incoming parameters fail validation, or the request conflicts with another request that's executing concurrently, we don't save the idempotent result..."
- Keys: "up to 255 characters long". Suggest "V4 UUIDs".
- Parameter check: "The idempotency layer compares incoming parameters to those of the original request and errors if they're not the same."

Important for the design: a key that is reused after 24 hours is treated as a new request, so a retry-safe client must store its own order-level key (the order id) in the database and not rely on Stripe's key alone.

### 5.2 Stripe PaymentIntent lifecycle (verified in part)
URL: https://docs.stripe.com/payments/paymentintents/lifecycle.md
Status: verified (fetched, lifecycle table).

- Statuses named on the page: `requires_payment_method`, `requires_confirmation`, `requires_action`, `processing`, `requires_capture`, `succeeded`, `canceled` (the page's wording: "Cancelled").
- "After you create the PaymentIntent, its status is requires_payment_method until you attach a payment method."
- "If the payment attempt fails (for example, due to a decline), the PaymentIntent's status returns to requires_payment_method so that the payment can be retried."
- "A PaymentIntent with a succeeded status means that the corresponding payment flow is complete. The funds are now in your account and you can confidently fulfil the order."
- Cancel: "Cancellation invalidates the PaymentIntent for future payment attempts, releases any held funds and can't be undone."
- "PaymentIntents might also automatically transition to cancelled if they're confirmed too many times."
- Separate auth and capture: "After the payment method is authorised, the PaymentIntent status transitions to requires_capture." (https://docs.stripe.com/payments/place-a-hold-on-a-payment-method, verified)

Retries: "retries can create multiple Charges" on one PaymentIntent (https://docs.stripe.com/payments/payment-intents, verified).

Design guidance Stripe states on the PaymentIntent page (verified): "Remember to provide an idempotency key to prevent the creation of duplicate PaymentIntents for the same purchase. This key is typically based on the ID that you associate with the cart or customer session." Also: "If the checkout process is interrupted and resumes later, attempt to reuse the same PaymentIntent instead of creating a new one."

Caveat: the same page says "For most integrations, Stripe recommends using the Checkout Sessions API with the Payment Element over Payment Intents." Newer Stripe docs push Checkout Sessions. The study note should say both.

### 5.3 Stripe authorization validity windows (verified)
URL: https://docs.stripe.com/payments/place-a-hold-on-a-payment-method
Status: verified (fetched).

Card-not-present (online):

| Card brand | MIT window | CIT window |
|---|---|---|
| Visa | 5 days | 7 days |
| Mastercard | 7 days | 7 days |
| American Express | 7 days | 7 days |
| Discover | 7 days | 7 days |

Card-present (in person): Visa 5 days, Mastercard 2 days, American Express 2 days, Discover 2 days. The page says: "The exact authorisation window is 4 days and 18 hours, to allow time for clearing processes."

Other facts on the same page:
- Japan: JPY holds for Visa, Mastercard, JCB, Diners Club, Discover "for up to 30 days".
- Klarna: capture "by midnight of the 28th calendar day after the charge request".
- PayPal: hold 10 days, auto-extended to 20 days.
- Cash App Pay: "must be captured within 7 days".
- Affirm: "You then have 30 days to capture the payment balance."
- Afterpay/Clearpay: 13 days.
- Automatic delayed capture (private preview): Stripe captures "about 6 hours before the expiry time" if `capture_method=automatic_delayed`.
- Extended authorization exists for eligible online and Terminal payments (link on the same page; not opened).
- "If the authorisation expires before you capture the funds, the funds are released and the payment status changes to canceled."

Design implication: a "reserve at checkout, capture at ship" model has a 7-day ceiling for most online cards, but Visa MIT is 5 days. A marketplace that ships in 2 days is safe. A pre-order model is not, unless it uses extended authorization or capture at order time.

### 5.4 Toss Payments confirm API (verified in part, Korean PG)
Reference page: https://docs.tosspayments.com/reference
Status: verified (fetched). Individual reference sub-pages returned 404 to my guessed URLs.

- Endpoint: `POST /v1/payments/confirm`.
- Required body fields: `paymentKey` (max 200 chars, "결제를 식별하는 역할로, 중복되지 않는 고유한 값입니다"), `orderId` (6 to 64 chars, letters, digits, `-`, `_`, `=` only), `amount`.
- Window: "결제 인증이 유효한 10분 안에 상점에서 결제 승인 API를 호출하지 않으면 해당 결제는 만료됩니다." Translated: if the merchant does not call the confirm API within 10 minutes of authentication, the payment expires.
- The same page describes a separate 30-minute expiry for IN_PROGRESS payments that are never confirmed (status section). The two windows differ. Status: verified as text on the page, but I did not reconcile them against a second source.
- Idempotency: the confirm section does not mention an idempotency key header. The page mentions a 멱등키 (idempotency key) header only for the cancel API. Status: verified absence on this page. Do not claim that Toss confirm is idempotent by key without checking the authorization page, which I did not open.

Design implication: the Korean flow is auth (redirect with paymentKey), then server-side confirm within 10 minutes. The server must make the stock commit and the confirm call safe to retry using orderId as the unique business key (inference).

### 5.5 Coupang payments
No Coupang primary doc on its PG or checkout flow was found. Status: unverified.

---

## 6. Search freshness

### 6.1 Elasticsearch refresh interval (verified)
URL: https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html
Status: verified (fetched).

- "The value defaults to 1s in Elastic Stack and 5s in Serverless."
- "In Serverless, 5s is also the minimum value that can be set."
- Search-idle: "shards that haven't seen search traffic for at least index.search.idle.after seconds will not receive background refreshes until they receive a search request. This behavior aims to automatically optimize bulk indexing in the default case when no searches are performed."
- Disable: "the setting can be set to -1 to disable periodic refresh operations. This does not fully prevent indexed documents becoming visible to search because there are mechanisms within Elasticsearch which perform refresh operations other than the periodic refresh."

Gap: the page does not describe the cost of lowering the interval below 1s. The usual cost (more segments, more merge work, more CPU) is known but was not in a primary source I opened. Status for the cost claim: unverified.

### 6.2 Coupang or eBay catalog-to-search latency
Not found in a primary source. Coupang's 2022 post describes minutes-level cache staleness ("99.99% identical on a minutes-basis") and seconds for some streams. That is the closest primary number. Status: verified as to the post's own wording (section 2.1). Not a search-index number.

---

## 7. Virtual waiting rooms

### 7.1 Cloudflare Waiting Room (secondary)
Configuration page: https://developers.cloudflare.com/waiting-room/reference/configuration-settings/
Status: secondary (search summary). The How-it-works page returned 404 to my guess.

- New users per minute: "the threshold of users allowed per minute (less than or equal to the number of total active users)". Docs suggest "100% of your expected peak traffic".
- Total active users: concurrent-session limit. Summary says it "must be greater than 200" and suggests "75% of origin traffic capacity".
- Session duration: 1 to 30 minutes, default 5.
- Data in dashboards and API is "cached for around 30 seconds".

Re-verify the 200 minimum and the 75% and 100% guidance on the live page before using them.

### 7.2 AWS Virtual Waiting Room on AWS (secondary)
English implementation guide returned no matching page. Translated pages were read via search summary.
- German performance page: https://docs.aws.amazon.com/de_de/solutions/latest/virtual-waiting-room-on-aws/performance-data.html. Summary: default quota, CloudFront "can handle a waiting room of 250,000 users, with each user polling the serving_num API at least once per second."
- Japanese guide PDF: https://docs.aws.amazon.com/ja_jp/solutions/latest/virtual-waiting-room-on-aws/virtual-waiting-room-on-aws.pdf. Summary: "up to 500 clients per second requesting a queue position" under default quotas. The rate also "affects the Lambda concurrency quota".
- Mechanism (translated pages): join calls `assign_queue_num` through API Gateway into SQS; Lambda batches and stores queue positions in ElastiCache (Redis OSS); client polls `serving_num`; admission is a serving counter incremented by an entry strategy; client then requests a JWT.

Status for all AWS numbers: secondary. Translated summaries, not checked against the English page.

### 7.3 Design implication (inference)
A waiting room is a rate limiter on admission, not an inventory fix. It reduces concurrent writers on the hot SKU. It does not stop double-booking by itself. The inventory write still needs a conditional decrement.

---

## 8. Shopping cart and listings

### 8.1 Amazon Dynamo paper (verified)
URL: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf (SOSP 2007)
Status: verified (PDF text extracted).

- "the shopping cart service must allow customers to add and remove items from their shopping cart even amidst network and server failures. This requirement forces us to push the complexity of conflict resolution to the reads in order to ensure that writes are never rejected."
- "the application that maintains customer shopping carts can choose to 'merge' the conflicting versions and return a single unified shopping cart."
- Scale: "the service that maintains shopping cart (Shopping Cart Service) served tens of millions requests that resulted in well over 3 million checkouts in a single day."
- SLA is measured at the 99.9th percentile.

Design implication: cart writes should be always-accept with merge on read. Stock and payment are not cart. Do not carry the always-accept rule into the checkout or stock path.

### 8.2 eBay listings and buyers (secondary)
Source: 2025 Annual Report (search summary): https://www.sec.gov/Archives/edgar/data/1065088/000155278126000287/e26087_ebay-ars.pdf
Status: secondary (search summary; PDF not opened).
- "At the end of 2025, eBay had 135 million active buyers and 2.5 billion live listings globally."
- Active buyer definition: buyers who paid for a transaction in the previous 12 months.
- The eBay Fast Facts page (https://investors.ebayinc.com/fast-facts/default.aspx) shows 147 million buyers and 2.8 billion listings, but these totals include Tise and Depop. Do not mix them with the 2025 year-end figures.

### 8.3 Coupang listings
Not found. Coupang does not publish a live-SKU count in the documents I read. Status: unverified.

---

## Conflicts and corrections

1. **Shopify peak RPM.** A ByteByteGo summary says BFCM 2025 peaked at "489 million requests per minute." I could not find this in a Shopify primary post. Shopify's own 2025 post gives a 200M RPM p99 test and a 2024 production peak of 284M RPM at the edge. Use Shopify's numbers and label the test versus production difference. Status: 489M is unverified.

2. **Alibaba peak orders.** Sources often mix "orders per second" with GMV or transactions. The 583,000 figure is the 2020 order creation peak. The 544,000 figure is the 2019 peak. Do not quote the 2020 figure as a general "Singles' Day" number. Also: the 583,000 figure is from a search summary of the Alibaba release, not a fetch. Confirm before a talk.

3. **Idempotency retention.** Stripe's docs say keys can be pruned after "at least 24 hours" for API v1. The v2 behavior differs: "retries don't repeat successful operations". Do not quote 24 hours for v2. Also, a pruned key is treated as new, so an order-level key in your own DB is required.

4. **Authorization windows.** The folklore "7 days" applies to most online cards, but Visa MIT is 5 days. Card-present windows are 2 days for Mastercard, Amex, Discover. Japan allows 30 days for some JPY holds. Quote a table, not one number.

5. **Stripe API advice.** Stripe's PaymentIntent page now says: "For most integrations, Stripe recommends using the Checkout Sessions API with the Payment Element over Payment Intents." The older guidance was to build on PaymentIntents. Both are true in different eras. State the recommendation as "Checkout Sessions by default, PaymentIntents for custom flows".

6. **Toss confirm window.** The Toss reference says 10 minutes from authentication to confirm. The status section says 30 minutes for an IN_PROGRESS payment never confirmed. These are different timers. Do not merge them.

7. **Toss idempotency.** It is tempting to say Toss confirm takes an Idempotency-Key header. The reference page does not say so for confirm. It does for cancel. Check the authorization page before claiming it.

8. **Elasticsearch default refresh.** The docs say the default is 1s in Elastic Stack and 5s in Serverless, and that 5s is the minimum in Serverless. The "1s for non-search-idle indices" phrasing in some blogs is a simplification. Quote the docs.

9. **Customer counts.** Coupang's "18 million customers" (2022 engineering post) is not comparable with "24.6 million Product Commerce active customers" (Q4 2025). Different date and metric. Do not chain them into a growth rate.

10. **Interview-prep "Coupang" designs.** Educative and PrepHub pages describe soft reservations with TTLs and conditional decrements as "how Coupang does it". Neither cites a Coupang source. Treat as generic advice, not Coupang's architecture.

11. **Redis numbers.** The 180k and 1.5M figures in the docs are examples on unnamed or laptop hardware with and without pipelining. They are not a capacity spec. Do not quote them as a Redis limit.

12. **DynamoDB limit.** The 1,000 WCU per partition is a design target, not a hard quota. The docs say "designed to deliver". Quote the wording.

13. **Coupang "Rocket Delivery" share.** Some third-party writeups give a share of orders. No primary source in my search gives it. Leave it out.

14. **Coupang data incident.** The 10-K and the Q4 release both say about 33 million accounts. The Q4 release adds that about 3,000 accounts were retained by the former employee. Quote the release if you cite the incident.

---

## Numbers to use in the design

Each line gives the number, its meaning, and the URL. Use the status column to decide how careful to be.

| # | Number | Meaning | URL | Status |
|---|---|---|---|---|
| 1 | 24.6 M Product Commerce active customers (Q4 2025) | Read-side scale for catalog and search | https://s206.q4cdn.com/919117365/files/doc_financials/2025/q4/2025-Q4_Earnings-Release_Final.pdf | verified |
| 2 | $34.5 B total net revenues FY2025, +14% | Order-volume ballpark (not an order count) | https://s206.q4cdn.com/919117365/files/doc_financials/2026/ar/Coupang-Inc-_10-K_2026_V3_PWO-65955-FINAL.pdf | verified |
| 3 | >78 M sq ft fulfillment and operating space (Korea, Taiwan, Asia, US) | Inventory footprint, shows why FC capacity is a constraint | same 10-K, Item 2 | verified |
| 4 | 18 M customers, 99.99% availability target, minutes-level cache staleness | Coupang's own 2022 serving-layer target | https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2 | verified (Wayback copy) |
| 5 | "FC cannot take any new customer orders" when daily outbound capacity is met | Inventory availability is FC-capacity-driven | same post | verified |
| 6 | 33 M accounts in the 2025 data incident | Security and PII design note | https://s206.q4cdn.com/919117365/files/doc_financials/2025/q4/2025-Q4_Earnings-Release_Final.pdf | verified |
| 7 | 583,000 orders per second (2020 Singles' Day peak) | Order-creation burst ceiling, 26 s after midnight | https://www.alibabagroup.com/document-1491144671282331648 | secondary |
| 8 | 146 M RPM and 80,000+ checkouts per minute (Shopify 2025 load test) | Checkout throughput reference | https://shopify.engineering/bfcm-readiness-2025 | verified |
| 9 | 284 M RPM edge peak (Shopify 2024 production) | Production peak versus load test | same post | verified |
| 10 | 1,000 write units/s and 3,000 read units/s per DynamoDB partition | Hot-key ceiling for one stock item | https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html | verified |
| 11 | 128 worker threads as the plateau in the Alibaba hot-row test | Cap concurrency on a hot row | https://www.alibabacloud.com/blog/how-to-process-hot-spot-data-in-e-commerce-scenarios_596491 | verified |
| 12 | 24 h Stripe idempotency key pruning (API v1); 255-char key limit | Retry window and key length | https://docs.stripe.com/api/idempotent_requests | verified |
| 13 | 7 days (CNP CIT, most cards); Visa MIT 5 days; card-present 2 days; exact 4 d 18 h | Auth-to-capture budget | https://docs.stripe.com/payments/place-a-hold-on-a-payment-method | verified |
| 14 | 10 min from auth to Toss confirm call | Korean PG confirm deadline | https://docs.tosspayments.com/reference | verified (text), timer conflict noted |
| 15 | 1s default refresh; 5s minimum in Serverless | Search freshness floor | https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules.html | verified |

Also cite for the cart rule: "writes are never rejected" (Dynamo paper, https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf), verified.

---

## Five facts I am least sure of

1. **Alibaba 583,000 orders/s.** Taken from a search summary of Alibaba's release, not from a fetch. The 26 seconds after midnight detail is also from a search summary. Confirm against alibabagroup.com before quoting.
2. **Coupang WOW membership count and FC count.** Not found in the 10-K or Q4 release text. The numbers may exist in the investor presentation or a call transcript, which I did not open. Mark as unknown.
3. **Cloudflare "total active users must be greater than 200" and the 75%/100% sizing guidance.** From a search summary of the configuration page, which I did not open. The How-it-works page 404'd.
4. **AWS Virtual Waiting Room 500 clients/s and 250,000 users.** Read from translated (Japanese and German) pages via search summary. The English figures were not checked.
5. **Toss 10-minute confirm window versus 30-minute IN_PROGRESS expiry, and whether confirm takes an idempotency key.** The reference page gives the 10-minute and 30-minute text but not the auth-page header details. I did not open the authorization page, so the idempotency-key claim is unresolved.

Other gaps: no primary source for Redis or Postgres capacity under a real hot-key load test; no Coupang payments doc; no Coupang or eBay engineering post on inventory reservation; the Stripe PaymentIntent statuses for `requires_confirmation` and `requires_action` are from the lifecycle table only.
