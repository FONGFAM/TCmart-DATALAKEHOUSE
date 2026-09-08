"""
gen_retail_pos.py — Data Generator cho retail_pos_db (Microsoft SQL Server)
Phụ thuộc: product_db (lấy product_id), employee_db (lấy employee_id)
"""
import sys
import os
import random
from sqlalchemy import text
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import MSSQL_URL, PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator
from sqlalchemy import create_engine


class RetailPOSGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(MSSQL_URL)
        # Kết nối phụ đến Postgres để lấy danh mục (Cross-Database)
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))

    def get_master_data(self):
        """Lấy product_ids và employee_ids từ PostgreSQL"""
        product_ids = []
        employee_ids = []
        with self.pg_engine.connect() as conn:
            # Lấy sản phẩm có trạng thái active
            res_prod = conn.execute(text("SELECT product_id, cost_price FROM product_db.products WHERE status='active'"))
            product_ids = [{"id": r[0], "cost": float(r[1])} for r in res_prod.fetchall()]
            
            # Lấy nhân viên thu ngân/bán hàng
            res_emp = conn.execute(text("SELECT employee_id FROM employee_db.employees WHERE status='active'"))
            employee_ids = [r[0] for r in res_emp.fetchall()]
            
        return product_ids, employee_ids

    def run(self):
        print("Generating data for retail_pos_db (SQL Server)...")
        
        products, employees = self.get_master_data()
        if not products or not employees:
            print("❌ Lỗi: Cần chạy gen_product.py và gen_employee.py trước!")
            return

        self.truncate_table("payments")
        self.truncate_table("sales_order_items")
        self.truncate_table("sales_orders")
        self.truncate_table("pos_terminals")
        self.truncate_table("pos_inventory")
        self.truncate_table("stores")
        
        with self.get_session() as session:
            # 1. Stores
            num_stores = GEN_CONFIG.get("num_stores", 10)
            store_ids = []
            for i in range(1, num_stores + 1):
                res = session.execute(
                    text("""
                        INSERT INTO stores (store_code, store_name, region, address, city, warehouse_id, opened_date, status)
                        OUTPUT INSERTED.store_id
                        VALUES (:code, :name, :region, :addr, :city, :wh, :date, :status)
                    """),
                    {
                        "code": f"STR-{i:03d}",
                        "name": f"TCmart {self.fake.city()}",
                        "region": random.choice(["North", "Central", "South"]),
                        "addr": self.fake.street_address(),
                        "city": self.fake.city(),
                        "wh": random.randint(1, 5),
                        "date": self.fake.date_between(start_date='-3y', end_date='-1y'),
                        "status": "active"
                    }
                )
                store_ids.append(res.scalar())
            print(f" - Inserted {len(store_ids)} stores.")

            # 2. POS Terminals
            terminal_ids = []
            for store_id in store_ids:
                for t in range(1, 4):
                    res = session.execute(
                        text("""
                            INSERT INTO pos_terminals (store_id, terminal_code, status)
                            OUTPUT INSERTED.terminal_id
                            VALUES (:sid, :code, 'active')
                        """),
                        {"sid": store_id, "code": f"POS-{store_id}-{t}"}
                    )
                    terminal_ids.append(res.scalar())
            
            # 3. Inventory POS
            for store_id in store_ids:
                for p in products:
                    if random.random() < 0.5:
                        session.execute(
                            text("INSERT INTO pos_inventory (store_id, product_id, quantity) VALUES (:sid, :pid, :qty)"),
                            {"sid": store_id, "pid": p["id"], "qty": random.randint(10, 500)}
                        )
                        
            # 4. Sales Orders & Items & Payments
            num_orders = GEN_CONFIG.get("num_sales_orders", 1000)
            for i in range(1, num_orders + 1):
                store_id = random.choice(store_ids)
                
                order_products = random.sample(products, k=random.randint(1, 5))
                subtotal = 0
                items_data = []
                for p in order_products:
                    qty = random.randint(1, 5)
                    unit_price = p["cost"] * 1.3
                    discount = unit_price * qty * (random.choice([0, 0.05, 0.1]))
                    tax = (unit_price * qty - discount) * 0.08
                    line_total = (unit_price * qty - discount) + tax
                    subtotal += (unit_price * qty - discount)
                    
                    items_data.append({
                        "product_id": p["id"], "quantity": qty, "unit_price": unit_price,
                        "discount": discount, "tax": tax, "line_total": line_total
                    })
                
                total_tax = subtotal * 0.08
                total_amount = subtotal + total_tax
                
                res = session.execute(
                    text("""
                        INSERT INTO sales_orders (order_number, store_id, terminal_id, employee_id, order_date, channel, subtotal, tax_amount, total_amount, status)
                        OUTPUT INSERTED.sales_order_id
                        VALUES (:num, :sid, :tid, :eid, :date, 'InStore', :sub, :tax, :total, 'Completed')
                    """),
                    {
                        "num": f"SO-{self.fake.date_this_year().strftime('%Y%m%d')}-{i:06d}",
                        "sid": store_id,
                        "tid": random.choice(terminal_ids),
                        "eid": random.choice(employees),
                        "date": self.fake.date_time_this_year(),
                        "sub": subtotal, "tax": total_tax, "total": total_amount
                    }
                )
                order_id = res.scalar()
                
                for item in items_data:
                    session.execute(
                        text("""
                            INSERT INTO sales_order_items (sales_order_id, product_id, quantity, unit_price, discount_amount, tax_amount, line_total)
                            VALUES (:oid, :pid, :qty, :up, :disc, :tax, :lt)
                        """),
                        {
                            "oid": order_id, "pid": item["product_id"], "qty": item["quantity"],
                            "up": item["unit_price"], "disc": item["discount"], "tax": item["tax"], "lt": item["line_total"]
                        }
                    )
                    
                session.execute(
                    text("""
                        INSERT INTO payments (sales_order_id, payment_method, amount, currency_code, status)
                        VALUES (:oid, :method, :amt, 'VND', 'Success')
                    """),
                    {"oid": order_id, "method": random.choice(["Cash", "CreditCard", "Momo", "VNPay"]), "amt": total_amount}
                )
                
            session.commit()
            print(f" - Inserted {num_orders} POS sales orders.")


if __name__ == "__main__":
    generator = RetailPOSGenerator()
    generator.run()
