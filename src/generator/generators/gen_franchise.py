"""
gen_franchise.py — Data Generator cho franchise_db (PostgreSQL)
Phụ thuộc: product_db (lấy product_id)
"""
import sys
import os
import random
from sqlalchemy import text
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import PG_BASE_URL, GEN_CONFIG
from generators.base import BaseGenerator
from sqlalchemy import create_engine


class FranchiseGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=franchise_db")
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))

    def get_master_data(self):
        product_ids = []
        with self.pg_engine.connect() as conn:
            res_prod = conn.execute(text("SELECT product_id, cost_price FROM product_db.products WHERE status='active'"))
            product_ids = [{"id": r[0], "cost": float(r[1])} for r in res_prod.fetchall()]
        return product_ids

    def run(self):
        print("Generating data for franchise_db...")
        products = self.get_master_data()
        if not products:
            print("❌ Lỗi: Cần chạy gen_product.py trước!")
            return

        # self.truncate_table("franchise_payments") # Không có bảng này
        self.truncate_table("franchise_orders_items")
        self.truncate_table("franchise_orders")
        self.truncate_table("franchise_monthly_reports")
        self.truncate_table("franchisees")
        
        with self.get_session() as session:
            # 1. Franchisees
            num_franchisees = GEN_CONFIG.get("num_franchisees", 20)
            franchisee_ids = []
            for i in range(1, num_franchisees + 1):
                contract_start = self.fake.date_between(start_date='-5y', end_date='-1y')
                res = session.execute(
                    text("""
                        INSERT INTO franchisees (franchisee_code, franchisee_name, owner_name, phone, email, region, city, address, contract_start, contract_end, status)
                        VALUES (:code, :name, :owner, :phone, :email, :region, :city, :addr, :startd, :endd, 'active')
                        RETURNING franchisee_id
                    """),
                    {
                        "code": f"FRA-{i:03d}",
                        "name": f"Đại lý {self.fake.company()}",
                        "owner": self.fake.name(),
                        "phone": self.vn_phone(),
                        "email": self.fake.company_email(),
                        "region": random.choice(["North", "Central", "South"]),
                        "city": self.fake.city(),
                        "addr": self.fake.address(),
                        "startd": contract_start,
                        "endd": contract_start + timedelta(days=365 * random.randint(2, 5))
                    }
                )
                franchisee_ids.append(res.scalar())
            print(f" - Inserted {len(franchisee_ids)} franchisees.")

            # 2. Franchise Orders & Items
            num_orders = GEN_CONFIG.get("num_franchise_orders", 300)
            for i in range(1, num_orders + 1):
                fran_id = random.choice(franchisee_ids)
                order_date = self.fake.date_time_this_year()
                
                order_products = random.sample(products, k=random.randint(5, 20))
                subtotal = 0
                items_data = []
                for p in order_products:
                    qty = random.randint(50, 500)
                    unit_price = p["cost"] * 1.15
                    discount = unit_price * qty * (random.choice([0.05, 0.1, 0.15]))
                    line_total = (unit_price * qty - discount)
                    subtotal += line_total
                    
                    items_data.append({
                        "product_id": p["id"], "quantity": qty, "unit_price": unit_price,
                        "discount": discount, "line_total": line_total
                    })
                
                total_amount = subtotal
                
                res = session.execute(
                    text("""
                        INSERT INTO franchise_orders (order_number, franchisee_id, order_date, currency_code, total_amount, status)
                        VALUES (:num, :fid, :date, 'VND', :total, :status)
                        RETURNING franchisee_order_id
                    """),
                    {
                        "num": f"FRO-{order_date.strftime('%Y%m%d')}-{i:04d}",
                        "fid": fran_id,
                        "date": order_date,
                        "total": total_amount,
                        "status": random.choice(["Completed", "Processing", "Cancelled"])
                    }
                )
                order_id = res.scalar()
                
                for item in items_data:
                    session.execute(
                        text("""
                            INSERT INTO franchise_orders_items (franchisee_order_id, product_id, quantity, unit_price, discount_amount, line_total)
                            VALUES (:oid, :pid, :qty, :up, :disc, :lt)
                        """),
                        {
                            "oid": order_id, "pid": item["product_id"], "qty": item["quantity"],
                            "up": item["unit_price"], "disc": item["discount"], "lt": item["line_total"]
                        }
                    )
                    
            session.commit()
            print(f" - Inserted {num_orders} franchise orders.")


if __name__ == "__main__":
    generator = FranchiseGenerator()
    generator.run()
