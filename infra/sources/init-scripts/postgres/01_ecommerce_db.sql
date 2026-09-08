-- ==============================================================================
-- DATABASE: ecommerce_db (PostgreSQL)
-- DESCRIPTION: Hệ thống bán hàng thương mại điện tử (Web/App)
-- ==============================================================================

-- Bật schema riêng biệt cho gọn gàng (nếu cần thiết, hiện tại dùng chung public)
CREATE SCHEMA IF NOT EXISTS ecommerce_db;
SET search_path TO ecommerce_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng customers (Khách hàng)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    customer_code VARCHAR(50) NOT NULL UNIQUE,
    fullname VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(100),
    gender VARCHAR(100),
    date_of_birth DATE NOT NULL,
    country INT NOT NULL,
    customer_type VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng online_orders (Đơn hàng online Web/App)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS online_orders (
    online_order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id INT NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    channel VARCHAR(50) NOT NULL,
    currency_code VARCHAR(50) NOT NULL,
    subtotal DECIMAL(18,2) NOT NULL,
    discount_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    shipping_fee DECIMAL(18,2), -- đổi từ varchar sang decimal cho đúng bản chất
    total_amount DECIMAL(18,2) NOT NULL,
    order_status VARCHAR(100),
    
    CONSTRAINT fk_online_orders_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng delivery_addresses (Địa chỉ giao hàng)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS delivery_addresses (
    address_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    recipient_name VARCHAR(100),
    phone VARCHAR(100),
    country INT NOT NULL,
    province VARCHAR(100),
    district VARCHAR(100),
    ward VARCHAR(100),
    address_detail VARCHAR(100),
    is_default BOOLEAN, -- Đổi từ varchar sang boolean
    
    CONSTRAINT fk_delivery_address_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng online_order_items (Chi tiết sản phẩm đơn online)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS online_order_items (
    online_order_item_id SERIAL PRIMARY KEY,
    online_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(18,2) NOT NULL,
    discount_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    line_total DECIMAL(18,2) NOT NULL,
    
    CONSTRAINT fk_order_items_order FOREIGN KEY (online_order_id) REFERENCES online_orders(online_order_id)
    -- product_id trỏ sang hệ thống Master Data (Product DB) nên không tạo FK cứng ở đây
);

-- ------------------------------------------------------------------------------
-- 5. Bảng payments (Thanh toán đơn online)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments (
    payment_id SERIAL PRIMARY KEY,
    online_order_id INT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_code VARCHAR(50) NOT NULL UNIQUE,
    amount DECIMAL(18,2) NOT NULL,
    currency_code VARCHAR(50) NOT NULL,
    payment_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_payments_order FOREIGN KEY (online_order_id) REFERENCES online_orders(online_order_id)
);
