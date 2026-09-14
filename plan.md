# Kế Hoạch Triển Khai: TCmart Data Lakehouse

Phương pháp: **Kimball Lifecycle (Top-Down)** — Thiết kế mô hình phân tích trước, rồi mới đi xuống nguồn dữ liệu.

---

## 🎯 Chiến lược 2 giai đoạn lớn

> **Giai đoạn A — Single Source (Đang thực hiện):**
> Tập trung hoàn chỉnh 100% pipeline end-to-end từ **một nguồn duy nhất (SQL Server POS)**. Mục tiêu là có một pipeline "xương sống" chuẩn chỉnh, kiểm thử được, có DQ và BI trước.
>
> **Giai đoạn B — Multi Source (Sau khi Giai đoạn A hoàn chỉnh):**
> Giả lập và tích hợp thêm các nguồn dữ liệu mới để làm giàu hệ thống, mở rộng bài toán phân tích sang nhiều chiều hơn (xem phần cuối).

---

## Các Business Requirements — Giai đoạn A

Dự án này tập trung giải quyết 2 "nỗi đau" vận hành lớn nhất của hệ thống siêu thị Việt Nam bằng cách sử dụng **2 nguồn dữ liệu kết hợp**: (1) Hệ thống POS bán lẻ trên SQL Server và (2) API tỷ giá ngoại tệ.

1. **Đối soát thanh toán đa phương thức & Thất thoát tiền két:** Tự động hóa tính toán chênh lệch tiền mặt, thống kê tỷ trọng thanh toán phi tiền mặt (VietQR, MoMo), cô lập lỗi tỷ giá, **so sánh tỷ giá thu ngân nhập vs tỷ giá chính thức từ API để phát hiện gian lận hoặc sai sót**.
2. **Dự báo nhu cầu cục bộ (In-Store Demand Forecasting):** Tích hợp chu kỳ Lịch Âm (Rằm, Mùng 1, Lễ Tết) để dự báo sức mua hàng tươi sống bằng Prophet.

---

## 🗺 Lộ Trình Thực Thi — Giai đoạn A

### ✅ Phase 1: Star Schema & Business Requirements (Gold Layer)
- [x] Phân tích và định nghĩa các Dimensions: `Dim_Store`, `Dim_Product`, `Dim_Date` (có Lịch Âm), `Dim_Cashier`, `Dim_PaymentMethod`.
- [x] Phân tích và định nghĩa các Facts: `Fact_CashierShiftReconciliation`, `Fact_StoreSales`.
- [x] Tài liệu thiết kế Star Schema: `docs/01_gold_star_schema.md`.

### ✅ Phase 2: Thiết Kế Nguồn SQL Server & Data Generator
- [x] Viết DDL T-SQL (`retail_pos_db`) cho 14 bảng quan hệ → `infra/sources/init-scripts/sqlserver/retail_pos_db.sql`
- [x] Viết script Python (Faker) sinh Mock data → `src/generator/generators/gen_retail_pos.py`
- [x] Cố ý cấy 4 loại lỗi: lệch tiền thu ngân, lỗi tỷ giá ≤0, mã vạch lạ, đổi/trả hàng.
- [ ] **[CHỜ REVIEW]** Khởi động và test với `docker compose --profile sources up -d`.

### ✅ Phase 2b: Tích Hợp API Tỷ Giá Ngoại Tệ (Nguồn Dữ Liệu Thứ 2)
- [x] Lựa chọn API: **ExchangeRate-API** (miễn phí, fallback tỷ giá tĩnh khi API lỗi).
- [x] Viết Airflow DAG riêng (`dag_00_exchange_rate.py`) kéo tỷ giá mỗi ngày lúc 8h sáng.
- [x] Lưu raw JSON vào MinIO `raw-zone/exchange_rates/`, nạp vào `Dim_ExchangeRate`.
- [x] PySpark Silver: so sánh `exchange_rate` thực tế vs `reference_rate_vnd` → tính `fx_rate_variance_vnd`.

### ✅ Phase 3: Pipeline (Ingestion & Transformation)
- [x] Raw Zone (MinIO): `dag_02_ingestion.py` Airflow DAG kéo JDBC Batch mỗi giờ, incremental theo timestamp.
- [x] PySpark Silver (`src/processing/silver_transform.py`): Xử lý đa tiền tệ, tính `cash_variance`, gắn cờ `is_return`, so sánh tỷ giá.
- [x] DQ Gate (inline trong Silver job): Chuyển vi phạm tỷ giá vào Quarantine Zone.
- [x] `dag_03_silver_transform.py`: Trigger PySpark sau khi ingestion xong. → Quarantine.

### ✅ Phase 4: Tầng Gold (ClickHouse)
- [x] `init_gold.sql`: DDL 6 Dims + 2 Facts + 2 Views (ReplacingMergeTree).
- [x] `gold_load.py`: PySpark job tạo SK bằng xxhash64, map Dim, ghi Fact.
- [x] `populate_dim_date.py`: Seed Dim_Date 2024-2027 với Lịch Âm VN.
- [x] `dag_04_gold_load.py`: Airflow DAG chạy 2h sáng, kiểm tra Dim_Date trước khi load.

### Phase 5: BI & Machine Learning
- [ ] Apache Superset: Dashboard giám sát vận hành thu ngân.
- [ ] Prophet: Mô hình dự báo nhu cầu tích hợp Lịch Âm.

---

## 🔮 Giai đoạn B — Mở rộng Multi Source (Kế hoạch tương lai)

Sau khi Giai đoạn A hoàn chỉnh, chúng ta sẽ giả lập thêm các nguồn để làm giàu hệ thống và mở ra nhiều bài toán phân tích đa dạng hơn. Các nguồn tiềm năng:

| Nguồn Dữ Liệu (Giả lập) | Loại DB | Bài Toán Phân Tích Mở Rộng |
|---|---|---|
| **E-commerce** (website bán online) | PostgreSQL | Phân tích hành vi khách hàng omni-channel (Online vs Offline) |
| **Procurement / Nhà cung cấp** | PostgreSQL | Phân tích hiệu suất nhà cung cấp, tối ưu đơn hàng nhập |
| **Kho hàng trung tâm** | PostgreSQL | Phân tích vòng quay hàng tồn kho, tối ưu phân phối kho → siêu thị |
| **Nhân sự (HR)** | PostgreSQL | Phân tích năng suất nhân viên, lên ca tối ưu theo lượng khách |
| **Marketing / Khuyến mãi** | JSON/File | Đo lường ROI chiến dịch khuyến mãi, phân tích hiệu quả voucher |

> **Lưu ý:** Khi bổ sung nguồn mới, chúng ta sẽ luôn thiết kế Galaxy Schema mở rộng (bổ sung Fact/Dim mới) theo đúng nguyên tắc Kimball mà không làm thay đổi pipeline hiện có.