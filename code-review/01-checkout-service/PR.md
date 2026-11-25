# PR 1187: Checkout v2 in checkout-service

**Author:** a mid-level engineer, 14 months on the team. First PR in this service.
**Reviewers:** you (required approver), one peer (already approved: "LGTM, nice and clean").
**CI:** green. 1 unit test added.
**Labels:** `low-risk`, `needs-review-today`

## What

Moves checkout out of the monolith into `checkout-service`. Mostly a copy of the monolith code, cleaned up.

- `POST /v2/checkout` places an order: reserves stock, prices the cart, charges the card, publishes `order-events`, writes an audit row.
- Overselling is prevented: `placeOrder` is `synchronized`.
- Promotion prices are cached in memory (`PriceCache`). This saves a ~200 ms call to the promotion service per cart line.
- The card processor is flaky (~0.5% timeouts), so `PaymentClient` retries up to 3 times.
- The audit row has its own transaction, so it is kept even if the order rolls back.
- `OrderHistoryService` for the new "My orders" page, and `OrderSearchDao` for the back-office search screen.
- `OrderStats` counters for the ops dashboard.
- `OrderStatus`: copied from the monolith, plus a new `PAYMENT_PENDING` for the async payment flow (next PR). The monolith enum is `CREATED, PAID, SHIPPED, CANCELLED`.
- Migration `V42`: adds `orders.payment_id` with an index, and the `audit_log` table.

## Context

| | |
|---|---|
| Runtime | Java 21, Spring Boot 3, PostgreSQL 16 (the monolith's database, shared) |
| Deployment | 6 pods, 200 Tomcat request threads each, HikariCP pool of 10 per pod |
| Traffic | 150 checkouts/s normal, 1,200 checkouts/s peak during flash sales (next sale in 9 days) |
| Payment processor | p50 300 ms, p99 2 s. `POST /charges` accepts an `Idempotency-Key` header |
| SLO | checkout p99 under 800 ms, 99.95% success |
| Rollout | the gateway routes `/checkout` to `checkout-service` as soon as it deploys. The monolith's checkout stays up for mobile app v5 until that app is retired (~30% of checkouts) |

## Testing

- `CheckoutServiceTest.placesOrder` covers the happy path.
- Tested manually on staging with 3 orders.

## Files

```
src/main/java/com/shop/checkout/
  CheckoutController.java     34 lines
  CheckoutRequest.java        10
  CheckoutService.java        73   <- start here
  PaymentClient.java          70
  PriceCache.java             49
  OrderStats.java             35
  OrderHistoryService.java    40
  OrderSearchDao.java         23
  Order.java                  75
  OrderItem.java              47
  OrderStatus.java             9
  Product.java                39
  AuditEntry.java             37
  OrderEventPublisher.java     6
  ProductRepository.java, OrderRepository.java, AuditRepository.java   (Spring Data, empty)
src/main/resources/db/
  V42__checkout_v2.sql        new
  existing-schema.sql         reference only, not changed
src/test/java/com/shop/checkout/
  CheckoutServiceTest.java    44
```
