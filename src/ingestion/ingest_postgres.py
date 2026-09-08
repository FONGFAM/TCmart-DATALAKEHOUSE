"""
Script: ingest_postgres.py
Tác dụng: Đọc các table từ PostgreSQL source và đẩy lên MinIO dưới dạng file Parquet (Bronze Layer).
"""
import os
import boto3
import pandas as pd
from sqlalchemy import create_engine
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../../infra/.env"))

# Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin2026")
BUCKET_NAME = "tc-mart-datalake"
PG_URL = "postgresql+psycopg2://{user}:{password}@localhost:5433/{db}".format(
    user=os.getenv("POSTGRES_USER", "tcmart"),
    password=os.getenv("POSTGRES_PASSWORD", "tcmart2026"),
    db="postgres" # Dùng chung 1 DB nhưng khác schema
)

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

PG_TABLES = {
    "ecommerce_db": ["customers", "online_orders", "online_order_items", "payments", "delivery_addresses"],
    "employee_db": ["departments", "positions", "employees", "employee_shifts", "employee_assignments"],
    "product_db": ["products", "brands", "categories", "product_prices"],
    "marketing_db": ["campaigns", "campaign_channels", "impressions", "clicks", "campaign_costs"],
    "promotion_db": ["promotions", "promotion_stores", "promotion_discounts", "promotion_products"],
    "franchise_db": ["franchise_monthly_reports", "franchisees", "franchise_orders", "franchise_orders_items"],
    "exchange_rate_db": ["currencies", "exchange_rates"],
    "invoice_db": ["invoices", "invoice_taxes", "invoice_items"],
    "warehouse_db": ["warehouses", "warehouse_locations", "inventory_transactions", "inventory", "stock_transfers", "stock_transfer_items"],
    "procurement_db": ["suppliers", "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items"],
    "production_db": ["factories", "production_orders", "finished_products", "production_order_items", "raw_materials", "material_consumptions"]
}

def ingest_postgres_to_minio():
    print(f"🚀 Bắt đầu quá trình Ingest từ PostgreSQL lên MinIO...")
    engine = create_engine(PG_URL)
    
    total_tables = sum([len(t) for t in PG_TABLES.values()])
    count = 0
    
    for schema, tables in PG_TABLES.items():
        for table in tables:
            count += 1
            print(f"  [{count}/{total_tables}] Đang ingest {schema}.{table}...")
            
            query = f"SELECT * FROM {schema}.{table}"
            try:
                # Dùng trực tiếp engine để mỗi query tự quản lý transaction
                df = pd.read_sql(query, engine)
            except Exception as e:
                print(f"    ❌ Lỗi khi đọc {schema}.{table}: {e}")
                continue
            
            if df.empty:
                print(f"    ⚠️ Bảng {schema}.{table} rỗng, bỏ qua.")
                continue
            
            local_parquet = f"/tmp/{schema}_{table}.parquet"
            # Cố gắng chuyển datetime có múi giờ về chuẩn
            for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
            df.to_parquet(local_parquet, index=False)
            
            minio_path = f"bronze/{schema}/{table}/{schema}_{table}_full.parquet"
            
            try:
                s3_client.upload_file(local_parquet, BUCKET_NAME, minio_path)
                print(f"    ✅ Đã đẩy {len(df)} rows lên {minio_path}")
            except Exception as e:
                print(f"    ❌ Lỗi khi upload lên MinIO: {e}")
            finally:
                if os.path.exists(local_parquet):
                    os.remove(local_parquet)

    print("🎉 HOÀN THÀNH INGEST POSTGRESQL!")

if __name__ == "__main__":
    ingest_postgres_to_minio()
