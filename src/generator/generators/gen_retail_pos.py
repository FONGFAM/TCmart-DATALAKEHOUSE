"""
gen_retail_pos.py — Data Generator hoàn chỉnh cho retail_pos_db (SQL Server)

THIẾT KẾ:
  - Tự cung cấp dữ liệu nội bộ, KHÔNG phụ thuộc PostgreSQL/Oracle
  - Giới hạn: MAX 5,000 hóa đơn/lần chạy để bảo vệ RAM 16GB
  - Cố ý cấy 4 kịch bản lỗi để test Data Quality pipeline:
      [E1] 3% hóa đơn bị gửi lặp 2 lần (duplicate invoice_id)
      [E2] Lỗi tỷ giá: exchange_rate ≤ 0 khi khách trả USD/CNY
      [E3] Dòng đổi/trả hàng tạo Negative Fact (sales_returns)
      [E4] Mã vạch lạ không tồn tại trong bảng products
"""
import random
import uuid
import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal

# pyrefly: ignore [missing-import]
from faker import Faker
# pyrefly: ignore [missing-import]
from faker.providers import address, person, phone_number
from sqlalchemy import create_engine, text

# ─── Cấu hình kết nối ───────────────────────────────────────────────────────
MSSQL_CONN = os.getenv(
    "MSSQL_URL",
    "mssql+pyodbc://sa:TCMart%402026%21Strong@localhost:1433/retail_pos_db"
    "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
)

# ─── Cấu hình số lượng ──────────────────────────────────────────────────────
CONFIG = {
    "num_stores": 8,            # Số siêu thị
    "terminals_per_store": 3,   # Số máy POS mỗi siêu thị
    "num_products": 200,        # Số SKU sản phẩm
    "num_customers": 500,       # Số khách hàng thành viên
    "num_cashiers": 40,         # Số nhân viên thu ngân
    "num_invoices": 2000,       # Số hóa đơn (MAX 5000 — quy định RAM)
    "pct_member_customer": 0.4, # 40% hóa đơn có khách thành viên
    "pct_fx_payment": 0.05,     # 5% hóa đơn thanh toán ngoại tệ (USD/CNY)
    "pct_split_payment": 0.1,   # 10% hóa đơn thanh toán split
    "pct_return": 0.08,         # 8% hóa đơn bị đổi/trả
    # ─── Tỷ lệ lỗi cấy vào ────
    "err_e1_duplicate_pct": 0.03,   # [E1] 3% hóa đơn duplicate
    "err_e2_bad_rate_pct": 0.30,    # [E2] 30% giao dịch ngoại tệ có tỷ giá sai
    "err_e4_bad_barcode_pct": 0.02, # [E4] 2% items có barcode không hợp lệ
}

fake = Faker("vi_VN")
fake.add_provider(address)
fake.add_provider(person)
fake.add_provider(phone_number)

# ─── Dữ liệu tham chiếu tĩnh ────────────────────────────────────────────────
STORE_FORMATS = ["HYPERMARKET", "SUPERMARKET", "MINIMART"]
REGIONS = ["NORTH", "CENTRAL", "SOUTH"]
DEPARTMENTS = ["FRESH_FOOD", "FMCG", "BEVERAGE", "NON_FOOD", "PERSONAL_CARE"]
PAYMENT_METHODS = ["CASH", "VIETQR", "MOMO", "ZALOPAY", "CREDIT_CARD"]
RETURN_REASONS = ["EXPIRED", "DAMAGED", "CUSTOMER_CHANGE_MIND", "CASHIER_ERROR"]
LOYALTY_TIERS = ["STANDARD", "SILVER", "GOLD", "PLATINUM"]

# Tỷ giá tham chiếu chính thức (VND/1 đơn vị ngoại tệ)
OFFICIAL_RATES = {"USD": 25400.0, "CNY": 3500.0, "EUR": 27800.0}
FX_CURRENCIES = ["USD", "CNY"]

CITIES = {
    "NORTH":   ["Hà Nội", "Hải Phòng", "Quảng Ninh"],
    "CENTRAL": ["Đà Nẵng", "Huế", "Quảng Nam"],
    "SOUTH":   ["TP. Hồ Chí Minh", "Bình Dương", "Đồng Nai"],
}

PRODUCT_NAMES_BY_DEPT = {
    "FRESH_FOOD":    ["Thịt heo ba chỉ", "Thịt bò nhập khẩu", "Cá basa fillet", "Rau muống", "Bắp cải", "Cà chua"],
    "FMCG":          ["Mì gói Hảo Hảo", "Dầu ăn Neptune", "Nước mắm Phú Quốc", "Sữa đặc Ông Thọ"],
    "BEVERAGE":      ["Bia Tiger lon", "Nước suối Aquafina", "Pepsi lon", "Trà xanh 0°"],
    "NON_FOOD":      ["Xà phòng Lifebuoy", "Nước tẩy rửa Gift", "Giấy vệ sinh Pulppy"],
    "PERSONAL_CARE": ["Dầu gội Sunsilk", "Sữa tắm Dove", "Kem đánh răng Colgate"],
}


def gen_stores(engine, n: int) -> list[dict]:
    stores = []
    for i in range(1, n + 1):
        region = random.choice(REGIONS)
        fmt = random.choice(STORE_FORMATS)
        city = random.choice(CITIES[region])
        area = round(random.uniform(200, 8000), 2) if fmt == "HYPERMARKET" else \
               round(random.uniform(100, 2000), 2) if fmt == "SUPERMARKET" else \
               round(random.uniform(30, 300), 2)
        s = {
            "store_id": f"STORE_{region[:2]}_{i:03d}",
            "store_name": f"TC Mart {city} {i:02d}",
            "store_format": fmt,
            "region_id": region,
            "address": fake.street_address(),
            "city": city,
            "district": fake.city_prefix(),
            "floor_area_sqm": area,
            "is_active": 1,
            "opened_date": fake.date_between(start_date="-5y", end_date="-1y"),
        }
        stores.append(s)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dbo.store_inventory_snapshots"))
        conn.execute(text("DELETE FROM dbo.sales_returns"))
        conn.execute(text("DELETE FROM dbo.sales_item_discounts"))
        conn.execute(text("DELETE FROM dbo.customer_loyalty_transactions"))
        conn.execute(text("DELETE FROM dbo.sales_payment_tenders"))
        conn.execute(text("DELETE FROM dbo.sales_invoice_items"))
        conn.execute(text("DELETE FROM dbo.sales_invoices"))
        conn.execute(text("DELETE FROM dbo.cashier_shifts"))
        conn.execute(text("DELETE FROM dbo.customers"))
        conn.execute(text("DELETE FROM dbo.store_price_books"))
        conn.execute(text("DELETE FROM dbo.product_barcodes"))
        conn.execute(text("DELETE FROM dbo.products"))
        conn.execute(text("DELETE FROM dbo.pos_terminals"))
        conn.execute(text("DELETE FROM dbo.stores"))
        conn.execute(
            text("""INSERT INTO dbo.stores
                    (store_id, store_name, store_format, region_id, address, city, district,
                     floor_area_sqm, is_active, opened_date)
                    VALUES (:store_id, :store_name, :store_format, :region_id, :address, :city, :district,
                            :floor_area_sqm, :is_active, :opened_date)"""),
            stores
        )
    print(f"  ✅ stores: {len(stores)} rows")
    return stores


def gen_terminals(engine, stores: list) -> list[dict]:
    terminals = []
    for s in stores:
        for j in range(1, CONFIG["terminals_per_store"] + 1):
            terminals.append({
                "terminal_id": f"POS_{s['store_id']}_{j:02d}",
                "store_id": s["store_id"],
                "mac_address": fake.mac_address(),
                "ip_address": f"192.168.{random.randint(1,10)}.{random.randint(10,250)}",
                "is_self_checkout": 1 if j == CONFIG["terminals_per_store"] else 0,
                "is_active": 1,
            })
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.pos_terminals
                    (terminal_id, store_id, mac_address, ip_address, is_self_checkout, is_active)
                    VALUES (:terminal_id, :store_id, :mac_address, :ip_address, :is_self_checkout, :is_active)"""),
            terminals
        )
    print(f"  ✅ pos_terminals: {len(terminals)} rows")
    return terminals


def gen_cashiers(n: int) -> list[dict]:
    """Tạo danh sách thu ngân (không có bảng riêng — embedded trong shifts)"""
    cashiers = []
    for i in range(1, n + 1):
        cashiers.append({
            "cashier_id": f"EMP_{i:05d}",
            "cashier_name": fake.name(),
            "status": "ACTIVE",
        })
    return cashiers


def gen_products(engine, n: int) -> list[dict]:
    products = []
    barcodes = []
    for i in range(1, n + 1):
        dept = random.choice(DEPARTMENTS)
        names = PRODUCT_NAMES_BY_DEPT[dept]
        base_name = random.choice(names)
        product_id = f"SKU_{dept[:4]}_{i:05d}"
        uom = "KG" if dept == "FRESH_FOOD" else random.choice(["CAI", "HOP", "GOI", "CHAI", "LON"])
        products.append({
            "product_id": product_id,
            "product_name": f"{base_name} {fake.bothify('??-###')}",
            "department": dept,
            "category_name": base_name,
            "base_uom": uom,
            "is_weighted": 1 if uom == "KG" else 0,
            "vat_rate": random.choice([0.0, 5.0, 8.0, 10.0]),
            "is_active": 1,
        })
        # Mỗi sản phẩm có 1-3 barcode
        primary_barcode = fake.ean(length=13)
        barcodes.append({
            "barcode": primary_barcode, "product_id": product_id,
            "packaging_unit": "ITEM", "conversion_factor": 1.0, "is_primary": 1
        })
        if random.random() < 0.3:
            barcodes.append({
                "barcode": fake.ean(length=13), "product_id": product_id,
                "packaging_unit": "PACK", "conversion_factor": 4.0, "is_primary": 0
            })

    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.products
                    (product_id, product_name, department, category_name, base_uom,
                     is_weighted, vat_rate, is_active)
                    VALUES (:product_id, :product_name, :department, :category_name, :base_uom,
                            :is_weighted, :vat_rate, :is_active)"""),
            products
        )
        conn.execute(
            text("""INSERT INTO dbo.product_barcodes
                    (barcode, product_id, packaging_unit, conversion_factor, is_primary)
                    VALUES (:barcode, :product_id, :packaging_unit, :conversion_factor, :is_primary)"""),
            barcodes
        )
    print(f"  ✅ products: {len(products)} rows | product_barcodes: {len(barcodes)} rows")
    return products


def gen_price_books(engine, stores: list, products: list):
    price_books = []
    for s in stores:
        for p in products:
            base_price = round(random.uniform(5000, 500000), 0)
            price_books.append({
                "store_id": s["store_id"],
                "product_id": p["product_id"],
                "retail_price": base_price,
                "effective_from": datetime(2025, 1, 1),
                "effective_to": None,
            })
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.store_price_books
                    (store_id, product_id, retail_price, effective_from, effective_to)
                    VALUES (:store_id, :product_id, :retail_price, :effective_from, :effective_to)"""),
            price_books
        )
    print(f"  ✅ store_price_books: {len(price_books)} rows")


def gen_customers(engine, stores: list, n: int) -> list[dict]:
    customers = []
    phones_seen = set()
    for i in range(n):
        phone = fake.phone_number().replace(" ", "").replace("-", "")[:15]
        while phone in phones_seen:
            phone = fake.phone_number().replace(" ", "").replace("-", "")[:15]
        phones_seen.add(phone)
        customers.append({
            "phone_number": phone,
            "full_name": fake.name(),
            "loyalty_tier": random.choices(
                LOYALTY_TIERS, weights=[70, 20, 7, 3]
            )[0],
            "current_loyalty_points": random.randint(0, 50000),
            "registered_store_id": random.choice(stores)["store_id"],
            "registered_at": fake.date_time_between(start_date="-3y", end_date="now"),
        })
    inserted_ids = []
    with engine.begin() as conn:
        for c in customers:
            r = conn.execute(
                text("""INSERT INTO dbo.customers
                        (phone_number, full_name, loyalty_tier, current_loyalty_points,
                         registered_store_id, registered_at)
                        OUTPUT INSERTED.customer_id
                        VALUES (:phone_number, :full_name, :loyalty_tier, :current_loyalty_points,
                                :registered_store_id, :registered_at)"""),
                c
            )
            inserted_ids.append(r.scalar())
    print(f"  ✅ customers: {len(customers)} rows")
    return inserted_ids


def gen_shifts(engine, stores: list, terminals: list, cashiers: list,
               start_date: date, days: int) -> list[dict]:
    """Tạo ca làm việc: 2 ca/ngày (sáng 7h-15h, chiều 15h-23h)"""
    shifts = []
    terminal_by_store = {}
    for t in terminals:
        terminal_by_store.setdefault(t["store_id"], []).append(t["terminal_id"])

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        for s in stores:
            for t_id in terminal_by_store.get(s["store_id"], []):
                for shift_hour in [7, 15]:
                    cashier = random.choice(cashiers)
                    opened_at = datetime.combine(current_date, datetime.min.time()).replace(hour=shift_hour)
                    closed_at = opened_at + timedelta(hours=8)
                    shift_id = f"SHIFT_{s['store_id']}_{t_id}_{current_date.strftime('%Y%m%d')}_{shift_hour:02d}"
                    shifts.append({
                        "shift_id": shift_id,
                        "store_id": s["store_id"],
                        "terminal_id": t_id,
                        "cashier_id": cashier["cashier_id"],
                        "cashier_name": cashier["cashier_name"],
                        "opened_at": opened_at,
                        "closed_at": closed_at,
                        "opening_cash_float": round(random.uniform(500000, 2000000), 0),
                        "system_expected_cash": None,  # Tính sau
                        "actual_closing_cash": None,   # Tính sau
                        "cash_variance": None,
                        "shift_status": "CLOSED",
                    })

    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.cashier_shifts
                    (shift_id, store_id, terminal_id, cashier_id, cashier_name,
                     opened_at, closed_at, opening_cash_float, system_expected_cash,
                     actual_closing_cash, cash_variance, shift_status)
                    VALUES (:shift_id, :store_id, :terminal_id, :cashier_id, :cashier_name,
                            :opened_at, :closed_at, :opening_cash_float, :system_expected_cash,
                            :actual_closing_cash, :cash_variance, :shift_status)"""),
            shifts
        )
    print(f"  ✅ cashier_shifts: {len(shifts)} rows (for {days} days)")
    return shifts


def gen_invoices_and_payments(
    engine,
    stores: list, products: list, customer_ids: list, shifts: list,
    n_invoices: int
):
    """
    Tạo hóa đơn + items + tenders. Cố tình cấy các kịch bản lỗi.
    """
    shift_by_terminal = {}
    for sh in shifts:
        shift_by_terminal.setdefault(sh["terminal_id"], []).append(sh)

    # Price lookup: {(store_id, product_id): price}
    price_lookup = {}
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT store_id, product_id, retail_price FROM dbo.store_price_books"))
        for r in rows:
            price_lookup[(r[0], r[1])] = float(r[2])

    # Barcode lookup: {product_id: barcode}
    barcode_lookup = {}
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT product_id, barcode FROM dbo.product_barcodes WHERE is_primary = 1"))
        for r in rows:
            barcode_lookup[r[0]] = r[1]

    invoices, items, tenders, returns, loyalty_tx, discounts = [], [], [], [], [], []
    n_duplicate = int(n_invoices * CONFIG["err_e1_duplicate_pct"])
    duplicate_invoices = []
    
    global_invoice_item_id = 1

    all_shifts_list = shifts.copy()

    for i in range(n_invoices):
        shift = random.choice(all_shifts_list)
        store_id = shift["store_id"]
        terminal_id = shift["terminal_id"]
        shift_id = shift["shift_id"]
        cashier_id = shift["cashier_id"]

        # Thời gian hóa đơn trong khoảng ca làm việc
        inv_date = shift["opened_at"] + timedelta(
            seconds=random.randint(60, int((shift["closed_at"] - shift["opened_at"]).total_seconds()) - 60)
        )
        invoice_id = str(uuid.uuid4())

        # Chọn khách hàng
        customer_id = None
        if random.random() < CONFIG["pct_member_customer"] and customer_ids:
            customer_id = random.choice(customer_ids)

        # Chọn sản phẩm (2-6 items/hóa đơn)
        n_items = random.randint(2, 6)
        chosen_products = random.sample(products, k=min(n_items, len(products)))

        total_gross = 0.0
        total_discount = 0.0
        invoice_items = []
        for line_num, p in enumerate(chosen_products, start=1):
            pid = p["product_id"]
            qty = round(random.uniform(0.2, 3.0), 3) if p["is_weighted"] else float(random.randint(1, 5))
            unit_price = price_lookup.get((store_id, pid), round(random.uniform(5000, 200000), 0))
            discount_pct = random.choice([0, 0.05, 0.10])
            line_discount = round(unit_price * qty * discount_pct, 2)
            line_total = round(unit_price * qty - line_discount, 2)
            total_gross += round(unit_price * qty, 2)
            total_discount += line_discount

            invoice_item_id = global_invoice_item_id
            global_invoice_item_id += 1

            # [E4] Cấy barcode lạ cho 2% items
            if random.random() < CONFIG["err_e4_bad_barcode_pct"]:
                scanned_barcode = f"UNKNOWN_{random.randint(1000000000000, 9999999999999)}"
            else:
                scanned_barcode = barcode_lookup.get(pid, "")

            invoice_items.append({
                "invoice_item_id": invoice_item_id,
                "invoice_id": invoice_id, "line_number": line_num,
                "product_id": pid, "scanned_barcode": scanned_barcode,
                "quantity": qty, "unit_price": unit_price,
                "line_discount_amount": line_discount, "line_total_amount": line_total,
            })
            
            if line_discount > 0:
                discounts.append({
                    "invoice_item_id": invoice_item_id,
                    "discount_type": "PROMO_CAMPAIGN" if discount_pct == 0.05 else "COMBO",
                    "promo_reference_id": f"PROMO_{random.randint(100, 999)}",
                    "discount_value": line_discount
                })

        total_tax = round((total_gross - total_discount) * 0.08, 2)
        total_net = round(total_gross - total_discount + total_tax, 2)

        invoices.append({
            "invoice_id": invoice_id, "store_id": store_id,
            "terminal_id": terminal_id, "shift_id": shift_id,
            "cashier_id": cashier_id, "customer_id": customer_id,
            "invoice_date": inv_date,
            "total_gross_amount": round(total_gross, 2),
            "total_discount_amount": round(total_discount, 2),
            "total_tax_amount": total_tax, "total_net_amount": total_net,
            "status": "COMPLETED",
        })
        items.extend(invoice_items)
        
        if customer_id is not None:
            loyalty_tx.append({
                "customer_id": customer_id,
                "invoice_id": invoice_id,
                "points_earned": int(total_net / 10000),
                "points_redeemed": 0,
                "transaction_timestamp": inv_date
            })

        # ─── Tạo payment tenders ────────────────────────────────────────────
        is_fx = random.random() < CONFIG["pct_fx_payment"]
        is_split = random.random() < CONFIG["pct_split_payment"]

        if is_fx:
            currency = random.choice(FX_CURRENCIES)
            official_rate = OFFICIAL_RATES[currency]
            # [E2] 30% giao dịch ngoại tệ dùng tỷ giá sai
            if random.random() < CONFIG["err_e2_bad_rate_pct"]:
                applied_rate = random.choice([
                    -1.0,           # Âm — lỗi hệ thống
                    1.0,            # Nhầm = VND
                    official_rate * random.uniform(1.3, 2.0),  # Quá cao
                ])
            else:
                applied_rate = round(official_rate * random.uniform(0.98, 1.02), 4)

            fx_amount_original = round(total_net / max(abs(applied_rate), 0.01), 2)
            tenders.append({
                "invoice_id": invoice_id, "payment_method": "CASH",
                "currency_code": currency,
                "exchange_rate": applied_rate,
                "tender_amount_original": fx_amount_original,
                "tender_amount_vnd": round(fx_amount_original * abs(applied_rate), 2),
                "change_amount_vnd": 0.0,
            })
        elif is_split:
            half = round(total_net / 2, 2)
            tenders.append({
                "invoice_id": invoice_id, "payment_method": "CASH",
                "currency_code": "VND", "exchange_rate": 1.0,
                "tender_amount_original": half, "tender_amount_vnd": half, "change_amount_vnd": 0.0,
            })
            tenders.append({
                "invoice_id": invoice_id,
                "payment_method": random.choice(["VIETQR", "MOMO", "ZALOPAY"]),
                "currency_code": "VND", "exchange_rate": 1.0,
                "tender_amount_original": total_net - half,
                "tender_amount_vnd": total_net - half, "change_amount_vnd": 0.0,
            })
        else:
            method = random.choices(
                PAYMENT_METHODS, weights=[40, 25, 20, 10, 5]
            )[0]
            change = round(random.uniform(0, 50000), 0) if method == "CASH" else 0.0
            tenders.append({
                "invoice_id": invoice_id, "payment_method": method,
                "currency_code": "VND", "exchange_rate": 1.0,
                "tender_amount_original": total_net + change,
                "tender_amount_vnd": total_net + change, "change_amount_vnd": change,
            })

        # [E3] Đổi/trả hàng
        if random.random() < CONFIG["pct_return"] and invoice_items:
            item_to_return = random.choice(invoice_items)
            returns.append({
                "return_id": str(uuid.uuid4()),
                "original_invoice_id": invoice_id,
                "store_id": store_id,
                "return_timestamp": inv_date + timedelta(hours=random.randint(1, 72)),
                "product_id": item_to_return["product_id"],
                "returned_quantity": item_to_return["quantity"],
                "refund_amount_vnd": item_to_return["line_total_amount"],
                "return_reason": random.choice(RETURN_REASONS),
            })

        # [E1] Cấy duplicate invoice
        if len(duplicate_invoices) < n_duplicate:
            dup = dict(invoices[-1])
            duplicate_invoices.append(dup)  # Lưu lại để insert sau

    # Insert to DB
    print(f"  ⏳ Inserting {len(invoices)} invoices...")
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.sales_invoices
                    (invoice_id, store_id, terminal_id, shift_id, cashier_id, customer_id,
                     invoice_date, total_gross_amount, total_discount_amount,
                     total_tax_amount, total_net_amount, status)
                    VALUES (:invoice_id, :store_id, :terminal_id, :shift_id, :cashier_id, :customer_id,
                            :invoice_date, :total_gross_amount, :total_discount_amount,
                            :total_tax_amount, :total_net_amount, :status)"""),
            invoices
        )
        # [E1] Insert thêm hóa đơn trùng lặp (dùng invoice_id gốc)
        if duplicate_invoices:
            print(f"  ⚠️  [E1] Inserting {len(duplicate_invoices)} DUPLICATE invoices...")
            for dup in duplicate_invoices:
                try:
                    conn.execute(
                        text("""INSERT INTO dbo.sales_invoices
                                (invoice_id, store_id, terminal_id, shift_id, cashier_id, customer_id,
                                 invoice_date, total_gross_amount, total_discount_amount,
                                 total_tax_amount, total_net_amount, status)
                                VALUES (:invoice_id, :store_id, :terminal_id, :shift_id, :cashier_id, :customer_id,
                                        :invoice_date, :total_gross_amount, :total_discount_amount,
                                        :total_tax_amount, :total_net_amount, :status)"""),
                        dup
                    )
                except Exception:
                    pass  # PK violation expected — ghi log lỗi ở pipeline DQ

    with engine.begin() as conn:
        conn.execute(text("SET IDENTITY_INSERT dbo.sales_invoice_items ON"))
        conn.execute(
            text("""INSERT INTO dbo.sales_invoice_items
                    (invoice_item_id, invoice_id, line_number, product_id, scanned_barcode,
                     quantity, unit_price, line_discount_amount, line_total_amount)
                    VALUES (:invoice_item_id, :invoice_id, :line_number, :product_id, :scanned_barcode,
                            :quantity, :unit_price, :line_discount_amount, :line_total_amount)"""),
            items
        )
        conn.execute(text("SET IDENTITY_INSERT dbo.sales_invoice_items OFF"))
        
    with engine.begin() as conn:
        if discounts:
            conn.execute(
                text("""INSERT INTO dbo.sales_item_discounts
                        (invoice_item_id, discount_type, promo_reference_id, discount_value)
                        VALUES (:invoice_item_id, :discount_type, :promo_reference_id, :discount_value)"""),
                discounts
            )
            
    with engine.begin() as conn:
        if loyalty_tx:
            conn.execute(
                text("""INSERT INTO dbo.customer_loyalty_transactions
                        (customer_id, invoice_id, points_earned, points_redeemed, transaction_timestamp)
                        VALUES (:customer_id, :invoice_id, :points_earned, :points_redeemed, :transaction_timestamp)"""),
                loyalty_tx
            )

    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.sales_payment_tenders
                    (invoice_id, payment_method, currency_code, exchange_rate,
                     tender_amount_original, tender_amount_vnd, change_amount_vnd)
                    VALUES (:invoice_id, :payment_method, :currency_code, :exchange_rate,
                            :tender_amount_original, :tender_amount_vnd, :change_amount_vnd)"""),
            tenders
        )

    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.sales_returns
                    (return_id, original_invoice_id, store_id, return_timestamp,
                     product_id, returned_quantity, refund_amount_vnd, return_reason)
                    VALUES (:return_id, :original_invoice_id, :store_id, :return_timestamp,
                            :product_id, :returned_quantity, :refund_amount_vnd, :return_reason)"""),
            returns
        )

    print(f"  ✅ sales_invoices: {len(invoices)} | items: {len(items)}")
    print(f"  ✅ tenders: {len(tenders)} | returns: {len(returns)}")
    print(f"  ⚠️  [E1] Duplicate invoices seeded: {len(duplicate_invoices)}")
    fx_err = sum(1 for t in tenders if t["currency_code"] != "VND" and (t["exchange_rate"] <= 0 or t["exchange_rate"] == 1.0))
    print(f"  ⚠️  [E2] Bad FX rate records seeded: ~{fx_err}")
    bad_barcodes = sum(1 for it in items if "UNKNOWN_" in (it["scanned_barcode"] or ""))
    print(f"  ⚠️  [E4] Unknown barcode records seeded: {bad_barcodes}")
    print(f"  ⚠️  [E3] Return records seeded: {len(returns)}")


def update_shift_reconciliation(engine, shifts: list):
    """Tính lại system_expected_cash và actual_closing_cash, cash_variance cho mỗi ca"""
    print("  ⏳ Calculating shift reconciliation...")
    with engine.begin() as conn:
        for sh in shifts:
            # Tổng tiền mặt hệ thống tính trong ca này
            r = conn.execute(
                text("""
                    SELECT COALESCE(SUM(t.tender_amount_vnd), 0)
                    FROM dbo.sales_invoices i
                    JOIN dbo.sales_payment_tenders t ON i.invoice_id = t.invoice_id
                    WHERE i.shift_id = :sid AND t.payment_method = 'CASH' AND t.currency_code = 'VND'
                """),
                {"sid": sh["shift_id"]}
            ).scalar()
            total_cash_sales = float(r or 0)
            expected = sh["opening_cash_float"] + total_cash_sales

            # Cấy lệch ngẫu nhiên: 20% ca có chênh lệch >50,000 VND
            if random.random() < 0.2:
                variance = round(random.uniform(-150000, 150000), 0)
            else:
                variance = round(random.uniform(-30000, 30000), 0)

            actual = expected + variance

            conn.execute(
                text("""UPDATE dbo.cashier_shifts
                        SET system_expected_cash = :exp,
                            actual_closing_cash  = :actual,
                            cash_variance        = :var
                        WHERE shift_id = :sid"""),
                {"exp": expected, "actual": actual, "var": variance, "sid": sh["shift_id"]}
            )
    print(f"  ✅ cashier_shifts reconciliation updated for {len(shifts)} shifts")


def gen_inventory_snapshots(engine, stores: list, products: list, days: int):
    snapshots = []
    start = date.today() - timedelta(days=days)
    for day_offset in range(days):
        snap_date = start + timedelta(days=day_offset)
        for s in stores:
            sampled_products = random.sample(products, k=min(20, len(products)))
            for p in sampled_products:
                snapshots.append({
                    "store_id": s["store_id"],
                    "product_id": p["product_id"],
                    "snapshot_date": snap_date,
                    "shelf_stock_qty": round(random.uniform(0, 200), 3),
                    "backroom_stock_qty": round(random.uniform(0, 500), 3),
                    "damaged_loss_qty": round(random.uniform(0, 5), 3),
                })
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO dbo.store_inventory_snapshots
                    (store_id, product_id, snapshot_date, shelf_stock_qty,
                     backroom_stock_qty, damaged_loss_qty)
                    VALUES (:store_id, :product_id, :snapshot_date, :shelf_stock_qty,
                            :backroom_stock_qty, :damaged_loss_qty)"""),
            snapshots
        )
    print(f"  ✅ store_inventory_snapshots: {len(snapshots)} rows")


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  TC Mart POS Data Generator")
    print(f"  Target: {CONFIG['num_invoices']} invoices (max 5,000)")
    print("=" * 60)

    engine = create_engine(MSSQL_CONN, echo=False)
    try:
        engine.connect()
        print("  ✅ Connected to SQL Server")
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        sys.exit(1)

    # Tạo dữ liệu theo thứ tự phụ thuộc FK
    stores    = gen_stores(engine, CONFIG["num_stores"])
    terminals = gen_terminals(engine, stores)
    cashiers  = gen_cashiers(CONFIG["num_cashiers"])
    products  = gen_products(engine, CONFIG["num_products"])
    gen_price_books(engine, stores, products)
    customer_ids = gen_customers(engine, stores, CONFIG["num_customers"])

    # Tạo ca làm việc cho 30 ngày gần nhất
    start_date = date.today() - timedelta(days=30)
    shifts = gen_shifts(engine, stores, terminals, cashiers, start_date, days=30)

    # Tạo hóa đơn & giao dịch (có cấy 4 loại lỗi)
    gen_invoices_and_payments(
        engine, stores, products, customer_ids, shifts,
        CONFIG["num_invoices"]
    )

    # Cập nhật đối soát ca sau khi có đủ hóa đơn
    update_shift_reconciliation(engine, shifts)

    # Tạo tồn kho snapshot
    gen_inventory_snapshots(engine, stores, products, days=30)

    print("\n" + "=" * 60)
    print("  ✅ Data generation COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
