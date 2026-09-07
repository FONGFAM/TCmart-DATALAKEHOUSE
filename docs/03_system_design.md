# Thiết kế hệ thống Data Lakehouse cho TCmart

## Kiến trúc tổng quan
```mermaid
flowchart TB
    subgraph Source[Source Systems]
        direction TB
        MSSQL[SQL Server] -->|JDBC| NiFi
        PostgreSQL[PostgreSQL] -->|JDBC| NiFi
        Oracle[Oracle XE] -->|JDBC| NiFi
        Files[Excel/CSV/JSON] -->|S3 API| MinIO
    end
    NiFi -->|Publish| Kafka
    Kafka -->|Consume| Spark
    Spark -->|Write| ClickHouse[ClickHouse (Bronze)]
    subgraph Bronze[Bronze Layer]
        ClickHouse
    end
    Spark -->|Transform| ClickHouseSilver[ClickHouse (Silver)]
    Airflow -->|Batch Load| ClickHouseSilver
    ClickHouseSilver -->|Materialize| ClickHouseGold[ClickHouse (Gold)]
    ClickHouseGold -->|Query| Superset[Apache Superset]
    DataSteward[FastAPI Data‑Steward] -->|Log| PostgreSQLAudit[PostgreSQL (Audit)]
    Superset -->|Dashboard| Users[End Users]
    Prometheus --> Grafana[Grafana]
```

## Thành phần chính
- **Docker Compose** – orkestration mọi service.
- **NiFi** – ingest data từ MinIO, chuyển sang Kafka.
- **Kafka** – message bus cho streaming.
- **Spark Structured Streaming** – xử lý real‑time, ghi vào ClickHouse.
- **Airflow** – schedule batch jobs, chạy ETL.
- **ClickHouse** – lưu trữ lakehouse (Bronze/Silver/Gold).
- **FastAPI Data‑Steward** – validation, error handling.
- **Superset** – BI dashboard.
- **Prometheus + Grafana** – monitoring & alerting.

---
*File này mô tả kiến trúc hệ thống và các thành phần liên quan.*
