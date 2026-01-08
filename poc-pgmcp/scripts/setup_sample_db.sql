-- Sample database setup for PGMCP POC
-- Run: psql $DATABASE_URL -f scripts/setup_sample_db.sql

-- Clean up existing tables
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'USA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2)
);

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- Insert sample data
INSERT INTO customers (name, email, city, country) VALUES
    ('Alice Johnson', 'alice@example.com', 'New York', 'USA'),
    ('Bob Smith', 'bob@example.com', 'Los Angeles', 'USA'),
    ('Carol White', 'carol@example.com', 'Chicago', 'USA'),
    ('David Brown', 'david@example.com', 'Houston', 'USA'),
    ('Eve Davis', 'eve@example.com', 'Phoenix', 'USA'),
    ('Frank Miller', 'frank@example.com', 'Seattle', 'USA'),
    ('Grace Lee', 'grace@example.com', 'Boston', 'USA');

INSERT INTO products (name, category, price, stock_quantity) VALUES
    ('Laptop Pro 15', 'Electronics', 1299.99, 50),
    ('Wireless Mouse', 'Electronics', 29.99, 200),
    ('USB-C Hub', 'Electronics', 49.99, 150),
    ('Mechanical Keyboard', 'Electronics', 149.99, 75),
    ('Monitor 27"', 'Electronics', 399.99, 30),
    ('Office Chair', 'Furniture', 299.99, 40),
    ('Standing Desk', 'Furniture', 599.99, 25),
    ('Desk Lamp', 'Furniture', 39.99, 100),
    ('Notebook Set', 'Office Supplies', 12.99, 500),
    ('Pen Pack', 'Office Supplies', 8.99, 1000);

INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
    (1, NOW() - INTERVAL '60 days', 'completed', 1329.98),
    (1, NOW() - INTERVAL '30 days', 'completed', 299.99),
    (2, NOW() - INTERVAL '45 days', 'completed', 629.98),
    (2, NOW() - INTERVAL '15 days', 'completed', 149.99),
    (3, NOW() - INTERVAL '20 days', 'shipped', 449.98),
    (4, NOW() - INTERVAL '10 days', 'shipped', 29.99),
    (5, NOW() - INTERVAL '5 days', 'pending', 1299.99),
    (6, NOW() - INTERVAL '3 days', 'pending', 599.99),
    (7, NOW() - INTERVAL '1 day', 'pending', 49.99);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1299.99), (1, 2, 1, 29.99),
    (2, 6, 1, 299.99),
    (3, 7, 1, 599.99), (3, 2, 1, 29.99),
    (4, 4, 1, 149.99),
    (5, 5, 1, 399.99), (5, 3, 1, 49.99),
    (6, 2, 1, 29.99),
    (7, 1, 1, 1299.99),
    (8, 7, 1, 599.99),
    (9, 3, 1, 49.99);

-- Verify
SELECT 'Setup complete!' as status,
       (SELECT COUNT(*) FROM customers) as customers,
       (SELECT COUNT(*) FROM products) as products,
       (SELECT COUNT(*) FROM orders) as orders;
