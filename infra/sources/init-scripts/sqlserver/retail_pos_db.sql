-- ==============================================================================
-- DATABASE: retail_pos_db (SQL Server)
-- DESCRIPTION: Hệ thống bán lẻ tại quầy (POS)
-- ==============================================================================

USE master;
GO

-- Tạo database nếu chưa tồn tại
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'retail_pos_db')
BEGIN
    CREATE DATABASE retail_pos_db;
END
GO

USE retail_pos_db;
GO

-- ------------------------------------------------------------------------------
-- 1. Bảng stores (Cửa hàng)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[stores]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[stores](
        [store_id] [int] IDENTITY(1,1) NOT NULL,
        [store_code] [varchar](50) NOT NULL UNIQUE,
        [store_name] [nvarchar](100) NULL,
        [region] [nvarchar](50) NOT NULL,
        [address] [nvarchar](255) NULL,
        [city] [nvarchar](100) NULL,
        [warehouse_id] [int] NULL,
        [opened_date] [datetime] NOT NULL,
        [status] [varchar](50) NOT NULL,
        CONSTRAINT [PK_stores] PRIMARY KEY CLUSTERED ([store_id] ASC)
    );
END
GO

-- ------------------------------------------------------------------------------
-- 2. Bảng pos_terminals (Máy POS)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[pos_terminals]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[pos_terminals](
        [terminal_id] [int] IDENTITY(1,1) NOT NULL,
        [store_id] [int] NOT NULL,
        [terminal_code] [varchar](50) NOT NULL UNIQUE,
        [status] [varchar](50) NOT NULL,
        CONSTRAINT [PK_pos_terminals] PRIMARY KEY CLUSTERED ([terminal_id] ASC),
        CONSTRAINT [FK_terminals_store] FOREIGN KEY ([store_id]) REFERENCES [dbo].[stores] ([store_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 3. Bảng sales_orders (Hóa đơn bán hàng POS)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_orders]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[sales_orders](
        [sales_order_id] [int] IDENTITY(1,1) NOT NULL,
        [order_number] [varchar](50) NOT NULL UNIQUE,
        [store_id] [int] NOT NULL,
        [terminal_id] [int] NOT NULL,
        [customer_id] [int] NULL,
        [employee_id] [int] NOT NULL,
        [order_date] [datetime] NOT NULL DEFAULT GETDATE(),
        [channel] [varchar](50) NOT NULL,
        [subtotal] [decimal](18, 2) NOT NULL,
        [discount_amount] [decimal](18, 2) NOT NULL DEFAULT 0,
        [tax_amount] [decimal](18, 2) NOT NULL,
        [total_amount] [decimal](18, 2) NOT NULL,
        [status] [varchar](50) NOT NULL,
        CONSTRAINT [PK_sales_orders] PRIMARY KEY CLUSTERED ([sales_order_id] ASC),
        CONSTRAINT [FK_sales_orders_store] FOREIGN KEY ([store_id]) REFERENCES [dbo].[stores] ([store_id]),
        CONSTRAINT [FK_sales_orders_terminal] FOREIGN KEY ([terminal_id]) REFERENCES [dbo].[pos_terminals] ([terminal_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 4. Bảng sales_order_items (Chi tiết hóa đơn POS)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sales_order_items]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[sales_order_items](
        [sales_order_item_id] [int] IDENTITY(1,1) NOT NULL,
        [sales_order_id] [int] NOT NULL,
        [product_id] [int] NOT NULL,
        [quantity] [int] NOT NULL,
        [unit_price] [decimal](18, 2) NOT NULL,
        [discount_amount] [decimal](18, 2) NOT NULL DEFAULT 0,
        [tax_amount] [decimal](18, 2) NOT NULL,
        [line_total] [decimal](18, 2) NOT NULL,
        CONSTRAINT [PK_sales_order_items] PRIMARY KEY CLUSTERED ([sales_order_item_id] ASC),
        CONSTRAINT [FK_sales_items_order] FOREIGN KEY ([sales_order_id]) REFERENCES [dbo].[sales_orders] ([sales_order_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 5. Bảng payments (Giao dịch thanh toán)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[payments]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[payments](
        [payment_id] [int] IDENTITY(1,1) NOT NULL,
        [sales_order_id] [int] NOT NULL,
        [payment_method] [varchar](50) NOT NULL,
        [amount] [decimal](18, 2) NOT NULL,
        [currency_code] [varchar](50) NOT NULL,
        [payment_time] [datetime] NOT NULL DEFAULT GETDATE(),
        [status] [varchar](50) NOT NULL,
        CONSTRAINT [PK_payments] PRIMARY KEY CLUSTERED ([payment_id] ASC),
        CONSTRAINT [FK_payments_order] FOREIGN KEY ([sales_order_id]) REFERENCES [dbo].[sales_orders] ([sales_order_id])
    );
END
GO

-- ------------------------------------------------------------------------------
-- 6. Bảng pos_inventory (Tồn kho quầy)
-- ------------------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[pos_inventory]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[pos_inventory](
        [pos_inventory_id] [int] IDENTITY(1,1) NOT NULL,
        [store_id] [int] NOT NULL,
        [product_id] [int] NOT NULL,
        [quantity] [int] NOT NULL,
        [last_updated_at] [datetime] NOT NULL DEFAULT GETDATE(),
        CONSTRAINT [PK_pos_inventory] PRIMARY KEY CLUSTERED ([pos_inventory_id] ASC),
        CONSTRAINT [FK_inventory_store] FOREIGN KEY ([store_id]) REFERENCES [dbo].[stores] ([store_id])
    );
END
GO
