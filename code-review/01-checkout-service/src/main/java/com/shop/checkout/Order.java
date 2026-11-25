package com.shop.checkout;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.Table;

@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private Long customerId;
    private OrderStatus status = OrderStatus.CREATED;
    private double total;
    private String paymentId;
    private LocalDateTime createdAt = LocalDateTime.now();

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items = new ArrayList<>();

    protected Order() {
    }

    public Order(Long customerId) {
        this.customerId = customerId;
    }

    public void addItem(Product product, int quantity, double unitPrice) {
        items.add(new OrderItem(this, product, quantity, unitPrice));
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Long getCustomerId() { return customerId; }
    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) { this.status = status; }
    public double getTotal() { return total; }
    public void setTotal(double total) { this.total = total; }
    public String getPaymentId() { return paymentId; }
    public void setPaymentId(String paymentId) { this.paymentId = paymentId; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public List<OrderItem> getItems() { return items; }

    @Override
    public boolean equals(Object o) {
        if (!(o instanceof Order other)) {
            return false;
        }
        return Objects.equals(id, other.id) && Objects.equals(customerId, other.customerId)
                && status == other.status && total == other.total && Objects.equals(items, other.items);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, customerId, status, total, items);
    }

    @Override
    public String toString() {
        return "Order{id=" + id + ", customerId=" + customerId + ", status=" + status
                + ", total=" + total + ", items=" + items + "}";
    }
}
