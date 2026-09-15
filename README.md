# TC MART Data Lakehouse

Dự án Xây dựng hệ thống Data Lakehouse cho chuỗi siêu thị bán lẻ TC MART.

## Giới thiệu
Dự án này nhằm mục đích xây dựng một kiến trúc dữ liệu hiện đại (Data Lakehouse) để thu thập, xử lý và lưu trữ dữ liệu từ hệ thống bán lẻ (POS) của TC MART. Hệ thống sẽ phục vụ các bài toán phân tích kinh doanh như:
- Tối ưu hóa tồn kho
- Đánh giá hiệu suất cửa hàng
- Khai phá hành vi mua sắm của khách hàng
- Quản lý các chương trình Loyalty & Khuyến mãi

## Kiến trúc (Dự kiến)
- **Source:** CSDL OLTP (SQL Server) ghi nhận các giao dịch bán hàng, thông tin khách hàng, tồn kho.
- **Data Lake/Data Warehouse:** Quản lý bằng Iceberg / ClickHouse.
- **ETL/ELT Pipeline:** Apache Spark, Apache Airflow.
- **BI Dashboard:** Apache Superset hoặc PowerBI.

## Khởi tạo dự án
Dự án được khởi tạo ở nhánh `master` này như một bảng trắng. Mã nguồn chi tiết sẽ được phát triển ở các nhánh chức năng tương ứng.
