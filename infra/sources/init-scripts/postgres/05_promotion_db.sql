-- ==============================================================================
-- DATABASE: promotion_db (PostgreSQL)
-- DESCRIPTION: Hệ thống quản lý chương trình khuyến mãi
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS promotion_db;
SET search_path TO promotion_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng promotions (Chương trình khuyến mãi)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS promotions (
    promotion_id SERIAL PRIMARY KEY,
    promotion_code VARCHAR(50) NOT NULL UNIQUE,
    promotion_name VARCHAR(255),
    promotion_type VARCHAR(100),
    employee_id INT, -- Người tạo
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng promotion_products (Sản phẩm tham gia KM)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS promotion_products (
    promotion_product_id SERIAL PRIMARY KEY,
    promotion_id INT NOT NULL,
    product_id INT NOT NULL,
    
    CONSTRAINT fk_promo_prod_promotion FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng promotion_stores (Cửa hàng áp dụng KM)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS promotion_stores (
    promotion_store_id SERIAL PRIMARY KEY,
    promotion_id INT NOT NULL,
    store_id INT NOT NULL,
    
    CONSTRAINT fk_promo_store_promotion FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng promotion_discounts (Định mức giảm giá KM)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS promotion_discounts (
    discount_id SERIAL PRIMARY KEY,
    promotion_id INT NOT NULL,
    discount_type INT NOT NULL, -- 1: %, 2: VND
    discount_value DECIMAL(18,2) NOT NULL,
    max_discount DECIMAL(18,2) NOT NULL,
    min_order_value DECIMAL(18,2),
    
    CONSTRAINT fk_promo_discount_promotion FOREIGN KEY (promotion_id) REFERENCES promotions(promotion_id)
);
