# 🏪 TCmart Data Lakehouse

> **Nghiên cứu, Xây dựng Hệ thống Data Lakehouse cho Chuỗi Cửa hàng Bán lẻ TC MART**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-24.x-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-green.svg)](https://python.org)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-24.3-orange.svg)](https://clickhouse.com/)

---

## 📖 Giới thiệu

**TC MART** là chuỗi cửa hàng bán lẻ đa kênh (cửa hàng vật lý, website, mobile app). Dữ liệu hiện đang phân tán trên nhiều hệ thống:

| Nguồn dữ liệu | Hệ thống | Loại dữ liệu |
|---|---|---|
| **POS** | Microsoft SQL Server | Đơn hàng, giao dịch |
| **CRM** | PostgreSQL | Khách hàng, thẻ thành viên |
| **ERP / Procurement** | Oracle XE | Nhập kho, nhà cung cấp |
| **HR** | PostgreSQL | Nhân sự, ca làm việc |
| **File import** | MinIO (S3) | Excel, CSV, JSON, XML |
| **Khuyến mãi** | PostgreSQL | Chương trình KM, mã giảm giá |

Dự án này xây dựng một **Data Lakehouse** thống nhất với kiến trúc **Bronze → Silver → Gold** trên **ClickHouse**, hỗ trợ cả **batch ETL** (Airflow) và **real-time streaming** (Kafka + Spark), kèm theo **BI Dashboard** (Superset) và **dự báo bán hàng** (Prophet).

---

## 🏗️ Kiến trúc hệ thống

```
Source Systems
    ├─ SQL Server (POS)         ─┐
    ├─ PostgreSQL (CRM, HR...)  ─┤─→ Apache NiFi ──→ Kafka ──→ Spark Streaming ──→ ClickHouse (Bronze)
    ├─ Oracle XE (ERP)          ─┘
    └─ Files (MinIO)            ──→ Apache NiFi ──→ Kafka ──→ Spark Streaming ──→ ClickHouse (Bronze)

ClickHouse
    ├─ Bronze  (Raw / Event Streams)
    ├─ Silver  (Cleaned / Staging)
    └─ Gold    (Star Schema / OLAP Cube)
               └─→ Apache Superset (Dashboard)
               └─→ Prophet (Sales Forecast)

Orchestration & Monitoring
    ├─ Apache Airflow (Batch scheduler)
    ├─ FastAPI Data-Steward (Validation & Audit)
    ├─ Great Expectations (Data Quality)
    └─ Prometheus + Grafana (Monitoring)
```

---

## 📋 Lộ trình 15 bước

```
01. CHỐT SOURCE DATABASE          07. SILVER / STAGING
02. CHỐT DATA MODEL SOURCE        08. DATA QUALITY
03. THIẾT KẾ DATA GENERATOR       09. DATA STEWARD / XỬ LÝ LỖI
04. DỰNG CÁC SOURCE DB            10. GOLD / LAKEHOUSE
05. XÂY SOURCE INGESTION          11. STAR + SNOWFLAKE + OLAP CUBE
06. BRONZE / RAW                  12. BI / DASHBOARD
                                  13. FORECAST
                                  14. ORCHESTRATION + MONITORING
                                  15. DEMO END-TO-END
```

---

## 🗂️ Cấu trúc dự án

```
TCmart-DATALAKEHOUSE/
├─ docs/
│   ├─ 01_source_data_dictionary.md   # Từ điển dữ liệu – 12 CSDL, 42 bảng
│   ├─ 02_technology_overview.md      # Tổng quan công nghệ
│   ├─ 03_system_design.md            # Kiến trúc hệ thống
│   └─ 04_development_plan.md         # Kế hoạch phát triển
├─ infra/
│   ├─ docker-compose.yml             # Orchestration toàn bộ service
│   ├─ .env.example                   # Biến môi trường mẫu
│   └─ init-scripts/                  # SQL scripts khởi tạo DB
├─ src/
│   ├─ generator/                     # Script tạo dữ liệu mẫu
│   ├─ data_steward/                  # FastAPI Data-Steward service
│   ├─ spark_jobs/                    # PySpark streaming & batch jobs
│   └─ airflow_dags/                  # Airflow DAGs
├─ notebooks/
│   └─ forecast.ipynb                 # Dự báo bán hàng Prophet
├─ plan.md                            # Lộ trình 15 bước
├─ Makefile                           # Shortcuts: make up, make down, make test
├─ .gitignore
└─ README.md
```

---

## ⚙️ Yêu cầu môi trường

> 💡 Được tối ưu hoá cho **macOS Intel (i7, 16 GB RAM)**. Cũng hoạt động trên **Windows** với Docker Desktop.

| Công cụ | Phiên bản | Ghi chú |
|---|---|---|
| Docker Desktop | Latest | Bật *File Sharing* cho thư mục dự án |
| Python | 3.11 | Cài qua Homebrew: `brew install python@3.11` |
| Java OpenJDK | 11 hoặc 17 | Cần cho Spark, NiFi, Airflow |
| Node.js | 20 LTS | Cần cho Superset UI |
| Git | Latest | Quản lý phiên bản |
| Make | Latest | Đã có sẵn trên macOS |

---

## 🚀 Hướng dẫn cài đặt & chạy

### Trên macOS (môi trường chính)

```bash
# 1. Clone dự án về máy
git clone https://github.com/<username>/TCmart-DATALAKEHOUSE.git
cd TCmart-DATALAKEHOUSE

# 2. Cài các công cụ cần thiết (nếu chưa có)
brew install python@3.11 openjdk@11 node

# 3. Tạo file .env từ template
cp infra/.env.example infra/.env
# Chỉnh sửa .env nếu cần (password, port...)

# 4. Khởi động toàn bộ service
make up
# hoặc: docker compose -f infra/docker-compose.yml up -d
```

### Kiểm tra các service

| Service | URL | Tài khoản mặc định |
|---|---|---|
| **Superset** | http://localhost:8088 | admin / admin |
| **Airflow** | http://localhost:8080 | admin / admin |
| **MinIO** | http://localhost:9000 | minioadmin / minioadmin |
| **FastAPI Data-Steward** | http://localhost:8000/docs | - |
| **Grafana** | http://localhost:3000 | admin / admin |

### Chạy pipeline mẫu

```bash
# Kích hoạt môi trường Python
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Tạo dữ liệu mẫu và tải lên MinIO
python src/generator/generate_data.py

# Kiểm tra Bronze layer trong ClickHouse
clickhouse-client -q "SELECT count(*) FROM bronze_db.sales_events;"
```

---

## 🧪 Kiểm thử

```bash
# Unit tests
make test
# hoặc: pytest src/tests/ -v

# Integration tests (cần Docker đang chạy)
make test-integration
```

---

## 📚 Tài liệu

| Tài liệu | Mô tả |
|---|---|
| [01_source_data_dictionary.md](docs/01_source_data_dictionary.md) | Từ điển dữ liệu – 12 CSDL, 42 bảng, đầy đủ kiểu dữ liệu và ràng buộc |
| [02_technology_overview.md](docs/02_technology_overview.md) | Tổng quan toàn bộ công nghệ và phiên bản sử dụng |
| [03_system_design.md](docs/03_system_design.md) | Kiến trúc hệ thống và diagram luồng dữ liệu |
| [plan.md](plan.md) | Lộ trình 15 bước phát triển |

---

## 🔧 Lệnh Make hữu ích

```bash
make up          # Khởi động toàn bộ service
make down        # Tắt toàn bộ service
make restart     # Restart service
make test        # Chạy unit tests
make logs        # Xem logs tất cả container
make ps          # Xem trạng thái các container
make clean       # Dọn dẹp volumes và containers
```

---

## 🤝 Đóng góp

1. Fork repo này.
2. Tạo nhánh mới: `git checkout -b feature/<tên-tính-năng>`.
3. Commit thay đổi: `git commit -m "feat: mô tả thay đổi"`.
4. Push lên nhánh: `git push origin feature/<tên-tính-năng>`.
5. Mở Pull Request.

---

## 📄 Giấy phép

Dự án này được phân phối dưới giấy phép **MIT**. Xem [LICENSE](LICENSE) để biết thêm chi tiết.

---

*Được xây dựng như một đồ án nghiên cứu Data Lakehouse cho hệ thống bán lẻ TC MART.*
