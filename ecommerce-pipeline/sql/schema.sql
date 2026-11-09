-- E-commerce data model (PostgreSQL)
DROP TABLE IF EXISTS order_items, orders, customers, products CASCADE;

CREATE TABLE products (
    product_id  INTEGER       PRIMARY KEY,
    title       TEXT          NOT NULL,
    category    TEXT,
    brand       TEXT,
    price       NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    stock       INTEGER       CHECK (stock >= 0),
    rating      NUMERIC(3,2)
);

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    full_name   TEXT    NOT NULL,
    email       TEXT,
    country     TEXT
);

CREATE TABLE orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date  DATE    NOT NULL
);

CREATE TABLE order_items (
    order_item_id BIGSERIAL    PRIMARY KEY,
    order_id      INTEGER      NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id    INTEGER      NOT NULL REFERENCES products(product_id),
    quantity      INTEGER      NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    UNIQUE (order_id, product_id)
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_items_product   ON order_items(product_id);
