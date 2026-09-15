# Kế Hoạch Triển Khai: TCmart Data Lakehouse
*(Dựa trên lộ trình chi tiết của dự án - CSV)*

## Tổng quan Bài toán (T.1)
- Chọn bài toán: Phân tích Doanh thu & Top Sản Phẩm (Doanh thu & Top SP)
- Nguồn dữ liệu: Hệ thống máy bán hàng POS (SQL Server)

## Lộ Trình Thực Thi

### T.2: Thiết kế Database cho nguồn dữ liệu và giả lập dữ liệu
- [x] 2.1: Thiết kế Database cho nguồn dữ liệu
- [x] 2.2: Chọn loại DB và viết script tạo DB (SQL Server)
- [ ] 2.3: Viết file giả lập dữ liệu cho hệ thống DB nguồn

### T.3: Chọn data modeling trên datalakehouse
- [ ] 3.1: Chọn mô hình dữ liệu cho ở datalake
- [ ] 3.2: Thiết kế mô hình dữ liệu đầu ra (Star Schema)
- [ ] 3.3: Viết script tạo mô hình dữ liệu (ClickHouse)

### T.4: Chọn công nghệ và xây dựng hệ thống ETL
- [ ] 4.1: Chọn công nghệ/ giải pháp xây dựng hệ thống ETL và datalake
- [ ] 4.2: Set up môi trường và cấu trúc thư mục (Docker Compose)
- [ ] 4.3: Viết chức năng trích xuất dữ liệu SQL Server -> Bronze
- [ ] 4.4: Viết chức năng ETL & Data quality dữ liệu từ Raw qua staging
- [ ] 4.5: Xây dựng module kiểm tra chất lượng dữ liệu thủ công và Giao diện xử lý dữ liệu ngoại lệ
- [ ] 4.6: Xây dựng quy trình Chuyển đổi Dữ liệu Nghiệp vụ từ staging sang Gold Layer (datalakehouse)

### T.5: Xây dựng các giao diện UI và dashboard phân tích
- [ ] 5.1: Kết nối PowerBI dựng Dashboard phân tích Doanh thu & Top SP

### T.6: Viết tài liệu hướng dẫn, mô tả chi tiết
- [ ] 6.1: Tổng hợp mô tả nghiệp vụ, kiến trúc, code và hình ảnh vào File Word Báo cáo
- [ ] 6.2: Viết file README.md hướng dẫn chạy dự án, test lại luồng chạy từ A-Z để chuẩn bị Demo

### T.7: Báo cáo kết quả cuối cùng & Demo sản phẩm
- [ ] 7.1: Đóng gói Repo
- [ ] 7.2: Rà soát định dạng File Word Báo cáo Final
- [ ] 7.3: Review kết quả cuối cùng