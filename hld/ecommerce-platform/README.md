# E-commerce marketplace: catalog, cart, checkout, and no overselling

> One-line answer: split the read world from the money world. Catalog and search are a read model fed by change events from the listing database, cached hard and allowed to be seconds stale. The truth about stock lives in one place: an inventory service that keeps `on_hand`, `reserved`, `sold` and `carved` (units set aside for a flash deal) per SKU per stock pool, and changes them only by conditional writes. Checkout is a saga keyed by one idempotency key per order attempt: reserve stock with a short TTL, price the order, authorize the payment, confirm the order and convert the reservation, or release everything on failure. A flash sale on one SKU is the hot spot, so its stock is split into buckets and admitted through a gate that can say "sold out" without touching the database. The red node is that flash-sale SKU's inventory row.

Status: **studied** (solution, diagrams, edge cases, 5 deep dives with runnable simulations, facts survey). Missing: `my-attempt.md` and my excalidraw.

Tier 3, problem #61 in [`hld/README.md`](../README.md). Reported at Coupang for Staff (4 Staff reports on Hello Interview's community board, December 2025 to August 2026), also seen at Udemy, Goldman Sachs and others. Two candidate notes say the round focused on placing the order and inventory management ("double booking" inventory), and on the inventory registration path plus idempotent payments during a flash sale, with overselling kept to a minimum. Related: [`../ticket-booking/`](../ticket-booking/) (the last-room conditional update), [`../payments-ledger/`](../payments-ledger/) (idempotency, attempt ids, unknown outcomes), [`../payments-risk-decisioning/`](../payments-risk-decisioning/) (inline risk at checkout), [`../warehouse-management/`](../warehouse-management/) (#62, physical stock and fulfillment), [`../../concepts/distributed-transactions.md`](../../concepts/distributed-transactions.md), [`../../concepts/caching-patterns.md`](../../concepts/caching-patterns.md), [`../../concepts/exactly-once.md`](../../concepts/exactly-once.md).

## Problem statement (as reported, paraphrased)

Design an eBay-like e-commerce platform. Buyers view products, manage a shopping cart, place orders, check out and pay. Reported follow-ups: placing the order without double booking inventory, the path sellers use to register inventory, idempotent payment during a flash sale, and keeping overselling to a minimum.

Scoping questions to ask in the first 5 minutes:
- **Marketplace or first party?** Both: third-party sellers list offers and ship themselves, and the platform also sells its own stock from its fulfillment centers (Coupang's Rocket model). Stock for the second kind comes from the warehouse system (#62). A fulfillment center that has hit its daily outbound capacity stops taking new orders (Coupang engineering blog), so checkout must pick a center with capacity left.
- **Is "zero oversell" the goal?** Zero for stock we have counted, at the moment of reservation. Physical loss (damage, miscount) is handled after the fact by the warehouse and a cancel or substitute flow.
- **Flash sales?** Yes: a deal opens at a fixed time with limited units, and many buyers arrive in the same second.

## Functional requirements

Core:
1. **Browse and search.** Buyers search and filter products and open a product page with offers, price and availability.
2. **Register inventory.** Sellers create listings (product, variant, offer, price) and set or adjust stock. Warehouse events adjust stock for platform-held inventory.
3. **Cart.** Buyers add, update and remove items, and see current price and availability.
4. **Checkout.** Placing an order reserves stock, prices the order (coupons, shipping, tax), authorizes payment and confirms the order, all safe to retry. Flash sales use the same path.
5. **Orders.** Buyers see order status and history and can cancel before shipment, which releases stock and voids or refunds the payment.

Below the line: recommendations, reviews, ads, returns logistics, seller payouts and settlement, fraud scoring (see #52), fulfillment and warehouse operations (see #62), delivery routing.

## Non-functional requirements

| Dimension | Target |
|---|---|
| Scale | 24.6M active customers (Coupang Q4 2025, [facts survey](research/facts-survey.md)), ~10M daily [estimate]. Product page and search reads ~60k a second at peak. Orders ~3M a day, ~35 a second on average, ~350 at a sale peak [estimate]. Catalog ~500M listings [estimate] |
| Flash sale | One deal with 10k units opens at 10:00. Up to 1M buyers tap "buy" within the first 10 s: ~100k attempts a second on one SKU |
| Latency | Product page p99 under 200 ms. Add to cart p99 under 300 ms. Place order p99 under 2 s, not counting time the buyer spends in a 3-D Secure or bank app step |
| Inventory correctness | Never reserve more units than sellable stock (`on_hand - sold - reserved - carved`). A reservation expires (default 10 min, 5 min for flash deals) and returns to stock if the order is not confirmed. It is not released while a payment outcome is unknown, up to a 30-minute ceiling |
| Payment correctness | One charge per order, whatever the retries. No confirmed order without an authorized payment, and no captured payment without an order. Authorize at place order and capture at shipment, so a short pick or a cancel before shipment is a smaller capture or a void |
| Consistency | Strong per SKU for reservations. Read-your-writes for the cart. Search and product-page availability may lag by seconds (p99 ~3 s) and are re-checked at reserve time. FC stock follows the WMS within 2 s p99 (problem 62) |
| Availability | Browse 99.99%. Checkout 99.95%. A slow payment provider must not take browsing down |

## What interviewers probe

1. Flash sale: 10k units, 1M buyers at 10:00:00. How do you avoid both overselling and melting the database on one hot row?
2. Checkout is reserve, price, pay, confirm. The payment call times out and the buyer taps again. How do you avoid a double charge, a double order, or stock stuck in a reservation?
3. A seller sets stock to 50 while three checkouts are reserving the same SKU. How is no update lost?
4. Search shows "in stock" but checkout says "sold out". How fresh is availability, and where is the truth checked?
5. The price or a coupon changes between the cart and checkout. What does the buyer see and pay?

## Files

[`solution.md`](solution.md) · [`diagrams.md`](diagrams.md) · [`edge-cases.md`](edge-cases.md) · deep dives: [flash sale and hot sku](deep-dives/flash-sale-and-hot-sku.md), [checkout saga and payment idempotency](deep-dives/checkout-saga-and-payment-idempotency.md), [inventory registration and stock model](deep-dives/inventory-registration-and-stock-model.md), [catalog search and read scaling](deep-dives/catalog-search-and-read-scaling.md), [cart and pricing](deep-dives/cart-and-pricing.md) · research: [facts survey](research/facts-survey.md) · missing: `ecommerce-platform.excalidraw` (mine to draw), `my-attempt.md`
