-- PostgreSQL schema for Sales Analytics project
CREATE TABLE IF NOT EXISTS customers (
  customer_id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  signup_date DATE,
  country VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS products (
  product_id SERIAL PRIMARY KEY,
  sku VARCHAR(64) UNIQUE NOT NULL,
  name VARCHAR(255),
  category VARCHAR(100),
  price NUMERIC(12,2) CHECK (price >= 0)
);

CREATE TABLE IF NOT EXISTS orders (
  order_id SERIAL PRIMARY KEY,
  order_external_id VARCHAR(64) UNIQUE NOT NULL,
  customer_id INT NOT NULL REFERENCES customers(customer_id),
  order_date TIMESTAMP NOT NULL,
  status VARCHAR(50),
  total_amount NUMERIC(12,2) CHECK (total_amount >= 0)
);

CREATE TABLE IF NOT EXISTS order_items (
  order_item_id SERIAL PRIMARY KEY,
  order_id INT NOT NULL REFERENCES orders(order_id),
  product_id INT NOT NULL REFERENCES products(product_id),
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
  line_total NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS shipments (
  shipment_id SERIAL PRIMARY KEY,
  order_id INT NOT NULL REFERENCES orders(order_id),
  shipped_date DATE,
  delivery_date DATE,
  carrier VARCHAR(100),
  tracking_number VARCHAR(128)
);

CREATE INDEX IF NOT EXISTS idx_orders_order_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);