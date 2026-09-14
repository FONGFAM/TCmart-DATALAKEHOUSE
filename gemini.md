Góc nhìn của bạn hoàn toàn chuẩn xác cho một hệ thống bán lẻ thực tế. Trong một chuỗi siêu thị như TC Mart, cơ sở dữ liệu vận hành tại cửa hàng (In-Store Operations & POS System) không thể chỉ có 2–3 bảng hóa đơn đơn giản, mà là một hệ thống quản trị điểm bán hoàn chỉnh quản lý từ ca kíp thu ngân, két tiền, chia nhỏ hình thức thanh toán (split-tender), danh mục bảng giá theo khu vực, đổi trả hàng đến kiểm kê tồn kho quầy kệ.

Dưới đây là thiết kế chuẩn hóa gồm **14 bảng quan hệ** phản ánh đầy đủ hoạt động nghiệp vụ của chuỗi cửa hàng bán lẻ offline TC Mart trên **SQL Server**.

---

### SƠ ĐỒ PHÂN HỆ QUẢN TRỊ ĐIỂM BÁN (IN-STORE OLTP)

```
[ CẤU TRÚC ĐIỂM BÁN & THU NGÂN ]
├── 1. stores (Thông tin siêu thị, diện tích, phân vùng)
├── 2. pos_terminals (Máy POS vật lý tại quầy)
└── 3. cashier_shifts (Ca làm việc, số dư két đầu ca, chốt két cuối ca)

[ DANH MỤC SẢN PHẨM & CHÍNH SÁCH GIÁ ]
├── 4. products (Danh mục hàng hóa tổng)
├── 5. product_barcodes (Mã vạch EAN-13, mã thùng/lốc)
└── 6. store_price_books (Bảng giá bán lẻ phân theo vùng/siêu thị)

[ KHÁCH HÀNG & THÀNH VIÊN OFFLINE ]
├── 7. customers (Khách hàng thành viên)
└── 8. customer_loyalty_transactions (Lịch sử tích/tiêu điểm tại quầy)

[ GIAO DỊCH BÁN LẺ & THANH TOÁN (CORE FACT) ]
├── 9.  sales_invoices (Hóa đơn bán lẻ - Header)
├── 10. sales_invoice_items (Chi tiết từng món hàng - Line Item)
├── 11. sales_payment_tenders (Phân bổ thanh toán: Tiền mặt, Thẻ, QR, Ngoại tệ)
└── 12. sales_item_discounts (Chi tiết voucher, khuyến mãi áp vào từng dòng)

[ HẬU MÃI & QUẢN TRỊ TỒN KHO TẠI CHỖ ]
├── 13. sales_returns (Phiếu đổi trả hàng, hủy hóa đơn)
└── 14. store_inventory_snapshots (Tồn kho thực tế tại quầy và kho sau siêu thị)

```

---

### CHI TIẾT 14 BẢNG CƠ SỞ DỮ LIỆU BÁN LẺ OFFLINE (SQL SERVER)

#### Phân Hệ 1: Cấu Trúc Điểm Bán & Ca Kíp Thu Ngân

Quản lý hạ tầng máy móc và dòng tiền vật lý ra vào két thu ngân theo từng phiên làm việc.

* **1. `stores` (Danh mục siêu thị vật lý)**
* `store_id` (VARCHAR(20), PK): Mã siêu thị (`STORE_HN_001`).


* `store_name` (VARCHAR(150)): Tên chi nhánh (TC Mart Cầu Giấy).
* `store_format` (VARCHAR(30)): Định dạng (`HYPERMARKET`, `SUPERMARKET`, `MINIMART`).


* `region_id` (VARCHAR(20)): Vùng (`NORTH`, `CENTRAL`, `SOUTH`).


* `address`, `city`, `district` (VARCHAR(100)).


* `floor_area_sqm` (DECIMAL(10, 2)): Diện tích sàn kinh doanh phục vụ tính doanh thu/m².


* `is_active` (BOOLEAN): Trạng thái hoạt động.


* **2. `pos_terminals` (Máy tính tiền vật lý tại quầy)**
* `terminal_id` (VARCHAR(20), PK): Mã định danh máy POS (`POS_HN01_01`).
* `store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`): Cửa hàng đặt máy.


* `mac_address` (VARCHAR(50)): Địa chỉ phần cứng máy trạm.
* `ip_address` (VARCHAR(50)): Địa chỉ mạng nội bộ.
* `is_self_checkout` (BOOLEAN): Cờ phân biệt quầy thu ngân thường hay quầy khách tự thanh toán.


* **3. `cashier_shifts` (Phiên làm việc & Quản lý két tiền mặt)**
* `shift_id` (VARCHAR(40), PK): Mã ca làm việc (`SHIFT_20260914_01`).
* `store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`).


* `terminal_id` (VARCHAR(20), FK $\rightarrow$ `pos_terminals.terminal_id`).
* `cashier_id` (VARCHAR(20)): Mã nhân viên thu ngân mở ca.


* `opened_at` (DATETIME): Thời gian mở ca.


* `closed_at` (DATETIME, NULLABLE): Thời gian chốt ca.
* `opening_cash_float` (DECIMAL(15, 2)): Tiền lẻ ban đầu bàn giao vào két.
* `system_expected_cash` (DECIMAL(15, 2)): Tổng tiền mặt phần mềm tính toán phải có lúc kết ca.
* `actual_closing_cash` (DECIMAL(15, 2)): Tiền mặt thực tế đếm được khi bàn giao.
* `cash_variance` (DECIMAL(15, 2)): Chênh lệch thừa/thiếu tiền két (Actual - Expected).
* `shift_status` (VARCHAR(20)): `OPEN`, `CLOSED`, `RECONCILED` (Đã đối soát).



---

#### Phân Hệ 2: Danh Mục Sản Phẩm & Chính Sách Giá Vùng

Giải quyết đặc thù một mặt hàng có nhiều mã vạch quét quầy và giá bán khác nhau theo từng miền.

* **4. `products` (Danh mục mặt hàng Master)**
* `product_id` (VARCHAR(30), PK): Mã SKU sản phẩm nội bộ (`SKU_MILK_001`).


* `product_name` (VARCHAR(255)): Tên hiển thị trên hóa đơn.


* `department` (VARCHAR(50)): Ngành hàng (`FRESH_FOOD`, `FMCG`, `NON_FOOD`).


* `category_name` (VARCHAR(100)): Phân loại nhóm hàng.


* `base_uom` (VARCHAR(20)): Đơn vị tính cơ bản (`CAI`, `HOP`, `KG`, `GRAM`).
* `is_weighted` (BOOLEAN): Hàng cần cân ký tại quầy (rau củ, thịt tươi sống).
* `vat_rate` (DECIMAL(5, 2)): Thuế suất GTGT đầu ra (0%, 5%, 8%, 10%).




* **5. `product_barcodes` (Bảng quản lý mã vạch quét máy)**
* `barcode` (VARCHAR(30), PK): Mã vạch chuẩn GS1/EAN-13 quét tại máy đọc mã.


* `product_id` (VARCHAR(30), FK $\rightarrow$ `products.product_id`): Trỏ về SKU gốc.


* `packaging_unit` (VARCHAR(20)): Quy cách đóng gói (`ITEM` - chiếc lẻ, `PACK` - lốc 4 hộp, `BOX` - thùng 24 hộp).
* `conversion_factor` (DECIMAL(10, 3)): Hệ số quy đổi về đơn vị chuẩn (ví dụ 1 thùng = 24 chiếc).
* `is_primary` (BOOLEAN): Mã vạch in mặc định trên thân sản phẩm.


* **6. `store_price_books` (Chính sách giá theo từng khu vực / Siêu thị)**
* `price_book_id` (BIGINT, PK, IDENTITY).
* `store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`).


* `product_id` (VARCHAR(30), FK $\rightarrow$ `products.product_id`).


* `retail_price` (DECIMAL(15, 2)): Giá bán lẻ niêm yết chuẩn VND tại siêu thị đó.


* `effective_from` (DATETIME): Thời điểm giá bắt đầu có hiệu lực.
* `effective_to` (DATETIME, NULLABLE): Thời điểm hết hiệu lực.



---

#### Phân Hệ 3: Khách Hàng Thành Viên & Tích Điểm Tại Quầy

Lưu thông tin khách mua trực tiếp quẹt thẻ thành viên hoặc đọc số điện thoại.

* **7. `customers` (Hồ sơ khách hàng thành viên)**
* `customer_id` (BIGINT, PK): Mã số khách hàng.


* `phone_number` (VARCHAR(15), UNIQUE): Khóa định danh khi mua tại quầy.


* `full_name` (VARCHAR(150)).


* `loyalty_tier` (VARCHAR(20)): Hạng thẻ (`STANDARD`, `SILVER`, `GOLD`, `PLATINUM`).


* `current_loyalty_points` (INT): Số điểm tích lũy khả dụng.


* `registered_store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`): Nơi mở thẻ lần đầu.




* **8. `customer_loyalty_transactions` (Lịch sử biến động điểm tích lũy)**
* `loyalty_tx_id` (BIGINT, PK, IDENTITY).
* `customer_id` (BIGINT, FK $\rightarrow$ `customers.customer_id`).


* `invoice_id` (VARCHAR(40)): Mã hóa đơn phát sinh giao dịch tích/tiêu.


* `points_earned` (INT): Điểm cộng thêm từ đơn hàng.
* `points_redeemed` (INT): Điểm cấn trừ để giảm tiền mặt trên hóa đơn.
* `transaction_timestamp` (DATETIME).





---

#### Phân Hệ 4: Hạt Nhân Giao Dịch Bán Lẻ & Đa Tiền Tệ

Phản ánh chính xác nghiệp vụ thanh toán phức tạp: tách hình thức thanh toán (split payments), trả bằng ngoại tệ và phân bổ chiết khấu.

* **9. `sales_invoices` (Hóa đơn bán hàng quầy - Header)**
* `invoice_id` (VARCHAR(40), PK): UUID/Số hóa đơn bán lẻ.


* `store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`): Cửa hàng phát sinh giao dịch.


* `terminal_id` (VARCHAR(20), FK $\rightarrow$ `pos_terminals.terminal_id`): Máy POS bán đơn này.
* `shift_id` (VARCHAR(40), FK $\rightarrow$ `cashier_shifts.shift_id`): Thuộc ca làm việc nào.
* `cashier_id` (VARCHAR(20)): Mã thu ngân chốt bill.


* `customer_id` (BIGINT, NULLABLE, FK $\rightarrow$ `customers.customer_id`): NULL nếu khách vãng lai.


* `invoice_date` (DATETIME): Thời gian in hóa đơn chính xác đến giây.


* `total_gross_amount` (DECIMAL(15, 2)): Tổng tiền hàng nguyên giá trước giảm.


* `total_discount_amount` (DECIMAL(15, 2)): Tổng tiền chiết khấu toàn đơn.


* `total_tax_amount` (DECIMAL(15, 2)): Tiền thuế VAT.


* `total_net_amount` (DECIMAL(15, 2)): Tổng tiền phải trả cuối cùng bằng VND.


* `status` (VARCHAR(20)): `COMPLETED`, `VOIDED` (Hóa đơn hủy), `RETURNED` (Đã bị trả hàng).




* **10. `sales_invoice_items` (Chi tiết giỏ hàng - Hạt nhân Line Item)**
* `invoice_item_id` (BIGINT, PK, IDENTITY).
* `invoice_id` (VARCHAR(40), FK $\rightarrow$ `sales_invoices.invoice_id`).


* `line_number` (INT): Thứ tự dòng sản phẩm trên hóa đơn giấy.
* `product_id` (VARCHAR(30), FK $\rightarrow$ `products.product_id`).


* `scanned_barcode` (VARCHAR(30)): Mã vạch thực tế máy quét bắt được.


* `quantity` (DECIMAL(12, 3)): Số lượng bán (0.450 kg thịt tươi sống, hoặc 2 lon nước).


* `unit_price` (DECIMAL(15, 2)): Đơn giá bán tại thời điểm quét.


* `line_discount_amount` (DECIMAL(15, 2)): Tổng giảm giá phân bổ cho dòng này.


* `line_total_amount` (DECIMAL(15, 2)): Thành tiền dòng sau giảm giá.




* **11. `sales_payment_tenders` (Phương thức thanh toán & Ngoại tệ)**
* *Nghiệp vụ thực tế:* Một hóa đơn khách có thể thanh toán kết hợp (ví dụ: bill 1 triệu khách trả 500k tiền mặt + 500k quẹt Momo; hoặc khách nước ngoài đưa tờ 20 USD, thối lại bằng tiền VND).


* `tender_id` (BIGINT, PK, IDENTITY).
* `invoice_id` (VARCHAR(40), FK $\rightarrow$ `sales_invoices.invoice_id`).


* `payment_method` (VARCHAR(30)): `CASH`, `CREDIT_CARD`, `VIETQR`, `MOMO`, `VOUCHER`.


* `currency_code` (VARCHAR(3)): Tiền tệ gốc giao dịch (`VND`, `USD`, `CNY`).


* `exchange_rate` (DECIMAL(12, 4)): Tỷ giá hạch toán lúc thu ngân nhận tiền (1.0 nếu VND, 25,400 nếu USD).


* `tender_amount_original` (DECIMAL(15, 2)): Số tiền đưa theo đồng tiền gốc (ví dụ 50.00 USD).


* `tender_amount_vnd` (DECIMAL(15, 2)): Số tiền quy đổi ra VND ($tender\_amount\_original \times exchange\_rate$).


* `change_amount_vnd` (DECIMAL(15, 2)): Tiền thừa thối lại cho khách (luôn thối lại bằng VND).


* **12. `sales_item_discounts` (Bảng phân bổ chi tiết giảm giá)**
* `discount_entry_id` (BIGINT, PK, IDENTITY).
* `invoice_item_id` (BIGINT, FK $\rightarrow$ `sales_invoice_items.invoice_item_id`).
* `discount_type` (VARCHAR(30)): `PROMO_CAMPAIGN` (Khuyến mãi ngành hàng), `COMBO`, `LOYALTY_POINT`, `COUPON_CODE`.


* `promo_reference_id` (VARCHAR(50)): Mã chương trình ưu đãi để theo dõi hiệu quả.


* `discount_value` (DECIMAL(15, 2)): Số tiền giảm giá cụ thể trên mặt hàng.





---

#### Phân Hệ 5: Hậu Mãi, Hủy Hóa Đơn & Tồn Kho Điểm Bán

Xử lý các tình huống đổi trả, lỗi quẹt sai món và theo dõi số lượng tồn trên kệ siêu thị.

* **13. `sales_returns` (Biên bản đổi trả / Hủy đơn tại quầy)**
* `return_id` (VARCHAR(40), PK): Mã phiếu trả hàng.
* `original_invoice_id` (VARCHAR(40), FK $\rightarrow$ `sales_invoices.invoice_id`): Hóa đơn gốc được đối soát.


* `store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`).


* `return_timestamp` (DATETIME): Thời điểm trả hàng.
* `product_id` (VARCHAR(30), FK $\rightarrow$ `products.product_id`): Món hàng bị trả lại.


* `returned_quantity` (DECIMAL(12, 3)): Số lượng trả.


* `refund_amount_vnd` (DECIMAL(15, 2)): Tiền mặt/chuyển khoản hoàn lại cho khách.


* `return_reason` (VARCHAR(100)): `EXPIRED` (Hết hạn), `DAMAGED` (Hư hỏng), `CUSTOMER_CHANGE_MIND` (Khách đổi ý).
* *Ý nghĩa DE:* Bảng này sẽ được Spark biến đổi thành các dòng thực tế âm (**Negative Facts**) liên kết vào Fact_StoreSales ở tầng Gold để báo cáo doanh thu thuần không bị thổi phồng.




* **14. `store_inventory_snapshots` (Chốt tồn kho tại siêu thị vật lý)**
* `snapshot_id` (BIGINT, PK, IDENTITY).
* `store_id` (VARCHAR(20), FK $\rightarrow$ `stores.store_id`).


* `product_id` (VARCHAR(30), FK $\rightarrow$ `products.product_id`).


* `snapshot_date` (DATE): Ngày chốt số liệu kiểm kê.


* `shelf_stock_qty` (DECIMAL(12, 3)): Số lượng đang trưng bày trên quầy kệ.
* `backroom_stock_qty` (DECIMAL(12, 3)): Số lượng lưu trong kho phụ sau siêu thị.
* `damaged_loss_qty` (DECIMAL(12, 3)): Số lượng thất thoát/dập nát ghi nhận trong ngày.



---

### MAPPING CƠ CHẾ NẠP (INGESTION) TỪ 14 BẢNG VÀO LAKEHOUSE

Khi bạn bảo vệ đồ án, thầy cô sẽ đánh giá cao tư duy kiến trúc nếu bạn phân loại được cách dữ liệu di chuyển từ 14 bảng nguồn này vào **Raw Zone (MinIO)** và **Staging Zone (Iceberg)**:

| Nhóm Bảng Nguồn (SQL Server) | Cơ Chế Nạp (Ingestion Method) | Tần Suất Thu Thập | Xử Lý Tại Tầng Silver (Spark Job)

 | Ánh Xạ Tầng Gold (ClickHouse Star Schema)

 |
| --- | --- | --- | --- | --- |
| **`sales_invoices`, `sales_invoice_items**`<br> | **CDC / Batch JDBC**<br> | Mỗi 30–60 phút

 | Flatten cấu trúc lồng, khử trùng lặp theo `invoice_id` + `line_number`.

 | Nạp vào **`Fact_StoreSales`** (Hạt nhân chi tiết từng dòng).

 |
| **`sales_payment_tenders`**<br> | **Batch JDBC**<br> | Mỗi giờ

 | Tính toán quy đổi đa tiền tệ (USD/CNY) về VND qua tỷ giá giao dịch.

 | Nạp vào bảng phụ trợ **`Fact_PaymentTransactions`** hoặc tổng hợp theo hóa đơn.

 |
| **`sales_returns`**<br> | **Batch JDBC**<br> | Cuối mỗi ngày

 | Tạo bản ghi hoàn tiền âm (negative measures) tương thích hóa đơn gốc.

 | Giảm trừ trực tiếp trên chỉ số Net Sales của **`Fact_StoreSales`**.

 |
| **`cashier_shifts`** | **Batch JDBC**<br> | Cuối mỗi ca/ngày

 | Tính toán tỷ lệ thất thoát chênh lệch két tiền mặt (`cash_variance`). | Nạp vào **`Fact_CashierShiftReconciliation`** phục vụ kiểm toán nội bộ. |
| **`products`, `product_barcodes`, `store_price_books**`<br> | **Snapshot JDBC**<br> | 1 lần/ngày (đêm)

 | Áp dụng kỹ thuật SCD Type 2 để theo dõi lịch sử biến động giá và thông số.

 | Nạp vào **`Dim_Product`** (Bảng chiều sản phẩm có lịch sử hiệu lực).

 |
| **`stores`, `pos_terminals**`<br> | **Full Snapshot**<br> | Khi có thay đổi | Chuẩn hóa thông tin địa lý, gắn cờ định dạng siêu thị và phân cụm cửa hàng.

 | Nạp vào **`Dim_Store`**.

 |
| **`customers`, `customer_loyalty_transactions**`<br> | **Incremental JDBC**<br> | Mỗi giờ

 | Mã hóa bảo mật thông tin định danh (PII Hashing), chuẩn hóa số điện thoại.

 | Nạp vào **`Dim_Customer`**.

 |
| **`store_inventory_snapshots`** | **Batch JDBC**<br> | Cuối ngày

 | Tính toán tỷ lệ hao hụt hàng tươi sống trên kệ. | Nạp vào **`Fact_DailyStoreInventory`**.

 |

Thiết kế này giải quyết triệt để quy mô một hệ thống bán lẻ thực tế: có đủ bài toán tiền mặt, ngoại tệ, ca kíp thu ngân, mã vạch và chính sách giá vùng. Khi bắt đầu làm giả lập, bạn có thể tạo mã nguồn DDL bằng SQL Server và script sinh Mock Data cho cụm 14 bảng này theo đúng đồ thị phụ thuộc.
Bài toán nghiệp vụ tối ưu nhất khi tập trung hoàn toàn vào dữ liệu bán lẻ trực tiếp (POS từ SQL Server) là: **"Tối ưu hóa hiệu quả mặt sàn bán lẻ và khai phá hành vi giỏ hàng tại chuỗi siêu thị vật lý" (Physical Store Space Optimization & In-Store Market Basket Analytics)**.

Bài toán này khai thác triệt để độ chi tiết đến từng dòng sản phẩm trên hóa đơn (line-item grain), gắn liền với hạ tầng vật lý của siêu thị (diện tích sàn, máy tính tiền, ca kíp thu ngân) mà không cần phụ thuộc vào các nguồn khác.

---

**1. Mục Tiêu Nghiệp Vụ & Bài Toán Cần Giải Quyết**

Ban điều hành chuỗi siêu thị TC Mart cần trả lời 4 bài toán kinh doanh then chốt tại các điểm bán offline:

* **Hiệu suất mặt sàn kinh doanh:** Cửa hàng nào, định dạng nào (Hypermarket, Supermarket hay Minimart) đang mang lại doanh thu cao nhất trên mỗi mét vuông sàn (`floor_area_sqm`)?


* **Khai phá giỏ hàng (Market Basket Analysis):** Những cặp sản phẩm nào thường xuyên được khách hàng mua cùng nhau trong một lần quẹt bill để sắp xếp quầy kệ cạnh nhau hoặc tạo combo khuyến mãi kích cầu?


* **Kiểm soát vận hành & Thất thoát tiền mặt:** Tỷ lệ chênh lệch tiền két thực tế so với sổ sách (`cash_variance`) theo từng ca thu ngân (`cashier_shifts`) là bao nhiêu?


* **Dự báo nhu cầu cục bộ (In-Store Demand Forecasting):** Lượng tiêu thụ của từng mặt hàng tại mỗi siêu thị trong 7 ngày tới dự kiến ra sao để chủ động điều phối hàng bày lên kệ, giảm thiểu tình trạng đứt hàng (stockouts)?



---

**2. Các Chỉ Số Đo Lường Cốt Lõi (Key Metrics & KPIs)**

| Nhóm Phân Tích | Chỉ Số / KPI | Công Thức / Cơ Chế Tính Toán | Ý Nghĩa Điều Hành |
| --- | --- | --- | --- |
| **Hiệu suất cửa hàng**<br> | **Sales per $m^2$**<br> | $\frac{\text{Doanh thu thuần}}{\text{floor\_area\_sqm}}$<br> | Đánh giá hiệu quả khai thác diện tích thuê mặt bằng.

 |
| **Chất lượng giỏ hàng**<br> | **AOV & Basket Size**<br> | $\frac{\sum \text{Net Sales}}{\text{Số lượng HĐ}}$ và $\frac{\sum \text{Quantity}}{\text{Số lượng HĐ}}$<br> | Đo lường mức chi tiêu trung bình và số món trên một lượt khách.

 |
| **Quan hệ mặt hàng**<br> | **Support, Confidence, Lift** | Tần suất xuất hiện đồng thời của cặp SKU A và SKU B trong cùng `invoice_id`<br> | Tối ưu hóa vị trí đặt quầy kệ và thiết kế chương trình giảm giá chéo.

 |
| **Vận hành thu ngân**<br> | **Cash Variance Rate**<br> | $\text{actual\_cash} - \text{expected\_cash}$ theo từng `shift_id`<br> | Phát hiện thất thoát tiền mặt, sai sót khi thối tiền hoặc gian lận ca kíp.

 |
| **Tài chính đa tệ**<br> | **Normalized Net Sales**<br> | $\sum (\text{Qty} \times \text{Price} - \text{Discount}) \times \text{Exchange\_Rate}$<br> | Quy đổi toàn bộ hóa đơn ngoại tệ (USD, CNY) về đồng VND chuẩn hóa.

 |

---

**3. Kiến Trúc Pipeline Dành Riêng Cho Nguồn POS**

```
[SQL Server (14 bảng POS)] 
       │ 
       ▼ (Airflow JDBC Batch mỗi giờ)[cite: 1, 2]
[Raw Zone (MinIO)] ────────► pos_invoices, pos_items, shifts, products (Parquet thô)[cite: 1, 2]
       │ 
       ▼ (PySpark Transformation & Data Quality Gate)[cite: 1, 2]
+──────────────────────────────────────────────────────────────+
|  CỔNG KIỂM TRA CHẤT LƯỢNG (Great Expectations / PySpark)     |[cite: 1]
|  - Check trùng invoice_id, quantity > 0[cite: 1, 2]         |
|  - Check exchange_rate > 0 (giao dịch USD, CNY)[cite: 1, 2] |
|  - Check khóa ngoại product_id tồn tại[cite: 1, 2]          |
+──────────────────────────────┬───────────────────────────────+
                               │
            ┌──────────────────┴──────────────────┐
            ▼ (Hợp lệ)                            ▼ (Vi phạm)
[Silver Zone (Apache Iceberg)]        [Quarantine Zone (MinIO)][cite: 1, 2]
- Bảng Fact_StoreSales sạch           - Bản ghi lỗi tỷ giá / sai SKU[cite: 1, 2]
- Bảng Fact_CashierReconciliation     - Đẩy lên Data Steward Portal duyệt[cite: 1, 2]
- Quản lý SCD Type 2 giá sản phẩm[cite: 2]
            │
            ▼ (Spark ClickHouse Connector)[cite: 1, 2]
[Gold Zone (Star Schema trên ClickHouse)][cite: 1, 2]
  ├── Fact_StoreSales (ReplacingMergeTree)[cite: 1, 2]
  ├── Dim_Store, Dim_Product, Dim_Date (Lịch 4-4-5)[cite: 2]
  └── ML Forecast: Model Prophet / SARIMA (Dự báo số lượng bán)[cite: 1]
            │
            ▼
[Apache Superset Dashboard] ──► Giám sát doanh thu sàn, giỏ hàng & rủi ro két tiền[cite: 1, 2]

```

---

**4. Kịch Bản Cấy Dữ Liệu Kiểm Thử (Edge Cases Cho Đồ Án)**

Để bài toán bảo vệ đồ án gây ấn tượng mạnh về kỹ năng xử lý dữ liệu (DE), script giả lập dữ liệu sẽ cấy sẵn 4 kịch bản lỗi thực tế:

* **Trùng lặp giao dịch do đứt mạng:** 3% hóa đơn bị gửi lặp 2 lần do mạng POS cục bộ chập chờn rồi đồng bộ bù (kiểm thử khả năng khử trùng lặp của Iceberg/ClickHouse).


* **Lỗi tỷ giá ngoại hối:** Khách nước ngoài trả bằng USD/CNY nhưng `exchange_rate` bị âm hoặc bằng 1.0 (nhầm sang VND) $\rightarrow$ Hệ thống tự động chuyển vào vùng Quarantine để cô lập.


* **Bán hàng âm & Hàng trả lại:** Tạo các bản ghi hoàn hủy từ bảng `sales_returns` để sinh ra các dòng thực tế âm (negative facts), kiểm tra logic trừ doanh thu thuần.


* **Mã vạch lạ tại quầy:** Hóa đơn chứa sản phẩm không nằm trong danh mục `Dim_Product` (kiểm tra tính toàn vẹn khóa ngoại tham chiếu).



Xây dựng trọn vẹn bài toán này giúp bạn sở hữu một pipeline chuẩn chỉnh: từ trích xuất RDBMS, kiểm định chất lượng tự động, mô hình hóa Star Schema cho đến trực quan hóa BI và mô hình học máy dự báo nhu cầu.