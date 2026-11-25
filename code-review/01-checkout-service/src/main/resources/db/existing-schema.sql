-- Existing tables, owned by the monolith today. NOT changed by this PR. Shown for reference.
-- PostgreSQL 16. Row counts as of last month.

-- ~2M rows
CREATE TABLE products (
    id     BIGSERIAL PRIMARY KEY,
    sku    VARCHAR(64) NOT NULL,
    name   VARCHAR(255),
    price  DOUBLE PRECISION NOT NULL,
    stock  INT NOT NULL
);

-- ~400M rows, ~1.5M inserts a day
CREATE TABLE orders (
    id          BIGSERIAL PRIMARY KEY,
    customer_id BIGINT NOT NULL,
    status      SMALLINT NOT NULL,          -- enum ordinal
    total       DOUBLE PRECISION,
    created_at  TIMESTAMP
);

-- ~1.1B rows
CREATE TABLE order_items (
    id          BIGSERIAL PRIMARY KEY,
    order_id    BIGINT,
    product_id  BIGINT,
    quantity    INT,
    unit_price  DOUBLE PRECISION
);
