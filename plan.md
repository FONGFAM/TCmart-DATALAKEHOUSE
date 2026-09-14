# Kế Hoạch Triển Khai: TCmart Data Lakehouse (Top-Down Approach)

Dự án này tập trung giải quyết 4 bài toán kinh doanh cốt lõi của siêu thị TC Mart bằng cách sử dụng **một nguồn dữ liệu duy nhất nhưng cực kỳ chi tiết**: Hệ thống POS bán lẻ trên SQL Server (14 bảng).

Chúng ta áp dụng phương pháp **Kimball Lifecycle (Top-Down)**: Đi từ yêu cầu nghiệp vụ $\rightarrow$ Thiết kế Star Schema $\rightarrow$ Thiết kế ELT $\rightarrow$ Xây dựng nguồn.

## Các Business Requirements (Mục tiêu nghiệp vụ)
1. **Hiệu suất mặt sàn:** Doanh thu trên mỗi mét vuông sàn (`Sales per sqm`).
2. **Khai phá giỏ hàng (Market Basket Analysis):** Những cặp sản phẩm thường được mua cùng nhau.
3. **Thất thoát tiền két:** Tỷ lệ chênh lệch tiền thu thực tế so với hệ thống.
4. **Dự báo nhu cầu cục bộ (In-Store Demand Forecasting):** Dự báo số lượng tiêu thụ.

---

## Lộ Trình Thực Thi (Roadmap)

### Phase 1: Xác định Yêu Cầu Nghiệp Vụ & Thiết Kế Star Schema (Gold Layer)
- [ ] Phân tích và định nghĩa các dimensions: `Dim_Store`, `Dim_Product`, `Dim_Date`, `Dim_Customer`.
- [ ] Phân tích và định nghĩa các facts: `Fact_StoreSales`, `Fact_CashierShiftReconciliation`.
- [ ] Tạo tài liệu thiết kế Star Schema (Data Dictionary cho tầng Gold).

### Phase 2: Đối Chiếu & Thiết Kế Nguồn (Source System - SQL Server)
- [ ] Thiết kế DDL SQL Server (`retail_pos_db`) tạo 14 bảng quan hệ đáp ứng đủ schema cho tầng Gold.
- [ ] Xây dựng Data Generator bằng Python (Faker).
- [ ] Cấy 4 kịch bản lỗi (Trùng lặp, tỷ giá ngoại hối, trả hàng âm, mã vạch lạ).
- [ ] Khởi chạy profile `sources` để test generator (limit 2,000 - 5,000 records).

### Phase 3: Thiết Kế Pipeline (Ingestion & Transformation)
- [ ] Xây dựng Raw Zone (MinIO).
- [ ] Cấu hình Airflow / JDBC để extract dữ liệu từ SQL Server lên MinIO.
- [ ] Xây dựng PySpark jobs để flatten dữ liệu, tính toán quy đổi ngoại tệ.
- [ ] Viết Data Quality rules (Great Expectations). Đưa dữ liệu vi phạm vào Quarantine.
- [ ] Nạp dữ liệu sạch vào Silver Zone (Iceberg / ClickHouse).

### Phase 4: Xây Dựng Tầng Cung Cấp Data (Gold Zone)
- [ ] Tạo các bảng `Dim` và `Fact` (ReplacingMergeTree) trên ClickHouse.
- [ ] Load dữ liệu từ Silver sang Gold.

### Phase 5: Phân Tích & Báo Cáo (BI & ML)
- [ ] Setup Apache Superset.
- [ ] Xây dựng 4 Dashboard trả lời 4 Business Requirements.
- [ ] Triển khai model Prophet forecast.