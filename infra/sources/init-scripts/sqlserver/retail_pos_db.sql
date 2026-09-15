-- ==============================================================================
-- DATABASE: retail_pos_db (SQL Server 2022 — T-SQL)
-- DESCRIPTION: Hệ thống bán lẻ POS tại quầy cho chuỗi siêu thị TC Mart
-- THIẾT KẾ: 14 bảng theo mô hình OLTP chuẩn hóa, mapping sang Star Schema Gold
-- ==============================================================================

USE master;
GO

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'retail_pos_db')
BEGIN
    CREATE DATABASE retail_pos_db
    COLLATE Vietnamese_CI_AS;
END
GO

USE retail_pos_db;
GO

-- ==============================================================================
-- PHÂN HỆ 1: CẤU TRÚC ĐIỂM BÁN & CA KÍP THU NGÂN
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. stores — Danh mục siêu thị vật lý
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[stores]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[stores] (
        [store_id]         VARCHAR(20)     NOT NULL,
        [store_name]       NVARCHAR(150)   NOT NULL,
        [store_format]     VARCHAR(30)     NOT NULL,   -- HYPERMARKET | SUPERMARKET | MINIMART
        [region_id]        VARCHAR(20)     NOT NULL,   -- NORTH | CENTRAL | SOUTH
        [address]          NVARCHAR(200)   NULL,
        [city]             NVARCHAR(100)   NULL,
        [district]         NVARCHAR(100)   NULL,
        [floor_area_sqm]   DECIMAL(10,2)   NOT NULL,   -- Diện tích sàn KD (m²) — dùng cho Sales/sqm
        [is_active]        BIT             NOT NULL DEFAULT 1,
        [opened_date]      DATE            NOT NULL,
        CONSTRAINT [PK_stores] PRIMARY KEY ([store_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 2. pos_terminals — Máy tính tiền vật lý tại quầy
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[pos_terminals]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[pos_terminals] (
        [terminal_id]      VARCHAR(20)     NOT NULL,
        [store_id]         VARCHAR(20)     NOT NULL,
        [mac_address]      VARCHAR(50)     NULL,
        [ip_address]       VARCHAR(50)     NULL,
        [is_self_checkout] BIT             NOT NULL DEFAULT 0,
        [is_active]        BIT             NOT NULL DEFAULT 1,
        CONSTRAINT [PK_pos_terminals] PRIMARY KEY ([terminal_id]),
        CONSTRAINT [FK_terminals_store] FOREIGN KEY ([store_id]) REFERENCES [dbo].[stores]([store_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 3. cashier_shifts — Phiên làm việc & Quản lý két tiền mặt
--    ⚠️  Bảng gốc của Fact_CashierShiftReconciliation
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[cashier_shifts]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[cashier_shifts] (
        [shift_id]               VARCHAR(60)     NOT NULL,
        [store_id]               VARCHAR(20)     NOT NULL,
        [terminal_id]            VARCHAR(20)     NOT NULL,
        [cashier_id]             VARCHAR(20)     NOT NULL,  -- Mã nhân viên (source of Dim_Cashier)
        [cashier_name]           NVARCHAR(100)   NULL,
        [opened_at]              DATETIME        NOT NULL,
        [closed_at]              DATETIME        NULL,
        [opening_cash_float]     DECIMAL(15,2)   NOT NULL DEFAULT 0,
        [system_expected_cash]   DECIMAL(15,2)   NULL,      -- Hệ thống tính toán khi đóng ca
        [actual_closing_cash]    DECIMAL(15,2)   NULL,      -- Tiền thực tế đếm được
        [cash_variance]          DECIMAL(15,2)   NULL,      -- = actual - expected (âm = thiếu, dương = thừa)
        [shift_status]           VARCHAR(20)     NOT NULL DEFAULT 'OPEN', -- OPEN | CLOSED | RECONCILED
        CONSTRAINT [PK_cashier_shifts] PRIMARY KEY ([shift_id]),
        CONSTRAINT [FK_shifts_store]    FOREIGN KEY ([store_id])    REFERENCES [dbo].[stores]([store_id]),
        CONSTRAINT [FK_shifts_terminal] FOREIGN KEY ([terminal_id]) REFERENCES [dbo].[pos_terminals]([terminal_id])
    );
END
GO

-- ==============================================================================
-- PHÂN HỆ 2: DANH MỤC SẢN PHẨM & CHÍNH SÁCH GIÁ VÙNG
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 4. products — Danh mục mặt hàng Master
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[products]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[products] (
        [product_id]      VARCHAR(30)     NOT NULL,
        [product_name]    NVARCHAR(255)   NOT NULL,
        [department]      VARCHAR(50)     NOT NULL,   -- FRESH_FOOD | FMCG | NON_FOOD | BEVERAGE
        [category_name]   NVARCHAR(100)   NULL,
        [base_uom]        VARCHAR(20)     NOT NULL,   -- KG | CAI | HOP | GOI | CHAI
        [is_weighted]     BIT             NOT NULL DEFAULT 0,  -- Hàng cân ký (rau, thịt tươi)
        [vat_rate]        DECIMAL(5,2)    NOT NULL DEFAULT 8.00, -- % VAT: 0 | 5 | 8 | 10
        [is_active]       BIT             NOT NULL DEFAULT 1,
        CONSTRAINT [PK_products] PRIMARY KEY ([product_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 5. product_barcodes — Bảng quản lý mã vạch quét máy
--    Một SKU có thể có nhiều barcode (chiếc lẻ, lốc 4, thùng 24)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[product_barcodes]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[product_barcodes] (
        [barcode]              VARCHAR(30)    NOT NULL,
        [product_id]           VARCHAR(30)    NOT NULL,
        [packaging_unit]       VARCHAR(20)    NOT NULL,  -- ITEM | PACK | BOX
        [conversion_factor]    DECIMAL(10,3)  NOT NULL DEFAULT 1.000, -- 1 BOX = 24 ITEM
        [is_primary]           BIT            NOT NULL DEFAULT 0,
        CONSTRAINT [PK_product_barcodes] PRIMARY KEY ([barcode]),
        CONSTRAINT [FK_barcodes_product] FOREIGN KEY ([product_id]) REFERENCES [dbo].[products]([product_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 6. store_price_books — Chính sách giá bán lẻ theo từng siêu thị / khu vực
--    Hỗ trợ SCD Type 2 qua effective_from / effective_to
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[store_price_books]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[store_price_books] (
        [price_book_id]  BIGINT          NOT NULL IDENTITY(1,1),
        [store_id]       VARCHAR(20)     NOT NULL,
        [product_id]     VARCHAR(30)     NOT NULL,
        [retail_price]   DECIMAL(15,2)   NOT NULL,
        [effective_from] DATETIME        NOT NULL,
        [effective_to]   DATETIME        NULL,  -- NULL = đang hiệu lực
        CONSTRAINT [PK_price_books] PRIMARY KEY ([price_book_id]),
        CONSTRAINT [FK_price_store]   FOREIGN KEY ([store_id])   REFERENCES [dbo].[stores]([store_id]),
        CONSTRAINT [FK_price_product] FOREIGN KEY ([product_id]) REFERENCES [dbo].[products]([product_id])
    );
END
GO

-- ==============================================================================
-- PHÂN HỆ 3: KHÁCH HÀNG THÀNH VIÊN & TÍCH ĐIỂM
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 7. customers — Hồ sơ khách hàng thành viên
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[customers]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[customers] (
        [customer_id]           BIGINT          NOT NULL IDENTITY(1,1),
        [phone_number]          VARCHAR(15)     NOT NULL,  -- Khóa định danh khi quẹt thẻ tại quầy
        [full_name]             NVARCHAR(150)   NULL,
        [loyalty_tier]          VARCHAR(20)     NOT NULL DEFAULT 'STANDARD', -- STANDARD | SILVER | GOLD | PLATINUM
        [current_loyalty_points] INT            NOT NULL DEFAULT 0,
        [registered_store_id]   VARCHAR(20)     NULL,
        [registered_at]         DATETIME        NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_customers] PRIMARY KEY ([customer_id]),
        CONSTRAINT [UQ_customer_phone] UNIQUE ([phone_number]),
        CONSTRAINT [FK_customers_store] FOREIGN KEY ([registered_store_id]) REFERENCES [dbo].[stores]([store_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 8. customer_loyalty_transactions — Lịch sử biến động điểm tích lũy
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[customer_loyalty_transactions]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[customer_loyalty_transactions] (
        [loyalty_tx_id]          BIGINT       NOT NULL IDENTITY(1,1),
        [customer_id]            BIGINT       NOT NULL,
        [invoice_id]             VARCHAR(40)  NULL,  -- Hóa đơn phát sinh giao dịch
        [points_earned]          INT          NOT NULL DEFAULT 0,
        [points_redeemed]        INT          NOT NULL DEFAULT 0,
        [transaction_timestamp]  DATETIME     NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_loyalty_tx] PRIMARY KEY ([loyalty_tx_id]),
        CONSTRAINT [FK_loyalty_customer] FOREIGN KEY ([customer_id]) REFERENCES [dbo].[customers]([customer_id])
    );
END
GO

-- ==============================================================================
-- PHÂN HỆ 4: GIAO DỊCH BÁN LẺ & THANH TOÁN ĐA PHƯƠNG THỨC
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 9. sales_invoices — Hóa đơn bán lẻ (Header)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_invoices]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[sales_invoices] (
        [invoice_id]             VARCHAR(40)     NOT NULL,  -- UUID
        [store_id]               VARCHAR(20)     NOT NULL,
        [terminal_id]            VARCHAR(20)     NOT NULL,
        [shift_id]               VARCHAR(60)     NOT NULL,
        [cashier_id]             VARCHAR(20)     NOT NULL,
        [customer_id]            BIGINT          NULL,      -- NULL nếu khách vãng lai
        [invoice_date]           DATETIME        NOT NULL,
        [total_gross_amount]     DECIMAL(15,2)   NOT NULL,  -- Tổng tiền hàng trước giảm
        [total_discount_amount]  DECIMAL(15,2)   NOT NULL DEFAULT 0,
        [total_tax_amount]       DECIMAL(15,2)   NOT NULL DEFAULT 0,
        [total_net_amount]       DECIMAL(15,2)   NOT NULL,  -- Tổng phải trả (VND)
        [status]                 VARCHAR(20)     NOT NULL DEFAULT 'COMPLETED', -- COMPLETED | VOIDED | RETURNED
        CONSTRAINT [PK_sales_invoices] PRIMARY KEY ([invoice_id]),
        CONSTRAINT [FK_inv_store]    FOREIGN KEY ([store_id])    REFERENCES [dbo].[stores]([store_id]),
        CONSTRAINT [FK_inv_terminal] FOREIGN KEY ([terminal_id]) REFERENCES [dbo].[pos_terminals]([terminal_id]),
        CONSTRAINT [FK_inv_shift]    FOREIGN KEY ([shift_id])    REFERENCES [dbo].[cashier_shifts]([shift_id]),
        CONSTRAINT [FK_inv_customer] FOREIGN KEY ([customer_id]) REFERENCES [dbo].[customers]([customer_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 10. sales_invoice_items — Chi tiết giỏ hàng (Line Item — Hạt nhân)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_invoice_items]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[sales_invoice_items] (
        [invoice_item_id]       BIGINT          NOT NULL IDENTITY(1,1),
        [invoice_id]            VARCHAR(40)     NOT NULL,
        [line_number]           INT             NOT NULL,
        [product_id]            VARCHAR(30)     NOT NULL,
        [scanned_barcode]       VARCHAR(30)     NULL,  -- Mã vạch thực tế máy quét bắt được
        [quantity]              DECIMAL(12,3)   NOT NULL,  -- Hỗ trợ hàng cân kg (0.450 kg)
        [unit_price]            DECIMAL(15,2)   NOT NULL,
        [line_discount_amount]  DECIMAL(15,2)   NOT NULL DEFAULT 0,
        [line_total_amount]     DECIMAL(15,2)   NOT NULL,
        CONSTRAINT [PK_invoice_items] PRIMARY KEY ([invoice_item_id]),
        CONSTRAINT [FK_items_invoice] FOREIGN KEY ([invoice_id])  REFERENCES [dbo].[sales_invoices]([invoice_id]),
        CONSTRAINT [FK_items_product] FOREIGN KEY ([product_id])  REFERENCES [dbo].[products]([product_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 11. sales_payment_tenders — Phương thức thanh toán & Ngoại tệ
--     ⚠️  Một hóa đơn có thể có NHIỀU tender (split payment)
--     ⚠️  Nguồn dữ liệu chính cho bài toán đối soát tỷ giá
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_payment_tenders]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[sales_payment_tenders] (
        [tender_id]               BIGINT          NOT NULL IDENTITY(1,1),
        [invoice_id]              VARCHAR(40)     NOT NULL,
        [payment_method]          VARCHAR(30)     NOT NULL,  -- CASH | CREDIT_CARD | VIETQR | MOMO | ZALOPAY | VOUCHER
        [currency_code]           VARCHAR(3)      NOT NULL DEFAULT 'VND', -- VND | USD | CNY
        [exchange_rate]           DECIMAL(12,4)   NOT NULL DEFAULT 1.0000, -- Tỷ giá thu ngân nhập
        [tender_amount_original]  DECIMAL(15,2)   NOT NULL,  -- Số tiền theo đồng tiền gốc
        [tender_amount_vnd]       DECIMAL(15,2)   NOT NULL,  -- = tender_amount_original * exchange_rate
        [change_amount_vnd]       DECIMAL(15,2)   NOT NULL DEFAULT 0, -- Tiền thừa thối lại
        CONSTRAINT [PK_tenders] PRIMARY KEY ([tender_id]),
        CONSTRAINT [FK_tenders_invoice] FOREIGN KEY ([invoice_id]) REFERENCES [dbo].[sales_invoices]([invoice_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 12. sales_item_discounts — Phân bổ chi tiết giảm giá trên từng dòng hàng
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_item_discounts]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[sales_item_discounts] (
        [discount_entry_id]    BIGINT          NOT NULL IDENTITY(1,1),
        [invoice_item_id]      BIGINT          NOT NULL,
        [discount_type]        VARCHAR(30)     NOT NULL,  -- PROMO_CAMPAIGN | COMBO | LOYALTY_POINT | COUPON_CODE
        [promo_reference_id]   VARCHAR(50)     NULL,
        [discount_value]       DECIMAL(15,2)   NOT NULL,
        CONSTRAINT [PK_item_discounts] PRIMARY KEY ([discount_entry_id]),
        CONSTRAINT [FK_discounts_item] FOREIGN KEY ([invoice_item_id]) REFERENCES [dbo].[sales_invoice_items]([invoice_item_id])
    );
END
GO

-- ==============================================================================
-- PHÂN HỆ 5: HẬU MÃI & TỒN KHO ĐIỂM BÁN
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 13. sales_returns — Biên bản đổi trả / Hủy hóa đơn tại quầy
--     ⚠️  Sẽ tạo Negative Facts trong Fact_StoreSales
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_returns]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[sales_returns] (
        [return_id]              VARCHAR(40)     NOT NULL,
        [original_invoice_id]   VARCHAR(40)     NOT NULL,
        [store_id]               VARCHAR(20)     NOT NULL,
        [return_timestamp]       DATETIME        NOT NULL DEFAULT GETDATE(),
        [product_id]             VARCHAR(30)     NOT NULL,
        [returned_quantity]      DECIMAL(12,3)   NOT NULL,
        [refund_amount_vnd]      DECIMAL(15,2)   NOT NULL,
        [return_reason]          VARCHAR(100)    NULL,  -- EXPIRED | DAMAGED | CUSTOMER_CHANGE_MIND | CASHIER_ERROR
        CONSTRAINT [PK_sales_returns] PRIMARY KEY ([return_id]),
        CONSTRAINT [FK_returns_invoice] FOREIGN KEY ([original_invoice_id]) REFERENCES [dbo].[sales_invoices]([invoice_id]),
        CONSTRAINT [FK_returns_store]   FOREIGN KEY ([store_id])            REFERENCES [dbo].[stores]([store_id]),
        CONSTRAINT [FK_returns_product] FOREIGN KEY ([product_id])          REFERENCES [dbo].[products]([product_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 14. store_inventory_snapshots — Chốt tồn kho tại siêu thị vật lý hàng ngày
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[store_inventory_snapshots]') AND type = N'U')
BEGIN
    CREATE TABLE [dbo].[store_inventory_snapshots] (
        [snapshot_id]        BIGINT          NOT NULL IDENTITY(1,1),
        [store_id]           VARCHAR(20)     NOT NULL,
        [product_id]         VARCHAR(30)     NOT NULL,
        [snapshot_date]      DATE            NOT NULL,
        [shelf_stock_qty]    DECIMAL(12,3)   NOT NULL DEFAULT 0,  -- Tồn trên quầy kệ
        [backroom_stock_qty] DECIMAL(12,3)   NOT NULL DEFAULT 0,  -- Tồn kho phụ sau siêu thị
        [damaged_loss_qty]   DECIMAL(12,3)   NOT NULL DEFAULT 0,  -- Hao hụt ghi nhận trong ngày
        CONSTRAINT [PK_inventory_snapshots] PRIMARY KEY ([snapshot_id]),
        CONSTRAINT [FK_inv_snap_store]   FOREIGN KEY ([store_id])   REFERENCES [dbo].[stores]([store_id]),
        CONSTRAINT [FK_inv_snap_product] FOREIGN KEY ([product_id]) REFERENCES [dbo].[products]([product_id])
    );
END
GO

PRINT 'retail_pos_db: 14 tables created successfully.';
GO
