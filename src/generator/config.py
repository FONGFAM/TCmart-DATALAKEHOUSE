"""
config.py — Cấu hình kết nối Database và tham số Generator
Đọc từ file .env ở thư mục infra/
"""
import os
from dotenv import load_dotenv

# Load .env từ infra/
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../infra/.env"))

# ─── Connection Strings ───────────────────────────────────────────────────────

# SQL Server — retail_pos_db (T-SQL)
MSSQL_URL = (
    "mssql+pyodbc://sa:{password}@localhost:1433/retail_pos_db"
    "?driver=ODBC+Driver+17+for+SQL+Server"
).format(password=os.getenv("SA_PASSWORD", "TCMart@2026!Strong"))

# PostgreSQL — 8 databases (dùng chung 1 server, tách schema/db)
PG_BASE_URL = "postgresql+psycopg2://{user}:{password}@localhost:5432/{db}".format(
    user=os.getenv("POSTGRES_USER", "tcmart"),
    password=os.getenv("POSTGRES_PASSWORD", "tcmart2026"),
    db="{db}",
)
PG_DATABASES = {
    "ecommerce_db":    PG_BASE_URL.format(db="ecommerce_db"),
    "employee_db":     PG_BASE_URL.format(db="employee_db"),
    "franchise_db":    PG_BASE_URL.format(db="franchise_db"),
    "product_db":      PG_BASE_URL.format(db="product_db"),
    "promotion_db":    PG_BASE_URL.format(db="promotion_db"),
    "marketing_db":    PG_BASE_URL.format(db="marketing_db"),
    "invoice_db":      PG_BASE_URL.format(db="invoice_db"),
    "exchange_rate_db": PG_BASE_URL.format(db="exchange_rate_db"),
}

# Oracle — procurement_db, warehouse_db, production_db (PL/SQL)
ORACLE_URL = "oracle+oracledb://{user}:{password}@localhost:1521/?service_name=XEPDB1".format(
    user=os.getenv("ORACLE_APP_USER", "tcmart"),
    password=os.getenv("ORACLE_APP_USER_PASSWORD", "tcmart2026"),
)

# ─── Generator Parameters ─────────────────────────────────────────────────────
# ⚠️  Giữ ≤ 10,000 records/table để tránh OOM theo quy tắc AGENTS.md
GEN_CONFIG = {
    # Master data (ít records, dùng nhiều lần làm FK)
    "num_categories":   20,
    "num_brands":       30,
    "num_products":     200,
    "num_stores":       10,
    "num_warehouses":   5,
    "num_factories":    3,
    "num_employees":    100,
    "num_customers":    500,
    "num_franchisees":  20,
    "num_suppliers":    50,
    "num_campaigns":    10,

    # Transactional data (nhiều records hơn)
    "num_sales_orders":         2000,
    "num_online_orders":        1500,
    "num_purchase_orders":      500,
    "num_production_orders":    200,
    "num_stock_transfers":      100,
    "num_promotions":           15,
    "num_franchise_orders":     300,

    # Dirty data ratio (5% tổng số records)
    "dirty_ratio":              0.05,
}

# ─── Locale ───────────────────────────────────────────────────────────────────
FAKER_LOCALE = "vi_VN"   # Vietnamese data (tên người, địa chỉ VN)
RANDOM_SEED  = 42        # Đảm bảo reproducible
