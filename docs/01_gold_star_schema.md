# TỪ ĐIỂN DỮ LIỆU TẦNG GOLD (STAR SCHEMA)
## HỆ THỐNG PHÂN TÍCH BÁN LẺ ĐẶC THÙ VIỆT NAM (RETAIL POS ANALYTICS)

> Tài liệu này định nghĩa cấu trúc dữ liệu ở tầng Gold (ClickHouse) được thiết kế theo phương pháp Top-Down (Kimball Lifecycle) để giải quyết 2 bài toán lớn nhất trong vận hành chuỗi siêu thị tại Việt Nam: Đối soát thanh toán đa phương thức và Dự báo nhu cầu theo Lịch Âm.
>
> **Nguồn dữ liệu:** 2 nguồn kết hợp — (1) SQL Server POS nội bộ và (2) API tỷ giá ngoại tệ bên ngoài.

---

## 1. Mục Tiêu Nghiệp Vụ (Business Requirements)
1. **Đối soát thanh toán đa phương thức & chênh lệch tiền két**: Tự động tính toán độ chênh lệch thu ngân, bắt lỗi mạng VietQR/MoMo, **phát hiện lệch tỷ giá thu ngân so với tỷ giá chính thức từ API**, và kiểm soát rủi ro thất thoát cuối ca (với cờ báo hiệu biến động > 50.000đ).
2. **Dự báo nhu cầu cục bộ (In-Store Demand Forecasting) có tích hợp Lịch Âm**: Dự báo số lượng tiêu thụ hàng tươi sống theo chu kỳ Rằm, Mùng 1, Lễ Tết truyền thống.

---

## 2. Các Bảng Chiều (Dimensions)

### 2.1. `Dim_Store` (Chiều Cửa Hàng)
- `store_sk` (Int64): Surrogate Key (Khóa nhân tạo).
- `store_id` (String): Mã cửa hàng gốc từ hệ thống POS.
- `store_name` (String): Tên cửa hàng.
- `store_format` (String): Định dạng (HYPERMARKET, SUPERMARKET, MINIMART).
- `region` (String): Khu vực (NORTH, CENTRAL, SOUTH).
- `effective_start_date` (Date): SCD Type 2 - Ngày bắt đầu hiệu lực.
- `effective_end_date` (Date): SCD Type 2 - Ngày kết thúc hiệu lực.
- `is_current` (UInt8): Cờ đánh dấu bản ghi hiện tại.

### 2.2. `Dim_Product` (Chiều Sản Phẩm)
- `product_sk` (Int64): Surrogate Key.
- `product_id` (String): Mã SKU gốc.
- `barcode` (String): Mã vạch chuẩn.
- `product_name` (String): Tên sản phẩm.
- `department` (String): Ngành hàng (FRESH_FOOD, FMCG...).
- `category` (String): Nhóm hàng.
- `base_uom` (String): Đơn vị tính (KG, CAI...).
- `current_retail_price` (Float64): Giá bán lẻ hiện tại (VND).

### 2.3. `Dim_Cashier` (Chiều Thu Ngân)
Phục vụ truy vết trách nhiệm nếu ca làm việc xảy ra thất thoát tiền mặt.
- `cashier_sk` (Int64): Surrogate Key.
- `cashier_id` (String): Mã định danh nhân viên thu ngân gốc.
- `cashier_name` (String): Tên nhân viên.
- `status` (String): Trạng thái nhân sự (ACTIVE, RESIGNED).

### 2.4. `Dim_PaymentMethod` (Chiều Phương Thức Thanh Toán)
- `payment_method_sk` (Int64): Surrogate Key.
- `payment_method_code` (String): Mã phương thức (CASH, VIETQR, MOMO, ZALOPAY, CREDIT_CARD).
- `payment_method_name` (String): Tên phương thức thanh toán.
- `payment_group` (String): Phân nhóm (TIỀN MẶT, VÍ ĐIỆN TỬ, CHUYỂN KHOẢN, THẺ).

### 2.5. `Dim_Date` (Chiều Thời Gian - Tích hợp Lịch Âm)
Lịch chuẩn mở rộng riêng cho bài toán Machine Learning dự báo bán lẻ Việt Nam.
- `date_sk` (Int32): Khóa ngày (VD: 20260914).
- `full_date` (Date): Ngày dương lịch.
- `day_of_week` (UInt8): Thứ trong tuần.
- `is_weekend` (UInt8): Cờ cuối tuần.
- `lunar_day` (UInt8): Ngày âm lịch.
- `lunar_month` (UInt8): Tháng âm lịch.
- `lunar_year` (UInt16): Năm âm lịch.
- `is_vietnam_holiday` (UInt8): Cờ Lễ Tết Việt Nam (Tết Nguyên Đán, Trung Thu, Giỗ Tổ...).

### 2.6. `Dim_ExchangeRate` (Chiều Tỷ Giá Ngoại Tệ — Nguồn API)
**Nguồn:** API tỷ giá bên ngoài (Ngân hàng Nhà nước VN hoặc ExchangeRate-API). Kéo hàng ngày vào 8h sáng bằng Airflow DAG riêng.

> **Mục đích cốt lõi:** Cung cấp tỷ giá **tham chiếu chính thức** để so sánh với tỷ giá thu ngân đã nhập thực tế trong `sales_payment_tenders`. Nếu lệch > ngưỡng cho phép → phát hiện gian lận hoặc nhập sai.

- `rate_sk` (Int64): Surrogate Key.
- `rate_date` (Date): Ngày áp dụng tỷ giá.
- `currency_code` (String): Mã ngoại tệ (USD, CNY, EUR, JPY...).
- `buy_rate_vnd` (Float64): Tỷ giá mua vào (VND / 1 đơn vị ngoại tệ).
- `sell_rate_vnd` (Float64): Tỷ giá bán ra (VND / 1 đơn vị ngoại tệ).
- `reference_rate_vnd` (Float64): Tỷ giá trung tâm tham chiếu (NHNN VN công bố).
- `data_source` (String): Tên API nguồn (NHNN / ExchangeRate-API / Open Exchange Rates).

---

## 3. Các Bảng Sự Kiện (Facts)

### 3.1. `Fact_CashierShiftReconciliation` (Fact Đối Soát Ca Thu Ngân)
Grain: Từng ca làm việc của từng thu ngân tại một máy POS.
- `shift_sk` (Int64): Surrogate Key.
- `shift_id` (String): Mã ca làm việc gốc (Degenerate Dimension).
- `store_sk` (Int64): FK tới Dim_Store.
- `date_sk` (Int32): FK tới Dim_Date (ngày chốt ca).
- `cashier_sk` (Int64): FK tới Dim_Cashier.
- `terminal_id` (String): Mã máy POS.
- `opening_cash_float` (Float64): Tiền lẻ bàn giao đầu ca (VND).
- `system_total_cash_sales` (Float64): Tổng doanh số thanh toán bằng Tiền Mặt trên phần mềm (VND).
- `actual_closing_cash` (Float64): Tiền mặt thực tế đếm được cuối ca (VND).
- `cash_variance` (Float64): Chênh lệch tiền mặt = `actual_closing_cash` - (`opening_cash_float` + `system_total_cash_sales`).
- `system_total_qr_sales` (Float64): Tổng doanh số VietQR ghi nhận.
- `system_total_ewallet_sales` (Float64): Tổng doanh số qua ví điện tử.
- `anomaly_flag` (String): Nhãn cảnh báo chênh lệch (NORMAL, ANOMALY_DEFICIT, ANOMALY_SURPLUS).
- **`total_fx_sales_original`** (Float64): Tổng doanh thu thanh toán bằng ngoại tệ (theo đồng tiền gốc quy đổi về VND theo tỷ giá thu ngân nhập).
- **`total_fx_sales_reference`** (Float64): Tổng doanh thu ngoại tệ quy đổi lại theo tỷ giá chính thức từ `Dim_ExchangeRate` (cùng ngày).
- **`fx_rate_variance_vnd`** (Float64): Chênh lệch VND do lệch tỷ giá = `total_fx_sales_reference` - `total_fx_sales_original`. Dương = thu ngân áp tỷ giá thấp hơn chính thức (thiệt cho cửa hàng); Âm = áp cao hơn.

### 3.2. `Fact_StoreSales` (Fact Bán Hàng)
Grain: Chi tiết từng dòng sản phẩm trên từng hóa đơn.
- `invoice_item_sk` (Int64): Surrogate Key của dòng hóa đơn.
- `invoice_id` (String): Mã hóa đơn gốc (Degenerate Dimension).
- `date_sk` (Int32): FK tới Dim_Date.
- `store_sk` (Int64): FK tới Dim_Store.
- `product_sk` (Int64): FK tới Dim_Product.
- `payment_method_sk` (Int64): FK tới Dim_PaymentMethod (áp dụng cao nhất trên bill).
- `quantity` (Float64): Số lượng bán.
- `unit_price_vnd` (Float64): Đơn giá bán (VND).
- `discount_amount_vnd` (Float64): Tiền giảm giá.
- `net_sales_vnd` (Float64): Doanh thu thuần (Quantity * Unit Price - Discount).
- `is_return` (UInt8): Cờ đánh dấu dòng này là dòng trả hàng (Negative Fact).
