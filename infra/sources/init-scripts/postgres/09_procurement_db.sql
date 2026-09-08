-- ==============================================================================
-- DATABASE: procurement_db (PostgreSQL - Fallback for Oracle)
-- DESCRIPTION: Hệ thống quản lý Mua hàng
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS procurement_db;
SET search_path TO procurement_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng suppliers
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(50) NOT NULL UNIQUE,
    supplier_name VARCHAR(100),
    supplier_type VARCHAR(100),
    tax_code VARCHAR(50) NOT NULL UNIQUE,
    phone VARCHAR(100),
    email VARCHAR(100),
    address VARCHAR(255),
    country INT NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 2. Bảng purchase_orders
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_orders (
    purchase_order_id SERIAL PRIMARY KEY,
    po_numder VARCHAR(100) UNIQUE,
    supplier_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    employee_id INT NOT NULL,
    order_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expected_date TIMESTAMP NOT NULL,
    currency_code VARCHAR(50) NOT NULL,
    total_amount DECIMAL(18,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_po_supplier FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng purchase_order_items
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purchase_order_items (
    purchase_order_item_id SERIAL PRIMARY KEY,
    purchase_order_id INT NOT NULL,
    product_id INT NOT NULL,
    ordered_quantity INT NOT NULL,
    unit_price DECIMAL(18,2) NOT NULL,
    tax_amount DECIMAL(18,2) NOT NULL,
    discount_amount DECIMAL(18,2) NOT NULL,
    line_amount DECIMAL(18,2) NOT NULL,
    
    CONSTRAINT fk_po_items_po FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(purchase_order_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng goods_receipts
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goods_receipts (
    goods_receipt_id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) NOT NULL UNIQUE,
    purchase_order_id INT NOT NULL,
    warehouse_id INT NOT NULL,
    receipt_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    employee_id INT NOT NULL,
    
    CONSTRAINT fk_gr_po FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(purchase_order_id)
);

-- ------------------------------------------------------------------------------
-- 5. Bảng goods_receipt_items
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS goods_receipt_items (
    goods_receipt_item_id SERIAL PRIMARY KEY,
    goods_receipt_id INT NOT NULL,
    product_id INT NOT NULL,
    purchase_order_item_id INT NOT NULL,
    ordered_quantity INT NOT NULL,
    received_quantity INT NOT NULL,
    rejected_quantity INT NOT NULL,
    
    CONSTRAINT fk_gri_gr FOREIGN KEY (goods_receipt_id) REFERENCES goods_receipts(goods_receipt_id),
    CONSTRAINT fk_gri_poi FOREIGN KEY (purchase_order_item_id) REFERENCES purchase_order_items(purchase_order_item_id)
);
