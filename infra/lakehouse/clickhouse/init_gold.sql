-- ==============================================================================
-- CLICKHOUSE GOLD ZONE — Star Schema DDL
-- Engine: ReplacingMergeTree (hỗ trợ upsert khi re-load)
-- DATABASE: gold
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS gold;

-- ==============================================================================
-- DIMENSIONS
-- ==============================================================================

-- Dim_Date (pre-populated bằng Python script riêng, có Lịch Âm)
CREATE TABLE IF NOT EXISTS gold.Dim_Date (
    date_sk             Int32,     -- YYYYMMDD
    full_date           Date,
    year                UInt16,
    quarter             UInt8,
    month               UInt8,
    week_of_year        UInt8,
    day_of_week         UInt8,     -- 1=Mon ... 7=Sun
    day_name            String,
    is_weekend          UInt8,
    is_month_start      UInt8,
    is_month_end        UInt8,
    -- Lịch Âm Việt Nam
    lunar_day           UInt8,
    lunar_month         UInt8,
    lunar_year          UInt16,
    is_lunar_new_year   UInt8,     -- Tết Nguyên Đán
    is_mid_autumn       UInt8,     -- Tết Trung Thu
    is_vietnam_holiday  UInt8      -- Tất cả ngày lễ VN
) ENGINE = ReplacingMergeTree()
ORDER BY date_sk;

-- Dim_Store (SCD Type 2)
CREATE TABLE IF NOT EXISTS gold.Dim_Store (
    store_sk              Int64,
    store_id              String,
    store_name            String,
    store_format          String,   -- HYPERMARKET | SUPERMARKET | MINIMART
    region_id             String,   -- NORTH | CENTRAL | SOUTH
    city                  String,
    floor_area_sqm        Float64,
    is_active             UInt8,
    effective_start_date  Date,
    effective_end_date    Nullable(Date),
    is_current            UInt8,
    dw_updated_at         DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(dw_updated_at)
ORDER BY (store_sk);

-- Dim_Product (SCD Type 2)
CREATE TABLE IF NOT EXISTS gold.Dim_Product (
    product_sk            Int64,
    product_id            String,
    product_name          String,
    department            String,
    category_name         String,
    base_uom              String,
    is_weighted           UInt8,
    vat_rate              Float64,
    current_retail_price  Float64,
    effective_start_date  Date,
    effective_end_date    Nullable(Date),
    is_current            UInt8,
    dw_updated_at         DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(dw_updated_at)
ORDER BY (product_sk);

-- Dim_Cashier
CREATE TABLE IF NOT EXISTS gold.Dim_Cashier (
    cashier_sk    Int64,
    cashier_id    String,
    cashier_name  String,
    status        String     -- ACTIVE | RESIGNED
) ENGINE = ReplacingMergeTree()
ORDER BY cashier_sk;

-- Dim_Customer
CREATE TABLE IF NOT EXISTS gold.Dim_Customer (
    customer_sk            Int64,
    customer_id            String,
    loyalty_tier           String,    -- STANDARD | SILVER | GOLD | PLATINUM
    registered_store_id    String
) ENGINE = ReplacingMergeTree()
ORDER BY customer_sk;

-- Dim_PaymentMethod
CREATE TABLE IF NOT EXISTS gold.Dim_PaymentMethod (
    payment_method_sk    Int64,
    payment_method_code  String,  -- CASH | VIETQR | MOMO | ZALOPAY | CREDIT_CARD
    payment_method_name  String,
    payment_group        String   -- TIỀN MẶT | VÍ ĐIỆN TỬ | CHUYỂN KHOẢN | THẺ
) ENGINE = ReplacingMergeTree()
ORDER BY payment_method_sk;

-- Dim_ExchangeRate (kéo từ API mỗi ngày)
CREATE TABLE IF NOT EXISTS gold.Dim_ExchangeRate (
    rate_sk              Int64,
    rate_date            Date,
    currency_code        String,   -- USD | CNY | EUR | JPY...
    buy_rate_vnd         Float64,
    sell_rate_vnd        Float64,
    reference_rate_vnd   Float64,  -- Tỷ giá trung tâm NHNN
    data_source          String    -- open.er-api.com | NHNN | fallback
) ENGINE = ReplacingMergeTree()
ORDER BY (rate_date, currency_code);

-- ==============================================================================
-- FACTS
-- ==============================================================================

-- Fact_StoreSales (grain: dòng sản phẩm / line-item)
CREATE TABLE IF NOT EXISTS gold.Fact_StoreSales (
    invoice_item_sk      Int64,
    invoice_id           String,    -- Degenerate Dimension
    date_sk              Int32,
    store_sk             Int64,
    product_sk           Int64,
    customer_sk          Nullable(Int64),
    payment_method_sk    Int64,
    shift_id             String,    -- Degenerate Dimension
    -- Measures
    quantity             Float64,
    unit_price_vnd       Float64,
    discount_amount_vnd  Float64,
    net_sales_vnd        Float64,   -- Âm nếu is_return = 1
    is_return            UInt8,     -- 1 = dòng đổi/trả (Negative Fact)
    -- Metadata
    dq_run_date          Date,
    loaded_at            DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(loaded_at)
PARTITION BY toYYYYMM(toDate(date_sk::String, 'YYYYMMDD'))
ORDER BY (date_sk, store_sk, invoice_id, invoice_item_sk);

-- Fact_CashierShiftReconciliation (grain: ca làm việc)
CREATE TABLE IF NOT EXISTS gold.Fact_CashierShiftReconciliation (
    shift_sk                    Int64,
    shift_id                    String,    -- Degenerate Dimension
    store_sk                    Int64,
    date_sk                     Int32,
    cashier_sk                  Int64,
    terminal_id                 String,
    -- Tiền mặt
    opening_cash_float          Float64,
    system_total_cash_sales     Float64,
    actual_closing_cash         Float64,
    cash_variance               Float64,   -- actual - (opening + system_cash)
    anomaly_flag                String,    -- NORMAL | ANOMALY_DEFICIT | ANOMALY_SURPLUS
    -- Phương thức thanh toán khác
    system_total_qr_sales       Float64,
    system_total_ewallet_sales  Float64,
    -- Ngoại tệ — So sánh tỷ giá thu ngân vs tỷ giá tham chiếu
    total_fx_sales_cashier_rate Float64,   -- Theo tỷ giá thu ngân nhập
    total_fx_sales_reference    Float64,   -- Theo tỷ giá NHNN (từ Dim_ExchangeRate)
    fx_rate_variance_vnd        Float64,   -- Chênh lệch VND do lệch tỷ giá
    -- Metadata
    dq_run_date                 Date,
    loaded_at                   DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(loaded_at)
PARTITION BY toYYYYMM(toDate(date_sk::String, 'YYYYMMDD'))
ORDER BY (date_sk, store_sk, shift_id);



-- ==============================================================================
-- VIEWS tiện ích
-- ==============================================================================

-- View: Shift anomaly với thông tin chi tiết
CREATE OR REPLACE VIEW gold.v_shift_anomalies AS
SELECT
    f.shift_id,
    s.store_name,
    s.store_format,
    s.region_id,
    d.full_date,
    c.cashier_name,
    f.cash_variance,
    f.anomaly_flag,
    f.fx_rate_variance_vnd,
    f.system_total_qr_sales,
    f.system_total_ewallet_sales
FROM gold.Fact_CashierShiftReconciliation f
JOIN gold.Dim_Store   s ON f.store_sk   = s.store_sk   AND s.is_current = 1
JOIN gold.Dim_Date    d ON f.date_sk    = d.date_sk
JOIN gold.Dim_Cashier c ON f.cashier_sk = c.cashier_sk
WHERE f.anomaly_flag != 'NORMAL';

-- View: Doanh thu theo ngày + cửa hàng (phục vụ Superset)
CREATE OR REPLACE VIEW gold.v_daily_sales_by_store AS
SELECT
    d.full_date,
    d.is_vietnam_holiday,
    d.lunar_day,
    s.store_name,
    s.store_format,
    s.region_id,
    s.floor_area_sqm,
    SUM(f.net_sales_vnd) AS total_net_sales,
    SUM(f.net_sales_vnd) / s.floor_area_sqm AS sales_per_sqm,
    COUNT(DISTINCT f.invoice_id) AS num_invoices,
    SUM(f.quantity) AS total_units_sold
FROM gold.Fact_StoreSales f
JOIN gold.Dim_Date    d ON f.date_sk  = d.date_sk
JOIN gold.Dim_Store   s ON f.store_sk = s.store_sk AND s.is_current = 1
WHERE f.is_return = 0
GROUP BY d.full_date, d.is_vietnam_holiday, d.lunar_day,
         s.store_name, s.store_format, s.region_id, s.floor_area_sqm;
