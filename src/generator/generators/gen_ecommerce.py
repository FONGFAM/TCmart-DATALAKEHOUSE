"""
gen_ecommerce.py — Data Generator cho ecommerce_db (PostgreSQL)
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


class EcommerceGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(PG_BASE_URL.format(db="postgres") + "?options=-c%20search_path=ecommerce_db")
        self.pg_engine = create_engine(PG_BASE_URL.format(db="postgres"))

    def get_master_data(self):
        product_ids = []
        with self.pg_engine.connect() as conn:
            res_prod = conn.execute(text("SELECT product_id, cost_price FROM product_db.products WHERE status='active'"))
            product_ids = [{"id": r[0], "cost": float(r[1])} for r in res_prod.fetchall()]
        return product_ids

    def run(self):
        print("Generating data for ecommerce_db...")
        products = self.get_master_data()
        if not products:
            print("❌ Lỗi: Cần chạy gen_product.py trước!")
            return

        self.truncate_table("payments")
        self.truncate_table("online_order_items")
        self.truncate_table("online_orders")
        self.truncate_table("customers")
        
        with self.get_session() as session:
            # 1. Customers
            num_customers = GEN_CONFIG.get("num_customers", 500)
            customer_ids = []
            for i in range(1, num_customers + 1):
                res = session.execute(
                    text("""
                        INSERT INTO customers (customer_code, fullname, gender, date_of_birth, phone, email, country, customer_type, created_at, status)
                        VALUES (:code, :name, :gender, :dob, :phone, :email, :country, :type, :created, 'active')
                        RETURNING customer_id
                    """),
                    {
                        "code": f"CUST-ECO-{i:05d}",
                        "name": self.fake.name(),
                        "gender": random.choice(["Male", "Female"]),
                        "dob": self.fake.date_of_birth(minimum_age=16, maximum_age=70),
                        "phone": self.vn_phone(),
                        "email": self.fake.email(),
                        "country": 84,
                        "type": random.choice(["Standard", "Silver", "Gold", "Platinum"]),
                        "created": self.fake.date_between(start_date='-2y', end_date='today')
                    }
                )
                customer_ids.append(res.scalar())
            print(f" - Inserted {len(customer_ids)} customers.")

            # 2. Orders & Items
            num_orders = GEN_CONFIG.get("num_online_orders", 1500)
            for i in range(1, num_orders + 1):
                cust_id = random.choice(customer_ids)
                order_date = self.fake.date_time_this_year()
                
                order_products = random.sample(products, k=random.randint(1, 4))
                subtotal = 0
                items_data = []
                for p in order_products:
                    qty = random.randint(1, 3)
                    unit_price = p["cost"] * 1.4
                    discount = unit_price * qty * (random.choice([0, 0, 0, 0.1, 0.2]))
                    line_total = (unit_price * qty - discount)
                    subtotal += line_total
                    
                    items_data.append({
                        "product_id": p["id"], "quantity": qty, "unit_price": unit_price,
                        "discount": discount, "line_total": line_total
                    })
                
                shipping_fee = random.choice([0, 15000, 30000])
                total_amount = subtotal + shipping_fee
                
                res = session.execute(
                    text("""
                        INSERT INTO online_orders (order_number, customer_id, order_date, channel, currency_code, subtotal, discount_amount, shipping_fee, total_amount, order_status)
                        VALUES (:num, :cid, :date, :chan, 'VND', :sub, 0, :ship, :total, :status)
                        RETURNING online_order_id
                    """),
                    {
                        "num": f"ECO-{order_date.strftime('%Y%m%d')}-{i:05d}",
                        "cid": cust_id,
                        "date": order_date,
                        "chan": random.choice(["Web", "App"]),
                        "sub": subtotal, "ship": shipping_fee, "total": total_amount,
                        "status": random.choice(["Delivered", "Shipped", "Processing", "Cancelled"])
                    }
                )
                order_id = res.scalar()
                
                for item in items_data:
                    session.execute(
                        text("""
                            INSERT INTO online_order_items (online_order_id, product_id, quantity, unit_price, discount_amount, line_total)
                            VALUES (:oid, :pid, :qty, :up, :disc, :lt)
                        """),
                        {
                            "oid": order_id, "pid": item["product_id"], "qty": item["quantity"],
                            "up": item["unit_price"], "disc": item["discount"], "lt": item["line_total"]
                        }
                    )
                    
                # Payment
                session.execute(
                    text("""
                        INSERT INTO payments (online_order_id, payment_method, transaction_code, amount, currency_code, status)
                        VALUES (:oid, :method, :trans, :amt, 'VND', 'Success')
                    """),
                    {
                        "oid": order_id, 
                        "method": random.choice(["COD", "CreditCard", "Momo", "ZaloPay"]), 
                        "trans": f"TRX-{self.fake.uuid4()[:8].upper()}",
                        "amt": total_amount
                    }
                )
                
            session.commit()
            print(f" - Inserted {num_orders} eCommerce orders.")


if __name__ == "__main__":
    generator = EcommerceGenerator()
    generator.run()
