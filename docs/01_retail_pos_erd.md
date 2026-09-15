# Thiết Kế Cơ Sở Dữ Liệu Nguồn (Retail POS)

## 1. Tổng Quan Cấu Trúc Bảng
Để đáp ứng bài toán Phân tích Doanh Thu & Top Sản Phẩm, hệ thống nguồn SQL Server được thiết kế bao gồm 14 bảng, lưu trữ đầy đủ thông tin về Cửa hàng, Sản phẩm, Khách hàng và Giao dịch POS.

## 2. Data Dictionary

### [Phân hệ 1] Cửa hàng & Thiết bị
1. **stores**: Quản lý thông tin chi nhánh siêu thị, diện tích sàn, khu vực.
2. **pos_terminals**: Thông tin máy tính tiền vật lý đặt tại quầy.
3. **cashier_shifts**: Ca làm việc của thu ngân, thời điểm mở/kết ca.

### [Phân hệ 2] Sản phẩm & Giá bán
4. **products**: Danh mục sản phẩm cốt lõi (SKU, Ngành hàng, Phân loại).
5. **product_barcodes**: Danh sách mã vạch quét máy của từng SKU.
6. **store_price_books**: Sổ giá bán lẻ theo từng khu vực hoặc cửa hàng.

### [Phân hệ 3] Khách hàng
7. **customers**: Thông tin định danh khách hàng Loyalty.
8. **customer_loyalty_transactions**: Lịch sử tích điểm của khách hàng.

### [Phân hệ 4] Giao dịch Bán lẻ (Core)
9. **sales_invoices**: Bảng Fact Header lưu tổng hóa đơn (Tổng tiền, Giảm giá, Thuế).
10. **sales_invoice_items**: Bảng Fact Line Item lưu chi tiết từng món hàng trong hóa đơn.
11. **sales_payment_tenders**: Bảng phương thức thanh toán (Tiền mặt, MoMo, VNPay, Ngoại tệ).
12. **sales_item_discounts**: Chi tiết các chương trình khuyến mãi áp dụng.

### [Phân hệ 5] Hoạt động Khác
13. **sales_returns**: Lịch sử hóa đơn bị đổi hoặc trả lại.
14. **store_inventory_snapshots**: Tồn kho tại thời điểm cuối ngày.

## 3. Mô hình Quan hệ (ERD - Simplified)
- `sales_invoices` liên kết với `stores`, `pos_terminals`, `cashier_shifts`, `customers`.
- `sales_invoice_items` liên kết với `sales_invoices` (1-N) và `products` (N-1).
- `sales_payment_tenders` liên kết với `sales_invoices`.

*(File SQL DDL nằm trong thư mục `infra/sources/init-scripts/sqlserver/retail_pos_db.sql`)*
