-- ==============================================================================
-- DATABASE: franchise_db (PostgreSQL)
-- DESCRIPTION: Hệ thống quản lý đại lý nhượng quyền (Franchise)
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS franchise_db;
SET search_path TO franchise_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng franchisees (Đại lý nhượng quyền)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS franchisees (
    franchisee_id SERIAL PRIMARY KEY,
    franchisee_code VARCHAR(50) NOT NULL UNIQUE,
    franchisee_name VARCHAR(100),
    owner_name VARCHAR(100),
    phone VARCHAR(100),
    email VARCHAR(100),
    region VARCHAR(50) NOT NULL,
    city VARCHAR(100),
    address VARCHAR(255),
    contract_start DATE,
    contract_end DATE,
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng franchise_orders (Đơn mua sỉ của đại lý)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS franchise_orders (
    franchisee_order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) NOT NULL UNIQUE,
    franchisee_id INT NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    currency_code VARCHAR(50) NOT NULL,
    total_amount DECIMAL(18,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_franchise_orders_franchisee FOREIGN KEY (franchisee_id) REFERENCES franchisees(franchisee_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng franchise_monthly_reports (Báo cáo doanh thu tháng của đại lý)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS franchise_monthly_reports (
    report_id SERIAL PRIMARY KEY,
    franchisee_id INT NOT NULL,
    report_month VARCHAR(10) NOT NULL, -- YYYY-MM
    total_sales DECIMAL(18,2) NOT NULL,
    total_quantity DECIMAL(18,2) NOT NULL,
    return_quantity INT NOT NULL DEFAULT 0,
    net_sales DECIMAL(18,2),
    file_name VARCHAR(255),
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_reports_franchisee FOREIGN KEY (franchisee_id) REFERENCES franchisees(franchisee_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng franchise_orders_items (Chi tiết đơn mua sỉ)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS franchise_orders_items (
    franchisee_order_item_id SERIAL PRIMARY KEY,
    franchisee_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(18,2) NOT NULL,
    discount_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    line_total DECIMAL(18,2) NOT NULL,
    
    CONSTRAINT fk_order_items_order FOREIGN KEY (franchisee_order_id) REFERENCES franchise_orders(franchisee_order_id)
);
