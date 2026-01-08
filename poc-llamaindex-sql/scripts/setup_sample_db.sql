-- Sample database setup for LlamaIndex POC
-- Run: psql $POSTGRES_URI -f scripts/setup_sample_db.sql

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

COMMENT ON TABLE customers IS 'Store customer information including contact details';
COMMENT ON COLUMN customers.name IS 'Full name of the customer';
COMMENT ON COLUMN customers.email IS 'Email address (unique identifier)';

-- Products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0
);

COMMENT ON TABLE products IS 'Product catalog with pricing and inventory';
COMMENT ON COLUMN products.category IS 'Product category (Electronics, Furniture, etc.)';
COMMENT ON COLUMN products.price IS 'Unit price in USD';

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2)
);

COMMENT ON TABLE orders IS 'Customer orders with status tracking';
COMMENT ON COLUMN orders.status IS 'Order status: pending, shipped, completed, cancelled';

-- Order items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL
);

COMMENT ON TABLE order_items IS 'Line items for each order';

-- Insert sample data
INSERT INTO customers (name, email, city, country) VALUES
    ('Alice Johnson', 'alice@example.com', 'New York', 'USA'),
    ('Bob Smith', 'bob@example.com', 'Los Angeles', 'USA'),
    ('Carol White', 'carol@example.com', 'Chicago', 'USA'),
    ('David Brown', 'david@example.com', 'Houston', 'USA'),
    ('Eve Davis', 'eve@example.com', 'Phoenix', 'USA');

INSERT INTO products (name, category, price, stock_quantity) VALUES
    ('Laptop Pro', 'Electronics', 1299.99, 50),
    ('Wireless Mouse', 'Electronics', 29.99, 200),
    ('Office Chair', 'Furniture', 299.99, 40),
    ('Standing Desk', 'Furniture', 599.99, 25),
    ('Notebook Set', 'Office Supplies', 12.99, 500);

INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
    (1, NOW() - INTERVAL '30 days', 'completed', 1329.98),
    (1, NOW() - INTERVAL '15 days', 'completed', 299.99),
    (2, NOW() - INTERVAL '20 days', 'completed', 629.98),
    (3, NOW() - INTERVAL '10 days', 'shipped', 29.99),
    (4, NOW() - INTERVAL '5 days', 'pending', 1299.99);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 1, 1, 1299.99), (1, 2, 1, 29.99),
    (2, 3, 1, 299.99),
    (3, 4, 1, 599.99), (3, 2, 1, 29.99),
    (4, 2, 1, 29.99),
    (5, 1, 1, 1299.99);

SELECT 'Setup complete!' as status;
