-- New in this PR. Runs automatically (Flyway) when the first checkout-service pod starts.

ALTER TABLE orders ADD COLUMN payment_id VARCHAR(64);
CREATE INDEX idx_orders_payment_id ON orders (payment_id);

CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    action      VARCHAR(32) NOT NULL,
    order_id    BIGINT,
    details     TEXT,
    created_at  TIMESTAMP
);
