"""
Script: ingest_files.py
Tác dụng: Upload các file JSON, XML, Excel từ data/raw/ lên MinIO (Bronze Layer).
Mô phỏng đường ống đẩy thẳng dữ liệu External/API vào Data Lake.
"""
import os
import boto3
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

# Load env variables if they exist
load_dotenv(os.path.join(os.path.dirname(__file__), "../../infra/.env"))

# MinIO Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin") # Thay bằng Access Key thực tế
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin2026") # Thay bằng Secret Key thực tế
BUCKET_NAME = "tc-mart-datalake"

# Setup S3 Client
s3 = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1' # Default cho boto3 khi connect S3 API
)

def upload_folder(local_folder, minio_prefix):
    """Đẩy toàn bộ file trong thư mục lên MinIO"""
    if not os.path.exists(local_folder):
        print(f"⚠️ Thư mục {local_folder} không tồn tại!")
        return

    files = [f for f in os.listdir(local_folder) if os.path.isfile(os.path.join(local_folder, f))]
    if not files:
        print(f"⚠️ Thư mục {local_folder} rỗng!")
        return

    print(f"🚀 Bắt đầu upload {len(files)} files vào {BUCKET_NAME}/{minio_prefix}")
    
    count = 0
    for filename in files:
        local_path = os.path.join(local_folder, filename)
        minio_path = f"{minio_prefix}/{filename}"
        
        try:
            s3.upload_file(local_path, BUCKET_NAME, minio_path)
            count += 1
            if count % 100 == 0:
                print(f"  - Đã upload {count}/{len(files)} files...")
        except Exception as e:
            print(f"❌ Lỗi khi upload {filename}: {e}")
            
    print(f"✅ Đã hoàn thành upload {count} files vào {minio_prefix}!")

if __name__ == "__main__":
    # Đảm bảo bucket tồn tại
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except:
        print(f"Bucket {BUCKET_NAME} chưa tồn tại. Đang tạo...")
        s3.create_bucket(Bucket=BUCKET_NAME)
        print("Tạo bucket thành công!")

    # Đường dẫn thư mục Data
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/raw"))
    
    # 1. Ingest Marketing (JSON)
    upload_folder(os.path.join(base_dir, "marketing_ads"), "bronze/marketing_ads")
    
    # 2. Ingest Franchise (Excel)
    upload_folder(os.path.join(base_dir, "franchise_reports"), "bronze/franchise_reports")
    
    # 3. Ingest E-invoices (XML)
    upload_folder(os.path.join(base_dir, "e_invoices"), "bronze/e_invoices")
    
    print("🎉 TẤT CẢ FILE EXTERNAL ĐÃ ĐƯỢC TẢI LÊN MINIO (BRONZE LAYER)!")
