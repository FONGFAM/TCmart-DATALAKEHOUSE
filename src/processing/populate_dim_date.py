"""
populate_dim_date.py — Tạo bảng Dim_Date với Lịch Âm Việt Nam
Chạy 1 lần để seed Dim_Date cho các năm 2024-2027.
Yêu cầu: pip install lunardate requests clickhouse-driver
"""
import requests
from lunardate import LunarDate
from datetime import date, timedelta
import os

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASS = os.getenv("CLICKHOUSE_PASSWORD", "tcmart2026")

# Ngày lễ Việt Nam cố định (MM-DD)
VN_FIXED_HOLIDAYS = {
    "01-01": "Tết Dương Lịch",
    "04-30": "Ngày Giải Phóng",
    "05-01": "Quốc Tế Lao Động",
    "09-02": "Quốc Khánh",
}
# Ngày lễ Âm Lịch (lunar_month, lunar_day)
VN_LUNAR_HOLIDAYS = {
    (1, 1): "Tết Nguyên Đán",
    (1, 2): "Tết Nguyên Đán",
    (1, 3): "Tết Nguyên Đán",
    (1, 15): "Rằm tháng Giêng",
    (3, 10): "Giỗ Tổ Hùng Vương",
    (7, 15): "Rằm tháng 7",
    (8, 15): "Tết Trung Thu",
    (12, 30): "Giao Thừa",
}


def build_dim_date(start: date, end: date) -> list[dict]:
    rows = []
    current = start
    sk = int(start.strftime("%Y%m%d"))

    while current <= end:
        # Lịch Âm
        try:
            lunar = LunarDate.fromSolarDate(current.year, current.month, current.day)
            lunar_day   = lunar.day
            lunar_month = lunar.month
            lunar_year  = lunar.year
        except Exception:
            lunar_day = lunar_month = lunar_year = 0

        # Cờ Lễ Tết
        is_vietnam_holiday = 0
        is_lunar_new_year  = 0
        is_mid_autumn      = 0

        mmdd = current.strftime("%m-%d")
        if mmdd in VN_FIXED_HOLIDAYS:
            is_vietnam_holiday = 1
        if (lunar_month, lunar_day) in VN_LUNAR_HOLIDAYS:
            is_vietnam_holiday = 1
        if lunar_month == 1 and lunar_day in [1, 2, 3]:
            is_lunar_new_year = 1
        if lunar_month == 8 and lunar_day == 15:
            is_mid_autumn = 1

        rows.append({
            "date_sk":            int(current.strftime("%Y%m%d")),
            "full_date":          current.strftime("%Y-%m-%d"),
            "year":               current.year,
            "quarter":            (current.month - 1) // 3 + 1,
            "month":              current.month,
            "week_of_year":       int(current.strftime("%W")),
            "day_of_week":        current.isoweekday(),  # 1=Mon
            "day_name":           current.strftime("%A"),
            "is_weekend":         1 if current.weekday() >= 5 else 0,
            "is_month_start":     1 if current.day == 1 else 0,
            "is_month_end":       1 if (current + timedelta(days=1)).month != current.month else 0,
            "lunar_day":          lunar_day,
            "lunar_month":        lunar_month,
            "lunar_year":         lunar_year,
            "is_lunar_new_year":  is_lunar_new_year,
            "is_mid_autumn":      is_mid_autumn,
            "is_vietnam_holiday": is_vietnam_holiday,
        })
        current += timedelta(days=1)
    return rows


def insert_to_clickhouse(rows: list[dict]):
    ch_url = f"http://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/"
    auth   = (CLICKHOUSE_USER, CLICKHOUSE_PASS)

    # Batch insert via VALUES
    BATCH = 500
    total = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i+BATCH]
        values = ",\n".join([
            f"({r['date_sk']}, '{r['full_date']}', {r['year']}, {r['quarter']}, "
            f"{r['month']}, {r['week_of_year']}, {r['day_of_week']}, '{r['day_name']}', "
            f"{r['is_weekend']}, {r['is_month_start']}, {r['is_month_end']}, "
            f"{r['lunar_day']}, {r['lunar_month']}, {r['lunar_year']}, "
            f"{r['is_lunar_new_year']}, {r['is_mid_autumn']}, {r['is_vietnam_holiday']})"
            for r in batch
        ])
        sql = f"""INSERT INTO gold.Dim_Date
            (date_sk, full_date, year, quarter, month, week_of_year, day_of_week,
             day_name, is_weekend, is_month_start, is_month_end,
             lunar_day, lunar_month, lunar_year,
             is_lunar_new_year, is_mid_autumn, is_vietnam_holiday)
            VALUES {values}"""
        resp = requests.post(ch_url, data=sql.encode("utf-8"), auth=auth, timeout=30)
        if resp.status_code != 200:
            print(f"  ❌ Batch {i}: {resp.text[:200]}")
        else:
            total += len(batch)
    print(f"  ✅ Inserted {total} rows into gold.Dim_Date")


if __name__ == "__main__":
    print("⏳ Building Dim_Date (2024-01-01 to 2027-12-31)...")
    rows = build_dim_date(date(2024, 1, 1), date(2027, 12, 31))
    print(f"  Built {len(rows)} rows")
    insert_to_clickhouse(rows)
