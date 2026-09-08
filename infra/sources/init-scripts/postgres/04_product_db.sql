-- ==============================================================================
-- DATABASE: product_db (PostgreSQL)
-- DESCRIPTION: Hệ thống quản lý danh mục sản phẩm (Master Data)
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS product_db;
SET search_path TO product_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng categories (Danh mục ngành hàng)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categories (
    category_id SERIAL PRIMARY KEY,
    category_code VARCHAR(50) NOT NULL UNIQUE,
    category_name VARCHAR(100),
    parent_category_id INT, -- Có thể NULL nếu là cấp cao nhất
    
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id) REFERENCES categories(category_id)
);

-- ------------------------------------------------------------------------------
-- 2. Bảng brands (Thương hiệu)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS brands (
    brand_id SERIAL PRIMARY KEY,
    brand_code VARCHAR(50) NOT NULL UNIQUE,
    brand_name VARCHAR(100)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng products (Sản phẩm)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) NOT NULL UNIQUE,
    product_name VARCHAR(255),
    category_id INT NOT NULL,
    brand_id INT NOT NULL,
    employee_id INT, -- Người tạo
    unit VARCHAR(50),
    barcode VARCHAR(100),
    product_type VARCHAR(100),
    cost_price DECIMAL(18,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(category_id),
    CONSTRAINT fk_products_brand FOREIGN KEY (brand_id) REFERENCES brands(brand_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng product_prices (Bảng giá sản phẩm)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_prices (
    price_id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    price_type VARCHAR(100) NOT NULL, -- Retail, Wholesale, Online
    price DECIMAL(18,2) NOT NULL,
    currency_code VARCHAR(50) NOT NULL,
    effective_from DATE,
    effective_to DATE,
    
    CONSTRAINT fk_product_prices_product FOREIGN KEY (product_id) REFERENCES products(product_id)
);
