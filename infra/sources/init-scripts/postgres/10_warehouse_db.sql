-- ==============================================================================
-- DATABASE: warehouse_db (PostgreSQL - Fallback for Oracle)
-- DESCRIPTION: Hệ thống quản lý Kho bãi
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS warehouse_db;
SET search_path TO warehouse_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng warehouses (Kho hàng)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id SERIAL PRIMARY KEY,
    warehouse_code VARCHAR(50) NOT NULL UNIQUE,
    warehouse_name VARCHAR(100),
    warehouse_type VARCHAR(100),
    region VARCHAR(50) NOT NULL,
    address VARCHAR(255),
    capacity INT NOT NULL,
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng warehouse_locations (Vị trí trong kho)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouse_locations (
    location_id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL,
    location_code VARCHAR(50) NOT NULL UNIQUE,
    location_name VARCHAR(100),
    zone VARCHAR(100),
    
    CONSTRAINT fk_locations_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng inventory_transactions (Giao dịch thẻ kho)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_transactions (
    inventory_transaction_id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL,
    product_id INT NOT NULL,
    transaction_type VARCHAR(100),
    reference_type VARCHAR(100),
    reference_id INT NOT NULL,
    quantity INT NOT NULL,
    transaction_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    employee_id INT NOT NULL,
    
    CONSTRAINT fk_inv_trans_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng inventory (Tồn kho)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL,
    location_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    reserved_quantity INT NOT NULL,
    available_quantity INT NOT NULL,
    last_updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_inv_warehouse FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
    CONSTRAINT fk_inv_location FOREIGN KEY (location_id) REFERENCES warehouse_locations(location_id)
);

-- ------------------------------------------------------------------------------
-- 5. Bảng stock_transfers (Lệnh điều chuyển kho)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_transfers (
    transfer_id SERIAL PRIMARY KEY,
    transfer_number VARCHAR(50) NOT NULL UNIQUE,
    from_warehouse_id INT NOT NULL,
    to_warehouse_id INT NOT NULL,
    employee_id INT NOT NULL,
    transfer_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_trf_from_wh FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(warehouse_id),
    CONSTRAINT fk_trf_to_wh FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(warehouse_id)
);

-- ------------------------------------------------------------------------------
-- 6. Bảng stock_transfer_items (Chi tiết sản phẩm điều chuyển)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS stock_transfer_items (
    transfer_item_id SERIAL PRIMARY KEY,
    transfer_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    
    CONSTRAINT fk_sti_transfer FOREIGN KEY (transfer_id) REFERENCES stock_transfers(transfer_id)
);
