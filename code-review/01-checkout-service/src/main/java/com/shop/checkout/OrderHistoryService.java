package com.shop.checkout;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

import org.springframework.stereotype.Service;

/** GET /v2/orders?customerId=..&page=..&size=.. (controller not in this PR). */
@Service
public class OrderHistoryService {

    private final OrderRepository orders;

    public OrderHistoryService(OrderRepository orders) {
        this.orders = orders;
    }

    public List<OrderSummary> history(Long customerId, int page, int size) {
        List<Order> all = orders.findAll();
        List<OrderSummary> result = new ArrayList<>();

        for (Order o : all) {
            if (o.getCustomerId() == customerId) {
                int itemCount = 0;
                for (OrderItem item : o.getItems()) {
                    itemCount += item.getQuantity();
                }
                result.add(new OrderSummary(o.getId(), o.getStatus(), o.getTotal(), itemCount, o.getCreatedAt()));
            }
        }

        result.sort(Comparator.comparing(OrderSummary::createdAt).reversed());
        return result.subList(page * size, Math.min(result.size(), (page + 1) * size));
    }

    public record OrderSummary(Long id, OrderStatus status, double total, int itemCount, LocalDateTime createdAt) {
    }
}
