package com.shop.checkout;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class CheckoutService {

    private final ProductRepository products;
    private final OrderRepository orders;
    private final AuditRepository audits;
    private final PaymentClient payments;
    private final PriceCache prices;
    private final OrderEventPublisher events;
    private final OrderStats stats;

    public CheckoutService(ProductRepository products, OrderRepository orders, AuditRepository audits,
                           PaymentClient payments, PriceCache prices, OrderEventPublisher events,
                           OrderStats stats) {
        this.products = products;
        this.orders = orders;
        this.audits = audits;
        this.payments = payments;
        this.prices = prices;
        this.events = events;
        this.stats = stats;
    }

    // synchronized so two shoppers cannot buy the last unit at the same time
    @Transactional
    public synchronized Order placeOrder(CheckoutRequest req) throws PaymentClient.PaymentDeclinedException {
        Order order = new Order(req.customerId());
        double total = 0;

        for (CheckoutRequest.Line line : req.lines()) {
            Product p = products.findById(line.productId()).get();
            if (p.getStock() < line.qty()) {
                throw new OutOfStockException(p.getSku());
            }
            p.setStock(p.getStock() - line.qty());
            products.save(p);

            double unitPrice = line.unitPrice() > 0 ? line.unitPrice() : prices.priceOf(p.getSku(), p.getPrice());
            total += unitPrice * line.qty();
            order.addItem(p, line.qty(), unitPrice);
        }

        order.setTotal(total);
        orders.save(order);

        String chargeId = payments.charge(req.customerId(), req.cardNumber(), req.cvv(), total);
        order.setPaymentId(chargeId);
        order.setStatus(OrderStatus.PAID);

        events.publish("order-events", order.getId().toString(), "PLACED:" + order.getId());
        recordAudit(order);
        stats.increment();
        return order;
    }

    // own transaction, so the audit row survives even if the order rolls back
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void recordAudit(Order order) {
        audits.save(new AuditEntry("ORDER_PLACED", order.getId(), order.toString()));
    }

    public static class OutOfStockException extends RuntimeException {
        public OutOfStockException(String sku) {
            super("out of stock: " + sku);
        }
    }
}
