# Công nghệ sử dụng cho dự án TCmart Data Lakehouse

## 1. Hạ tầng và môi trường
- **Docker Desktop** (latest) – quản lý toàn bộ service trong containers.
- **Docker Compose** – orchestration cho các service.
- **Python 3.11** (via Homebrew) – viết pipeline, generator, FastAPI.
- **Java OpenJDK 11** – chạy Apache Spark, Apache NiFi, Apache Airflow.
- **Node.js 20 LTS** – hỗ trợ UI Superset customisation.

## 2. Cơ sở dữ liệu & lưu trữ
| Thành phần | Công nghệ | Phiên bản đề xuất |
|------------|-----------|-------------------|
| **Source DB** | Microsoft SQL Server Express, PostgreSQL 15, Oracle XE | Docker images `mcr.microsoft.com/mssql/server:2022-latest`, `postgres:15-alpine`, `gvenzl/oracle-xe:21-slim` |
| **Lakehouse** | ClickHouse | `clickhouse/clickhouse-server:24.3` |
| **Object Storage** | MinIO (S3 compatible) | `minio/minio:RELEASE.2024-03-26T20-38-09Z` |
| **Metadata / Audit** | PostgreSQL | `postgres:15-alpine` |

## 3. Tiền xử lý & chuyển đổi dữ liệu
- **Apache NiFi** – kéo dữ liệu từ MinIO, chuyển vào Kafka.
- **Apache Kafka** (Confluent Platform) – luồng sự kiện thực thời.
- **Apache Spark Structured Streaming** – tiêu thụ Kafka, áp dụng schema, ghi vào ClickHouse (Bronze).
- **Airflow** – schedule batch jobs, chạy ETL từ source DB vào Bronze.
- **Great Expectations** – kiểm tra chất lượng dữ liệu trong Airflow tasks.

## 4. Data Steward & Quality
- **FastAPI** (Python) – service kiểm tra dữ liệu theo JSON‑Schema, lưu log lỗi vào PostgreSQL.
- **Great Expectations** – kiểm tra tự động.

## 5. Phân tích & BI
- **Apache Superset** – dashboard trực quan trên ClickHouse.
- **Metabase** (tùy chọn) – alternative UI.
- **Jupyter Notebook** + **Prophet** – dự báo bán hàng.

## 6. Orchestration & Monitoring
- **Apache Airflow** – workflow engine chính.
- **Prometheus + Grafana** – giám sát container, Kafka lag, Spark job health.
- **Alertmanager** – gửi cảnh báo Slack/Email.

## 7. Công cụ phát triển
- **VS Code** + extensions: Docker, Python, SQLTools, Remote‑Containers.
- **Git** – version control.
- **DBeaver** – quản trị DB GUI.
- **Makefile** – shortcut cho `make up`, `make down`, `make test`.

## 8. Khác
- **MCP (Model Context Protocol)** – không cần thiết cho phần này, nhưng có thể dùng để chuẩn hoá mô hình dữ liệu trong tương lai.
- **Extensions** – các plugin VS Code để hỗ trợ Docker‑Compose validation.

---
*File này tổng hợp toàn bộ stack công nghệ sẽ được dùng cho dự án.*
