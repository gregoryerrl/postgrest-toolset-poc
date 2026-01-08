-- Shared Sample Database Setup
-- Used by all POCs for consistent testing
-- Run: psql -h localhost -U postgres -d testdb -f shared/setup_sample_db.sql

-- Clean up existing tables
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- ============================================================
-- CUSTOMERS TABLE
-- Stores customer information
-- ============================================================
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'USA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE customers IS 'Customer information including contact details and location';
COMMENT ON COLUMN customers.id IS 'Unique customer identifier';
COMMENT ON COLUMN customers.name IS 'Full name of the customer';
COMMENT ON COLUMN customers.email IS 'Email address (unique)';
COMMENT ON COLUMN customers.city IS 'City of residence';
COMMENT ON COLUMN customers.country IS 'Country of residence';

-- ============================================================
-- PRODUCTS TABLE
-- Stores product catalog
-- ============================================================
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE products IS 'Product catalog with pricing and inventory';
COMMENT ON COLUMN products.category IS 'Product category (Electronics, Furniture, Office Supplies)';
COMMENT ON COLUMN products.price IS 'Unit price in USD';
COMMENT ON COLUMN products.stock_quantity IS 'Current inventory count';

-- ============================================================
-- ORDERS TABLE
-- Stores order headers
-- ============================================================
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2),
    shipping_address TEXT,
    notes TEXT
);

COMMENT ON TABLE orders IS 'Order headers with status and totals';
COMMENT ON COLUMN orders.status IS 'Order status: pending, processing, shipped, completed, cancelled';
COMMENT ON COLUMN orders.total_amount IS 'Total order value in USD';

-- ============================================================
-- ORDER_ITEMS TABLE
-- Stores order line items
-- ============================================================
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL
);

COMMENT ON TABLE order_items IS 'Individual line items within an order';
COMMENT ON COLUMN order_items.quantity IS 'Number of units ordered';
COMMENT ON COLUMN order_items.unit_price IS 'Price per unit at time of order';

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Insert customers (5 customers)
INSERT INTO customers (name, email, city, country) VALUES
    ('Alice Johnson', 'alice@example.com', 'New York', 'USA'),
    ('Bob Smith', 'bob@example.com', 'Los Angeles', 'USA'),
    ('Carol White', 'carol@example.com', 'Chicago', 'USA'),
    ('David Brown', 'david@example.com', 'Houston', 'USA'),
    ('Eve Davis', 'eve@example.com', 'Phoenix', 'USA'),
    ('Frank Miller', 'frank@example.com', 'Philadelphia', 'USA'),
    ('Grace Wilson', 'grace@example.com', 'San Antonio', 'USA'),
    ('Henry Taylor', 'henry@example.com', 'San Diego', 'USA');

-- Insert products (8 products across 3 categories)
INSERT INTO products (name, category, price, stock_quantity) VALUES
    ('Laptop Pro 15"', 'Electronics', 1299.99, 50),
    ('Wireless Mouse', 'Electronics', 29.99, 200),
    ('USB-C Hub', 'Electronics', 49.99, 150),
    ('Office Chair Deluxe', 'Furniture', 299.99, 40),
    ('Standing Desk', 'Furniture', 599.99, 25),
    ('Monitor Stand', 'Furniture', 79.99, 100),
    ('Notebook Set (3-pack)', 'Office Supplies', 12.99, 500),
    ('Pen Collection', 'Office Supplies', 8.99, 300);

-- Insert orders with various statuses
INSERT INTO orders (customer_id, order_date, status, total_amount, shipping_address) VALUES
    (1, NOW() - INTERVAL '45 days', 'completed', 1329.98, '123 Main St, New York, NY'),
    (1, NOW() - INTERVAL '30 days', 'completed', 299.99, '123 Main St, New York, NY'),
    (2, NOW() - INTERVAL '25 days', 'completed', 679.98, '456 Oak Ave, Los Angeles, CA'),
    (3, NOW() - INTERVAL '20 days', 'completed', 629.98, '789 Pine Rd, Chicago, IL'),
    (4, NOW() - INTERVAL '15 days', 'shipped', 1299.99, '321 Elm St, Houston, TX'),
    (5, NOW() - INTERVAL '10 days', 'shipped', 349.98, '654 Cedar Ln, Phoenix, AZ'),
    (6, NOW() - INTERVAL '5 days', 'processing', 29.99, '987 Birch Dr, Philadelphia, PA'),
    (7, NOW() - INTERVAL '3 days', 'pending', 599.99, '147 Maple Way, San Antonio, TX'),
    (8, NOW() - INTERVAL '1 day', 'pending', 91.97, '258 Walnut Blvd, San Diego, CA'),
    (2, NOW() - INTERVAL '2 days', 'pending', 1349.98, '456 Oak Ave, Los Angeles, CA');

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    -- Order 1: Laptop + Mouse
    (1, 1, 1, 1299.99),
    (1, 2, 1, 29.99),
    -- Order 2: Office Chair
    (2, 4, 1, 299.99),
    -- Order 3: Standing Desk + Monitor Stand
    (3, 5, 1, 599.99),
    (3, 6, 1, 79.99),
    -- Order 4: USB-C Hub + Standing Desk
    (4, 3, 1, 49.99),
    (4, 5, 1, 579.99),
    -- Order 5: Laptop
    (5, 1, 1, 1299.99),
    -- Order 6: Office Chair + USB-C Hub
    (6, 4, 1, 299.99),
    (6, 3, 1, 49.99),
    -- Order 7: Mouse
    (7, 2, 1, 29.99),
    -- Order 8: Standing Desk
    (8, 5, 1, 599.99),
    -- Order 9: Notebooks + Pens + Monitor Stand
    (9, 7, 3, 12.99),
    (9, 8, 2, 8.99),
    (9, 6, 1, 79.99),
    -- Order 10: Laptop + USB-C Hub
    (10, 1, 1, 1299.99),
    (10, 3, 1, 49.99);

-- ============================================================
-- CREATE USEFUL VIEWS
-- ============================================================

-- View: Order summary with customer names
CREATE OR REPLACE VIEW order_summary AS
SELECT
    o.id AS order_id,
    c.name AS customer_name,
    c.email AS customer_email,
    o.order_date,
    o.status,
    o.total_amount,
    COUNT(oi.id) AS item_count
FROM orders o
JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, c.name, c.email, o.order_date, o.status, o.total_amount;

-- View: Product sales summary
CREATE OR REPLACE VIEW product_sales AS
SELECT
    p.id AS product_id,
    p.name AS product_name,
    p.category,
    p.price AS current_price,
    p.stock_quantity,
    COALESCE(SUM(oi.quantity), 0) AS total_sold,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS total_revenue
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY p.id, p.name, p.category, p.price, p.stock_quantity;

-- View: Customer lifetime value
CREATE OR REPLACE VIEW customer_ltv AS
SELECT
    c.id AS customer_id,
    c.name,
    c.email,
    c.city,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS lifetime_value,
    MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id, c.name, c.email, c.city;

-- ============================================================
-- VERIFICATION
-- ============================================================
SELECT '=== Database Setup Complete ===' AS message;
SELECT 'Tables created:' AS info;
SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS columns
FROM information_schema.tables t
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

SELECT 'Row counts:' AS info;
SELECT 'customers' AS table_name, COUNT(*) AS rows FROM customers
UNION ALL SELECT 'products', COUNT(*) FROM products
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;

SELECT 'Views created:' AS info;
SELECT table_name AS view_name
FROM information_schema.views
WHERE table_schema = 'public';
