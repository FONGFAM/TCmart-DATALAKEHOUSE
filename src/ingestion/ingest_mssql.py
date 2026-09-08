"""
Script: ingest_mssql.py
Tác dụng: Đọc các table từ MSSQL source và đẩy lên MinIO dưới dạng file Parquet (Bronze Layer).
"""
import os
import urllib.parse
import boto3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../../infra/.env"))

# Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin2026")
BUCKET_NAME = "tc-mart-datalake"

MSSQL_URL = "mssql+pymssql://sa:{password}@localhost:1433/retail_pos_db".format(
    password=urllib.parse.quote_plus(os.getenv("SA_PASSWORD", "TCMart@2026!Strong"))
)

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

# Danh sách các table cần ingest từ MSSQL
MSSQL_TABLES = ["stores", "sales_orders", "sales_order_items"]
SCHEMA_NAME = "retail_pos_db"

def ingest_mssql_to_minio():
    print(f"🚀 Bắt đầu quá trình Ingest từ MSSQL lên MinIO...")
    engine = create_engine(MSSQL_URL)
    
    count = 0
    with engine.connect() as conn:
        for table in MSSQL_TABLES:
            count += 1
            print(f"  [{count}/{len(MSSQL_TABLES)}] Đang ingest {SCHEMA_NAME}.{table}...")
            
            query = f"SELECT * FROM {table}"
            try:
                df = pd.read_sql(query, conn)
            except Exception as e:
                print(f"    ❌ Lỗi khi đọc {table}: {e}")
                continue
            
            if df.empty:
                print(f"    ⚠️ Bảng {table} rỗng, bỏ qua.")
                continue
            
            # Lưu tạm ra file parquet local
            local_parquet = f"/tmp/{SCHEMA_NAME}_{table}.parquet"
            # Ép kiểu datetime nếu cần để tương thích Parquet
            for col in df.select_dtypes(include=['datetime64', 'datetimetz']).columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                
            df.to_parquet(local_parquet, index=False)
            
            # Upload lên MinIO
            minio_path = f"bronze/{SCHEMA_NAME}/{table}/{SCHEMA_NAME}_{table}_full.parquet"
            
            try:
                s3_client.upload_file(local_parquet, BUCKET_NAME, minio_path)
                print(f"    ✅ Đã đẩy {len(df)} rows lên {minio_path}")
            except Exception as e:
                print(f"    ❌ Lỗi khi upload lên MinIO: {e}")
            finally:
                if os.path.exists(local_parquet):
                    os.remove(local_parquet)

    print("🎉 HOÀN THÀNH INGEST MSSQL!")

if __name__ == "__main__":
    ingest_mssql_to_minio()
