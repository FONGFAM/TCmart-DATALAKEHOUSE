-- ==============================================================================
-- DATABASE: exchange_rate_db (PostgreSQL)
-- DESCRIPTION: Hệ thống lưu trữ tỷ giá ngoại tệ
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS exchange_rate_db;
SET search_path TO exchange_rate_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng currencies (Danh mục tiền tệ)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS currencies (
    currency_id SERIAL PRIMARY KEY,
    currency_code VARCHAR(50) NOT NULL UNIQUE,
    currency_name VARCHAR(100),
    symbol VARCHAR(10)
);

-- ------------------------------------------------------------------------------
-- 2. Bảng exchange_rates (Tỷ giá ngoại tệ)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exchange_rates (
    exchange_rate_id SERIAL PRIMARY KEY,
    from_currency VARCHAR(50) NOT NULL,
    to_currency VARCHAR(50) NOT NULL,
    rate DECIMAL(18,5) NOT NULL, -- Tỷ giá nên có phần thập phân dài hơn
    rate_date DATE NOT NULL,
    source VARCHAR(100),
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_ex_rates_from FOREIGN KEY (from_currency) REFERENCES currencies(currency_code),
    CONSTRAINT fk_ex_rates_to FOREIGN KEY (to_currency) REFERENCES currencies(currency_code)
);
