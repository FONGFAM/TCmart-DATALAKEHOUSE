"""
Script: ingest_oracle.py
Tác dụng: Đọc các table từ Oracle source (khi được bật) và đẩy lên MinIO dưới dạng file Parquet (Bronze Layer).
Lưu ý: Chỉ chạy script này khi container oracle-source đang bật.
"""
import os
import boto3
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), "../../infra/.env"))

# Config MinIO
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin2026")
BUCKET_NAME = "tc-mart-datalake"

# Config Oracle
ORACLE_URL = "oracle+oracledb://{user}:{password}@localhost:1521/?service_name=XEPDB1".format(
    user=os.getenv("ORACLE_APP_USER", "tcmart"),
    password=os.getenv("ORACLE_APP_USER_PASSWORD", "tcmart2026"),
)

s3_client = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1'
)

# Danh sách các schema/tables bên trong Oracle
# Trong Oracle, user 'tcmart' thường sở hữu luôn các table này, 
# hoặc chúng được chia thành các schema riêng. Ở đây ta giả lập cấu trúc chuẩn.
ORACLE_TABLES = {
    "warehouse_db": ["warehouses", "warehouse_locations", "inventory_transactions", "inventory", "stock_transfers", "stock_transfer_items"],
    "procurement_db": ["suppliers", "purchase_orders", "purchase_order_items", "goods_receipts", "goods_receipt_items"],
    "production_db": ["factories", "production_orders", "finished_products", "production_order_items", "raw_materials", "material_consumptions"]
}

def ingest_oracle_to_minio():
    print(f"🚀 Bắt đầu quá trình Ingest từ Oracle XE lên MinIO...")
    try:
        engine = create_engine(ORACLE_URL)
        # Test connection
        with engine.connect() as conn:
            pass
    except Exception as e:
        print("❌ Không thể kết nối tới Oracle. Vui lòng đảm bảo container tcmart-oracle đang chạy.")
        print("👉 Lệnh bật Oracle: docker compose -f infra/sources/docker-compose.yml --profile oracle up -d")
        return
    
    total_tables = sum([len(t) for t in ORACLE_TABLES.values()])
    count = 0
    
    for schema, tables in ORACLE_TABLES.items():
        for table in tables:
            count += 1
            print(f"  [{count}/{total_tables}] Đang ingest {schema}.{table}...")
            
            # Giả định các bảng được tạo trực tiếp dưới user tcmart, hoặc schema tương ứng
            # Có thể cần chỉnh sửa tuỳ thuộc vào cách init-script của Oracle được cấu hình.
            query = f"SELECT * FROM {table}"
            try:
                df = pd.read_sql(query, engine)
            except Exception as e:
                print(f"    ❌ Lỗi khi đọc {table} từ Oracle: {e}")
                continue
            
            if df.empty:
                print(f"    ⚠️ Bảng {table} rỗng, bỏ qua.")
                continue
            
            local_parquet = f"/tmp/oracle_{schema}_{table}.parquet"
            # Ép kiểu datetime
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

    print("🎉 HOÀN THÀNH INGEST ORACLE!")

if __name__ == "__main__":
    ingest_oracle_to_minio()
