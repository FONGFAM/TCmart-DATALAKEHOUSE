# TỪ ĐIỂN DỮ LIỆU TẦNG GOLD (STAR SCHEMA)
## HỆ THỐNG PHÂN TÍCH BÁN LẺ (RETAIL POS ANALYTICS)

> Tài liệu này định nghĩa cấu trúc dữ liệu ở tầng Gold (ClickHouse) được thiết kế theo phương pháp Top-Down (Kimball Lifecycle) để giải quyết 4 bài toán kinh doanh cốt lõi của TC Mart.

---

## 1. Mục Tiêu Nghiệp Vụ (Business Requirements)
1. **Hiệu suất mặt sàn (Sales per $m^2$)**: Tìm ra cửa hàng/định dạng cửa hàng mang lại doanh thu cao nhất trên mỗi mét vuông.
2. **Khai phá giỏ hàng (Market Basket Analysis)**: Phân tích các cặp sản phẩm thường mua cùng nhau (Support, Confidence).
3. **Thất thoát tiền két (Cash Variance)**: Theo dõi chênh lệch tiền mặt thực tế và hệ thống theo từng ca làm việc.
4. **Dự báo nhu cầu cục bộ (In-Store Demand Forecasting)**: Dự báo số lượng tiêu thụ từng sản phẩm tại từng cửa hàng.

---

## 2. Các Bảng Chiều (Dimensions)

### 2.1. `Dim_Store` (Chiều Cửa Hàng)
Chứa thông tin về hạ tầng vật lý, phục vụ bài toán phân tích hiệu suất mặt sàn.
- `store_sk` (Int64): Surrogate Key (Khóa nhân tạo).
- `store_id` (String): Mã cửa hàng gốc từ hệ thống POS.
- `store_name` (String): Tên cửa hàng.
- `store_format` (String): Định dạng (HYPERMARKET, SUPERMARKET, MINIMART).
- `region` (String): Khu vực (NORTH, CENTRAL, SOUTH).
- `floor_area_sqm` (Float64): Diện tích sàn (phục vụ tính Sales per $m^2$).
- `effective_start_date` (Date): SCD Type 2 - Ngày bắt đầu hiệu lực.
- `effective_end_date` (Date): SCD Type 2 - Ngày kết thúc hiệu lực.
- `is_current` (UInt8): Cờ đánh dấu bản ghi hiện tại.

### 2.2. `Dim_Product` (Chiều Sản Phẩm)
Chứa thông tin danh mục, phục vụ phân tích giỏ hàng và dự báo.
- `product_sk` (Int64): Surrogate Key.
- `product_id` (String): Mã SKU gốc.
- `barcode` (String): Mã vạch (một sản phẩm có thể có nhiều barcode).
- `product_name` (String): Tên sản phẩm.
- `department` (String): Ngành hàng (FRESH_FOOD, FMCG...).
- `category` (String): Nhóm hàng.
- `base_uom` (String): Đơn vị tính (KG, CAI...).
- `current_retail_price` (Float64): Giá bán lẻ hiện tại (VND).
- `effective_start_date` (Date): SCD Type 2.
- `effective_end_date` (Date): SCD Type 2.
- `is_current` (UInt8): Cờ đánh dấu bản ghi hiện tại.

### 2.3. `Dim_Customer` (Chiều Khách Hàng)
- `customer_sk` (Int64): Surrogate Key.
- `customer_id` (String): Mã khách hàng gốc.
- `loyalty_tier` (String): Hạng thẻ (STANDARD, SILVER, GOLD, PLATINUM).
- `registered_store_sk` (Int64): FK tới Dim_Store nơi mở thẻ.

### 2.4. `Dim_Date` (Chiều Thời Gian)
Lịch chuẩn 4-4-5 cho ngành bán lẻ.
- `date_sk` (Int32): Khóa ngày (VD: 20260914).
- `full_date` (Date): Ngày thực tế.
- `day_of_week` (UInt8): Thứ trong tuần.
- `is_weekend` (UInt8): Cờ cuối tuần.
- `retail_week` (UInt8): Tuần bán lẻ.
- `retail_month` (UInt8): Tháng bán lẻ.
- `retail_quarter` (UInt8): Quý bán lẻ.
- `retail_year` (UInt16): Năm bán lẻ.

---

## 3. Các Bảng Sự Kiện (Facts)

### 3.1. `Fact_StoreSales` (Doanh thu & Giỏ hàng)
Hạt nhân chi tiết đến từng dòng hóa đơn (Line-item grain).
- `invoice_item_sk` (Int64): Surrogate Key của dòng hóa đơn.
- `invoice_id` (String): Mã hóa đơn gốc (Degenerate Dimension - Dùng để gom giỏ hàng tính Market Basket).
- `date_sk` (Int32): FK tới Dim_Date.
- `store_sk` (Int64): FK tới Dim_Store.
- `product_sk` (Int64): FK tới Dim_Product.
- `customer_sk` (Int64): FK tới Dim_Customer.
- `shift_id` (String): Ca làm việc.
- `quantity` (Float64): Số lượng bán.
- `unit_price_vnd` (Float64): Đơn giá bán thực tế (VND).
- `discount_amount_vnd` (Float64): Tiền giảm giá.
- `net_sales_vnd` (Float64): Doanh thu thuần (Quantity * Unit Price - Discount). Bị trừ đi nếu là dòng đổi/trả hàng.
- `exchange_rate` (Float64): Tỷ giá áp dụng (nếu thanh toán bằng ngoại tệ).
- `is_return` (UInt8): Cờ đánh dấu dòng này là dòng trả hàng (Negative Fact).

### 3.2. `Fact_CashierShiftReconciliation` (Theo dõi Két Tiền Thu Ngân)
Grain ở cấp độ từng ca làm việc của thu ngân.
- `shift_sk` (Int64): Surrogate Key.
- `shift_id` (String): Mã ca làm việc gốc.
- `store_sk` (Int64): FK tới Dim_Store.
- `date_sk` (Int32): FK tới Dim_Date (ngày đóng ca).
- `cashier_id` (String): Mã nhân viên thu ngân.
- `terminal_id` (String): Mã máy POS.
- `opening_cash_float` (Float64): Tiền lẻ đầu ca.
- `system_expected_cash` (Float64): Tiền mặt kỳ vọng trên hệ thống.
- `actual_closing_cash` (Float64): Tiền mặt kiểm đếm thực tế cuối ca.
- `cash_variance` (Float64): Chênh lệch (Actual - Expected). Metric phục vụ bài toán số 3.
