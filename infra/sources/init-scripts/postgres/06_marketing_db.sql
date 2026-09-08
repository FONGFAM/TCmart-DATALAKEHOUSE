-- ==============================================================================
-- DATABASE: marketing_db (PostgreSQL)
-- DESCRIPTION: Hệ thống quản lý chiến dịch Marketing & Quảng cáo
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS marketing_db;
SET search_path TO marketing_db, public;

-- ------------------------------------------------------------------------------
-- 1. Bảng campaigns (Chiến dịch Marketing)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id SERIAL PRIMARY KEY,
    campaign_code VARCHAR(50) NOT NULL UNIQUE,
    campaign_name VARCHAR(255),
    employee_id INT, -- Người tạo
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    budget DECIMAL(18,2),
    status VARCHAR(50) NOT NULL
);

-- ------------------------------------------------------------------------------
-- 2. Bảng campaign_channels (Kênh truyền thông quảng cáo)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campaign_channels (
    channel_id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL,
    channel_name VARCHAR(100),
    
    CONSTRAINT fk_channels_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id)
);

-- ------------------------------------------------------------------------------
-- 3. Bảng impressions (Lượt hiển thị)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS impressions (
    impression_id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL,
    channel_id INT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    impression_count INT NOT NULL,
    
    CONSTRAINT fk_impressions_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    CONSTRAINT fk_impressions_channel FOREIGN KEY (channel_id) REFERENCES campaign_channels(channel_id)
);

-- ------------------------------------------------------------------------------
-- 4. Bảng clicks (Lượt nhấp chuột)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clicks (
    click_id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL,
    channel_id INT NOT NULL,
    event_time TIMESTAMP NOT NULL,
    click_count INT NOT NULL,
    
    CONSTRAINT fk_clicks_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    CONSTRAINT fk_clicks_channel FOREIGN KEY (channel_id) REFERENCES campaign_channels(channel_id)
);

-- ------------------------------------------------------------------------------
-- 5. Bảng campaign_costs (Chi phí quảng cáo)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS campaign_costs (
    cost_id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL,
    channel_id INT NOT NULL,
    cost_date DATE NOT NULL,
    amount DECIMAL(18,2) NOT NULL,
    currency_code VARCHAR(50) NOT NULL,
    
    CONSTRAINT fk_costs_campaign FOREIGN KEY (campaign_id) REFERENCES campaigns(campaign_id),
    CONSTRAINT fk_costs_channel FOREIGN KEY (channel_id) REFERENCES campaign_channels(channel_id)
);
