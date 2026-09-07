# TỪ ĐIỂN DỮ LIỆU CSDL NGUỒN (SOURCE DATA DICTIONARY)
## DỰ ÁN DATA LAKEHOUSE CHO HỆ THỐNG CỬA HÀNG BÁN LẺ TC MART
### (Chi tiết 100% tất cả 12 CSDL và 42 Bảng dữ liệu trích xuất từ ERD.drawio)

> Tài liệu này mô tả đầy đủ tất cả các trường dữ liệu, kiểu dữ liệu, các ràng buộc và ý nghĩa nghiệp vụ tiếng Việt chi tiết của từng bảng trong hệ thống.

---

### HỆ THỐNG PROCUREMENT_DB (procurement_db)

#### 📌 Bảng / File: `suppliers` (Bảng dữ liệu thuộc procurement_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `supplier_id` | `INT` | PK, AUTO_INCREMENT | Mã nhà cung cấp |
| 2 | `supplier_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code nhà cung cấp (VD: SUP001) |
| 3 | `supplier_name` | `VARCHAR(100)` | NULL / Optional | Tên doanh nghiệp nhà cung cấp |
| 4 | `supplier_type` | `VARCHAR(100)` | NULL / Optional | Phân loại nhà cung cấp |
| 5 | `tax_code` | `VARCHAR(50)` | UK, NOT NULL | Mã số thuế doanh nghiệp |
| 6 | `phone` | `VARCHAR(100)` | NULL / Optional | Số điện thoại liên hệ |
| 7 | `email` | `VARCHAR(100)` | NULL / Optional | Địa chỉ Email |
| 8 | `address` | `VARCHAR(100)` | NULL / Optional | Địa chỉ chi tiết |
| 9 | `country` | `INT` | NOT NULL | Quốc gia |
| 10 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |
| 11 | `created_at` | `DATE / TIMESTAMP` | NOT NULL | Thời gian tạo bản ghi |

#### 📌 Bảng / File: `purchase_orders` (Bảng dữ liệu thuộc procurement_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `purchase_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn đặt hàng mua PO |
| 2 | `po_numder` | `VARCHAR(100)` | NULL / Optional | Mã số đơn PO (VD: PO-2026-001) |
| 3 | `supplier_id` | `INT` | PK, AUTO_INCREMENT | Mã nhà cung cấp |
| 4 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 5 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 6 | `order_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày lập đơn đặt hàng mua PO |
| 7 | `expected_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày dự kiến hàng về kho |
| 8 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 9 | `total_amount` | `DECIMAL(18,2)` | NOT NULL | Tổng số tiền thanh toán |
| 10 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `purchase_order_items` (Bảng dữ liệu thuộc procurement_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `purchase_order_item_id` | `INT` | PK, AUTO_INCREMENT | Mã chi tiết sản phẩm đơn PO |
| 2 | `purchase_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn đặt hàng mua PO |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `ordered_quantity` | `INT` | NOT NULL | Số lượng hàng đặt mua theo hợp đồng |
| 5 | `unit_price` | `DECIMAL(18,2)` | NOT NULL | Đơn giá chưa thuế/giảm giá |
| 6 | `tax_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền thuế VAT |
| 7 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 8 | `line_amount` | `DECIMAL(18,2)` | NOT NULL | Thành tiền của dòng sản phẩm |

#### 📌 Bảng / File: `goods_receipts` (Bảng dữ liệu thuộc procurement_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `goods_receipt_id` | `INT` | PK, AUTO_INCREMENT | Mã phiếu nhập kho |
| 2 | `receipt_number` | `VARCHAR(50)` | UK, NOT NULL | Số phiếu nhập kho (VD: GR-2026-001) |
| 3 | `purchase_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn đặt hàng mua PO |
| 4 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 5 | `receipt_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày thực tế nhập hàng vào kho |
| 6 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |
| 7 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |

#### 📌 Bảng / File: `goods_receipts_items` (Bảng dữ liệu thuộc procurement_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `goods_receipt_item_id` | `INT` | PK, AUTO_INCREMENT | Mã dòng chi tiết phiếu nhập kho |
| 2 | `goods_receipt_id` | `INT` | PK, AUTO_INCREMENT | Mã phiếu nhập kho |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `purchase_order_item_id` | `INT` | PK, AUTO_INCREMENT | Mã chi tiết sản phẩm đơn PO |
| 5 | `ordered_quantity` | `INT` | NOT NULL | Số lượng hàng đặt mua theo hợp đồng |
| 6 | `received_quantity` | `INT` | NOT NULL | Số lượng thực tế kho tiếp nhận |
| 7 | `rejected_quantity` | `INT` | NOT NULL | Số lượng hàng trả lại do lỗi/hỏng |

---

### HỆ THỐNG WAREHOUSE_DB (warehouse_db)

#### 📌 Bảng / File: `warehouses` (Bảng dữ liệu thuộc warehouse_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 2 | `warehouse_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code kho hàng (VD: WH-HN-01) |
| 3 | `warehouse_name` | `VARCHAR(100)` | NULL / Optional | Tên kho hàng |
| 4 | `warehouse_type` | `VARCHAR(100)` | NULL / Optional | Loại kho (Kho tổng Central, Kho trung chuyển Transit) |
| 5 | `region` | `VARCHAR(50)` | NOT NULL | Khu vực địa lý (Miền Bắc, Miền Trung, Miền Nam) |
| 6 | `address` | `VARCHAR(100)` | NULL / Optional | Địa chỉ chi tiết |
| 7 | `capacity` | `INT` | NOT NULL | Sức chứa kho (m3 / tấn) |
| 8 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `warehouse_locations` (Bảng dữ liệu thuộc warehouse_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `location_id` | `INT` | PK, AUTO_INCREMENT | Mã vị trí ô/kệ trong kho |
| 2 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 3 | `location_code` | `VARCHAR(50)` | UK, NOT NULL | Mã hiệu vị trí (VD: K-A1-L2) |
| 4 | `location_name` | `VARCHAR(100)` | NULL / Optional | Tên vị trí chi tiết |
| 5 | `zone` | `VARCHAR(100)` | NULL / Optional | Phân khu kho (Khu A, Khu bảo quản lạnh) |

#### 📌 Bảng / File: `inventory_transactions` (Bảng dữ liệu thuộc warehouse_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `inventory_transaction_id` | `INT` | PK, AUTO_INCREMENT | Mã giao dịch thẻ kho |
| 2 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `transaction_type` | `VARCHAR(100)` | NULL / Optional | Loại giao dịch kho (Nhập IN, Xuất OUT, Điều chỉnh ADJUST) |
| 5 | `reference_type` | `VARCHAR(100)` | NULL / Optional | Chứng từ nguồn (PO, TRANSFER, SALE) |
| 6 | `reference_id` | `INT` | PK, AUTO_INCREMENT | Mã chứng từ đối chiếu |
| 7 | `quantity` | `INT` | NOT NULL | Số lượng |
| 8 | `transaction_date` | `DATE / TIMESTAMP` | NOT NULL | Thời gian phát sinh giao dịch kho |
| 9 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |

#### 📌 Bảng / File: `inventory` (Bảng dữ liệu thuộc warehouse_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `inventory_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi tồn kho |
| 2 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 3 | `location_id` | `INT` | PK, AUTO_INCREMENT | Mã vị trí ô/kệ trong kho |
| 4 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 5 | `quantity` | `INT` | NOT NULL | Số lượng |
| 6 | `reserved_quantity` | `INT` | NOT NULL | Số lượng kho giữ hàng chờ giao |
| 7 | `available_quantity` | `INT` | NOT NULL | Số lượng thực tế khả dụng để bán |
| 8 | `last_updated_at` | `DATE / TIMESTAMP` | NOT NULL | Thời điểm cập nhật tồn kho gần nhất |

#### 📌 Bảng / File: `stock_transfers` (Bảng dữ liệu thuộc warehouse_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `transfer_id` | `INT` | PK, AUTO_INCREMENT | Mã lệnh điều chuyển kho |
| 2 | `transfer_number` | `VARCHAR(50)` | UK, NOT NULL | Số lệnh điều chuyển (VD: TRF-001) |
| 3 | `from_warehouse_id` | `INT` | PK, AUTO_INCREMENT | Kho phát hành xuất chuyển |
| 4 | `to_warehouse_id` | `INT` | PK, AUTO_INCREMENT | Kho đích tiếp nhận hàng |
| 5 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 6 | `transfer_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày khởi tạo lệnh điều chuyển |
| 7 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `stock_transfer_items` (Bảng dữ liệu thuộc warehouse_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `transfer_item_id` | `INT` | PK, AUTO_INCREMENT | Mã chi tiết sản phẩm điều chuyển |
| 2 | `transfer_id` | `INT` | PK, AUTO_INCREMENT | Mã lệnh điều chuyển kho |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `quantity` | `INT` | NOT NULL | Số lượng |

---

### HỆ THỐNG PRODUCTION_DB (production_db)

#### 📌 Bảng / File: `factories` (Bảng dữ liệu thuộc production_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `factory_id` | `INT` | PK, AUTO_INCREMENT | Mã xưởng sản xuất |
| 2 | `factory_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code xưởng sản xuất (VD: FAC-01) |
| 3 | `factory_name` | `VARCHAR(100)` | NULL / Optional | Tên xưởng sản xuất nội bộ |
| 4 | `region` | `VARCHAR(50)` | NOT NULL | Khu vực địa lý (Miền Bắc, Miền Trung, Miền Nam) |
| 5 | `address` | `VARCHAR(100)` | NULL / Optional | Địa chỉ chi tiết |
| 6 | `capacity` | `INT` | NOT NULL | Sức chứa kho (m3 / tấn) |
| 7 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `production_orders` (Bảng dữ liệu thuộc production_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `production_order_id` | `INT` | PK, AUTO_INCREMENT | Mã lệnh sản xuất thành phẩm |
| 2 | `production_order_number` | `VARCHAR(50)` | UK, NOT NULL | Mã số lệnh sản xuất (VD: PRD-2026-001) |
| 3 | `factory_id` | `INT` | PK, AUTO_INCREMENT | Mã xưởng sản xuất |
| 4 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 5 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 6 | `planned_quantity` | `INT` | NOT NULL | Số lượng sản phẩm kế hoạch sản xuất |
| 7 | `actual_quantity` | `INT` | NOT NULL | Số lượng sản phẩm thực tế hoàn thành |
| 8 | `start_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày bắt đầu sản xuất |
| 9 | `end_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày hoàn thành lệnh sản xuất |
| 10 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `finished_products` (Bảng dữ liệu thuộc production_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `finished_product_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi thành phẩm nhập kho |
| 2 | `production_order_id` | `INT` | PK, AUTO_INCREMENT | Mã lệnh sản xuất thành phẩm |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `quantity` | `INT` | NOT NULL | Số lượng |
| 5 | `production_date` | `DATE / TIMESTAMP` | NOT NULL | Thời gian hoàn thành sản xuất thành phẩm |
| 6 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |

#### 📌 Bảng / File: `production_order_items` (Bảng dữ liệu thuộc production_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `production_order_item_id` | `INT` | PK, AUTO_INCREMENT | Mã dòng kế hoạch định mức nguyên liệu |
| 2 | `production_order_id` | `INT` | PK, AUTO_INCREMENT | Mã lệnh sản xuất thành phẩm |
| 3 | `material_id` | `INT` | PK, AUTO_INCREMENT | Mã nguyên vật liệu |
| 4 | `plan` | `VARCHAR(100)` | NULL / Optional | Mô tả thuộc tính nghiệp vụ plan |
| 5 | `ned_quantity` | `INT` | NOT NULL | Mô tả thuộc tính nghiệp vụ ned_quantity |
| 6 | `actual_quantity` | `INT` | NOT NULL | Số lượng sản phẩm thực tế hoàn thành |

#### 📌 Bảng / File: `material_consumptions` (Bảng dữ liệu thuộc production_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `consumption_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi thực tế tiêu hao nguyên liệu |
| 2 | `production_order_id` | `INT` | PK, AUTO_INCREMENT | Mã lệnh sản xuất thành phẩm |
| 3 | `material_id` | `INT` | PK, AUTO_INCREMENT | Mã nguyên vật liệu |
| 4 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 5 | `quantity` | `INT` | NOT NULL | Số lượng |
| 6 | `consumed_at` | `DATE / TIMESTAMP` | NOT NULL | Thời điểm xuất kho nguyên liệu sản xuất |

#### 📌 Bảng / File: `raw_materials` (Bảng dữ liệu thuộc production_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `material_id` | `INT` | PK, AUTO_INCREMENT | Mã nguyên vật liệu |
| 2 | `material_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code nguyên vật liệu |
| 3 | `material_name` | `VARCHAR(100)` | NULL / Optional | Tên nguyên vật liệu sản xuất |
| 4 | `unit` | `VARCHAR(100)` | NULL / Optional | Đơn vị tính |

---

### HỆ THỐNG RETAIL_POS_DB (retail_pos_db)

#### 📌 Bảng / File: `stores` (Bảng dữ liệu thuộc retail_pos_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `store_id` | `INT` | PK, AUTO_INCREMENT | Mã cửa hàng bán lẻ |
| 2 | `store_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code cửa hàng (VD: STR-HN-01) |
| 3 | `store_name` | `VARCHAR(100)` | NULL / Optional | Tên cửa hàng bán lẻ |
| 4 | `region` | `VARCHAR(50)` | NOT NULL | Khu vực địa lý (Miền Bắc, Miền Trung, Miền Nam) |
| 5 | `address` | `VARCHAR(100)` | NULL / Optional | Địa chỉ chi tiết |
| 6 | `city` | `VARCHAR(100)` | NULL / Optional | Tỉnh / Thành phố |
| 7 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 8 | `opened_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày chính thức khai trương cửa hàng |
| 9 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `sales_orders` (Bảng dữ liệu thuộc retail_pos_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `sales_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn hàng bán POS |
| 2 | `order_number` | `VARCHAR(50)` | UK, NOT NULL | Số hóa đơn bán hàng POS (VD: POS-20260907-001) |
| 3 | `store_id` | `INT` | PK, AUTO_INCREMENT | Mã cửa hàng bán lẻ |
| 4 | `terminal_id` | `INT` | PK, AUTO_INCREMENT | Mã máy thu ngân POS |
| 5 | `customer_id` | `INT` | PK, AUTO_INCREMENT | Mã khách hàng |
| 6 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 7 | `order_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày lập đơn đặt hàng mua PO |
| 8 | `channel` | `VARCHAR(50)` | NOT NULL | Kênh bán hàng (POS, Web, App) |
| 9 | `subtotal` | `DECIMAL(18,2)` | NOT NULL | Tổng tiền trước thuế/giảm giá |
| 10 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 11 | `tax_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền thuế VAT |
| 12 | `total_amount` | `DECIMAL(18,2)` | NOT NULL | Tổng số tiền thanh toán |
| 13 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `pos_terminals` (Bảng dữ liệu thuộc retail_pos_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `terminal_id` | `INT` | PK, AUTO_INCREMENT | Mã máy thu ngân POS |
| 2 | `store_id` | `INT` | PK, AUTO_INCREMENT | Mã cửa hàng bán lẻ |
| 3 | `terminal_code` | `VARCHAR(50)` | UK, NOT NULL | Mã hiệu máy POS (VD: POS-01) |
| 4 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `sales_order_items` (Bảng dữ liệu thuộc retail_pos_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `sales_order_item_id` | `INT` | PK, AUTO_INCREMENT | Mã dòng hóa đơn bán lẻ POS |
| 2 | `sales_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn hàng bán POS |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `quantity` | `INT` | NOT NULL | Số lượng |
| 5 | `unit_price` | `DECIMAL(18,2)` | NOT NULL | Đơn giá chưa thuế/giảm giá |
| 6 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 7 | `tax_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền thuế VAT |
| 8 | `line_total` | `DECIMAL(18,2)` | NOT NULL | Thành tiền dòng = (Giá * SL) - Giảm giá |

#### 📌 Bảng / File: `payments` (Bảng dữ liệu thuộc retail_pos_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `payment_id` | `INT` | PK, AUTO_INCREMENT | Mã giao dịch thanh toán |
| 2 | `sales_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn hàng bán POS |
| 3 | `payment_method` | `VARCHAR(50)` | NOT NULL | Hình thức thanh toán (Tiền mặt Cash, Thẻ Card, QR Code, Momo, COD) |
| 4 | `amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giao dịch |
| 5 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 6 | `payment_time` | `DATE / TIMESTAMP` | NOT NULL | Thời gian thực hiện thanh toán |
| 7 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `pos_inventory` (Bảng dữ liệu thuộc retail_pos_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `pos_inventory_id` | `INT` | PK, AUTO_INCREMENT | Mã tồn kho quầy bán lẻ |
| 2 | `store_id` | `INT` | PK, AUTO_INCREMENT | Mã cửa hàng bán lẻ |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `quantity` | `INT` | NOT NULL | Số lượng |
| 5 | `last_updated_at` | `DATE / TIMESTAMP` | NOT NULL | Thời điểm cập nhật tồn kho gần nhất |

---

### HỆ THỐNG ECOMMERCE_DB (ecommerce_db)

#### 📌 Bảng / File: `customers` (Bảng dữ liệu thuộc ecommerce_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `customer_id` | `INT` | PK, AUTO_INCREMENT | Mã khách hàng |
| 2 | `customer_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code khách hàng thành viên (VD: CUST-1001) |
| 3 | `fullname` | `VARCHAR(100)` | NULL / Optional | Họ và tên khách hàng đầy đủ |
| 4 | `email` | `VARCHAR(100)` | NULL / Optional | Địa chỉ Email |
| 5 | `phone` | `VARCHAR(100)` | NULL / Optional | Số điện thoại liên hệ |
| 6 | `gender` | `VARCHAR(100)` | NULL / Optional | Giới tính khách hàng |
| 7 | `date_of_birth` | `DATE / TIMESTAMP` | NOT NULL | Ngày tháng năm sinh |
| 8 | `country` | `INT` | NOT NULL | Quốc gia |
| 9 | `customer_type` | `VARCHAR(100)` | NULL / Optional | Phân loại khách hàng (Bán lẻ Retail, Bán sỉ Wholesale) |
| 10 | `created_at` | `DATE / TIMESTAMP` | NOT NULL | Thời gian tạo bản ghi |
| 11 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `online_orders` (Bảng dữ liệu thuộc ecommerce_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `online_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn hàng online Web/App |
| 2 | `order_number` | `VARCHAR(50)` | UK, NOT NULL | Số hóa đơn bán hàng POS (VD: POS-20260907-001) |
| 3 | `customer_id` | `INT` | PK, AUTO_INCREMENT | Mã khách hàng |
| 4 | `order_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày lập đơn đặt hàng mua PO |
| 5 | `channel` | `VARCHAR(50)` | NOT NULL | Kênh bán hàng (POS, Web, App) |
| 6 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 7 | `subtotal` | `DECIMAL(18,2)` | NOT NULL | Tổng tiền trước thuế/giảm giá |
| 8 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 9 | `shipping_fee` | `VARCHAR(100)` | NULL / Optional | Phí vận chuyển giao hàng |
| 10 | `total_amount` | `DECIMAL(18,2)` | NOT NULL | Tổng số tiền thanh toán |
| 11 | `order_status` | `VARCHAR(100)` | NULL / Optional | Trạng thái đơn online (Pending, Processing, Delivered, Cancelled) |

#### 📌 Bảng / File: `delivery_addresses` (Bảng dữ liệu thuộc ecommerce_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `address_id` | `INT` | PK, AUTO_INCREMENT | Mã địa chỉ giao hàng |
| 2 | `customer_id` | `INT` | PK, AUTO_INCREMENT | Mã khách hàng |
| 3 | `recipient_name` | `VARCHAR(100)` | NULL / Optional | Tên người nhận hàng |
| 4 | `phone` | `VARCHAR(100)` | NULL / Optional | Số điện thoại liên hệ |
| 5 | `country` | `INT` | NOT NULL | Quốc gia |
| 6 | `province` | `VARCHAR(100)` | NULL / Optional | Mô tả thuộc tính nghiệp vụ province |
| 7 | `district` | `VARCHAR(100)` | NULL / Optional | Quận / Huyện |
| 8 | `ward` | `VARCHAR(100)` | NULL / Optional | Phường / Xã |
| 9 | `address_detail` | `VARCHAR(100)` | NULL / Optional | Số nhà, tên đường chi tiết |
| 10 | `is_default` | `VARCHAR(100)` | NULL / Optional | Cờ báo địa chỉ giao hàng mặc định (True/False) |

#### 📌 Bảng / File: `online_order_items` (Bảng dữ liệu thuộc ecommerce_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `online_order_item_id` | `INT` | PK, AUTO_INCREMENT | Mã dòng sản phẩm đơn online |
| 2 | `online_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn hàng online Web/App |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `quantity` | `INT` | NOT NULL | Số lượng |
| 5 | `unit_price` | `DECIMAL(18,2)` | NOT NULL | Đơn giá chưa thuế/giảm giá |
| 6 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 7 | `line_total` | `DECIMAL(18,2)` | NOT NULL | Thành tiền dòng = (Giá * SL) - Giảm giá |

#### 📌 Bảng / File: `payments` (Bảng dữ liệu thuộc ecommerce_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `payment_id` | `INT` | PK, AUTO_INCREMENT | Mã giao dịch thanh toán |
| 2 | `online_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn hàng online Web/App |
| 3 | `payment_method` | `VARCHAR(50)` | NOT NULL | Hình thức thanh toán (Tiền mặt Cash, Thẻ Card, QR Code, Momo, COD) |
| 4 | `transaction_code` | `VARCHAR(50)` | UK, NOT NULL | Mã giao dịch ngân hàng / cổng thanh toán |
| 5 | `amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giao dịch |
| 6 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 7 | `payment_time` | `DATE / TIMESTAMP` | NOT NULL | Thời gian thực hiện thanh toán |
| 8 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

---

### HỆ THỐNG FRANCHISE_DB (franchise_db)

#### 📌 Bảng / File: `franchisees` (Bảng dữ liệu thuộc franchise_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `franchisee_id` | `INT` | PK, AUTO_INCREMENT | Mã đại lý nhượng quyền |
| 2 | `franchisee_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code đại lý (VD: FR-001) |
| 3 | `franchisee_name` | `VARCHAR(100)` | NULL / Optional | Tên công ty / doanh nghiệp đại lý |
| 4 | `owner_name` | `VARCHAR(100)` | NULL / Optional | Tên chủ đại lý / người đại diện pháp luật |
| 5 | `phone` | `VARCHAR(100)` | NULL / Optional | Số điện thoại liên hệ |
| 6 | `email` | `VARCHAR(100)` | NULL / Optional | Địa chỉ Email |
| 7 | `region` | `VARCHAR(50)` | NOT NULL | Khu vực địa lý (Miền Bắc, Miền Trung, Miền Nam) |
| 8 | `city` | `VARCHAR(100)` | NULL / Optional | Tỉnh / Thành phố |
| 9 | `address` | `VARCHAR(100)` | NULL / Optional | Địa chỉ chi tiết |
| 10 | `contract_start` | `VARCHAR(100)` | NULL / Optional | Ngày bắt đầu hợp đồng nhượng quyền |
| 11 | `contract_end` | `VARCHAR(100)` | NULL / Optional | Ngày hết hạn hợp đồng nhượng quyền |
| 12 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `franchise_orders` (Bảng dữ liệu thuộc franchise_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `franchisee_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn mua sỉ của đại lý |
| 2 | `order_number` | `VARCHAR(50)` | UK, NOT NULL | Số hóa đơn bán hàng POS (VD: POS-20260907-001) |
| 3 | `franchisee_id` | `INT` | PK, AUTO_INCREMENT | Mã đại lý nhượng quyền |
| 4 | `order_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày lập đơn đặt hàng mua PO |
| 5 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 6 | `total_amount` | `DECIMAL(18,2)` | NOT NULL | Tổng số tiền thanh toán |
| 7 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `franchise_monthly_reports` (Bảng dữ liệu thuộc franchise_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `report_id` | `INT` | PK, AUTO_INCREMENT | Mã báo cáo doanh thu đại lý |
| 2 | `franchisee_id` | `INT` | PK, AUTO_INCREMENT | Mã đại lý nhượng quyền |
| 3 | `report_month` | `VARCHAR(100)` | NULL / Optional | Tháng báo cáo doanh thu (YYYY-MM) |
| 4 | `total_sales` | `DECIMAL(18,2)` | NOT NULL | Tổng doanh thu đại lý báo cáo |
| 5 | `total_quantity` | `DECIMAL(18,2)` | NOT NULL | Tổng số lượng sản phẩm đại lý bán ra |
| 6 | `return_quantity` | `INT` | NOT NULL | Số lượng sản phẩm khách trả lại đại lý |
| 7 | `net_sales` | `VARCHAR(100)` | NULL / Optional | Doanh thu thuần sau đổi trả của đại lý |
| 8 | `file_name` | `VARCHAR(100)` | NULL / Optional | Tên file báo cáo Excel đính kèm |
| 9 | `received_at` | `DATE / TIMESTAMP` | NOT NULL | Thời điểm tiếp nhận file vào Data Lake |

#### 📌 Bảng / File: `franchise_orders_items` (Bảng dữ liệu thuộc franchise_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `franchisee_order_item_id` | `INT` | PK, AUTO_INCREMENT | Mã dòng sản phẩm đơn mua sỉ |
| 2 | `franchisee_order_id` | `INT` | PK, AUTO_INCREMENT | Mã đơn mua sỉ của đại lý |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `quantity` | `INT` | NOT NULL | Số lượng |
| 5 | `unit_price` | `DECIMAL(18,2)` | NOT NULL | Đơn giá chưa thuế/giảm giá |
| 6 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 7 | `line_total` | `DECIMAL(18,2)` | NOT NULL | Thành tiền dòng = (Giá * SL) - Giảm giá |

---

### HỆ THỐNG PRODUCT_DB (product_db)

#### 📌 Bảng / File: `categories` (Bảng dữ liệu thuộc product_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `category_id` | `INT` | PK, AUTO_INCREMENT | Mã danh mục ngành hàng |
| 2 | `category_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code ngành hàng (VD: CAT-BEV) |
| 3 | `category_name` | `VARCHAR(100)` | NULL / Optional | Tên ngành hàng (Đồ uống, Bánh kẹo...) |
| 4 | `parent_category_id` | `INT` | PK, AUTO_INCREMENT | Mã ngành hàng cấp cha (dành cho cây danh mục) |

#### 📌 Bảng / File: `brands` (Bảng dữ liệu thuộc product_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `brand_id` | `INT` | PK, AUTO_INCREMENT | Mã thương hiệu |
| 2 | `brand_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code thương hiệu (VD: BRD-VNM) |
| 3 | `brand_name` | `VARCHAR(100)` | NULL / Optional | Tên thương hiệu sản phẩm (Vinamilk, Pepsi) |

#### 📌 Bảng / File: `products` (Bảng dữ liệu thuộc product_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 2 | `product_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code sản phẩm (VD: PROD-10001) |
| 3 | `product_name` | `VARCHAR(100)` | NULL / Optional | Tên đầy đủ của sản phẩm |
| 4 | `category_id` | `INT` | PK, AUTO_INCREMENT | Mã danh mục ngành hàng |
| 5 | `brand_id` | `INT` | PK, AUTO_INCREMENT | Mã thương hiệu |
| 6 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 7 | `unit` | `VARCHAR(100)` | NULL / Optional | Đơn vị tính |
| 8 | `barcode` | `VARCHAR(100)` | NULL / Optional | Mã vạch sản phẩm EAN-13 |
| 9 | `product_type` | `VARCHAR(100)` | NULL / Optional | Loại sản phẩm (Thành phẩm Finished_Good, Nguyên liệu Raw_Material) |
| 10 | `cost_price` | `DECIMAL(18,2)` | NOT NULL | Giá vốn niêm yết mua vào |
| 11 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |
| 12 | `created_at` | `DATE / TIMESTAMP` | NOT NULL | Thời gian tạo bản ghi |

#### 📌 Bảng / File: `product_prices` (Bảng dữ liệu thuộc product_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `price_id` | `INT` | PK, AUTO_INCREMENT | Mã bảng giá bán niêm yết |
| 2 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 3 | `price_type` | `DECIMAL(18,2)` | NOT NULL | Loại giá (Giá bán lẻ POS, Giá Online, Giá Bán sỉ) |
| 4 | `price` | `DECIMAL(18,2)` | NOT NULL | Mức giá bán quy định |
| 5 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 6 | `effective_from` | `VARCHAR(100)` | NULL / Optional | Ngày bắt đầu hiệu lực bảng giá |
| 7 | `effective_to` | `VARCHAR(100)` | NULL / Optional | Ngày kết thúc hiệu lực bảng giá |

---

### HỆ THỐNG PROMOTION_DB (promotion_db)

#### 📌 Bảng / File: `promotions` (Bảng dữ liệu thuộc promotion_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `promotion_id` | `INT` | PK, AUTO_INCREMENT | Mã chương trình khuyến mãi |
| 2 | `promotion_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code khuyến mãi (VD: PROMO-SUMMER) |
| 3 | `promotion_name` | `VARCHAR(100)` | NULL / Optional | Tên chương trình khuyến mãi |
| 4 | `promotion_type` | `VARCHAR(100)` | NULL / Optional | Loại khuyến mãi (Percent_Discount, Fixed_Amount, Buy1Get1) |
| 5 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 6 | `start_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày bắt đầu sản xuất |
| 7 | `end_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày hoàn thành lệnh sản xuất |
| 8 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `promotion_products` (Bảng dữ liệu thuộc promotion_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `promotion_product_id` | `INT` | PK, AUTO_INCREMENT | Mã chi tiết sản phẩm tham gia KM |
| 2 | `promotion_id` | `INT` | PK, AUTO_INCREMENT | Mã chương trình khuyến mãi |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |

#### 📌 Bảng / File: `promotion_stores` (Bảng dữ liệu thuộc promotion_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `promotion_store_id` | `INT` | PK, AUTO_INCREMENT | Mã chi tiết cửa hàng áp dụng KM |
| 2 | `promotion_id` | `INT` | PK, AUTO_INCREMENT | Mã chương trình khuyến mãi |
| 3 | `store_id` | `INT` | PK, AUTO_INCREMENT | Mã cửa hàng bán lẻ |

#### 📌 Bảng / File: `promotion_discounts` (Bảng dữ liệu thuộc promotion_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `discount_id` | `INT` | PK, AUTO_INCREMENT | Mã định mức giảm giá KM |
| 2 | `promotion_id` | `INT` | PK, AUTO_INCREMENT | Mã chương trình khuyến mãi |
| 3 | `discount_type` | `INT` | NOT NULL | Kiểu giảm giá (Phần trăm %, Số tiền VND) |
| 4 | `discount_value` | `INT` | NOT NULL | Giá trị giảm tương ứng |
| 5 | `max_discount` | `INT` | NOT NULL | Số tiền giảm giá tối đa |
| 6 | `min_order_value` | `VARCHAR(100)` | NULL / Optional | Giá trị đơn hàng tối thiểu để nhận KM |

---

### HỆ THỐNG MARKETING_DB (marketing_db)

#### 📌 Bảng / File: `campaigns` (Bảng dữ liệu thuộc marketing_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `campaign_id` | `INT` | PK, AUTO_INCREMENT | Mã chiến dịch Marketing |
| 2 | `campaign_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code chiến dịch (VD: MKT-FB-01) |
| 3 | `campaign_name` | `VARCHAR(100)` | NULL / Optional | Tên chiến dịch quảng cáo |
| 4 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 5 | `start_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày bắt đầu sản xuất |
| 6 | `end_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày hoàn thành lệnh sản xuất |
| 7 | `budget` | `VARCHAR(100)` | NULL / Optional | Ngân sách cấp cho chiến dịch Marketing |
| 8 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `campaign_channels` (Bảng dữ liệu thuộc marketing_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `channel_id` | `INT` | PK, AUTO_INCREMENT | Mã kênh truyền thông quảng cáo |
| 2 | `campaign_id` | `INT` | PK, AUTO_INCREMENT | Mã chiến dịch Marketing |
| 3 | `channel_name` | `VARCHAR(100)` | NULL / Optional | Tên kênh quảng cáo (Facebook_Ads, Google_Ads, TikTok_Ads) |

#### 📌 Bảng / File: `impressions` (Bảng dữ liệu thuộc marketing_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `impression_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi lượt hiển thị quảng cáo |
| 2 | `campaign_id` | `INT` | PK, AUTO_INCREMENT | Mã chiến dịch Marketing |
| 3 | `channel_id` | `INT` | PK, AUTO_INCREMENT | Mã kênh truyền thông quảng cáo |
| 4 | `event_time` | `DATE / TIMESTAMP` | NOT NULL | Thời gian phát sinh sự kiện quảng cáo |
| 5 | `impression_count` | `INT` | NOT NULL | Số lượt hiển thị quảng cáo ghi nhận |

#### 📌 Bảng / File: `clicks` (Bảng dữ liệu thuộc marketing_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `click_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi lượt nhấp chuột quảng cáo |
| 2 | `campaign_id` | `INT` | PK, AUTO_INCREMENT | Mã chiến dịch Marketing |
| 3 | `channel_id` | `INT` | PK, AUTO_INCREMENT | Mã kênh truyền thông quảng cáo |
| 4 | `event_time` | `DATE / TIMESTAMP` | NOT NULL | Thời gian phát sinh sự kiện quảng cáo |
| 5 | `click_count` | `INT` | NOT NULL | Số lượt nhấp chuột vào quảng cáo |

#### 📌 Bảng / File: `campaign_costs` (Bảng dữ liệu thuộc marketing_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `cost_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi chi phí quảng cáo |
| 2 | `campaign_id` | `INT` | PK, AUTO_INCREMENT | Mã chiến dịch Marketing |
| 3 | `channel_id` | `INT` | PK, AUTO_INCREMENT | Mã kênh truyền thông quảng cáo |
| 4 | `cost_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày ghi nhận chi phí quảng cáo |
| 5 | `amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giao dịch |
| 6 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |

---

### HỆ THỐNG INVOICE_DB (invoice_db)

#### 📌 Bảng / File: `invoices` (Bảng dữ liệu thuộc invoice_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `invoice_id` | `INT` | PK, AUTO_INCREMENT | Mã hóa đơn điện tử GTGT |
| 2 | `invoice_number` | `VARCHAR(50)` | UK, NOT NULL | Số hóa đơn GTGT (VD: HD-2026-0091) |
| 3 | `invoice_type` | `VARCHAR(100)` | NULL / Optional | Loại hóa đơn (Hóa đơn bán VAT_Sale, Hóa đơn mua VAT_Purchase) |
| 4 | `invoice_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày giờ phát hành hóa đơn điện tử |
| 5 | `seller_tax_code` | `VARCHAR(50)` | UK, NOT NULL | Mã số thuế bên bán (TC MART) |
| 6 | `buyer_tax_code` | `VARCHAR(50)` | UK, NOT NULL | Mã số thuế đơn vị mua hàng |
| 7 | `buyer_name` | `VARCHAR(100)` | NULL / Optional | Tên cá nhân / đơn vị mua hàng |
| 8 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 9 | `subtotal` | `DECIMAL(18,2)` | NOT NULL | Tổng tiền trước thuế/giảm giá |
| 10 | `tax_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền thuế VAT |
| 11 | `total_amount` | `DECIMAL(18,2)` | NOT NULL | Tổng số tiền thanh toán |
| 12 | `xml_file_name` | `VARCHAR(100)` | NULL / Optional | Tên file XML lưu giữ trong Data Lake |
| 13 | `received_at` | `DATE / TIMESTAMP` | NOT NULL | Thời điểm tiếp nhận file vào Data Lake |
| 14 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `invoice_items` (Bảng dữ liệu thuộc invoice_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `invoice_item_id` | `INT` | PK, AUTO_INCREMENT | Mã chi tiết sản phẩm trên hóa đơn XML |
| 2 | `invoice_id` | `INT` | PK, AUTO_INCREMENT | Mã hóa đơn điện tử GTGT |
| 3 | `product_id` | `INT` | PK, AUTO_INCREMENT | Mã sản phẩm master |
| 4 | `tax_rate` | `DECIMAL(18,2)` | NOT NULL | Thuế suất VAT áp dụng (%8, %10) |
| 5 | `description` | `VARCHAR(100)` | NULL / Optional | Tên diễn giải hàng hóa trên hóa đơn XML |
| 6 | `quantity` | `INT` | NOT NULL | Số lượng |
| 7 | `unit_price` | `DECIMAL(18,2)` | NOT NULL | Đơn giá chưa thuế/giảm giá |
| 8 | `discount_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền giảm giá / chiết khấu |
| 9 | `tax_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền thuế VAT |
| 10 | `line_total` | `DECIMAL(18,2)` | NOT NULL | Thành tiền dòng = (Giá * SL) - Giảm giá |

#### 📌 Bảng / File: `invoice_taxes` (Bảng dữ liệu thuộc invoice_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `invoice_tax_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi tổng hợp thuế VAT |
| 2 | `invoice_id` | `INT` | PK, AUTO_INCREMENT | Mã hóa đơn điện tử GTGT |
| 3 | `tax_rate` | `DECIMAL(18,2)` | NOT NULL | Thuế suất VAT áp dụng (%8, %10) |
| 4 | `taxable_amount` | `DECIMAL(18,2)` | NOT NULL | Doanh số chịu thuế VAT |
| 5 | `tax_amount` | `DECIMAL(18,2)` | NOT NULL | Số tiền thuế VAT |

---

### HỆ THỐNG EXCHANGE_RATE_DB (exchange_rate_db)

#### 📌 Bảng / File: `currencies` (Bảng dữ liệu thuộc exchange_rate_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `currency_id` | `INT` | PK, AUTO_INCREMENT | Mã đồng tiền ngoại tệ |
| 2 | `currency_code` | `VARCHAR(50)` | UK, NOT NULL | Đơn vị tiền tệ (VND, USD, CNY) |
| 3 | `currency_name` | `VARCHAR(100)` | NULL / Optional | Mô tả thuộc tính nghiệp vụ currency_name |
| 4 | `symbol` | `VARCHAR(100)` | NULL / Optional | Ký hiệu tiền tệ ($, ¥, ₫) |

#### 📌 Bảng / File: `exchange_rates` (Bảng dữ liệu thuộc exchange_rate_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `exchange_rate_id` | `INT` | PK, AUTO_INCREMENT | Mã bản ghi tỷ giá ngoại tệ |
| 2 | `from_currency` | `VARCHAR(100)` | NULL / Optional | Đồng tiền gốc quy đổi (USD, CNY) |
| 3 | `to_` | `VARCHAR(100)` | NULL / Optional | Mô tả thuộc tính nghiệp vụ to_ |
| 4 | `currency` | `VARCHAR(100)` | NULL / Optional | Mô tả thuộc tính nghiệp vụ currency |
| 5 | `rate` | `DECIMAL(18,2)` | NOT NULL | Tỷ giá quy đổi thực tế (VD: 25400.50) |
| 6 | `rate_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày áp dụng tỷ giá |
| 7 | `source` | `VARCHAR(100)` | NULL / Optional | Nguồn công bố tỷ giá (Vietcombank, Ngân hàng Nhà nước) |
| 8 | `received_at` | `DATE / TIMESTAMP` | NOT NULL | Thời điểm tiếp nhận file vào Data Lake |

---

### HỆ THỐNG EMPLOYEE_DB (employee_db)

#### 📌 Bảng / File: `departments` (Bảng dữ liệu thuộc employee_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `department_id` | `INT` | PK, AUTO_INCREMENT | Mã phòng ban |
| 2 | `department_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code phòng ban (VD: DEP-SALES) |
| 3 | `department_name` | `VARCHAR(100)` | NULL / Optional | Tên phòng ban |
| 4 | `description` | `VARCHAR(100)` | NULL / Optional | Tên diễn giải hàng hóa trên hóa đơn XML |
| 5 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `positions` (Bảng dữ liệu thuộc employee_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `position_id` | `INT` | PK, AUTO_INCREMENT | Mã vị trí chức danh công việc |
| 2 | `position_code` | `VARCHAR(50)` | UK, NOT NULL | Mã code chức danh (VD: POS-CASHIER) |
| 3 | `position_name` | `VARCHAR(100)` | NULL / Optional | Tên chức danh công việc (Thu ngân, Quản đốc) |
| 4 | `department_id` | `INT` | PK, AUTO_INCREMENT | Mã phòng ban |
| 5 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `employee_assignments` (Bảng dữ liệu thuộc employee_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `assignment_id` | `INT` | PK, AUTO_INCREMENT | Mã phân công địa điểm làm việc |
| 2 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 3 | `assignment_type` | `VARCHAR(100)` | NULL / Optional | Nơi được phân công (Cửa hàng Store, Kho Warehouse, Xưởng Factory) |
| 4 | `store_id` | `INT` | PK, AUTO_INCREMENT | Mã cửa hàng bán lẻ |
| 5 | `warehouse_id` | `INT` | PK, AUTO_INCREMENT | Mã kho hàng |
| 6 | `factory_id` | `INT` | PK, AUTO_INCREMENT | Mã xưởng sản xuất |
| 7 | `start_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày bắt đầu sản xuất |
| 8 | `end_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày hoàn thành lệnh sản xuất |
| 9 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `employee_shifts` (Bảng dữ liệu thuộc employee_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `shift_id` | `INT` | PK, AUTO_INCREMENT | Mã ca làm việc |
| 2 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 3 | `shift_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày trực ca làm việc |
| 4 | `shift_type` | `VARCHAR(100)` | NULL / Optional | Loại ca làm việc (Ca sáng Morning, Ca chiều Afternoon, Ca đêm Night) |
| 5 | `start_time` | `DATE / TIMESTAMP` | NOT NULL | Giờ bắt đầu ca trực |
| 6 | `end_time` | `DATE / TIMESTAMP` | NOT NULL | Giờ kết thúc ca trực |
| 7 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

#### 📌 Bảng / File: `employees` (Bảng dữ liệu thuộc employee_db)

| STT | Tên Trường (Field Name) | Kiểu Dữ Liệu (Data Type) | Ràng Buộc (Constraints) | Ý Nghĩa / Mô Tả Nghiệp Vụ |
|:---:|:---|:---|:---|:---|
| 1 | `employee_id` | `INT` | PK, AUTO_INCREMENT | Mã định danh nhân viên |
| 2 | `employee_code` | `VARCHAR(50)` | UK, NOT NULL | Mã nhân viên (VD: EMP-0001) |
| 3 | `full_name` | `VARCHAR(100)` | NULL / Optional | Họ và tên nhân viên |
| 4 | `gender` | `VARCHAR(100)` | NULL / Optional | Giới tính khách hàng |
| 5 | `date_of_birth` | `DATE / TIMESTAMP` | NOT NULL | Ngày tháng năm sinh |
| 6 | `phone` | `VARCHAR(100)` | NULL / Optional | Số điện thoại liên hệ |
| 7 | `email` | `VARCHAR(100)` | NULL / Optional | Địa chỉ Email |
| 8 | `address` | `VARCHAR(100)` | NULL / Optional | Địa chỉ chi tiết |
| 9 | `position_id` | `INT` | PK, AUTO_INCREMENT | Mã vị trí chức danh công việc |
| 10 | `hire_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày chính thức vào làm |
| 11 | `termination_date` | `DATE / TIMESTAMP` | NOT NULL | Ngày nghỉ việc chính thức |
| 12 | `employment_type` | `VARCHAR(100)` | NULL / Optional | Loại hợp đồng lao động (FullTime, PartTime) |
| 13 | `status` | `VARCHAR(50)` | NOT NULL | Trạng thái hoạt động / xử lý |

