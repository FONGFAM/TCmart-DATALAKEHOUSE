# ADR 002: Chọn Kafka làm Message Broker

## Quyết định
Dùng Kafka làm lớp trung gian giữa Source DB và ClickHouse Bronze thay vì kết nối JDBC trực tiếp.

## Lý do
- Tách biệt Source và Sink (loose coupling)
- Cho phép nhiều consumer xử lý cùng 1 event stream
- Replay event khi pipeline bị lỗi (retention 24h)
- Mô phỏng kiến trúc thực tế của hệ thống bán lẻ lớn
