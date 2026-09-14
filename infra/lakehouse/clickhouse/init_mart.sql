CREATE DATABASE IF NOT EXISTS mart;

-- ==============================================================================
-- 1. BÁO CÁO DOANH THU BÁN HÀNG (Semantic View cho BI)
-- Mục đích: Đổi tên cột sang tiếng Việt thân thiện, tính toán Lợi Nhuận
-- ==============================================================================
CREATE VIEW IF NOT EXISTS mart.BaoCao_DoanhThu AS
SELECT 
    d.date_actual           AS NgayGiaoDich,
    d.day_name_vn           AS ThuTrongTuan,
    d.holiday_name_vn       AS NgayLeTet,
    s.store_name            AS TenCuaHang,
    s.region                AS KhuVuc,
    p.product_name          AS TenSanPham,
    p.category              AS DanhMuc,
    p.brand                 AS ThuongHieu,
    c.customer_name         AS TenKhachHang,
    c.loyalty_tier          AS HangThanhVien,
    f.invoice_id            AS MaHoaDon,
    f.quantity              AS SoLuongBan,
    f.unit_price            AS DonGia,
    f.total_sales_amount    AS DoanhThu,
    f.total_tax_amount      AS TienThue,
    f.total_cost_amount     AS GiaVon,
    (f.total_sales_amount - f.total_cost_amount) AS LoiNhuan
FROM gold.Fact_StoreSales f
LEFT JOIN (SELECT * FROM gold.Dim_Date FINAL) d ON f.date_sk = d.date_sk
LEFT JOIN (SELECT * FROM gold.Dim_Store FINAL) s ON f.store_sk = s.store_sk
LEFT JOIN (SELECT * FROM gold.Dim_Product FINAL) p ON f.product_sk = p.product_sk
LEFT JOIN (SELECT * FROM gold.Dim_Customer FINAL) c ON f.customer_sk = c.customer_sk;


-- ==============================================================================
-- 2. BÁO CÁO ĐỐI SOÁT THU NGÂN (Semantic View cho BI)
-- Mục đích: Theo dõi lệch tiền, lệch tỷ giá, phát hiện gian lận
-- ==============================================================================
CREATE VIEW IF NOT EXISTS mart.BaoCao_DoiSoatThuNgan AS
SELECT 
    d.date_actual           AS NgayGiaoDich,
    s.store_name            AS TenCuaHang,
    c.cashier_name          AS TenThuNgan,
    f.shift_id              AS MaCaLamViec,
    f.start_time            AS GioBatDau,
    f.end_time              AS GioKetThuc,
    f.system_total_sales_vnd AS DoanhThu_HeThong_GhiNhan,
    f.shift_total_collected_vnd AS TienThuNgan_NopLen,
    f.cash_variance_vnd     AS LechTien_ThucTe,
    f.fx_rate_variance_vnd  AS LechTien_DoTyGia,
    CASE 
        WHEN f.anomaly_flag = 'NORMAL' THEN 'Hợp Lệ'
        WHEN f.anomaly_flag = 'ANOMALY_DEFICIT' THEN 'Thiếu Tiền'
        WHEN f.anomaly_flag = 'ANOMALY_SURPLUS' THEN 'Thừa Tiền'
        ELSE f.anomaly_flag
    END                     AS TrangThai_DoiSoat
FROM gold.Fact_CashierShiftReconciliation f
LEFT JOIN (SELECT * FROM gold.Dim_Date FINAL) d ON f.date_sk = d.date_sk
LEFT JOIN (SELECT * FROM gold.Dim_Store FINAL) s ON f.store_sk = s.store_sk
LEFT JOIN (SELECT * FROM gold.Dim_Cashier FINAL) c ON f.cashier_sk = c.cashier_sk;
