-- ==============================================================================
-- DATABASE: production_db (PostgreSQL - Fallback for Oracle)
-- DESCRIPTION: Hệ thống quản lý Sản xuất
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS production_db;
SET search_path TO production_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng factories (Xưởng sản xuất)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS factories (
    factory_id SERIAL PRIMARY KEY,
    factory_code VARCHAR(50) NOT NULL UNIQUE,
    factory_name VARCHAR(100),
    region VARCHAR(50) NOT NULL,
    address VARCHAR(255),
    capacity INT NOT NULL,
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng production_orders (Lệnh sản xuất)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_orders (
    production_order_id SERIAL PRIMARY KEY,
    production_order_number VARCHAR(50) NOT NULL UNIQUE,
    factory_id INT NOT NULL,
    product_id INT NOT NULL,
    employee_id INT NOT NULL,
    planned_quantity INT NOT NULL,
    actual_quantity INT NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_po_factory FOREIGN KEY (factory_id) REFERENCES factories(factory_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng finished_products (Thành phẩm nhập kho)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS finished_products (
    finished_product_id SERIAL PRIMARY KEY,
    production_order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    production_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    warehouse_id INT NOT NULL,
    
    CONSTRAINT fk_fp_order FOREIGN KEY (production_order_id) REFERENCES production_orders(production_order_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng raw_materials (Nguyên vật liệu)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_materials (
    material_id SERIAL PRIMARY KEY,
    material_code VARCHAR(50) NOT NULL UNIQUE,
    material_name VARCHAR(100),
    unit VARCHAR(50)
);

-- ------------------------------------------------------------------------------
-- 5. Bảng production_order_items (Định mức nguyên liệu)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_order_items (
    production_order_item_id SERIAL PRIMARY KEY,
    production_order_id INT NOT NULL,
    material_id INT NOT NULL,
    plan VARCHAR(100),
    ned_quantity INT NOT NULL,
    actual_quantity INT NOT NULL,
    
    CONSTRAINT fk_poi_order FOREIGN KEY (production_order_id) REFERENCES production_orders(production_order_id),
    CONSTRAINT fk_poi_material FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
);

-- ------------------------------------------------------------------------------
-- 6. Bảng material_consumptions (Thực tế tiêu hao nguyên liệu)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS material_consumptions (
    consumption_id SERIAL PRIMARY KEY,
    production_order_id INT NOT NULL,
    material_id INT NOT NULL,
    employee_id INT NOT NULL,
    quantity INT NOT NULL,
    consumed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_mc_order FOREIGN KEY (production_order_id) REFERENCES production_orders(production_order_id),
    CONSTRAINT fk_mc_material FOREIGN KEY (material_id) REFERENCES raw_materials(material_id)
);
