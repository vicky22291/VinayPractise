# Facts survey: warehouse management system (WMS) for a fulfillment network

Survey date: 2026-11-22. Purpose: verified facts for a system design study note on a WMS for fulfillment centers (inventory per bin with on-hand, allocated, picked, shipped states, lots and expiry, inbound receiving and putaway, outbound allocation, picking, packing and shipping via handheld scanners, and real-time inventory sync to the commerce site). Coupang is the reference company.

## 0. Method and status legend

Status values:
- **verified**: text read from the page itself (fetched with curl, Wayback Machine, r.jina.ai, WebFetch, or pdftotext) in this session.
- **secondary**: seen only in a search-result excerpt or a summary from a fetch tool, or the source is a vendor or trade publication. Re-check before quoting.
- **unverified**: claim found in a secondary place only, or the primary page could not be opened. Do not use as a hard number.

Fetch log (what worked and what did not):
- `ir.aboutcoupang.com` returned HTTP 403 to curl. Its investor pages were not read directly.
- `news.coupang.com` returned HTTP 403 (Akamai "Access Denied") to curl. The WMS newsroom article was read only through search-result excerpts.
- `sec.gov` returned HTTP 403 to curl, but WebFetch opened the Coupang 10-K HTML pages. The FY2024 Item 1 text was read. Item 2 (Properties) was not reached in any fetch pass because the tool returned risk-factor excerpts for the offsets tried.
- `medium.com/coupang-engineering/*` returned HTTP 403 directly. The Wayback Machine (`https://web.archive.org/web/2025id_/<url>`) returned HTTP 200 and the text was read.
- `gs1.org` pages returned HTTP 403 to curl, but `https://r.jina.ai/<url>` returned the page text. The SSCC, GTIN and GLN pages were read.
- `blog.picnic.nl` WMS post redirects to `jobs.picnic.app`, which returned HTTP 404 for the WMS path. The Picnic WMS post was seen only through search excerpts.
- `ocadotechnology.com/press-centre` could not be read by WebFetch. Ocado figures come from search excerpts.
- DeHoratius and Raman (2008) PDF was not retrievable (Cardiff repository returned HTML or 403). The 65% figure comes from a Scribd excerpt.
- Amazon robotics article (`aboutamazon.com`) and Oracle WMS Cloud 26B secondary-ordering page were read in full.
- Zebra MC3300 spec page was read via WebFetch.

Search and fetch calls made: about 50 (search plus fetch, across all sections).

## 1. Checklist table

| # | Fact | Value | URL | Status |
|---|---|---|---|---|
| 1a | Coupang fulfillment and logistics space, FY2024 10-K | "over 67 million square feet" of fulfillment and logistics space (Korea, other Asia, US) | https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm | secondary (figure from search summary of filing; Item 2 not read) |
| 1b | Coupang space, FY2025 10-K | "over 78 million square feet" of fulfillment, logistics and other operating space (Korea, Taiwan, other Asia, US) | https://www.sec.gov/Archives/edgar/data/1834584/000183458426000024/cpng-20251231.htm | secondary (search summary; scope differs from FY2024) |
| 1c | Coupang space, FY2021 10-K | approx. 42 million sq ft (fulfillment and logistics), per search summary | https://www.sec.gov/Archives/edgar/data/1834584/000183458422000015/cpng-20211231.htm | secondary |
| 1d | Coupang center count | "over 100 fulfillment and logistics centers in over 30 cities" as of 31 Dec 2020; "over 25 million square feet" | https://www.sec.gov/Archives/edgar/data/1834584/000162828021001984/coupang-sx1.htm | secondary (S-1 excerpt via search) |
| 1e | Coupang center count, latest | "100+ logistics centers" and "30+ regions" | https://news.coupang.com/wp-content/uploads/2026/04/Coupang_2025_Q4_factsheet_updated.pdf | secondary (search excerpt; fetch 403) |
| 1f | Population within distance of a center | 70% within 7 miles (2021 S-1); 70% of Korean population within 10 km (IPO-era newsroom) | https://www.sec.gov/Archives/edgar/data/1834584/000162828021001984/coupang-sx1.htm ; newsroom IPO release (URL from search, not opened) | secondary; "within 10 minutes" NOT FOUND |
| 1g | Order cut-off and delivery (dawn) | "with order cutoffs as late as midnight"; receive "by 7 am the next morning" | https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm (Item 1, "Our Customer Experience") | verified (FY2024 10-K text via WebFetch); FY2025 10-K has "order cutoffs as late as midnight" (verified via WebFetch) |
| 1h | Rocket Delivery (next-day) | "free, next-day delivery for orders placed anytime of the day" | https://www.sec.gov/Archives/edgar/data/1834584/000183458426000024/cpng-20251231.htm (search excerpt) | secondary |
| 1i | Items or deliveries per day | No per-day figure found. Only "millions of general merchandise items" (FY2024 10-K Item 1) | https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm | verified (absence in Item 1 text) |
| 1j | Automation claim | "The technology, automation and efficiencies gained through our end-to-end systems" | https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm | verified (qualitative, no count) |
| 1k | Coupang customers | "18 million customers" (engineering post, date unknown) | https://web.archive.org/web/2025id_/https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2 | verified (Wayback text); date unknown |
| 1l | Coupang active customers | about 24.6 million product-commerce active customers (Q4 2025) | https://news.coupang.com/wp-content/uploads/2026/04/Coupang_2025_Q4_factsheet_updated.pdf | secondary |
| 2a | Coupang WMS (in-house) | Built in-house; covers inbound to outbound; picks fulfillment center per order at payment time; "processes each order as it arrives" | https://news.coupang.com/archives/18754/ | secondary (search excerpt; fetch 403) |
| 2b | Coupang backend stock path | Stock and guaranteed-delivery data sit in a separate "Stock and Fulfillment" microservice; FC at daily outbound capacity "cannot take any new customer orders" | https://web.archive.org/web/2025id_/https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2 | verified |
| 2c | Coupang stock staleness | read-through cache "provides minutes latency"; stock "must be updated in a matter of seconds" | same as 2b | verified |
| 2d | Rocket Delivery spatial index | Delivery areas on H3 hexagons; "South Korea can be divided into approximately 432 million hexagons in 12-level resolution" | https://web.archive.org/web/2025id_/https://medium.com/coupang-engineering/coupang-rocket-deliverys-spatial-index-based-delivery-management-system-26940eaaee63 | verified (Wayback text) |
| 2e | SCM low-code inventory data builder | pulls inventory and order data from multiple sources to compute transfers between centers | https://medium.com/coupang-engineering/coupang-scm-workflow-building-a-low-code-no-code-platform-3d035c1fa37a | secondary (search excerpt; fetch 403) |
| 3a | Amazon robots | "more than 1 million robots across its operations network" since 2012 | https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center | verified (published 9 Oct 2024, updated 4 Jun 2026) |
| 3b | Amazon Sequoia | identify and store inventory "up to 75% faster" | https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center | verified (speed claim, not capacity) |
| 3c | Amazon Vulcan | can pick and stow "approximately three quarters of all various types of items" | https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center | verified |
| 3d | Amazon items per FC | No per-center item count or storage capacity published in the robotics article | https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center | verified (absence) |
| 3e | Amazon random stow | Items stowed "randomly rather than grouped by category"; pods hold "up to 10 items on average" per compartment | https://www.aboutamazon.com/news/operations/inside-amazons-fulfillment-centers-what-you-can-expect-to-see-on-a-warehouse-tour | secondary (search excerpt; not opened) |
| 4a | Picnic WMS origin | Started on an off-the-shelf vendor WMS; migrated feature by feature by having the vendor emit events | https://blog.picnic.nl/building-picnics-warehouse-management-system-a3192db3e15c | secondary (search excerpt; WMS post not opened) |
| 4b | Picnic database | Postgres chosen over MongoDB for transactional support, run on Amazon RDS | same as 4a | secondary |
| 4c | Picnic split | 2024 post: Warehouse Control System (WCS) for conveyor, WMS for everything outside the conveyor | https://blog.picnic.nl/picnic-10-years-2024-building-a-modular-warehouse-0f886bd0e212 | secondary |
| 4d | Picnic scale | "delivers groceries to millions across three countries" | https://blog.picnic.nl/ | verified (curl text) |
| 4e | Ocado Hive/grid | 1,100 robots at Andover (2018 blog); planned hives 0.75 million storage locations and over 3,500 robots | https://www.ocadotechnology.com/blog/2018/12/20/step-inside-ocados-next-generation-warehouses ; https://www.ocadotechnology.com/press-centre | secondary (search excerpts; press centre fetch failed) |
| 4f | Ocado comms | robot swarms reached "ten times a second" on unlicensed spectrum | https://www.ocadotechnology.com/press-centre | secondary |
| 4g | Zalando event model | Event stream as primary source of truth, local projections built from it | https://engineering.zalando.com/posts/2017/11/why-event-driven.html | secondary (search excerpt); no Zalando WMS post found |
| 4h | Shopify / 6 River Systems | About $450 million acquisition; "100% orders at SFN are going through warehouse management softwares that 6 River has built" | https://www.mmh.com/article/shopify_completes_acquisition_of_6_river_systems/news ; https://www.modernretail.co/platforms/much-more-intentional-how-shopifys-latest-fulfillment-moves-aim-to-simplify-logistics-for-sellers/ | secondary (trade press and interview excerpts); no Shopify engineering post on WMS architecture found |
| 4i | Flipkart warehouse design (2018) | Layered warehouse system; Service Request decomposed by orchestrator; capacity reserved in a "process capacity view"; multi-tenant (Myntra, Jabong) | https://blog.flipkart.tech/lego-building-blocks-to-model-supply-chain-workflows-slashn-2018-f55f4e39d84 | secondary (search excerpt, about 8 years old) |
| 4j | Walmart inventory availability design | Event-sourced design proposal: immutable events, materialized views; Cosmos DB change feed suggested | https://medium.com/walmartglobaltech/design-inventory-availability-system-using-event-sourcing-1d0f022e399f | secondary (search excerpt; a design proposal, not confirmed production) |
| 4k | Instacart | Does not run its own warehouses; availability prediction across 80,000+ retail locations | https://tech.instacart.com/instacarts-item-availability-architecture-solving-for-scale-and-consistency-f5661acb20a6 | secondary |
| 5a | SSCC identifies | "a logistic unit, which can be any combination of trade items packaged together for storage and/or transport purposes; for example a case, pallet or parcel" | https://www.gs1.org/standards/id-keys/sscc | verified (r.jina.ai text) |
| 5b | SSCC length (18 digits) | not found in fetched text | https://www.gs1.org/standards/id-keys/sscc | unverified (length) |
| 5c | GTIN purpose | "uniquely identify all of its trade items"; trade items are "priced, ordered or invoiced at any point in the supply chain" | https://www.gs1.org/standards/id-keys/gtin | verified |
| 5d | GTIN lengths (8, 12, 13, 14) | not found in fetched text | https://www.gs1.org/standards/id-keys/gtin | unverified |
| 5e | GLN purpose | "can be used by companies to identify their locations" | https://www.gs1.org/standards/id-keys/gln | verified |
| 5f | GLN length (13) | not found in fetched text | https://www.gs1.org/standards/id-keys/gln | unverified |
| 5g | ASN as EDI 856 / DESADV | not found in fetched GS1 EDI page | https://www.gs1.org/standards/edi-xml | unverified |
| 6a | Oracle WMS Cloud FEFO / LEFO / FIFO / LIFO | methods listed: "First Expiry First Out (FEFO)/ Last Expiry First Out (LEFO), First In First Out (FIFO)/ Last In First Out (LIFO), Location Sequence Ascending/ Descending, Quantity Ascending/ Descending" | https://docs.oracle.com/en/cloud/saas/warehouse-management/26b/owmol/secondary-allocation-method.html | verified |
| 6b | Oracle secondary ordering | "if there are multiple candidate LPN's with the same expiry date, then the system allows you to order by secondary ordering criteria like Quantity Ascending or Quantity Descending" | same as 6a | verified |
| 6c | Oracle invalid combo | "FEFO | LEFO and FEFO" flagged as invalid secondary method | same as 6a | verified |
| 6d | Oracle multi-SKU LPN FEFO caveat | FEFO "can be compromised when SKUs in one LPN have different expiry dates" | https://docs.oracle.com/en/cloud/saas/warehouse-management/23d/ (What's New, via search excerpt) | secondary |
| 6e | Oracle waveless picking | No WMS Cloud page found naming waveless allocation; "Direct Allocation" is the closest term | https://docs.oracle.com/en/cloud/saas/warehouse-management/20d/owmsu/outbound.html | secondary (search excerpt) |
| 6f | SAP EWM FEFO | FEFO = "First-Expire, First-Out", uses shelf-life expiration date; FIFO uses goods receipt date | https://help.sap.com/docs/SUPPORT_CONTENT/sewm/3354621266.html | secondary (search excerpt) |
| 6g | SAP EWM putaway vs FIFO | "addition to existing stock" putaway "violates the FIFO principle" | https://learning.sap.com/courses/basic-customizing-in-sap-s-4hana-ewm/applying-putaway-rules | secondary (search excerpt) |
| 6h | Pick productivity (vendor) | "total units per hour (TUPH)" as best productivity measure; travel is 50% of person-to-goods picking time | https://www.swisslog.com/en-us/blog/reducing-labor-dependencies-in-e-grocery-fulfillment | secondary (vendor; not MHI) |
| 6i | Dematic travel share | "up to 70% of a picker's time can be spent travelling between locations in manual warehouses" | https://www.dematic.com/en-au/insights/articles/improving-productivity-in-manual-warehouses-starts-with-picking/ | secondary (vendor) |
| 6j | Goods-to-person station rate (vendor) | "up to 1,000 picks per hour" (SSI Schaefer); "exceeding 600 order lines per hour per station" (Dematic Multishuttle) | https://ssi-schaefer.com/en-de/how-can-the-picking-performance-be-improved--746848 ; https://www.dematic.com/content/dam/dematic/downloads/infographics/Dematic-WF-Infographic.pdf | secondary (vendor; units differ: picks vs order lines) |
| 6k | MHI pick rate benchmark | not found | n/a | unverified (no MHI source located) |
| 7a | Zebra MC3300 roaming | "PMKID/OKC/CCKM/802.11r" fast roam | https://www.zebra.com/us/en/products/spec-sheets/mobile-computers/handheld/mc3300.html | verified |
| 7b | Zebra MC3300 offline or batch mode | no statement on the spec page | https://www.zebra.com/us/en/products/spec-sheets/mobile-computers/handheld/mc3300.html | verified (absence) |
| 7c | Zebra roaming features | 802.11v, 802.11r (Aggregated Fast Transition), ScanAssist | https://techdocs.zebra.com/emdk-for-android/9-0/mx/wifi/ | secondary (search excerpt; version-specific) |
| 7d | Zebra imager range | SE4850 "captures barcodes in hand and on your uppermost warehouse racks" | https://www.zebra.com/us/en/products/spec-sheets/mobile-computers/handheld/mc3300.html | verified (marketing wording) |
| 7e | Scan-to-confirm latency target | no primary source found | n/a | unverified |
| 7f | Warehouse Wi-Fi dead zones | no primary source found | n/a | unverified |
| 8a | Inventory record inaccuracy study | DeHoratius and Raman, "Inventory Record Inaccuracy: An Empirical Analysis", Management Science 54(4), 2008, pp. 627-641 | https://ideas.repec.org/a/inm/ormnsc/v54y2008i4p627-641.html | secondary (bibliographic record verified via RePEc listing) |
| 8b | "65% of records inaccurate" | excerpt: "inaccuracies in 65% of the 369,567 inventory records" | https://www.scribd.com/document/619909654/dehoratius2008 | unverified (Scribd excerpt, sentence truncated; primary PDF not retrieved) |
| 8c | Variance explained by covariates | 67.6% (stores) and 69.0% (product categories) | https://ideas.repec.org/a/inm/ormnsc/v54y2008i4p627-641.html | secondary (search excerpt) |
| 8d | Profit impact of IRI | "profit losses ... between 3% and 10%" (cited by a later paper) | n/a | unverified (second-hand; do not use) |

## 2. Coupang: fulfillment network from the 10-K

Verified text from FY2024 10-K, Item 1 ("Our Customer Experience"):
- "with order cutoffs as late as midnight" and "receive products by 7 am the next morning" (dawn and same-day service).
- Automation: "The technology, automation and efficiencies gained through our end-to-end systems".
- "millions of general merchandise items" (no daily volume).
- Source: https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm

Verified text from FY2025 10-K, Item 1:
- "with order cutoffs as late as midnight" appears in the same section (WebFetch, 0 to 100000 characters).
- "Our Merchant Experience" section: "direct sourcing and mobile fulfillment sites" and "receive, store, pick, pack, and ship those products directly to customers".
- Source: https://www.sec.gov/Archives/edgar/data/1834584/000183458426000024/cpng-20251231.htm

Verified text from FY2024 Item 1A (Risk Factors, read through WebFetch excerpt):
- "maintain fulfillment centers in the United States, Taiwan, and Europe" (note: a different country list than Item 1).
- "a fire at our Deokpyeong fulfillment center which caused extensive damage" in June 2021.
- Source: https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm

Not found in any fetched 10-K text:
- An exact count of fulfillment and logistics centers in the latest 10-K.
- The "within 10 minutes" population statistic.
- Items shipped per day or deliveries per day.
- Rocket Delivery "order by midnight, delivered by 7 am" wording. The 7 am promise is attached to dawn or fresh delivery. Rocket Delivery in the FY2025 10-K is "free, next-day delivery for orders placed anytime of the day" (search excerpt, secondary).

Item 2 (Properties): not read. Both the FY2024 and FY2025 WebFetch passes returned risk-factor text for the offsets tried. Next step: fetch the 10-K at offset 0 with a prompt asking only for Item 2, or use the EDGAR full-text search for "square feet".

Square footage history (all secondary, from search summaries of the filings):
- FY2021: about 42 million sq ft.
- FY2022: about 47 million sq ft.
- FY2023: over 55 million sq ft.
- FY2024: over 67 million sq ft, fulfillment and logistics only.
- FY2025: over 78 million sq ft, fulfillment, logistics and "other operating spaces". The scope changed, so the FY2024 to FY2025 jump is not like-for-like.

Coverage and distance (all secondary):
- S-1 (2021): "70% of the population lives within 7 miles of a Coupang logistics center" and "over 100 fulfillment and logistics centers in over 30 cities" as of 31 Dec 2020. Source: https://www.sec.gov/Archives/edgar/data/1834584/000162828021001984/coupang-sx1.htm
- IPO-era newsroom (English): "70 percent of the South Korean population lives within 10 kilometers of a Coupang logistics center". Source found via search; URL not opened.
- Q4 2025 factsheet: "100+ logistics centers" and "30+ regions". Source: https://news.coupang.com/wp-content/uploads/2026/04/Coupang_2025_Q4_factsheet_updated.pdf (fetch returned 403; excerpt only)

Fulfillment cut-offs (secondary, Coupang newsroom via search):
- Rocket Fresh dawn delivery: midnight cut-off and 7 am delivery since 2018, same-day service added in 2020. Source: Korean newsroom (search excerpt). Original newsroom text: https://news.coupang.com/archives/51079/ (Jeju fresh dawn launch, February 2025, about 400 fresh items at launch, planned to expand to 1,700+).
- Taiwan: Rocket Delivery covers about 70% of Taiwan's geography with next-day delivery seven days a week. Source: https://ir.aboutcoupang.com/news-events/news/news-details/2026/Coupang-Jumps-to-No--132-on-Fortune-500-as-the-Company-Scales-AI-Driven-Global-Commerce/default.aspx (search excerpt).
- Fast Company 2025 release: "millions of items ... can be ordered by midnight and delivered by dawn the next morning". Source: https://ir.aboutcoupang.com/news-events/news/news-details/2025/Coupang-Named-a-Fast-Company-Most-Innovative-Company-for-2025/default.aspx (search excerpt).

## 3. Coupang engineering blog and newsroom: fulfillment, WMS, inventory

Verified (Wayback copy of Medium post, "Our backend strategy to handle massive traffic"; date unknown, search says about 2 years old):
- Data split by microservice: "the product image and title data is managed by the Catalog microservice and the guaranteed delivery date data by the Stock and Fulfillment microservice". Source: https://web.archive.org/web/2025id_/https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2
- "if the daily outbound capacity of a fulfillment center (FC) is met, the FC cannot take any new customer orders, and the relevant inventory and guaranteed delivery date information must be updated on the frontend for affected customers."
- Freshness: "The read-through cache layer provides minutes latency, but some data needs to be updated in a matter of seconds. One example is stock information."
- Scale mention: "our 18 million customers".
- Design implication: stock is a per-FC capacity gate, not only on-hand count. Read path is cached, and stock needs a push path (seconds).

Verified (Wayback copy of Medium post on Rocket Delivery spatial index; the post is delivery-area management, not warehouse inventory): "South Korea can be divided into approximately 432 million hexagons in 12-level resolution." Source: https://web.archive.org/web/2025id_/https://medium.com/coupang-engineering/coupang-rocket-deliverys-spatial-index-based-delivery-management-system-26940eaaee63

Secondary (search excerpts, pages not opened):
- Coupang newsroom WMS article (https://news.coupang.com/archives/18754/, returned 403 to curl): Coupang built its own WMS covering "inbound receiving to outbound shipping". On payment, the WMS "immediately checks the delivery address and inventory at each fulfillment center nationwide" to choose which center ships. It guides workers on picking routes and packaging size. Centers "do not batch orders by the hour"; each order is processed "as it arrives". This is the single most relevant Coupang source for the prompt and needs a direct read before the note cites it.
- SCM workflow post (https://medium.com/coupang-engineering/coupang-scm-workflow-building-a-low-code-no-code-platform-3d035c1fa37a): demand prediction; an algorithm that distributes products among fulfillment centers; a no-code data builder that pulls inventory and order data from several sources to compute transfer quantities between centers.
- An inbound-scheduling post (Korean, URL not captured): an ML model predicts the number of trucks a vendor needs for an inbound slot. The post reports vendor date changes caused by slot shortage fell by 67.9%. [unverified, URL not captured]

Gaps: no Coupang engineering post about the WMS itself (picking, putaway, handheld scanners, lots or expiry) was found. The fulfillment and inventory posts available are about the commerce-side stock service and SCM.

## 4. Amazon fulfillment scale

Verified (aboutamazon.com, "Amazon robotics: Meet the robots inside fulfillment centers", published 9 Oct 2024, updated 4 Jun 2026):
- "Since then, Amazon has developed, produced, and deployed more than 1 million robots across its operations network." Source: https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center
- Sequoia: "enables Amazon to identify and store inventory up to 75% faster at our fulfillment centers" (speed, not capacity).
- Vulcan: "can pick and stow approximately three quarters of all various types of items stored at our fulfillment centers" (share of item types, not a count).
- The article gives no per-center item count and no storage capacity. It does not use the words "random" or "chaotic".

Secondary (aboutamazon.com "Inside Amazon's fulfillment centers" tour, search excerpt, not opened): the stow approach is random. "All of the inventory ... is stowed randomly rather than grouped by category." Pods are fabric-covered, divided into compartments "about a foot square", each holding "up to 10 items on average". Robotic drive units bring pods to stations. Source: https://www.aboutamazon.com/news/operations/inside-amazons-fulfillment-centers-what-you-can-expect-to-see-on-a-warehouse-tour

Amazon patent context (secondary): a USPTO-hosted patent on "warehouse inventory item location consolidations based on real-time volumetric space utilization" (https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11055661). Use only as evidence that location-level slotting is patented, not as a number.

## 5. Companies that built their own WMS

Picnic (Netherlands, grocery micro-fulfillment):
- Scale, verified on https://blog.picnic.nl/ : "Started in 2015 in the Netherlands, Picnic now delivers groceries to millions across three countries".
- Secondary: started with an off-the-shelf WMS. Its strategy was to have the vendor emit events, then rebuild features one by one, with the new system listening to events and "tracking stock levels". Source: https://blog.picnic.nl/building-picnics-warehouse-management-system-a3192db3e15c (search excerpt; redirect target returned 404 when fetched).
- Secondary: Postgres chosen over MongoDB "for transactional support", run on Amazon RDS. Same source.
- Secondary: 2020 post on a modular monolith; 2024 post splits a Warehouse Control System (WCS) for conveyor operations from a WMS for work outside the conveyor. Source: https://blog.picnic.nl/picnic-10-years-2024-building-a-modular-warehouse-0f886bd0e212
- Not found: an explicit event-sourced WMS design, or offline scanner behavior.

Ocado Technology (grid storage robotics):
- Secondary: 1,100 robots lifting crates at Andover (2018). Source: https://www.ocadotechnology.com/blog/2018/12/20/step-inside-ocados-next-generation-warehouses
- Secondary (press centre fact sheet): planned hives with "0.75 million storage locations" managed by swarms of "over 3,500 robots"; swarm reach "ten times a second" over unlicensed spectrum. Source: https://www.ocadotechnology.com/press-centre (fetch failed; search excerpt).
- Secondary (Medium, Ocado engineering manager): each bot has a Linux board "BotPC" connected to sub-systems over CAN, USART and SPI. Source: https://medium.com/ocadotechnology/how-is-ocado-technology-using-automated-solutions-to-build-robots-c734da08c6ef
- Not found: a public description of the warehouse control system software.
- Caution: a third-party article's "swarm intelligence" wording is not corroborated by Ocado. Do not use it.

Zalando:
- Secondary: event-first architecture. "Why Event Driven?" (2017) argues the event stream should be the primary source of truth, with local projections built from it. Source: https://engineering.zalando.com/posts/2017/11/why-event-driven.html
- Secondary: 2025 inventory optimisation post uses a batch forecast, publishes "report generated" notices to an event stream, and queues online updates on AWS SQS with Lambda. Source: https://engineering.zalando.com/posts/2025/06/inventory-optimisation-system.html
- Not found: a Zalando WMS post.

Shopify and 6 River Systems:
- Secondary: the acquisition was reported at about $450 million, adding 6 River's software and "Chuck" mobile robots to Shopify Fulfillment Network (SFN). Source: https://www.mmh.com/article/shopify_completes_acquisition_of_6_river_systems/news
- Secondary (Modern Retail interview): "100% orders at SFN are going through warehouse management softwares that 6 River has built for us". Source: https://www.modernretail.co/platforms/much-more-intentional-how-shopifys-latest-fulfillment-moves-aim-to-simplify-logistics-for-sellers/
- Secondary (VentureBeat): "customers with over 50 pickers using the system at once". URL from search; not opened.
- Not found: a Shopify engineering post on WMS architecture. Treat the software architecture as unknown.

Instacart:
- Secondary: Instacart does not run its own warehouses. It is a layer over retailer systems. Its availability work predicts item availability "across 80,000+ retail locations". Source: https://tech.instacart.com/instacarts-item-availability-architecture-solving-for-scale-and-consistency-f5661acb20a6 (search excerpt).
- Not relevant to WMS internals. Useful only as a model for "availability prediction" versus "system of record" stock.

Walmart Global Tech:
- Secondary: a Medium design write-up proposes event sourcing for inventory availability. "These events will be immutable and will be the source of truth in the system." It suggests Cosmos DB change feed and notes it resembles Kafka's consumer and offset model. It lists "orders shipped or cancelled at a warehouse" as inputs. Source: https://medium.com/walmartglobaltech/design-inventory-availability-system-using-event-sourcing-1d0f022e399f . Search says this is about 1,356 days old and is a design proposal.
- Secondary: a lakehouse post says business event streams are "primarily backed by Apache Kafka" and names inventory as a dependent domain. URL from search: https://medium.com/walmartglobaltech/lakehouse-at-fortune-1-scale-480bcb10391b
- [unverified] "connect to our 4,700 stores, fulfillment centers, distribution centers and our suppliers": the exact page was not identified.

Flipkart:
- Secondary, 2018 SlashN talk on a warehouse system: layered design with a core layer of inventory, shipment, container and layout data behind CRUD APIs; an orchestration layer composing blocks such as Receive, Quality Check and Transfer; work tracked as a Service Request decomposed into child requests; capacity reserved through a "process capacity view". Multi-tenant, serving Myntra and Jabong. Source: https://blog.flipkart.tech/lego-building-blocks-to-model-supply-chain-workflows-slashn-2018-f55f4e39d84
- Secondary, newer tech blog: fulfillment centers feed "Mother Hubs"; wave cut-off design and a Central Planning Platform that aligns labor with transport. Date unclear. Source: https://blog.flipkart.tech/feed

Summary of architecture patterns seen across these builders (for the design note):
- Vendor WMS to in-house migration by event emission (Picnic).
- Per-site or per-domain split: conveyor control (WCS) separated from WMS (Picnic 2024).
- Relational store for WMS transactions (Picnic on Postgres/RDS).
- Event streams as the source of truth for downstream inventory (Walmart design, Zalando event-first).
- Capacity gating at the fulfillment-center level (Coupang FC daily outbound capacity).
- Read cache plus push updates for stock, with seconds-level freshness (Coupang backend post).
- Offline scanner behavior: not found in any builder source.

## 6. GS1 identifiers and EDI

Verified from GS1 pages (fetched through r.jina.ai, because gs1.org returned 403 to curl):
- SSCC: "Serial Shipping Container Code can be used by companies to identify a logistic unit, which can be any combination of trade items packaged together for storage and/ or transport purposes; for example a case, pallet or parcel." Source: https://www.gs1.org/standards/id-keys/sscc
- GTIN: "Global Trade Item Number (GTIN) can be used by a company to uniquely identify all of its trade items. GS1 defines trade items as products or services that are priced, ordered or invoiced at any point in the supply chain." Source: https://www.gs1.org/standards/id-keys/gtin
- GLN: "Global Location Number (GLN) can be used by companies to identify their locations, giving them complete flexibility to identify any type or level of location required." Source: https://www.gs1.org/standards/id-keys/gln

Design implications (from the verified definitions):
- The SSCC names a logistic unit (case, pallet, parcel). It maps to a license plate or LPN in WMS terms, not to a SKU. In the design, the SSCC identifies the box or pallet that is put away and shipped.
- GTIN identifies the product (trade item). It maps to the SKU.
- GLN identifies a location, which maps to a fulfillment center or dock. A bin address is a WMS-internal code, not a GS1 key.

Unverified (not present in the fetched text; confirm against GS1 General Specifications before using):
- SSCC is 18 digits (includes extension digit, GS1 company prefix, serial reference, check digit).
- GTIN lengths are 8, 12, 13 and 14 digits.
- GLN is 13 digits.
- ASN is carried as EDI 856 (ANSI X12) or DESADV (EANCOM). The GS1 EDI page was fetched (HTTP 200) but the mapping was not found in its text. Source checked: https://www.gs1.org/standards/edi-xml

## 7. WMS process facts from vendor docs

Verified, Oracle WMS Cloud 26B, "Secondary Ordering Criteria in Waving" (https://docs.oracle.com/en/cloud/saas/warehouse-management/26b/owmol/secondary-allocation-method.html):
- Allocation methods listed: FEFO and LEFO, FIFO and LIFO, Location Sequence Ascending or Descending, Quantity Ascending or Descending.
- Secondary ordering breaks ties. "if there are multiple candidate LPN's with the same expiry date, then the system allows you to order by secondary ordering criteria like Quantity Ascending or Quantity Descending."
- "a valid error message is displayed if you attempt to configure the following invalid Secondary Allocation Method": FEFO with LEFO is listed as invalid.
- The method is set on the Wave Template (per the 21B What's New, secondary, https://docs.oracle.com/en/cloud/saas/warehouse-management/26b/owmol/secondary-allocation-method.html).

Secondary, Oracle WMS Cloud (search excerpts):
- 23D: FEFO extended to LPN allocation for multiple details of the same SKU and for multi-SKU LPNs. "FEFO can be compromised when SKUs in one LPN have different expiry dates." The "Include Multi SKU LPN" flag is needed. Source: Oracle 23D What's New (search result, https://www.oracle.com/webfolder/technetwork/tutorials/tutorial/cloud/wms/releases/23D/23D-wms-wn.htm).
- 20C User Guide: FEFO uses the LPN's expiry date. An "allow_expired_inventory" flag on order type and manual wave prevents expired stock allocation. Source: https://docs.oracle.com/en/cloud/saas/warehouse-management/20c/owmsu/outbound.html (search excerpt).
- 18C What's New: FEFO uses the inventory priority date; a blank priority date means FEFO.

Waveless picking:
- Not found by name in Oracle WMS Cloud docs. The closest term is "Direct Allocation", described in the outbound packing section of the 20D user guide (https://docs.oracle.com/en/cloud/saas/warehouse-management/20d/owmsu/outbound.html), which allocates inventory to an order without running a wave. Secondary.
- Wave picking is the default in Oracle WMS Cloud documentation (secondary).

SAP EWM (search excerpts):
- Removal rule configured under Goods Issue Process, Strategies, "Specify Stock Removal Rule". It can be set by warehouse process type or by the product's Stock Removal Control Indicator. Source: https://help.sap.com/docs/SUPPORT_CONTENT/sewm/3354621266.html
- FEFO: "First-Expire, First-Out", based on shelf-life expiration date. FIFO uses the goods receipt date. Same source.
- Putaway: SAP Learning says the common setting "addition to existing stock" "violates the FIFO principle". Source: https://learning.sap.com/courses/basic-customizing-in-sap-s-4hana-ewm/applying-putaway-rules
- A SAP Community post notes flow racks are often used when strict FIFO is needed for expiring products. Dated (about 5.7 years for the removal-strategy thread). Source: https://community.sap.com/t5/supply-chain-management-q-a/strategy-for-stock-removal-fefo/qaq-p/12384824
- Caveat from the same thread (dated): the system checks the first storage type first, so the picked location may not be strict FEFO across bulk areas.

Cycle counting, short pick, directed putaway:
- Not verified from a primary vendor page in this session. Oracle and SAP search results did not surface the relevant pages. Mark as unverified in the note, or search again for "Oracle WMS Cloud cycle count" and "SAP EWM physical inventory" in the next pass.

Pick rates (vendor material only; no MHI source located):
- Swisslog: TUPH is the "best measure of productivity in a fulfillment center". In its e-grocery model, picking is "almost half (48%) of the manhours". Goods-to-person "cut picking manhours by 36% and improved site productivity by 49%" at a constant order rate. Mixed human plus robot gave "156% improvement". Source: https://www.swisslog.com/en-us/blog/reducing-labor-dependencies-in-e-grocery-fulfillment
- Swisslog: "travel time typically consumes 50% of order picking time in person-to-goods picking".
- Dematic: "up to 70% of a picker's time can be spent travelling". Source: https://www.dematic.com/en-au/insights/articles/improving-productivity-in-manual-warehouses-starts-with-picking/
- Dematic: voice-directed picking "boost productivity up to 45%". AutoStore "300 to 500%" (vendor claims).
- SSI Schaefer: goods-to-person stations "up to 1,000 picks per hour". Source: https://ssi-schaefer.com/en-de/how-can-the-picking-performance-be-improved--746848
- Dematic Multishuttle: "exceeding 600 order lines per hour per station". Source: https://www.dematic.com/content/dam/dematic/downloads/infographics/Dematic-WF-Infographic.pdf
- These vendor numbers are not comparable: "picks" and "order lines" are different units, and the vendors have an interest in the outcome. Use only as directional ranges with the vendor named.

## 8. Handheld scanner reality

Verified, Zebra MC3300 spec page (https://www.zebra.com/us/en/products/spec-sheets/mobile-computers/handheld/mc3300.html):
- Roaming: "PMKID/OKC/CCKM/802.11r" listed under Fast Roam.
- Marketing: "The MC3300 supports 802.11ac with fast roaming".
- Imager: "The extended range SE4850 imager captures barcodes in hand and on your uppermost warehouse racks".
- Use case: "If you are using Zebra Android handheld and wearable devices in the warehouse, workers and IT will benefit".
- No statement on offline mode or batch mode on this page. Do not claim either from this source.

Secondary, Zebra Wi-Fi Manager docs (versions vary; https://techdocs.zebra.com/emdk-for-android/9-0/mx/wifi/):
- 802.11v switch: devices get network load information from nearby access points to help roaming decisions.
- Aggregated Fast Transition (802.11r): described by Zebra as more reliable and consistent fast roaming with Zebra infrastructure.
- ScanAssist: lets the device monitor neighboring access points without extra scans (see the same docs family).
- Subnet roam switch: roaming between subnets attached to different wireless controllers.
- Radio data rates on the spec sheet: 2.4 GHz 144 Mbps, 5 GHz 867 Mbps (search excerpt; verify against the PDF spec sheet at https://www.zebra.com/content/dam/zebra_dam/en/spec-sheets/mc3300-specification-sheet-en-us.pdf).

Not found (unverified):
- Zebra or Honeywell primary docs on offline or batch scanning for WMS integration (the only batch mode found is for RFID readers).
- Wi-Fi dead-zone or roaming-latency numbers in warehouses.
- Scan-to-confirm latency target from any primary source.

Design implication: treat scan confirmation as a local action that must survive short Wi-Fi drops. Queue confirmations on the device and reconcile them server side. This is a design choice, not a sourced fact, and should be labeled as such in the note.

## 9. Inventory accuracy and cycle counting

Study (verified bibliographic record): DeHoratius, N. and Raman, A., "Inventory Record Inaccuracy: An Empirical Analysis", Management Science, vol. 54, no. 4, April 2008, pp. 627-641, DOI 10.1287/mnsc.1070.0789.
- Source: https://ideas.repec.org/a/inm/ormnsc/v54y2008i4p627-641.html (RePEc listing, verified via search). Also https://pubsonline.informs.org/doi/suppl/10.1287/mnsc.1070.0789
- Retail context (not a warehouse study). The paper examines store-level inventory records.

The 65% figure:
- Excerpt (Scribd copy, not primary): "inaccuracies in 65% of the 369,567 inventory records". The sentence was truncated in the excerpt. Source: https://www.scribd.com/document/619909654/dehoratius2008
- Status: [unverified]. Re-check against the published paper at pubsonline.informs.org before using. Do not quote "65%" as a finding until the primary text is read.

Covariates (secondary, search excerpt from the paper): audit practices reduce inaccuracy; store complexity and distribution structure increase it. Together they explain "67.6% and 69.0% of the variance in IRI across stores and product categories".

Profit impact: a later paper cites "profit losses ... between 3% and 10%" from IRI (second-hand, unverified). Do not use.

Cycle counting practice: no primary vendor page on cycle count (Oracle, SAP) was read in this session. Mark the cycle-count design as a design choice unless a primary doc is found.

## Conflicts and corrections

1. "Within 10 minutes" coverage claim (folklore risk). No Coupang source found with a 10-minute population metric. The sources that do exist use different measures:
   - 2021 S-1: "70% of the population lives within 7 miles".
   - IPO-era newsroom: "70 percent of the South Korean population lives within 10 kilometers".
   - Recommendation: do not write "10 minutes" in the note. Use "about 70% of the Korean population lives within 10 km of a center (IPO-era, company-stated)".
   - Source: https://www.sec.gov/Archives/edgar/data/1834584/000162828021001984/coupang-sx1.htm
2. Square footage is not like-for-like across years. FY2024: "over 67 million square feet of fulfillment and logistics space". FY2025: "over 78 million square feet of fulfillment, logistics and other operating spaces". Use the FY2025 figure with the scope caveat.
   - Sources: https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm ; https://www.sec.gov/Archives/edgar/data/1834584/000183458426000024/cpng-20251231.htm
3. Midnight to 7 am is a dawn or fresh service, not a general Rocket Delivery rule. The 10-K ties "order cutoffs as late as midnight" to dawn and same-day service. Rocket Delivery in the FY2025 10-K is described as "next-day delivery for orders placed anytime of the day" (search excerpt). Write the two as separate products.
   - Sources: https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm (verified) ; FY2025 10-K (secondary).
4. Rocket Now in the 10-K is a brand name only (verified in the Item 1 text). Do not treat it as a separate delivery promise.
5. Amazon "random stow". Amazon's robotics article does not use "random". The random stow claim comes from a separate Amazon tour article (search excerpt). The two Amazon sources are compatible, but the random claim is secondary.
   - Sources: https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center (verified, no "random") ; https://www.aboutamazon.com/news/operations/inside-amazons-fulfillment-centers-what-you-can-expect-to-see-on-a-warehouse-tour (secondary).
6. Pick-rate units conflict. SSI Schaefer quotes "picks per hour" and Dematic quotes "order lines per hour". These are different units. Never compare them directly.
7. Event sourcing is a design proposal in the Walmart case, not confirmed production architecture. Picnic's public material describes a vendor WMS migration, not event sourcing. Shopify's WMS is described only in trade press. Do not present any of these as "how X does it" without a primary architecture post.
8. Coupang's own WMS description has two different layers. The newsroom says the WMS picks an FC "as the customer presses payment". The backend post says the FC gate is "daily outbound capacity", and the cache is minutes-stale except stock which needs seconds. The design note should say that capacity and stock are separate signals (secondary for the newsroom).
9. Oracle FEFO. The 23D note says FEFO "can be compromised" when SKUs in one LPN have different expiry dates. This is a real caveat, not a folklore claim. Keep it in the design.
10. The 65% record-inaccuracy figure is widely repeated, but this session could not read the primary paper. Treat as folklore until verified.
11. Ocado "swarm intelligence" wording comes from a third-party article and is not corroborated by Ocado. Do not use.
12. Amazon robot count date. "More than 1 million robots" is in an article first published 9 Oct 2024 and updated 4 Jun 2026. The article gives no date for reaching that total.

## Numbers to use in the design

1. Coupang storage footprint: over 78 million sq ft (FY2025 10-K, fulfillment, logistics and other operating space). Source: https://www.sec.gov/Archives/edgar/data/1834584/000183458426000024/cpng-20251231.htm (secondary).
2. Coupang storage footprint, prior scope: over 67 million sq ft (FY2024, fulfillment and logistics only). Source: https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm (secondary).
3. Coupang center count: 100+ logistics centers, 30+ regions (Q4 2025). Source: https://news.coupang.com/wp-content/uploads/2026/04/Coupang_2025_Q4_factsheet_updated.pdf (secondary).
4. Population near a center: about 70% within 10 km (IPO-era, company-stated). Source: https://www.sec.gov/Archives/edgar/data/1834584/000162828021001984/coupang-sx1.htm (secondary; the S-1 uses 7 miles).
5. Dawn promise: order by midnight, receive by 7 am (FY2024 10-K). Source: https://www.sec.gov/Archives/edgar/data/1834584/000183458425000030/cpng-20241231.htm (verified).
6. Customers: 18 million (engineering post, date unknown). Source: https://web.archive.org/web/2025id_/https://medium.com/coupang-engineering/our-backend-strategy-to-handle-massive-traffic-d30cd6cc4fb2 (verified text).
7. FC gate: an FC at daily outbound capacity takes no new orders (engineering post). Source: same URL (verified).
8. Stock freshness target: seconds for stock; read cache is minutes (engineering post). Source: same URL (verified).
9. Amazon robots: more than 1 million. Source: https://www.aboutamazon.com/news/operations/amazon-robotics-robots-fulfillment-center (verified).
10. Sequoia: up to 75% faster inventory store (speed claim). Source: same URL (verified).
11. FEFO tie-break: quantity ascending or descending; FEFO with LEFO is invalid. Source: https://docs.oracle.com/en/cloud/saas/warehouse-management/26b/owmol/secondary-allocation-method.html (verified).
12. Travel share of pick time: about 50% (person-to-goods, Swisslog) to up to 70% (manual, Dematic). Vendor claims. Sources: https://www.swisslog.com/en-us/blog/reducing-labor-dependencies-in-e-grocery-fulfillment ; https://www.dematic.com/en-au/insights/articles/improving-productivity-in-manual-warehouses-starts-with-picking/ (secondary).
13. Goods-to-person station: up to 1,000 picks per hour (vendor). Source: https://ssi-schaefer.com/en-de/how-can-the-picking-performance-be-improved--746848 (secondary).
14. GS1 keys: SSCC names a logistic unit (case, pallet, parcel); GTIN names a trade item; GLN names a location. Sources: https://www.gs1.org/standards/id-keys/sscc ; https://www.gs1.org/standards/id-keys/gtin ; https://www.gs1.org/standards/id-keys/gln (verified).
15. Record inaccuracy: "65%" of records (DeHoratius and Raman 2008, UNVERIFIED; re-check against the paper). Source: https://www.scribd.com/document/619909654/dehoratius2008 (not primary).

## Gaps and next steps

- Read Coupang 10-K Item 2 (Properties) in full to confirm the center count and the square footage split (owned vs leased). Try WebFetch with offset 0 and a prompt that asks only for Item 2.
- Open the Coupang WMS newsroom article through another route (the 403 blocked curl). The article is the only Coupang source that describes its WMS.
- Find a primary source for the "within 10 minutes" claim, or drop it. Korean-language newsroom search for the delivery-time claim is the next step.
- Read the DeHoratius and Raman paper from pubsonline.informs.org to confirm the 65% figure.
- Find GS1 General Specifications for GTIN, SSCC and GLN digit lengths, and the EANCOM DESADV mapping for ASN.
- Find an MHI or independent pick-rate study. None was located.
- Find Zebra or Honeywell primary docs on offline and batch scanning, and on warehouse Wi-Fi roaming behavior.
- Find Oracle WMS Cloud and SAP EWM pages for cycle counting, short-pick handling and directed putaway (none read yet).
- Check Picnic's WMS post directly at its jobs.picnic.app or blog.picnic.nl URL (current URL returned 404 on the redirect target).
- Check the Ocado press centre fact sheet directly (WebFetch failed).
