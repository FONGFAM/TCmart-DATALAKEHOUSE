-- ==============================================================================
-- DATABASE: invoice_db (PostgreSQL)
-- DESCRIPTION: Hệ thống quản lý hóa đơn điện tử GTGT
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS invoice_db;
SET search_path TO invoice_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng invoices (Hóa đơn điện tử)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    invoice_type VARCHAR(100),
    invoice_date TIMESTAMP NOT NULL,
    seller_tax_code VARCHAR(50) NOT NULL,
    buyer_tax_code VARCHAR(50) NOT NULL,
    buyer_name VARCHAR(255),
    currency_code VARCHAR(50) NOT NULL,
    subtotal DECIMAL(18,2) NOT NULL,
    tax_amount DECIMAL(18,2) NOT NULL,
    total_amount DECIMAL(18,2) NOT NULL,
    xml_file_name VARCHAR(255),
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng invoice_items (Chi tiết sản phẩm trên hóa đơn)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL,
    product_id INT, -- Có thể NULL nếu hàng ngoài hệ thống
    tax_rate DECIMAL(18,2) NOT NULL,
    description VARCHAR(255),
    quantity INT NOT NULL,
    unit_price DECIMAL(18,2) NOT NULL,
    discount_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
    tax_amount DECIMAL(18,2) NOT NULL,
    line_total DECIMAL(18,2) NOT NULL,
    
    CONSTRAINT fk_invoice_items_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng invoice_taxes (Tổng hợp thuế VAT theo mức thuế suất)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoice_taxes (
    invoice_tax_id SERIAL PRIMARY KEY,
    invoice_id INT NOT NULL,
    tax_rate DECIMAL(18,2) NOT NULL,
    taxable_amount DECIMAL(18,2) NOT NULL,
    tax_amount DECIMAL(18,2) NOT NULL,
    
    CONSTRAINT fk_invoice_taxes_invoice FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
);
