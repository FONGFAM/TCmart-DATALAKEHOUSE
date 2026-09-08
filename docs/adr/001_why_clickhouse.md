# ADR 001: Chọn ClickHouse làm Analytics Engine

## Quyết định
Sử dụng ClickHouse thay vì PostgreSQL, Redshift, hoặc Druid làm engine lưu trữ và query cho OLAP layer.

## Lý do
- Hiệu năng query cột (columnar) nhanh gấp 100–1000x so với PostgreSQL cho aggregation
- Hỗ trợ tốt trên Docker (nhẹ hơn Druid/Pinot)
- Native Kafka ingestion qua ClickHouse Kafka Engine
- Phù hợp On-premise, không phụ thuộc cloud
