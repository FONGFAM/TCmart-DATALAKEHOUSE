# 🏪 TCmart Data Lakehouse

> **Nghiên cứu, Xây dựng Hệ thống Data Lakehouse cho Chuỗi Cửa hàng Bán lẻ TC MART**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-24.x-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10-green.svg)](https://python.org)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-24.3-orange.svg)](https://clickhouse.com/)
[![Airflow](https://img.shields.io/badge/Airflow-2.9-blue.svg)](https://airflow.apache.org/)

---

## 📖 Giới thiệu

**TC MART** là chuỗi cửa hàng bán lẻ đa kênh (cửa hàng vật lý, website, đại lý nhượng quyền). Dữ liệu hiện đang phân tán trên **12 hệ thống cơ sở dữ liệu** khác nhau, thuộc 3 hệ quản trị CSDL lớn:

| Hệ quản trị | Số lượng DB | Các hệ thống tiêu biểu |
|---|---|---|
| **PostgreSQL** | 8 | eCommerce, Nhân sự, Khuyến mãi, Marketing, Sản phẩm... |
| **Microsoft SQL Server** | 1 | Retail POS (Bán lẻ tại quầy) |
| **Oracle XE** | 3 | Procurement (Mua hàng), Warehouse (Kho), Production (Sản xuất) |

Dự án này xây dựng một **Data Lakehouse** thống nhất với kiến trúc **Bronze → Silver → Gold** trên **ClickHouse**, hỗ trợ cả **batch ETL** (Airflow) và **real-time streaming** (Kafka + Spark), kèm theo **BI Dashboard** (Superset) và **dự báo bán hàng** (Prophet).

Đặc biệt, dự án bao gồm một bộ **Data Generator** mạnh mẽ được viết bằng Python, có khả năng tự động khởi tạo và liên kết hàng chục nghìn bản ghi ngẫu nhiên (đơn hàng, khách hàng, giao dịch kho) xuyên suốt 12 DBs để phục vụ việc kiểm thử Data Quality và ETL pipeline.

---

## 🏗️ Kiến trúc hệ thống

```text
Source Systems (12 DBs)
    ├─ SQL Server (POS)         ─┐
    ├─ PostgreSQL (CRM, HR...)  ─┤─→ Apache NiFi ──→ Kafka ──→ Spark Streaming ──→ ClickHouse (Bronze)
    ├─ Oracle XE (ERP, Kho...)  ─┘
    └─ Files (MinIO)            ──→ Airflow (Batch) ──→ Spark / ClickHouse SQL ──→ ClickHouse (Bronze)

ClickHouse
    ├─ Bronze  (Raw / Event Streams / Batch Ingestion)
    ├─ Silver  (Cleaned / Staging / Data Quality with Great Expectations)
    └─ Gold    (Star Schema / OLAP Cube)
               └─→ Apache Superset (Dashboard)
               └─→ Prophet (Sales Forecast)

Orchestration & Monitoring
    ├─ Apache Airflow (Batch scheduler & Orchestration)
    ├─ FastAPI Data-Steward (Validation & Audit API)
    └─ Prometheus + Grafana (Monitoring)
```

---

## 📋 Lộ trình 15 bước (Đang thực hiện)

```text
✅ 01. CHỐT SOURCE DATABASE          07. SILVER / STAGING
✅ 02. CHỐT DATA MODEL SOURCE        08. DATA QUALITY
✅ 03. THIẾT KẾ DATA GENERATOR       09. DATA STEWARD / XỬ LÝ LỖI
✅ 04. DỰNG CÁC SOURCE DB            10. GOLD / LAKEHOUSE
✅ 05. XÂY SOURCE INGESTION          11. STAR + SNOWFLAKE + OLAP CUBE
✅ 06. BRONZE / RAW                  12. BI / DASHBOARD
                                     13. FORECAST
                                     14. ORCHESTRATION + MONITORING
                                     15. DEMO END-TO-END
```

---

## 🗂️ Cấu trúc dự án

```text
TCmart-DATALAKEHOUSE/
├─ docs/                              # Tài liệu dự án (Từ điển dữ liệu, Thiết kế kiến trúc)
├─ infra/                             # Scripts và cấu hình Docker cho toàn bộ hạ tầng
│   ├─ sources/                       # Docker compose cho 12 DBs nguồn (Postgres, SQL Server, Oracle)
│   ├─ lakehouse/                     # Docker compose cho ClickHouse, Airflow
│   ├─ streaming/                     # Docker compose cho Kafka, NiFi
│   └─ bi/                            # Docker compose cho Superset
├─ src/                               # Mã nguồn chính
│   ├─ generator/                     # Bộ Python scripts sinh dữ liệu giả lập cho 12 DBs
│   ├─ orchestration/                 # Airflow DAGs (Ingestion, Bronze, Silver, Gold)
│   ├─ processing/                    # Spark jobs (Java/Python) xử lý dữ liệu
│   └─ ingestion/                     # Python scripts (Boto3, Pandas) đẩy data lên MinIO (Bronze Layer)
├─ Makefile                           # Tập hợp các phím tắt terminal (make up-sources, make gen-all...)
└─ plan.md                            # Tracking tiến độ dự án chi tiết
```

---

## ⚙️ Yêu cầu hệ thống

> 💡 **Khuyến nghị**: Máy tính nên có tối thiểu **16GB RAM** (do dự án chạy cùng lúc nhiều Databases hạng nặng như Oracle, SQL Server, Spark). Quá trình khởi động được chia làm nhiều **Phases** trong Makefile để tránh quá tải RAM.

| Công cụ | Ghi chú |
|---|---|
| **Docker Desktop** | Bắt buộc (bật File Sharing) |
| **Python 3.10** | Dùng để chạy Data Generator và Airflow DAG testing |
| **Make** | Đã có sẵn trên macOS/Linux |
| **Java 17** | Cần để build các job Spark (Maven) |

---

## 🚀 Hướng dẫn cài đặt & Khởi động

Dự án cung cấp file `Makefile` giúp bạn khởi chạy hệ thống theo từng giai đoạn (Phased Startup) để tiết kiệm RAM.

### 1. Chuẩn bị môi trường

```bash
# Clone dự án
git clone https://github.com/FONGFAM/TCmart-DATALAKEHOUSE.git
cd TCmart-DATALAKEHOUSE

# Cài đặt Python Virtual Environment cho Generator
make setup
```

### 2. Khởi động Data Sources & Sinh dữ liệu (Phase 1)

```bash
# Khởi động PostgreSQL, SQL Server và MinIO (Tiêu tốn ~4GB RAM)
make up-sources

# (Tuỳ chọn) Khởi động Oracle XE - Khá nặng (~2GB RAM), chỉ bật khi cần test DB Kho/Sản xuất
make up-oracle

# Sinh dữ liệu tự động vào 12 CSDL (Chạy kịch bản Python)
make gen-all

### 3. Đẩy dữ liệu lên Data Lake - Lớp Bronze (Phase 2)

```bash
# Đẩy dữ liệu từ file (Excel, JSON, XML) lên MinIO
python src/ingestion/ingest_files.py

# Đẩy dữ liệu từ Database (PostgreSQL, MSSQL, Oracle) lên MinIO bằng Parquet
python src/ingestion/ingest_postgres.py
python src/ingestion/ingest_mssql.py
# python src/ingestion/ingest_oracle.py (Chỉ chạy khi bật Oracle)
```

### 4. Khởi động Data Lakehouse & Orchestration (Phase 3)

```bash
# Khởi động Airflow và ClickHouse
make up-lakehouse

# Truy cập:
# - Airflow UI: http://localhost:8080 (admin/admin)
# - ClickHouse: http://localhost:8123
```

---

## 🔧 Các lệnh Make hữu ích khác

| Lệnh | Mô tả |
|---|---|
| `make ram-check` | Kiểm tra dung lượng RAM khả dụng trên máy (macOS) |
| `make down-sources` | Tắt cụm Source Databases |
| `make down-oracle` | Tắt độc lập Oracle XE để giải phóng RAM |
| `make down-all` | Tắt TOÀN BỘ hệ thống Docker Containers |
| `make gen-dirty` | (Dành cho test Data Quality) Bơm dữ liệu lỗi (null, sai format) có chủ đích |
| `make test` | Chạy bộ Unit Tests |

---

## 📄 Giấy phép

Dự án này được phân phối dưới giấy phép **MIT**. Xem `LICENSE` để biết thêm chi tiết.
