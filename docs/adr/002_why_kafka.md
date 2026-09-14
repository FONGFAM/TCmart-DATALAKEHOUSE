# ADR 002: Bỏ Kafka — Dùng Airflow + PySpark JDBC

## Quyết định
Không sử dụng Kafka. Ingestion từ SQL Server lên MinIO sẽ do **Airflow DAG điều phối + PySpark đọc qua JDBC**.

## Lý do
- Bài toán là Batch ingestion định kỳ mỗi giờ, **không phải real-time streaming** → Kafka là over-engineering.
- Kafka + Zookeeper tốn thêm ~1GB RAM trên máy 16GB — không chấp nhận được.
- PySpark JDBC trực tiếp đơn giản hơn, dễ debug, dễ bảo trì hơn cho đồ án.
- Airflow đã đủ vai trò orchestration, không cần message broker bổ sung.

## Luồng thay thế
```
SQL Server (retail_pos_db)
    │
    ▼ Airflow DAG (JDBC Batch, mỗi giờ)
MinIO (Raw Zone — Parquet files)
    │
    ▼ PySpark Job (Silver Transformation)
ClickHouse (Bronze → Silver → Gold)
```
