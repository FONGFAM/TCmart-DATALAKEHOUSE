# TC Mart - Retail Data Lakehouse 🛒

Dự án Data Lakehouse thực tế giải quyết các bài toán vận hành cốt lõi của chuỗi siêu thị bán lẻ (tương tự WinMart, Bách Hóa Xanh).

> **Chiến lược:** Kimball Lifecycle (Top-Down Approach). Đi từ Yêu cầu nghiệp vụ $\rightarrow$ Mô hình phân tích (Star Schema) $\rightarrow$ Thiết kế ELT Pipeline $\rightarrow$ Hệ thống gốc (SQL Server).

## 🚀 Business Requirements (Mục tiêu bài toán)
1. **Đối soát thanh toán & Thất thoát tiền két**: Tự động tính toán chênh lệch thu ngân, đối soát tỷ trọng thanh toán phi tiền mặt (VietQR, MoMo), phát hiện lỗi tỷ giá ngoại tệ USD/CNY.
2. **Dự báo nhu cầu cục bộ theo Lịch Âm**: Tích hợp chu kỳ Rằm, Mùng 1, Lễ Tết vào mô hình Prophet để dự báo sức mua hàng hóa thiết yếu (Fresh Food).

---

## 🏗 Kiến trúc Hệ thống (Architecture)

Toàn bộ hệ thống chạy trên **Docker** với resource profile được tối ưu hóa cho máy 16GB RAM:

```text
[ POS System ]         [ Ingestion ]          [ Processing & Quality ]           [ Analytics & BI ]
 SQL Server ─────────→ Airflow / JDBC ──────→ PySpark & Great Expectations ────→ ClickHouse (Star Schema)
 (14 Tables)                                                                     │
                                                                                 │
                                                                                 ├─→ Apache Superset (BI)
                                                                                 └─→ Prophet (ML Forecast)
```

1. **Source (SQL Server)**: Giả lập 14 bảng dữ liệu vận hành siêu thị (Hóa đơn, Ca làm việc, Thanh toán đa phương thức...).
2. **Bronze / Raw (MinIO)**: Lưu trữ thô dữ liệu trích xuất (CDC/Batch).
3. **Silver / Transformation**: Dùng **PySpark** để flatten dữ liệu, quy đổi ngoại tệ về VND, tính toán chênh lệch. Dùng **Great Expectations** làm Data Quality Gate.
4. **Gold / Data Mart**: Bảng Fact và Dimension trên **ClickHouse**.
5. **Serving**: BI Dashboard trên **Superset** và Machine Learning với **Prophet**.

---

## 📁 Cấu trúc Thư mục Dự án

```text
TCmart-DATALAKEHOUSE/
├── docs/                             # Tài liệu thiết kế (Data Dictionary, Star Schema...)
├── src/
│   ├── generator/                    # Script Python sinh Mock data
│   ├── orchestration/                # Airflow DAGs
│   ├── processing/                   # PySpark jobs
│   └── quality/                      # Great Expectations rules
├── infra/                            # Infrastructure configuration
│   ├── sources/                      # Docker-compose cho SQL Server & MinIO
│   ├── lakehouse/                    # Docker-compose cho ClickHouse & Airflow
│   └── bi/                           # Docker-compose cho Superset
├── .agents/                          # Workspace rules (Agent configs)
├── plan.md                           # Kế hoạch & Lộ trình thực thi
└── Makefile                          # Lệnh tự động hóa
```

## ⚠️ Lưu ý phần cứng
- Host requirement: 16 GB RAM.
- **TUYỆT ĐỐI KHÔNG** khởi động toàn bộ stack cùng lúc. Sử dụng Docker Profiles (e.g., `docker compose --profile sources up -d`).
