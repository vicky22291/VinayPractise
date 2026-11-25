package com.shop.checkout;

import java.time.Instant;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "audit_log")
public class AuditEntry {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String action;
    private Long orderId;
    private String details;
    private Instant createdAt = Instant.now();

    protected AuditEntry() {
    }

    public AuditEntry(String action, Long orderId, String details) {
        this.action = action;
        this.orderId = orderId;
        this.details = details;
    }

    public Long getId() { return id; }
    public String getAction() { return action; }
    public Long getOrderId() { return orderId; }
    public String getDetails() { return details; }
}
